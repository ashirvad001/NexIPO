"""
Tests for Model Accuracy API endpoints (/api/v1/model-accuracy/*).

Covers:
- GET /api/v1/model-accuracy (empty and populated)
- GET /api/v1/model-accuracy/summary (aggregate stats calculation)
- Filtering and sorting on /api/v1/model-accuracy
- Public access without auth headers
"""

import pytest
from datetime import datetime
from app.models.ipo import IPO, IPOStatus, IPOType
from app.models.prediction_log import PredictionLog


class TestModelAccuracyEndpoints:
    """Tests for public model accuracy endpoints."""

    def test_get_model_accuracy_empty(self, client):
        """Should return empty records list when no predictions exist."""
        response = client.get("/api/v1/model-accuracy")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 0
        assert data["records"] == []

    def test_get_model_accuracy_summary_empty(self, client):
        """Should return empty summary when no predictions exist."""
        response = client.get("/api/v1/model-accuracy/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["sample_size"] == 0
        assert data["overall_accuracy"] is None
        assert data["mean_absolute_error"] is None

    def test_model_accuracy_with_data(self, client, db_session):
        """Test accuracy calculation and summary with populated prediction logs and IPOs."""
        # 1. Mainboard IPO - Directionally correct (predicted +15%, actual +20%)
        ipo1 = IPO(
            company_name="Alpha Tech Ltd",
            symbol="ALPHATECH",
            status=IPOStatus.LISTED,
            ipo_type=IPOType.MAINBOARD,
            issue_price=100.0,
            listing_price=120.0,  # actual gain: +20%
            listing_date=datetime(2025, 1, 15),
        )
        # 2. Mainboard IPO - Directionally incorrect (predicted +10%, actual -10%)
        ipo2 = IPO(
            company_name="Beta Retail Ltd",
            symbol="BETARETAIL",
            status=IPOStatus.LISTED,
            ipo_type=IPOType.MAINBOARD,
            issue_price=200.0,
            listing_price=180.0,  # actual gain: -10%
            listing_date=datetime(2025, 2, 10),
        )
        # 3. SME IPO - Directionally correct (predicted +30%, actual +50%)
        ipo3 = IPO(
            company_name="Gamma SME Ltd",
            symbol="GAMMASME",
            status=IPOStatus.LISTED,
            ipo_type=IPOType.SME,
            issue_price=50.0,
            listing_price=75.0,  # actual gain: +50%
            listing_date=datetime(2025, 3, 5),
        )

        db_session.add_all([ipo1, ipo2, ipo3])
        db_session.commit()

        # Add PredictionLogs
        log1 = PredictionLog(
            ipo_id=ipo1.id,
            predicted_gain=15.0,
            predicted_at=datetime(2025, 1, 10),
            model_version="bert-lstm-v1",
        )
        log2 = PredictionLog(
            ipo_id=ipo2.id,
            predicted_gain=10.0,
            predicted_at=datetime(2025, 2, 5),
            model_version="bert-lstm-v1",
        )
        log3 = PredictionLog(
            ipo_id=ipo3.id,
            predicted_gain=30.0,
            predicted_at=datetime(2025, 3, 1),
            model_version="bert-lstm-v1",
        )
        db_session.add_all([log1, log2, log3])
        db_session.commit()

        # Test GET /api/v1/model-accuracy
        res = client.get("/api/v1/model-accuracy")
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert data["count"] == 3
        
        # Check specific records
        alpha = next(r for r in data["records"] if r["company_name"] == "Alpha Tech Ltd")
        assert alpha["predicted_gain"] == 15.0
        assert alpha["actual_gain"] == 20.0
        assert alpha["error"] == 5.0
        assert alpha["directionally_correct"] is True
        assert alpha["ipo_type"] == "mainboard"

        beta = next(r for r in data["records"] if r["company_name"] == "Beta Retail Ltd")
        assert beta["predicted_gain"] == 10.0
        assert beta["actual_gain"] == -10.0
        assert beta["error"] == 20.0
        assert beta["directionally_correct"] is False

        # Test filtering by ipo_type=sme
        sme_res = client.get("/api/v1/model-accuracy?ipo_type=sme")
        assert sme_res.status_code == 200
        sme_data = sme_res.json()
        assert sme_data["count"] == 1
        assert sme_data["records"][0]["company_name"] == "Gamma SME Ltd"

        # Test search filter
        search_res = client.get("/api/v1/model-accuracy?search=Alpha")
        assert search_res.status_code == 200
        assert search_res.json()["count"] == 1

        # Test GET /api/v1/model-accuracy/summary
        sum_res = client.get("/api/v1/model-accuracy/summary")
        assert sum_res.status_code == 200
        sum_data = sum_res.json()
        assert sum_data["success"] is True
        assert sum_data["sample_size"] == 3
        # 2 correct out of 3 = 66.7%
        assert sum_data["overall_accuracy"] == 66.7
        # MAE: (5 + 20 + 20) / 3 = 45 / 3 = 15.0
        assert sum_data["mean_absolute_error"] == 15.0
        # Breakdown
        assert sum_data["breakdown"]["mainboard"]["sample_size"] == 2
        assert sum_data["breakdown"]["mainboard"]["accuracy"] == 50.0
        assert sum_data["breakdown"]["sme"]["sample_size"] == 1
        assert sum_data["breakdown"]["sme"]["accuracy"] == 100.0
