"""
Unit tests for the Allotment Probability Calculator (pure logic, no database).

Tests the core SEBI allotment algorithm implementation directly.
"""

import pytest
from app.services.allotment_calculator import (
    calculate_allotment_probability,
    get_category_comparison,
)


class TestAllotmentCalculation:
    """Unit tests for calculate_allotment_probability()"""

    def test_oversubscribed_draw(self):
        """Heavily oversubscribed IPO triggers lucky draw scenario."""
        result = calculate_allotment_probability(
            lot_size=100,
            price_band_upper=150.0,
            issue_size_rs_cr=500.0,
            retail_subscription=5.0,
            total_subscription=8.0,
            lots_applied=1,
        )
        assert result["success"] is True
        assert result["scenario"] == "oversubscribed_draw"
        assert result["probability_pct"] < 100.0
        assert result["probability_pct"] > 0
        assert result["expected_lots"] == 1
        assert "lucky draw" in result["allotment_note"].lower()

    def test_undersubscribed(self):
        """Undersubscribed IPO gives 100% allotment probability."""
        result = calculate_allotment_probability(
            lot_size=100,
            price_band_upper=100.0,
            issue_size_rs_cr=200.0,
            retail_subscription=0.5,
            total_subscription=0.5,
            lots_applied=1,
        )
        assert result["success"] is True
        assert result["scenario"] == "undersubscribed"
        assert result["probability_pct"] == 100.0
        assert result["expected_lots"] == 1

    def test_lightly_oversubscribed(self):
        """1.0 < subscription < 2.0 is lightly oversubscribed."""
        result = calculate_allotment_probability(
            lot_size=100,
            price_band_upper=100.0,
            issue_size_rs_cr=200.0,
            retail_subscription=1.5,
            total_subscription=1.5,
            lots_applied=1,
        )
        assert result["success"] is True
        assert result["scenario"] == "lightly_oversubscribed"

    def test_pending_subscription(self):
        """Zero subscription returns pending scenario."""
        result = calculate_allotment_probability(
            lot_size=100,
            price_band_upper=100.0,
            issue_size_rs_cr=200.0,
            retail_subscription=0.0,
            total_subscription=0.0,
            lots_applied=1,
        )
        assert result["success"] is True
        assert result["scenario"] == "pending"
        assert result["probability_pct"] is None

    def test_invalid_lot_size(self):
        """Negative lot_size returns error."""
        result = calculate_allotment_probability(
            lot_size=-1,
            price_band_upper=100.0,
            issue_size_rs_cr=200.0,
            retail_subscription=1.0,
            total_subscription=1.0,
            lots_applied=1,
        )
        assert result["success"] is False
        assert "lot_size" in str(result["errors"])

    def test_invalid_price(self):
        """Zero price returns error."""
        result = calculate_allotment_probability(
            lot_size=100,
            price_band_upper=0,
            issue_size_rs_cr=200.0,
            retail_subscription=1.0,
            total_subscription=1.0,
            lots_applied=1,
        )
        assert result["success"] is False

    def test_invalid_issue_size(self):
        """Zero issue size returns error."""
        result = calculate_allotment_probability(
            lot_size=100,
            price_band_upper=100.0,
            issue_size_rs_cr=0,
            retail_subscription=1.0,
            total_subscription=1.0,
            lots_applied=1,
        )
        assert result["success"] is False

    def test_multiple_lots_applied(self):
        """Applying multiple lots in undersubscribed scenario gives all lots."""
        result = calculate_allotment_probability(
            lot_size=50,
            price_band_upper=100.0,
            issue_size_rs_cr=300.0,
            retail_subscription=0.5,
            total_subscription=0.5,
            lots_applied=3,
        )
        assert result["success"] is True
        assert result["expected_lots"] == 3

    def test_nii_warning_triggered(self):
        """Application exceeding ₹2L triggers NII/HNI warning."""
        result = calculate_allotment_probability(
            lot_size=100,
            price_band_upper=2500.0,  # 100 * 2500 = ₹2.5L > ₹2L threshold
            issue_size_rs_cr=1000.0,
            retail_subscription=2.0,
            total_subscription=3.0,
            lots_applied=1,
        )
        assert result["success"] is True
        assert result["insights"]["nii_warning"] is not None
        assert "hni" in result["insights"]["nii_warning"].lower()

    def test_nii_warning_not_triggered(self):
        """Application under ₹2L doesn't trigger NII warning."""
        result = calculate_allotment_probability(
            lot_size=100,
            price_band_upper=150.0,  # 100 * 150 = ₹15K < ₹2L
            issue_size_rs_cr=500.0,
            retail_subscription=2.0,
            total_subscription=3.0,
            lots_applied=1,
        )
        assert result["success"] is True
        assert result["insights"]["nii_warning"] is None

    def test_breakdown_structure(self):
        """Verify breakdown dict has all expected keys."""
        result = calculate_allotment_probability(
            lot_size=100,
            price_band_upper=150.0,
            issue_size_rs_cr=500.0,
            retail_subscription=3.0,
            total_subscription=5.0,
            lots_applied=1,
        )
        assert "breakdown" in result
        breakdown = result["breakdown"]
        assert "retail_shares_available" in breakdown
        assert "retail_lots_available" in breakdown
        assert "estimated_applications" in breakdown
        assert "retail_subscription" in breakdown
        assert "retail_portion_pct" in breakdown

    def test_application_info_structure(self):
        """Verify application dict has all expected keys."""
        result = calculate_allotment_probability(
            lot_size=50,
            price_band_upper=200.0,
            issue_size_rs_cr=300.0,
            retail_subscription=1.5,
            total_subscription=2.0,
            lots_applied=2,
        )
        assert "application" in result
        app_info = result["application"]
        assert app_info["lots_applied"] == 2
        assert app_info["shares_applied"] == 100  # 2 * 50
        assert app_info["application_amount_rs"] == 20000.0  # 2 * 50 * 200
        assert app_info["min_lot_size"] == 50

    def test_sme_ipo_type(self):
        """SME IPOs use the same 35% retail portion."""
        result = calculate_allotment_probability(
            lot_size=100,
            price_band_upper=100.0,
            issue_size_rs_cr=50.0,
            retail_subscription=3.0,
            total_subscription=3.0,
            ipo_type="sme",
            lots_applied=1,
        )
        assert result["success"] is True
        assert result["breakdown"]["retail_portion_pct"] == 35.0


class TestCategoryComparison:
    """Unit tests for get_category_comparison()"""

    def test_all_categories_present(self):
        """Compare all three categories when data is available."""
        result = get_category_comparison(
            lot_size=100,
            price_band_upper=150.0,
            issue_size_rs_cr=500.0,
            retail_subscription=5.0,
            nii_subscription=3.0,
            qib_subscription=10.0,
        )
        assert "categories" in result
        cats = result["categories"]
        assert "retail" in cats
        assert "nii" in cats
        assert "qib" in cats

    def test_retail_only(self):
        """Only retail category when NII/QIB data is missing."""
        result = get_category_comparison(
            lot_size=100,
            price_band_upper=150.0,
            issue_size_rs_cr=500.0,
            retail_subscription=5.0,
            nii_subscription=None,
            qib_subscription=None,
        )
        cats = result["categories"]
        assert "retail" in cats
        assert "nii" not in cats
        assert "qib" not in cats

    def test_category_labels(self):
        """Verify human-readable labels are set."""
        result = get_category_comparison(
            lot_size=100,
            price_band_upper=150.0,
            issue_size_rs_cr=500.0,
            retail_subscription=3.0,
            nii_subscription=2.0,
            qib_subscription=8.0,
        )
        assert result["categories"]["retail"]["label"] == "Retail (RII)"
        assert result["categories"]["nii"]["label"] == "HNI/NII"
        assert result["categories"]["qib"]["label"] == "QIB"
