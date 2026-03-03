from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import Optional
import math

from app.db.database import get_db
from app.schemas.ipo import (
    IPOCreate,
    IPOUpdate,
    IPOResponse,
    IPOListResponse,
    IPOFilter,
    IPOStatus,
    IPOType
)
from app.services.ipo_service import IPOService
from app.services.ipo_scraper import sync_ipos
from app.services.ipo_analyzer import analyze_ipo

router = APIRouter(prefix="/ipos", tags=["IPOs"])


@router.post("/sync", tags=["IPOs"])
async def sync_ipo_data(db: Session = Depends(get_db)):
    """
    Trigger a manual sync of real-time Indian IPO data.
    Scrapes from IPO Central (listings + GMP) and Moneycontrol (detail pages).
    """
    try:
        summary = await sync_ipos(db)
        return {
            "status": "success",
            "message": (
                f"Synced {summary['total_scraped']} IPOs: "
                f"{summary['added']} added, {summary['updated']} updated, "
                f"{summary['enriched']} enriched from Moneycontrol"
            ),
            "details": summary,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Sync failed: {str(e)}",
        )


@router.get("/{ipo_id}/analysis", tags=["IPOs"])
def get_ipo_analysis(ipo_id: int, db: Session = Depends(get_db)):
    """
    Get a data-driven analysis of an IPO including Pros, Cons, Risks, and Verdict.
    """
    analysis = analyze_ipo(db, ipo_id)
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="IPO not found",
        )
    return analysis


@router.post("/", response_model=IPOResponse, status_code=status.HTTP_201_CREATED)
def create_ipo(
    ipo_data: IPOCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new IPO entry.
    
    - **company_name**: Name of the company
    - **symbol**: Stock symbol/ticker
    - **status**: IPO status (upcoming/open/closed/listed/withdrawn)
    - **ipo_type**: mainboard or SME
    """
    # Check if symbol already exists
    if ipo_data.symbol:
        existing = IPOService.get_ipo_by_symbol(db, ipo_data.symbol)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"IPO with symbol '{ipo_data.symbol}' already exists"
            )
    
    ipo = IPOService.create_ipo(db, ipo_data)
    
    # Add computed fields
    response = IPOResponse.model_validate(ipo)
    response.is_active = ipo.is_active
    response.listing_gain_percentage = ipo.listing_gain_percentage
    
    return response


@router.get("/", response_model=IPOListResponse)
def get_ipos(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: Optional[IPOStatus] = Query(None, description="Filter by status"),
    ipo_type: Optional[IPOType] = Query(None, description="Filter by IPO type"),
    industry_sector: Optional[str] = Query(None, description="Filter by industry"),
    min_issue_size: Optional[float] = Query(None, ge=0, description="Minimum issue size"),
    max_issue_size: Optional[float] = Query(None, ge=0, description="Maximum issue size"),
    min_subscription: Optional[float] = Query(None, ge=0, description="Minimum subscription"),
    min_risk_score: Optional[float] = Query(None, ge=0, le=100, description="Minimum risk score"),
    max_risk_score: Optional[float] = Query(None, ge=0, le=100, description="Maximum risk score"),
    search: Optional[str] = Query(None, description="Search in company name or symbol"),
    sort_by: str = Query("created_at", description="Field to sort by"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    db: Session = Depends(get_db)
):
    """
    Get paginated list of IPOs with optional filters.
    
    Supports filtering by:
    - Status (upcoming, open, closed, listed, withdrawn)
    - IPO type (mainboard, SME)
    - Industry sector
    - Issue size range
    - Subscription levels
    - Risk score range
    - Text search
    """
    # Build filters
    filters = IPOFilter(
        status=status,
        ipo_type=ipo_type,
        industry_sector=industry_sector,
        min_issue_size=min_issue_size,
        max_issue_size=max_issue_size,
        min_subscription=min_subscription,
        min_risk_score=min_risk_score,
        max_risk_score=max_risk_score,
        search=search
    )
    
    # Calculate skip
    skip = (page - 1) * page_size
    
    # Get IPOs
    ipos, total = IPOService.get_ipos(
        db=db,
        filters=filters,
        skip=skip,
        limit=page_size,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    # Calculate total pages
    total_pages = math.ceil(total / page_size) if total > 0 else 0
    
    # Convert to response models with computed fields
    items = []
    for ipo in ipos:
        response = IPOResponse.model_validate(ipo)
        response.is_active = ipo.is_active
        response.listing_gain_percentage = ipo.listing_gain_percentage
        items.append(response)
    
    return IPOListResponse(
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        items=items
    )


@router.get("/active", response_model=list[IPOResponse])
def get_active_ipos(db: Session = Depends(get_db)):
    """
    Get all currently active (open for subscription) IPOs.
    """
    ipos = IPOService.get_active_ipos(db)
    
    items = []
    for ipo in ipos:
        response = IPOResponse.model_validate(ipo)
        response.is_active = ipo.is_active
        response.listing_gain_percentage = ipo.listing_gain_percentage
        items.append(response)
    
    return items


@router.get("/upcoming", response_model=list[IPOResponse])
def get_upcoming_ipos(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of upcoming IPOs"),
    db: Session = Depends(get_db)
):
    """
    Get upcoming IPOs sorted by open date.
    """
    ipos = IPOService.get_upcoming_ipos(db, limit=limit)
    
    items = []
    for ipo in ipos:
        response = IPOResponse.model_validate(ipo)
        response.is_active = ipo.is_active
        response.listing_gain_percentage = ipo.listing_gain_percentage
        items.append(response)
    
    return items


@router.get("/{ipo_id}", response_model=IPOResponse)
def get_ipo(
    ipo_id: int,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a specific IPO by ID.
    """
    ipo = IPOService.get_ipo_by_id(db, ipo_id)
    if not ipo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IPO with id {ipo_id} not found"
        )
    
    response = IPOResponse.model_validate(ipo)
    response.is_active = ipo.is_active
    response.listing_gain_percentage = ipo.listing_gain_percentage
    
    return response


@router.get("/symbol/{symbol}", response_model=IPOResponse)
def get_ipo_by_symbol(
    symbol: str,
    db: Session = Depends(get_db)
):
    """
    Get IPO details by stock symbol.
    """
    ipo = IPOService.get_ipo_by_symbol(db, symbol)
    if not ipo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IPO with symbol '{symbol}' not found"
        )
    
    response = IPOResponse.model_validate(ipo)
    response.is_active = ipo.is_active
    response.listing_gain_percentage = ipo.listing_gain_percentage
    
    return response


@router.put("/{ipo_id}", response_model=IPOResponse)
def update_ipo(
    ipo_id: int,
    ipo_data: IPOUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing IPO. Only provided fields will be updated.
    """
    ipo = IPOService.update_ipo(db, ipo_id, ipo_data)
    if not ipo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IPO with id {ipo_id} not found"
        )
    
    response = IPOResponse.model_validate(ipo)
    response.is_active = ipo.is_active
    response.listing_gain_percentage = ipo.listing_gain_percentage
    
    return response


@router.delete("/{ipo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ipo(
    ipo_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete an IPO by ID.
    """
    deleted = IPOService.delete_ipo(db, ipo_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"IPO with id {ipo_id} not found"
        )
    
    return None