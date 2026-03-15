import React, { useState, useEffect } from 'react';
import { apiService } from '@/services/api';

interface VolatilityForecastProps {
  ipoId: number;
  symbol: string;
  companyName: string;
}

const VolatilityForecast: React.FC<VolatilityForecastProps> = ({
  ipoId,
  symbol,
  companyName
}) => {
  const [forecast, setForecast] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchForecast = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiService.predictVolatility(ipoId);
      setForecast(data);
    } catch (err: any) {
      console.error('Forecast failed:', err);
      setError(err?.response?.data?.detail || "Failed to analyze volatility");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchForecast();
  }, [ipoId]);

  if (loading) {
    return (
      <div className="card bg-white p-6 shadow-sm rounded-xl animate-pulse">
        <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
        <div className="h-24 bg-gray-100 rounded mb-4"></div>
        <div className="grid grid-cols-2 gap-4">
           <div className="h-16 bg-gray-100 rounded"></div>
           <div className="h-16 bg-gray-100 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
        <div className="card bg-rose-50 p-6 border border-rose-100 rounded-xl">
            <h3 className="text-lg font-semibold text-rose-800 mb-2">Volatility Analysis Unavailable</h3>
            <p className="text-rose-600 text-sm">{error}</p>
            <button onClick={fetchForecast} className="mt-4 px-4 py-2 bg-rose-100 text-rose-800 rounded-lg text-sm font-medium hover:bg-rose-200 transition-colors">
                Retry Analysis
            </button>
        </div>
    );
  }

  if (!forecast && !loading) return null;
  if (!forecast) return null; // Safety fallback

  // Tailwind JIT fix: Map risk levels to static class strings
  const colorMap: Record<string, { bg: string, text: string, border: string, badge: string }> = {
    'LOW': { bg: 'bg-emerald-50', text: 'text-emerald-600', border: 'border-emerald-200', badge: 'bg-emerald-500' },
    'MEDIUM': { bg: 'bg-amber-50', text: 'text-amber-600', border: 'border-amber-200', badge: 'bg-amber-500' },
    'HIGH': { bg: 'bg-orange-50', text: 'text-orange-600', border: 'border-orange-200', badge: 'bg-orange-500' },
    'VERY HIGH': { bg: 'bg-red-50', text: 'text-red-600', border: 'border-red-200', badge: 'bg-red-500' },
    'DEFAULT': { bg: 'bg-gray-50', text: 'text-gray-600', border: 'border-gray-200', badge: 'bg-gray-500' }
  };
  
  const styles = colorMap[forecast.risk_level] || colorMap['DEFAULT'];

  return (
    <div className="card bg-gradient-to-br from-indigo-50 to-blue-50/50 p-6 rounded-2xl border border-indigo-100/50 shadow-sm relative overflow-hidden transition-all duration-300 hover:shadow-md group">
      {/* Decorative background element */}
      <div className="absolute top-0 right-0 w-32 h-32 bg-indigo-100 rounded-bl-full opacity-50 -z-10 group-hover:scale-110 transition-transform duration-500"></div>

      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-bold text-gray-800 flex items-center gap-2">
          <span className="text-xl">📊</span> 
          <span>Volatility Forecast</span>
          <span className="text-xs font-normal text-indigo-600 bg-indigo-100 px-2 py-0.5 rounded-full uppercase tracking-wide">AI-Powered</span>
        </h3>
        <button
            onClick={fetchForecast}
            className="text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 p-2 rounded-full transition-colors"
            title="Refresh Forecast"
        >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>
        </button>
      </div>

      {/* Main Metric */}
      <div className="text-center mb-8 relative">
        <div className={`inline-flex flex-col items-center justify-center w-40 h-40 ${styles.bg} border-4 ${styles.border} rounded-full shadow-inner relative z-10 transition-all duration-300 hover:scale-105`}>
          <div className={`text-4xl font-black ${styles.text} tracking-tight`}>
            {forecast.predicted_volatility_percentage.toFixed(1)}<span className="text-2xl text-[0.6em] ml-0.5">%</span>
          </div>
          <div className="text-xs font-medium text-gray-500 uppercase tracking-wider mt-1">Predicted</div>
        </div>
        
        {/* Risk Badge */}
        <div className="absolute -bottom-3 left-1/2 -translate-x-1/2 z-20">
            <span className={`px-5 py-1.5 ${styles.badge} text-white rounded-full text-sm font-bold shadow-lg uppercase tracking-wider whitespace-nowrap`}>
                {forecast.risk_level} RISK
            </span>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="p-4 bg-white/80 backdrop-blur-sm rounded-xl border border-gray-100 shadow-sm transition-transform hover:-translate-y-1">
          <div className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-1">History</div>
          <div className="text-xl font-bold text-gray-800">
            {(forecast.historical_volatility * 100).toFixed(1)}%
          </div>
        </div>
        <div className="p-4 bg-white/80 backdrop-blur-sm rounded-xl border border-gray-100 shadow-sm transition-transform hover:-translate-y-1">
          <div className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-1">Confidence</div>
          <div className="text-xl font-bold text-gray-800">
            {(forecast.confidence_score * 100).toFixed(0)}%
          </div>
        </div>
      </div>

      {/* Sentiment Bar */}
      <div className="mb-6 bg-white/60 p-4 rounded-xl border border-gray-100">
        <div className="flex justify-between items-end mb-2">
          <span className="text-sm font-semibold text-gray-700">Market Sentiment</span>
          <span className={`text-sm font-bold ${forecast.sentiment_score > 0 ? 'text-emerald-600' : 'text-rose-600'} flex items-center gap-1`}>
            {forecast.sentiment_score > 0 ? (
                <><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg> Positive</>
            ) : (
                <><svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" /></svg> Negative</>
            )}
          </span>
        </div>
        
        {/* Bidirectional progress bar wrapper */}
        <div className="w-full bg-gray-200 rounded-full h-2.5 flex relative overflow-hidden">
            {/* Center line marker */}
            <div className="absolute left-1/2 top-0 bottom-0 w-px bg-gray-400 z-10"></div>
            
            {/* Negative fill (grows left from center) */}
            <div className="w-1/2 flex justify-end">
                {forecast.sentiment_score < 0 && (
                     <div 
                         className="h-2.5 bg-rose-500 rounded-l-full animate-pulse" 
                         style={{ width: `${Math.min(100, Math.abs(forecast.sentiment_score) * 100)}%` }}
                     ></div>
                )}
            </div>
            {/* Positive fill (grows right from center) */}
            <div className="w-1/2 flex justify-start">
               {forecast.sentiment_score > 0 && (
                     <div 
                         className="h-2.5 bg-emerald-500 rounded-r-full animate-pulse" 
                         style={{ width: `${Math.min(100, forecast.sentiment_score * 100)}%` }}
                     ></div>
                )}
            </div>
        </div>
      </div>

      {/* Geopolitical Alert (Subtle) */}
      {forecast.geopolitical_impact_score > 2 && (
        <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl mb-6 flex items-center gap-3 animate-fade-in">
            <div className="text-amber-600">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            </div>
            <div className="text-xs font-bold text-amber-900">Geopolitical Impact Detected ({forecast.geopolitical_impact_score.toFixed(1)})</div>
        </div>
      )}

      {/* Structured Diagnosis */}
      <div className="mb-6 bg-white/40 p-5 rounded-2xl border border-white/60 shadow-inner">
        <h4 className="text-xs font-bold text-indigo-500 uppercase tracking-widest mb-3 flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-indigo-500"></span>
            Diagnosis
        </h4>
        <p className="text-sm text-gray-800 font-medium leading-relaxed italic">
            "{forecast.risk_reason}"
        </p>
      </div>

      {/* Pros & Cons Grid */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="p-4 bg-emerald-50/50 rounded-xl border border-emerald-100">
            <div className="text-[10px] font-black text-emerald-600 uppercase tracking-tighter mb-2">Strengths (Pros)</div>
            <ul className="space-y-1.5">
                {forecast.pros.map((pro: string, idx: number) => (
                    <li key={idx} className="text-xs text-emerald-800 flex items-center gap-1.5 font-medium">
                        <svg className="w-3 h-3 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
                        {pro}
                    </li>
                ))}
            </ul>
        </div>
        <div className="p-4 bg-rose-50/50 rounded-xl border border-rose-100">
            <div className="text-[10px] font-black text-rose-600 uppercase tracking-tighter mb-2">Weaknesses (Cons)</div>
            <ul className="space-y-1.5">
                {forecast.cons.map((con: string, idx: number) => (
                    <li key={idx} className="text-xs text-rose-800 flex items-center gap-1.5 font-medium">
                        <svg className="w-3 h-3 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" /></svg>
                        {con}
                    </li>
                ))}
            </ul>
        </div>
      </div>

      {/* Remaining AI Insights */}
      {forecast.insights.length > 0 && (
          <div className="bg-indigo-900/5 p-4 rounded-xl border border-indigo-900/5">
            <div className="space-y-2">
                {forecast.insights.map((insight: string, idx: number) => (
                    <div key={idx} className="text-xs text-indigo-900/70 font-medium flex items-start gap-2">
                        <span>💡</span>
                        <span>{insight.replace(/^[^a-zA-Z0-9]+/, '')}</span>
                    </div>
                ))}
            </div>
          </div>
      )}
    </div>
  );
};

export default VolatilityForecast;
