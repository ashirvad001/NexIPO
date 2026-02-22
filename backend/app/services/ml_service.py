# ML Service for IPO Risk Prediction
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.ipo import IPO
from app.ml_service.inference.risk_predictor import get_predictor
from app.core.mongodb import MongoDB


class MLService:
    """Service for ML predictions and risk assessment"""
    
    _predictor = None
    
    @classmethod
    def get_predictor(cls):
        """Get or initialize predictor singleton"""
        if cls._predictor is None:
            cls._predictor = get_predictor()
        return cls._predictor
    
    @classmethod
    async def predict_risk(cls, ipo_id: int, db: Session) -> Dict[str, Any]:
        """
        Predict risk for an IPO using its prospectus
        
        Args:
            ipo_id: IPO database ID
            db: Database session
            
        Returns:
            Prediction results with risk score, category, and explanation
        """
        # Get IPO from database
        ipo = db.query(IPO).filter(IPO.id == ipo_id).first()
        if not ipo:
            raise ValueError(f"IPO with id {ipo_id} not found")
        
        if not ipo.prospectus_file_id:
            raise ValueError(f"No prospectus uploaded for IPO {ipo_id}")
        
        # Get prospectus from MongoDB
        prospectus_coll = MongoDB.get_prospectus_collection()
        prospectus_doc = await prospectus_coll.find_one({"_id": ipo.prospectus_file_id})
        
        if not prospectus_doc:
            raise ValueError(f"Prospectus not found in MongoDB")
        
        # Get predictor and make prediction
        predictor = cls.get_predictor()
        
        # Prepare input data
        prospectus_text = prospectus_doc.get("full_text", "")
        sections = prospectus_doc.get("sections", {})
        
        ipo_data = {
            "issue_size_rs_cr": ipo.issue_size_rs_cr,
            "price_band_lower": ipo.price_band_lower,
            "price_band_upper": ipo.price_band_upper,
            "total_subscription": ipo.total_subscription,
            "gmp_percentage": ipo.gmp_percentage
        }
        
        # Make prediction
        result = predictor.predict(
            prospectus_text=prospectus_text,
            sections=sections,
            ipo_data=ipo_data,
            explain=True
        )
        
        # Update IPO record
        ipo.risk_score = result["risk_score"]
        ipo.risk_category = result["risk_category"]
        ipo.ml_processed = True
        ipo.ml_processed_at = datetime.utcnow()
        db.commit()
        db.refresh(ipo)
        
        # Store explanation in MongoDB
        if result.get("explanation"):
            await prospectus_coll.update_one(
                {"_id": ipo.prospectus_file_id},
                {"$set": {
                    "ml_prediction": {
                        "risk_score": result["risk_score"],
                        "risk_category": result["risk_category"],
                        "confidence": result.get("confidence"),
                        "explanation": result["explanation"],
                        "predicted_at": datetime.utcnow()
                    }
                }}
            )
        
        return {
            "ipo_id": ipo_id,
            "risk_score": result["risk_score"],
            "risk_category": result["risk_category"],
            "confidence": result.get("confidence"),
            "risk_indicators": result.get("risk_indicators"),
            "explanation": result.get("explanation"),
            "success": True
        }
    
    @classmethod
    async def get_prediction(cls, ipo_id: int, db: Session) -> Optional[Dict[str, Any]]:
        """Get existing prediction for an IPO"""
        ipo = db.query(IPO).filter(IPO.id == ipo_id).first()
        if not ipo or not ipo.ml_processed:
            return None
        
        # Get explanation from MongoDB if available
        explanation = None
        if ipo.prospectus_file_id:
            prospectus_coll = MongoDB.get_prospectus_collection()
            prospectus_doc = await prospectus_coll.find_one({"_id": ipo.prospectus_file_id})
            if prospectus_doc and "ml_prediction" in prospectus_doc:
                explanation = prospectus_doc["ml_prediction"].get("explanation")
        
        return {
            "ipo_id": ipo_id,
            "risk_score": ipo.risk_score,
            "risk_category": ipo.risk_category,
            "ml_processed_at": ipo.ml_processed_at,
            "explanation": explanation
        }
    
    @classmethod
    def get_model_info(cls) -> Dict[str, Any]:
        """Get ML model information"""
        predictor = cls.get_predictor()
        return {
            "model_type": "Logistic Regression",
            "is_fitted": predictor.classifier.is_fitted,
            "feature_count": 1034,
            "risk_categories": ["low", "medium", "high"],
            "version": "1.0.0"
        }
    
    @classmethod
    async def get_statistics(cls, db: Session) -> Dict[str, Any]:
        """Get ML processing statistics"""
        total_ipos = db.query(IPO).count()
        processed_ipos = db.query(IPO).filter(IPO.ml_processed == True).count()
        
        low_risk = db.query(IPO).filter(IPO.risk_category == "low").count()
        medium_risk = db.query(IPO).filter(IPO.risk_category == "medium").count()
        high_risk = db.query(IPO).filter(IPO.risk_category == "high").count()
        
        return {
            "total_ipos": total_ipos,
            "processed_ipos": processed_ipos,
            "pending_ipos": total_ipos - processed_ipos,
            "risk_distribution": {
                "low": low_risk,
                "medium": medium_risk,
                "high": high_risk
            }
        }
