"""
Tests for the shared feature schema.

Verifies that:
  1. RiskFeatureSchema produces vectors of the correct width and order.
  2. VolatilityFeatureSchema validates feature counts correctly.
  3. Feature names are canonical and ordered.
  4. build_feature_vector round-trips match expected_width.
  5. If a saved model exists, its stored feature count matches the schema.
"""

import json
import os
import sys
from pathlib import Path

import numpy as np
import pytest

# Ensure backend is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ml_service.feature_schema import (
    RISK_CUSTOM_FEATURE_COUNT,
    RISK_CUSTOM_FEATURES,
    SCHEMA_VERSION,
    VOLATILITY_FEATURE_COUNT,
    VOLATILITY_FEATURES,
    RiskFeatureSchema,
    VolatilityFeatureSchema,
    export_feature_spec,
)


# ---------------------------------------------------------------------------
# Risk Classifier Schema Tests
# ---------------------------------------------------------------------------


class TestRiskFeatureSchema:
    """Tests for the Risk Classifier feature schema."""

    def test_custom_feature_count_constant(self):
        """The constant matches the length of the feature definition list."""
        assert RISK_CUSTOM_FEATURE_COUNT == len(RISK_CUSTOM_FEATURES)
        assert RISK_CUSTOM_FEATURE_COUNT == 24

    def test_expected_width_default(self):
        schema = RiskFeatureSchema()
        assert schema.expected_width == 1000 + 24  # default tfidf + custom

    def test_expected_width_custom_tfidf(self):
        schema = RiskFeatureSchema(max_tfidf_features=500)
        assert schema.expected_width == 500 + 24

    def test_custom_feature_names_order(self):
        schema = RiskFeatureSchema()
        names = schema.custom_feature_names()
        assert len(names) == 24
        # First 8 are risk indicators
        assert names[0] == "risk_count"
        assert names[7] == "risk_density"
        # Next 4 are readability
        assert names[8] == "word_count"
        assert names[11] == "avg_sentence_length"
        # Next 8 are section features
        assert names[12] == "risk_factors_word_count"
        assert names[19] == "business_strategy_present"
        # Last 4 are financial metrics
        assert names[20] == "issue_size"
        assert names[23] == "pe_ratio"

    def test_get_feature_names_with_tfidf(self):
        schema = RiskFeatureSchema(max_tfidf_features=3)
        tfidf_names = ["tfidf_a", "tfidf_b", "tfidf_c"]
        all_names = schema.get_feature_names(tfidf_names)
        assert len(all_names) == 3 + 24
        assert all_names[:3] == tfidf_names
        assert all_names[3] == "risk_count"

    def test_get_feature_names_placeholder(self):
        schema = RiskFeatureSchema(max_tfidf_features=5)
        all_names = schema.get_feature_names()
        assert len(all_names) == 5 + 24
        assert all_names[0] == "tfidf_0"
        assert all_names[4] == "tfidf_4"

    def test_build_custom_vector_shape(self):
        schema = RiskFeatureSchema()
        vec = schema.build_custom_vector(
            risk_indicators={"high_risk": 3, "financial_risk": 1},
            text="This is a sample sentence. Another sentence here.",
            sections={"risk_factors": "Some risk text"},
            ipo_data={"issue_size_rs_cr": 500, "pe_ratio": 30},
        )
        assert vec.shape == (24,)
        assert vec.dtype == np.float64

    def test_build_custom_vector_values(self):
        """Verify specific values are placed in the correct positions."""
        schema = RiskFeatureSchema()
        vec = schema.build_custom_vector(
            risk_indicators={
                "high_risk": 5,
                "financial_risk": 2,
                "regulatory_risk": 1,
                "market_risk": 0,
                "operational_risk": 3,
                "negative_indicators": 4,
                "hedging_words": 6,
                "risk_density": 0.05,
            },
            text="hello world",
            sections={},
            ipo_data={"issue_size_rs_cr": 100, "pe_ratio": 20},
        )
        # risk_count = 5
        assert vec[0] == 5.0
        # financial_risk_count = 2
        assert vec[1] == 2.0
        # risk_density = 0.05
        assert vec[7] == pytest.approx(0.05)
        # issue_size = 100
        assert vec[20] == 100.0
        # pe_ratio = 20
        assert vec[23] == 20.0

    def test_build_feature_vector_full(self):
        schema = RiskFeatureSchema(max_tfidf_features=10)
        tfidf = np.ones(10)
        combined = schema.build_feature_vector(
            tfidf_features=tfidf,
            risk_indicators={},
            text="test text here.",
            sections={},
            ipo_data={},
        )
        assert combined.shape == (1, 10 + 24)

    def test_build_feature_vector_width_matches_expected(self):
        """Round-trip: build → check width matches expected_width."""
        schema = RiskFeatureSchema(max_tfidf_features=1000)
        tfidf = np.zeros(1000)
        combined = schema.build_feature_vector(
            tfidf_features=tfidf,
            risk_indicators={},
            text="some text.",
            sections={},
            ipo_data={},
        )
        assert combined.shape[1] == schema.expected_width

    def test_build_feature_vector_rejects_wrong_tfidf_width(self):
        """If tfidf width doesn't match, the assertion should catch it."""
        schema = RiskFeatureSchema(max_tfidf_features=100)
        tfidf = np.zeros(50)  # wrong width
        with pytest.raises(AssertionError, match="Feature vector width mismatch"):
            schema.build_feature_vector(
                tfidf_features=tfidf,
                risk_indicators={},
                text="text.",
                sections={},
                ipo_data={},
            )

    def test_empty_inputs(self):
        """Schema handles empty inputs without crashing."""
        schema = RiskFeatureSchema(max_tfidf_features=5)
        vec = schema.build_custom_vector(
            risk_indicators={},
            text="",
            sections={},
            ipo_data={},
        )
        assert vec.shape == (24,)
        # word_count = 0, sentence_count = 0
        assert vec[8] == 0.0
        assert vec[9] == 0.0


# ---------------------------------------------------------------------------
# Volatility LSTM Schema Tests
# ---------------------------------------------------------------------------


class TestVolatilityFeatureSchema:
    """Tests for the Volatility LSTM feature schema."""

    def test_feature_count_constant(self):
        assert VOLATILITY_FEATURE_COUNT == len(VOLATILITY_FEATURES)
        assert VOLATILITY_FEATURE_COUNT == 8

    def test_expected_width(self):
        schema = VolatilityFeatureSchema()
        assert schema.expected_width == 8

    def test_feature_names_order(self):
        schema = VolatilityFeatureSchema()
        names = schema.feature_names()
        assert names == [
            "log_return",
            "rolling_vol_7d",
            "volume_change",
            "high_low_range",
            "rsi_14",
            "sma_ratio_20",
            "sentiment_proxy",
            "momentum_5d",
        ]

    def test_validate_dataframe_columns_correct(self):
        schema = VolatilityFeatureSchema()
        schema.validate_dataframe_columns(schema.feature_names())  # should not raise

    def test_validate_dataframe_columns_wrong_order(self):
        schema = VolatilityFeatureSchema()
        wrong_order = list(reversed(schema.feature_names()))
        with pytest.raises(ValueError, match="Volatility feature column mismatch"):
            schema.validate_dataframe_columns(wrong_order)

    def test_validate_dataframe_columns_missing(self):
        schema = VolatilityFeatureSchema()
        with pytest.raises(ValueError, match="Volatility feature column mismatch"):
            schema.validate_dataframe_columns(["log_return", "rsi_14"])

    def test_validate_input_size_correct(self):
        schema = VolatilityFeatureSchema()
        schema.validate_input_size(8)  # should not raise

    def test_validate_input_size_wrong(self):
        schema = VolatilityFeatureSchema()
        with pytest.raises(ValueError, match="does not match"):
            schema.validate_input_size(10)


# ---------------------------------------------------------------------------
# feature_spec.json Export Tests
# ---------------------------------------------------------------------------


class TestFeatureSpecExport:
    """Tests for the JSON export helper."""

    def test_export_structure(self):
        spec = export_feature_spec()
        assert spec["schema_version"] == SCHEMA_VERSION
        assert "risk_classifier" in spec
        assert "volatility_lstm" in spec

    def test_risk_classifier_spec(self):
        spec = export_feature_spec()
        rc = spec["risk_classifier"]
        assert rc["max_tfidf_features"] == 1000
        assert rc["custom_feature_count"] == 24
        assert rc["total_width"] == 1024
        assert len(rc["custom_features"]) == 24
        # Verify first feature
        assert rc["custom_features"][0]["name"] == "risk_count"

    def test_volatility_lstm_spec(self):
        spec = export_feature_spec()
        vl = spec["volatility_lstm"]
        assert vl["feature_count"] == 8
        assert len(vl["features"]) == 8
        assert vl["features"][0]["name"] == "log_return"

    def test_json_serialisable(self):
        """export_feature_spec output must be JSON-serialisable."""
        spec = export_feature_spec()
        json_str = json.dumps(spec)
        loaded = json.loads(json_str)
        assert loaded["schema_version"] == SCHEMA_VERSION


# ---------------------------------------------------------------------------
# Model compatibility test (runs only if a saved model exists)
# ---------------------------------------------------------------------------


class TestModelCompatibility:
    """If a trained model file exists, verify its feature count matches."""

    def test_risk_model_feature_count(self):
        """Saved risk model's expected_feature_count matches schema."""
        model_path = Path(__file__).resolve().parent.parent / "models" / "risk_classifier.joblib"
        if not model_path.exists():
            pytest.skip("No saved risk model found — skipping compatibility check")

        import joblib
        data = joblib.load(model_path)
        saved_count = data.get("expected_feature_count")
        if saved_count is None:
            pytest.skip("Model was saved without expected_feature_count metadata")

        schema = RiskFeatureSchema()
        assert saved_count == schema.expected_width, (
            f"Saved model expects {saved_count} features, "
            f"but schema defines {schema.expected_width}"
        )

    def test_volatility_model_input_size(self):
        """Saved LSTM model's input_size matches schema."""
        meta_path = Path(__file__).resolve().parent.parent / "models" / "lstm_volatility_model_meta.pkl"
        if not meta_path.exists():
            pytest.skip("No saved LSTM model metadata found — skipping compatibility check")

        import joblib
        meta = joblib.load(meta_path)
        input_size = meta.get("input_size")
        if input_size is None:
            pytest.skip("LSTM meta does not contain input_size")

        schema = VolatilityFeatureSchema()
        assert input_size == schema.expected_width, (
            f"Saved LSTM model expects input_size={input_size}, "
            f"but schema defines {schema.expected_width}"
        )
