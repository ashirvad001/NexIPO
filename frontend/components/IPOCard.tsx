// components/IPOCard.tsx
import React from 'react';
import Link from 'next/link';
import { IPO } from '@/types/ipo';
import {
  formatCrores,
  formatPercentage,
  formatSubscription,
  formatDate,
  getStatusColor,
  getRiskColor,
  getDaysUntil,
} from '@/utils/formatters';

interface IPOCardProps {
  ipo: IPO;
}

const IPOCard: React.FC<IPOCardProps> = ({ ipo }) => {
  const daysUntilOpen = getDaysUntil(ipo.open_date);
  const daysUntilClose = getDaysUntil(ipo.close_date);

  return (
    <Link href={`/ipo/${ipo.id}`}>
      <div className="card hover:scale-[1.02] transition-transform cursor-pointer">
        {/* Header */}
        <div className="flex justify-between items-start mb-4">
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 mb-1">
              {ipo.company_name}
            </h3>
            {ipo.symbol && (
              <p className="text-sm text-gray-600 font-mono">
                {ipo.symbol}
              </p>
            )}
          </div>
          <span className={`badge ${getStatusColor(ipo.status)}`}>
            {ipo.status.toUpperCase()}
          </span>
        </div>

        {/* Industry & Type */}
        <div className="flex gap-2 mb-4">
          {ipo.industry_sector && (
            <span className="badge bg-gray-100 text-gray-700">
              {ipo.industry_sector}
            </span>
          )}
          <span className="badge bg-blue-100 text-blue-700">
            {ipo.ipo_type === 'mainboard' ? 'Mainboard' : 'SME'}
          </span>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          {/* Price Band */}
          {ipo.price_band_lower && ipo.price_band_upper && (
            <div>
              <p className="text-xs text-gray-500 mb-1">Price Band</p>
              <p className="text-sm font-semibold text-gray-900">
                ₹{ipo.price_band_lower} - ₹{ipo.price_band_upper}
              </p>
            </div>
          )}

          {/* Issue Size */}
          {ipo.issue_size_rs_cr && (
            <div>
              <p className="text-xs text-gray-500 mb-1">Issue Size</p>
              <p className="text-sm font-semibold text-gray-900">
                {formatCrores(ipo.issue_size_rs_cr)}
              </p>
            </div>
          )}

          {/* Subscription */}
          {ipo.total_subscription && (
            <div>
              <p className="text-xs text-gray-500 mb-1">Subscription</p>
              <p className="text-sm font-semibold text-green-600">
                {formatSubscription(ipo.total_subscription)}
              </p>
            </div>
          )}

          {/* GMP */}
          {ipo.gmp_percentage && (
            <div>
              <p className="text-xs text-gray-500 mb-1">GMP</p>
              <p className={`text-sm font-semibold ${
                ipo.gmp_percentage > 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {formatPercentage(ipo.gmp_percentage)}
              </p>
            </div>
          )}
        </div>

        {/* Dates */}
        <div className="border-t border-gray-200 pt-4 mb-4">
          {ipo.status === 'open' && daysUntilClose !== null && (
            <div className="flex items-center text-sm">
              <svg className="w-4 h-4 mr-2 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
              </svg>
              <span className="text-gray-700">
                Closes in <span className="font-semibold">{daysUntilClose} days</span>
              </span>
            </div>
          )}

          {ipo.status === 'upcoming' && daysUntilOpen !== null && daysUntilOpen > 0 && (
            <div className="flex items-center text-sm">
              <svg className="w-4 h-4 mr-2 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
              </svg>
              <span className="text-gray-700">
                Opens in <span className="font-semibold">{daysUntilOpen} days</span>
              </span>
            </div>
          )}

          {ipo.open_date && ipo.close_date && (
            <div className="text-xs text-gray-500 mt-2">
              {formatDate(ipo.open_date, 'dd MMM')} - {formatDate(ipo.close_date, 'dd MMM yyyy')}
            </div>
          )}
        </div>

        {/* Risk Assessment */}
        {ipo.ml_processed && ipo.risk_score !== null && (
          <div className="border-t border-gray-200 pt-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <svg className="w-4 h-4 mr-2 text-purple-500" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
                  <path fillRule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm9.707 5.707a1 1 0 00-1.414-1.414L9 12.586l-1.293-1.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span className="text-xs text-gray-600">Risk Score</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="text-right">
                  <p className="text-sm font-semibold text-gray-900">
                    {ipo.risk_score.toFixed(1)}/100
                  </p>
                </div>
                {ipo.risk_category && (
                  <span className={`badge ${getRiskColor(ipo.risk_category)}`}>
                    {ipo.risk_category.toUpperCase()}
                  </span>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Listing Gain (for listed IPOs) */}
        {ipo.status === 'listed' && ipo.listing_gain_percentage !== null && (
          <div className="border-t border-gray-200 pt-4 mt-4">
            <div className="flex items-center justify-between">
              <span className="text-xs text-gray-600">Listing Gain</span>
              <span className={`text-sm font-semibold ${
                ipo.listing_gain_percentage > 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {formatPercentage(ipo.listing_gain_percentage)}
              </span>
            </div>
          </div>
        )}
      </div>
    </Link>
  );
};

export default IPOCard;
