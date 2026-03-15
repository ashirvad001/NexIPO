"""
Phase 1 – End-to-End Test Script
==================================
Run from the ``backend/`` directory:

    python scripts/test_phase1.py

Prerequisites
-------------
1. ``pip install transformers torch yfinance newsapi-python python-dotenv``
2. A valid ``NEWS_API_KEY`` in ``.env``
3. Internet access (model downloads + API calls on first run)
"""

import os
import sys

# Ensure the backend package root is on sys.path so that
# ``from app.ml_service.volatility …`` resolves correctly.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv

load_dotenv()

from app.ml_service.volatility.data_collector import (
    NewsDataCollector,
    StockDataCollector,
)
from app.ml_service.volatility.bert_embeddings import BERTSentimentExtractor


# ------------------------------------------------------------------
# Test helpers
# ------------------------------------------------------------------
def test_news_collection() -> list:
    """Test NewsDataCollector."""
    print("\n📰 Testing News Collection...")

    api_key = os.getenv("NEWS_API_KEY", "")
    collector = NewsDataCollector(newsapi_key=api_key)

    # Company news
    news = collector.get_recent_news("Tesla", days_back=7)
    print(f"  ✓ Collected {len(news)} articles about Tesla")
    if news:
        print(f"    Sample: {news[0][:100]}…")

    # Geopolitical news
    geo_news = collector.get_geopolitical_news(days_back=7)
    print(f"  ✓ Collected {len(geo_news)} geopolitical articles")
    if geo_news:
        print(f"    Sample category: {geo_news[0]['category']}")

    return news


def test_bert_sentiment(news_articles: list) -> None:
    """Test BERTSentimentExtractor."""
    print("\n🤖 Testing BERT Sentiment...")

    bert = BERTSentimentExtractor()

    if not news_articles:
        # Use a fallback sentence so the rest of the test still runs.
        news_articles = [
            "Tesla reports record quarterly earnings beating all analyst expectations.",
            "Global markets tumble as trade war tensions escalate between nations.",
            "Federal Reserve announces unchanged interest rates for next quarter.",
        ]
        print("  ⚠ No live articles – using built-in sample sentences.")

    # Single-article sentiment
    sentiment = bert.extract_sentiment(news_articles[0])
    print(
        f"  ✓ Sentiment: {sentiment['label']} "
        f"(score: {sentiment['score']:.2f}, polarity: {sentiment['polarity']})"
    )

    # Embeddings shape
    embeddings = bert.extract_embeddings(news_articles[0])
    print(f"  ✓ Embeddings shape: {embeddings.shape}")

    # Batch processing
    batch = news_articles[: min(5, len(news_articles))]
    batch_results = bert.process_news_batch(batch)
    print(f"  ✓ Batch avg sentiment: {batch_results['avg_sentiment']:.4f}")
    print(f"  ✓ Sentiment volatility: {batch_results['sentiment_volatility']:.4f}")
    print(f"  ✓ Embeddings matrix shape: {batch_results['embeddings'].shape}")

    # Geopolitical feature detection
    geo_features = bert.extract_geopolitical_features(news_articles[0])
    print(f"  ✓ Geopolitical score: {geo_features['total_geopolitical_score']}")
    for k, v in geo_features.items():
        if k != "total_geopolitical_score":
            print(f"      {k}: {v}")


def test_stock_data() -> None:
    """Test StockDataCollector."""
    print("\n📊 Testing Stock Data Collection...")

    collector = StockDataCollector()

    # Download data
    data = collector.get_stock_data("AAPL", period="1mo")
    print(f"  ✓ Downloaded {len(data)} days of AAPL data")
    print(f"    Columns: {list(data.columns)}")
    print(f"    Latest close: ${data['Close'].iloc[-1]:.2f}")

    # Realised volatility
    volatility = collector.calculate_realized_volatility(data)
    print(f"  ✓ Realised volatility: {volatility:.4f} ({volatility * 100:.2f}%)")


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 55)
    print("  PHASE 1 TESTING – Volatility Forecaster Pipeline")
    print("=" * 55)

    try:
        news = test_news_collection()
    except Exception as exc:
        print(f"  ✗ News collection failed: {exc}")
        news = []

    try:
        test_bert_sentiment(news)
    except Exception as exc:
        print(f"  ✗ BERT sentiment test failed: {exc}")

    try:
        test_stock_data()
    except Exception as exc:
        print(f"  ✗ Stock data test failed: {exc}")

    print("\n" + "=" * 55)
    print("  ✅  PHASE 1 TESTS COMPLETE")
    print("=" * 55)
