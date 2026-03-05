from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, Enum as SQLEnum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.db.database import Base


class IPOStatus(str, Enum):
    """IPO lifecycle status"""
    UPCOMING = "upcoming"
    OPEN = "open"
    CLOSED = "closed"
    LISTED = "listed"
    WITHDRAWN = "withdrawn"


class IPOType(str, Enum):
    """IPO offering type"""
    MAINBOARD = "mainboard"
    SME = "sme"


class IPO(Base):
    """
    IPO model representing Initial Public Offerings.
    Optimized with indexes for common query patterns.
    """
    __tablename__ = "ipos"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Information
    company_name = Column(String(255), nullable=False, index=True)
    symbol = Column(String(50), unique=True, index=True)
    status = Column(SQLEnum(IPOStatus), nullable=False, default=IPOStatus.UPCOMING, index=True)
    ipo_type = Column(SQLEnum(IPOType), nullable=False, default=IPOType.MAINBOARD)
    
    # Dates
    open_date = Column(DateTime, nullable=True, index=True)
    close_date = Column(DateTime, nullable=True, index=True)
    allotment_date = Column(DateTime, nullable=True)
    listing_date = Column(DateTime, nullable=True, index=True)
    
    # Pricing
    price_band_lower = Column(Float, nullable=True)
    price_band_upper = Column(Float, nullable=True)
    issue_price = Column(Float, nullable=True)
    listing_price = Column(Float, nullable=True)
    current_price = Column(Float, nullable=True)
    
    # Issue Size
    issue_size_rs_cr = Column(Float, nullable=True)  # in Crores
    shares_offered = Column(Integer, nullable=True)
    fresh_issue_size = Column(Float, nullable=True)
    offer_for_sale = Column(Float, nullable=True)
    
    # Subscription Details
    qib_subscription = Column(Float, nullable=True)  # Qualified Institutional Buyers
    nii_subscription = Column(Float, nullable=True)  # Non-Institutional Investors
    retail_subscription = Column(Float, nullable=True)
    total_subscription = Column(Float, nullable=True, index=True)
    
    # Grey Market Premium (GMP)
    gmp_amount = Column(Float, nullable=True)
    gmp_percentage = Column(Float, nullable=True)
    estimated_listing_price = Column(Float, nullable=True)
    
    # Company Details
    industry_sector = Column(String(100), nullable=True, index=True)
    lead_managers = Column(Text, nullable=True)  # JSON array as string
    registrar = Column(String(255), nullable=True)
    
    # Financial Metrics
    market_cap_cr = Column(Float, nullable=True)
    pe_ratio = Column(Float, nullable=True)
    roce = Column(Float, nullable=True)  # Return on Capital Employed
    roe = Column(Float, nullable=True)   # Return on Equity
    revenue_growth = Column(Float, nullable=True)
    profit_growth = Column(Float, nullable=True)
    face_value = Column(Float, nullable=True)
    revenue_cr = Column(Float, nullable=True)   # Revenue in Crores
    profit_cr = Column(Float, nullable=True)    # Profit in Crores
    eps = Column(Float, nullable=True)          # Earnings Per Share
    
    # ML Risk Assessment
    risk_score = Column(Float, nullable=True, index=True)  # 0-100
    risk_category = Column(String(20), nullable=True)  # low, medium, high
    ml_processed = Column(Boolean, default=False, index=True)
    ml_processed_at = Column(DateTime, nullable=True)
    
    # Document References
    prospectus_url = Column(String(500), nullable=True)
    prospectus_file_id = Column(String(255), nullable=True)  # MongoDB reference
    
    # Additional Information
    lot_size = Column(Integer, nullable=True)
    min_investment = Column(Float, nullable=True)
    detail_url = Column(String(500), nullable=True)        # Source-specific detail/review URL
    description = Column(Text, nullable=True)
    
    # Data Enrichment Tracking
    data_source = Column(String(100), nullable=True)       # Which source populated data
    last_enriched_at = Column(DateTime, nullable=True)     # When data was last enriched
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    gmp_history = relationship("GMPHistory", back_populates="ipo", cascade="all, delete-orphan")
    news_and_announcements = Column(Text, nullable=True) # JSON array of text announcements
    
    def __repr__(self):
        return f"<IPO(id={self.id}, company={self.company_name}, status={self.status})>"
    
    @property
    def is_active(self) -> bool:
        """Check if IPO is currently open for subscription"""
        if not self.open_date or not self.close_date:
            return False
        now = datetime.now()
        return self.open_date <= now <= self.close_date
    
    @property
    def listing_gain_percentage(self) -> float | None:
        """Calculate listing gain if both issue and listing prices are available"""
        if self.issue_price and self.listing_price:
            return ((self.listing_price - self.issue_price) / self.issue_price) * 100
        return None