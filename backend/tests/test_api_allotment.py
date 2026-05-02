"""
Tests for Allotment Calculator API endpoints (/api/v1/allotment/*).

Covers:
- POST /allotment/calculate/{ipo_id} — probability calculation
- GET  /allotment/calculate/{ipo_id} — GET variant
- GET  /allotment/compare/{ipo_id}  — category comparison
- GET  /allotment/quick/{ipo_id}    — quick summary card
"""

import pytest
from app.models.ipo import IPOStatus


class TestCalculateAllotment:
    """Tests for POST /api/v1/allotment/calculate/{ipo_id}"""

    def test_calculate_oversubscribed(self, client, create_test_ipo):
        """Calculate allotment for an oversubscribed IPO."""
        ipo = create_test_ipo(
            company_name="Hot IPO",
            symbol="HOTIPO",
            lot_size=100,
            price_band_upper=150.0,
            issue_size_rs_cr=500.0,
            retail_subscription=5.0,
            total_subscription=8.0,
        )
        response = client.post(
            f"/api/v1/allotment/calculate/{ipo.id}",
            json={"lots_applied": 1},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["scenario"] == "oversubscribed_draw"
        assert data["probability_pct"] < 100.0
        assert data["expected_lots"] == 1

    def test_calculate_undersubscribed(self, client, create_test_ipo):
        """Calculate allotment for an undersubscribed IPO — 100% probability."""
        ipo = create_test_ipo(
            company_name="Cold IPO",
            symbol="COLDIPO",
            lot_size=100,
            price_band_upper=100.0,
            issue_size_rs_cr=200.0,
            retail_subscription=0.5,
            total_subscription=0.5,
        )
        response = client.post(
            f"/api/v1/allotment/calculate/{ipo.id}",
            json={"lots_applied": 1},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["scenario"] == "undersubscribed"
        assert data["probability_pct"] == 100.0

    def test_calculate_pending(self, client, create_test_ipo):
        """Calculate allotment when subscription data is not available."""
        ipo = create_test_ipo(
            company_name="Pending IPO",
            symbol="PENDING",
            lot_size=100,
            price_band_upper=100.0,
            issue_size_rs_cr=200.0,
            retail_subscription=0.0,
            total_subscription=0.0,
        )
        response = client.post(
            f"/api/v1/allotment/calculate/{ipo.id}",
            json={"lots_applied": 1},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["scenario"] == "pending"

    def test_calculate_missing_fields(self, client, create_test_ipo):
        """422 when IPO is missing required fields (lot_size, etc.)."""
        ipo = create_test_ipo(
            company_name="Incomplete IPO",
            symbol="INCOMPLETE",
            lot_size=None,
            price_band_upper=None,
            issue_size_rs_cr=None,
        )
        response = client.post(
            f"/api/v1/allotment/calculate/{ipo.id}",
            json={"lots_applied": 1},
        )
        assert response.status_code == 422

    def test_calculate_not_found(self, client):
        """404 when IPO doesn't exist."""
        response = client.post(
            "/api/v1/allotment/calculate/99999",
            json={"lots_applied": 1},
        )
        assert response.status_code == 404


class TestCalculateGET:
    """Tests for GET /api/v1/allotment/calculate/{ipo_id}"""

    def test_calculate_get_variant(self, client, create_test_ipo):
        """GET variant of the allotment calculator."""
        ipo = create_test_ipo(
            company_name="GET Test IPO",
            symbol="GETTEST",
            lot_size=50,
            price_band_upper=200.0,
            issue_size_rs_cr=400.0,
            retail_subscription=3.0,
            total_subscription=4.5,
        )
        response = client.get(
            f"/api/v1/allotment/calculate/{ipo.id}?lots_applied=2"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["company_name"] == "GET Test IPO"


class TestCategoryComparison:
    """Tests for GET /api/v1/allotment/compare/{ipo_id}"""

    def test_compare_categories(self, client, active_ipo):
        """Compare allotment across Retail/NII/QIB categories."""
        response = client.get(f"/api/v1/allotment/compare/{active_ipo.id}")
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert "retail" in data["categories"]
        assert data["company_name"] == "Active IPO Corp"

    def test_compare_not_found(self, client):
        """404 when IPO doesn't exist."""
        response = client.get("/api/v1/allotment/compare/99999")
        assert response.status_code == 404


class TestQuickSummary:
    """Tests for GET /api/v1/allotment/quick/{ipo_id}"""

    def test_quick_summary(self, client, active_ipo):
        """Quick summary card for the IPO detail widget."""
        response = client.get(f"/api/v1/allotment/quick/{active_ipo.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is True
        assert "probability_pct" in data
        assert "lot_size" in data

    def test_quick_summary_incomplete_data(self, client, create_test_ipo):
        """Quick summary when IPO data is incomplete."""
        ipo = create_test_ipo(
            company_name="Incomplete",
            symbol="INCMPL",
            lot_size=None,
            price_band_upper=None,
            issue_size_rs_cr=None,
        )
        response = client.get(f"/api/v1/allotment/quick/{ipo.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False
