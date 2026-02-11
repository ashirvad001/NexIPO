import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '@/components/Layout';
import SubscriptionChart from '@/components/SubscriptionChart';
import GMPChart from '@/components/GMPChart';
import Loading from '@/components/Loading';
import Error from '@/components/Error';
import { apiService } from '@/services/api';
import { IPO } from '@/types/ipo';
import {
  formatCrores,
  formatCurrency,
  formatPercentage,
  formatSubscription,
  formatDate,
  formatNumber,
  getStatusColor,
  getRiskColor,
} from '@/utils/formatters';

export default function IPODetail() {
  const router = useRouter();
  const { id } = router.query;
  const [ipo, setIPO] = useState<IPO | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchIPO = async () => {
    if (!id) return;

    setLoading(true);
    setError(null);

    try {
      const data = await apiService.getIPOById(Number(id));
      setIPO(data);
    } catch (err: any) {
      console.error('Error fetching IPO:', err);
      setError(err.response?.data?.detail || 'Failed to fetch IPO details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) {
      fetchIPO();
    }
  }, [id]);

  if (loading) {
    return (
      <Layout>
        <Loading fullScreen text="Loading IPO details..." />
      </Layout>
    );
  }

  if (error || !ipo) {
    return (
      <Layout>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <Error message={error || 'IPO not found'} retry={fetchIPO} />
        </div>
      </Layout>
    );
  }

  return (
    <Layout title={`${ipo.company_name} - IPO Details`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.back()}
            className="text-primary-600 hover:text-primary-700 mb-4 flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back
          </button>

          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                {ipo.company_name}
              </h1>
              {ipo.symbol && (
                <p className="text-lg text-gray-600 font-mono">{ipo.symbol}</p>
              )}
            </div>
            <span className={`badge text-base ${getStatusColor(ipo.status)}`}>
              {ipo.status.toUpperCase()}
            </span>
          </div>

          {ipo.description && (
            <p className="mt-4 text-gray-600 max-w-3xl">{ipo.description}</p>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-8">
            {/* Price Information */}
            <div className="card">
              <h2 className="text-xl font-semibold mb-4">Price Information</h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {ipo.price_band_lower && ipo.price_band_upper && (
                  <div>
                    <p className="text-sm text-gray-500 mb-1">Price Band</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {formatCurrency(ipo.price_band_lower)} - {formatCurrency(ipo.price_band_upper)}
                    </p>
                  </div>
                )}
                {ipo.issue_price && (
                  <div>
                    <p className="text-sm text-gray-500 mb-1">Issue Price</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {formatCurrency(ipo.issue_price)}
                    </p>
                  </div>
                )}
                {ipo.min_investment && (
                  <div>
                    <p className="text-sm text-gray-500 mb-1">Min Investment</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {formatCurrency(ipo.min_investment)}
                    </p>
                  </div>
                )}
                {ipo.lot_size && (
                  <div>
                    <p className="text-sm text-gray-500 mb-1">Lot Size</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {formatNumber(ipo.lot_size)}
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Subscription Data */}
            {ipo.total_subscription && (
              <div className="card">
                <h2 className="text-xl font-semibold mb-4">Subscription Status</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                  <div>
                    <p className="text-sm text-gray-500 mb-1">Total</p>
                    <p className="text-lg font-semibold text-green-600">
                      {formatSubscription(ipo.total_subscription)}
                    </p>
                  </div>
                  {ipo.qib_subscription && (
                    <div>
                      <p className="text-sm text-gray-500 mb-1">QIB</p>
                      <p className="text-lg font-semibold text-gray-900">
                        {formatSubscription(ipo.qib_subscription)}
                      </p>
                    </div>
                  )}
                  {ipo.nii_subscription && (
                    <div>
                      <p className="text-sm text-gray-500 mb-1">NII</p>
                      <p className="text-lg font-semibold text-gray-900">
                        {formatSubscription(ipo.nii_subscription)}
                      </p>
                    </div>
                  )}
                  {ipo.retail_subscription && (
                    <div>
                      <p className="text-sm text-gray-500 mb-1">Retail</p>
                      <p className="text-lg font-semibold text-gray-900">
                        {formatSubscription(ipo.retail_subscription)}
                      </p>
                    </div>
                  )}
                </div>
                <SubscriptionChart
                  qib={ipo.qib_subscription}
                  nii={ipo.nii_subscription}
                  retail={ipo.retail_subscription}
                />
              </div>
            )}

            {/* Grey Market Premium */}
            {ipo.gmp_amount && (
              <div className="card">
                <h2 className="text-xl font-semibold mb-4">Grey Market Premium (GMP)</h2>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
                  <div>
                    <p className="text-sm text-gray-500 mb-1">GMP Amount</p>
                    <p className="text-lg font-semibold text-gray-900">
                      {formatCurrency(ipo.gmp_amount)}
                    </p>
                  </div>
                  {ipo.gmp_percentage && (
                    <div>
                      <p className="text-sm text-gray-500 mb-1">GMP %</p>
                      <p className={`text-lg font-semibold ${ipo.gmp_percentage > 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatPercentage(ipo.gmp_percentage)}
                      </p>
                    </div>
                  )}
                  {ipo.estimated_listing_price && (
                    <div>
                      <p className="text-sm text-gray-500 mb-1">Est. Listing Price</p>
                      <p className="text-lg font-semibold text-gray-900">
                        {formatCurrency(ipo.estimated_listing_price)}
                      </p>
                    </div>
                  )}
                </div>
                <GMPChart
                  priceBandLower={ipo.price_band_lower}
                  priceBandUpper={ipo.price_band_upper}
                  gmpAmount={ipo.gmp_amount}
                  estimatedListingPrice={ipo.estimated_listing_price}
                />
              </div>
            )}

            {/* Financial Metrics */}
            {(ipo.market_cap_cr || ipo.pe_ratio || ipo.roce || ipo.roe) && (
              <div className="card">
                <h2 className="text-xl font-semibold mb-4">Financial Metrics</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {ipo.market_cap_cr && (
                    <div>
                      <p className="text-sm text-gray-500 mb-1">Market Cap</p>
                      <p className="text-lg font-semibold text-gray-900">
                        {formatCrores(ipo.market_cap_cr)}
                      </p>
                    </div>
                  )}
                  {ipo.pe_ratio && (
                    <div>
                      <p className="text-sm text-gray-500 mb-1">P/E Ratio</p>
                      <p className="text-lg font-semibold text-gray-900">
                        {ipo.pe_ratio.toFixed(2)}
                      </p>
                    </div>
                  )}
                  {ipo.roce && (
                    <div>
                      <p className="text-sm text-gray-500 mb-1">ROCE</p>
                      <p className="text-lg font-semibold text-gray-900">
                        {formatPercentage(ipo.roce)}
                      </p>
                    </div>
                  )}
                  {ipo.roe && (
                    <div>
                      <p className="text-sm text-gray-500 mb-1">ROE</p>
                      <p className="text-lg font-semibold text-gray-900">
                        {formatPercentage(ipo.roe)}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Timeline */}
            <div className="card">
              <h3 className="font-semibold mb-4">Timeline</h3>
              <div className="space-y-3">
                {ipo.open_date && (
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Opens</span>
                    <span className="text-sm font-medium">{formatDate(ipo.open_date)}</span>
                  </div>
                )}
                {ipo.close_date && (
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Closes</span>
                    <span className="text-sm font-medium">{formatDate(ipo.close_date)}</span>
                  </div>
                )}
                {ipo.allotment_date && (
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Allotment</span>
                    <span className="text-sm font-medium">{formatDate(ipo.allotment_date)}</span>
                  </div>
                )}
                {ipo.listing_date && (
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Listing</span>
                    <span className="text-sm font-medium">{formatDate(ipo.listing_date)}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Issue Details */}
            <div className="card">
              <h3 className="font-semibold mb-4">Issue Details</h3>
              <div className="space-y-3">
                {ipo.issue_size_rs_cr && (
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Issue Size</p>
                    <p className="font-medium">{formatCrores(ipo.issue_size_rs_cr)}</p>
                  </div>
                )}
                {ipo.fresh_issue_size && (
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Fresh Issue</p>
                    <p className="font-medium">{formatCrores(ipo.fresh_issue_size)}</p>
                  </div>
                )}
                {ipo.offer_for_sale && (
                  <div>
                    <p className="text-sm text-gray-600 mb-1">OFS</p>
                    <p className="font-medium">{formatCrores(ipo.offer_for_sale)}</p>
                  </div>
                )}
                {ipo.industry_sector && (
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Sector</p>
                    <p className="font-medium">{ipo.industry_sector}</p>
                  </div>
                )}
              </div>
            </div>

            {/* Risk Assessment */}
            {ipo.ml_processed && ipo.risk_score !== null && (
              <div className="card bg-gradient-to-br from-purple-50 to-blue-50 border-2 border-purple-200">
                <div className="flex items-center gap-2 mb-4">
                  <svg className="w-5 h-5 text-purple-600" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
                    <path fillRule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm9.707 5.707a1 1 0 00-1.414-1.414L9 12.586l-1.293-1.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <h3 className="font-semibold">ML Risk Assessment</h3>
                </div>
                <div className="space-y-4">
                  <div>
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm text-gray-700">Risk Score</span>
                      <span className="text-2xl font-bold text-gray-900">
                        {ipo.risk_score.toFixed(1)}/100
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-3">
                      <div
                        className="bg-gradient-to-r from-green-500 via-yellow-500 to-red-500 h-3 rounded-full transition-all"
                        style={{ width: `${ipo.risk_score}%` }}
                      ></div>
                    </div>
                  </div>
                  {ipo.risk_category && (
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-700">Category</span>
                      <span className={`badge text-base ${getRiskColor(ipo.risk_category)}`}>
                        {ipo.risk_category.toUpperCase()} RISK
                      </span>
                    </div>
                  )}
                  {ipo.ml_processed_at && (
                    <p className="text-xs text-gray-500">
                      Analyzed {formatDate(ipo.ml_processed_at, 'dd MMM yyyy, HH:mm')}
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
}
