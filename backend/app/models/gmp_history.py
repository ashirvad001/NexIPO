from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

class GMPHistory(Base):
    __tablename__ = "gmp_history"

    id = Column(Integer, primary_key=True, index=True)
    ipo_id = Column(Integer, ForeignKey("ipos.id"), index=True, nullable=False)
    gmp_amount = Column(Float, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationship
    ipo = relationship("IPO", back_populates="gmp_history")
