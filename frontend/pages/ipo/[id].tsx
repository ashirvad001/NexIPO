// pages/ipo/[id].tsx - Full IPO Detail Page with Analysis
import { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Layout from '@/components/Layout';
import Loading from '@/components/Loading';
import RHPViewer from '@/components/RHPViewer';
import VolatilityForecast from '@/components/VolatilityForecast';
import AllotmentCalculator from '@/components/AllotmentCalculator';
import { apiService } from '@/services/api';
import { IPO } from '@/types/ipo';
import { useWebSocket } from '@/contexts/WebSocketContext';

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—';
  try {
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: 'numeric', month: 'short', year: 'numeric'
    });
  } catch { return '—'; }
}

function formatCurrency(val: number | null | undefined): string {
  if (val == null) return '—';
  return `₹${val.toLocaleString('en-IN')}`;
}

function formatNumber(val: number | null | undefined, suffix = ''): string {
  if (val == null) return '—';
  return `${val.toLocaleString('en-IN')}${suffix}`;
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    open: 'bg-success-50 text-success-700 border-success-200',
    upcoming: 'bg-accent-50 text-accent-700 border-accent-200',
    closed: 'bg-navy-100 text-navy-700 border-navy-200',
    listed: 'bg-purple-100 text-purple-800 border-purple-200',
    withdrawn: 'bg-danger-50 text-danger-700 border-danger-200',
  };
  return (
    <span className={`inline-flex items-center px-2.5 sm:px-3 py-1 rounded-full text-xs sm:text-sm font-medium border ${colors[status] || colors.upcoming}`}>
      <span className={`w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full mr-1.5 sm:mr-2 ${status === 'open' ? 'bg-success-500 animate-pulse' : status === 'upcoming' ? 'bg-accent-500' : status === 'listed' ? 'bg-purple-500' : 'bg-navy-500'}`} />
      {status.charAt(0).toUpperCase() + status.slice(1)}
    </span>
  );
}

function TypeBadge({ type }: { type: string }) {
  return (
    <span className={`inline-flex items-center px-2.5 sm:px-3 py-1 rounded-full text-2xs sm:text-xs font-semibold uppercase tracking-wide ${type === 'sme' ? 'bg-warning-100 text-warning-600' : 'bg-accent-100 text-accent-700'}`}>
      {type === 'sme' ? 'SME' : 'Mainboard'}
    </span>
  );
}

function InfoCard({ title, children, icon }: { title: string; children: React.ReactNode; icon: React.ReactNode }) {
  return (
    <div className="bg-white rounded-xl border border-navy-100 shadow-card hover:shadow-card-hover transition-shadow">
      <div className="px-4 sm:px-5 py-3 sm:py-4 border-b border-navy-100 flex items-center gap-2">
        <span className="text-primary-600 flex-shrink-0">{icon}</span>
        <h3 className="text-xs sm:text-sm font-semibold text-navy-900 uppercase tracking-wide">{title}</h3>
      </div>
      <div className="px-4 sm:px-5 py-3 sm:py-4">{children}</div>
    </div>
  );
}

function DataRow({ label, value, highlight, valueClass }: { label: string; value: string; highlight?: boolean; valueClass?: string }) {
  return (
    <div className={`flex justify-between items-center py-2 sm:py-2.5 ${highlight ? '' : 'border-b border-navy-50'}`}>
      <span className="text-xs sm:text-sm text-navy-500">{label}</span>
      <span className={`text-xs sm:text-sm font-semibold ${valueClass || 'text-navy-900'}`}>{value}</span>
    </div>
  );
}

function GmpIndicator({ gmp, percentage }: { gmp: number | null; percentage: number | null }) {
  if (gmp == null) return <span className="text-navy-400">—</span>;
  const isPositive = gmp >= 0;
  return (
    <div className={`flex items-center gap-2 ${isPositive ? 'text-success-600' : 'text-danger-600'}`}>
      <span className="text-base sm:text-lg font-bold">{isPositive ? '+' : ''}{formatCurrency(gmp)}</span>
      {percentage != null && (
        <span className={`text-xs sm:text-sm px-2 py-0.5 rounded-full ${isPositive ? 'bg-success-100' : 'bg-danger-100'}`}>
          {isPositive ? '↑' : '↓'} {Math.abs(percentage).toFixed(1)}%
        </span>
      )}
    </div>
  );
}

function SubscriptionBar({ label, value, color }: { label: string; value: number | null; color: string }) {
  if (value == null) return null;
  const width = Math.min(value * 20, 100);
  return (
    <div className="mb-3">
      <div className="flex justify-between text-xs sm:text-sm mb-1">
        <span className="text-navy-600">{label}</span>
        <span className="font-semibold text-navy-900">{value.toFixed(2)}x</span>
      </div>
      <div className="w-full bg-navy-100 rounded-full h-2 sm:h-2.5">
        <div className={`h-2 sm:h-2.5 rounded-full transition-all duration-500 ${color}`} style={{ width: `${width}%` }} />
      </div>
    </div>
  );
}

/* ─────────────────────────────────────────────── */
/*  Analysis Components                            */
/* ─────────────────────────────────────────────── */

function ImpactBadge({ impact }: { impact: string }) {
  const styles: Record<string, string> = {
    high: 'bg-warning-100 text-warning-600',
    medium: 'bg-warning-50 text-warning-500',
    low: 'bg-navy-100 text-navy-600',
  };
  return (
    <span className={`text-2xs font-semibold uppercase px-2 py-0.5 rounded-full ${styles[impact] || styles.low}`}>
      {impact} impact
    </span>
  );
}

function AnalysisItem({ item, iconColor }: { item: { title: string; detail: string; impact: string }; iconColor: string }) {
  return (
    <div className="flex gap-3 py-3 border-b border-navy-50 last:border-0">
      <div className={`flex-shrink-0 w-2 h-2 rounded-full mt-2 ${iconColor}`} />
      <div className="flex-1 min-w-0">
        <div className="flex flex-wrap items-center gap-2 mb-1">
          <span className="text-xs sm:text-sm font-semibold text-navy-900">{item.title}</span>
          <ImpactBadge impact={item.impact} />
        </div>
        <p className="text-xs sm:text-sm text-navy-600 leading-relaxed">{item.detail}</p>
      </div>
    </div>
  );
}

function VerdictGauge({ score, label, color }: { score: number; label: string; color: string }) {
  const colors: Record<string, { ring: string; bg: string; text: string }> = {
    green: { ring: 'text-success-500', bg: 'bg-success-50 border-success-200', text: 'text-success-700' },
    yellow: { ring: 'text-warning-500', bg: 'bg-warning-50 border-warning-200', text: 'text-warning-600' },
    red: { ring: 'text-danger-500', bg: 'bg-danger-50 border-danger-200', text: 'text-danger-700' },
    gray: { ring: 'text-navy-400', bg: 'bg-navy-50 border-navy-200', text: 'text-navy-600' },
  };
  const c = colors[color] || colors.gray;
  const circumference = 2 * Math.PI * 45;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className={`rounded-xl border p-4 sm:p-6 text-center ${c.bg}`}>
      <div className="relative inline-flex items-center justify-center w-20 h-20 sm:w-28 sm:h-28 mb-2 sm:mb-3">
        <svg className="w-20 h-20 sm:w-28 sm:h-28 -rotate-90" viewBox="0 0 100 100" aria-hidden="true">
          <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" strokeWidth="6" className="text-navy-200" />
          <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" strokeWidth="6"
            className={c.ring}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
          />
        </svg>
        <span className="absolute text-xl sm:text-2xl font-bold text-navy-900">{score}</span>
      </div>
      <p className={`text-sm sm:text-lg font-bold ${c.text}`}>{label}</p>
    </div>
  );
}

/* ─────────────────────────────────────────────── */
/*  Main Page Component                            */
/* ─────────────────────────────────────────────── */

export default function IPODetailPage() {
  const router = useRouter();
  const { id } = router.query;
  const [initialIpo, setInitialIpo] = useState<IPO | null>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'pros' | 'cons' | 'risks'>('pros');
  const [error, setError] = useState<string | null>(null);

  const { updates } = useWebSocket();
  const liveUpdate = id ? updates[Number(id)] : null;

  // Merge live WS data with REST data
  const ipo = initialIpo ? { ...initialIpo, ...liveUpdate } : null;
  const hasRecentUpdate = liveUpdate && (Date.now() - liveUpdate._timestamp < 2000);

  useEffect(() => {
    if (id) {
      loadIPO();
    }
  }, [id]);

  const loadIPO = async () => {
    try {
      setLoading(true);
      setError(null);
      const [data, analysisData] = await Promise.all([
        apiService.getIPOById(Number(id)),
        apiService.getIPOAnalysis(Number(id)).catch(() => null),
      ]);
      setInitialIpo(data);
      setAnalysis(analysisData);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load IPO');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Layout title="Loading... - NexIPO">
        <Loading fullScreen text="Loading IPO details..." />
      </Layout>
    );
  }

  if (error || !ipo) {
    return (
      <Layout title="Error - NexIPO">
        <div className="max-w-4xl mx-auto px-4 py-8 sm:py-12 text-center">
          <div className="bg-danger-50 rounded-xl sm:rounded-2xl p-6 sm:p-8">
            <svg className="w-12 h-12 sm:w-16 sm:h-16 text-danger-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
            <h2 className="text-lg sm:text-xl font-bold text-navy-900 mb-2">IPO Not Found</h2>
            <p className="text-sm text-navy-500 mb-6">{error || 'The requested IPO could not be found.'}</p>
            <button onClick={() => router.push('/ipos')} className="btn-primary">
              ← Back to All IPOs
            </button>
          </div>
        </div>
      </Layout>
    );
  }

  const hasSubscriptionData = ipo.qib_subscription || ipo.nii_subscription || ipo.retail_subscription || ipo.total_subscription;
  const hasFinancials = ipo.pe_ratio || ipo.roce || ipo.roe || ipo.revenue_growth || ipo.profit_growth || ipo.market_cap_cr;

  const tabs = [
    { key: 'pros' as const, label: 'Pros', count: analysis?.pros?.length || 0, color: 'text-success-600', activeBg: 'bg-success-50 border-success-200', icon: '✓' },
    { key: 'cons' as const, label: 'Cons', count: analysis?.cons?.length || 0, color: 'text-danger-600', activeBg: 'bg-danger-50 border-danger-200', icon: '✗' },
    { key: 'risks' as const, label: 'Risks', count: analysis?.risks?.length || 0, color: 'text-warning-600', activeBg: 'bg-warning-50 border-warning-200', icon: '⚠' },
  ];

  const dotColors: Record<string, string> = {
    pros: 'bg-success-500',
    cons: 'bg-danger-500',
    risks: 'bg-warning-500',
  };

  return (
    <Layout title={`${ipo.company_name} - NexIPO`}>
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">

        {/* Back Button */}
        <button
          onClick={() => router.back()}
          className="flex items-center gap-1 text-sm text-navy-500 hover:text-primary-600 mb-4 sm:mb-6 transition-colors"
          aria-label="Go back"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back
        </button>

        {/* Header Section */}
        <div className="card p-5 sm:p-8 mb-5 sm:mb-6">
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
            <div className="min-w-0">
              <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold text-navy-900 mb-2">{ipo.company_name}</h1>
              <div className="flex flex-wrap items-center gap-2 sm:gap-3 mb-4">
                {ipo.symbol && (
                  <span className="text-xs sm:text-sm font-mono bg-navy-100 text-navy-700 px-2 py-1 rounded">{ipo.symbol}</span>
                )}
                <StatusBadge status={ipo.status} />
                <TypeBadge type={ipo.ipo_type} />
              </div>
            </div>

            {/* GMP Highlight */}
            {ipo.gmp_amount != null && (
              <div className={`flex-shrink-0 rounded-xl p-3 sm:p-4 text-center transition-colors duration-1000 ${hasRecentUpdate && liveUpdate?.type === 'gmp_update' ? 'bg-success-100 border-success-400' : (ipo.gmp_amount >= 0 ? 'bg-success-50 border border-success-200' : 'bg-danger-50 border border-danger-200')}`}>
                <p className="text-2xs sm:text-xs font-semibold text-navy-500 uppercase tracking-wide mb-1">GMP</p>
                <GmpIndicator gmp={ipo.gmp_amount} percentage={ipo.gmp_percentage} />
                {ipo.estimated_listing_price && (
                  <p className="text-2xs sm:text-xs text-navy-500 mt-2">Est. Listing: {formatCurrency(ipo.estimated_listing_price)}</p>
                )}
              </div>
            )}
          </div>

          {/* Key Metrics Row */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4 mt-5 sm:mt-6 pt-5 sm:pt-6 border-t border-navy-100">
            <div>
              <p className="text-2xs sm:text-xs text-navy-500 mb-0.5 sm:mb-1">Price Band</p>
              <p className="text-sm sm:text-lg font-bold text-navy-900">
                {ipo.price_band_lower && ipo.price_band_upper
                  ? `${formatCurrency(ipo.price_band_lower)} – ${formatCurrency(ipo.price_band_upper)}`
                  : ipo.price_band_upper ? formatCurrency(ipo.price_band_upper) : '—'}
              </p>
            </div>
            <div>
              <p className="text-2xs sm:text-xs text-navy-500 mb-0.5 sm:mb-1">Issue Size</p>
              <p className="text-sm sm:text-lg font-bold text-navy-900">
                {ipo.issue_size_rs_cr ? `₹${ipo.issue_size_rs_cr.toLocaleString('en-IN')} Cr` : '—'}
              </p>
            </div>
            <div>
              <p className="text-2xs sm:text-xs text-navy-500 mb-0.5 sm:mb-1">Lot Size</p>
              <p className="text-sm sm:text-lg font-bold text-navy-900">{ipo.lot_size ? `${ipo.lot_size} shares` : '—'}</p>
            </div>
            <div>
              <p className="text-2xs sm:text-xs text-navy-500 mb-0.5 sm:mb-1">Min Investment</p>
              <p className="text-sm sm:text-lg font-bold text-navy-900">{formatCurrency(ipo.min_investment)}</p>
            </div>
          </div>
          {ipo.current_price && (
            <div className={`mt-4 pt-4 border-t border-navy-100 flex items-center justify-between rounded px-2 transition-colors duration-1000 ${hasRecentUpdate && liveUpdate?.type === 'price_update' ? 'bg-success-100' : ''}`}>
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 bg-success-500 rounded-full animate-pulse" />
                <span className="text-xs font-semibold text-navy-600 uppercase">Live Market Price</span>
              </div>
              <span className="text-lg sm:text-xl font-bold text-navy-900">{formatCurrency(ipo.current_price)}</span>
            </div>
          )}
        </div>

        {/* ═══ ANALYSIS SECTION ═══ */}
        {analysis && (
          <div className="card mb-5 sm:mb-6 overflow-hidden p-0">
            <div className="px-4 sm:px-6 py-4 sm:py-5 border-b border-navy-100 flex items-center gap-3">
              <div className="w-7 h-7 sm:w-8 sm:h-8 bg-primary-100 text-primary-600 rounded-lg flex items-center justify-center flex-shrink-0">
                <svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                </svg>
              </div>
              <div>
                <h2 className="text-base sm:text-lg font-bold text-navy-900">IPO Analysis</h2>
                <p className="text-2xs sm:text-xs text-navy-500">Data-driven assessment based on available metrics</p>
              </div>
            </div>

            <div className="p-4 sm:p-6">
              {/* Verdict + Key Metrics Row */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-6 mb-6 sm:mb-8">
                <VerdictGauge
                  score={analysis.verdict.score}
                  label={analysis.verdict.label}
                  color={analysis.verdict.color}
                />
                <div className="sm:col-span-2">
                  <p className="text-xs sm:text-sm text-navy-700 mb-4 leading-relaxed">{analysis.verdict.detail}</p>
                  {analysis.key_metrics && analysis.key_metrics.length > 0 && (
                    <div className="grid grid-cols-2 gap-2 sm:gap-3">
                      {analysis.key_metrics.map((m: any, i: number) => (
                        <div key={i} className="bg-navy-50 rounded-lg px-3 py-2">
                          <p className="text-2xs sm:text-xs text-navy-500">{m.label}</p>
                          <p className={`text-xs sm:text-sm font-bold ${m.status === 'positive' ? 'text-success-600' : m.status === 'negative' ? 'text-danger-600' : 'text-navy-900'}`}>
                            {m.value}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Tabs */}
              <div className="flex gap-1.5 sm:gap-2 mb-4 border-b border-navy-100 pb-3 overflow-x-auto" role="tablist">
                {tabs.map(tab => (
                  <button
                    key={tab.key}
                    onClick={() => setActiveTab(tab.key)}
                    role="tab"
                    aria-selected={activeTab === tab.key}
                    className={`flex items-center gap-1 sm:gap-2 px-3 sm:px-4 py-2 rounded-lg text-xs sm:text-sm font-medium transition-all whitespace-nowrap ${activeTab === tab.key
                      ? `${tab.activeBg} border ${tab.color}`
                      : 'text-navy-500 hover:text-navy-700 hover:bg-navy-50'
                      }`}
                  >
                    <span>{tab.icon}</span>
                    {tab.label}
                    <span className={`text-2xs sm:text-xs px-1.5 py-0.5 rounded-full ${activeTab === tab.key ? 'bg-white/60' : 'bg-navy-100'}`}>{tab.count}</span>
                  </button>
                ))}
              </div>

              {/* Tab Content */}
              <div className="min-h-[100px] sm:min-h-[120px]">
                {activeTab === 'pros' && (
                  analysis.pros.length > 0
                    ? analysis.pros.map((item: any, i: number) => <AnalysisItem key={i} item={item} iconColor="bg-success-500" />)
                    : <p className="text-xs sm:text-sm text-navy-400 py-4">No specific pros identified yet.</p>
                )}
                {activeTab === 'cons' && (
                  analysis.cons.length > 0
                    ? analysis.cons.map((item: any, i: number) => <AnalysisItem key={i} item={item} iconColor="bg-danger-500" />)
                    : <p className="text-xs sm:text-sm text-navy-400 py-4">No specific cons identified.</p>
                )}
                {activeTab === 'risks' && (
                  analysis.risks.length > 0
                    ? analysis.risks.map((item: any, i: number) => <AnalysisItem key={i} item={item} iconColor="bg-warning-500" />)
                    : <p className="text-xs sm:text-sm text-navy-400 py-4">No specific risks identified.</p>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Volatility Forecast Component */}
        <div className="mb-5 sm:mb-6">
          <VolatilityForecast 
            ipoId={ipo.id}
            symbol={ipo.symbol || ''}
            companyName={ipo.company_name}
          />
        </div>

        {/* Allotment Calculator Section */}
        <div className="mb-5 sm:mb-6">
          <AllotmentCalculator 
            ipoId={ipo.id}
            companyName={ipo.company_name}
            lotSize={ipo.lot_size}
            priceUpper={ipo.price_band_upper}
            retailSubscription={ipo.retail_subscription}
            status={ipo.status}
          />
        </div>

        {/* Details Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6 mb-5 sm:mb-6">

          {/* Important Dates */}
          <InfoCard title="Important Dates"
            icon={<svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>}
          >
            <DataRow label="Open Date" value={formatDate(ipo.open_date)} />
            <DataRow label="Close Date" value={formatDate(ipo.close_date)} />
            <DataRow label="Allotment Date" value={formatDate(ipo.allotment_date)} />
            <DataRow label="Listing Date" value={formatDate(ipo.listing_date)} highlight />
          </InfoCard>

          {/* Pricing Details */}
          <InfoCard title="Pricing"
            icon={<svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
          >
            <DataRow label="Price Band" value={ipo.price_band_lower && ipo.price_band_upper ? `${formatCurrency(ipo.price_band_lower)} – ${formatCurrency(ipo.price_band_upper)}` : '—'} />
            <DataRow label="Issue Price" value={formatCurrency(ipo.issue_price)} />
            <DataRow label="Listing Price" value={formatCurrency(ipo.listing_price)} valueClass={ipo.listing_price && ipo.issue_price ? (ipo.listing_price >= ipo.issue_price ? 'text-success-600' : 'text-danger-600') : undefined} />
            <DataRow label="Current Price" value={formatCurrency(ipo.current_price)} />
            {ipo.listing_gain_percentage != null && (
              <DataRow label="Listing Gain" value={`${ipo.listing_gain_percentage >= 0 ? '+' : ''}${ipo.listing_gain_percentage.toFixed(2)}%`}
                valueClass={ipo.listing_gain_percentage >= 0 ? 'text-success-600' : 'text-danger-600'} highlight />
            )}
          </InfoCard>

          {/* Issue Details */}
          <InfoCard title="Issue Details"
            icon={<svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>}
          >
            <DataRow label="Issue Size" value={ipo.issue_size_rs_cr ? `₹${formatNumber(ipo.issue_size_rs_cr)} Cr` : '—'} />
            <DataRow label="Fresh Issue" value={ipo.fresh_issue_size ? `₹${formatNumber(ipo.fresh_issue_size)} Cr` : '—'} />
            <DataRow label="Offer for Sale" value={ipo.offer_for_sale ? `₹${formatNumber(ipo.offer_for_sale)} Cr` : '—'} />
            <DataRow label="Shares Offered" value={ipo.shares_offered ? formatNumber(ipo.shares_offered) : '—'} />
            <DataRow label="Lot Size" value={ipo.lot_size ? `${ipo.lot_size} shares` : '—'} />
            <DataRow label="Min Investment" value={formatCurrency(ipo.min_investment)} highlight />
          </InfoCard>

          {/* Company Info */}
          <InfoCard title="Company Info"
            icon={<svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>}
          >
            <DataRow label="Industry Sector" value={ipo.industry_sector || '—'} />
            <DataRow label="IPO Type" value={ipo.ipo_type === 'sme' ? 'SME' : 'Mainboard'} />
            <DataRow label="Registrar" value={ipo.registrar || '—'} />
            <DataRow label="Lead Managers" value={ipo.lead_managers || '—'} highlight />
          </InfoCard>
        </div>

        {/* Subscription Data */}
        {hasSubscriptionData && (
          <div className="mb-5 sm:mb-6">
            <InfoCard title="Subscription Status"
              icon={<svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>}
            >
              <div className={`grid grid-cols-1 sm:grid-cols-2 gap-x-6 sm:gap-x-8 transition-colors duration-1000 rounded p-2 ${hasRecentUpdate && liveUpdate?.type === 'subscription_update' ? 'bg-success-50' : ''}`}>
                <div>
                  <SubscriptionBar label="QIB (Institutional)" value={ipo.qib_subscription} color="bg-accent-500" />
                  <SubscriptionBar label="NII (HNI)" value={ipo.nii_subscription} color="bg-purple-500" />
                </div>
                <div>
                  <SubscriptionBar label="Retail" value={ipo.retail_subscription} color="bg-success-500" />
                  <SubscriptionBar label="Total" value={ipo.total_subscription} color="bg-primary-600" />
                </div>
              </div>
            </InfoCard>
          </div>
        )}

        {/* Financial Metrics */}
        {hasFinancials && (
          <div className="mb-5 sm:mb-6">
            <InfoCard title="Financial Metrics"
              icon={<svg className="w-4 h-4 sm:w-5 sm:h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>}
            >
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 sm:gap-x-8">
                <div>
                  <DataRow label="Market Cap" value={ipo.market_cap_cr ? `₹${formatNumber(ipo.market_cap_cr)} Cr` : '—'} />
                  <DataRow label="P/E Ratio" value={ipo.pe_ratio ? formatNumber(ipo.pe_ratio, 'x') : '—'} />
                  <DataRow label="ROCE" value={ipo.roce ? `${ipo.roce.toFixed(1)}%` : '—'} />
                </div>
                <div>
                  <DataRow label="ROE" value={ipo.roe ? `${ipo.roe.toFixed(1)}%` : '—'} />
                  <DataRow label="Revenue Growth" value={ipo.revenue_growth ? `${ipo.revenue_growth.toFixed(1)}%` : '—'} valueClass={ipo.revenue_growth && ipo.revenue_growth > 0 ? 'text-success-600' : undefined} />
                  <DataRow label="Profit Growth" value={ipo.profit_growth ? `${ipo.profit_growth.toFixed(1)}%` : '—'} valueClass={ipo.profit_growth && ipo.profit_growth > 0 ? 'text-success-600' : undefined} />
                </div>
              </div>
            </InfoCard>
          </div>
        )}

        {/* ═══ RHP VIEWER SECTION ═══ */}
        <RHPViewer
          ipoId={ipo.id}
          companyName={ipo.company_name}
          hasProspectusInitially={!!ipo.prospectus_file_id}
        />

        {/* ═══ AI TRACK RECORD CTA ═══ */}
        <a
          href="/model-accuracy"
          className="group flex items-center justify-between gap-4 mt-6 sm:mt-8 px-5 py-4 rounded-xl bg-gradient-to-r from-primary-50 to-indigo-50 border border-primary-200 hover:border-primary-400 hover:shadow-md transition-all"
        >
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-primary-100 flex items-center justify-center flex-shrink-0">
              <svg className="w-5 h-5 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
            </div>
            <div>
              <p className="text-sm font-semibold text-navy-900">See our AI track record</p>
              <p className="text-xs text-navy-500">Compare predicted vs actual listing gains across all IPOs</p>
            </div>
          </div>
          <svg className="w-5 h-5 text-navy-400 group-hover:text-primary-600 group-hover:translate-x-0.5 transition-all flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" /></svg>
        </a>

        {/* Footer */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mt-6 sm:mt-8">
          <button
            onClick={() => router.push('/ipos')}
            className="btn-secondary text-sm"
          >
            ← All IPOs
          </button>
          <div className="text-xs text-navy-400 flex flex-col sm:flex-row gap-1 sm:gap-6">
            <span>Updated: {formatDate(ipo.updated_at)}</span>
            <span>Added: {formatDate(ipo.created_at)}</span>
          </div>
        </div>
      </div>
    </Layout>
  );
}
