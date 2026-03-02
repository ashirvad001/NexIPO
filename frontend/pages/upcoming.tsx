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
    <Layout title="Upcoming IPOs - NexIPO">
      <div className="page-container">
        {/* Header */}
        <div className="page-header">
          <h1>Upcoming IPOs</h1>
          <p>Opening soon</p>
        </div>

        {/* Content */}
        {loading ? (
          <Loading text="Loading upcoming IPOs..." />
        ) : error ? (
          <Error message={error} retry={fetchIPOs} />
        ) : ipos.length > 0 ? (
          <div className="ipo-grid">
            {ipos.map((ipo) => (
              <IPOCard key={ipo.id} ipo={ipo} />
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <div className="empty-state-icon">
              <svg className="w-7 h-7 text-navy-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-navy-900 mb-2">No Upcoming IPOs</h3>
            <p className="text-navy-500 text-sm">Check back later for new IPO announcements.</p>
          </div>
        )}
      </div>
    </Layout>
  );
}
