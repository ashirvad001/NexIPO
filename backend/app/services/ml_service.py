"""
ML Service — wires the database IPO record to the RiskPredictor.
Passes ALL available structured fields so the rule-based engine
produces genuinely differentiated scores per IPO.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.ipo import IPO
from app.ml_service.inference.risk_predictor import get_predictor
from app.core.mongodb import MongoDB


def _ipo_to_dict(ipo: IPO) -> Dict[str, Any]:
    """Convert an IPO ORM object to the dict the predictor expects."""
    return {
        # Subscription
        "total_subscription":   ipo.total_subscription,
        "qib_subscription":     ipo.qib_subscription,
        "nii_subscription":     ipo.nii_subscription,
        "retail_subscription":  ipo.retail_subscription,
        # GMP
        "gmp_amount":           ipo.gmp_amount,
        "gmp_percentage":       ipo.gmp_percentage,
        "estimated_listing_price": ipo.estimated_listing_price,
        # Valuation
        "pe_ratio":             ipo.pe_ratio,
        "issue_size_rs_cr":     ipo.issue_size_rs_cr,
        "fresh_issue_size":     ipo.fresh_issue_size,
        "offer_for_sale":       ipo.offer_for_sale,
        "market_cap_cr":        ipo.market_cap_cr,
        # Pricing
        "price_band_lower":     ipo.price_band_lower,
        "price_band_upper":     ipo.price_band_upper,
        "issue_price":          ipo.issue_price,
        "listing_price":        ipo.listing_price,
        "face_value":           ipo.face_value,
        # Financials
        "revenue_growth":       ipo.revenue_growth,
        "profit_growth":        ipo.profit_growth,
        "roce":                 ipo.roce,
        "roe":                  ipo.roe,
        "eps":                  ipo.eps,
        "revenue_cr":           ipo.revenue_cr,
        "profit_cr":            ipo.profit_cr,
        # Meta
        "ipo_type":             ipo.ipo_type.value if ipo.ipo_type else None,
        "industry_sector":      ipo.industry_sector,
        "lot_size":             ipo.lot_size,
        "min_investment":       ipo.min_investment,
    }


class MLService:
    """Service for ML predictions and risk assessment."""

    _predictor = None

    @classmethod
    def get_predictor(cls):
        if cls._predictor is None:
            cls._predictor = get_predictor()
        return cls._predictor

    @classmethod
    async def predict_risk(cls, ipo_id: int, db: Session) -> Dict[str, Any]:
        """Predict risk for an IPO, using prospectus text if available."""
        ipo = db.query(IPO).filter(IPO.id == ipo_id).first()
        if not ipo:
            raise ValueError(f"IPO with id {ipo_id} not found")

        # Build structured data dict — works even without a prospectus
        ipo_data = _ipo_to_dict(ipo)

        # Attempt to load prospectus text from MongoDB
        prospectus_text = ""
        sections: Dict[str, str] = {}

        if ipo.prospectus_file_id:
            try:
                prospectus_coll = MongoDB.get_prospectus_collection()
                prospectus_doc = await prospectus_coll.find_one(
                    {"ipo_id": ipo_id},
                    sort=[("created_at", -1)],
                )
                if prospectus_doc:
                    prospectus_text = (
                        prospectus_doc.get("cleaned_text")
                        or prospectus_doc.get("raw_text")
                        or prospectus_doc.get("full_text", "")
                    )
                    sections = prospectus_doc.get("sections", {})
            except Exception as exc:
                # Non-fatal — fall back to rule-based scoring
                pass

        # Run prediction
        predictor = cls.get_predictor()
        result = predictor.predict(
            prospectus_text=prospectus_text,
            sections=sections,
            ipo_data=ipo_data,
            explain=True,
        )

        # Persist results to PostgreSQL
        ipo.risk_score = result["risk_score"]
        ipo.risk_category = result["risk_category"]
        ipo.ml_processed = True
        ipo.ml_processed_at = datetime.utcnow()
        db.commit()
        db.refresh(ipo)

        # Optionally store explanation back in MongoDB
        if result.get("explanation") and ipo.prospectus_file_id:
            try:
                prospectus_coll = MongoDB.get_prospectus_collection()
                await prospectus_coll.update_one(
                    {"ipo_id": ipo_id},
                    {
                        "$set": {
                            "ml_prediction": {
                                "risk_score":    result["risk_score"],
                                "risk_category": result["risk_category"],
                                "confidence":    result.get("confidence"),
                                "explanation":   result["explanation"],
                                "predicted_at":  datetime.utcnow(),
                            }
                        }
                    },
                    upsert=False,
                )
            except Exception:
                pass

        return {
            "ipo_id":          ipo_id,
            "risk_score":      result["risk_score"],
            "risk_category":   result["risk_category"],
            "confidence":      result.get("confidence"),
            "risk_indicators": result.get("risk_indicators"),
            "explanation":     result.get("explanation"),
            "dimension_scores": result.get("dimension_scores"),
            "success":         True,
        }

    @classmethod
    async def get_prediction(cls, ipo_id: int, db: Session) -> Optional[Dict[str, Any]]:
        """Return cached prediction from the database."""
        ipo = db.query(IPO).filter(IPO.id == ipo_id).first()
        if not ipo or not ipo.ml_processed:
            return None

        explanation = None
        if ipo.prospectus_file_id:
            try:
                coll = MongoDB.get_prospectus_collection()
                doc = await coll.find_one({"ipo_id": ipo_id})
                if doc and "ml_prediction" in doc:
                    explanation = doc["ml_prediction"].get("explanation")
            except Exception:
                pass

        return {
            "ipo_id":           ipo_id,
            "risk_score":       ipo.risk_score,
            "risk_category":    ipo.risk_category,
            "ml_processed_at":  ipo.ml_processed_at,
            "explanation":      explanation,
        }

    @classmethod
    def get_model_info(cls) -> Dict[str, Any]:
        predictor = cls.get_predictor()
        return {
            "model_type":       "Multi-Factor Rule Engine + Optional TF-IDF/LR",
            "is_fitted":        predictor.classifier.is_fitted,
            "feature_count":    1034,
            "risk_categories":  ["low", "medium", "high"],
            "scoring_dimensions": list({
                "subscription": 25,
                "gmp": 20,
                "valuation": 20,
                "financials": 15,
                "text_nlp": 20,
            }.keys()),
            "version": "2.0.0",
        }

    @classmethod
    async def get_statistics(cls, db: Session) -> Dict[str, Any]:
        total_ipos      = db.query(IPO).count()
        processed_ipos  = db.query(IPO).filter(IPO.ml_processed == True).count()
        low_risk        = db.query(IPO).filter(IPO.risk_category == "low").count()
        medium_risk     = db.query(IPO).filter(IPO.risk_category == "medium").count()
        high_risk       = db.query(IPO).filter(IPO.risk_category == "high").count()

        return {
            "total_ipos":      total_ipos,
            "processed_ipos":  processed_ipos,
            "pending_ipos":    total_ipos - processed_ipos,
            "risk_distribution": {
                "low":    low_risk,
                "medium": medium_risk,
                "high":   high_risk,
            },
        }