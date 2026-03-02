import React, { useState } from 'react';
import { apiService } from '@/services/api';

interface MLPredictButtonProps {
  ipoId: number;
  onPredictionComplete?: (result: any) => void;
  onPredictionError?: (error: string) => void;
  variant?: 'primary' | 'secondary';
  disabled?: boolean;
}

const MLPredictButton: React.FC<MLPredictButtonProps> = ({
  ipoId,
  onPredictionComplete,
  onPredictionError,
  variant = 'primary',
  disabled = false
}) => {
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);

  const handlePredict = async () => {
    setLoading(true);
    setProgress(0);

    const progressInterval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return 90;
        }
        return prev + 10;
      });
    }, 500);

    try {
      const result = await apiService.predictRisk(ipoId);
      setProgress(100);

      setTimeout(() => {
        setLoading(false);
        setProgress(0);
        if (onPredictionComplete) {
          onPredictionComplete(result);
        }
      }, 500);
    } catch (error: any) {
      clearInterval(progressInterval);
      setLoading(false);
      setProgress(0);

      const errorMessage = error.response?.data?.detail || error.message || 'Prediction failed';
      if (onPredictionError) {
        onPredictionError(errorMessage);
      }
    }
  };

  return (
    <div className="w-full">
      <button
        onClick={handlePredict}
        disabled={disabled || loading}
        className={`w-full px-4 sm:px-6 py-2.5 sm:py-3 rounded-lg font-semibold text-sm sm:text-base transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 ${variant === 'primary'
            ? 'bg-navy-900 hover:bg-navy-800 text-white active:scale-[0.98]'
            : 'bg-navy-100 hover:bg-navy-200 text-navy-800'
          }`}
        aria-label={loading ? `Analyzing IPO ${progress}%` : 'Run ML Analysis'}
      >
        {loading ? (
          <>
            <svg className="animate-spin h-4 w-4 sm:h-5 sm:w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" aria-hidden="true">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span>Analyzing... {progress}%</span>
          </>
        ) : (
          <>
            <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <span>Run ML Analysis</span>
          </>
        )}
      </button>

      {loading && (
        <div className="mt-2 w-full bg-navy-100 rounded-full h-1.5 sm:h-2 overflow-hidden" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}>
          <div
            className="bg-primary-500 h-1.5 sm:h-2 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}
    </div>
  );
};

export default MLPredictButton;
