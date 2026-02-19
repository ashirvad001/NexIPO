import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.ml_service.inference.risk_predictor import RiskPredictor

# Sample prospectus text
text = """
The company faces significant financial risks including high debt levels and 
uncertain market conditions. There are ongoing litigation issues and regulatory 
compliance challenges. The competitive landscape is volatile with adverse 
market trends affecting revenue growth.
"""

sections = {
    'risk_factors': text,
    'financial_information': 'Revenue declined by 15% year-over-year.',
    'management': 'Experienced management team with 20+ years.',
    'business_strategy': 'Focus on market expansion and cost reduction.'
}

ipo_data = {
    'issue_size_rs_cr': 1000,
    'price_band_lower': 200,
    'price_band_upper': 220,
    'total_subscription': 2.5,
    'qib_subscription': 3.2,
    'retail_subscription': 1.8,
    'gmp_percentage': 5.0,
    'pe_ratio': 25,
    'roce': 12.5,
    'roe': 15.0
}

print("🔮 Testing ML Risk Prediction Pipeline...\n")

try:
    predictor = RiskPredictor('models/risk_classifier.joblib')
    
    result = predictor.predict(
        prospectus_text=text,
        sections=sections,
        ipo_data=ipo_data,
        explain=False  # Set to True if SHAP explainer is fitted
    )
    
    if result['success']:
        print(f"✅ Prediction successful!\n")
        print(f"📊 Risk Score: {result['risk_score']}/100")
        print(f"🎯 Risk Category: {result['risk_category'].upper()}")
        print(f"💯 Confidence: {result['confidence']:.2%}")
        print(f"\n📈 Risk Indicators:")
        for key, value in result['risk_indicators'].items():
            print(f"  - {key}: {value}")
    else:
        print(f"❌ Prediction failed: {result.get('error')}")
        
except FileNotFoundError:
    print("❌ Model not found. Please run 'python train_model.py' first.")
except Exception as e:
    print(f"❌ Error: {e}")
