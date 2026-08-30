"""
Volatility forecasting API endpoints
"""

import asyncio
import time
from functools import partial
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from app.db.database import get_db
from app.core.config import get_settings
from app.models.ipo import IPO
from app.ml_service.volatility.volatility_predictor import VolatilityForecaster
from app.api.routes.auth import get_current_user

router = APIRouter(prefix="/volatility", tags=["Volatility Forecasting"])

settings = get_settings()

# Global predictor instance
try:
    predictor = VolatilityForecaster(newsapi_key=settings.NEWS_API_KEY)
except Exception as e:
    print(f"Failed to initialize VolatilityForecaster: {e}")
    predictor = None


@router.post("/predict/{ipo_id}")
async def predict_ipo_volatility(
    ipo_id: int,
    days_ahead: int = 7,  # Fixed to 7 for Phase 2 LSTM
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Predict stock volatility for an IPO
    
    - **ipo_id**: IPO identifier
    - **days_ahead**: Forecast horizon (7 days)
    
    Returns volatility prediction with risk assessment
    """
    if not predictor:
        raise HTTPException(status_code=503, detail="ML Predictor is not currently available.")
        
    ipo = db.query(IPO).filter(IPO.id == ipo_id).first()
    if not ipo:
        raise HTTPException(status_code=404, detail=f"IPO with ID {ipo_id} not found")
        
    # If symbol is missing (upcoming IPOs), we use a placeholder to trigger the heuristic fallback
    symbol = ipo.symbol or "PENDING"
        
    try:
        t_start = time.time()
        
        # Run CPU-bound ML prediction in a thread pool to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            partial(
                predictor.predict_volatility,
                symbol=symbol,
                company_name=ipo.company_name,
                days_ahead=days_ahead,
            )
        )
        
        elapsed = time.time() - t_start
        print(f"[PERF] Volatility prediction for {ipo.company_name}: {elapsed:.2f}s")
        
        # Optionally, save ML risk back to the IPO model
        ipo.risk_score = result.get('predicted_volatility_percentage')
        ipo.risk_category = result.get('risk_level')
        ipo.ml_processed = True
        ipo.ml_processed_at = datetime.now()
        db.commit()
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error predicting volatility: {str(e)}")


@router.get("/geopolitical-events")
async def get_current_geopolitical_events():
    """Get current geopolitical events affecting markets"""
    if not predictor or not predictor.news_collector:
        raise HTTPException(status_code=503, detail="News Data Collector is not available.")
        
    try:
        # Fetch 7 days of recent global geopolitical news
        events = predictor.news_collector.get_geopolitical_news(days_back=7, page_size=20)
        return {
            "success": True,
            "events": events,
            "count": len(events),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch geopolitical news: {str(e)}")


@router.post("/batch-predict")
async def batch_predict_volatility(ipo_ids: List[int], db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """Predict volatility for multiple IPOs at once"""
    if not predictor:
        raise HTTPException(status_code=503, detail="ML Predictor is not currently available.")
        
    results = []
    errors = []
    
    ipos = db.query(IPO).filter(IPO.id.in_(ipo_ids)).all()
    
    for ipo in ipos:
        if not ipo.symbol:
            errors.append({"id": ipo.id, "error": "No symbol defined"})
            continue
            
        try:
            res = predictor.predict_volatility(
                symbol=ipo.symbol,
                company_name=ipo.company_name,
                days_ahead=7
            )
            
            # Update DB state 
            ipo.risk_score = res.get('predicted_volatility_percentage')
            ipo.risk_category = res.get('risk_level')
            ipo.ml_processed = True
            ipo.ml_processed_at = datetime.now()
            
            res['ipo_id'] = ipo.id
            results.append(res)
            
        except Exception as e:
             errors.append({"id": ipo.id, "error": str(e)})
             
    db.commit()
    
    return {
        "success": True,
        "processed": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors
    }


@router.get("/high-volatility-alert")
async def get_high_volatility_ipos(db: Session = Depends(get_db)):
    """Get list of IPOs with HIGH or VERY HIGH volatility"""
    
    # We query from the database, updated by the daily background job or user requests
    high_vol_ipos = db.query(IPO).filter(
        IPO.status == "listed",
        IPO.risk_category.in_(["HIGH", "VERY HIGH"])
    ).order_by(IPO.risk_score.desc()).limit(20).all()
    
    # Format the response
    results = []
    for ipo in high_vol_ipos:
        results.append({
            "id": ipo.id,
            "symbol": ipo.symbol,
            "company_name": ipo.company_name,
            "risk_level": ipo.risk_category,
            "risk_score_percentage": ipo.risk_score,
            "last_updated": ipo.ml_processed_at.isoformat() if ipo.ml_processed_at else None
        })
        
    return {
        "success": True,
        "count": len(results),
        "alerts": results
    }
