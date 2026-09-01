// pages/model-accuracy.tsx — AI Track Record / Model Accuracy Page
import { useState, useEffect, useMemo, useCallback } from 'react';
import Layout from '@/components/Layout';
import Loading from '@/components/Loading';
import { apiService } from '@/services/api';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Cell,
} from 'recharts';

/* ─── Types ─── */
interface AccuracyRecord {
  ipo_id: number;
  company_name: string;
  listing_date: string | null;
  predicted_gain: number;
  actual_gain: number;
  error: number;
  directionally_correct: boolean;
  ipo_type: string;
  model_version: string;
  predicted_at: string | null;
}

interface AccuracySummary {
  sample_size: number;
  overall_accuracy: number | null;
  mean_absolute_error: number | null;
  breakdown: {
    mainboard: { sample_size: number; accuracy: number; mean_absolute_error: number } | null;
    sme: { sample_size: number; accuracy: number; mean_absolute_error: number } | null;
  };
}

/* ─── Helpers ─── */
function formatDate(dateStr: string | null): string {
  if (!dateStr) return '—';
  try {
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  } catch {
    return '—';
  }
}

type SortKey = 'listing_date' | 'predicted_gain' | 'actual_gain' | 'error' | 'company_name';

/* ─── Scatter tooltip ─── */
function CustomTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload as AccuracyRecord;
  return (
    <div className="bg-navy-900 text-white rounded-lg px-4 py-3 shadow-modal text-sm max-w-xs">
      <p className="font-semibold text-primary-300 mb-1">{d.company_name}</p>
      <p>Predicted: <span className="font-medium">{d.predicted_gain.toFixed(1)}%</span></p>
      <p>Actual: <span className="font-medium">{d.actual_gain.toFixed(1)}%</span></p>
      <p>Error: <span className="font-medium">{d.error.toFixed(1)}pp</span></p>
      <p className="mt-1">
        {d.directionally_correct
          ? <span className="text-emerald-400">✓ Directionally Correct</span>
          : <span className="text-red-400">✗ Wrong Direction</span>}
      </p>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════════ */

export default function ModelAccuracyPage() {
  const [records, setRecords] = useState<AccuracyRecord[]>([]);
  const [summary, setSummary] = useState<AccuracySummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters & sort
  const [search, setSearch] = useState('');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [sortKey, setSortKey] = useState<SortKey>('listing_date');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  /* ─── Fetch data ─── */
  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const [accRes, sumRes] = await Promise.all([
          apiService.getModelAccuracy(),
          apiService.getModelAccuracySummary(),
        ]);
        if (!cancelled) {
          setRecords(accRes.records ?? []);
          setSummary(sumRes);
        }
      } catch (e: any) {
        if (!cancelled) setError(e?.message ?? 'Failed to load data');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  /* ─── Client-side filter + sort ─── */
  const filtered = useMemo(() => {
    let data = [...records];
    if (typeFilter !== 'all') {
      data = data.filter((r) => r.ipo_type === typeFilter);
    }
    if (search.trim()) {
      const q = search.toLowerCase();
      data = data.filter((r) => r.company_name.toLowerCase().includes(q));
    }
    // Sort
    data.sort((a, b) => {
      let av: any, bv: any;
      switch (sortKey) {
        case 'company_name':
          av = a.company_name.toLowerCase();
          bv = b.company_name.toLowerCase();
          break;
        case 'listing_date':
          av = a.listing_date ?? '';
          bv = b.listing_date ?? '';
          break;
        default:
          av = (a as any)[sortKey];
          bv = (b as any)[sortKey];
      }
      if (av < bv) return sortOrder === 'asc' ? -1 : 1;
      if (av > bv) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });
    return data;
  }, [records, typeFilter, search, sortKey, sortOrder]);

  const handleSort = useCallback(
    (key: SortKey) => {
      if (sortKey === key) {
        setSortOrder((o) => (o === 'asc' ? 'desc' : 'asc'));
      } else {
        setSortKey(key);
        setSortOrder('desc');
      }
    },
    [sortKey],
  );

  function SortIcon({ column }: { column: SortKey }) {
    if (sortKey !== column) return <span className="text-navy-300 ml-1">↕</span>;
    return <span className="text-primary-400 ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>;
  }

  /* ─── Render ─── */
  if (loading) {
    return (
      <Layout title="AI Track Record — NexIPO" description="Model accuracy and prediction track record">
        <div className="max-w-7xl mx-auto px-4 py-20"><Loading /></div>
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout title="AI Track Record — NexIPO">
        <div className="max-w-7xl mx-auto px-4 py-20 text-center">
          <p className="text-danger-600 text-lg">{error}</p>
        </div>
      </Layout>
    );
  }

  const acc = summary?.overall_accuracy;
  const mae = summary?.mean_absolute_error;
  const n = summary?.sample_size ?? 0;
  const mbBreak = summary?.breakdown?.mainboard;
  const smeBreak = summary?.breakdown?.sme;

  return (
    <Layout
      title="AI Track Record — NexIPO"
      description={`Our BERT+LSTM model has ${acc != null ? acc + '% directional accuracy' : 'no predictions yet'} across ${n} IPOs.`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">

        {/* ═══ HERO / HEADLINE STATS ═══ */}
        <section className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-navy-900 via-navy-800 to-primary-900 p-8 sm:p-10 mb-10 shadow-xl">
          {/* Decorative rings */}
          <div className="absolute -right-20 -top-20 w-72 h-72 rounded-full border border-primary-500/10" />
          <div className="absolute -right-10 -top-10 w-52 h-52 rounded-full border border-primary-500/5" />

          <div className="relative z-10">
            <div className="flex items-center gap-2 mb-3">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-primary-500/15 text-primary-300 text-xs font-semibold tracking-wide uppercase">
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                BERT + LSTM Model
              </span>
            </div>

            {n > 0 ? (
              <>
                <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black text-white tracking-tight mb-2">
                  <span className="text-primary-400">{acc}%</span> Directional Accuracy
                </h1>
                <p className="text-navy-300 text-base sm:text-lg mb-8">
                  across <span className="text-white font-semibold">{n}</span> IPOs with a mean absolute error of <span className="text-white font-semibold">{mae}pp</span>
                </p>
              </>
            ) : (
              <>
                <h1 className="text-3xl sm:text-4xl lg:text-5xl font-black text-white tracking-tight mb-2">
                  AI Track Record
                </h1>
                <p className="text-navy-300 text-base sm:text-lg mb-8">
                  No predictions have been recorded yet. Run volatility predictions on listed IPOs to start building the track record.
                </p>
              </>
            )}

            {/* Breakdown cards */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <StatCard label="Sample Size" value={n.toString()} sub="Total IPOs evaluated" />
              {mbBreak && (
                <StatCard
                  label="Mainboard"
                  value={`${mbBreak.accuracy}%`}
                  sub={`${mbBreak.sample_size} IPOs · ${mbBreak.mean_absolute_error}pp MAE`}
                />
              )}
              {smeBreak && (
                <StatCard
                  label="SME"
                  value={`${smeBreak.accuracy}%`}
                  sub={`${smeBreak.sample_size} IPOs · ${smeBreak.mean_absolute_error}pp MAE`}
                />
              )}
            </div>
          </div>
        </section>

        {/* ═══ SCATTER CHART ═══ */}
        {filtered.length > 0 && (
          <section className="bg-white rounded-2xl border border-navy-100 shadow-card p-5 sm:p-8 mb-10">
            <h2 className="text-lg font-bold text-navy-900 mb-1">Predicted vs Actual Listing Gain</h2>
            <p className="text-sm text-navy-400 mb-6">Each dot is one IPO. Points near the diagonal line indicate accurate predictions.</p>
            <div className="w-full" style={{ height: 400 }}>
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart margin={{ top: 10, right: 30, bottom: 20, left: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis
                    type="number"
                    dataKey="predicted_gain"
                    name="Predicted"
                    unit="%"
                    tick={{ fontSize: 12 }}
                    label={{ value: 'Predicted Gain %', position: 'insideBottom', offset: -10, fontSize: 13 }}
                  />
                  <YAxis
                    type="number"
                    dataKey="actual_gain"
                    name="Actual"
                    unit="%"
                    tick={{ fontSize: 12 }}
                    label={{ value: 'Actual Gain %', angle: -90, position: 'insideLeft', offset: 5, fontSize: 13 }}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  {/* Perfect-prediction diagonal */}
                  <ReferenceLine
                    segment={[
                      { x: Math.min(...filtered.map(r => r.predicted_gain), ...filtered.map(r => r.actual_gain)) - 5,
                        y: Math.min(...filtered.map(r => r.predicted_gain), ...filtered.map(r => r.actual_gain)) - 5 },
                      { x: Math.max(...filtered.map(r => r.predicted_gain), ...filtered.map(r => r.actual_gain)) + 5,
                        y: Math.max(...filtered.map(r => r.predicted_gain), ...filtered.map(r => r.actual_gain)) + 5 },
                    ]}
                    stroke="#6366f1"
                    strokeDasharray="6 3"
                    strokeWidth={1.5}
                  />
                  <Scatter data={filtered} fill="#3b82f6">
                    {filtered.map((entry, idx) => (
                      <Cell
                        key={idx}
                        fill={entry.directionally_correct ? '#10b981' : '#ef4444'}
                        opacity={0.75}
                      />
                    ))}
                  </Scatter>
                </ScatterChart>
              </ResponsiveContainer>
            </div>
            <div className="flex items-center gap-6 mt-4 text-xs text-navy-500">
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" /> Directionally Correct</span>
              <span className="flex items-center gap-1.5"><span className="w-2.5 h-2.5 rounded-full bg-red-500 inline-block" /> Wrong Direction</span>
              <span className="flex items-center gap-1.5"><span className="w-5 border-t-2 border-dashed border-indigo-500 inline-block" /> Perfect Prediction</span>
            </div>
          </section>
        )}

        {/* ═══ FILTERS ═══ */}
        <section className="flex flex-col sm:flex-row gap-3 mb-6">
          {/* Search */}
          <div className="relative flex-1">
            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-navy-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by company name..."
              className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-navy-200 bg-white text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 transition-shadow"
            />
          </div>
          {/* Type filter */}
          <div className="flex rounded-xl border border-navy-200 overflow-hidden bg-white">
            {(['all', 'mainboard', 'sme'] as const).map((t) => (
              <button
                key={t}
                onClick={() => setTypeFilter(t)}
                className={`px-4 py-2.5 text-sm font-medium transition-colors ${
                  typeFilter === t
                    ? 'bg-primary-500 text-white'
                    : 'text-navy-600 hover:bg-navy-50'
                }`}
              >
                {t === 'all' ? 'All' : t === 'mainboard' ? 'Mainboard' : 'SME'}
              </button>
            ))}
          </div>
        </section>

        {/* ═══ TABLE ═══ */}
        <section className="bg-white rounded-2xl border border-navy-100 shadow-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-navy-100">
              <thead className="bg-navy-50">
                <tr>
                  {([
                    ['company_name', 'Company'],
                    ['listing_date', 'Listed'],
                    ['predicted_gain', 'Predicted'],
                    ['actual_gain', 'Actual'],
                    ['error', 'Error'],
                  ] as [SortKey, string][]).map(([key, label]) => (
                    <th
                      key={key}
                      onClick={() => handleSort(key)}
                      className="px-4 py-3 text-left text-xs font-semibold text-navy-600 uppercase tracking-wider cursor-pointer hover:text-primary-600 select-none whitespace-nowrap"
                    >
                      {label}
                      <SortIcon column={key} />
                    </th>
                  ))}
                  <th className="px-4 py-3 text-left text-xs font-semibold text-navy-600 uppercase tracking-wider">Direction</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-navy-600 uppercase tracking-wider">Type</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-navy-50">
                {filtered.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-4 py-16 text-center text-navy-400 text-sm">
                      {records.length === 0
                        ? 'No prediction records yet. Run volatility predictions on listed IPOs to populate this table.'
                        : 'No results match your filters.'}
                    </td>
                  </tr>
                ) : (
                  filtered.map((r) => (
                    <tr key={r.ipo_id} className="hover:bg-navy-50/50 transition-colors">
                      <td className="px-4 py-3 text-sm font-medium text-navy-900 max-w-[220px] truncate">
                        <a href={`/ipo/${r.ipo_id}`} className="hover:text-primary-600 transition-colors">
                          {r.company_name}
                        </a>
                      </td>
                      <td className="px-4 py-3 text-sm text-navy-500 whitespace-nowrap">{formatDate(r.listing_date)}</td>
                      <td className={`px-4 py-3 text-sm font-medium whitespace-nowrap ${r.predicted_gain >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                        {r.predicted_gain >= 0 ? '+' : ''}{r.predicted_gain.toFixed(1)}%
                      </td>
                      <td className={`px-4 py-3 text-sm font-medium whitespace-nowrap ${r.actual_gain >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                        {r.actual_gain >= 0 ? '+' : ''}{r.actual_gain.toFixed(1)}%
                      </td>
                      <td className="px-4 py-3 text-sm text-navy-600 whitespace-nowrap">{r.error.toFixed(1)}pp</td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        {r.directionally_correct ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
                            Correct
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-red-50 text-red-700 border border-red-200">
                            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" /></svg>
                            Wrong
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-2xs font-semibold uppercase tracking-wide ${r.ipo_type === 'sme' ? 'bg-amber-100 text-amber-700' : 'bg-sky-100 text-sky-700'}`}>
                          {r.ipo_type === 'sme' ? 'SME' : 'Mainboard'}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          {filtered.length > 0 && (
            <div className="px-4 py-3 bg-navy-50 border-t border-navy-100 text-xs text-navy-500">
              Showing {filtered.length} of {records.length} records
            </div>
          )}
        </section>
      </div>
    </Layout>
  );
}

/* ─── Sub-components ─── */
function StatCard({ label, value, sub }: { label: string; value: string; sub: string }) {
  return (
    <div className="bg-white/5 backdrop-blur-sm rounded-xl px-5 py-4 border border-white/10">
      <p className="text-xs font-semibold text-navy-400 uppercase tracking-wider mb-1">{label}</p>
      <p className="text-2xl font-black text-white">{value}</p>
      <p className="text-xs text-navy-400 mt-0.5">{sub}</p>
    </div>
  );
}
