import traceback
from app.db.database import SessionLocal
from app.services.ipo_service import IPOService

def test_active_ipos():
    db = SessionLocal()
    try:
        print("Fetching active IPOs...")
        ipos = IPOService.get_active_ipos(db)
        print(f"Found {len(ipos)} active IPOs")
    except Exception as e:
        print("Exception caught:")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_active_ipos()
