# SHAP Explainer for model interpretability
import numpy as np
from typing import Dict, List, Any


class Explainer:
    """Simple explainer for risk predictions"""
    
    def __init__(self, classifier, feature_extractor):
        self.classifier = classifier
        self.feature_extractor = feature_extractor
    
    def explain(self, features: np.ndarray, feature_names: List[str], top_k: int = 5) -> Dict[str, Any]:
        """
        Generate explanation for prediction
        
        Args:
            features: Feature vector
            feature_names: List of feature names
            top_k: Number of top features to return
            
        Returns:
            Dictionary with top contributing features
        """
        if not self.classifier.is_fitted:
            return {
                "top_features": [],
                "summary": "Model not trained yet"
            }
        
        # Get model coefficients (feature importance)
        try:
            coefficients = self.classifier.model.coef_[0]
            
            # Calculate feature contributions
            contributions = features.flatten() * coefficients
            
            # Get top features by absolute contribution
            top_indices = np.argsort(np.abs(contributions))[-top_k:][::-1]
            
            top_features = []
            for idx in top_indices:
                if idx < len(feature_names):
                    top_features.append({
                        "feature": feature_names[idx],
                        "contribution": float(contributions[idx]),
                        "importance_rank": len(top_features) + 1
                    })
            
            # Generate summary
            summary = self._generate_summary(top_features)
            
            return {
                "top_features": top_features,
                "summary": summary
            }
        except Exception as e:
            return {
                "top_features": [],
                "summary": f"Explanation generation failed: {str(e)}"
            }
    
    def _generate_summary(self, top_features: List[Dict]) -> str:
        """Generate human-readable summary"""
        if not top_features:
            return "No significant features identified"
        
        top_feature = top_features[0]
        feature_name = top_feature['feature']
        
        return f"Risk assessment primarily influenced by {feature_name} and related factors"
