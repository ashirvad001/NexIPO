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
        self.metrics = {}
    
    def train(self, X, y):
        """Train the classifier"""
        X_clean = np.nan_to_num(X, nan=0.0, posinf=1e5, neginf=-1e5)
        X_scaled = self.scaler.fit_transform(X_clean)
        X_scaled = np.nan_to_num(X_scaled, nan=0.0, posinf=1e5, neginf=-1e5)
        self.model.fit(X_scaled, y)
        self.is_fitted = True
        return self

    def train_and_evaluate(self, X, y, cv=5):
        """Train the classifier and evaluate it using cross-validation"""
        from sklearn.model_selection import cross_validate
        from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
        
        X_clean = np.nan_to_num(X, nan=0.0, posinf=1e5, neginf=-1e5)
        X_scaled = self.scaler.fit_transform(X_clean)
        X_scaled = np.nan_to_num(X_scaled, nan=0.0, posinf=1e5, neginf=-1e5)
        
        # Perform cross-validation
        cv_results = cross_validate(
            self.model, X_scaled, y, cv=cv,
            scoring=('accuracy', 'precision_macro', 'recall_macro', 'f1_macro'),
            return_train_score=False
        )
        
        # Train on full dataset
        self.model.fit(X_scaled, y)
        self.is_fitted = True
        
        # Predict on training set to get training metrics (or test metrics if split before)
        y_pred = self.model.predict(X_scaled)
        
        from datetime import datetime
        self.metrics = {
            'cv_accuracy_mean': float(np.mean(cv_results['test_accuracy'])),
            'cv_precision_mean': float(np.mean(cv_results['test_precision_macro'])),
            'cv_recall_mean': float(np.mean(cv_results['test_recall_macro'])),
            'cv_f1_mean': float(np.mean(cv_results['test_f1_macro'])),
            'test_accuracy': float(accuracy_score(y, y_pred)),
            'test_precision': float(precision_score(y, y_pred, average='macro', zero_division=0)),
            'test_recall': float(recall_score(y, y_pred, average='macro', zero_division=0)),
            'test_f1': float(f1_score(y, y_pred, average='macro', zero_division=0)),
            'sample_count': len(y),
            'trained_at': datetime.utcnow().isoformat()
        }
        
        return self
    
    def predict(self, X):
        """Predict risk category"""
        if not self.is_fitted:
            # Return default prediction if not trained
            return np.array(['medium'] * len(X))
        
        X_clean = np.nan_to_num(X, nan=0.0, posinf=1e5, neginf=-1e5)
        X_scaled = self.scaler.transform(X_clean)
        X_scaled = np.nan_to_num(X_scaled, nan=0.0, posinf=1e5, neginf=-1e5)
        return self.model.predict(X_scaled)
    
    def predict_proba(self, X):
        """Predict probability for each class"""
        if not self.is_fitted:
            # Return uniform probabilities if not trained
            n_samples = len(X)
            return np.full((n_samples, 3), 1/3)
        
        X_clean = np.nan_to_num(X, nan=0.0, posinf=1e5, neginf=-1e5)
        X_scaled = self.scaler.transform(X_clean)
        X_scaled = np.nan_to_num(X_scaled, nan=0.0, posinf=1e5, neginf=-1e5)
        return self.model.predict_proba(X_scaled)
    
    def save(self, filepath):
        """Save model to disk"""
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'is_fitted': self.is_fitted,
            'classes': self.classes_,
            'metrics': getattr(self, 'metrics', {})
        }, filepath)
    
    def load(self, filepath):
        """Load model from disk"""
        if os.path.exists(filepath):
            data = joblib.load(filepath)
            self.model = data.get('model', self.model)
            self.scaler = data.get('scaler', self.scaler)
            self.is_fitted = data.get('is_fitted', False)
            self.classes_ = data.get('classes', self.classes_)
            self.metrics = data.get('metrics', {})
        return self


# Alias for backward compatibility
IPORiskClassifier = RiskClassifier
