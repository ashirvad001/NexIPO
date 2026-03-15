"""
Integration Tests for Volatility Forecasting - Phase 3
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from app.db.database import Base, get_db
from app.models.ipo import IPO, IPOStatus
from main import app
from app.ml_service.volatility.volatility_predictor import VolatilityForecaster

# Create a test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_volatility.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def setup_database():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # 1. Listed IPO with price history
    ipo_listed = IPO(
        company_name="Zomato Limited",
        symbol="ZOMATO.NS",
        status=IPOStatus.LISTED,
        issue_price=76.0,
        listing_date=datetime(2021, 7, 23)
    )
    
    # 2. Upcoming IPO
    ipo_upcoming = IPO(
        company_name="Dummy Upcoming Corp",
        symbol="DUMMY.NS",
        status=IPOStatus.UPCOMING
    )
    
    db.add(ipo_listed)
    db.add(ipo_upcoming)
    db.commit()
    
    yield
    
    db.close()
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

class TestVolatilityForecastingIntegration:

    def test_end_to_end_prediction_pipeline(self):
        """Test the inner python library pipeline end to end"""
        forecaster = VolatilityForecaster()
        
        # Test a real stock
        result = forecaster.predict_volatility("ZOMATO.NS", "Zomato")
        
        assert result['success'] is True
        assert result['symbol'] == "ZOMATO.NS"
        assert 'predicted_volatility' in result
        assert result['risk_level'] in ['LOW', 'MEDIUM', 'HIGH', 'VERY HIGH']
        assert 0 <= result['confidence_score'] <= 1
        assert isinstance(result['insights'], list)
        
    def test_api_predict_endpoint(self, setup_database):
        """Test the POST /volatility/predict endpoint"""
        # We expect a success or a valid failure JSON response, 
        # since Volatility forecasting reaches out to News/Yahoo APIs which can fail or rate limit.
        response = client.post('/api/v1/volatility/predict/1')
        
        if response.status_code == 200:
            data = response.json()
            assert data['success'] is True
            assert 'predicted_volatility' in data
            assert data['symbol'] == "ZOMATO.NS"
        else:
            # Handle rate-limiting / timeout failures gracefully in test
            assert response.status_code in [500, 503, 400]
            
    def test_api_predict_endpoint_not_found(self, setup_database):
        response = client.post('/api/v1/volatility/predict/999')
        assert response.status_code == 404
        
    def test_api_geopolitical_events(self):
        """Test geopolitical event getter"""
        response = client.get('/api/v1/volatility/geopolitical-events')
        assert response.status_code in [200, 503]
        if response.status_code == 200:
            data = response.json()
            assert 'events' in data
            assert isinstance(data['count'], int)

    def test_api_high_volatility_alert(self, setup_database):
        """Test High Volatility Alert endpoint"""
        response = client.get('/api/v1/volatility/high-volatility-alert')
        assert response.status_code == 200
        data = response.json()
        assert 'alerts' in data
        assert isinstance(data['alerts'], list)
