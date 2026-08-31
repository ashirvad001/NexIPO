import numpy as np
from typing import List, Dict, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
import logging

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """Extract ML features from preprocessed prospectus text"""
    
    def __init__(self, max_features: int = 1000, ngram_range: Tuple[int, int] = (1, 2)):
        self.max_features = max_features
        self.ngram_range = ngram_range
        
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=ngram_range,
            min_df=2,
            max_df=0.8,
            stop_words='english'
        )
        
        self.scaler = StandardScaler()
        self.is_fitted = False
    
    def extract_tfidf_features(self, texts: List[str], fit: bool = False) -> np.ndarray:
        if fit:
            features = self.tfidf_vectorizer.fit_transform(texts)
        else:
            features = self.tfidf_vectorizer.transform(texts)
        return features.toarray()
    
    def extract_risk_features(self, risk_indicators: Dict) -> Dict[str, float]:
        return {
            'risk_count': risk_indicators.get('high_risk', 0),
            'financial_risk_count': risk_indicators.get('financial_risk', 0),
            'regulatory_risk_count': risk_indicators.get('regulatory_risk', 0),
            'market_risk_count': risk_indicators.get('market_risk', 0),
            'operational_risk_count': risk_indicators.get('operational_risk', 0),
            'negative_indicator_count': risk_indicators.get('negative_indicators', 0),
            'hedging_word_count': risk_indicators.get('hedging_words', 0),
            'risk_density': risk_indicators.get('risk_density', 0),
        }
    
    def extract_readability_features(self, text: str) -> Dict[str, float]:
        words = text.split()
        sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        word_count = len(words)
        sentence_count = len(sentences)
        
        return {
            'word_count': word_count,
            'sentence_count': sentence_count,
            'avg_word_length': np.mean([len(w) for w in words]) if words else 0,
            'avg_sentence_length': word_count / sentence_count if sentence_count > 0 else 0,
        }
    
    def extract_section_features(self, sections: Dict[str, str]) -> Dict[str, float]:
        features = {}
        for section_name in ['risk_factors', 'financial_information', 'management', 'business_strategy']:
            section_text = sections.get(section_name, '')
            word_count = len(section_text.split())
            features[f'{section_name}_word_count'] = word_count
            features[f'{section_name}_present'] = 1 if word_count > 0 else 0
        return features
    
    def extract_financial_metrics_features(self, ipo_data: Dict) -> Dict[str, float]:
        features = {
            'issue_size': ipo_data.get('issue_size_rs_cr', 0) or 0,
            'total_subscription': ipo_data.get('total_subscription', 0) or 0,
            'gmp_percentage': ipo_data.get('gmp_percentage', 0) or 0,
            'pe_ratio': ipo_data.get('pe_ratio', 0) or 0,
        }
        return features
    
    def combine_features(self, tfidf_features: np.ndarray, risk_features: Dict, 
                        readability_features: Dict, section_features: Dict, 
                        financial_features: Dict) -> np.ndarray:
        custom_features = {}
        custom_features.update(risk_features)
        custom_features.update(readability_features)
        custom_features.update(section_features)
        custom_features.update(financial_features)
        
        custom_feature_values = []
        for v in custom_features.values():
            if v is None:
                custom_feature_values.append(0.0)
            else:
                try:
                    val = float(v)
                    custom_feature_values.append(0.0 if (np.isnan(val) or np.isinf(val)) else val)
                except Exception:
                    custom_feature_values.append(0.0)
        
        custom_feature_array = np.array(custom_feature_values, dtype=np.float64).reshape(1, -1)
        
        if tfidf_features.ndim == 1:
            tfidf_features = tfidf_features.reshape(1, -1)
        
        combined = np.hstack([tfidf_features, custom_feature_array])
        return np.nan_to_num(combined, nan=0.0, posinf=1e5, neginf=-1e5)
    
    def fit_transform(self, texts: List[str], risk_indicators_list: List[Dict],
                     sections_list: List[Dict], ipo_data_list: List[Dict]) -> Tuple[np.ndarray, List[str]]:
        tfidf_features = self.extract_tfidf_features(texts, fit=True)
        
        all_features = []
        for i in range(len(texts)):
            risk_feats = self.extract_risk_features(risk_indicators_list[i])
            read_feats = self.extract_readability_features(texts[i])
            sect_feats = self.extract_section_features(sections_list[i])
            fin_feats = self.extract_financial_metrics_features(ipo_data_list[i])
            
            combined = self.combine_features(tfidf_features[i], risk_feats, read_feats, sect_feats, fin_feats)
            all_features.append(combined.flatten())
        
        feature_matrix = np.vstack(all_features)
        feature_matrix = np.nan_to_num(feature_matrix, nan=0.0, posinf=1e5, neginf=-1e5)
        feature_matrix = self.scaler.fit_transform(feature_matrix)
        feature_matrix = np.nan_to_num(feature_matrix, nan=0.0, posinf=1e5, neginf=-1e5)
        
        self.is_fitted = True
        
        tfidf_names = [f'tfidf_{name}' for name in self.tfidf_vectorizer.get_feature_names_out()]
        custom_names = (
            list(self.extract_risk_features({}).keys()) +
            list(self.extract_readability_features('').keys()) +
            list(self.extract_section_features({}).keys()) +
            list(self.extract_financial_metrics_features({}).keys())
        )
        feature_names = tfidf_names + custom_names
        
        return feature_matrix, feature_names
    
    def extract_features(
        self,
        processed_text: str,
        sections: Dict[str, str],
        ipo_data: Dict,
        risk_indicators: Dict
    ) -> np.ndarray:
        """Extract features for single prediction"""
        if self.is_fitted:
            try:
                tfidf_features = self.extract_tfidf_features([processed_text], fit=False)[0]
            except Exception:
                tfidf_features = np.zeros(self.max_features)
        else:
            tfidf_features = np.zeros(self.max_features)
        
        risk_feats = self.extract_risk_features(risk_indicators)
        read_feats = self.extract_readability_features(processed_text)
        sect_feats = self.extract_section_features(sections)
        fin_feats = self.extract_financial_metrics_features(ipo_data)
        
        combined = self.combine_features(tfidf_features, risk_feats, read_feats, sect_feats, fin_feats)
        return combined
    
    def get_feature_names(self) -> List[str]:
        """Get list of feature names"""
        if self.is_fitted and hasattr(self.tfidf_vectorizer, "get_feature_names_out"):
            try:
                tfidf_names = [f'tfidf_{name}' for name in self.tfidf_vectorizer.get_feature_names_out()]
            except Exception:
                tfidf_names = [f'tfidf_{i}' for i in range(self.max_features)]
        else:
            tfidf_names = [f'tfidf_{i}' for i in range(self.max_features)]
        custom_names = (
            list(self.extract_risk_features({}).keys()) +
            list(self.extract_readability_features('').keys()) +
            list(self.extract_section_features({}).keys()) +
            list(self.extract_financial_metrics_features({}).keys())
        )
        return tfidf_names + custom_names
    
    def transform(self, text: str, risk_indicators: Dict, sections: Dict, ipo_data: Dict) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("FeatureExtractor must be fitted before transform")
        
        tfidf_features = self.extract_tfidf_features([text], fit=False)[0]
        risk_feats = self.extract_risk_features(risk_indicators)
        read_feats = self.extract_readability_features(text)
        sect_feats = self.extract_section_features(sections)
        fin_feats = self.extract_financial_metrics_features(ipo_data)
        
        combined = self.combine_features(tfidf_features, risk_feats, read_feats, sect_feats, fin_feats)
        combined = self.scaler.transform(combined)
        
        return combined.flatten()

    def save(self, filepath: str):
        import joblib, os
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        joblib.dump({
            'tfidf_vectorizer': self.tfidf_vectorizer,
            'scaler': self.scaler,
            'is_fitted': self.is_fitted,
            'max_features': self.max_features,
            'ngram_range': self.ngram_range
        }, filepath)

    def load(self, filepath: str):
        import joblib, os
        if os.path.exists(filepath):
            data = joblib.load(filepath)
            self.tfidf_vectorizer = data.get('tfidf_vectorizer', self.tfidf_vectorizer)
            self.scaler = data.get('scaler', self.scaler)
            self.is_fitted = data.get('is_fitted', False)
            self.max_features = data.get('max_features', self.max_features)
            self.ngram_range = data.get('ngram_range', self.ngram_range)
        return self
