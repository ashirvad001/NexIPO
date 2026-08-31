import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

# Download NLTK data
for resource in ['tokenizers/punkt', 'tokenizers/punkt_tab', 'corpora/stopwords', 'corpora/wordnet']:
    try:
        nltk.data.find(resource)
    except LookupError:
        name = resource.split('/')[-1]
        nltk.download(name, quiet=True)


class TextPreprocessor:
    """Preprocess IPO prospectus text for ML analysis"""
    
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        
        # Risk keywords
        self.risk_keywords = {
            'high_risk': ['risk', 'uncertain', 'volatile', 'loss', 'adverse', 'litigation', 'default'],
            'financial_risk': ['debt', 'liability', 'deficit', 'bankruptcy', 'insolvent'],
            'regulatory_risk': ['regulatory', 'compliance', 'violation', 'penalty', 'investigation'],
            'market_risk': ['competition', 'market share', 'downturn', 'recession'],
            'operational_risk': ['disruption', 'failure', 'breach', 'cyber', 'fraud']
        }
        
        self.negative_indicators = ['may not', 'cannot', 'unable', 'fail', 'decline', 'decrease']
        self.hedging_words = ['may', 'might', 'could', 'possibly', 'potentially', 'uncertain']
    
    def preprocess(self, text: str, return_string: bool = True) -> str | List[str]:
        """Clean and preprocess text"""
        text = text.lower()
        text = re.sub(r'[^a-z\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        try:
            tokens = word_tokenize(text)
        except Exception:
            tokens = text.split()
            
        tokens = [self.lemmatizer.lemmatize(t) for t in tokens if t not in self.stop_words and len(t) > 2]
        
        return ' '.join(tokens) if return_string else tokens
    
    def extract_risk_indicators(self, text: str) -> Dict:
        """Extract risk indicators from text"""
        text_lower = text.lower()
        
        indicators = {}
        for category, keywords in self.risk_keywords.items():
            indicators[category] = sum(text_lower.count(kw) for kw in keywords)
        
        indicators['negative_indicators'] = sum(text_lower.count(ni) for ni in self.negative_indicators)
        indicators['hedging_words'] = sum(text_lower.count(hw) for hw in self.hedging_words)
        indicators['risk_density'] = indicators.get('high_risk', 0) / max(len(text.split()), 1)
        
        return indicators
