import pytest
from bs4 import BeautifulSoup
import re

# Mock the logic for table selection and scraping
def simulate_gmp_scrape(html):
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
    
    if target_table:
        header_row = target_table.find('tr')
        headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
        
        name_idx = headers.index('name')
        gmp_idx = headers.index('gmp')
        price_idx = next((i for i, h in enumerate(headers) if 'price' in h), -1)

        rows = target_table.find_all("tr")
        for row in rows[1:]:
            cells = row.find_all(["td", "th"])
            
            raw_name = cells[name_idx].get_text(strip=True)
            company_name = re.sub(r"\(.*?\)\s*$", "", raw_name).strip()
            
            gmp_text = cells[gmp_idx].get_text(strip=True)
            gmp_match = re.search(r'-?\d+\.?\d*', gmp_text.replace(',', ''))
            gmp = float(gmp_match.group(0)) if gmp_match else 0.0
            
            price = 0.0
            if price_idx != -1:
                price_text = cells[price_idx].get_text(strip=True)
                p_match = re.search(r'\d+\.?\d*', price_text.replace(',', ''))
                price = float(p_match.group(0)) if p_match else 0.0

            results[company_name] = {"gmp": gmp, "price": price}
            
    return results

def test_robust_table_selection():
    html = """
    <html>
    <table><tr><td>Ad Header</td></tr><tr><td>Leaderboard</td></tr></table>
    <div class="data-table-wrapper">
        <table>
            <tr><th>Name</th><th>GMP</th><th>Rating</th><th>Sub</th><th>Price (₹)</th></tr>
            <tr><td>Novus Loyalty</td><td>₹ 45 (10%)</td><td>5</td><td>2x</td><td>450</td></tr>
            <tr><td>Skyways Air</td><td>₹ 100</td><td>4</td><td>1x</td><td>1000</td></tr>
        </table>
    </div>
    </html>
    """
    results = simulate_gmp_scrape(html)
    assert "Novus Loyalty" in results
    assert results["Novus Loyalty"]["gmp"] == 45.0
    assert results["Novus Loyalty"]["price"] == 450.0
    assert results["Skyways Air"]["gmp"] == 100.0

def test_negative_gmp():
    html = """
    <table>
        <tr><th>Name</th><th>GMP</th><th>Price (₹)</th></tr>
        <tr><td>Risky IPO</td><td>₹ -10 (-5%)</td><td>200</td></tr>
    </table>
    """
    results = simulate_gmp_scrape(html)
    assert results["Risky IPO"]["gmp"] == -10.0

if __name__ == "__main__":
    pytest.main([__file__])
