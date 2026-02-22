# Risk Predictor - End-to-end prediction pipeline
from typing import Dict, Any, Optional
import numpy as np

from app.ml_service.preprocessing.text_preprocessor import TextPreprocessor
from app.ml_service.feature_engineering.feature_extractor import FeatureExtractor
from app.ml_service.models.risk_classifier import RiskClassifier
from app.ml_service.inference.explainer import Explainer


class RiskPredictor:
    """End-to-end IPO risk prediction pipeline"""
    
    def __init__(self):
        self.preprocessor = TextPreprocessor()
        self.feature_extractor = FeatureExtractor()
        self.classifier = RiskClassifier()
        self.explainer = Explainer(self.classifier, self.feature_extractor)
    
    def predict(
        self,
        prospectus_text: str,
        sections: Optional[Dict[str, str]] = None,
        ipo_data: Optional[Dict[str, Any]] = None,
        explain: bool = True
    ) -> Dict[str, Any]:
        """
        Predict IPO risk from prospectus
        
        Args:
            prospectus_text: Full prospectus text
            sections: Dictionary of prospectus sections
            ipo_data: IPO metadata (issue_size, price_band, etc.)
            explain: Whether to generate SHAP explanation
            
        Returns:
            Dictionary with risk_score, risk_category, confidence, explanation
        """
        try:
            # Step 1: Preprocess text
            processed_text = self.preprocessor.preprocess(prospectus_text)
            risk_indicators = self.preprocessor.extract_risk_indicators(prospectus_text)
            
            # Step 2: Extract features
            features = self.feature_extractor.extract_features(
                processed_text=processed_text,
                sections=sections or {},
                ipo_data=ipo_data or {},
                risk_indicators=risk_indicators
            )
            
            # Step 3: Predict risk
            if self.classifier.is_fitted:
                prediction = self.classifier.predict(features)[0]
                probabilities = self.classifier.predict_proba(features)[0]
                confidence = float(np.max(probabilities))
            else:
                # Default prediction if model not trained
                prediction = self._default_prediction(risk_indicators)
                confidence = 0.5
            
            # Step 4: Convert to risk score (0-100)
            risk_score = self._calculate_risk_score(prediction, risk_indicators)
            
            # Step 5: Generate explanation
            explanation = None
            if explain:
                feature_names = self.feature_extractor.get_feature_names()
                explanation = self.explainer.explain(features, feature_names, top_k=5)
            
            return {
                "risk_score": risk_score,
                "risk_category": prediction,
                "confidence": confidence,
                "risk_indicators": risk_indicators,
                "explanation": explanation,
                "success": True
            }
        
        except Exception as e:
            return {
                "risk_score": 50,
                "risk_category": "medium",
                "confidence": 0.0,
                "error": str(e),
                "success": False
            }
    
    def _default_prediction(self, risk_indicators: Dict[str, int]) -> str:
        """Generate default prediction based on risk indicators"""
        total_risk = sum(risk_indicators.values())
        
        if total_risk > 50:
            return "high"
        elif total_risk > 20:
            return "medium"
        else:
            return "low"
    
    def _calculate_risk_score(self, risk_category: str, risk_indicators: Dict[str, int]) -> int:
        """Convert risk category to 0-100 score"""
        base_scores = {
            "low": 20,
            "medium": 50,
            "high": 80
        }
        
        base_score = base_scores.get(risk_category, 50)
        
        # Adjust based on risk indicators
        total_risk = sum(risk_indicators.values())
        adjustment = min(total_risk // 2, 15)
        
        final_score = base_score + adjustment
        return max(0, min(100, final_score))
    
    def load_model(self, filepath: str):
        """Load trained model from disk"""
        self.classifier.load(filepath)
        return self
    
    def save_model(self, filepath: str):
        """Save trained model to disk"""
        self.classifier.save(filepath)
        return self


# Singleton instance
_predictor_instance = None


def get_predictor() -> RiskPredictor:
    """Get or create predictor singleton"""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = RiskPredictor()
    return _predictor_instance
