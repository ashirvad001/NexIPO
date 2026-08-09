import numpy as np
from typing import List, Dict, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
import logging

from app.ml_service.feature_schema import RiskFeatureSchema, RISK_SECTION_NAMES

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """Extract ML features from preprocessed prospectus text.

    Uses ``RiskFeatureSchema`` as the single source of truth for the
    custom (non-TF-IDF) feature list, guaranteeing identical feature
    vectors in both training and inference.
    """

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

        # Shared schema — single source of truth for feature layout
        self.schema = RiskFeatureSchema(max_tfidf_features=max_features)

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
        for section_name in RISK_SECTION_NAMES:
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

    def combine_features(self, tfidf_features: np.ndarray, risk_indicators: Dict,
                        text: str, sections: Dict[str, str],
                        ipo_data: Dict) -> np.ndarray:
        """Combine TF-IDF and custom features using the shared schema.

        Delegates custom feature construction to
        ``RiskFeatureSchema.build_feature_vector()`` to guarantee
        canonical ordering.
        """
        return self.schema.build_feature_vector(
            tfidf_features=tfidf_features,
            risk_indicators=risk_indicators,
            text=text,
            sections=sections,
            ipo_data=ipo_data,
        )

    def fit_transform(self, texts: List[str], risk_indicators_list: List[Dict],
                     sections_list: List[Dict], ipo_data_list: List[Dict]) -> Tuple[np.ndarray, List[str]]:
        tfidf_features = self.extract_tfidf_features(texts, fit=True)

        all_features = []
        for i in range(len(texts)):
            combined = self.combine_features(
                tfidf_features[i],
                risk_indicators_list[i],
                texts[i],
                sections_list[i],
                ipo_data_list[i],
            )
            all_features.append(combined.flatten())

        feature_matrix = np.vstack(all_features)
        feature_matrix = self.scaler.fit_transform(feature_matrix)

        self.is_fitted = True

        tfidf_names = [f'tfidf_{name}' for name in self.tfidf_vectorizer.get_feature_names_out()]
        feature_names = self.schema.get_feature_names(tfidf_names)

        return feature_matrix, feature_names

    def extract_features(
        self,
        processed_text: str,
        sections: Dict[str, str],
        ipo_data: Dict,
        risk_indicators: Dict
    ) -> np.ndarray:
        """Extract features for single prediction.

        Uses the shared schema to build the custom feature vector in
        canonical order, and applies the fitted scaler if available.
        """
        tfidf_features = np.zeros(self.max_features)

        combined = self.schema.build_feature_vector(
            tfidf_features=tfidf_features,
            risk_indicators=risk_indicators,
            text=processed_text,
            sections=sections,
            ipo_data=ipo_data,
        )

        # Apply scaling if the scaler was fitted during training
        if self.is_fitted:
            combined = self.scaler.transform(combined)

        return combined

    def get_feature_names(self) -> List[str]:
        """Get list of feature names from the shared schema."""
        return self.schema.get_feature_names()

    def transform(self, text: str, risk_indicators: Dict, sections: Dict, ipo_data: Dict) -> np.ndarray:
        if not self.is_fitted:
            raise ValueError("FeatureExtractor must be fitted before transform")

        tfidf_features = self.extract_tfidf_features([text], fit=False)[0]

        combined = self.schema.build_feature_vector(
            tfidf_features=tfidf_features,
            risk_indicators=risk_indicators,
            text=text,
            sections=sections,
            ipo_data=ipo_data,
        )
        combined = self.scaler.transform(combined)

        return combined.flatten()
