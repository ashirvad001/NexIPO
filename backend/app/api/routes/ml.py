# ML API Routes - Phase 5
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.db.database import get_db
from app.services.ml_service import MLService
from app.ml_service.inference.risk_predictor import get_predictor
from app.api.routes.auth import get_current_user

router = APIRouter(prefix="/ml", tags=["Machine Learning"])


@router.post("/predict/{ipo_id}")
async def predict_risk(ipo_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """
    Trigger ML risk prediction for an IPO
    
    Args:
        ipo_id: IPO database ID
        
    Returns:
        Prediction results with risk score, category, and explanation
    """
    try:
        result = await MLService.predict_risk(ipo_id, db)
        return {
            "message": "Risk prediction completed successfully",
            **result
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.post("/predict/batch")
async def predict_batch(
    ipo_ids: List[int],
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Trigger batch ML predictions for multiple IPOs
    
    Args:
        ipo_ids: List of IPO database IDs
        
    Returns:
        Batch job status
    """
    async def process_batch():
        results = []
        for ipo_id in ipo_ids:
            try:
                result = await MLService.predict_risk(ipo_id, db)
                results.append({"ipo_id": ipo_id, "status": "success", **result})
            except Exception as e:
                results.append({"ipo_id": ipo_id, "status": "failed", "error": str(e)})
        return results
    
    background_tasks.add_task(process_batch)
    
    return {
        "message": f"Batch prediction started for {len(ipo_ids)} IPOs",
        "ipo_ids": ipo_ids,
        "status": "processing"
    }


@router.get("/prediction/{ipo_id}")
async def get_prediction(ipo_id: int, db: Session = Depends(get_db)):
    """
    Get existing ML prediction for an IPO
    
    Args:
        ipo_id: IPO database ID
        
    Returns:
        Existing prediction or 404 if not found
    """
    result = await MLService.get_prediction(ipo_id, db)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No ML prediction found for IPO {ipo_id}"
        )
    return result


@router.delete("/prediction/{ipo_id}")
async def delete_prediction(ipo_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    """
    Delete ML prediction for an IPO
    
    Args:
        ipo_id: IPO database ID
        
    Returns:
        Deletion confirmation
    """
    from app.models.ipo import IPO
    
    ipo = db.query(IPO).filter(IPO.id == ipo_id).first()
    if not ipo:
        raise HTTPException(status_code=404, detail=f"IPO {ipo_id} not found")
    
    ipo.risk_score = None
    ipo.risk_category = None
    ipo.ml_processed = False
    ipo.ml_processed_at = None
    db.commit()
    
    return {
        "message": f"ML prediction deleted for IPO {ipo_id}",
        "ipo_id": ipo_id
    }


@router.get("/model/info")
async def get_model_info():
    """
    Get ML model information and metadata
    
    Returns:
        Model type, feature count, version, etc.
    """
    return MLService.get_model_info()


@router.get("/model/performance")
async def get_model_performance():
    """
    Get ML model performance metrics
    
    Returns:
        Training accuracy, F1 scores, and validation metrics
    """
    predictor = get_predictor()
    
    if not predictor.classifier.is_fitted:
        return {
            "message": "Model not trained yet. Run 'python scripts/train_model.py' to train.",
            "is_fitted": False,
            "status": "not_trained"
        }
    
    metrics = getattr(predictor.classifier, "metrics", {})
    if metrics:
        # Return comprehensive performance summary
        return {
            "is_fitted": True,
            "status": "ready",
            "model_type": metrics.get("model_type", "TF-IDF + Logistic Regression"),
            "performance": {
                "test_accuracy": metrics.get("accuracy", metrics.get("test_accuracy")),
                "test_precision": metrics.get("precision_macro", metrics.get("test_precision")),
                "test_recall": metrics.get("recall_macro", metrics.get("test_recall")),
                "test_f1": metrics.get("f1_score_macro", metrics.get("test_f1")),
                "cv_f1_mean": metrics.get("cv_f1_mean"),
                "cv_f1_std": metrics.get("cv_f1_std"),
            },
            "dataset": {
                "total_samples": metrics.get("total_samples", metrics.get("sample_count")),
                "training_samples": metrics.get("training_samples"),
                "test_samples": metrics.get("test_samples"),
                "feature_count": metrics.get("feature_count"),
                "classes": metrics.get("classes", ["low", "medium", "high"]),
            },
            "trained_at": metrics.get("trained_at"),
            "confusion_matrix": metrics.get("confusion_matrix"),
            "class_report": metrics.get("class_report"),
        }
    
    return {
        "is_fitted": True,
        "status": "ready",
        "model_type": "TF-IDF + Logistic Regression",
        "feature_count": len(predictor.feature_extractor.get_feature_names()),
        "message": "Model is fitted but no detailed metrics were persisted. Re-train to see full metrics."
    }


@router.get("/statistics")
async def get_statistics(db: Session = Depends(get_db)):
    """
    Get ML processing statistics
    
    Returns:
        Total IPOs, processed count, risk distribution
    """
    return await MLService.get_statistics(db)


@router.post("/predict-risk")
async def predict_risk_direct(data: Dict[str, Any], current_user=Depends(get_current_user)):
    """
    Direct risk prediction from prospectus text (no database)
    
    Args:
        data: Dictionary with prospectus_text, sections, ipo_data, explain
        
    Returns:
        Risk prediction results
    """
    try:
        predictor = get_predictor()
        result = predictor.predict(
            prospectus_text=data.get("prospectus_text", ""),
            sections=data.get("sections", {}),
            ipo_data=data.get("ipo_data", {}),
            explain=data.get("explain", True)
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.get("/model-status")
async def get_model_status():
    """
    Get ML model status
    
    Returns:
        Model loaded status and readiness
    """
    try:
        predictor = get_predictor()
        metrics = getattr(predictor.classifier, "metrics", {}) or {}
        feat_count = metrics.get(
            "feature_count",
            len(predictor.feature_extractor.get_feature_names())
        )
        return {
            "status": "ready" if predictor.classifier.is_fitted else "not_trained",
            "is_fitted": predictor.classifier.is_fitted,
            "model_type": metrics.get("model_type", "TF-IDF + Logistic Regression"),
            "feature_count": feat_count,
            "total_samples": metrics.get("total_samples", metrics.get("sample_count")),
            "test_f1": metrics.get("f1_score_macro", metrics.get("test_f1")),
            "cv_f1_mean": metrics.get("cv_f1_mean"),
            "trained_at": metrics.get("trained_at"),
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
