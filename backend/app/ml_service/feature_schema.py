"""
Shared Feature Schema — Single Source of Truth
================================================
Defines the exact ordered feature lists, types, and transformations for
BOTH ML pipelines in NexIPO:

  1. Risk Classifier  (TF-IDF + Logistic Regression)
  2. Volatility LSTM  (BiLSTM + BERT sentiment)

Every training script and serving/inference path MUST import from this
module to guarantee that feature vectors are identical in count, order,
dtype, and scaling.

Version: 1.0.0
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# Schema version — bump when any feature is added / removed / reordered
# ---------------------------------------------------------------------------
SCHEMA_VERSION = "1.0.0"


# ═══════════════════════════════════════════════════════════════════════════
# Risk Classifier Feature Schema
# ═══════════════════════════════════════════════════════════════════════════

# Canonical ordered list of custom (non-TF-IDF) feature definitions.
# Each tuple: (name, dtype, source_category, transformation)
RISK_CUSTOM_FEATURES: List[Tuple[str, str, str, str]] = [
    # ── Risk indicator features (8) ──────────────────────────────────────
    ("risk_count",               "float64", "risk_indicators", "raw count from text"),
    ("financial_risk_count",     "float64", "risk_indicators", "raw count from text"),
    ("regulatory_risk_count",    "float64", "risk_indicators", "raw count from text"),
    ("market_risk_count",        "float64", "risk_indicators", "raw count from text"),
    ("operational_risk_count",   "float64", "risk_indicators", "raw count from text"),
    ("negative_indicator_count", "float64", "risk_indicators", "raw count from text"),
    ("hedging_word_count",       "float64", "risk_indicators", "raw count from text"),
    ("risk_density",             "float64", "risk_indicators", "high_risk / word_count"),

    # ── Readability features (4) ─────────────────────────────────────────
    ("word_count",               "float64", "readability",     "len(words)"),
    ("sentence_count",           "float64", "readability",     "len(sentences)"),
    ("avg_word_length",          "float64", "readability",     "mean char length per word"),
    ("avg_sentence_length",      "float64", "readability",     "words / sentences"),

    # ── Section features (8 = 4 sections × 2) ───────────────────────────
    ("risk_factors_word_count",           "float64", "sections", "len(section.split())"),
    ("risk_factors_present",              "float64", "sections", "1 if word_count > 0 else 0"),
    ("financial_information_word_count",  "float64", "sections", "len(section.split())"),
    ("financial_information_present",     "float64", "sections", "1 if word_count > 0 else 0"),
    ("management_word_count",             "float64", "sections", "len(section.split())"),
    ("management_present",                "float64", "sections", "1 if word_count > 0 else 0"),
    ("business_strategy_word_count",      "float64", "sections", "len(section.split())"),
    ("business_strategy_present",         "float64", "sections", "1 if word_count > 0 else 0"),

    # ── Financial metric features (4) ────────────────────────────────────
    ("issue_size",               "float64", "ipo_data",        "issue_size_rs_cr, default 0"),
    ("total_subscription",       "float64", "ipo_data",        "total_subscription, default 0"),
    ("gmp_percentage",           "float64", "ipo_data",        "gmp_percentage, default 0"),
    ("pe_ratio",                 "float64", "ipo_data",        "pe_ratio, default 0"),
]

# Section names used for section features (canonical order)
RISK_SECTION_NAMES: List[str] = [
    "risk_factors",
    "financial_information",
    "management",
    "business_strategy",
]

RISK_CUSTOM_FEATURE_COUNT = len(RISK_CUSTOM_FEATURES)  # 24


@dataclass
class RiskFeatureSchema:
    """
    Defines the complete feature vector for the IPO Risk Classifier.

    Feature vector layout:
        [tfidf_0, tfidf_1, ..., tfidf_{n-1}, custom_0, ..., custom_23]

    Total width = max_tfidf_features + 24 custom features.
    """

    max_tfidf_features: int = 1000

    # ── Derived properties ─────────────────────────────────────────────

    @property
    def custom_feature_count(self) -> int:
        return RISK_CUSTOM_FEATURE_COUNT

    @property
    def expected_width(self) -> int:
        """Total feature vector length the model expects."""
        return self.max_tfidf_features + RISK_CUSTOM_FEATURE_COUNT

    def custom_feature_names(self) -> List[str]:
        """Ordered list of custom (non-TF-IDF) feature names."""
        return [f[0] for f in RISK_CUSTOM_FEATURES]

    def get_feature_names(self, tfidf_names: Optional[List[str]] = None) -> List[str]:
        """
        Full ordered feature name list.

        Args:
            tfidf_names: Actual TF-IDF feature names from the fitted
                         vectorizer.  If *None*, generic placeholders
                         ``tfidf_0 … tfidf_{n-1}`` are used.
        """
        if tfidf_names is None:
            tfidf_names = [f"tfidf_{i}" for i in range(self.max_tfidf_features)]
        return tfidf_names + self.custom_feature_names()

    # ── Feature vector construction ────────────────────────────────────

    def build_custom_vector(
        self,
        risk_indicators: Dict[str, Any],
        text: str,
        sections: Dict[str, str],
        ipo_data: Dict[str, Any],
    ) -> np.ndarray:
        """
        Build the 24-element custom feature vector in canonical order.

        This is the **single** function both training and inference must
        call so the feature order can never drift.
        """
        values: List[float] = []

        # ── Risk indicator features (8) ──────────────────────────────
        values.append(float(risk_indicators.get("high_risk", 0)))
        values.append(float(risk_indicators.get("financial_risk", 0)))
        values.append(float(risk_indicators.get("regulatory_risk", 0)))
        values.append(float(risk_indicators.get("market_risk", 0)))
        values.append(float(risk_indicators.get("operational_risk", 0)))
        values.append(float(risk_indicators.get("negative_indicators", 0)))
        values.append(float(risk_indicators.get("hedging_words", 0)))
        values.append(float(risk_indicators.get("risk_density", 0)))

        # ── Readability features (4) ─────────────────────────────────
        words = text.split()
        sentences = [s.strip() for s in text.split(".") if s.strip()]
        word_count = len(words)
        sentence_count = len(sentences)

        values.append(float(word_count))
        values.append(float(sentence_count))
        values.append(
            float(np.mean([len(w) for w in words])) if words else 0.0
        )
        values.append(
            float(word_count / sentence_count) if sentence_count > 0 else 0.0
        )

        # ── Section features (8) ─────────────────────────────────────
        for section_name in RISK_SECTION_NAMES:
            section_text = sections.get(section_name, "")
            wc = len(section_text.split())
            values.append(float(wc))
            values.append(1.0 if wc > 0 else 0.0)

        # ── Financial metrics (4) ────────────────────────────────────
        values.append(float(ipo_data.get("issue_size_rs_cr", 0) or 0))
        values.append(float(ipo_data.get("total_subscription", 0) or 0))
        values.append(float(ipo_data.get("gmp_percentage", 0) or 0))
        values.append(float(ipo_data.get("pe_ratio", 0) or 0))

        assert len(values) == RISK_CUSTOM_FEATURE_COUNT, (
            f"Custom feature count mismatch: got {len(values)}, "
            f"expected {RISK_CUSTOM_FEATURE_COUNT}"
        )
        return np.array(values, dtype=np.float64)

    def build_feature_vector(
        self,
        tfidf_features: np.ndarray,
        risk_indicators: Dict[str, Any],
        text: str,
        sections: Dict[str, str],
        ipo_data: Dict[str, Any],
    ) -> np.ndarray:
        """
        Build the complete feature vector (TF-IDF + custom) in canonical
        order.  Returns shape ``(1, expected_width)``.
        """
        custom = self.build_custom_vector(
            risk_indicators, text, sections, ipo_data,
        )

        if tfidf_features.ndim == 1:
            tfidf_features = tfidf_features.reshape(1, -1)
        custom = custom.reshape(1, -1)

        combined = np.hstack([tfidf_features, custom])
        assert combined.shape[1] == self.expected_width, (
            f"Feature vector width mismatch: got {combined.shape[1]}, "
            f"expected {self.expected_width}"
        )
        return combined


# ═══════════════════════════════════════════════════════════════════════════
# Volatility LSTM Feature Schema
# ═══════════════════════════════════════════════════════════════════════════

# Canonical ordered list of volatility LSTM feature definitions.
VOLATILITY_FEATURES: List[Tuple[str, str, str, str]] = [
    ("log_return",      "float64", "price_data",  "log(close / close.shift(1))"),
    ("rolling_vol_7d",  "float64", "price_data",  "log_return.rolling(7).std() * sqrt(252)"),
    ("volume_change",   "float64", "price_data",  "log((volume+1) / (volume.shift(1)+1))"),
    ("high_low_range",  "float64", "price_data",  "(high - low) / close"),
    ("rsi_14",          "float64", "price_data",  "RSI(close, 14) / 100"),
    ("sma_ratio_20",    "float64", "price_data",  "(close / SMA(20)) - 1"),
    ("sentiment_proxy", "float64", "sentiment",   "sign(log_return) * |log_return|; last 7d overwritten with sentiment/10"),
    ("momentum_5d",     "float64", "price_data",  "(close / close.shift(5)) - 1"),
]

VOLATILITY_FEATURE_COUNT = len(VOLATILITY_FEATURES)  # 8


@dataclass
class VolatilityFeatureSchema:
    """
    Defines the feature vector for the BiLSTM Volatility Predictor.

    Each time-step has 8 features in the canonical order defined by
    ``VOLATILITY_FEATURES``.
    """

    @property
    def expected_width(self) -> int:
        return VOLATILITY_FEATURE_COUNT

    def feature_names(self) -> List[str]:
        """Ordered list of feature names."""
        return [f[0] for f in VOLATILITY_FEATURES]

    def validate_dataframe_columns(self, columns: List[str]) -> None:
        """
        Assert that the given column list matches the canonical order.
        Raises ``ValueError`` on mismatch.
        """
        expected = self.feature_names()
        if list(columns) != expected:
            raise ValueError(
                f"Volatility feature column mismatch!\n"
                f"  Expected: {expected}\n"
                f"  Got:      {list(columns)}"
            )

    def validate_input_size(self, input_size: int) -> None:
        """
        Assert that a model's input_size matches the schema.
        """
        if input_size != self.expected_width:
            raise ValueError(
                f"Model input_size ({input_size}) does not match "
                f"volatility schema ({self.expected_width} features)."
            )


# ═══════════════════════════════════════════════════════════════════════════
# JSON export helper
# ═══════════════════════════════════════════════════════════════════════════

def export_feature_spec() -> Dict[str, Any]:
    """
    Build a JSON-serialisable dict describing both feature schemas.
    Suitable for writing to ``feature_spec.json``.
    """
    risk_schema = RiskFeatureSchema()
    vol_schema = VolatilityFeatureSchema()

    def _feature_list(features: List[Tuple[str, str, str, str]]) -> List[Dict]:
        return [
            {
                "name": name,
                "dtype": dtype,
                "source": source,
                "transformation": transformation,
            }
            for name, dtype, source, transformation in features
        ]

    return {
        "schema_version": SCHEMA_VERSION,
        "risk_classifier": {
            "max_tfidf_features": risk_schema.max_tfidf_features,
            "custom_feature_count": risk_schema.custom_feature_count,
            "total_width": risk_schema.expected_width,
            "scaling": "StandardScaler (fit during training, applied at inference)",
            "custom_features": _feature_list(RISK_CUSTOM_FEATURES),
        },
        "volatility_lstm": {
            "feature_count": vol_schema.expected_width,
            "sequence_length": 30,
            "scaling": "MinMaxScaler (fit during training, applied at inference)",
            "features": _feature_list(VOLATILITY_FEATURES),
        },
    }


def write_feature_spec_json(
    path: Optional[str] = None,
) -> str:
    """Write ``feature_spec.json`` to disk and return the path used."""
    if path is None:
        path = os.path.join(os.path.dirname(__file__), "feature_spec.json")
    spec = export_feature_spec()
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(spec, fp, indent=2, ensure_ascii=False)
    return path
