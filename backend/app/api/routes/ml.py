# app/api/routes/ml.py
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ml", tags=["Machine Learning"])


class RiskPredictionRequest(BaseModel):
    prospectus_text: str
    sections: Dict[str, str] = {}
    ipo_data: Dict = {}
    explain: bool = True


class RiskPredictionResponse(BaseModel):
    risk_score: int
    risk_category: str
    confidence: float
    risk_indicators: Dict
    explanation: Optional[Dict] = None
    explanation_text: Optional[str] = None
    success: bool


@router.post("/predict-risk", response_model=RiskPredictionResponse)
async def predict_risk(request: RiskPredictionRequest):
    """Predict IPO risk from prospectus text"""
    try:
        from app.ml_service.inference.risk_predictor import get_predictor
        
        predictor = get_predictor()
        result = predictor.predict(
            request.prospectus_text,
            request.sections,
            request.ipo_data,
            request.explain
        )
        
        if not result.get('success'):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get('error', 'Prediction failed')
            )
        
        return result
        
    except Exception as e:
        logger.error(f"ML prediction error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ML service error: {str(e)}"
        )


@router.get("/model-status")
async def model_status():
    """Check ML model status"""
    try:
        from app.ml_service.inference.risk_predictor import get_predictor
        
        predictor = get_predictor()
        
        return {
            "model_loaded": predictor.classifier.is_fitted,
            "explainer_available": predictor.explainer is not None,
            "status": "ready" if predictor.classifier.is_fitted else "not_trained"
        }
    except Exception as e:
        return {
            "model_loaded": False,
            "status": "error",
            "error": str(e)
        }
