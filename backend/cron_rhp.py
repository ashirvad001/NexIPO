import asyncio
import argparse
import sys
import os
import logging
from datetime import datetime

# Setup path so we can import 'app'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.models.ipo import IPO
from app.services.rhp_downloader import RHPDownloader

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

async def main():
    parser = argparse.ArgumentParser(description="Automated RHP Downloader for IPOs")
    parser.add_argument("--ipo-id", type=int, help="Download RHP for a specific IPO ID")
    parser.add_argument("--all-missing", action="store_true", help="Download RHPs for all IPOs missing a prospectus")
    args = parser.parse_args()
    
    db = SessionLocal()
    target_ipos = []
    
    try:
        if args.ipo_id:
            ipo = db.query(IPO).filter(IPO.id == args.ipo_id).first()
            if ipo:
                if ipo.prospectus_file_id:
                    logger.info(f"IPO {ipo.company_name} already has a prospectus.")
                    return
                target_ipos = [ipo]
            else:
                logger.error(f"IPO ID {args.ipo_id} not found.")
                return
        elif args.all_missing:
            target_ipos = db.query(IPO).filter(IPO.prospectus_file_id == None).all()
        else:
            parser.print_help()
            return
            
        if not target_ipos:
            logger.info("No IPOs need downloading.")
            return
            
        logger.info(f"Starting RHP Download for {len(target_ipos)} IPOs...")
        downloader = RHPDownloader()
        
        # Ensure temporary directory
        download_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tmp_downloads")
        os.makedirs(download_dir, exist_ok=True)
        
        success_count = 0
        failed_count = 0
        details = []
        
        for ipo in target_ipos:
            logger.info(f"Processing: {ipo.company_name}")
            result = await downloader.process_ipo(ipo, download_dir)
            
            if result.get("status") == "success":
                success_count += 1
                details.append(f"[SUCCESS] {ipo.company_name} - Downloaded from {result['source']} ({result.get('pages', 0)} pages, {result.get('size_mb', 0)} MB)")
            else:
                failed_count += 1
                details.append(f"[FAILED] {ipo.company_name} - {result.get('error', 'Failed')}")
                
        # Generate Report
        report_date = datetime.now().strftime("%Y-%m-%d")
        report = f"""RHP Download Report - {report_date}
Successfully Downloaded: {success_count}
Failed: {failed_count}
Already Exists: {db.query(IPO).filter(IPO.prospectus_file_id != None).count()}

Details:
"""
        for d in details:
            report += f"{d}\n"
            
        import sys
        print("\n" + "="*50, file=sys.stdout)
        print(report.encode("utf-8", "replace").decode("utf-8"), file=sys.stdout)
        print("="*50 + "\n", file=sys.stdout)
        
        # Save report
        with open(f"rhp_report_{report_date}.txt", "w", encoding="utf-8") as f:
            f.write(report)
            
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
