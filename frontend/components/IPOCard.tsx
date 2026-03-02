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
    <Link href={`/ipo/${ipo.id}`} className="block group" aria-label={`View details for ${ipo.company_name}`}>
      <div className="card hover:scale-[1.02] transition-all duration-200 h-full flex flex-col">
        {/* Header */}
        <div className="flex justify-between items-start gap-3 mb-3">
          <div className="min-w-0 flex-1">
            <h3 className="text-base sm:text-lg font-semibold text-navy-900 mb-0.5 line-clamp-2 group-hover:text-primary-600 transition-colors">
              {ipo.company_name}
            </h3>
            {ipo.symbol && (
              <p className="text-xs sm:text-sm text-navy-500 font-mono truncate">
                {ipo.symbol}
              </p>
            )}
          </div>
          <span className={`badge flex-shrink-0 ${getStatusColor(ipo.status)}`}>
            {ipo.status.toUpperCase()}
          </span>
        </div>

        {/* Industry & Type */}
        <div className="flex flex-wrap gap-1.5 mb-3">
          {ipo.industry_sector && (
            <span className="badge bg-navy-100 text-navy-700 text-2xs sm:text-xs">
              {ipo.industry_sector}
            </span>
          )}
          <span className="badge bg-accent-100 text-accent-700 text-2xs sm:text-xs">
            {ipo.ipo_type === 'mainboard' ? 'Mainboard' : 'SME'}
          </span>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-2 gap-x-4 gap-y-2 mb-3 flex-1">
          {ipo.price_band_lower && ipo.price_band_upper && (
            <div>
              <p className="text-2xs sm:text-xs text-navy-400 mb-0.5">Price Band</p>
              <p className="text-xs sm:text-sm font-semibold text-navy-900">
                ₹{ipo.price_band_lower} - ₹{ipo.price_band_upper}
              </p>
            </div>
          )}
          {ipo.issue_size_rs_cr && (
            <div>
              <p className="text-2xs sm:text-xs text-navy-400 mb-0.5">Issue Size</p>
              <p className="text-xs sm:text-sm font-semibold text-navy-900">
                {formatCrores(ipo.issue_size_rs_cr)}
              </p>
            </div>
          )}
          {ipo.total_subscription && (
            <div>
              <p className="text-2xs sm:text-xs text-navy-400 mb-0.5">Subscription</p>
              <p className="text-xs sm:text-sm font-semibold text-success-600">
                {formatSubscription(ipo.total_subscription)}
              </p>
            </div>
          )}
          {ipo.gmp_percentage && (
            <div>
              <p className="text-2xs sm:text-xs text-navy-400 mb-0.5">GMP</p>
              <p className={`text-xs sm:text-sm font-semibold ${ipo.gmp_percentage > 0 ? 'text-success-600' : 'text-danger-600'}`}>
                {formatPercentage(ipo.gmp_percentage)}
              </p>
            </div>
          )}
        </div>

        {/* Dates */}
        <div className="border-t border-navy-100 pt-3 mb-3 mt-auto">
          {ipo.status === 'open' && daysUntilClose !== null && (
            <div className="flex items-center text-xs sm:text-sm">
              <svg className="w-3.5 h-3.5 sm:w-4 sm:h-4 mr-1.5 text-success-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
              </svg>
              <span className="text-navy-700">
                Closes in <span className="font-semibold">{daysUntilClose} days</span>
              </span>
            </div>
          )}
          {ipo.status === 'upcoming' && daysUntilOpen !== null && daysUntilOpen > 0 && (
            <div className="flex items-center text-xs sm:text-sm">
              <svg className="w-3.5 h-3.5 sm:w-4 sm:h-4 mr-1.5 text-accent-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
              </svg>
              <span className="text-navy-700">
                Opens in <span className="font-semibold">{daysUntilOpen} days</span>
              </span>
            </div>
          )}
          {ipo.open_date && ipo.close_date && (
            <div className="text-2xs sm:text-xs text-navy-400 mt-1.5">
              {formatDate(ipo.open_date, 'dd MMM')} - {formatDate(ipo.close_date, 'dd MMM yyyy')}
            </div>
          )}
        </div>

        {/* Risk Assessment */}
        {ipo.ml_processed && ipo.risk_score !== null && (
          <div className="border-t border-navy-100 pt-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <svg className="w-3.5 h-3.5 text-purple-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                  <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z" />
                  <path fillRule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm9.707 5.707a1 1 0 00-1.414-1.414L9 12.586l-1.293-1.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span className="text-2xs sm:text-xs text-navy-500">Risk Score</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs sm:text-sm font-semibold text-navy-900">
                  {ipo.risk_score.toFixed(1)}/100
                </span>
                {ipo.risk_category && (
                  <span className={`badge text-2xs ${getRiskColor(ipo.risk_category)}`}>
                    {ipo.risk_category.toUpperCase()}
                  </span>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Listing Gain (for listed IPOs) */}
        {ipo.status === 'listed' && ipo.listing_gain_percentage !== null && (
          <div className="border-t border-navy-100 pt-3 mt-3">
            <div className="flex items-center justify-between">
              <span className="text-2xs sm:text-xs text-navy-500">Listing Gain</span>
              <span className={`text-xs sm:text-sm font-semibold ${ipo.listing_gain_percentage > 0 ? 'text-success-600' : 'text-danger-600'}`}>
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
