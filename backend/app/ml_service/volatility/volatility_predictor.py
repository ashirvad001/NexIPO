"""
Complete end-to-end volatility forecasting pipeline 
Integrates Phase 1 (BERT) and Phase 2 (LSTM)
"""
import logging
import time
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

from app.ml_service.volatility.bert_embeddings import BERTSentimentExtractor
from app.ml_service.volatility.lstm_model import LSTMVolatilityPredictor
from app.ml_service.volatility.data_collector import NewsDataCollector, StockDataCollector
from app.ml_service.feature_schema import VolatilityFeatureSchema

logger = logging.getLogger(__name__)

class VolatilityForecaster:
    """Complete BERT+LSTM prediction pipeline"""
    
    def __init__(self, newsapi_key: str = "your_newsapi_key_here"):
        """Initialize all components"""
        logger.info("Initializing VolatilityForecaster pipeline...")
        self.bert = BERTSentimentExtractor()
        
        # Load trained model
        self.lstm = LSTMVolatilityPredictor()
        try:
            self.lstm.load_model('models/lstm_volatility_model.pth')
            logger.info("Successfully loaded LSTM weights.")
        except Exception as e:
            logger.error(f"Could not load LSTM model: {e}")
            raise RuntimeError(f"Failed to load LSTM weights: {e}")
            
        try:
            self.news_collector = NewsDataCollector(newsapi_key=newsapi_key)
        except Exception as e:
            logger.warning(f"NewsDataCollector initialization issue: {e}. News fetching may fail.")
            self.news_collector = None
            
        self.stock_collector = StockDataCollector()
        
        # Simple In-Memory Cache: {symbol_or_name: (timestamp, result_dict)}
        self._cache: Dict[str, tuple] = {}
        self._cache_ttl = timedelta(hours=1)

    def predict_volatility(
        self,
        symbol: str,
        company_name: str,
        days_ahead: int = 7
    ) -> Dict:
        """
        Complete prediction pipeline with caching and structured insights
        """
        # Cache Check
        cache_key = f"{symbol}_{company_name}"
        if cache_key in self._cache:
            ts, cached_res = self._cache[cache_key]
            if datetime.now() - ts < self._cache_ttl:
                logger.info(f"Returning cached prediction for {cache_key}")
                return cached_res

        t0 = time.time()
        logger.info(f"Starting volatility prediction for {company_name} ({symbol})")
        
        # 1. Collect News & 2. Extract Sentiment
        articles = []
        if self.news_collector:
            articles = self.news_collector.get_recent_news(company_name, days_back=7)
        
        # Limit to top 10 articles to cap BERT processing time
        articles = articles[:10]
            
        t1 = time.time()
        logger.info(f"[PERF] News collection: {t1 - t0:.2f}s ({len(articles)} articles)")
            
        sentiment_data = self.bert.process_news_batch(articles)
        sentiment_score = sentiment_data.get("avg_sentiment", 0.0)
        sentiment_vol = sentiment_data.get("sentiment_volatility", 0.0)
        
        t2 = time.time()
        logger.info(f"[PERF] BERT sentiment: {t2 - t1:.2f}s")
        
        # 3. Detect Geopolitical Events
        agg_geo_text = " ".join(articles)
        geo_features = self.bert.extract_geopolitical_features(agg_geo_text)
        geo_score = geo_features.get("total_geopolitical_score", 0) / 10.0 # simple scaling
        
        # 4. Get stock prices
        try:
            stock_df = self.stock_collector.get_stock_data(symbol, period="60d")
            
            if len(stock_df) < (self.lstm.sequence_length + 10): 
                raise ValueError("Insufficient price history")
                
            historical_volatility = self.stock_collector.calculate_realized_volatility(stock_df, window=7)
            
            # 5. Prepare LSTM features
            features_df = self._prepare_lstm_features(stock_df, sentiment_score, sentiment_vol, geo_score)
            X_input_raw = features_df.values[-self.lstm.sequence_length:]
            X_input_scaled = self.lstm.scaler.transform(X_input_raw)
            X_seq = np.array([X_input_scaled], dtype=np.float32)
            
            t3 = time.time()
            logger.info(f"[PERF] Stock data + features: {t3 - t2:.2f}s")
            
            # 6 & 7. Predict volatility & Confidence (OPTIMIZED: 5 MC iterations)
            mean_pred, std_pred = self.lstm.predict_with_confidence(X_seq, n_iterations=5)
            
            pred_vol_sc = mean_pred[0].reshape(-1, 1)
            pred_vol_actual = self.lstm.target_scaler.inverse_transform(pred_vol_sc)[0][0]
            pred_std_sc = std_pred[0].reshape(-1, 1)
            pred_std_actual = self.lstm.target_scaler.inverse_transform(pred_std_sc)[0][0] - self.lstm.target_scaler.inverse_transform(np.zeros((1,1)))[0][0]
            
            predicted_volatility = float(max(0, pred_vol_actual))
            confidence_std = float(abs(pred_std_actual))
            risk_level = self.lstm.calculate_risk_level(predicted_volatility)
            
            # Structured Insights
            base_conf = max(0.0, 1.0 - (confidence_std / max(0.01, predicted_volatility)))
            confidence_score = min(0.99, base_conf * 1.5) 
            
            analysis = self._generate_structured_analysis(predicted_volatility, historical_volatility, sentiment_score, geo_score, symbol)

            result = {
                'success': True,
                'symbol': symbol,
                "company_name": company_name,
                'predicted_volatility': predicted_volatility,
                'predicted_volatility_percentage': predicted_volatility * 100,
                'historical_volatility': historical_volatility,
                'confidence_std': confidence_std,
                'risk_level': risk_level,
                'sentiment_score': sentiment_score,
                'geopolitical_impact_score': geo_score,
                'risk_reason': analysis['risk_reason'],
                'pros': analysis['pros'],
                'cons': analysis['cons'],
                'insights': analysis['insights'],
                'confidence_score': confidence_score,
                'timestamp': datetime.now().isoformat()
            }
            
            t4 = time.time()
            logger.info(f"[PERF] LSTM inference + post-processing: {t4 - t3:.2f}s")
            logger.info(f"[PERF] Total prediction time: {t4 - t0:.2f}s")
            
            # Store in Cache
            self._cache[cache_key] = (datetime.now(), result)
            return result
            
        except Exception as e:
            logger.warning(f"Error fetching stock data or predicting via LSTM for {symbol}: {e}")
            logger.info(f"Falling back to sentiment-based heuristic for {company_name}")
            res = self._predict_without_price_history(company_name, sentiment_score, geo_score)
            self._cache[cache_key] = (datetime.now(), res)
            return res

    def _prepare_lstm_features(
        self,
        price_data: pd.DataFrame,
        sentiment: float,
        sentiment_vol: float,
        geo_score: float
    ) -> pd.DataFrame:
        """Combine all features for LSTM."""
        def _rsi(series: pd.Series, period: int = 14):
            delta = series.diff()
            gain = delta.clip(lower=0).rolling(period).mean()
            loss = (-delta.clip(upper=0)).rolling(period).mean()
            rs = gain / (loss + 1e-10)
            return 100 - 100 / (1 + rs)
            
        close = price_data["Close"].squeeze()
        high = price_data["High"].squeeze()
        low = price_data["Low"].squeeze()
        volume = price_data["Volume"].squeeze()

        feat = pd.DataFrame(index=price_data.index)
        feat["log_return"] = np.log(close / close.shift(1))
        feat["rolling_vol_7d"] = feat["log_return"].rolling(7).std() * np.sqrt(252)
        feat["volume_change"] = np.log((volume + 1) / (volume.shift(1) + 1))
        feat["high_low_range"] = (high - low) / (close + 1e-10)
        feat["rsi_14"] = _rsi(close, 14) / 100.0
        sma20 = close.rolling(20).mean()
        feat["sma_ratio_20"] = (close / (sma20 + 1e-10)) - 1
        
        proxy = np.sign(feat["log_return"]) * feat["log_return"].abs()
        feat["sentiment_proxy"] = proxy
        if len(feat) >= 7:
            feat.loc[feat.index[-7:], "sentiment_proxy"] = sentiment / 10.0
        
        feat["momentum_5d"] = (close / close.shift(5)) - 1
        feat.dropna(inplace=True)

        # Enforce canonical column order from schema
        vol_schema = VolatilityFeatureSchema()
        expected_cols = vol_schema.feature_names()
        feat = feat[expected_cols]
        vol_schema.validate_dataframe_columns(list(feat.columns))

        return feat

    def _predict_without_price_history(
        self,
        company_name: str,
        sentiment: float,
        geo_score: float
    ) -> Dict:
        """Handle newly listed IPOs (no price history) using heuristic"""
        base_volatility = 0.40 
        sentiment_impact = -sentiment * 0.15 
        geo_impact = geo_score * 0.10
        predicted_volatility = max(0.1, base_volatility + sentiment_impact + geo_impact)
        risk_level = self.lstm.calculate_risk_level(predicted_volatility)
        
        analysis = self._generate_structured_analysis(predicted_volatility, 0.0, sentiment, geo_score, "NEW_IPO")
        
        return {
            'success': True,
            'symbol': "NEW_IPO",
            'company_name': company_name,
            'predicted_volatility': predicted_volatility,
            'predicted_volatility_percentage': predicted_volatility * 100,
            'historical_volatility': 0.0,
            'confidence_std': 0.05,
            'risk_level': risk_level,
            'sentiment_score': sentiment,
            'geopolitical_impact_score': geo_score,
            'risk_reason': analysis['risk_reason'],
            'pros': analysis['pros'],
            'cons': analysis['cons'],
            'insights': analysis['insights'],
            'confidence_score': 0.50 
        }

    def _generate_structured_analysis(
        self,
        pred_vol: float,
        hist_vol: float,
        sentiment: float,
        geo: float,
        symbol: str
    ) -> Dict:
        """Generate structured categorical analysis"""
        pros = []
        cons = []
        insights = []
        
        # Primary Risk Reason
        if symbol == "NEW_IPO":
            reason = "Limited price history and listing-day excitement are the primary volatility drivers."
        elif geo > 3.0:
            reason = "External geopolitical instability is currently overriding internal stock metrics."
        elif sentiment < -0.4:
            reason = "Dominant bearish news cycle and negative investor sentiment are inflating risk."
        elif pred_vol > hist_vol * 1.5:
            reason = "Technical indicators suggest a significant breakdown in price stability relative to history."
        else:
            reason = "Current market volatility is aligned with standard sector performance trends."

        # Pros/Cons Logic
        if sentiment > 0.1: pros.append("Positive news momentum")
        else: cons.append("Lack of positive media triggers")
        
        if geo < 1.5: pros.append("Stable macro environment")
        else: cons.append(f"Global macro risk (Impact: {geo:.1f})")
        
        if pred_vol < 0.25: pros.append("Low speculative interest")
        elif pred_vol > 0.45: cons.append("High speculative 'froth' observed")
        
        if hist_vol > 0 and pred_vol < hist_vol: pros.append("Volatility cooling trend")
        if hist_vol > 0 and pred_vol > hist_vol: cons.append("Spiking intraday variance")

        # Insights (Dynamic strings)
        if pred_vol > 0.40:
            insights.append("⚠️ High risk of sudden price swings; exercise caution in short-term positions.")
        if sentiment > 0.5:
            insights.append("🚀 Strong 'Buy' sentiment detected in institutional news feeds.")
        if symbol == "NEW_IPO":
            insights.append("ℹ️ Prediction relies on heuristic NLP mapping due to lack of historical OHLCV data.")

        return {
            "risk_reason": reason,
            "pros": pros[:3],
            "cons": cons[:3],
            "insights": insights[:3]
        }
