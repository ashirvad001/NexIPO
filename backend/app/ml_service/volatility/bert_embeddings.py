"""
BERT Sentiment & Embedding Extractor – Phase 1 of Stock Volatility Forecaster
===============================================================================
Uses **FinBERT** (ProsusAI/finbert) for financial-sentiment analysis and
**bert-base-uncased** for 768-dim embedding extraction.
"""

import logging
from typing import Dict, List

import numpy as np
import torch
from transformers import (
    BertModel,
    BertTokenizer,
    pipeline,
)

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)s  %(levelname)s  %(message)s",
)


class BERTSentimentExtractor:
    """Extract sentiment scores and dense embeddings from text using BERT."""

    # Keyword lists for geopolitical-event detection
    _GEO_KEYWORDS: Dict[str, List[str]] = {
        "war": [
            "war", "conflict", "military", "attack", "invasion",
            "missile", "airstrike", "troops", "combat", "battlefield",
        ],
        "economic": [
            "sanctions", "tariff", "trade war", "inflation",
            "interest rate", "recession", "embargo", "currency crisis",
            "economic downturn", "fiscal",
        ],
        "political": [
            "election", "government", "policy", "regulation",
            "legislation", "political crisis", "coup", "protest",
            "diplomatic", "geopolitical",
        ],
        "pandemic": [
            "pandemic", "covid", "lockdown", "outbreak",
            "quarantine", "vaccine", "epidemic", "virus",
            "public health", "contagion",
        ],
    }

    # Maps FinBERT labels → numeric polarity
    _POLARITY_MAP = {"positive": 1, "negative": -1, "neutral": 0}

    def __init__(self) -> None:
        """Load FinBERT (sentiment) and bert-base-uncased (embeddings)."""

        logger.info("Loading FinBERT sentiment model (ProsusAI/finbert) …")
        self.sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model="ProsusAI/finbert",
            tokenizer="ProsusAI/finbert",
            truncation=True,
            max_length=512,
        )

        logger.info("Loading BERT tokenizer & model (bert-base-uncased) …")
        self.tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
        self.bert_model = BertModel.from_pretrained("bert-base-uncased")
        self.bert_model.eval()  # inference-only

        logger.info("BERTSentimentExtractor ready.")

    # ------------------------------------------------------------------
    # Sentiment
    # ------------------------------------------------------------------
    def extract_sentiment(self, text: str) -> Dict:
        """
        Run FinBERT sentiment analysis on a single piece of text.

        Args:
            text: Article / headline text.

        Returns:
            ``{"label": "positive"|"negative"|"neutral",
              "score": float,   # confidence ∈ [0, 1]
              "polarity": 1|0|-1}``
        """
        if not text or not text.strip():
            return {"label": "neutral", "score": 0.0, "polarity": 0}

        try:
            result = self.sentiment_pipeline(text[:512])[0]
            label = result["label"]
            score = round(float(result["score"]), 4)
            polarity = self._POLARITY_MAP.get(label, 0)
            return {"label": label, "score": score, "polarity": polarity}
        except Exception as exc:
            logger.error("Sentiment extraction failed: %s", exc)
            return {"label": "neutral", "score": 0.0, "polarity": 0}

    # ------------------------------------------------------------------
    # Embeddings
    # ------------------------------------------------------------------
    def extract_embeddings(self, text: str) -> np.ndarray:
        """
        Produce a 768-dimensional [CLS]-token embedding via BERT.

        Args:
            text: Input text (truncated to 512 tokens internally).

        Returns:
            numpy array of shape ``(768,)``.
        """
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True,
        )

        with torch.no_grad():
            outputs = self.bert_model(**inputs)

        # outputs.last_hidden_state -> (batch, seq_len, hidden)
        cls_embedding = outputs.last_hidden_state[:, 0, :]  # [CLS] token
        return cls_embedding.squeeze().numpy()

    # ------------------------------------------------------------------
    # Batch processing
    # ------------------------------------------------------------------
    def process_news_batch(self, articles: List[str]) -> Dict:
        """
        Process a list of articles: extract sentiment + embeddings.

        Args:
            articles: List of article texts.

        Returns:
            ``{"embeddings":      np.ndarray (N, 768),
              "sentiments":       [float, …],   # polarity per article
              "avg_sentiment":    float,
              "sentiment_volatility": float}``
        """
        if not articles:
            return {
                "embeddings": np.array([]),
                "sentiments": [],
                "avg_sentiment": 0.0,
                "sentiment_volatility": 0.0,
            }

        embeddings: List[np.ndarray] = []
        sentiments: List[float] = []

        for idx, text in enumerate(articles):
            logger.info(
                "Processing article %d / %d …", idx + 1, len(articles),
            )

            # sentiment
            sent = self.extract_sentiment(text)
            sentiments.append(float(sent["polarity"]) * sent["score"])

            # embedding
            emb = self.extract_embeddings(text)
            embeddings.append(emb)

        sentiments_arr = np.array(sentiments)
        avg_sentiment = float(np.mean(sentiments_arr))
        sentiment_vol = float(np.std(sentiments_arr)) if len(sentiments_arr) > 1 else 0.0

        return {
            "embeddings": np.stack(embeddings),          # (N, 768)
            "sentiments": sentiments,
            "avg_sentiment": round(avg_sentiment, 4),
            "sentiment_volatility": round(sentiment_vol, 4),
        }

    # ------------------------------------------------------------------
    # Geopolitical features
    # ------------------------------------------------------------------
    def extract_geopolitical_features(self, text: str) -> Dict:
        """
        Score text for geopolitical-event signals using keyword matching.

        Args:
            text: Article text.

        Returns:
            ``{"war_score": int, "economic_score": int,
              "political_score": int, "pandemic_score": int,
              "total_geopolitical_score": int}``
        """
        text_lower = text.lower()
        scores: Dict[str, int] = {}

        for category, keywords in self._GEO_KEYWORDS.items():
            count = sum(1 for kw in keywords if kw in text_lower)
            scores[f"{category}_score"] = count

        scores["total_geopolitical_score"] = sum(
            v for k, v in scores.items() if k != "total_geopolitical_score"
        )
        return scores
