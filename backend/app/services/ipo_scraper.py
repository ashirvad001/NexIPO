"""
Real-time Indian IPO Data Scraper — Multi-Source
Scrapes live IPO data from multiple sources:
  - IPO Central (ipocentral.in): upcoming IPOs, GMP data, listed returns
  - Moneycontrol (moneycontrol.com): detail pages with dates, subscription,
    financials, registrar, lead managers
  - InvestorGain (investorgain.com): fallback GMP data

The scraper is designed to be run:
  1. As a background task on app startup (sync_ipos)
  2. As a standalone script (enrich_ipos.py)
  3. Via the /api/v1/ipos/sync endpoint
"""

import re
import asyncio
import logging
import random
from datetime import datetime
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from urllib.parse import urljoin, urlparse

from app.models.ipo import IPO, IPOStatus, IPOType

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants & configuration
# ---------------------------------------------------------------------------

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
]

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
}

IPOCENTRAL_HOME = "https://ipocentral.in/"
IPOCENTRAL_GMP = "https://ipocentral.in/ipo-discussion/"
IPOCENTRAL_YEAR = "https://ipocentral.in/ipo-2026/"

MONEYCONTROL_BASE = "https://www.moneycontrol.com"
MONEYCONTROL_IPO = "https://www.moneycontrol.com/ipo/"
MONEYCONTROL_CLOSED = "https://www.moneycontrol.com/ipo/closed-ipos/"
MONEYCONTROL_LISTED = "https://www.moneycontrol.com/ipo/listed-ipos/"

REQUEST_DELAY = 2.0  # seconds between requests to avoid rate limiting


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _random_headers() -> dict:
    """Return headers with a random User-Agent."""
    h = dict(HEADERS)
    h["User-Agent"] = random.choice(USER_AGENTS)
    return h


def _parse_float(text: str) -> Optional[float]:
    """Safely extract a float from text like '₹1,287', '15.25%', '(2)', etc."""
    if not text:
        return None
    cleaned = text.strip()
    neg = False
    if cleaned.startswith("(") and cleaned.endswith(")"):
        neg = True
        cleaned = cleaned[1:-1]
    cleaned = re.sub(r"[₹,%x×X\s]", "", cleaned)
    cleaned = cleaned.replace(",", "").replace("−", "-").replace("–", "-")
    if not cleaned or cleaned == "-" or cleaned.lower() in ("na", "n/a", ""):
        return None
    try:
        val = float(cleaned)
        return -val if neg else val
    except (ValueError, TypeError):
        return None


def _parse_int(text: str) -> Optional[int]:
    """Safely extract an integer from text."""
    val = _parse_float(text)
    if val is not None:
        return int(val)
    return None


def _parse_date_range(text: str, year: int = None) -> tuple[Optional[datetime], Optional[datetime]]:
    """Parse IPO date ranges like '25 – 27 Feb', '27 Feb – 4 Mar'."""
    if not text or text.strip() in ("-", "", "NA", "Coming soon"):
        return None, None

    if year is None:
        year = datetime.now().year

    text = text.strip().replace("–", "-").replace("—", "-")
    parts = [p.strip() for p in text.split("-")]
    if len(parts) < 2:
        return None, None

    months = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    }

    def _extract_day_month(s: str):
        s = s.strip()
        tokens = s.split()
        day = None
        month = None
        for t in tokens:
            t_lower = t.lower().rstrip(",.")
            if t_lower in months:
                month = months[t_lower]
            elif t.isdigit():
                day = int(t)
        return day, month

    close_day, close_month = _extract_day_month(parts[-1])
    open_day, open_month = _extract_day_month(parts[0])
    if open_month is None:
        open_month = close_month
    if close_month is None or close_day is None:
        return None, None

    open_date = None
    close_date = None
    try:
        if open_day and open_month:
            open_date = datetime(year, open_month, open_day)
        close_date = datetime(year, close_month, close_day)
    except (ValueError, TypeError):
        pass
    return open_date, close_date


def _parse_mc_date(text: str) -> Optional[datetime]:
    """Parse Moneycontrol date formats like '25 Feb 2026' or '2026-03-05'."""
    if not text:
        return None
    text = text.strip()
    formats = [
        "%d %b %Y", "%d %B %Y", "%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y",
        "%b %d, %Y", "%d-%b-%Y", "%d %b, %Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt)
        except (ValueError, TypeError):
            continue
    return None


def _determine_status(open_date: Optional[datetime], close_date: Optional[datetime],
                      listing_date: Optional[datetime] = None) -> IPOStatus:
    """Determine IPO status from dates."""
    now = datetime.now()
    if listing_date and listing_date <= now:
        return IPOStatus.LISTED
    if open_date and close_date:
        if open_date <= now <= close_date:
            return IPOStatus.OPEN
        elif now > close_date:
            return IPOStatus.CLOSED
        elif now < open_date:
            return IPOStatus.UPCOMING
    if open_date and now < open_date:
        return IPOStatus.UPCOMING
    return IPOStatus.UPCOMING


def _generate_symbol(company_name: str) -> str:
    """Generate a unique-ish symbol from company name."""
    words = re.sub(r"[^a-zA-Z\s]", "", company_name).split()
    if len(words) >= 2:
        symbol = (words[0][:4] + words[1][:3]).upper()
    elif words:
        symbol = words[0][:7].upper()
    else:
        symbol = "IPO"
    return symbol


def _normalize_name(name: str) -> str:
    """Normalize company name for matching."""
    n = name.lower().strip()
    n = re.sub(r"\s*(limited|ltd|pvt|private|inc|corp|corporation)\s*\.?\s*$", "", n, flags=re.I)
    n = re.sub(r"\s+", " ", n).strip()
    return n


async def _fetch_page(url: str, delay: float = 0) -> Optional[str]:
    """Fetch a web page with error handling and optional delay."""
    if delay > 0:
        await asyncio.sleep(delay)
    try:
        async with httpx.AsyncClient(
            headers=_random_headers(), timeout=30.0, follow_redirects=True
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None


# ---------------------------------------------------------------------------
# SOURCE 1: IPO Central (Listings + GMP)
# ---------------------------------------------------------------------------

async def scrape_homepage() -> list[dict]:
    """Scrape IPO Central homepage for upcoming/open IPOs."""
    html = await _fetch_page(IPOCENTRAL_HOME)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    results = []

    for table_idx in range(min(2, len(tables))):
        table = tables[table_idx]
        rows = table.find_all("tr")
        is_sme = table_idx == 1

        for row in rows[1:]:
            cells = row.find_all(["td", "th"])
            if len(cells) < 4:
                continue

            link_tag = cells[0].find("a")
            company_name = cells[0].get_text(strip=True)
            if not company_name or "More" in company_name:
                continue

            detail_url = urljoin(IPOCENTRAL_HOME, link_tag["href"]) if link_tag else None
            date_text = cells[1].get_text(strip=True)
            price_text = cells[2].get_text(strip=True)
            size_text = cells[3].get_text(strip=True)

            price_parts = re.split(r"[–\-]", price_text)
            price_lower = _parse_float(price_parts[0]) if len(price_parts) >= 2 else None
            price_upper = _parse_float(price_parts[-1]) if price_parts else None

            open_date, close_date = _parse_date_range(date_text)
            issue_size = _parse_float(size_text)

            ipo_data = {
                "company_name": company_name,
                "ipo_type": IPOType.SME if is_sme else IPOType.MAINBOARD,
                "price_band_lower": price_lower,
                "price_band_upper": price_upper,
                "open_date": open_date,
                "close_date": close_date,
                "issue_size_rs_cr": issue_size,
                "status": _determine_status(open_date, close_date),
                "data_source": f"ipocentral:home",
            }
            
            if detail_url:
                ipo_data["detail_url"] = detail_url

            if price_upper and price_upper > 0:
                estimated_lot = max(1, round(15000 / price_upper))
                ipo_data["lot_size"] = estimated_lot
                ipo_data["min_investment"] = estimated_lot * price_upper

            results.append(ipo_data)

    logger.info(f"Scraped {len(results)} IPOs from IPO Central homepage")
    return results


async def scrape_investorgain_gmp() -> dict[str, dict]:
    """Scrape GMP data from investorgain.com as fallback."""
    url = "https://www.investorgain.com/report/live-ipo-gmp/331/"
    html = await _fetch_page(url)
    if not html:
        return {}

    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    results = {}

    target_table = None
    for table in tables:
        header_row = table.find('tr')
        if header_row:
            headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
            if 'gmp' in headers and 'name' in headers:
                target_table = table
                break
    
    if not target_table and tables:
        target_table = tables[0]

    if target_table:
        header_row = target_table.find('tr')
        headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
        
        try:
            name_idx = headers.index('name')
            gmp_idx = headers.index('gmp')
            price_idx = next((i for i, h in enumerate(headers) if 'price' in h), -1)
        except (ValueError, StopIteration):
            name_idx, gmp_idx, price_idx = 0, 1, 4 # Fallback defaults

        rows = target_table.find_all("tr")
        for row in rows[1:]:
            cells = row.find_all(["td", "th"])
            if len(cells) <= max(name_idx, gmp_idx):
                continue

            raw_name = cells[name_idx].get_text(strip=True)
            if not raw_name:
                continue

            company_name = re.sub(r"\(.*?\)\s*$", "", raw_name).strip()
            # Clean "IPO" and "Limited" etc for matching
            norm_name = _normalize_name(company_name)

            gmp_text = cells[gmp_idx].get_text(strip=True)
            # Handle "₹ 45 (10%)"
            gmp_match = re.search(r'-?\d+\.?\d*', gmp_text.replace(',', ''))
            gmp = float(gmp_match.group(0)) if gmp_match else None
            
            price = None
            if price_idx != -1 and len(cells) > price_idx:
                price = _parse_float(cells[price_idx].get_text(strip=True))

            gmp_data = {}
            if gmp is not None:
                gmp_data["gmp_amount"] = gmp
                if price:
                    gmp_data["gmp_percentage"] = round((gmp / price) * 100, 2)
                    gmp_data["estimated_listing_price"] = price + gmp

            if gmp_data:
                results[norm_name] = gmp_data

    logger.info(f"Scraped InvestorGain GMP data for {len(results)} IPOs")
    return results


async def scrape_gmp_data() -> dict[str, dict]:
    """Scrape GMP data from ipocentral.in/ipo-discussion/ with InvestorGain fallback."""
    html = await _fetch_page(IPOCENTRAL_GMP)
    results = {}
    
    if html:
        soup = BeautifulSoup(html, "html.parser")
        tables = soup.find_all("table")

        for table in tables[:2]:
            rows = table.find_all("tr")
            for row in rows[1:]:
                cells = row.find_all(["td", "th"])
                if len(cells) < 4:
                    continue

                raw_name = cells[0].get_text(strip=True)
                if not raw_name:
                    continue

                company_name = re.sub(r"\(.*?\)\s*$", "", raw_name).strip()
                if not company_name or len(company_name) < 3:
                    continue

                price = _parse_float(cells[1].get_text(strip=True))
                gmp = _parse_float(cells[2].get_text(strip=True))
                gmp_pct = _parse_float(cells[3].get_text(strip=True))

                gmp_data = {}
                if gmp is not None:
                    gmp_data["gmp_amount"] = gmp
                if gmp_pct is not None:
                    gmp_data["gmp_percentage"] = gmp_pct
                if price and gmp is not None:
                    gmp_data["estimated_listing_price"] = price + gmp

                if gmp_data:
                    results[_normalize_name(company_name)] = gmp_data

        logger.info(f"Scraped IPOCentral GMP data for {len(results)} IPOs")

    # Merge with InvestorGain as fallback/supplement
    ig_results = await scrape_investorgain_gmp()
    for name, data in ig_results.items():
        if name not in results:
            results[name] = data
        else:
            # Optionally update missing fields
            for k, v in data.items():
                if k not in results[name] or results[name][k] is None:
                    results[name][k] = v

    return results


async def scrape_listed_ipos() -> list[dict]:
    """Scrape recently listed IPOs from the yearly page."""
    html = await _fetch_page(IPOCENTRAL_YEAR)
    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    results = []

    if not tables:
        return []

    rows = tables[0].find_all("tr")
    for row in rows[1:]:
        cells = row.find_all(["td", "th"])
        if len(cells) < 4:
            continue

        company_name = cells[0].get_text(strip=True)
        listing_date_text = cells[1].get_text(strip=True)
        issue_price = _parse_float(cells[2].get_text(strip=True))
        listing_return = _parse_float(cells[3].get_text(strip=True))

        listing_date = None
        try:
            listing_date = datetime.strptime(listing_date_text, "%m/%d/%Y")
        except (ValueError, TypeError):
            try:
                listing_date = datetime.strptime(listing_date_text, "%d/%m/%Y")
            except (ValueError, TypeError):
                pass

        if not company_name:
            continue

        ipo_data = {
            "company_name": company_name,
            "status": IPOStatus.LISTED,
            "issue_price": issue_price,
            "listing_date": listing_date,
            "ipo_type": IPOType.MAINBOARD,
        }

        if issue_price and listing_return is not None:
            ipo_data["listing_price"] = round(issue_price * (1 + listing_return / 100), 2)

        results.append(ipo_data)

    logger.info(f"Scraped {len(results)} listed IPOs from yearly page")
    return results


# ---------------------------------------------------------------------------
# SOURCE 2: Moneycontrol (Detail pages with rich data)
# ---------------------------------------------------------------------------

async def scrape_moneycontrol_ipo_links() -> list[dict]:
    """
    Scrape the Moneycontrol IPO main page + closed/listed pages
    to get links to individual IPO detail pages.
    Returns a list of {name, url, category}.
    """
    links = []
    pages = [
        (MONEYCONTROL_IPO, "current"),
        (MONEYCONTROL_CLOSED, "closed"),
        (MONEYCONTROL_LISTED, "listed"),
    ]

    for page_url, category in pages:
        html = await _fetch_page(page_url, delay=REQUEST_DELAY)
        if not html:
            continue

        # Strategy 1: BeautifulSoup (more structured)
        soup = BeautifulSoup(html, "html.parser")
        found_on_page = 0

        # Find all anchor tags linking to IPO detail pages
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "ipodetail" in href:
                # Handle relative URLs
                full_url = urljoin(MONEYCONTROL_BASE, href)
                name = a.get_text(separator=" ", strip=True)
                # Clean up name (remove "IPO" suffix if present)
                name = re.sub(r"\s*IPO\s*$", "", name, flags=re.I).strip()
                if name and len(name) > 2:
                    links.append({
                        "name": name,
                        "url": full_url,
                        "category": category,
                    })
                    found_on_page += 1

        # Strategy 2: Regex fallback (sometimes BeautifulSoup misses them if malformed)
        if found_on_page == 0:
            raw_links = re.findall(r'href=["\']([^"\']*ipodetail[^"\']*)', html)
            for rl in raw_links:
                full_url = urljoin(MONEYCONTROL_BASE, rl)
                # Parse name from slug as a fallback
                slug = full_url.split("/")[-1].replace("-ipodetail", "").replace("-", " ").title()
                links.append({
                    "name": slug,
                    "url": full_url,
                    "category": category,
                })
                found_on_page += 1

    # Deduplicate by URL
    seen = set()
    unique_links = []
    for link in links:
        if link["url"] not in seen:
            seen.add(link["url"])
            unique_links.append(link)

    logger.info(f"Found {len(unique_links)} IPO detail links on Moneycontrol")
    return unique_links


async def scrape_moneycontrol_detail(url: str) -> dict:
    """
    Scrape a Moneycontrol IPO detail page and extract all available data:
    - Dates (open, close, allotment, listing)
    - Issue details (issue size, fresh issue, OFS, lot size, face value)
    - Subscription data (QIB, NII, retail, total)
    - Company info (registrar, lead managers, industry)
    - Financial metrics (revenue, profit, EPS, PE, etc.)
    """
    html = await _fetch_page(url, delay=REQUEST_DELAY)
    if not html:
        return {}

    soup = BeautifulSoup(html, "html.parser")
    data = {}

    # Extract text content for pattern matching
    page_text = soup.get_text(separator="\n")

    # --- DATES ---
    date_patterns = {
        "open_date": [r"(?:Opening|Open)\s*(?:date|Date)[:\s]*(\d{1,2}\s+\w+\s+\d{4})", r"Opens?\s*:?\s*(\d{1,2}\s+\w+\s+\d{4})"],
        "close_date": [r"(?:Closing|Close)\s*(?:date|Date)[:\s]*(\d{1,2}\s+\w+\s+\d{4})", r"Closes?\s*:?\s*(\d{1,2}\s+\w+\s+\d{4})"],
        "allotment_date": [r"(?:Basis\s+of\s+)?Allotment[:\s]*(\d{1,2}\s+\w+\s+\d{4})", r"Allotment\s*(?:date|Date)[:\s]*(\d{1,2}\s+\w+\s+\d{4})"],
        "listing_date": [r"(?:Listing|listing)\s*(?:date|Date)[:\s]*(\d{1,2}\s+\w+\s+\d{4})", r"Listing\s*:?\s*(\d{1,2}\s+\w+\s+\d{4})"],
    }

    for field, patterns in date_patterns.items():
        for pattern in patterns:
            match = re.search(pattern, page_text, re.I)
            if match:
                parsed = _parse_mc_date(match.group(1))
                if parsed:
                    data[field] = parsed
                    break

    # --- PRICING ---
    price_patterns = {
        "price_band_lower": [r"(?:Price\s*Band|Price\s*Range)[:\s]*₹?\s*([\d,]+)\s*(?:to|-|–)\s*₹?\s*[\d,]+"],
        "price_band_upper": [r"(?:Price\s*Band|Price\s*Range)[:\s]*₹?\s*[\d,]+\s*(?:to|-|–)\s*₹?\s*([\d,]+)"],
        "face_value": [r"(?:Face\s*Value|FV)[:\s]*₹?\s*([\d,.]+)"],
        "lot_size": [r"(?:Lot\s*Size|Min\.?\s*Lot)[:\s]*([\d,]+)\s*(?:shares|Shares)?"],
        "issue_price": [r"(?:Issue\s*Price|Cut.off\s*Price)[:\s]*₹?\s*([\d,.]+)"],
    }

    for field, patterns in price_patterns.items():
        for pattern in patterns:
            match = re.search(pattern, page_text, re.I)
            if match:
                val = _parse_float(match.group(1))
                if val is not None:
                    if field == "lot_size":
                        data[field] = int(val)
                    else:
                        data[field] = val
                    break

    # --- ISSUE SIZE ---
    size_patterns = {
        "issue_size_rs_cr": [r"(?:Issue\s*Size|Total\s*Issue)[:\s]*₹?\s*([\d,.]+)\s*(?:Cr|crore|cr)", r"Rs\.?\s*([\d,.]+)\s*(?:Cr|crore)"],
        "fresh_issue_size": [r"(?:Fresh\s*Issue)[:\s]*₹?\s*([\d,.]+)\s*(?:Cr|crore|cr)", r"fresh\s*issue\s*of\s*₹?\s*([\d,.]+)\s*(?:Cr|crore)"],
        "offer_for_sale": [r"(?:Offer\s*for\s*Sale|OFS)[:\s]*₹?\s*([\d,.]+)\s*(?:Cr|crore|cr)"],
        "shares_offered": [r"([\d,.]+)\s*(?:crore|cr\.?)\s*shares", r"([\d,.]+)\s*(?:lakh|lac)\s*shares"],
    }

    for field, patterns in size_patterns.items():
        for pattern in patterns:
            match = re.search(pattern, page_text, re.I)
            if match:
                val = _parse_float(match.group(1))
                if val is not None:
                    if field == "shares_offered":
                        # Convert crores/lakhs to actual number
                        if "crore" in match.group(0).lower() or "cr" in match.group(0).lower():
                            data[field] = int(val * 10000000)
                        elif "lakh" in match.group(0).lower() or "lac" in match.group(0).lower():
                            data[field] = int(val * 100000)
                        else:
                            data[field] = int(val)
                    else:
                        data[field] = val
                    break

    # --- SUBSCRIPTION DATA (from tables) ---
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                label = cells[0].get_text(strip=True).lower()
                value_text = cells[-1].get_text(strip=True)

                if "qib" in label or "qualified" in label:
                    val = _parse_float(value_text)
                    if val is not None:
                        data["qib_subscription"] = val
                elif "n" in label and "ii" in label or "non-institutional" in label or "hni" in label:
                    val = _parse_float(value_text)
                    if val is not None:
                        data["nii_subscription"] = val
                elif "retail" in label and "subscription" not in label[:5]:
                    val = _parse_float(value_text)
                    if val is not None:
                        data["retail_subscription"] = val
                elif "total" in label and ("subscription" in label or "times" in value_text.lower()):
                    val = _parse_float(value_text)
                    if val is not None:
                        data["total_subscription"] = val
                elif "registrar" in label:
                    registrar = cells[-1].get_text(strip=True)
                    if registrar and len(registrar) > 2 and registrar != "-":
                        data["registrar"] = registrar
                elif "lead manager" in label or "book running" in label:
                    lm = cells[-1].get_text(strip=True)
                    if lm and len(lm) > 2 and lm != "-":
                        data["lead_managers"] = lm

    # --- COMPANY INFO ---
    # Try to find registrar and lead managers from structured sections
    for dt_tag in soup.find_all(["dt", "strong", "b", "span"]):
        text = dt_tag.get_text(strip=True).lower()
        if "registrar" in text:
            sibling = dt_tag.find_next(["dd", "span", "td", "p"])
            if sibling:
                val = sibling.get_text(strip=True)
                if val and len(val) > 2 and val != "-":
                    data["registrar"] = val
        elif "lead manager" in text or "book running" in text:
            sibling = dt_tag.find_next(["dd", "span", "td", "p"])
            if sibling:
                val = sibling.get_text(strip=True)
                if val and len(val) > 2 and val != "-":
                    data["lead_managers"] = val

    # --- FINANCIAL METRICS ---
    fin_patterns = {
        "pe_ratio": [r"(?:P/?E\s*Ratio|PE\s*Ratio|Price.Earning)[:\s]*([\d,.]+)"],
        "eps": [r"(?:EPS|Earnings\s*Per\s*Share)[:\s]*₹?\s*([\d,.]+)"],
        "roce": [r"(?:ROCE|Return\s*on\s*Capital\s*Employed)[:\s]*([\d,.]+)\s*%?"],
        "roe": [r"(?:ROE|Return\s*on\s*Equity)[:\s]*([\d,.]+)\s*%?"],
        "market_cap_cr": [r"(?:Market\s*Cap)[:\s]*₹?\s*([\d,.]+)\s*(?:Cr|crore)"],
    }

    for field, patterns in fin_patterns.items():
        for pattern in patterns:
            match = re.search(pattern, page_text, re.I)
            if match:
                val = _parse_float(match.group(1))
                if val is not None:
                    data[field] = val
                    break

    # Calculate min_investment if we have lot_size and price_band_upper
    if "lot_size" in data and "price_band_upper" in data:
        data["min_investment"] = data["lot_size"] * data["price_band_upper"]
    elif "lot_size" in data:
        upper = data.get("issue_price") or data.get("price_band_upper")
        if upper:
            data["min_investment"] = data["lot_size"] * upper

    logger.debug(f"Extracted {len(data)} fields from Moneycontrol detail page")
    return data


# ---------------------------------------------------------------------------
# Enrichment Logic
# ---------------------------------------------------------------------------

async def scrape_ipocentral_detail(url: str) -> dict:
    """
    Scrape an IPO Central review/detail page for additional info:
    Registrar, Lead Manager, Face Value, Fresh Issue, OFS, etc.
    """
    html = await _fetch_page(url, delay=REQUEST_DELAY)
    if not html:
        return {}
        
    soup = BeautifulSoup(html, "html.parser")
    data = {}
    
    # IPO Central usually has data in tables
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                label = cells[0].get_text(strip=True).lower()
                value = cells[-1].get_text(strip=True)
                
                if "registrar" in label:
                    data["registrar"] = value
                elif "lead manager" in label or "book running" in label:
                    data["lead_managers"] = value
                elif "face value" in label:
                    data["face_value"] = _parse_float(value)
                elif "fresh issue" in label:
                    data["fresh_issue_size"] = _parse_float(value)
                elif "offer for sale" in label or "ofs" in label:
                    data["offer_for_sale"] = _parse_float(value)
                elif "shares offered" in label:
                    data["shares_offered"] = _parse_int(value)
                elif "lot size" in label:
                    data["lot_size"] = _parse_int(value)
                elif "allotment date" in label or "basis of allotment" in label:
                    dt = _parse_mc_date(value)
                    if dt: data["allotment_date"] = dt
                elif "listing date" in label:
                    dt = _parse_mc_date(value)
                    if dt: data["listing_date"] = dt
                    
    # Also look for subscription data if present in a "Live Subscription" section
    sub_table = soup.find("table", string=re.compile(r"subscription", re.I))
    if not sub_table:
        # Tables with specific classes or nearby headers
        headers = soup.find_all(["h2", "h3", "strong"])
        for h in headers:
            if "subscription" in h.get_text().lower():
                table = h.find_next("table")
                if table:
                    rows = table.find_all("tr")
                    for r in rows:
                        c = r.find_all(["td", "th"])
                        if len(c) >= 2:
                            lab = c[0].get_text().lower()
                            val = c[-1].get_text()
                            if "qib" in lab: data["qib_subscription"] = _parse_float(val)
                            elif "nii" in lab or "hni" in lab: data["nii_subscription"] = _parse_float(val)
                            elif "retail" in lab: data["retail_subscription"] = _parse_float(val)
                            elif "total" in lab: data["total_subscription"] = _parse_float(val)
                            
    return data


def _count_missing_fields(ipo: IPO) -> list[str]:
    """Return a list of field names that are None/empty for the given IPO."""
    fields_to_check = [
        "allotment_date", "listing_date", "issue_price", "listing_price",
        "fresh_issue_size", "offer_for_sale", "shares_offered", "face_value",
        "qib_subscription", "nii_subscription", "retail_subscription", "total_subscription",
        "gmp_amount", "gmp_percentage",
        "industry_sector", "registrar", "lead_managers",
        "pe_ratio", "roce", "roe", "eps", "market_cap_cr",
        "lot_size", "min_investment",
    ]
    missing = []
    for f in fields_to_check:
        val = getattr(ipo, f, None)
        if val is None:
            missing.append(f)
    return missing


def _name_words(name: str) -> set[str]:
    """Extract significant words from a company name for matching."""
    stop = {"ltd", "limited", "pvt", "private", "inc", "corp", "corporation",
            "india", "the", "of", "and", "&", "ipo"}
    words = re.sub(r"[^a-z0-9\s]", " ", name.lower()).split()
    return {w for w in words if w not in stop and len(w) > 1}


def _match_score(name_a: str, name_b: str) -> float:
    """Calculate word-overlap matching score between two company names (0.0–1.0)."""
    words_a = _name_words(name_a)
    words_b = _name_words(name_b)
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    # Jaccard-like: overlap relative to the *smaller* set
    return len(intersection) / min(len(words_a), len(words_b))


async def enrich_from_moneycontrol(db: Session, ipo: IPO, mc_links: list[dict]) -> dict:
    """
    Try to find and scrape the Moneycontrol detail page for a given IPO,
    then update the database with any new data found.
    Returns a dict summarizing what was updated.
    """
    detail_url = None
    best_score = 0.0

    # Strategy 1: Exact normalized match
    norm_name = _normalize_name(ipo.company_name)
    for link in mc_links:
        link_norm = _normalize_name(link["name"])
        if norm_name == link_norm:
            detail_url = link["url"]
            break

    # Strategy 2: Word-token overlap (>= 60% of words match)
    if not detail_url:
        for link in mc_links:
            score = _match_score(ipo.company_name, link["name"])
            if score > best_score:
                best_score = score
                if score >= 0.6:
                    detail_url = link["url"]

    # Strategy 3: URL slug matching
    if not detail_url:
        ipo_words = _name_words(ipo.company_name)
        for link in mc_links:
            slug = link["url"].lower().split("/")[-1]
            slug_words = set(re.sub(r"[^a-z0-9\s]", " ", slug).split())
            overlap = ipo_words & slug_words
            if len(overlap) >= 2 or (len(ipo_words) <= 2 and len(overlap) >= 1):
                detail_url = link["url"]
                break

    detail_data = {}
    source_name = "none"

    if detail_url:
        detail_data = await scrape_moneycontrol_detail(detail_url)
        source_name = f"moneycontrol:{detail_url.split('/')[-1][:50]}"

    # Strategy 4: Fallback to IPO Central detail URL if we had one from homepage
    if not detail_data and hasattr(ipo, "detail_url") and ipo.detail_url:
        detail_data = await scrape_ipocentral_detail(ipo.detail_url)
        source_name = "ipocentral:detail"

    if not detail_data:
        return {"status": "no_match", "fields_updated": 0}

    # Update only fields that are currently None
    fields_updated = 0
    for field, value in detail_data.items():
        if value is not None:
            current_val = getattr(ipo, field, None)
            if current_val is None:
                setattr(ipo, field, value)
                fields_updated += 1

    # Update status based on new date info
    if fields_updated > 0:
        new_status = _determine_status(ipo.open_date, ipo.close_date, ipo.listing_date)
        if new_status != ipo.status:
            ipo.status = new_status

        ipo.data_source = source_name
        ipo.last_enriched_at = datetime.now()
        db.commit()

    return {"status": "enriched", "fields_updated": fields_updated, "url": detail_url or ipo.detail_url}


# ---------------------------------------------------------------------------
# Main sync logic
# ---------------------------------------------------------------------------

def _find_existing_ipo(db: Session, company_name: str) -> Optional[IPO]:
    """Find an existing IPO by normalized company name."""
    norm = _normalize_name(company_name)
    all_ipos = db.query(IPO).all()
    for ipo in all_ipos:
        if _normalize_name(ipo.company_name) == norm:
            return ipo
        cn = _normalize_name(ipo.company_name)
        if len(norm) > 5 and len(cn) > 5 and (norm in cn or cn in norm):
            return ipo
    return None


async def sync_ipos(db: Session) -> dict:
    """
    Main sync function: scrape all sources and upsert into database.
    Returns a summary dict with counts.
    """
    summary = {"added": 0, "updated": 0, "enriched": 0, "errors": 0, "total_scraped": 0}

    # Step 1: Scrape upcoming/open IPOs from homepage
    upcoming_ipos = await scrape_homepage()

    # Step 2: Scrape GMP data
    gmp_data = await scrape_gmp_data()

    # Step 3: Scrape recently listed IPOs
    listed_ipos = await scrape_listed_ipos()

    # Combine all IPO data
    all_ipos = upcoming_ipos + listed_ipos
    summary["total_scraped"] = len(all_ipos)

    if not all_ipos:
        logger.warning("No IPO data scraped — source may be unavailable")
        return summary

    # Step 4: Enrich with GMP data
    for ipo_info in all_ipos:
        norm_name = _normalize_name(ipo_info["company_name"])
        if norm_name in gmp_data:
            ipo_info.update(gmp_data[norm_name])
        else:
            for gmp_name, gmp_vals in gmp_data.items():
                if len(norm_name) > 5 and len(gmp_name) > 5:
                    if norm_name in gmp_name or gmp_name in norm_name:
                        ipo_info.update(gmp_vals)
                        break

    # Step 5: Upsert into database
    for ipo_info in all_ipos:
        try:
            company_name = ipo_info["company_name"]
            existing = _find_existing_ipo(db, company_name)

            if existing:
                for field, value in ipo_info.items():
                    if field == "company_name":
                        continue
                    if value is not None:
                        setattr(existing, field, value)
                existing.updated_at = datetime.now()
                db.commit()
                summary["updated"] += 1
            else:
                symbol = _generate_symbol(company_name)
                counter = 1
                base_symbol = symbol
                while db.query(IPO).filter(IPO.symbol == symbol).first():
                    symbol = f"{base_symbol}{counter}"
                    counter += 1

                ipo_info_copy = {k: v for k, v in ipo_info.items()}
                ipo_info_copy["symbol"] = symbol
                new_ipo = IPO(**ipo_info_copy)
                db.add(new_ipo)
                db.commit()
                summary["added"] += 1

        except Exception as e:
            db.rollback()
            logger.error(f"Error upserting IPO '{ipo_info.get('company_name', '?')}': {e}")
            summary["errors"] += 1
            continue

    # Step 6: Enrich all IPOs from Moneycontrol detail pages
    try:
        logger.info("Fetching Moneycontrol IPO links...")
        mc_links = await scrape_moneycontrol_ipo_links()

        if mc_links:
            all_db_ipos = db.query(IPO).all()
            # Priority: open > closed > upcoming > listed
            priority_order = {
                IPOStatus.OPEN: 0,
                IPOStatus.CLOSED: 1,
                IPOStatus.UPCOMING: 2,
                IPOStatus.LISTED: 3,
            }
            sorted_ipos = sorted(all_db_ipos, key=lambda x: priority_order.get(x.status, 4))

            for ipo in sorted_ipos:
                missing = _count_missing_fields(ipo)
                if len(missing) < 3:
                    continue  # Skip if mostly complete

                try:
                    result = await enrich_from_moneycontrol(db, ipo, mc_links)
                    if result["fields_updated"] > 0:
                        summary["enriched"] += 1
                        logger.info(f"Enriched '{ipo.company_name}': {result['fields_updated']} fields")
                except Exception as e:
                    logger.error(f"Error enriching '{ipo.company_name}': {e}")
                    summary["errors"] += 1

    except Exception as e:
        logger.error(f"Moneycontrol enrichment failed: {e}")
        logger.warning(f"Moneycontrol enrichment failed (non-critical): {e}")

    logger.info(
        f"IPO sync complete: {summary['added']} added, "
        f"{summary['updated']} updated, {summary['enriched']} enriched, "
        f"{summary['errors']} errors"
    )
    return summary
