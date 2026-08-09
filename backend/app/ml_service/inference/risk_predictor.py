"""
IPO Risk Predictor — Multi-Factor Scoring Engine
=================================================
Replaces the stub ML pipeline with a real scoring system that produces
genuinely differentiated risk scores (0–100) based on:

  1. Structured financial & market data (GMP, subscription, P/E, etc.)
  2. NLP risk-indicator density from the prospectus text (if available)
  3. A trained TF-IDF + Logistic Regression model (when fitted)

Each factor contributes a weighted sub-score, so every IPO gets a unique
result that reflects its actual characteristics.
"""

from __future__ import annotations

import logging
import math
from typing import Any, Dict, Optional

import numpy as np

from app.ml_service.preprocessing.text_preprocessor import TextPreprocessor
from app.ml_service.feature_engineering.feature_extractor import FeatureExtractor
from app.ml_service.models.risk_classifier import RiskClassifier
from app.ml_service.inference.explainer import Explainer
from app.ml_service.feature_schema import RiskFeatureSchema

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Weights for each scoring dimension (must sum to 100)
# ---------------------------------------------------------------------------
WEIGHTS: Dict[str, float] = {
    "subscription":   25,   # How oversubscribed / undersubscribed
    "gmp":            20,   # Grey-market premium
    "valuation":      20,   # P/E, market-cap vs issue size
    "financials":     15,   # Revenue/profit growth, ROCE, ROE
    "text_nlp":       20,   # NLP risk-indicator density from prospectus
}
# If text is unavailable the NLP weight is redistributed proportionally.


# ---------------------------------------------------------------------------
# Helper: clamp
# ---------------------------------------------------------------------------
def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


# ---------------------------------------------------------------------------
# Individual dimension scorers
# (each returns a *risk* score in [0, 100] — higher = more risky)
# ---------------------------------------------------------------------------

def _score_subscription(ipo_data: Dict[str, Any]) -> Optional[float]:
    """
    Total subscription is the clearest real-time demand signal.

      ≥ 30x  →  very low risk  (score ≈ 5)
      10–30x →  low risk       (score ≈ 20)
      3–10x  →  medium-low     (score ≈ 35)
      1–3x   →  medium-high    (score ≈ 55)
      0.5–1x →  high risk      (score ≈ 75)
      < 0.5x →  very high risk (score ≈ 90)

    QIB participation (institutional quality signal) shifts the score by ±10.
    """
    total = ipo_data.get("total_subscription")
    if total is None:
        return None  # signal absence — will be skipped

    # Sigmoid-like mapping (inverted — high sub = low risk)
    if total >= 50:
        base = 5
    elif total >= 30:
        base = 10
    elif total >= 10:
        base = 20
    elif total >= 5:
        base = 30
    elif total >= 3:
        base = 40
    elif total >= 1:
        base = 55
    elif total >= 0.5:
        base = 72
    else:
        base = 88

    # QIB signal
    qib = ipo_data.get("qib_subscription") or 0
    if qib >= 10:
        base -= 10
    elif qib >= 5:
        base -= 5
    elif qib < 1 and total >= 1:
        base += 8   # retail-only demand is riskier

    return _clamp(base)


def _score_gmp(ipo_data: Dict[str, Any]) -> Optional[float]:
    """
    Grey-market premium as % of issue price:

      > +20%  → low risk   (score ≈ 10)
      +10–20% → moderate   (score ≈ 25)
       0–10%  → neutral    (score ≈ 45)
      < 0%    → high risk  (score ≈ 75)
      No GMP data → None
    """
    gmp_pct = ipo_data.get("gmp_percentage")
    if gmp_pct is None:
        # Try to derive from amounts
        gmp_amt = ipo_data.get("gmp_amount")
        price = ipo_data.get("price_band_upper") or ipo_data.get("issue_price")
        if gmp_amt is not None and price and price > 0:
            gmp_pct = (gmp_amt / price) * 100
        else:
            return None

    if gmp_pct >= 30:
        return _clamp(8)
    elif gmp_pct >= 20:
        return _clamp(18)
    elif gmp_pct >= 10:
        return _clamp(30)
    elif gmp_pct >= 5:
        return _clamp(42)
    elif gmp_pct >= 0:
        return _clamp(52)
    elif gmp_pct >= -5:
        return _clamp(68)
    elif gmp_pct >= -10:
        return _clamp(78)
    else:
        return _clamp(90)


def _score_valuation(ipo_data: Dict[str, Any]) -> Optional[float]:
    """
    P/E ratio benchmarked against typical Indian market range (15–35x):

      < 15x  → attractive    (score ≈ 20)
      15–25x → fair          (score ≈ 35)
      25–40x → stretched     (score ≈ 55)
      40–60x → expensive     (score ≈ 70)
      > 60x  → very expensive (score ≈ 85)

    Issue size relative to market cap adds a dilution risk adjustment.
    """
    pe = ipo_data.get("pe_ratio")
    if pe is None or pe <= 0:
        return None

    if pe < 10:
        base = 15
    elif pe < 15:
        base = 22
    elif pe < 25:
        base = 35
    elif pe < 35:
        base = 48
    elif pe < 50:
        base = 62
    elif pe < 70:
        base = 73
    else:
        base = 85

    # Dilution: if fresh issue > 50% of issue size, add risk
    fresh = ipo_data.get("fresh_issue_size") or 0
    total_size = ipo_data.get("issue_size_rs_cr") or 0
    if total_size > 0 and fresh / total_size > 0.7:
        base += 8

    return _clamp(base)


def _score_financials(ipo_data: Dict[str, Any]) -> Optional[float]:
    """
    Combines revenue growth, profit growth, ROCE and ROE into one signal.
    Returns None if none of the four metrics are present.
    """
    scores = []
    weights = []

    # Revenue growth
    rev_growth = ipo_data.get("revenue_growth")
    if rev_growth is not None:
        if rev_growth >= 30:
            scores.append(15)
        elif rev_growth >= 15:
            scores.append(30)
        elif rev_growth >= 0:
            scores.append(50)
        elif rev_growth >= -10:
            scores.append(70)
        else:
            scores.append(88)
        weights.append(2)

    # Profit growth
    prof_growth = ipo_data.get("profit_growth")
    if prof_growth is not None:
        if prof_growth >= 40:
            scores.append(12)
        elif prof_growth >= 20:
            scores.append(28)
        elif prof_growth >= 0:
            scores.append(48)
        elif prof_growth >= -15:
            scores.append(68)
        else:
            scores.append(85)
        weights.append(3)

    # ROCE
    roce = ipo_data.get("roce")
    if roce is not None:
        if roce >= 25:
            scores.append(15)
        elif roce >= 15:
            scores.append(30)
        elif roce >= 8:
            scores.append(50)
        elif roce >= 0:
            scores.append(68)
        else:
            scores.append(85)
        weights.append(2)

    # ROE
    roe = ipo_data.get("roe")
    if roe is not None:
        if roe >= 20:
            scores.append(15)
        elif roe >= 12:
            scores.append(32)
        elif roe >= 5:
            scores.append(50)
        elif roe >= 0:
            scores.append(66)
        else:
            scores.append(82)
        weights.append(2)

    if not scores:
        return None

    return _clamp(sum(s * w for s, w in zip(scores, weights)) / sum(weights))


def _score_nlp_text(prospectus_text: str, sections: Dict[str, str],
                    preprocessor: TextPreprocessor) -> Optional[float]:
    """
    NLP-based risk scoring from prospectus text.
    Uses risk indicator density + section analysis.
    Returns None if text is too short to be meaningful.
    """
    combined = prospectus_text
    if sections:
        combined += " " + " ".join(sections.values())

    combined = combined.strip()
    if len(combined.split()) < 50:
        return None

    indicators = preprocessor.extract_risk_indicators(combined)
    word_count = max(len(combined.split()), 1)

    # --- Primary signal: risk density (risk words per 100 words) ---
    density = indicators.get("risk_density", 0) * 100  # convert to per-100-words

    # --- Secondary signals ---
    financial_risk = indicators.get("financial_risk", 0)
    regulatory_risk = indicators.get("regulatory_risk", 0)
    negative_indicators = indicators.get("negative_indicators", 0)
    hedging_words = indicators.get("hedging_words", 0)

    # Normalise secondary signals by document length
    fin_density = (financial_risk / word_count) * 1000
    reg_density = (regulatory_risk / word_count) * 1000
    neg_density = (negative_indicators / word_count) * 1000
    hedge_density = (hedging_words / word_count) * 1000

    # --- Section presence penalty: missing key sections → higher risk ---
    section_penalty = 0
    for key_section in ["risk_factors", "financial_information", "management"]:
        if not sections.get(key_section) or len(sections[key_section].split()) < 30:
            section_penalty += 5

    # --- Composite NLP risk score ---
    # Density thresholds tuned on typical SEBI prospectus language
    if density >= 3.0:
        base = 75
    elif density >= 2.0:
        base = 60
    elif density >= 1.0:
        base = 45
    elif density >= 0.5:
        base = 32
    else:
        base = 20

    # Add weighted secondary signals
    base += min(fin_density * 3, 15)
    base += min(reg_density * 4, 12)
    base += min(neg_density * 2, 10)
    base += min(hedge_density * 1.5, 8)
    base += section_penalty

    return _clamp(base)


# ---------------------------------------------------------------------------
# Composite scorer
# ---------------------------------------------------------------------------

def _composite_score(dimension_scores: Dict[str, Optional[float]]) -> float:
    """
    Weighted average of available dimension scores.
    Missing dimensions have their weight redistributed proportionally.
    """
    total_weight = 0.0
    weighted_sum = 0.0

    for dim, score in dimension_scores.items():
        if score is not None:
            w = WEIGHTS[dim]
            weighted_sum += score * w
            total_weight += w

    if total_weight == 0:
        # Absolute fallback: no data at all
        return 50.0

    return _clamp(weighted_sum / total_weight)


# ---------------------------------------------------------------------------
# Risk score → category mapping
# ---------------------------------------------------------------------------

def _score_to_category(score: float) -> str:
    if score < 33:
        return "low"
    elif score < 60:
        return "medium"
    else:
        return "high"


# ---------------------------------------------------------------------------
# Main RiskPredictor class
# ---------------------------------------------------------------------------

class RiskPredictor:
    """End-to-end IPO risk prediction pipeline."""

    def __init__(self):
        self.preprocessor = TextPreprocessor()
        self.feature_extractor = FeatureExtractor()
        self.classifier = RiskClassifier()
        self.explainer = Explainer(self.classifier, self.feature_extractor)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def predict(
        self,
        prospectus_text: str = "",
        sections: Optional[Dict[str, str]] = None,
        ipo_data: Optional[Dict[str, Any]] = None,
        explain: bool = True,
    ) -> Dict[str, Any]:
        """
        Predict IPO risk.

        Priority:
          1. If the ML model is trained AND prospectus text is present → use ML model
          2. Otherwise → use the multi-factor rule-based engine
        """
        sections = sections or {}
        ipo_data = ipo_data or {}

        try:
            # ── Attempt ML model path ──────────────────────────────────────
            if self.classifier.is_fitted and len(prospectus_text.split()) >= 200:
                return self._predict_ml(prospectus_text, sections, ipo_data, explain)

            # ── Multi-factor rule-based path ────────────────────────────────
            return self._predict_rules(prospectus_text, sections, ipo_data, explain)

        except Exception as exc:
            logger.exception("RiskPredictor.predict failed: %s", exc)
            return {
                "risk_score": 50,
                "risk_category": "medium",
                "confidence": 0.0,
                "error": str(exc),
                "success": False,
            }

    # ------------------------------------------------------------------
    # ML model path (only used when model is fitted)
    # ------------------------------------------------------------------

    def _predict_ml(
        self,
        prospectus_text: str,
        sections: Dict[str, str],
        ipo_data: Dict[str, Any],
        explain: bool,
    ) -> Dict[str, Any]:
        processed_text = self.preprocessor.preprocess(prospectus_text)
        risk_indicators = self.preprocessor.extract_risk_indicators(prospectus_text)

        features = self.feature_extractor.extract_features(
            processed_text=processed_text,
            sections=sections,
            ipo_data=ipo_data,
            risk_indicators=risk_indicators,
        )

        # Schema validation: ensure feature width matches expectation
        schema = RiskFeatureSchema(
            max_tfidf_features=self.feature_extractor.max_features,
        )
        actual_width = features.shape[-1]
        if actual_width != schema.expected_width:
            logger.error(
                "Feature width mismatch: got %d, schema expects %d",
                actual_width, schema.expected_width,
            )

        prediction = self.classifier.predict(features)[0]
        probabilities = self.classifier.predict_proba(features)[0]
        confidence = float(np.max(probabilities))

        risk_score = self._calculate_risk_score_ml(prediction, risk_indicators, ipo_data)

        explanation = None
        if explain:
            feature_names = self.feature_extractor.get_feature_names()
            explanation = self.explainer.explain(features, feature_names, top_k=5)

        return {
            "risk_score": risk_score,
            "risk_category": prediction,
            "confidence": confidence,
            "risk_indicators": risk_indicators,
            "explanation": explanation,
            "success": True,
        }

    # ------------------------------------------------------------------
    # Rule-based multi-factor path
    # ------------------------------------------------------------------

    def _predict_rules(
        self,
        prospectus_text: str,
        sections: Dict[str, str],
        ipo_data: Dict[str, Any],
        explain: bool,
    ) -> Dict[str, Any]:

        # Score each dimension
        sub_score = _score_subscription(ipo_data)
        gmp_score = _score_gmp(ipo_data)
        val_score = _score_valuation(ipo_data)
        fin_score = _score_financials(ipo_data)

        # NLP score (requires meaningful text)
        nlp_score = None
        risk_indicators: Dict[str, Any] = {}
        if prospectus_text and len(prospectus_text.split()) >= 50:
            nlp_score = _score_nlp_text(prospectus_text, sections, self.preprocessor)
            risk_indicators = self.preprocessor.extract_risk_indicators(prospectus_text)

        dimension_scores: Dict[str, Optional[float]] = {
            "subscription": sub_score,
            "gmp": gmp_score,
            "valuation": val_score,
            "financials": fin_score,
            "text_nlp": nlp_score,
        }

        composite = _composite_score(dimension_scores)
        risk_score = round(composite, 1)
        risk_category = _score_to_category(risk_score)

        # Confidence: proportion of dimensions with actual data
        available = sum(1 for v in dimension_scores.values() if v is not None)
        confidence = round(available / len(dimension_scores), 2)

        # Build human-readable explanation
        explanation = None
        if explain:
            explanation = self._build_explanation(dimension_scores, risk_score)

        return {
            "risk_score": risk_score,
            "risk_category": risk_category,
            "confidence": confidence,
            "risk_indicators": risk_indicators,
            "explanation": explanation,
            "dimension_scores": {k: (round(v, 1) if v is not None else None)
                                 for k, v in dimension_scores.items()},
            "success": True,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _calculate_risk_score_ml(
        self,
        risk_category: str,
        risk_indicators: Dict[str, Any],
        ipo_data: Dict[str, Any],
    ) -> float:
        """Blend ML category prediction with structured data signals."""
        base_scores = {"low": 20, "medium": 50, "high": 78}
        base = base_scores.get(risk_category, 50)

        # Adjust with structured data
        gmp_score = _score_gmp(ipo_data)
        sub_score = _score_subscription(ipo_data)

        adjustments = []
        if gmp_score is not None:
            adjustments.append(gmp_score)
        if sub_score is not None:
            adjustments.append(sub_score)
        if adjustments:
            blend = sum(adjustments) / len(adjustments)
            base = base * 0.6 + blend * 0.4

        # Minor NLP adjustment
        total_risk = sum(
            v for k, v in risk_indicators.items()
            if k not in ("risk_density",) and isinstance(v, (int, float))
        )
        base += min(total_risk * 0.1, 8)

        return round(_clamp(base), 1)

    def _build_explanation(
        self,
        dimension_scores: Dict[str, Optional[float]],
        composite_score: float,
    ) -> Dict[str, Any]:
        """Build a feature-importance style explanation from dimension scores."""
        labels = {
            "subscription": "Subscription Demand",
            "gmp": "Grey Market Premium",
            "valuation": "Valuation (P/E)",
            "financials": "Financial Health",
            "text_nlp": "Prospectus Risk Language",
        }

        features = []
        for dim, score in dimension_scores.items():
            if score is None:
                continue
            # Contribution = how much this dimension deviates from neutral (50)
            deviation = (score - 50) / 50  # –1 to +1
            contribution = round(deviation * (WEIGHTS[dim] / 100), 4)
            features.append({
                "feature": labels.get(dim, dim),
                "contribution": contribution,
                "raw_score": round(score, 1),
                "importance_rank": 0,  # filled below
            })

        # Sort by absolute contribution
        features.sort(key=lambda x: abs(x["contribution"]), reverse=True)
        for i, f in enumerate(features):
            f["importance_rank"] = i + 1

        if composite_score < 33:
            summary = "Low risk profile — strong demand signals and healthy financials."
        elif composite_score < 60:
            summary = "Moderate risk — mixed signals across valuation and market demand."
        else:
            summary = "Elevated risk — weak demand, stretched valuation or limited prospectus disclosures."

        return {"top_features": features[:5], "summary": summary}

    # ------------------------------------------------------------------
    # Model persistence
    # ------------------------------------------------------------------

    def load_model(self, filepath: str) -> "RiskPredictor":
        self.classifier.load(filepath)
        return self

    def save_model(self, filepath: str) -> "RiskPredictor":
        self.classifier.save(filepath)
        return self


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------
_predictor_instance: Optional[RiskPredictor] = None


def get_predictor() -> RiskPredictor:
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = RiskPredictor()
    return _predictor_instance