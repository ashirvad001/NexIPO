// types/ml.ts
export interface RiskPrediction {
  risk_score: number;
  risk_category: 'low' | 'medium' | 'high';
  confidence: number;
  risk_indicators: {
    high_risk: number;
    financial_risk: number;
    regulatory_risk: number;
    market_risk: number;
    operational_risk: number;
    negative_indicators: number;
    hedging_words: number;
    risk_density: number;
  };
  explanation?: {
    top_features: Array<{
      feature: string;
      contribution: number;
      importance_rank: number;
    }>;
    all_contributions?: Record<string, number>;
  };
  explanation_text?: string;
  success: boolean;
  error?: string;
}

export interface ModelStatus {
  model_loaded: boolean;
  explainer_available: boolean;
  status: 'ready' | 'not_trained' | 'error';
  error?: string;
}
