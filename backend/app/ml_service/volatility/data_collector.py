"""
Data Collection Module – Phase 1 of Stock Volatility Forecaster
================================================================
Collects news articles (via NewsAPI) and stock price data (via yfinance)
for the BERT+LSTM volatility prediction pipeline.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import yfinance as yf
from newsapi import NewsApiClient
from newsapi.newsapi_exception import NewsAPIException

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)s  %(levelname)s  %(message)s",
)


# ---------------------------------------------------------------------------
# News Data Collector
# ---------------------------------------------------------------------------
class NewsDataCollector:
    """Collect news articles from NewsAPI for sentiment analysis."""

    # Keyword groups used when scanning for geopolitical events
    GEOPOLITICAL_KEYWORDS = {
        "war": [
            "war", "conflict", "military", "attack", "invasion",
            "missile", "airstrike", "troops", "combat",
        ],
        "economic": [
            "sanctions", "tariff", "trade war", "inflation",
            "interest rate", "recession", "embargo", "currency crisis",
        ],
        "political": [
            "election", "government", "policy", "regulation",
            "legislation", "political crisis", "coup", "protest",
        ],
        "pandemic": [
            "pandemic", "covid", "lockdown", "outbreak",
            "quarantine", "vaccine", "epidemic", "virus",
        ],
    }

    def __init__(self, newsapi_key: str) -> None:
        """
        Initialise the NewsAPI client.

        Args:
            newsapi_key: API key obtained from https://newsapi.org/
        """
        if not newsapi_key or newsapi_key == "your_newsapi_key_here":
            raise ValueError(
                "A valid NewsAPI key is required.  "
                "Sign up at https://newsapi.org/ and add it to your .env file."
            )
        self.api = NewsApiClient(api_key=newsapi_key)
        logger.info("NewsDataCollector initialised successfully.")

    # ----- public helpers ---------------------------------------------------

    def get_recent_news(
        self,
        company_name: str,
        days_back: int = 30,
        page_size: int = 50,
    ) -> List[str]:
        """
        Fetch recent English-language articles about *company_name*.

        Args:
            company_name: Search query (e.g. ``"Tesla"``).
            days_back: How many days into the past to search.
            page_size: Maximum articles per request (max 100).

        Returns:
            List of article texts (``"title. description"``).
        """
        from_date = (datetime.utcnow() - timedelta(days=days_back)).strftime(
            "%Y-%m-%d"
        )
        to_date = datetime.utcnow().strftime("%Y-%m-%d")

        logger.info(
            "Fetching news for '%s' from %s to %s …",
            company_name, from_date, to_date,
        )

        try:
            response = self.api.get_everything(
                q=company_name,
                from_param=from_date,
                to=to_date,
                language="en",
                sort_by="relevancy",
                page_size=min(page_size, 100),
            )
        except NewsAPIException as exc:
            logger.error("NewsAPI error for '%s': %s", company_name, exc)
            return []

        articles: List[str] = []
        for article in response.get("articles", []):
            title = article.get("title") or ""
            description = article.get("description") or ""
            text = f"{title}. {description}".strip(". ")
            if text:
                articles.append(text)

        logger.info(
            "Collected %d articles for '%s'.", len(articles), company_name,
        )
        return articles

    def get_geopolitical_news(
        self,
        days_back: int = 7,
        page_size: int = 30,
    ) -> List[Dict]:
        """
        Fetch articles matching geopolitical-event keywords.

        Args:
            days_back: How many days into the past to search.
            page_size: Maximum articles per keyword category.

        Returns:
            List of dicts with keys ``title``, ``description``,
            ``source``, ``published_at``, ``category``.
        """
        from_date = (datetime.utcnow() - timedelta(days=days_back)).strftime(
            "%Y-%m-%d"
        )
        to_date = datetime.utcnow().strftime("%Y-%m-%d")

        collected: List[Dict] = []
        seen_titles: set = set()

        for category, keywords in self.GEOPOLITICAL_KEYWORDS.items():
            query = " OR ".join(keywords[:5])  # NewsAPI query limit
            logger.info("Searching geopolitical category '%s' …", category)

            try:
                response = self.api.get_everything(
                    q=query,
                    from_param=from_date,
                    to=to_date,
                    language="en",
                    sort_by="relevancy",
                    page_size=min(page_size, 100),
                )
            except NewsAPIException as exc:
                logger.warning(
                    "NewsAPI error for geo-category '%s': %s", category, exc,
                )
                continue

            for article in response.get("articles", []):
                title = article.get("title") or ""
                if title in seen_titles:
                    continue
                seen_titles.add(title)
                collected.append(
                    {
                        "title": title,
                        "description": article.get("description") or "",
                        "source": (article.get("source") or {}).get("name", "Unknown"),
                        "published_at": article.get("publishedAt", ""),
                        "category": category,
                    }
                )

            # Be nice to the free tier
            time.sleep(1)

        logger.info("Collected %d geopolitical articles.", len(collected))
        return collected

    def batch_collect_news(
        self,
        companies: List[str],
        days_back: int = 30,
    ) -> Dict[str, List[str]]:
        """
        Collect news for several companies in one go.

        A 1-second pause is inserted between companies to respect rate limits.

        Args:
            companies: List of company names / search queries.
            days_back: How many days back to search for each company.

        Returns:
            ``{company_name: [article_texts, …]}``.
        """
        results: Dict[str, List[str]] = {}
        for idx, company in enumerate(companies):
            results[company] = self.get_recent_news(
                company, days_back=days_back,
            )
            if idx < len(companies) - 1:
                time.sleep(1)  # rate-limit guard
        return results


# ---------------------------------------------------------------------------
# Stock Data Collector
# ---------------------------------------------------------------------------
class StockDataCollector:
    """Collect historical stock-price data using *yfinance*."""

    def get_stock_data(
        self,
        symbol: str,
        period: str = "60d",
    ) -> pd.DataFrame:
        """
        Download OHLCV data for *symbol*.

        Args:
            symbol: Yahoo Finance ticker (e.g. ``"AAPL"``, ``"ZOMATO.NS"``).
            period: Look-back window accepted by ``yfinance.download``
                    (``"1mo"``, ``"60d"``, ``"3mo"``, …).

        Returns:
            DataFrame with columns ``Open, High, Low, Close, Volume``
            indexed by date.

        Raises:
            ValueError: If no data is returned for the given symbol.
        """
        logger.info("Downloading stock data for '%s' (period=%s) …", symbol, period)

        try:
            data: pd.DataFrame = yf.download(
                symbol, period=period, progress=False,
            )
        except Exception as exc:
            logger.error("yfinance error for '%s': %s", symbol, exc)
            raise ValueError(f"Failed to download data for {symbol}: {exc}") from exc

        if data.empty:
            raise ValueError(
                f"No data returned for symbol '{symbol}'.  "
                "Check the ticker or try a different period."
            )

        # Flatten MultiIndex columns if present (yfinance ≥ 0.2.31)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        logger.info(
            "Downloaded %d rows for '%s' (%s → %s).",
            len(data), symbol,
            data.index.min().strftime("%Y-%m-%d"),
            data.index.max().strftime("%Y-%m-%d"),
        )
        return data

    def calculate_realized_volatility(
        self,
        prices: pd.DataFrame,
        window: int = 7,
    ) -> float:
        """
        Calculate annualised realised volatility from daily close prices.

        Formula:
            ``volatility = std(log_returns, window) × √252``

        Args:
            prices: DataFrame that includes a ``Close`` column.
            window: Rolling-window size (trading days).

        Returns:
            Latest rolling annualised volatility as a decimal
            (e.g. ``0.35`` ≈ 35 %).
        """
        if "Close" not in prices.columns:
            raise ValueError("DataFrame must contain a 'Close' column.")

        close = prices["Close"].dropna()
        if len(close) < window + 1:
            raise ValueError(
                f"Need at least {window + 1} data points; got {len(close)}."
            )

        log_returns = np.log(close / close.shift(1)).dropna()
        rolling_std = log_returns.rolling(window=window).std().dropna()
        annualised = float(rolling_std.iloc[-1]) * np.sqrt(252)

        logger.info(
            "Realised volatility (window=%d): %.4f (%.2f%%)",
            window, annualised, annualised * 100,
        )
        return annualised
