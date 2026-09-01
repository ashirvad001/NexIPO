"""
PredictionLog model — persists every AI prediction so we can
compare predicted vs actual listing-day outcomes on the public
accuracy / track-record page.
"""

from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class PredictionLog(Base):
    """
    Stores a snapshot of each ML volatility prediction made for an IPO.
    Used to compute directional accuracy and mean absolute error on the
    public /model-accuracy page.
    """
    __tablename__ = "prediction_logs"

    id = Column(Integer, primary_key=True, index=True)
    ipo_id = Column(Integer, ForeignKey("ipos.id", ondelete="CASCADE"), nullable=False, index=True)
    predicted_gain = Column(Float, nullable=False)          # predicted listing gain %
    predicted_at = Column(DateTime, server_default=func.now(), nullable=False)
    model_version = Column(String(50), nullable=False, default="bert-lstm-v1")

    # Relationship
    ipo = relationship("IPO", backref="prediction_logs")

    def __repr__(self):
        return (
            f"<PredictionLog(id={self.id}, ipo_id={self.ipo_id}, "
            f"predicted_gain={self.predicted_gain}, model_version={self.model_version})>"
        )
