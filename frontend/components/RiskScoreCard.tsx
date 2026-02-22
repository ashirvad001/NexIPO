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
    if (riskScore <= 33) return { bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200', badge: 'bg-green-100' };
    if (riskScore <= 66) return { bg: 'bg-yellow-50', text: 'text-yellow-700', border: 'border-yellow-200', badge: 'bg-yellow-100' };
    return { bg: 'bg-red-50', text: 'text-red-700', border: 'border-red-200', badge: 'bg-red-100' };
  };

  const getProgressColor = () => {
    if (riskScore <= 33) return '#10b981';
    if (riskScore <= 66) return '#f59e0b';
    return '#ef4444';
  };

  const colors = getRiskColor();
  const progressColor = getProgressColor();

  return (
    <div className={`border-2 ${colors.border} ${colors.bg} rounded-lg p-6 shadow-lg`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xl font-bold text-gray-800">ML Risk Assessment</h3>
        <span className={`px-3 py-1 rounded-full text-sm font-semibold ${colors.badge} ${colors.text}`}>
          {riskCategory.toUpperCase()} RISK
        </span>
      </div>

      <div className="flex items-center gap-6 mb-6">
        {/* Circular Progress */}
        <div className="relative w-32 h-32">
          <svg className="transform -rotate-90 w-32 h-32">
            <circle
              cx="64"
              cy="64"
              r="56"
              stroke="#e5e7eb"
              strokeWidth="8"
              fill="none"
            />
            <circle
              cx="64"
              cy="64"
              r="56"
              stroke={progressColor}
              strokeWidth="8"
              fill="none"
              strokeDasharray={`${2 * Math.PI * 56}`}
              strokeDashoffset={`${2 * Math.PI * 56 * (1 - riskScore / 100)}`}
              strokeLinecap="round"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className={`text-3xl font-bold ${colors.text}`}>{riskScore}</span>
          </div>
        </div>

        {/* Risk Details */}
        <div className="flex-1">
          <div className="mb-3">
            <div className="text-sm text-gray-600 mb-1">Risk Score</div>
            <div className={`text-2xl font-bold ${colors.text}`}>{riskScore} / 100</div>
          </div>
          
          {confidence !== undefined && (
            <div>
              <div className="text-sm text-gray-600 mb-1">Confidence</div>
              <div className="flex items-center gap-2">
                <div className="flex-1 bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${colors.text.replace('text', 'bg')}`}
                    style={{ width: `${confidence * 100}%` }}
                  />
                </div>
                <span className="text-sm font-semibold">{(confidence * 100).toFixed(0)}%</span>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Explanation Section */}
      {explanation && explanation.top_features && explanation.top_features.length > 0 && (
        <div className="border-t pt-4">
          <button
            onClick={() => setShowExplanation(!showExplanation)}
            className="flex items-center justify-between w-full text-left font-semibold text-gray-700 hover:text-gray-900"
          >
            <span>Top Contributing Factors</span>
            <span className="text-xl">{showExplanation ? '−' : '+'}</span>
          </button>

          {showExplanation && (
            <div className="mt-4 space-y-3">
              {explanation.top_features.slice(0, 5).map((factor, idx) => (
                <div key={idx} className="bg-white rounded p-3 shadow-sm">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">
                      {factor.feature}
                    </span>
                    <span className="text-xs text-gray-500">
                      {(factor.contribution * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-1.5">
                    <div
                      className="bg-purple-600 h-1.5 rounded-full"
                      style={{ width: `${Math.abs(factor.contribution) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
              
              {explanation.summary && (
                <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded text-sm text-gray-700">
                  <strong>Summary:</strong> {explanation.summary}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      <div className="mt-4 text-xs text-gray-500 italic">
        * This risk assessment is generated by ML models and should be used as one of many factors in investment decisions.
      </div>
    </div>
  );
};

export default RiskScoreCard;
