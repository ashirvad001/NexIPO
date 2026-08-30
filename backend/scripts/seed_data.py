"""
Seed script to populate database with sample IPO data for testing.
Run: python seed_data.py
"""

import sys
import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Add backend to path so we can import 'app'
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.database import SessionLocal, engine, Base
from app.models.ipo import IPO, IPOStatus, IPOType


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)


def create_sample_ipos(db: Session):
    """Create sample IPO entries"""
    
    sample_ipos = [
        {
            "company_name": "TechVision India Ltd",
            "symbol": "TECHVIS",
            "status": IPOStatus.OPEN,
            "ipo_type": IPOType.MAINBOARD,
            "open_date": datetime.now() - timedelta(days=1),
            "close_date": datetime.now() + timedelta(days=2),
            "listing_date": datetime.now() + timedelta(days=7),
            "price_band_lower": 280.0,
            "price_band_upper": 295.0,
            "issue_size_rs_cr": 1500.0,
            "shares_offered": 50000000,
            "qib_subscription": 2.5,
            "nii_subscription": 1.8,
            "retail_subscription": 3.2,
            "total_subscription": 2.8,
            "gmp_amount": 45.0,
            "gmp_percentage": 15.25,
            "industry_sector": "Technology",
            "lot_size": 50,
            "min_investment": 14750.0,
            "description": "Leading IT services and digital transformation company"
        },
        {
            "company_name": "Green Energy Solutions",
            "symbol": "GREENEN",
            "status": IPOStatus.UPCOMING,
            "ipo_type": IPOType.MAINBOARD,
            "open_date": datetime.now() + timedelta(days=5),
            "close_date": datetime.now() + timedelta(days=8),
            "listing_date": datetime.now() + timedelta(days=15),
            "price_band_lower": 450.0,
            "price_band_upper": 475.0,
            "issue_size_rs_cr": 2300.0,
            "shares_offered": 48000000,
            "industry_sector": "Renewable Energy",
            "lot_size": 30,
            "min_investment": 14250.0,
            "description": "Solar and wind energy solutions provider"
        },
        {
            "company_name": "FinServe Payments Ltd",
            "symbol": "FINSERV",
            "status": IPOStatus.LISTED,
            "ipo_type": IPOType.MAINBOARD,
            "open_date": datetime.now() - timedelta(days=20),
            "close_date": datetime.now() - timedelta(days=17),
            "listing_date": datetime.now() - timedelta(days=10),
            "price_band_lower": 180.0,
            "price_band_upper": 190.0,
            "issue_price": 190.0,
            "listing_price": 245.0,
            "current_price": 238.50,
            "issue_size_rs_cr": 850.0,
            "shares_offered": 44000000,
            "qib_subscription": 3.8,
            "nii_subscription": 2.9,
            "retail_subscription": 4.5,
            "total_subscription": 3.9,
            "gmp_amount": 52.0,
            "gmp_percentage": 27.37,
            "industry_sector": "Financial Services",
            "market_cap_cr": 4200.0,
            "pe_ratio": 28.5,
            "lot_size": 75,
            "description": "Digital payment and fintech solutions"
        },
        {
            "company_name": "MediCare Hospitals",
            "symbol": "MEDICARE",
            "status": IPOStatus.UPCOMING,
            "ipo_type": IPOType.MAINBOARD,
            "open_date": datetime.now() + timedelta(days=10),
            "close_date": datetime.now() + timedelta(days=13),
            "price_band_lower": 320.0,
            "price_band_upper": 340.0,
            "issue_size_rs_cr": 1200.0,
            "industry_sector": "Healthcare",
            "lot_size": 40,
            "description": "Multi-specialty hospital chain"
        },
        {
            "company_name": "SmartLogistics Solutions",
            "symbol": "SMARTLOG",
            "status": IPOStatus.OPEN,
            "ipo_type": IPOType.SME,
            "open_date": datetime.now() - timedelta(days=1),
            "close_date": datetime.now() + timedelta(days=1),
            "price_band_lower": 85.0,
            "price_band_upper": 90.0,
            "issue_size_rs_cr": 45.0,
            "qib_subscription": 1.2,
            "nii_subscription": 0.8,
            "retail_subscription": 1.5,
            "total_subscription": 1.3,
            "industry_sector": "Logistics",
            "lot_size": 1600,
            "description": "SME logistics and warehousing services"
        }
    ]
    
    for ipo_data in sample_ipos:
        ipo = IPO(**ipo_data)
        db.add(ipo)
    
    db.commit()
    print(f"✅ Created {len(sample_ipos)} sample IPOs")


def main():
    """Main seed function"""
    print("🌱 Starting database seeding...")
    
    # Initialize database
    init_db()
    print("✅ Database tables created")
    
    # Create session
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing_count = db.query(IPO).count()
        if existing_count > 0:
            print(f"⚠️  Database already contains {existing_count} IPOs")
            response = input("Do you want to add more sample data? (y/n): ")
            if response.lower() != 'y':
                print("❌ Seeding cancelled")
                return
        
        # Create sample data
        create_sample_ipos(db)
        
        # Verify
        total_count = db.query(IPO).count()
        print(f"✅ Database now contains {total_count} total IPOs")
        print("🎉 Seeding completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
