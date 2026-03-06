
from app.db.database import engine
from sqlalchemy import text

def migrate():
    with engine.connect() as conn:
        print("Adding return_1d column...")
        try:
            conn.execute(text("ALTER TABLE ipos ADD COLUMN return_1d FLOAT"))
            conn.commit()
        except Exception as e:
            print(f"return_1d already exists or error: {e}")
            
        print("Adding return_1w column...")
        try:
            conn.execute(text("ALTER TABLE ipos ADD COLUMN return_1w FLOAT"))
            conn.commit()
        except Exception as e:
            print(f"return_1w already exists or error: {e}")
            
        print("Adding return_1m column...")
        try:
            conn.execute(text("ALTER TABLE ipos ADD COLUMN return_1m FLOAT"))
            conn.commit()
        except Exception as e:
            print(f"return_1m already exists or error: {e}")
        
    print("Migration complete.")

if __name__ == "__main__":
    migrate()
