import React, { useEffect, useState } from 'react';
import Layout from '@/components/Layout';
import IPOCard from '@/components/IPOCard';
import Loading from '@/components/Loading';
import Error from '@/components/Error';
import { apiService } from '@/services/api';
import { IPO } from '@/types/ipo';

export default function UpcomingIPOs() {
  const [ipos, setIPOs] = useState<IPO[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchIPOs = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await apiService.getUpcomingIPOs(20);
      setIPOs(data);
    } catch (err: any) {
      console.error('Error fetching upcoming IPOs:', err);
      setError(err.response?.data?.detail || 'Failed to fetch upcoming IPOs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIPOs();
  }, []);

  return (
    <Layout title="Upcoming IPOs - IPO Intelligence Platform">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Upcoming IPOs</h1>
          <p className="text-gray-600">
            Opening soon
          </p>
        </div>

        {/* Content */}
        {loading ? (
          <Loading text="Loading upcoming IPOs..." />
        ) : error ? (
          <Error message={error} retry={fetchIPOs} />
        ) : ipos.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {ipos.map((ipo) => (
              <IPOCard key={ipo.id} ipo={ipo} />
            ))}
          </div>
        ) : (
          <div className="card text-center py-12">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Upcoming IPOs</h3>
            <p className="text-gray-600">Check back later for new IPO announcements.</p>
          </div>
        )}
      </div>
    </Layout>
  );
}
