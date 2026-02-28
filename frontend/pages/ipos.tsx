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
    setPage(1); // Reset to first page when filters change
  };

  return (
    <Layout title="All IPOs - NexIPO">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-navy-900 mb-2">All IPOs</h1>
          <p className="text-gray-600">
            {data ? `Showing ${data.items.length} of ${data.total} IPOs` : 'Browse all IPOs'}
          </p>
        </div>

        {/* Filters */}
        <div className="card mb-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {/* Search */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Search
              </label>
              <input
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
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Status
              </label>
              <select
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
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Type
              </label>
              <select
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
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Sector
              </label>
              <input
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
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Sort By
              </label>
              <select
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

          {/* Sort Order Toggle */}
          <div className="mt-4 flex gap-2">
            <button
              onClick={() => setSortOrder('asc')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${sortOrder === 'asc'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
            >
              Ascending
            </button>
            <button
              onClick={() => setSortOrder('desc')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${sortOrder === 'desc'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
            >
              Descending
            </button>

            {/* Clear Filters */}
            {(status || ipoType || sector || search) && (
              <button
                onClick={() => {
                  setStatus('');
                  setIPOType('');
                  setSector('');
                  setSearch('');
                  setPage(1);
                }}
                className="ml-auto px-4 py-2 bg-red-100 text-red-700 rounded-lg text-sm font-medium hover:bg-red-200 transition-colors"
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
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
              {data.items.map((ipo) => (
                <IPOCard key={ipo.id} ipo={ipo} />
              ))}
            </div>

            {/* Pagination */}
            {data.total_pages > 1 && (
              <div className="flex items-center justify-between">
                <p className="text-sm text-gray-600">
                  Page {data.page} of {data.total_pages}
                </p>

                <div className="flex gap-2">
                  <button
                    onClick={() => setPage(Math.max(1, page - 1))}
                    disabled={page === 1}
                    className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>

                  {/* Page numbers */}
                  <div className="hidden md:flex gap-2">
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
                          className={`px-4 py-2 rounded-lg text-sm font-medium ${page === pageNum
                            ? 'bg-primary-600 text-white'
                            : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                            }`}
                        >
                          {pageNum}
                        </button>
                      );
                    })}
                  </div>

                  <button
                    onClick={() => setPage(Math.min(data.total_pages, page + 1))}
                    disabled={page === data.total_pages}
                    className="px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="card text-center py-12">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-navy-900 mb-2">No IPOs Found</h3>
            <p className="text-gray-600 mb-4">Try adjusting your filters</p>
            <button
              onClick={() => {
                setStatus('');
                setIPOType('');
                setSector('');
                setSearch('');
                setPage(1);
              }}
              className="btn-primary"
            >
              Clear All Filters
            </button>
          </div>
        )}
      </div>
    </Layout>
  );
}
