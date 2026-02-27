"""
IPO Analysis Service
Generates data-driven Pros, Cons, Risk assessment, and Verdict for IPOs
based on available metrics (GMP, pricing, subscription, financials, etc.).
"""

from typing import Optional
from sqlalchemy.orm import Session
from app.models.ipo import IPO, IPOStatus, IPOType


def analyze_ipo(db: Session, ipo_id: int) -> Optional[dict]:
    """Generate a comprehensive analysis for an IPO."""
    ipo = db.query(IPO).filter(IPO.id == ipo_id).first()
    if not ipo:
        return None

    pros = []
    cons = []
    risks = []
    key_metrics = []
    verdict_score = 50  # Start neutral (0-100)

    # ───────────────────────────────────────────────
    # GMP Analysis
    # ───────────────────────────────────────────────
    if ipo.gmp_amount is not None:
        if ipo.gmp_amount > 0:
            pct = ipo.gmp_percentage or 0
            if pct > 20:
                pros.append({
                    "title": "Very Strong Grey Market Premium",
                    "detail": f"GMP of ₹{ipo.gmp_amount:,.0f} ({pct:.1f}%) indicates exceptionally high demand in the grey market.",
                    "impact": "high"
                })
                verdict_score += 15
            elif pct > 5:
                pros.append({
                    "title": "Positive Grey Market Premium",
                    "detail": f"GMP of ₹{ipo.gmp_amount:,.0f} ({pct:.1f}%) suggests healthy demand and likely listing gains.",
                    "impact": "medium"
                })
                verdict_score += 8
            else:
                pros.append({
                    "title": "Modest Grey Market Premium",
                    "detail": f"GMP of ₹{ipo.gmp_amount:,.0f} ({pct:.1f}%) — moderate interest in the grey market.",
                    "impact": "low"
                })
                verdict_score += 3
        elif ipo.gmp_amount < 0:
            cons.append({
                "title": "Negative Grey Market Premium",
                "detail": f"GMP of ₹{ipo.gmp_amount:,.0f} indicates weak demand. Listing at a discount is likely.",
                "impact": "high"
            })
            verdict_score -= 15
        else:
            cons.append({
                "title": "Zero Grey Market Premium",
                "detail": "No premium in the grey market suggests lukewarm demand.",
                "impact": "medium"
            })
            verdict_score -= 5

        key_metrics.append({
            "label": "GMP",
            "value": f"₹{ipo.gmp_amount:,.0f}",
            "status": "positive" if ipo.gmp_amount > 0 else "negative" if ipo.gmp_amount < 0 else "neutral"
        })

    # ───────────────────────────────────────────────
    # Issue Size Analysis
    # ───────────────────────────────────────────────
    if ipo.issue_size_rs_cr:
        key_metrics.append({
            "label": "Issue Size",
            "value": f"₹{ipo.issue_size_rs_cr:,.1f} Cr",
            "status": "neutral"
        })

        if ipo.ipo_type == IPOType.MAINBOARD:
            if ipo.issue_size_rs_cr > 5000:
                pros.append({
                    "title": "Large Issue Size",
                    "detail": f"At ₹{ipo.issue_size_rs_cr:,.0f} Cr, this is a large offering — typically from established companies with stronger financials.",
                    "impact": "medium"
                })
                verdict_score += 3
            elif ipo.issue_size_rs_cr < 200:
                risks.append({
                    "title": "Small Issue for Mainboard",
                    "detail": f"Issue size of ₹{ipo.issue_size_rs_cr:,.0f} Cr is relatively small for a mainboard IPO, which may indicate limited institutional interest.",
                    "impact": "low"
                })
        elif ipo.ipo_type == IPOType.SME:
            if ipo.issue_size_rs_cr > 100:
                pros.append({
                    "title": "Substantial SME Issue",
                    "detail": f"For an SME IPO, ₹{ipo.issue_size_rs_cr:,.0f} Cr is a sizable offering, suggesting strong growth ambitions.",
                    "impact": "low"
                })

    # ───────────────────────────────────────────────
    # Pricing Analysis
    # ───────────────────────────────────────────────
    if ipo.price_band_upper and ipo.price_band_lower:
        band_width = ((ipo.price_band_upper - ipo.price_band_lower) / ipo.price_band_lower) * 100
        key_metrics.append({
            "label": "Price Band",
            "value": f"₹{ipo.price_band_lower:,.0f} – ₹{ipo.price_band_upper:,.0f}",
            "status": "neutral"
        })

    if ipo.min_investment:
        if ipo.min_investment > 200000:
            cons.append({
                "title": "High Minimum Investment",
                "detail": f"Minimum investment of ₹{ipo.min_investment:,.0f} is steep, limiting retail participation.",
                "impact": "low"
            })
        elif ipo.min_investment <= 15000:
            pros.append({
                "title": "Accessible Entry Point",
                "detail": f"Minimum investment of ₹{ipo.min_investment:,.0f} keeps this IPO accessible to retail investors.",
                "impact": "low"
            })

    # ───────────────────────────────────────────────
    # Subscription Analysis
    # ───────────────────────────────────────────────
    if ipo.total_subscription:
        key_metrics.append({
            "label": "Total Subscription",
            "value": f"{ipo.total_subscription:.2f}x",
            "status": "positive" if ipo.total_subscription > 1 else "negative"
        })

        if ipo.total_subscription > 10:
            pros.append({
                "title": "Heavily Oversubscribed",
                "detail": f"Total subscription of {ipo.total_subscription:.2f}x signals extremely strong investor confidence.",
                "impact": "high"
            })
            verdict_score += 12
        elif ipo.total_subscription > 3:
            pros.append({
                "title": "Well Oversubscribed",
                "detail": f"Subscription of {ipo.total_subscription:.2f}x indicates solid demand across investor categories.",
                "impact": "medium"
            })
            verdict_score += 6
        elif ipo.total_subscription < 1:
            cons.append({
                "title": "Undersubscribed",
                "detail": f"Total subscription of only {ipo.total_subscription:.2f}x — demand is below the shares offered.",
                "impact": "high"
            })
            verdict_score -= 15

    if ipo.qib_subscription and ipo.qib_subscription > 5:
        pros.append({
            "title": "Strong Institutional Interest",
            "detail": f"QIB subscription of {ipo.qib_subscription:.2f}x shows significant confidence from institutional investors.",
            "impact": "medium"
        })
        verdict_score += 5

    if ipo.retail_subscription and ipo.retail_subscription > 5:
        pros.append({
            "title": "High Retail Demand",
            "detail": f"Retail subscription of {ipo.retail_subscription:.2f}x indicates strong interest among individual investors.",
            "impact": "medium"
        })
        verdict_score += 3

    # ───────────────────────────────────────────────
    # Financial Analysis
    # ───────────────────────────────────────────────
    if ipo.pe_ratio:
        key_metrics.append({
            "label": "P/E Ratio",
            "value": f"{ipo.pe_ratio:.1f}x",
            "status": "positive" if ipo.pe_ratio < 25 else "negative" if ipo.pe_ratio > 50 else "neutral"
        })
        if ipo.pe_ratio > 50:
            cons.append({
                "title": "High Valuation",
                "detail": f"P/E ratio of {ipo.pe_ratio:.1f}x is stretched. The company is priced at a premium to earnings.",
                "impact": "medium"
            })
            risks.append({
                "title": "Valuation Risk",
                "detail": "High P/E leaves limited margin of safety. Any earnings miss could lead to significant price correction.",
                "impact": "medium"
            })
            verdict_score -= 8
        elif ipo.pe_ratio < 20:
            pros.append({
                "title": "Reasonable Valuation",
                "detail": f"P/E ratio of {ipo.pe_ratio:.1f}x is attractive relative to market averages.",
                "impact": "medium"
            })
            verdict_score += 5

    if ipo.revenue_growth and ipo.revenue_growth > 20:
        pros.append({
            "title": "Strong Revenue Growth",
            "detail": f"Revenue growth of {ipo.revenue_growth:.1f}% demonstrates robust business expansion.",
            "impact": "medium"
        })
        verdict_score += 5

    if ipo.profit_growth is not None:
        if ipo.profit_growth > 25:
            pros.append({
                "title": "Excellent Profit Growth",
                "detail": f"Profit growth of {ipo.profit_growth:.1f}% shows improving profitability and operational efficiency.",
                "impact": "high"
            })
            verdict_score += 8
        elif ipo.profit_growth < 0:
            cons.append({
                "title": "Declining Profitability",
                "detail": f"Profit growth of {ipo.profit_growth:.1f}% indicates deteriorating bottom line.",
                "impact": "high"
            })
            verdict_score -= 10

    if ipo.roce and ipo.roce > 15:
        pros.append({
            "title": "Good Capital Efficiency",
            "detail": f"ROCE of {ipo.roce:.1f}% shows the company generates healthy returns on invested capital.",
            "impact": "medium"
        })
        verdict_score += 3

    if ipo.roe and ipo.roe > 15:
        pros.append({
            "title": "Strong Return on Equity",
            "detail": f"ROE of {ipo.roe:.1f}% indicates efficient use of shareholder capital.",
            "impact": "medium"
        })
        verdict_score += 3

    # ───────────────────────────────────────────────
    # IPO Type Risks
    # ───────────────────────────────────────────────
    if ipo.ipo_type == IPOType.SME:
        risks.append({
            "title": "SME Segment Risk",
            "detail": "SME IPOs carry higher risk due to lower regulatory scrutiny, limited track record, and lower liquidity post-listing.",
            "impact": "medium"
        })
        verdict_score -= 5
    else:
        pros.append({
            "title": "Mainboard Listing",
            "detail": "Listed on the mainboard exchange, which requires stricter compliance and offers better liquidity.",
            "impact": "low"
        })

    # ───────────────────────────────────────────────
    # Listing Performance (for listed IPOs)
    # ───────────────────────────────────────────────
    if ipo.listing_gain_percentage is not None:
        if ipo.listing_gain_percentage > 20:
            pros.append({
                "title": "Stellar Listing Performance",
                "detail": f"Listed at {ipo.listing_gain_percentage:+.1f}% gain, delivering strong returns to allottees.",
                "impact": "high"
            })
        elif ipo.listing_gain_percentage > 0:
            pros.append({
                "title": "Positive Listing",
                "detail": f"Listed at {ipo.listing_gain_percentage:+.1f}% gain over issue price.",
                "impact": "medium"
            })
        elif ipo.listing_gain_percentage < -10:
            cons.append({
                "title": "Poor Listing Performance",
                "detail": f"Listed at {ipo.listing_gain_percentage:+.1f}% — significant losses for allottees on listing day.",
                "impact": "high"
            })

    # ───────────────────────────────────────────────
    # General Risks (always present)
    # ───────────────────────────────────────────────
    risks.append({
        "title": "Market Conditions Risk",
        "detail": "Broad market sentiment and macroeconomic conditions can significantly impact IPO listing performance regardless of company fundamentals.",
        "impact": "medium"
    })

    if ipo.status == IPOStatus.UPCOMING:
        risks.append({
            "title": "Pre-IPO Uncertainty",
            "detail": "GMP and subscription data may fluctuate significantly before the IPO opens. Current estimates are not guaranteed.",
            "impact": "low"
        })

    # ───────────────────────────────────────────────
    # ML Risk Score
    # ───────────────────────────────────────────────
    if ipo.ml_processed and ipo.risk_score is not None:
        key_metrics.append({
            "label": "ML Risk Score",
            "value": f"{ipo.risk_score:.0f}/100",
            "status": "positive" if ipo.risk_score < 40 else "negative" if ipo.risk_score > 70 else "neutral"
        })
        if ipo.risk_score > 70:
            risks.append({
                "title": "High ML Risk Score",
                "detail": f"Our ML model assigns a risk score of {ipo.risk_score:.0f}/100, categorized as '{ipo.risk_category}' risk.",
                "impact": "high"
            })
            verdict_score -= 10
        elif ipo.risk_score < 30:
            pros.append({
                "title": "Low ML Risk Score",
                "detail": f"ML risk score of {ipo.risk_score:.0f}/100 ({ipo.risk_category} risk) based on comprehensive analysis.",
                "impact": "medium"
            })
            verdict_score += 5

    # ───────────────────────────────────────────────
    # Compute Verdict
    # ───────────────────────────────────────────────
    verdict_score = max(0, min(100, verdict_score))

    if verdict_score >= 75:
        verdict = "Strong Buy"
        verdict_detail = "Multiple positive indicators suggest this IPO has strong potential. GMP, financials, and demand metrics align favorably."
        verdict_color = "green"
    elif verdict_score >= 60:
        verdict = "Buy"
        verdict_detail = "Overall positive outlook with some factors to watch. Consider applying based on your risk appetite."
        verdict_color = "green"
    elif verdict_score >= 45:
        verdict = "Neutral"
        verdict_detail = "Mixed signals — some positives balanced by concerns. Suitable for moderate risk-takers."
        verdict_color = "yellow"
    elif verdict_score >= 30:
        verdict = "Avoid"
        verdict_detail = "Several negative indicators outweigh the positives. Proceed with caution or wait for better opportunities."
        verdict_color = "red"
    else:
        verdict = "Strong Avoid"
        verdict_detail = "Multiple red flags present. Risk significantly outweighs potential reward."
        verdict_color = "red"

    # Handle edge case when we have very little data
    if not pros and not cons:
        pros.append({
            "title": "Limited Data Available",
            "detail": "Insufficient data to identify specific strengths. More information needed for a thorough analysis.",
            "impact": "low"
        })
        verdict = "Insufficient Data"
        verdict_detail = "Not enough data is available to provide a meaningful assessment. Monitor for updates."
        verdict_color = "gray"
        verdict_score = 50

    return {
        "ipo_id": ipo.id,
        "company_name": ipo.company_name,
        "pros": pros,
        "cons": cons,
        "risks": risks,
        "key_metrics": key_metrics,
        "verdict": {
            "label": verdict,
            "detail": verdict_detail,
            "score": verdict_score,
            "color": verdict_color
        }
    }
