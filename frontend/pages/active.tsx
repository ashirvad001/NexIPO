import React, { useEffect, useState } from 'react';
import Layout from '@/components/Layout';
import IPOCard from '@/components/IPOCard';
import Loading from '@/components/Loading';
import Error from '@/components/Error';
import { apiService } from '@/services/api';
import { IPO } from '@/types/ipo';

export default function ActiveIPOs() {
  const [ipos, setIPOs] = useState<IPO[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchIPOs = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await apiService.getActiveIPOs();
      setIPOs(data);
    } catch (err: any) {
      console.error('Error fetching active IPOs:', err);
      setError(err.response?.data?.detail || 'Failed to fetch active IPOs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchIPOs();
  }, []);

  return (
    <Layout title="Active IPOs - NexIPO">
      <div className="page-container">
        {/* Header */}
        <div className="page-header">
          <h1>Active IPOs</h1>
          <p>Currently open for subscription</p>
        </div>

        {/* Content */}
        {loading ? (
          <Loading text="Loading active IPOs..." />
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
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-navy-900 mb-2">No Active IPOs</h3>
            <p className="text-navy-500 text-sm">There are currently no IPOs open for subscription.</p>
          </div>
        )}
      </div>
    </Layout>
  );
}
