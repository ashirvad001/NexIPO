# Risk Classifier - Logistic Regression Model
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import numpy as np
import joblib
import os


class RiskClassifier:
    """Logistic Regression classifier for IPO risk prediction"""
    
    def __init__(self):
        self.model = LogisticRegression(
            class_weight='balanced',
            max_iter=1000,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.classes_ = ['low', 'medium', 'high']
    
    def train(self, X, y):
        """Train the classifier"""
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.is_fitted = True
        return self
    
    def predict(self, X):
        """Predict risk category"""
        if not self.is_fitted:
            # Return default prediction if not trained
            return np.array(['medium'] * len(X))
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict(X_scaled)
    
    def predict_proba(self, X):
        """Predict probability for each class"""
        if not self.is_fitted:
            # Return uniform probabilities if not trained
            n_samples = len(X)
            return np.full((n_samples, 3), 1/3)
        
        X_scaled = self.scaler.transform(X)
        return self.model.predict_proba(X_scaled)
    
    def save(self, filepath):
        """Save model to disk"""
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'is_fitted': self.is_fitted,
            'classes': self.classes_
        }, filepath)
    
    def load(self, filepath):
        """Load model from disk"""
        if os.path.exists(filepath):
            data = joblib.load(filepath)
            self.model = data['model']
            self.scaler = data['scaler']
            self.is_fitted = data['is_fitted']
            self.classes_ = data['classes']
        return self
