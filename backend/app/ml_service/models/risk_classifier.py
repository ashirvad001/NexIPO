# Risk Classifier - Logistic Regression Model
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import f1_score, accuracy_score
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
        self.expected_feature_count = None

    def train(self, X, y):
        """Train the classifier"""
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled, y)
        self.is_fitted = True
        self.expected_feature_count = X.shape[1]
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
            'classes': self.classes_,
            'expected_feature_count': self.expected_feature_count,
        }, filepath)

    def load(self, filepath):
        """Load model from disk"""
        if os.path.exists(filepath):
            data = joblib.load(filepath)
            self.model = data['model']
            self.scaler = data['scaler']
            self.is_fitted = data['is_fitted']
            self.classes_ = data['classes']
            self.expected_feature_count = data.get('expected_feature_count')
        return self


class IPORiskClassifier(RiskClassifier):
    """Extended Risk Classifier with cross-validation and train/test split.

    This is the class used by ``train_model.py``.  It extends the base
    ``RiskClassifier`` with convenience parameters for ``test_size`` and
    ``cv_folds``, and stores the trained ``feature_names`` for later
    introspection.
    """

    def __init__(self):
        super().__init__()
        self.feature_names = None

    def train(self, X, y, feature_names=None, test_size=0.2, cv_folds=3):
        """Train with train/test split and cross-validation.

        Args:
            X: Feature matrix (n_samples, n_features).
            y: Labels array.
            feature_names: Optional list of feature names.
            test_size: Fraction of data held out for test evaluation.
            cv_folds: Number of cross-validation folds.

        Returns:
            dict with training metrics.
        """
        self.feature_names = feature_names
        self.expected_feature_count = X.shape[1]

        # Train / test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y,
        )

        # Fit scaler on training data
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        # Train model
        self.model.fit(X_train_scaled, y_train)
        self.is_fitted = True

        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        test_accuracy = accuracy_score(y_test, y_pred)
        test_f1 = f1_score(y_test, y_pred, average='macro')

        # Cross-validation on full (scaled) data
        X_all_scaled = self.scaler.transform(X)
        cv_scores = cross_val_score(
            self.model, X_all_scaled, y,
            cv=cv_folds, scoring='f1_macro',
        )

        return {
            'test_accuracy': test_accuracy,
            'test_f1_macro': test_f1,
            'cv_f1_mean': cv_scores.mean(),
            'cv_f1_std': cv_scores.std(),
        }

    def save(self, filepath):
        """Save model with feature names."""
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'is_fitted': self.is_fitted,
            'classes': self.classes_,
            'expected_feature_count': self.expected_feature_count,
            'feature_names': self.feature_names,
        }, filepath)

    def load(self, filepath):
        """Load model with feature names."""
        if os.path.exists(filepath):
            data = joblib.load(filepath)
            self.model = data['model']
            self.scaler = data['scaler']
            self.is_fitted = data['is_fitted']
            self.classes_ = data['classes']
            self.expected_feature_count = data.get('expected_feature_count')
            self.feature_names = data.get('feature_names')
        return self
