"""
Tests for IPO API endpoints (/api/v1/ipos/*).

Covers:
- IPO creation, retrieval, update, deletion
- Pagination and filtering
- Text search
- Active/upcoming IPO queries
"""

import pytest


class TestCreateIPO:
    """Tests for POST /api/v1/ipos/"""

    def test_create_ipo(self, client):
        """Create a new IPO and verify 201 response."""
        response = client.post("/api/v1/ipos/", json={
            "company_name": "New Tech Ltd",
            "symbol": "NEWTECH",
            "status": "upcoming",
            "ipo_type": "mainboard",
            "price_band_lower": 100.0,
            "price_band_upper": 120.0,
            "issue_size_rs_cr": 300.0,
            "lot_size": 50,
        })
        assert response.status_code == 201
        data = response.json()
        assert data["company_name"] == "New Tech Ltd"
        assert data["symbol"] == "NEWTECH"
        assert data["id"] is not None

    def test_create_ipo_duplicate_symbol(self, client, test_ipo):
        """Reject IPO creation when symbol already exists."""
        response = client.post("/api/v1/ipos/", json={
            "company_name": "Another Corp",
            "symbol": "TESTCORP",  # same as test_ipo
            "status": "upcoming",
            "ipo_type": "mainboard",
        })
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_create_ipo_minimal(self, client):
        """Create IPO with only required fields."""
        response = client.post("/api/v1/ipos/", json={
            "company_name": "Minimal Corp",
        })
        assert response.status_code == 201
        data = response.json()
        assert data["company_name"] == "Minimal Corp"
        assert data["status"] == "upcoming"  # default

    def test_create_ipo_invalid_price_band(self, client):
        """Reject when upper price band < lower price band."""
        response = client.post("/api/v1/ipos/", json={
            "company_name": "Bad Corp",
            "price_band_lower": 200.0,
            "price_band_upper": 100.0,
        })
        assert response.status_code == 422


class TestGetIPOs:
    """Tests for GET /api/v1/ipos/"""

    def test_get_ipos_empty(self, client):
        """Return empty list when no IPOs exist."""
        response = client.get("/api/v1/ipos/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_get_ipos_paginated(self, client, create_test_ipo):
        """Verify pagination structure."""
        for i in range(5):
            create_test_ipo(company_name=f"Corp {i}", symbol=f"CORP{i}")

        response = client.get("/api/v1/ipos/?page=1&page_size=2")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["page_size"] == 2
        assert len(data["items"]) == 2
        assert data["total_pages"] == 3

    def test_get_ipos_filtered_by_status(self, client, create_test_ipo):
        """Filter IPOs by status."""
        create_test_ipo(company_name="Open Corp", symbol="OPEN", status="open")
        create_test_ipo(company_name="Closed Corp", symbol="CLOSED", status="closed")

        response = client.get("/api/v1/ipos/?status=open")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["company_name"] == "Open Corp"

    def test_get_ipos_search(self, client, create_test_ipo):
        """Search IPOs by company name."""
        create_test_ipo(company_name="Alpha Technologies", symbol="ALPHA")
        create_test_ipo(company_name="Beta Services", symbol="BETA")

        response = client.get("/api/v1/ipos/?search=alpha")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert "Alpha" in data["items"][0]["company_name"]


class TestGetSingleIPO:
    """Tests for GET /api/v1/ipos/{ipo_id} and /api/v1/ipos/symbol/{symbol}"""

    def test_get_ipo_by_id(self, client, test_ipo):
        """Retrieve a single IPO by ID."""
        response = client.get(f"/api/v1/ipos/{test_ipo.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_ipo.id
        assert data["company_name"] == "Test Corp Ltd"

    def test_get_ipo_by_id_not_found(self, client):
        """404 when IPO ID doesn't exist."""
        response = client.get("/api/v1/ipos/99999")
        assert response.status_code == 404

    def test_get_ipo_by_symbol(self, client, test_ipo):
        """Retrieve IPO by stock symbol."""
        response = client.get(f"/api/v1/ipos/symbol/{test_ipo.symbol}")
        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "TESTCORP"

    def test_get_ipo_by_symbol_not_found(self, client):
        """404 when symbol doesn't exist."""
        response = client.get("/api/v1/ipos/symbol/NOSYMBOL")
        assert response.status_code == 404


class TestUpdateIPO:
    """Tests for PUT /api/v1/ipos/{ipo_id}"""

    def test_update_ipo(self, client, test_ipo):
        """Partial update of an IPO."""
        response = client.put(f"/api/v1/ipos/{test_ipo.id}", json={
            "status": "open",
            "issue_size_rs_cr": 750.0,
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "open"
        assert data["issue_size_rs_cr"] == 750.0

    def test_update_ipo_not_found(self, client):
        """404 when updating non-existent IPO."""
        response = client.put("/api/v1/ipos/99999", json={
            "status": "closed",
        })
        assert response.status_code == 404


class TestDeleteIPO:
    """Tests for DELETE /api/v1/ipos/{ipo_id}"""

    def test_delete_ipo(self, client, test_ipo):
        """Delete an IPO and verify 204."""
        response = client.delete(f"/api/v1/ipos/{test_ipo.id}")
        assert response.status_code == 204

        # Verify it's gone
        response = client.get(f"/api/v1/ipos/{test_ipo.id}")
        assert response.status_code == 404

    def test_delete_ipo_not_found(self, client):
        """404 when deleting non-existent IPO."""
        response = client.delete("/api/v1/ipos/99999")
        assert response.status_code == 404


class TestSpecializedQueries:
    """Tests for /active and /upcoming endpoints"""

    def test_get_active_ipos(self, client, active_ipo, test_ipo):
        """Only returns IPOs currently open for subscription."""
        response = client.get("/api/v1/ipos/active")
        assert response.status_code == 200
        data = response.json()
        # active_ipo has open_date in the past and close_date in the future
        symbols = [ipo["symbol"] for ipo in data]
        assert "ACTIVE" in symbols

    def test_get_upcoming_ipos(self, client, test_ipo):
        """Returns upcoming IPOs."""
        response = client.get("/api/v1/ipos/upcoming?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
