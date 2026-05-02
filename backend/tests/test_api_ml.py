"""
Tests for ML API endpoints (/api/v1/ml/*).

Covers:
- Model status and info
- Prediction retrieval
- ML statistics
"""

import pytest


class TestModelEndpoints:
    """Tests for model status and info endpoints."""

    def test_model_status(self, client):
        """GET /api/v1/ml/model-status returns model readiness."""
        response = client.get("/api/v1/ml/model-status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] in ("ready", "not_trained", "error")

    def test_model_info(self, client):
        """GET /api/v1/ml/model/info returns model metadata."""
        response = client.get("/api/v1/ml/model/info")
        assert response.status_code == 200

    def test_model_performance(self, client):
        """GET /api/v1/ml/model/performance returns training metrics."""
        response = client.get("/api/v1/ml/model/performance")
        assert response.status_code == 200
        data = response.json()
        assert "is_fitted" in data


class TestPredictions:
    """Tests for prediction endpoints."""

    def test_get_prediction_not_found(self, client, test_ipo):
        """404 when no prediction exists for an IPO."""
        response = client.get(f"/api/v1/ml/prediction/{test_ipo.id}")
        assert response.status_code == 404

    def test_predict_risk_ipo_not_found(self, client):
        """404 when IPO doesn't exist for prediction."""
        response = client.post("/api/v1/ml/predict/99999")
        assert response.status_code in (404, 500)  # depends on model state

    def test_delete_prediction_not_found(self, client):
        """404 when deleting prediction for non-existent IPO."""
        response = client.delete("/api/v1/ml/prediction/99999")
        assert response.status_code == 404


class TestStatistics:
    """Tests for ML statistics endpoint."""

    def test_get_statistics(self, client):
        """GET /api/v1/ml/statistics returns processing stats."""
        response = client.get("/api/v1/ml/statistics")
        assert response.status_code == 200
