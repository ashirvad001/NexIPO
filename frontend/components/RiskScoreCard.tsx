import React, { useState } from 'react';

interface RiskScoreCardProps {
  riskScore: number;
  riskCategory: string;
  confidence?: number;
  explanation?: {
    top_features?: Array<{
      feature: string;
      contribution: number;
      importance_rank?: number;
    }>;
    summary?: string;
  };
}

const RiskScoreCard: React.FC<RiskScoreCardProps> = ({
  riskScore,
  riskCategory,
  confidence,
  explanation
}) => {
  const [showExplanation, setShowExplanation] = useState(false);

  const getRiskColor = () => {
    if (riskScore <= 33) return { bg: 'bg-success-50', text: 'text-success-700', border: 'border-success-200', badge: 'bg-success-100', fill: '#10b981' };
    if (riskScore <= 66) return { bg: 'bg-warning-50', text: 'text-warning-600', border: 'border-warning-200', badge: 'bg-warning-100', fill: '#f59e0b' };
    return { bg: 'bg-danger-50', text: 'text-danger-700', border: 'border-danger-200', badge: 'bg-danger-100', fill: '#ef4444' };
  };

  const colors = getRiskColor();

  return (
    <div className={`border-2 ${colors.border} ${colors.bg} rounded-xl p-4 sm:p-6 shadow-card`}>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 mb-4">
        <h3 className="text-lg sm:text-xl font-bold text-navy-800">ML Risk Assessment</h3>
        <span className={`inline-flex items-center px-2.5 sm:px-3 py-1 rounded-full text-xs sm:text-sm font-semibold ${colors.badge} ${colors.text} whitespace-nowrap`}>
          {riskCategory.toUpperCase()} RISK
        </span>
      </div>

      <div className="flex flex-col xs:flex-row items-center gap-4 sm:gap-6 mb-4 sm:mb-6">
        {/* Circular Progress */}
        <div className="relative w-24 h-24 sm:w-32 sm:h-32 flex-shrink-0">
          <svg className="transform -rotate-90 w-24 h-24 sm:w-32 sm:h-32" aria-hidden="true">
            <circle cx="50%" cy="50%" r="40%" stroke="#e5e7eb" strokeWidth="8" fill="none" />
            <circle cx="50%" cy="50%" r="40%" stroke={colors.fill} strokeWidth="8" fill="none"
              strokeDasharray={`${2 * Math.PI * (0.4 * 128)}`}
              strokeDashoffset={`${2 * Math.PI * (0.4 * 128) * (1 - riskScore / 100)}`}
              strokeLinecap="round"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className={`text-2xl sm:text-3xl font-bold ${colors.text}`}>{riskScore}</span>
          </div>
        </div>

        {/* Risk Details */}
        <div className="flex-1 text-center xs:text-left">
          <div className="mb-3">
            <div className="text-xs sm:text-sm text-navy-500 mb-1">Risk Score</div>
            <div className={`text-xl sm:text-2xl font-bold ${colors.text}`}>{riskScore} / 100</div>
          </div>

          {confidence !== undefined && (
            <div>
              <div className="text-xs sm:text-sm text-navy-500 mb-1">Confidence</div>
              <div className="flex items-center gap-2">
                <div className="flex-1 bg-navy-200 rounded-full h-2" role="progressbar" aria-valuenow={Math.round(confidence * 100)} aria-valuemin={0} aria-valuemax={100}>
                  <div
                    className="h-2 rounded-full transition-all duration-500"
                    style={{ width: `${confidence * 100}%`, backgroundColor: colors.fill }}
                  />
                </div>
                <span className="text-xs sm:text-sm font-semibold text-navy-700">{(confidence * 100).toFixed(0)}%</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Explanation Section */}
      {explanation && explanation.top_features && explanation.top_features.length > 0 && (
        <div className="border-t border-navy-200 pt-4">
          <button
            onClick={() => setShowExplanation(!showExplanation)}
            className="flex items-center justify-between w-full text-left font-semibold text-navy-700 hover:text-navy-900 transition-colors"
            aria-expanded={showExplanation}
          >
            <span className="text-sm sm:text-base">Top Contributing Factors</span>
            <svg className={`w-4 h-4 sm:w-5 sm:h-5 transition-transform ${showExplanation ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {showExplanation && (
            <div className="mt-4 space-y-2.5 sm:space-y-3 animate-fade-in">
              {explanation.top_features.slice(0, 5).map((factor, idx) => (
                <div key={idx} className="bg-white rounded-lg p-3 shadow-card">
                  <div className="flex items-center justify-between mb-1.5 sm:mb-2">
                    <span className="text-xs sm:text-sm font-medium text-navy-700">
                      {factor.feature}
                    </span>
                    <span className="text-2xs sm:text-xs text-navy-500">
                      {(factor.contribution * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-navy-100 rounded-full h-1.5">
                    <div
                      className="bg-purple-500 h-1.5 rounded-full transition-all duration-300"
                      style={{ width: `${Math.abs(factor.contribution) * 100}%` }}
                    />
                  </div>
                </div>
              ))}

              {explanation.summary && (
                <div className="mt-4 p-3 bg-accent-50 border border-accent-200 rounded-lg text-xs sm:text-sm text-navy-700">
                  <strong>Summary:</strong> {explanation.summary}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      <div className="mt-4 text-2xs sm:text-xs text-navy-400 italic">
        * This risk assessment is generated by ML models and should be used as one of many factors in investment decisions.
      </div>
    </div>
  );
};

export default RiskScoreCard;
