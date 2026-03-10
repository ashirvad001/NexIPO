import os
import sys
import time
import json
import logging
from datetime import datetime, timedelta
import schedule
import httpx
import yfinance as yf
from bs4 import BeautifulSoup

# Setup paths so we can import models and database
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.models.ipo import IPO, IPOStatus
from app.models.gmp_history import GMPHistory

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - [LIVE UPDATER] - %(message)s")
logger = logging.getLogger(__name__)

# FastAPI internal webhook for triggering WebSocket broadcasts
WEBHOOK_URL = "http://localhost:8000/api/v1/ws/internal-broadcast"

class RealTimeUpdater:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def broadcast_update(self, payload: dict):
        """Sends data to FastAPI so it can be broadcasted to all connected WebSockets."""
        try:
            r = httpx.post(WEBHOOK_URL, json=payload, timeout=5)
            if r.status_code != 200:
                logger.warning(f"Failed to broadcast update: {r.text}")
        except Exception as e:
            logger.warning(f"Webhook broadcast failed (is FastAPI running?): {e}")

    def update_stock_prices(self):
        """Runs every 1 minute. Fetches live pricing from Yahoo Finance."""
        logger.info("Running stock price update...")
        db = SessionLocal()
        try:
            # We only care about listed IPOs for stock prices
            listed_ipos = db.query(IPO).filter(IPO.status == IPOStatus.LISTED).all()
            if not listed_ipos:
                return

            symbols = []
            for ipo in listed_ipos:
                if ipo.symbol:
                    # Append .NS for NSE tokens in yfinance
                    symbol = f"{ipo.symbol}.NS"
                    symbols.append(symbol)

            if not symbols:
                return

            # Batch download from Yahoo Finance
            data = yf.download(symbols, period="1d", interval="1m", progress=False)
            if data.empty:
                return

            for ipo in listed_ipos:
                if not ipo.symbol:
                    continue
                    
                symbol = f"{ipo.symbol}.NS"
                try:
                    # yfinance returns varied shapes depending on single vs multi ticker
                    if len(symbols) == 1:
                        current_price = float(data['Close'].iloc[-1])
                    else:
                        current_price = float(data['Close'][symbol].iloc[-1])
                        
                    if not current_price or current_price != current_price: # check for NaN
                        continue
                        
                    # Update DB if price changed
                    if abs(ipo.current_price or 0 - current_price) > 0.01:
                        ipo.current_price = round(current_price, 2)
                        
                        # Broadcast
                        self.broadcast_update({
                            "type": "price_update",
                            "ipo_id": ipo.id,
                            "symbol": ipo.symbol,
                            "current_price": ipo.current_price
                        })
                except Exception as e:
                    pass
            db.commit()
        except Exception as e:
            logger.error(f"Error updating stock prices: {e}")
        finally:
            db.close()

    def update_subscription_data(self):
        """Runs every 5 minutes during market hours."""
        logger.info("Running live subscription update...")
        db = SessionLocal()
        try:
            open_ipos = db.query(IPO).filter(IPO.status == IPOStatus.OPEN).all()
            for ipo in open_ipos:
                if not ipo.detail_url:
                    continue
                    
                # Scrape Moneycontrol detail page again for live subscription values
                try:
                    r = httpx.get(ipo.detail_url, headers=self.headers, timeout=15)
                    if r.status_code == 200:
                        soup = BeautifulSoup(r.text, 'html.parser')
                        # Searching for the subscription table 
                        # This relies on the table structure holding QIB, NII, Retail
                        sub_table = soup.find('table', class_='flR')
                        if not sub_table:
                            continue
                            
                        changed = False
                        rows = sub_table.find_all('tr')
                        for row in rows:
                            cols = row.find_all('td')
                            if len(cols) >= 2:
                                label = cols[0].text.strip().lower()
                                value_str = cols[1].text.replace('x', '').strip()
                                
                                try:
                                    val = float(value_str)
                                    if 'qib' in label and ipo.qib_subscription != val:
                                        ipo.qib_subscription = val
                                        changed = True
                                    elif 'nii' in label and ipo.nii_subscription != val:
                                        ipo.nii_subscription = val
                                        changed = True
                                    elif 'retail' in label and ipo.retail_subscription != val:
                                        ipo.retail_subscription = val
                                        changed = True
                                    elif 'total' in label and ipo.total_subscription != val:
                                        ipo.total_subscription = val
                                        changed = True
                                except ValueError:
                                    pass
                                    
                        if changed:
                            ipo.updated_at = datetime.utcnow()
                            db.commit()
                            self.broadcast_update({
                                "type": "subscription_update",
                                "ipo_id": ipo.id,
                                "qib": ipo.qib_subscription,
                                "nii": ipo.nii_subscription,
                                "retail": ipo.retail_subscription,
                                "total": ipo.total_subscription
                            })
                except Exception as e:
                    logger.warning(f"Failed subscription scrape for {ipo.company_name}: {e}")
        finally:
            db.close()

    def update_gmp(self):
        """Runs every 30 minutes to record historical GMP."""
        logger.info("Running GMP update...")
        db = SessionLocal()
        try:
            upcoming_and_open = db.query(IPO).filter(IPO.status.in_([IPOStatus.UPCOMING, IPOStatus.OPEN])).all()
            
            # Scrape Investorgain for GMP
            try:
                r = httpx.get('https://www.investorgain.com/report/live-ipo-gmp/331/camp/', headers=self.headers, timeout=15)
                if r.status_code == 200:
                    soup = BeautifulSoup(r.text, 'html.parser')
                    tables = soup.find_all('table')
                    
                    gmp_scraped = {}
                    if tables:
                        # Robust table selection: Find table with 'GMP' and 'Name' in headers
                        target_table = None
                        for table in tables:
                            header_row = table.find('tr')
                            if header_row:
                                headers = [th.get_text(strip=True).lower() for th in header_row.find_all(['th', 'td'])]
                                if 'gmp' in headers and 'name' in headers:
                                    target_table = table
                                    break
                        
                        if not target_table:
                            target_table = tables[0] # Fallback
                            
                        rows = target_table.find_all('tr')[1:] # skip header
                        for row in rows:
                            cols = row.find_all('td')
                            if len(cols) > 4:
                                # Index 0: Name, Index 1: GMP, Index 4: Price
                                name_cell = cols[0].get_text(strip=True)
                                # Clean name
                                clean_name = name_cell.replace('IPO', '').replace('Limited', '').replace('Ltd', '').strip().lower()
                                
                                gmp_cell = cols[1].get_text(strip=True)
                                try:
                                    # Extract number from "₹ 45 (10%)" or similar
                                    # Handle negative or zero
                                    if 'fixed' in gmp_cell.lower() or '--' in gmp_cell:
                                        gmp_val = 0.0
                                    else:
                                        # Match potential decimal or integer
                                        match = re.search(r'₹?\s*(-?\d+\.?\d*)', gmp_cell)
                                        if match:
                                            gmp_val = float(match.group(1))
                                        else:
                                            gmp_val = 0.0
                                    
                                    gmp_scraped[clean_name] = gmp_val
                                except:
                                    pass
                                    
                    # Now match against our database
                    for ipo in upcoming_and_open:
                        search_name = ipo.company_name.lower().split(' limited')[0].split(' ltd')[0].strip()
                        
                        # Find closest match
                        matched_gmp = None
                        for s_name, gmp_val in gmp_scraped.items():
                            if search_name in s_name or s_name in search_name:
                                matched_gmp = gmp_val
                                break
                                
                        if matched_gmp is not None:
                            # Add to history
                            history = GMPHistory(ipo_id=ipo.id, gmp_amount=matched_gmp)
                            db.add(history)
                            
                            # Update current tracking
                            if ipo.gmp_amount != matched_gmp:
                                ipo.gmp_amount = matched_gmp
                                ipo.updated_at = datetime.utcnow()
                                
                                self.broadcast_update({
                                    "type": "gmp_update",
                                    "ipo_id": ipo.id,
                                    "gmp_amount": matched_gmp
                                })
            except Exception as e:
                logger.error(f"Investorgain GMP scrape failed: {e}")
                
            db.commit()
        except Exception as e:
            logger.error(f"Error in GMP update: {e}")
        finally:
            db.close()

    def run(self):
        """Start the scheduler loops."""
        logger.info("Initializing Real-Time IPO Updater Service...")
        
        schedule.every(1).minutes.do(self.update_stock_prices)
        schedule.every(5).minutes.do(self.update_subscription_data)
        schedule.every(30).minutes.do(self.update_gmp)
        
        # Fire initial runs right away
        self.update_stock_prices()
        self.update_subscription_data()
        self.update_gmp()

        logger.info("Scheduler started successfully. Polling loop active.")
        while True:
            try:
                schedule.run_pending()
                time.sleep(1)
            except KeyboardInterrupt:
                logger.info("Shutting down updater...")
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                time.sleep(10) # backoff on crash

if __name__ == "__main__":
    updater = RealTimeUpdater()
    updater.run()
