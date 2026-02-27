"""
Real-time Indian IPO Data Scraper
Scrapes live IPO data from ipocentral.in (server-rendered HTML)
Sources:
  - Homepage: upcoming IPOs with dates, price bands, issue sizes
  - GMP page: Grey Market Premium data
  - Yearly page: listing returns for recently listed IPOs
"""

import re
import logging
from datetime import datetime
from typing import Optional

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.models.ipo import IPO, IPOStatus, IPOType

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

IPOCENTRAL_HOME = "https://ipocentral.in/"
IPOCENTRAL_GMP = "https://ipocentral.in/ipo-discussion/"
IPOCENTRAL_YEAR = "https://ipocentral.in/ipo-2026/"


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _parse_float(text: str) -> Optional[float]:
    """Safely extract a float from text like '₹1,287', '15.25%', '(2)', etc."""
    if not text:
        return None
    cleaned = text.strip()
    # Handle parenthesized negatives like '(10)' -> '-10'
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
    """
    Parse IPO date ranges like '25 – 27 Feb', '27 Feb – 4 Mar', '4 - 6 Mar'.
    Returns (open_date, close_date).
    """
    if not text or text.strip() in ("-", "", "NA", "Coming soon"):
        return None, None

    if year is None:
        year = datetime.now().year

    text = text.strip()
    # Normalize dashes
    text = text.replace("–", "-").replace("—", "-")

    # Try to split on dash
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

    # If open part has no month, inherit from close
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


async def _fetch_page(url: str) -> Optional[str]:
    """Fetch a web page with error handling."""
    try:
        async with httpx.AsyncClient(
            headers=HEADERS, timeout=30.0, follow_redirects=True
        ) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None


# ---------------------------------------------------------------------------
# Scrapers
# ---------------------------------------------------------------------------

async def scrape_homepage() -> list[dict]:
    """
    Scrape the IPO Central homepage for upcoming IPOs.
    Tables 0 and 1 have: [Company Name, IPO Dates, Price (INR), Size (INR Cr.)]
    """
    html = await _fetch_page(IPOCENTRAL_HOME)
    if not html:
        return []

    soup = BeautifulSoup(html, "lxml")
    tables = soup.find_all("table")
    results = []

    for table_idx in range(min(2, len(tables))):
        table = tables[table_idx]
        rows = table.find_all("tr")
        is_sme = table_idx == 1  # Table 1 is SME

        for row in rows[1:]:  # skip header
            cells = row.find_all(["td", "th"])
            if len(cells) < 4:
                continue

            company_name = cells[0].get_text(strip=True)
            if not company_name or "More" in company_name:
                continue

            date_text = cells[1].get_text(strip=True)
            price_text = cells[2].get_text(strip=True)
            size_text = cells[3].get_text(strip=True)

            # Parse price band (e.g., '1,287 – 1,352')
            price_parts = re.split(r"[–\-]", price_text)
            price_lower = _parse_float(price_parts[0]) if len(price_parts) >= 2 else None
            price_upper = _parse_float(price_parts[-1]) if price_parts else None

            # Parse dates
            open_date, close_date = _parse_date_range(date_text)

            # Parse issue size
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
            }

            # Calculate lot size & min investment estimate
            if price_upper and price_upper > 0:
                # Standard lot size estimation: ~₹15,000 / upper price
                estimated_lot = max(1, round(15000 / price_upper))
                ipo_data["lot_size"] = estimated_lot
                ipo_data["min_investment"] = estimated_lot * price_upper

            results.append(ipo_data)

    logger.info(f"Scraped {len(results)} IPOs from IPO Central homepage")
    return results


async def scrape_gmp_data() -> dict[str, dict]:
    """
    Scrape GMP data from ipocentral.in/ipo-discussion/
    Tables have: [IPO Name (with dates), Price, IPO GMP, GMP %, Subject to]
    Returns dict keyed by normalized company name.
    """
    html = await _fetch_page(IPOCENTRAL_GMP)
    if not html:
        return {}

    soup = BeautifulSoup(html, "lxml")
    tables = soup.find_all("table")
    results = {}

    for table in tables[:2]:  # Table 0 = Mainboard, Table 1 = SME
        rows = table.find_all("tr")
        for row in rows[1:]:  # skip header
            cells = row.find_all(["td", "th"])
            if len(cells) < 4:
                continue

            raw_name = cells[0].get_text(strip=True)
            if not raw_name:
                continue

            # Name contains dates in parens like 'Sedemac Mechatronics(4 - 6 Mar)'
            # Remove the date portion
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

    logger.info(f"Scraped GMP data for {len(results)} IPOs")
    return results


async def scrape_listed_ipos() -> list[dict]:
    """
    Scrape recently listed IPOs from the yearly page.
    Table 0 has: [IPO Name, Listing Date, Allotment Price, Listing Return %]
    """
    html = await _fetch_page(IPOCENTRAL_YEAR)
    if not html:
        return []

    soup = BeautifulSoup(html, "lxml")
    tables = soup.find_all("table")
    results = []

    if not tables:
        return []

    # Table 0: recently listed IPOs
    rows = tables[0].find_all("tr")
    for row in rows[1:]:  # skip header
        cells = row.find_all(["td", "th"])
        if len(cells) < 4:
            continue

        company_name = cells[0].get_text(strip=True)
        listing_date_text = cells[1].get_text(strip=True)
        issue_price = _parse_float(cells[2].get_text(strip=True))
        listing_return = _parse_float(cells[3].get_text(strip=True))

        # Parse listing date (format: 2/27/2026)
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

        # Calculate listing price from return percentage
        if issue_price and listing_return is not None:
            ipo_data["listing_price"] = round(issue_price * (1 + listing_return / 100), 2)

        results.append(ipo_data)

    logger.info(f"Scraped {len(results)} listed IPOs from yearly page")
    return results


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
        # Partial match for abbreviated names
        cn = _normalize_name(ipo.company_name)
        if len(norm) > 5 and len(cn) > 5 and (norm in cn or cn in norm):
            return ipo
    return None


async def sync_ipos(db: Session) -> dict:
    """
    Main sync function: scrape all sources and upsert into database.
    Returns a summary dict with counts.
    """
    summary = {"added": 0, "updated": 0, "errors": 0, "total_scraped": 0}

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
            # Try partial match
            for gmp_name, gmp_vals in gmp_data.items():
                if len(norm_name) > 5 and len(gmp_name) > 5:
                    if norm_name in gmp_name or gmp_name in norm_name:
                        ipo_info.update(gmp_vals)
                        break

    # Step 5: Upsert into database (commit per IPO to avoid one error killing all)
    for ipo_info in all_ipos:
        try:
            company_name = ipo_info["company_name"]
            existing = _find_existing_ipo(db, company_name)

            if existing:
                # Update existing IPO with fresh data
                for field, value in ipo_info.items():
                    if field == "company_name":
                        continue
                    if value is not None:
                        setattr(existing, field, value)
                existing.updated_at = datetime.now()
                db.commit()
                summary["updated"] += 1
            else:
                # Create new IPO
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
            print(f"  ❌ Error upserting '{ipo_info.get('company_name', '?')}': {e}")
            summary["errors"] += 1
            continue

    logger.info(
        f"IPO sync complete: {summary['added']} added, "
        f"{summary['updated']} updated, {summary['errors']} errors"
    )
    return summary

