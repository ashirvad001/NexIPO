"""
Model Accuracy / Track Record API endpoints.

Public-facing endpoints that compare the BERT+LSTM volatility forecaster's
historical predictions against actual listing-day outcomes.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func as sql_func, case
from typing import Optional

from app.db.database import get_db
from app.models.ipo import IPO
from app.models.prediction_log import PredictionLog

router = APIRouter(prefix="/model-accuracy", tags=["Model Accuracy"])


@router.get("")
async def get_model_accuracy(
    sort_by: str = Query("listing_date", pattern="^(listing_date|predicted_gain|actual_gain|error|company_name)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    ipo_type: Optional[str] = Query(None, pattern="^(mainboard|sme)$"),
    search: Optional[str] = Query(None, max_length=100),
    db: Session = Depends(get_db),
):
    """
    Per-IPO model accuracy records.

    Returns every IPO that has both a stored AI prediction and a final
    listing price, with predicted gain %, actual gain %, absolute error,
    and directional correctness.

    **Public endpoint — no authentication required.**
    """
    # Base query: join prediction logs with IPOs that have listing outcomes
    query = (
        db.query(
            IPO.id.label("ipo_id"),
            IPO.company_name,
            IPO.listing_date,
            IPO.issue_price,
            IPO.listing_price,
            IPO.ipo_type,
            PredictionLog.predicted_gain,
            PredictionLog.predicted_at,
            PredictionLog.model_version,
        )
        .join(PredictionLog, PredictionLog.ipo_id == IPO.id)
        .filter(
            IPO.issue_price.isnot(None),
            IPO.issue_price > 0,
            IPO.listing_price.isnot(None),
            PredictionLog.predicted_gain.isnot(None),
        )
    )

    # For each IPO, pick only the *latest* prediction (subquery approach)
    latest_pred = (
        db.query(
            PredictionLog.ipo_id,
            sql_func.max(PredictionLog.predicted_at).label("max_predicted_at"),
        )
        .group_by(PredictionLog.ipo_id)
        .subquery()
    )
    query = query.join(
        latest_pred,
        (PredictionLog.ipo_id == latest_pred.c.ipo_id)
        & (PredictionLog.predicted_at == latest_pred.c.max_predicted_at),
    )

    # Filters
    if ipo_type:
        query = query.filter(IPO.ipo_type == ipo_type)
    if search:
        query = query.filter(IPO.company_name.ilike(f"%{search}%"))

    rows = query.all()

    # Build response with computed fields
    records = []
    for row in rows:
        actual_gain = ((row.listing_price - row.issue_price) / row.issue_price) * 100
        predicted = row.predicted_gain
        error = abs(predicted - actual_gain)
        directionally_correct = (predicted >= 0 and actual_gain >= 0) or (predicted < 0 and actual_gain < 0)

        records.append({
            "ipo_id": row.ipo_id,
            "company_name": row.company_name,
            "listing_date": row.listing_date.isoformat() if row.listing_date else None,
            "predicted_gain": round(predicted, 2),
            "actual_gain": round(actual_gain, 2),
            "error": round(error, 2),
            "directionally_correct": directionally_correct,
            "ipo_type": row.ipo_type.value if row.ipo_type else "mainboard",
            "model_version": row.model_version,
            "predicted_at": row.predicted_at.isoformat() if row.predicted_at else None,
        })

    # Sort
    sort_key_map = {
        "listing_date": lambda r: r["listing_date"] or "",
        "predicted_gain": lambda r: r["predicted_gain"],
        "actual_gain": lambda r: r["actual_gain"],
        "error": lambda r: r["error"],
        "company_name": lambda r: r["company_name"].lower(),
    }
    key_fn = sort_key_map.get(sort_by, sort_key_map["listing_date"])
    records.sort(key=key_fn, reverse=(sort_order == "desc"))

    return {
        "success": True,
        "count": len(records),
        "records": records,
    }


@router.get("/summary")
async def get_model_accuracy_summary(
    db: Session = Depends(get_db),
):
    """
    Aggregate model accuracy statistics.

    Returns overall directional accuracy %, mean absolute error,
    sample size, and accuracy broken down by Mainboard vs SME.

    **Public endpoint — no authentication required.**
    """
    # Fetch all prediction+outcome pairs (latest prediction per IPO)
    latest_pred = (
        db.query(
            PredictionLog.ipo_id,
            sql_func.max(PredictionLog.predicted_at).label("max_predicted_at"),
        )
        .group_by(PredictionLog.ipo_id)
        .subquery()
    )

    rows = (
        db.query(
            IPO.ipo_type,
            IPO.issue_price,
            IPO.listing_price,
            PredictionLog.predicted_gain,
        )
        .join(PredictionLog, PredictionLog.ipo_id == IPO.id)
        .join(
            latest_pred,
            (PredictionLog.ipo_id == latest_pred.c.ipo_id)
            & (PredictionLog.predicted_at == latest_pred.c.max_predicted_at),
        )
        .filter(
            IPO.issue_price.isnot(None),
            IPO.issue_price > 0,
            IPO.listing_price.isnot(None),
            PredictionLog.predicted_gain.isnot(None),
        )
        .all()
    )

    if not rows:
        return {
            "success": True,
            "sample_size": 0,
            "overall_accuracy": None,
            "mean_absolute_error": None,
            "breakdown": {"mainboard": None, "sme": None},
        }

    # Compute stats
    total = 0
    correct = 0
    total_error = 0.0
    by_type: dict = {
        "mainboard": {"total": 0, "correct": 0, "total_error": 0.0},
        "sme": {"total": 0, "correct": 0, "total_error": 0.0},
    }

    for row in rows:
        actual_gain = ((row.listing_price - row.issue_price) / row.issue_price) * 100
        predicted = row.predicted_gain
        error = abs(predicted - actual_gain)
        dir_correct = (predicted >= 0 and actual_gain >= 0) or (predicted < 0 and actual_gain < 0)

        total += 1
        total_error += error
        if dir_correct:
            correct += 1

        ipo_type_key = row.ipo_type.value if row.ipo_type else "mainboard"
        bucket = by_type.get(ipo_type_key, by_type["mainboard"])
        bucket["total"] += 1
        bucket["total_error"] += error
        if dir_correct:
            bucket["correct"] += 1

    overall_accuracy = round((correct / total) * 100, 1) if total else None
    mae = round(total_error / total, 2) if total else None

    breakdown = {}
    for key, bucket in by_type.items():
        if bucket["total"] > 0:
            breakdown[key] = {
                "sample_size": bucket["total"],
                "accuracy": round((bucket["correct"] / bucket["total"]) * 100, 1),
                "mean_absolute_error": round(bucket["total_error"] / bucket["total"], 2),
            }
        else:
            breakdown[key] = None

    return {
        "success": True,
        "sample_size": total,
        "overall_accuracy": overall_accuracy,
        "mean_absolute_error": mae,
        "breakdown": breakdown,
    }
