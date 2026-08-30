import numpy as np
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ml_service.preprocessing.text_preprocessor import TextPreprocessor
from app.ml_service.feature_engineering.feature_extractor import FeatureExtractor
from app.ml_service.models.risk_classifier import IPORiskClassifier

# Sample training data
texts = [
    "Strong financial position with consistent revenue growth and minimal debt obligations.",
    "Company faces moderate competition and regulatory challenges in the market.",
    "Significant risks including high debt, litigation issues, and volatile market conditions.",
] * 30  # Duplicate to create 90 samples

labels = [0, 1, 2] * 30  # 0=low, 1=medium, 2=high

print("🚀 Starting ML model training...")
print(f"📊 Training samples: {len(texts)}")

# Preprocess
preprocessor = TextPreprocessor()
processed_texts = [preprocessor.preprocess(t, return_string=True) for t in texts]
risk_indicators = [preprocessor.extract_risk_indicators(t) for t in texts]
print("✅ Text preprocessing complete")

# Extract features
extractor = FeatureExtractor(max_features=500)
sections = [{'risk_factors': t[:200]} for t in texts]
ipo_data = [{'issue_size_rs_cr': 1000, 'pe_ratio': 25, 'price_band_lower': 100, 'price_band_upper': 120}] * len(texts)

X, feature_names = extractor.fit_transform(processed_texts, risk_indicators, sections, ipo_data)
y = np.array(labels)
print(f"✅ Feature extraction complete: {X.shape[1]} features")

# Train model
classifier = IPORiskClassifier()
metrics = classifier.train(X, y, feature_names, test_size=0.2, cv_folds=3)

print("\n📈 Training Results:")
print(f"  Test Accuracy: {metrics['test_accuracy']:.4f}")
print(f"  Test F1 Score: {metrics['test_f1_macro']:.4f}")
print(f"  CV F1 Mean: {metrics['cv_f1_mean']:.4f} ± {metrics['cv_f1_std']:.4f}")

# Save model
Path('models').mkdir(exist_ok=True)
classifier.save('models/risk_classifier.joblib')
print("\n✅ Model saved to models/risk_classifier.joblib")
print("🎉 Training complete!")
