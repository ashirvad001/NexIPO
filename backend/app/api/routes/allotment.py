from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, Field

from app.db.database import get_db
from app.services.ipo_service import IPOService
from app.services.allotment_calculator import (
    calculate_allotment_probability,
    get_category_comparison,
)

router = APIRouter(prefix="/allotment", tags=["Allotment Calculator"])


# ── Request / Response schemas ─────────────────────────────────────────────

class AllotmentRequest(BaseModel):
    lots_applied: int = Field(default=1, ge=1, le=100, description="Number of lots applied for")


class AllotmentResponse(BaseModel):
    success: bool
    probability_pct: Optional[float]
    scenario: Optional[str]
    expected_lots: Optional[int]
    allotment_note: Optional[str]
    breakdown: Optional[dict]
    application: Optional[dict]
    insights: Optional[dict]


# ── Endpoints ──────────────────────────────────────────────────────────────

@router.post("/calculate/{ipo_id}", response_model=AllotmentResponse)
def calculate_for_ipo(
    ipo_id: int,
    request: AllotmentRequest,
    db: Session = Depends(get_db),
):
    """
    Calculate allotment probability for a specific IPO.

    Fetches all required data from the database automatically.
    User only needs to provide how many lots they are applying for.
    """
    ipo = IPOService.get_ipo_by_id(db, ipo_id)
    if not ipo:
        raise HTTPException(status_code=404, detail=f"IPO {ipo_id} not found")

    # Validate required fields
    missing = []
    if not ipo.lot_size:
        missing.append("lot_size")
    if not ipo.price_band_upper:
        missing.append("price_band_upper")
    if not ipo.issue_size_rs_cr:
        missing.append("issue_size_rs_cr")

    if missing:
        raise HTTPException(
            status_code=422,
            detail=f"IPO is missing required fields: {', '.join(missing)}. "
                   "These will be available once the IPO opens for subscription.",
        )

    retail_sub = ipo.retail_subscription or 0.0

    result = calculate_allotment_probability(
        lot_size=ipo.lot_size,
        price_band_upper=ipo.price_band_upper,
        issue_size_rs_cr=ipo.issue_size_rs_cr,
        retail_subscription=retail_sub,
        total_subscription=ipo.total_subscription or retail_sub,
        ipo_type=ipo.ipo_type.value if hasattr(ipo.ipo_type, 'value') else str(ipo.ipo_type),
        lots_applied=request.lots_applied,
        qib_subscription=ipo.qib_subscription,
        nii_subscription=ipo.nii_subscription,
    )

    if not result["success"]:
        raise HTTPException(status_code=422, detail=result.get("errors", "Calculation failed"))

    return result


@router.get("/calculate/{ipo_id}")
def calculate_for_ipo_get(
    ipo_id: int,
    lots_applied: int = Query(default=1, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    GET version of allotment calculator (useful for direct URL access / sharing).
    """
    ipo = IPOService.get_ipo_by_id(db, ipo_id)
    if not ipo:
        raise HTTPException(status_code=404, detail=f"IPO {ipo_id} not found")

    if not ipo.lot_size or not ipo.price_band_upper or not ipo.issue_size_rs_cr:
        return {
            "success": False,
            "message": "Insufficient IPO data for calculation.",
            "ipo_id": ipo_id,
            "company_name": ipo.company_name,
        }

    retail_sub = ipo.retail_subscription or 0.0

    result = calculate_allotment_probability(
        lot_size=ipo.lot_size,
        price_band_upper=ipo.price_band_upper,
        issue_size_rs_cr=ipo.issue_size_rs_cr,
        retail_subscription=retail_sub,
        total_subscription=ipo.total_subscription or retail_sub,
        ipo_type=ipo.ipo_type.value if hasattr(ipo.ipo_type, 'value') else str(ipo.ipo_type),
        lots_applied=lots_applied,
        qib_subscription=ipo.qib_subscription,
        nii_subscription=ipo.nii_subscription,
    )

    return {
        **result,
        "ipo_id": ipo_id,
        "company_name": ipo.company_name,
        "symbol": ipo.symbol,
    }


@router.get("/compare/{ipo_id}")
def compare_categories(
    ipo_id: int,
    db: Session = Depends(get_db),
):
    """
    Compare allotment probability across Retail / HNI / QIB categories.
    Helps investors decide which category to apply under.
    """
    ipo = IPOService.get_ipo_by_id(db, ipo_id)
    if not ipo:
        raise HTTPException(status_code=404, detail=f"IPO {ipo_id} not found")

    if not ipo.lot_size or not ipo.price_band_upper or not ipo.issue_size_rs_cr:
        raise HTTPException(
            status_code=422,
            detail="Insufficient IPO data for category comparison.",
        )

    comparison = get_category_comparison(
        lot_size=ipo.lot_size,
        price_band_upper=ipo.price_band_upper,
        issue_size_rs_cr=ipo.issue_size_rs_cr,
        retail_subscription=ipo.retail_subscription or 0.0,
        nii_subscription=ipo.nii_subscription,
        qib_subscription=ipo.qib_subscription,
    )

    return {
        "ipo_id": ipo_id,
        "company_name": ipo.company_name,
        "symbol": ipo.symbol,
        **comparison,
    }


@router.get("/quick/{ipo_id}")
def quick_summary(
    ipo_id: int,
    db: Session = Depends(get_db),
):
    """
    Quick allotment summary card — used by the IPO detail page widget.
    Returns a compact summary without full breakdown.
    """
    ipo = IPOService.get_ipo_by_id(db, ipo_id)
    if not ipo:
        raise HTTPException(status_code=404, detail=f"IPO {ipo_id} not found")

    if not ipo.lot_size or not ipo.price_band_upper or not ipo.issue_size_rs_cr:
        return {
            "available": False,
            "reason": "IPO data incomplete",
            "ipo_id": ipo_id,
        }

    result = calculate_allotment_probability(
        lot_size=ipo.lot_size,
        price_band_upper=ipo.price_band_upper,
        issue_size_rs_cr=ipo.issue_size_rs_cr,
        retail_subscription=ipo.retail_subscription or 0.0,
        total_subscription=ipo.total_subscription or 0.0,
        ipo_type=ipo.ipo_type.value if hasattr(ipo.ipo_type, 'value') else str(ipo.ipo_type),
        lots_applied=1,
        qib_subscription=ipo.qib_subscription,
        nii_subscription=ipo.nii_subscription,
    )

    return {
        "available": True,
        "ipo_id": ipo_id,
        "company_name": ipo.company_name,
        "probability_pct": result.get("probability_pct"),
        "scenario": result.get("scenario"),
        "retail_subscription": ipo.retail_subscription,
        "estimated_applications": result.get("breakdown", {}).get("estimated_applications"),
        "retail_lots_available": result.get("breakdown", {}).get("retail_lots_available"),
        "lot_size": ipo.lot_size,
        "min_investment": ipo.lot_size * ipo.price_band_upper if ipo.lot_size and ipo.price_band_upper else None,
     }
