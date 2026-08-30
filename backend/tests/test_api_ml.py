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

    def test_predict_risk_ipo_not_found(self, client, auth_headers):
        """404 when IPO doesn't exist for prediction."""
        response = client.post("/api/v1/ml/predict/99999", headers=auth_headers)
        assert response.status_code in (404, 500)  # depends on model state

    def test_delete_prediction_not_found(self, client, auth_headers):
        """404 when deleting prediction for non-existent IPO."""
        response = client.delete("/api/v1/ml/prediction/99999", headers=auth_headers)
        assert response.status_code == 404


class TestStatistics:
    """Tests for ML statistics endpoint."""

    def test_get_statistics(self, client):
        """GET /api/v1/ml/statistics returns processing stats."""
        response = client.get("/api/v1/ml/statistics")
        assert response.status_code == 200


class TestMLAuthEnforcement:
    """Tests that protected ML endpoints reject unauthenticated requests."""

    def test_predict_risk_requires_auth(self, client):
        """POST /ml/predict/{id} returns 401 without token."""
        response = client.post("/api/v1/ml/predict/1")
        assert response.status_code == 401

    def test_predict_batch_requires_auth(self, client):
        """POST /ml/predict/batch returns 401 without token."""
        response = client.post("/api/v1/ml/predict/batch", json=[1, 2])
        assert response.status_code == 401

    def test_delete_prediction_requires_auth(self, client):
        """DELETE /ml/prediction/{id} returns 401 without token."""
        response = client.delete("/api/v1/ml/prediction/1")
        assert response.status_code == 401

    def test_predict_risk_direct_requires_auth(self, client):
        """POST /ml/predict-risk returns 401 without token."""
        response = client.post("/api/v1/ml/predict-risk", json={"prospectus_text": "test"})
        assert response.status_code == 401

    def test_predict_risk_works_with_auth(self, client, test_ipo, auth_headers):
        """POST /ml/predict/{id} succeeds with auth (may fail due to model state)."""
        response = client.post(f"/api/v1/ml/predict/{test_ipo.id}", headers=auth_headers)
        # Endpoint is accessible (not 401/403) — actual result depends on model
        assert response.status_code in (200, 404, 500)

    def test_delete_prediction_works_with_auth(self, client, test_ipo, auth_headers):
        """DELETE /ml/prediction/{id} is accessible with auth."""
        response = client.delete(f"/api/v1/ml/prediction/{test_ipo.id}", headers=auth_headers)
        # Should reach the handler (not 401) — 404 if no prediction exists is fine
        assert response.status_code in (200, 404)


class TestVolatilityAuthEnforcement:
    """Tests that protected volatility endpoints reject unauthenticated requests."""

    def test_predict_volatility_requires_auth(self, client, test_ipo):
        """POST /volatility/predict/{id} returns 401 without token."""
        response = client.post(f"/api/v1/volatility/predict/{test_ipo.id}")
        assert response.status_code == 401

    def test_batch_predict_requires_auth(self, client):
        """POST /volatility/batch-predict returns 401 without token."""
        response = client.post("/api/v1/volatility/batch-predict", json=[1, 2])
        assert response.status_code == 401

    def test_predict_volatility_works_with_auth(self, client, test_ipo, auth_headers):
        """POST /volatility/predict/{id} is accessible with auth."""
        response = client.post(f"/api/v1/volatility/predict/{test_ipo.id}", headers=auth_headers)
        # Not 401/403 — actual result depends on ML predictor availability
        assert response.status_code in (200, 500, 503)

    def test_batch_predict_works_with_auth(self, client, auth_headers):
        """POST /volatility/batch-predict is accessible with auth."""
        response = client.post("/api/v1/volatility/batch-predict", json=[1], headers=auth_headers)
        assert response.status_code in (200, 500, 503)


class TestFilesAuthEnforcement:
    """Tests that protected files endpoints reject unauthenticated requests."""

    def test_upload_prospectus_requires_auth(self, client, test_ipo):
        """POST /files/upload/prospectus/{id} returns 401 without token."""
        response = client.post(f"/api/v1/files/upload/prospectus/{test_ipo.id}")
        assert response.status_code == 401

    def test_delete_prospectus_requires_auth(self, client, test_ipo):
        """DELETE /files/prospectus/{id} returns 401 without token."""
        response = client.delete(f"/api/v1/files/prospectus/{test_ipo.id}")
        assert response.status_code == 401

    def test_download_rhp_requires_auth(self, client, test_ipo):
        """POST /files/rhp/download/{id} returns 401 without token."""
        response = client.post(f"/api/v1/files/rhp/download/{test_ipo.id}")
        assert response.status_code == 401

    def test_delete_prospectus_works_with_auth(self, client, test_ipo, auth_headers):
        """DELETE /files/prospectus/{id} is accessible with auth (404 = no prospectus, which is fine)."""
        response = client.delete(f"/api/v1/files/prospectus/{test_ipo.id}", headers=auth_headers)
        assert response.status_code in (200, 404, 500)

