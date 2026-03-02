import React, { useEffect, useState } from 'react';
import Layout from '@/components/Layout';
import IPOCard from '@/components/IPOCard';
import Loading from '@/components/Loading';
import Error from '@/components/Error';
import { apiService } from '@/services/api';
import { IPO, IPOListResponse, IPOStatus, IPOType } from '@/types/ipo';

export default function AllIPOs() {
  const [data, setData] = useState<IPOListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter states
  const [status, setStatus] = useState<IPOStatus | ''>('');
  const [ipoType, setIPOType] = useState<IPOType | ''>('');
  const [sector, setSector] = useState('');
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [page, setPage] = useState(1);
  const pageSize = 12;

  const fetchIPOs = async () => {
    setLoading(true);
    setError(null);

    try {
      const params: any = {
        page,
        page_size: pageSize,
        sort_by: sortBy,
        sort_order: sortOrder,
      };

      if (status) params.status = status;
      if (ipoType) params.ipo_type = ipoType;
      if (sector) params.industry_sector = sector;
      if (search) params.search = search;

      const result = await apiService.getIPOs(params);
      setData(result);
    } catch (err: any) {
      console.error('Error fetching IPOs:', err);
      setError(err.response?.data?.detail || 'Failed to fetch IPOs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIPOs();
  }, [page, status, ipoType, sector, search, sortBy, sortOrder]);

  const handleFilterChange = () => {
    setPage(1);
  };

  const hasActiveFilters = status || ipoType || sector || search;

  const clearAllFilters = () => {
    setStatus('');
    setIPOType('');
    setSector('');
    setSearch('');
    setPage(1);
  };

  return (
    <Layout title="All IPOs - NexIPO">
      <div className="page-container">
        {/* Header */}
        <div className="page-header">
          <h1>All IPOs</h1>
          <p>{data ? `Showing ${data.items.length} of ${data.total} IPOs` : 'Browse all IPOs'}</p>
        </div>

        {/* Filters */}
        <div className="card mb-6 sm:mb-8">
          <div className="grid grid-cols-1 xs:grid-cols-2 lg:grid-cols-5 gap-3 sm:gap-4">
            {/* Search */}
            <div className="xs:col-span-2 lg:col-span-1">
              <label htmlFor="filter-search" className="label">Search</label>
              <input
                id="filter-search"
                type="text"
                placeholder="Company name or symbol..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  handleFilterChange();
                }}
                className="input"
              />
            </div>

            {/* Status Filter */}
            <div>
              <label htmlFor="filter-status" className="label">Status</label>
              <select
                id="filter-status"
                value={status}
                onChange={(e) => {
                  setStatus(e.target.value as IPOStatus | '');
                  handleFilterChange();
                }}
                className="select"
              >
                <option value="">All Statuses</option>
                <option value="upcoming">Upcoming</option>
                <option value="open">Open</option>
                <option value="closed">Closed</option>
                <option value="listed">Listed</option>
                <option value="withdrawn">Withdrawn</option>
              </select>
            </div>

            {/* Type Filter */}
            <div>
              <label htmlFor="filter-type" className="label">Type</label>
              <select
                id="filter-type"
                value={ipoType}
                onChange={(e) => {
                  setIPOType(e.target.value as IPOType | '');
                  handleFilterChange();
                }}
                className="select"
              >
                <option value="">All Types</option>
                <option value="mainboard">Mainboard</option>
                <option value="sme">SME</option>
              </select>
            </div>

            {/* Sector Filter */}
            <div>
              <label htmlFor="filter-sector" className="label">Sector</label>
              <input
                id="filter-sector"
                type="text"
                placeholder="e.g., Technology"
                value={sector}
                onChange={(e) => {
                  setSector(e.target.value);
                  handleFilterChange();
                }}
                className="input"
              />
            </div>

            {/* Sort */}
            <div>
              <label htmlFor="filter-sort" className="label">Sort By</label>
              <select
                id="filter-sort"
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="select"
              >
                <option value="created_at">Latest</option>
                <option value="company_name">Company Name</option>
                <option value="open_date">Open Date</option>
                <option value="total_subscription">Subscription</option>
                <option value="issue_size_rs_cr">Issue Size</option>
                <option value="risk_score">Risk Score</option>
              </select>
            </div>
          </div>

          {/* Sort Order & Clear Filters */}
          <div className="mt-4 flex flex-wrap items-center gap-2">
            <button
              onClick={() => setSortOrder('asc')}
              className={`px-3 sm:px-4 py-2 rounded-lg text-xs sm:text-sm font-medium transition-colors ${sortOrder === 'asc'
                ? 'bg-primary-600 text-white'
                : 'bg-navy-100 text-navy-700 hover:bg-navy-200'
                }`}
              aria-pressed={sortOrder === 'asc'}
            >
              ↑ Ascending
            </button>
            <button
              onClick={() => setSortOrder('desc')}
              className={`px-3 sm:px-4 py-2 rounded-lg text-xs sm:text-sm font-medium transition-colors ${sortOrder === 'desc'
                ? 'bg-primary-600 text-white'
                : 'bg-navy-100 text-navy-700 hover:bg-navy-200'
                }`}
              aria-pressed={sortOrder === 'desc'}
            >
              ↓ Descending
            </button>

            {hasActiveFilters && (
              <button
                onClick={clearAllFilters}
                className="ml-auto px-3 sm:px-4 py-2 bg-danger-50 text-danger-700 rounded-lg text-xs sm:text-sm font-medium hover:bg-danger-100 transition-colors"
              >
                Clear Filters
              </button>
            )}
          </div>
        </div>

        {/* Content */}
        {loading ? (
          <Loading text="Loading IPOs..." />
        ) : error ? (
          <Error message={error} retry={fetchIPOs} />
        ) : data && data.items.length > 0 ? (
          <>
            {/* IPO Grid */}
            <div className="ipo-grid mb-6 sm:mb-8">
              {data.items.map((ipo) => (
                <IPOCard key={ipo.id} ipo={ipo} />
              ))}
            </div>

            {/* Pagination */}
            {data.total_pages > 1 && (
              <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                <p className="text-sm text-navy-500 order-2 sm:order-1">
                  Page {data.page} of {data.total_pages}
                </p>

                <div className="flex gap-2 order-1 sm:order-2">
                  <button
                    onClick={() => setPage(Math.max(1, page - 1))}
                    disabled={page === 1}
                    className="px-3 sm:px-4 py-2 bg-white border border-navy-200 rounded-lg text-xs sm:text-sm font-medium text-navy-700 hover:bg-navy-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    aria-label="Previous page"
                  >
                    ← Prev
                  </button>

                  {/* Page numbers */}
                  <div className="hidden sm:flex gap-1.5">
                    {Array.from({ length: Math.min(5, data.total_pages) }, (_, i) => {
                      let pageNum;
                      if (data.total_pages <= 5) {
                        pageNum = i + 1;
                      } else if (page <= 3) {
                        pageNum = i + 1;
                      } else if (page >= data.total_pages - 2) {
                        pageNum = data.total_pages - 4 + i;
                      } else {
                        pageNum = page - 2 + i;
                      }
                      return (
                        <button
                          key={pageNum}
                          onClick={() => setPage(pageNum)}
                          className={`w-9 h-9 rounded-lg text-sm font-medium transition-colors ${page === pageNum
                            ? 'bg-primary-600 text-white'
                            : 'bg-white border border-navy-200 text-navy-700 hover:bg-navy-50'
                            }`}
                          aria-label={`Go to page ${pageNum}`}
                          aria-current={page === pageNum ? 'page' : undefined}
                        >
                          {pageNum}
                        </button>
                      );
                    })}
                  </div>

                  {/* Mobile page indicator */}
                  <div className="sm:hidden flex items-center px-3 py-2 bg-white border border-navy-200 rounded-lg text-xs font-medium text-navy-700">
                    {page}/{data.total_pages}
                  </div>

                  <button
                    onClick={() => setPage(Math.min(data.total_pages, page + 1))}
                    disabled={page === data.total_pages}
                    className="px-3 sm:px-4 py-2 bg-white border border-navy-200 rounded-lg text-xs sm:text-sm font-medium text-navy-700 hover:bg-navy-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    aria-label="Next page"
                  >
                    Next →
                  </button>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="empty-state">
            <div className="empty-state-icon">
              <svg className="w-7 h-7 text-navy-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-navy-900 mb-2">No IPOs Found</h3>
            <p className="text-navy-500 text-sm mb-5">Try adjusting your filters</p>
            <button onClick={clearAllFilters} className="btn-primary">
              Clear All Filters
            </button>
          </div>
        )}
      </div>
    </Layout>
  );
}
