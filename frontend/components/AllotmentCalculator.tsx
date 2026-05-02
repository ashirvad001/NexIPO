import React, { useState, useEffect, useCallback } from 'react';
import { apiService } from '@/services/api';

// ─── Types ────────────────────────────────────────────────────────────────
interface AllotmentResult {
  success: boolean;
  probability_pct: number | null;
  scenario: string;
  expected_lots: number | null;
  allotment_note: string;
  breakdown: {
    retail_shares_available: number;
    retail_lots_available: number;
    estimated_applications: number;
    retail_subscription: number;
    retail_portion_pct: number;
  };
  application: {
    lots_applied: number;
    shares_applied: number;
    application_amount_rs: number;
    min_lot_size: number;
    price_per_share: number;
  };
  insights: {
    multi_lot_benefit: boolean;
    confidence: number;
    nii_warning: string | null;
    qib_subscription: number | null;
    nii_subscription: number | null;
  };
}

interface CategoryComparison {
  categories: {
    retail?: { label: string; subscription: number; probability_pct: number | null; note: string; issue_portion: string };
    nii?: { label: string; subscription: number; probability_pct: number | null; note: string; issue_portion: string };
    qib?: { label: string; subscription: number; probability_pct: number | null; note: string; issue_portion: string };
  };
}

interface AllotmentCalculatorProps {
  ipoId: number;
  companyName: string;
  lotSize: number | null;
  priceUpper: number | null;
  retailSubscription: number | null;
  status: string;
}

// ─── Helpers ──────────────────────────────────────────────────────────────
function formatINR(amount: number): string {
  if (amount >= 1_00_00_000) return `₹${(amount / 1_00_00_000).toFixed(2)} Cr`;
  if (amount >= 1_00_000) return `₹${(amount / 1_00_000).toFixed(2)}L`;
  return `₹${amount.toLocaleString('en-IN')}`;
}

function formatNum(n: number): string {
  if (n >= 1_00_00_000) return `${(n / 1_00_00_000).toFixed(1)}Cr`;
  if (n >= 1_00_000) return `${(n / 1_00_000).toFixed(1)}L`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
  return n.toLocaleString('en-IN');
}

function getProbabilityColor(pct: number | null): { ring: string; text: string; bg: string; bar: string } {
  if (pct === null) return { ring: '#64748b', text: '#475569', bg: '#f1f5f9', bar: '#94a3b8' };
  if (pct >= 70) return { ring: '#10b981', text: '#065f46', bg: '#ecfdf5', bar: '#10b981' };
  if (pct >= 40) return { ring: '#f59e0b', text: '#78350f', bg: '#fffbeb', bar: '#f59e0b' };
  if (pct >= 15) return { ring: '#f97316', text: '#7c2d12', bg: '#fff7ed', bar: '#f97316' };
  return { ring: '#ef4444', text: '#7f1d1d', bg: '#fef2f2', bar: '#ef4444' };
}

function getScenarioLabel(scenario: string): string {
  const map: Record<string, string> = {
    pending: 'Awaiting Data',
    undersubscribed: 'Undersubscribed',
    lightly_oversubscribed: 'Lightly Oversubscribed',
    oversubscribed_draw: 'Lucky Draw',
  };
  return map[scenario] || scenario;
}

// ─── Circular probability gauge ───────────────────────────────────────────
function ProbabilityGauge({ pct, size = 160 }: { pct: number | null; size?: number }) {
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const progress = pct !== null ? (pct / 100) * circumference : 0;
  const colors = getProbabilityColor(pct);

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox="0 0 120 120" className="-rotate-90">
        {/* Track */}
        <circle cx="60" cy="60" r={radius} fill="none" stroke="#e2e8f0" strokeWidth="10" />
        {/* Progress */}
        <circle
          cx="60" cy="60" r={radius}
          fill="none"
          stroke={colors.ring}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference - progress}
          style={{ transition: 'stroke-dashoffset 1s cubic-bezier(0.4,0,0.2,1)' }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        {pct !== null ? (
          <>
            <span className="text-3xl font-black tabular-nums" style={{ color: colors.ring, lineHeight: 1 }}>
              {pct < 1 ? '<1' : Math.round(pct)}
            </span>
            <span className="text-xs font-bold text-slate-400 mt-0.5">%</span>
          </>
        ) : (
          <span className="text-sm font-semibold text-slate-400">N/A</span>
        )}
      </div>
    </div>
  );
}

// ─── Mini stat pill ───────────────────────────────────────────────────────
function StatPill({ label, value, highlight = false }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className={`rounded-xl px-4 py-3 flex flex-col gap-0.5 ${highlight ? 'bg-indigo-50 border border-indigo-100' : 'bg-slate-50 border border-slate-100'}`}>
      <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">{label}</span>
      <span className={`text-base font-bold ${highlight ? 'text-indigo-700' : 'text-slate-800'}`}>{value}</span>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────
const AllotmentCalculator: React.FC<AllotmentCalculatorProps> = ({
  ipoId, companyName, lotSize, priceUpper, retailSubscription, status,
}) => {
  const [lotsApplied, setLotsApplied] = useState(1);
  const [result, setResult] = useState<AllotmentResult | null>(null);
  const [comparison, setComparison] = useState<CategoryComparison | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'calculator' | 'compare'>('calculator');
  const [hasCalculated, setHasCalculated] = useState(false);

  const minInvestment = lotSize && priceUpper ? lotSize * priceUpper : null;

  const calculate = useCallback(async (lots: number) => {
    setLoading(true);
    setError(null);
    try {
      const [calcData, compareData] = await Promise.all([
        apiService.getAllotmentCalculation(ipoId, lots),
        apiService.getAllotmentComparison(ipoId)
      ]);
      
      if (!calcData.success) {
        setError(calcData.message || 'Calculation failed');
      } else {
        setResult(calcData);
        setComparison(compareData);
        setHasCalculated(true);
      }
    } catch (e) {
      setError('Failed to connect to server. Ensure backend is running.');
    } finally {
      setLoading(false);
    }
  }, [ipoId]);

  // Auto-calculate on mount if data is available
  useEffect(() => {
    if (lotSize && priceUpper && (retailSubscription !== null)) {
      calculate(1);
    }
  }, []);

  // Recalculate when lots change (debounced)
  useEffect(() => {
    if (!hasCalculated) return;
    const t = setTimeout(() => calculate(lotsApplied), 400);
    return () => clearTimeout(t);
  }, [lotsApplied]);

  const colors = getProbabilityColor(result?.probability_pct ?? null);
  const canCalculate = !!(lotSize && priceUpper && retailSubscription !== null);

  // ── Cannot calculate state ─────────────────────────────────────────
  if (!canCalculate) {
    return (
      <div className="rounded-2xl border border-slate-200 bg-white overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-100 flex items-center justify-center">
            <svg className="w-4 h-4 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 11h.01M12 11h.01M15 11h.01M4 19h16a2 2 0 002-2V7a2 2 0 00-2-2H4a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          <h3 className="font-bold text-slate-900">Allotment Calculator</h3>
        </div>
        <div className="p-6 text-center">
          <div className="w-14 h-14 rounded-full bg-amber-50 border border-amber-100 flex items-center justify-center mx-auto mb-3">
            <svg className="w-7 h-7 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <p className="text-sm font-semibold text-slate-700 mb-1">Data Not Yet Available</p>
          <p className="text-xs text-slate-400">
            {status === 'upcoming'
              ? 'Lot size and subscription data will be available once the IPO opens.'
              : 'Required data (lot size, price band, subscription) is missing for this IPO.'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white overflow-hidden shadow-sm">

      {/* ── Header ──────────────────────────────────────────────────── */}
      <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-100 flex items-center justify-center flex-shrink-0">
            <svg className="w-4 h-4 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 11h.01M12 11h.01M15 11h.01M4 19h16a2 2 0 002-2V7a2 2 0 00-2-2H4a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          <div>
            <h3 className="font-bold text-slate-900 text-sm">Allotment Calculator</h3>
            <p className="text-xs text-slate-400">Based on SEBI retail allotment algorithm</p>
          </div>
        </div>
        {/* Tabs */}
        <div className="flex rounded-lg overflow-hidden border border-slate-200 text-xs font-semibold">
          {(['calculator', 'compare'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-3 py-1.5 capitalize transition-colors ${activeTab === tab
                ? 'bg-indigo-600 text-white'
                : 'text-slate-500 hover:text-slate-700 hover:bg-slate-50'}`}
            >
              {tab === 'compare' ? 'Categories' : tab}
            </button>
          ))}
        </div>
      </div>

      {/* ── Error ───────────────────────────────────────────────────── */}
      {error && (
        <div className="mx-5 mt-4 p-3 bg-red-50 border border-red-100 rounded-xl text-xs text-red-600 font-medium flex items-start gap-2">
          <svg className="w-4 h-4 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          {error}
        </div>
      )}

      {/* ══════════════════════════════════════════════════════════════
          TAB: CALCULATOR
      ══════════════════════════════════════════════════════════════ */}
      {activeTab === 'calculator' && (
        <div className="p-5 space-y-5">

          {/* Lots applied slider */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-bold text-slate-600 uppercase tracking-wider">
                Lots to Apply
              </label>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setLotsApplied(l => Math.max(1, l - 1))}
                  className="w-6 h-6 rounded-md bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-sm flex items-center justify-center transition-colors"
                >−</button>
                <span className="w-8 text-center font-black text-slate-900 tabular-nums">{lotsApplied}</span>
                <button
                  onClick={() => setLotsApplied(l => Math.min(20, l + 1))}
                  className="w-6 h-6 rounded-md bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-sm flex items-center justify-center transition-colors"
                >+</button>
              </div>
            </div>
            <input
              type="range"
              min={1} max={20} value={lotsApplied}
              onChange={e => setLotsApplied(Number(e.target.value))}
              className="w-full h-2 bg-slate-200 rounded-full appearance-none cursor-pointer accent-indigo-600"
            />
            <div className="flex justify-between text-xs text-slate-400 mt-1">
              <span>1 lot</span>
              <span>20 lots</span>
            </div>
            {minInvestment && (
              <p className="mt-2 text-xs text-center font-semibold text-slate-500">
                Application amount:{' '}
                <span className="text-indigo-600">{formatINR(lotsApplied * minInvestment)}</span>
                <span className="text-slate-400 font-normal ml-1">
                  ({lotsApplied * (lotSize || 0)} shares @ ₹{priceUpper})
                </span>
              </p>
            )}
          </div>

          {/* ── Result card ─────────────────────────────────────────── */}
          {loading ? (
            <div className="flex flex-col items-center justify-center py-8 gap-3">
              <div className="w-8 h-8 border-2 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
              <span className="text-xs text-slate-400 font-medium">Calculating...</span>
            </div>
          ) : result ? (
            <>
              {/* Gauge + scenario */}
              <div
                className="rounded-2xl p-5 flex flex-col sm:flex-row items-center gap-5"
                style={{ background: colors.bg, border: `1px solid ${colors.ring}22` }}
              >
                <ProbabilityGauge pct={result.probability_pct} size={140} />
                <div className="flex-1 text-center sm:text-left">
                  <div
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold uppercase tracking-wide mb-2"
                    style={{ background: `${colors.ring}18`, color: colors.ring }}
                  >
                    <span className="w-1.5 h-1.5 rounded-full inline-block" style={{ background: colors.ring }} />
                    {getScenarioLabel(result.scenario)}
                  </div>
                  <p className="text-sm font-semibold text-slate-700 leading-relaxed">
                    {result.allotment_note}
                  </p>
                  {result.expected_lots !== null && (
                    <p className="mt-2 text-xs text-slate-500">
                      Expected allotment:{' '}
                      <span className="font-bold text-slate-800">{result.expected_lots} lot{result.expected_lots !== 1 ? 's' : ''}</span>
                      {' '}= {result.expected_lots * (lotSize || 0)} shares
                    </p>
                  )}
                </div>
              </div>

              {/* Stats grid */}
              <div className="grid grid-cols-2 gap-2.5">
                <StatPill
                  label="Est. Applications"
                  value={formatNum(result.breakdown.estimated_applications)}
                />
                <StatPill
                  label="Lots Available"
                  value={formatNum(result.breakdown.retail_lots_available)}
                />
                <StatPill
                  label="Retail Subscription"
                  value={`${result.breakdown.retail_subscription.toFixed(2)}×`}
                />
                <StatPill
                  label="Your Application"
                  value={formatINR(result.application.application_amount_rs)}
                  highlight
                />
              </div>

              {/* Insight pills */}
              <div className="space-y-2">
                {/* Multi-lot insight */}
                <div className={`rounded-xl px-4 py-3 flex items-start gap-3 text-xs ${result.insights.multi_lot_benefit
                  ? 'bg-emerald-50 border border-emerald-100'
                  : 'bg-amber-50 border border-amber-100'}`}>
                  <span className="text-base flex-shrink-0 mt-0.5">
                    {result.insights.multi_lot_benefit ? '✅' : '⚠️'}
                  </span>
                  <div>
                    <p className={`font-bold mb-0.5 ${result.insights.multi_lot_benefit ? 'text-emerald-800' : 'text-amber-800'}`}>
                      {result.insights.multi_lot_benefit ? 'Applying more lots helps' : 'Applying more lots has no effect'}
                    </p>
                    <p className={result.insights.multi_lot_benefit ? 'text-emerald-700' : 'text-amber-700'}>
                      {result.insights.multi_lot_benefit
                        ? 'You can increase your chances by applying for more lots in this scenario.'
                        : 'In lucky draw mode, SEBI allots exactly 1 lot per applicant. Additional lots do not improve your odds.'}
                    </p>
                  </div>
                </div>

                {/* NII warning */}
                {result.insights.nii_warning && (
                  <div className="rounded-xl px-4 py-3 flex items-start gap-3 text-xs bg-red-50 border border-red-100">
                    <span className="text-base flex-shrink-0 mt-0.5">🚨</span>
                    <div>
                      <p className="font-bold text-red-800 mb-0.5">Category Warning</p>
                      <p className="text-red-700">{result.insights.nii_warning}</p>
                    </div>
                  </div>
                )}

                {/* Confidence */}
                <div className="rounded-xl px-4 py-3 bg-slate-50 border border-slate-100">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Estimate Confidence</span>
                    <span className="text-xs font-black text-slate-800">{Math.round(result.insights.confidence * 100)}%</span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-1.5">
                    <div
                      className="h-1.5 rounded-full bg-indigo-500 transition-all duration-700"
                      style={{ width: `${result.insights.confidence * 100}%` }}
                    />
                  </div>
                  <p className="text-xs text-slate-400 mt-1.5">
                    Based on {Math.round(result.insights.confidence * 5)}/5 available data points
                  </p>
                </div>
              </div>
            </>
          ) : (
            <div className="text-center py-6">
              <button
                onClick={() => calculate(lotsApplied)}
                className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-bold rounded-xl transition-colors"
              >
                Calculate Probability
              </button>
            </div>
          )}
        </div>
      )}

      {/* ══════════════════════════════════════════════════════════════
          TAB: CATEGORY COMPARISON
      ══════════════════════════════════════════════════════════════ */}
      {activeTab === 'compare' && (
        <div className="p-5 space-y-3">
          <p className="text-xs text-slate-500 leading-relaxed">
            Different investor categories have different allotment rules. Compare your odds across categories.
          </p>

          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="w-6 h-6 border-2 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
            </div>
          ) : comparison ? (
            Object.entries(comparison.categories).map(([key, cat]) => {
              const catColors = getProbabilityColor(cat.probability_pct);
              const isRetail = key === 'retail';
              return (
                <div
                  key={key}
                  className={`rounded-xl border p-4 ${isRetail ? 'ring-2 ring-indigo-400 ring-offset-1' : ''}`}
                  style={isRetail ? { borderColor: '#a5b4fc' } : { borderColor: '#e2e8f0' }}
                >
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-black text-slate-900">{cat.label}</span>
                        {isRetail && (
                          <span className="text-xs bg-indigo-100 text-indigo-700 font-bold px-2 py-0.5 rounded-full">You</span>
                        )}
                      </div>
                      <span className="text-xs text-slate-400">{cat.issue_portion} of issue reserved</span>
                    </div>
                    <div className="text-right flex-shrink-0">
                      {cat.probability_pct !== null ? (
                        <>
                          <span
                            className="text-2xl font-black tabular-nums"
                            style={{ color: catColors.ring }}
                          >
                            {cat.probability_pct < 1 ? '<1' : Math.round(cat.probability_pct)}%
                          </span>
                          <span className="text-xs text-slate-400 block">probability</span>
                        </>
                      ) : (
                        <span className="text-xs text-slate-400 font-medium">Discretionary</span>
                      )}
                    </div>
                  </div>

                  {/* Progress bar */}
                  {cat.probability_pct !== null && (
                    <div className="w-full bg-slate-100 rounded-full h-1.5 mb-2">
                      <div
                        className="h-1.5 rounded-full transition-all duration-700"
                        style={{
                          width: `${Math.min(cat.probability_pct, 100)}%`,
                          background: catColors.bar,
                        }}
                      />
                    </div>
                  )}

                  <div className="flex items-center justify-between text-xs text-slate-500">
                    <span>Subscription: <span className="font-bold text-slate-700">{cat.subscription?.toFixed(2)}×</span></span>
                  </div>
                  <p className="text-xs text-slate-400 mt-1.5 leading-relaxed">{cat.note}</p>
                </div>
              );
            })
          ) : (
            <div className="text-center py-6">
              <button
                onClick={() => calculate(lotsApplied)}
                className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-bold rounded-xl transition-colors"
              >
                Load Comparison
              </button>
            </div>
          )}

          {/* SEBI disclaimer */}
          <div className="rounded-xl bg-slate-50 border border-slate-100 px-4 py-3 text-xs text-slate-400 leading-relaxed">
            <span className="font-bold text-slate-500">SEBI Rule:</span> In oversubscribed retail categories, 
            each applicant receives a maximum of 1 lot via computerized lucky draw. Allotment is random — 
            probability estimates are statistical, not guaranteed.
          </div>
        </div>
      )}

      {/* ── Footer ──────────────────────────────────────────────────── */}
      <div className="px-5 py-3 border-t border-slate-100 bg-slate-50 flex items-center justify-between">
        <span className="text-xs text-slate-400">
          Estimates based on avg. 1.3 lots/application (historical NSE data)
        </span>
        {result && (
          <button
            onClick={() => calculate(lotsApplied)}
            className="text-xs text-indigo-600 hover:text-indigo-700 font-semibold transition-colors flex items-center gap-1"
          >
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </button>
        )}
      </div>
    </div>
  );
};

export default AllotmentCalculator;
