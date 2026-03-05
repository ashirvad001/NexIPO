import os
import re
import time
import logging
import asyncio
from typing import Optional, Dict
from pathlib import Path
import tempfile
import traceback

import httpx
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pdfplumber

from app.db.database import SessionLocal
from app.models.ipo import IPO
from app.services.file_service import FileService

logger = logging.getLogger(__name__)

class RHPDownloader:
    """
    Automated RHP PDF downloader for IPOs
    Searches various authoritative sources to find, download, and store RHP documents.
    """
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        }
    
    def _get_selenium_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
        
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver

    def normalize_name(self, name: str) -> str:
        """Strip 'Limited', 'Ltd', 'IPO' to get a clean search term."""
        name = re.sub(r'(?i)\b(limited|ltd|ipo)\b', '', name)
        return re.sub(r'[^a-zA-Z0-9]', '', name).strip().lower()

    async def download_from_chittorgarh(self, company_name: str, download_dir: str) -> Optional[str]:
        """Try to find the RHP link on Chittorgarh, which consolidates links."""
        try:
            search_query = company_name.replace(" ", "+")
            search_url = f"https://www.chittorgarh.com/search.asp?q={search_query}"
            
            async with httpx.AsyncClient(headers=self.headers, follow_redirects=True, timeout=30) as client:
                r = await client.get(search_url)
                soup = BeautifulSoup(r.text, 'html.parser')
                
                # Find the first IPO link
                ipo_link = None
                for a in soup.find_all('a', href=True):
                    if '/ipo/' in a['href'] and 'review' not in a['href']:
                        ipo_link = a['href']
                        break
                        
                if not ipo_link:
                    return None
                    
                # Ensure absolute URL
                if not ipo_link.startswith('http'):
                    ipo_link = f"https://www.chittorgarh.com{ipo_link}"
                    
                # Fetch IPO page to find Document/RHP links
                ipo_r = await client.get(ipo_link)
                ipo_soup = BeautifulSoup(ipo_r.text, 'html.parser')
                
                pdf_url = None
                for a in ipo_soup.find_all('a', href=True):
                    text = a.get_text().lower()
                    if 'rhp' in text or 'red herring' in text or 'prospectus' in text:
                        if a['href'].endswith('.pdf'):
                            pdf_url = a['href']
                            break
                            
                if not pdf_url:
                    return None
                    
                if not pdf_url.startswith('http'):
                    pdf_url = f"https://www.chittorgarh.com{pdf_url}"
                
                # Auto-download the PDF
                return await self._download_pdf_httpx(client, pdf_url, company_name, download_dir)

        except Exception as e:
            logger.warning(f"Chittorgarh download failed for {company_name}: {e}")
            return None

    def download_from_sebi(self, company_name: str, download_dir: str) -> Optional[str]:
        """Use Selenium to search SEBI's portal for the RHP/DRHP."""
        driver = None
        try:
            driver = self._get_selenium_driver()
            # SEBI Public Issues page
            driver.get("https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=3&ssid=15&smid=10")
            
            # Wait for search box
            search_box = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "search")) # Or matching input
            )
            
            clean_name = re.sub(r'(?i)\b(limited|ltd|ipo)\b', '', company_name).strip()
            
            search_box.send_keys(clean_name)
            # Find and click search button
            go_btn = driver.find_element(By.XPATH, "//a[contains(text(), 'Go')]")
            if not go_btn:
                go_btn = driver.find_element(By.CSS_SELECTOR, ".search-btn")
            go_btn.click()
            
            time.sleep(3) # Wait for table refresh
            
            # Find PDF links
            links = driver.find_elements(By.XPATH, "//a[contains(@href, '.pdf')]")
            for link in links:
                href = link.get_attribute('href')
                text = link.text.lower()
                if 'rhp' in text or 'red herring' in text or 'prospectus' in text:
                    # Download this PDF
                    pdf_url = href
                    return self._download_pdf_sync(pdf_url, company_name, download_dir)
                    
            return None
        except Exception as e:
            logger.warning(f"SEBI download failed for {company_name}: {e}")
            return None
        finally:
            if driver:
                driver.quit()

    async def _download_pdf_httpx(self, client: httpx.AsyncClient, url: str, name: str, download_dir: str) -> Optional[str]:
        safe_name = re.sub(r'[^a-zA-Z0-9]', '_', name).strip('_')
        file_path = os.path.join(download_dir, f"{safe_name}_RHP.pdf")
        
        try:
            async with client.stream('GET', url) as response:
                if response.status_code == 200:
                    with open(file_path, 'wb') as f:
                        async for chunk in response.aiter_bytes():
                            f.write(chunk)
                    return file_path
            return None
        except Exception:
            return None

    def _download_pdf_sync(self, url: str, name: str, download_dir: str) -> Optional[str]:
        safe_name = re.sub(r'[^a-zA-Z0-9]', '_', name).strip('_')
        file_path = os.path.join(download_dir, f"{safe_name}_RHP.pdf")
        try:
            r = httpx.get(url, headers=self.headers, follow_redirects=True, timeout=30)
            if r.status_code == 200:
                with open(file_path, 'wb') as f:
                    f.write(r.content)
                return file_path
            return None
        except Exception as e:
            logger.warning(f"Sync download failed: {e}")
            return None

    def verify_pdf(self, file_path: str) -> bool:
        """Verify PDF is valid and not corrupted"""
        if not os.path.exists(file_path):
            return False
            
        if os.path.getsize(file_path) < 10000:  # Less than 10KB is likely not an RHP
            return False
            
        try:
            with pdfplumber.open(file_path) as pdf:
                pages = len(pdf.pages)
                if pages > 0:
                    return True
        except Exception:
            return False
        return False

    def extract_metadata(self, file_path: str) -> dict:
        """Extract PDF metadata"""
        try:
            with pdfplumber.open(file_path) as pdf:
                return {
                    "page_count": len(pdf.pages),
                    "file_size_mb": round(os.path.getsize(file_path) / (1024 * 1024), 2)
                }
        except Exception:
            return {}

    async def upload_to_platform(self, file_path: str, ipo_id: int):
        """Upload to platform via existing FileService API"""
        from fastapi import UploadFile
        
        # We need to simulate a FastAPI UploadFile to pass to our internal FileService
        # This allows us to reuse all the mongo text extraction logic cleanly
        filename = os.path.basename(file_path)
        
        try:
            with open(file_path, "rb") as f:
                # Create a simple mock that FileService accepts
                class MockUploadFile(UploadFile):
                    def __init__(self, filename, file_obj):
                        self.filename = filename
                        self.file = file_obj
                        self.content_type = "application/pdf"
                        
                    async def read(self, size=-1):
                        return self.file.read(size)
                        
                    async def seek(self, offset):
                        self.file.seek(offset)
                        
                mock_file = MockUploadFile(filename, f)
                result = await FileService.upload_prospectus(ipo_id, mock_file)
                
                # Also update IPO
                db = SessionLocal()
                try:
                    ipo = db.query(IPO).filter(IPO.id == ipo_id).first()
                    if ipo and result.get("file_id"):
                        ipo.prospectus_file_id = result["file_id"]
                        db.commit()
                finally:
                    db.close()
                    
                return result
        except Exception as e:
            logger.error(f"Internal upload failed: {e}")
            logger.error(traceback.format_exc())
            return None

    async def process_ipo(self, ipo: IPO, download_dir: str) -> dict:
        """Process a single IPO."""
        log_result = {
            "ipo_id": ipo.id,
            "company": ipo.company_name,
            "status": "failed",
            "source": None,
            "error": None
        }
        
        # 1. Try Chittorgarh
        pdf_path = await self.download_from_chittorgarh(ipo.company_name, download_dir)
        source = "Chittorgarh"
        
        # 2. Try SEBI (Fallback)
        if not pdf_path:
            # Wrap synchronous Selenium scraper in a thread to avoid blocking the event loop
            pdf_path = await asyncio.to_thread(self.download_from_sebi, ipo.company_name, download_dir)
            source = "SEBI"
            
        if not pdf_path:
            log_result["error"] = "Not found on any portal"
            return log_result
            
        # Verify
        if not self.verify_pdf(pdf_path):
            log_result["error"] = "Downloaded PDF corrupted or too small"
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            return log_result
            
        # Metadata
        meta = self.extract_metadata(pdf_path)
        log_result["pages"] = meta.get("page_count", 0)
        log_result["size_mb"] = meta.get("file_size_mb", 0)
        
        # Upload
        upload_res = await self.upload_to_platform(pdf_path, ipo.id)
        if upload_res:
            log_result["status"] = "success"
            log_result["source"] = source
            
        # Cleanup temp file
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            
        return log_result
