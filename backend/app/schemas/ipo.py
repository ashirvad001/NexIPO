from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
from enum import Enum


class IPOStatus(str, Enum):
    UPCOMING = "upcoming"
    OPEN = "open"
    CLOSED = "closed"
    LISTED = "listed"
    WITHDRAWN = "withdrawn"


class IPOType(str, Enum):
    MAINBOARD = "mainboard"
    SME = "sme"


class IPOBase(BaseModel):
    """Base schema with common IPO fields"""
    company_name: str = Field(..., min_length=1, max_length=255)
    symbol: Optional[str] = Field(None, max_length=50)
    status: IPOStatus = IPOStatus.UPCOMING
    ipo_type: IPOType = IPOType.MAINBOARD
    
    open_date: Optional[datetime] = None
    close_date: Optional[datetime] = None
    allotment_date: Optional[datetime] = None
    listing_date: Optional[datetime] = None
    
    price_band_lower: Optional[float] = Field(None, ge=0)
    price_band_upper: Optional[float] = Field(None, ge=0)
    issue_price: Optional[float] = Field(None, ge=0)
    listing_price: Optional[float] = Field(None, ge=0)
    current_price: Optional[float] = Field(None, ge=0)
    
    issue_size_rs_cr: Optional[float] = Field(None, ge=0)
    shares_offered: Optional[int] = Field(None, ge=0)
    fresh_issue_size: Optional[float] = Field(None, ge=0)
    offer_for_sale: Optional[float] = Field(None, ge=0)
    
    qib_subscription: Optional[float] = Field(None, ge=0)
    nii_subscription: Optional[float] = Field(None, ge=0)
    retail_subscription: Optional[float] = Field(None, ge=0)
    total_subscription: Optional[float] = Field(None, ge=0)
    
    gmp_amount: Optional[float] = None
    gmp_percentage: Optional[float] = None
    estimated_listing_price: Optional[float] = Field(None, ge=0)
    
    industry_sector: Optional[str] = Field(None, max_length=100)
    lead_managers: Optional[str] = None
    registrar: Optional[str] = Field(None, max_length=255)
    
    market_cap_cr: Optional[float] = Field(None, ge=0)
    pe_ratio: Optional[float] = None
    roce: Optional[float] = None
    roe: Optional[float] = None
    revenue_growth: Optional[float] = None
    profit_growth: Optional[float] = None
    
    prospectus_url: Optional[str] = Field(None, max_length=500)
    
    lot_size: Optional[int] = Field(None, ge=1)
    min_investment: Optional[float] = Field(None, ge=0)
    description: Optional[str] = None

    @field_validator('price_band_upper')
    @classmethod
    def validate_price_band(cls, v, values):
        """Ensure upper price band is >= lower price band"""
        if v and 'price_band_lower' in values.data and values.data['price_band_lower']:
            if v < values.data['price_band_lower']:
                raise ValueError('Upper price band must be >= lower price band')
        return v


class IPOCreate(IPOBase):
    """Schema for creating a new IPO"""
    pass


class IPOUpdate(BaseModel):
    """Schema for updating an IPO (all fields optional)"""
    company_name: Optional[str] = Field(None, min_length=1, max_length=255)
    symbol: Optional[str] = Field(None, max_length=50)
    status: Optional[IPOStatus] = None
    ipo_type: Optional[IPOType] = None
    
    open_date: Optional[datetime] = None
    close_date: Optional[datetime] = None
    allotment_date: Optional[datetime] = None
    listing_date: Optional[datetime] = None
    
    price_band_lower: Optional[float] = Field(None, ge=0)
    price_band_upper: Optional[float] = Field(None, ge=0)
    issue_price: Optional[float] = Field(None, ge=0)
    listing_price: Optional[float] = Field(None, ge=0)
    current_price: Optional[float] = Field(None, ge=0)
    
    issue_size_rs_cr: Optional[float] = Field(None, ge=0)
    shares_offered: Optional[int] = Field(None, ge=0)
    
    qib_subscription: Optional[float] = Field(None, ge=0)
    nii_subscription: Optional[float] = Field(None, ge=0)
    retail_subscription: Optional[float] = Field(None, ge=0)
    total_subscription: Optional[float] = Field(None, ge=0)
    
    gmp_amount: Optional[float] = None
    gmp_percentage: Optional[float] = None
    
    industry_sector: Optional[str] = Field(None, max_length=100)
    
    risk_score: Optional[float] = Field(None, ge=0, le=100)
    risk_category: Optional[str] = Field(None, max_length=20)
    
    description: Optional[str] = None


class IPOResponse(IPOBase):
    """Schema for IPO response with additional fields"""
    id: int
    risk_score: Optional[float] = None
    risk_category: Optional[str] = None
    ml_processed: bool = False
    ml_processed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    is_active: bool = False
    listing_gain_percentage: Optional[float] = None
    
    class Config:
        from_attributes = True


class IPOListResponse(BaseModel):
    """Paginated list response"""
    total: int
    page: int
    page_size: int
    total_pages: int
    items: list[IPOResponse]


class IPOFilter(BaseModel):
    """Filter parameters for IPO list"""
    status: Optional[IPOStatus] = None
    ipo_type: Optional[IPOType] = None
    industry_sector: Optional[str] = None
    min_issue_size: Optional[float] = Field(None, ge=0)
    max_issue_size: Optional[float] = Field(None, ge=0)
    min_subscription: Optional[float] = Field(None, ge=0)
    min_risk_score: Optional[float] = Field(None, ge=0, le=100)
    max_risk_score: Optional[float] = Field(None, ge=0, le=100)
    search: Optional[str] = None  # Search in company_name or symbol