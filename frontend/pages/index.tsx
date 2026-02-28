import React, { useEffect, useState } from 'react';
import Layout from '@/components/Layout';
import IPOCard from '@/components/IPOCard';
import Loading from '@/components/Loading';
import Error from '@/components/Error';
import { apiService } from '@/services/api';
import { IPO } from '@/types/ipo';

export default function Home() {
  const [activeIPOs, setActiveIPOs] = useState<IPO[]>([]);
  const [upcomingIPOs, setUpcomingIPOs] = useState<IPO[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    setError(null);

    try {
      const [active, upcoming] = await Promise.all([
        apiService.getActiveIPOs(),
        apiService.getUpcomingIPOs(6),
      ]);

      setActiveIPOs(active);
      setUpcomingIPOs(upcoming);
    } catch (err: any) {
      console.error('Error fetching data:', err);
      setError(err.response?.data?.detail || 'Failed to fetch IPO data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) {
    return (
      <Layout>
        <Loading fullScreen text="Loading dashboard..." />
      </Layout>
    );
  }

  if (error) {
    return (
      <Layout>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <Error message={error} retry={fetchData} />
        </div>
      </Layout>
    );
  }

  return (
    <Layout title="Dashboard - NexIPO">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero Section */}
        <div className="bg-gradient-to-r from-navy-800 to-navy-900 rounded-2xl p-8 mb-8 text-white">
          <h1 className="text-3xl font-bold mb-3">
            Welcome to NexIPO
          </h1>
          <p className="text-navy-300 text-lg max-w-2xl">
            ML-powered analysis and risk assessment for Initial Public Offerings.
            Make informed investment decisions with data-driven insights.
          </p>
          <div className="mt-6 flex gap-4">
            <div className="bg-white/10 backdrop-blur-sm rounded-xl px-6 py-3 border border-white/10">
              <p className="text-2xl font-bold">{activeIPOs.length}</p>
              <p className="text-sm text-navy-300">Active IPOs</p>
            </div>
            <div className="bg-white/10 backdrop-blur-sm rounded-xl px-6 py-3 border border-white/10">
              <p className="text-2xl font-bold">{upcomingIPOs.length}</p>
              <p className="text-sm text-navy-300">Upcoming</p>
            </div>
          </div>
        </div>

        {/* Active IPOs Section */}
        <section className="mb-12">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold text-navy-900">Active IPOs</h2>
              <p className="text-navy-500 mt-1">Currently open for subscription</p>
            </div>
            {activeIPOs.length > 0 && (
              <a href="/active" className="text-primary-600 hover:text-primary-700 font-medium text-sm">
                View all →
              </a>
            )}
          </div>

          {activeIPOs.length === 0 ? (
            <div className="card text-center py-12">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No Active IPOs</h3>
              <p className="text-gray-600">There are currently no IPOs open for subscription.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {activeIPOs.map((ipo) => (
                <IPOCard key={ipo.id} ipo={ipo} />
              ))}
            </div>
          )}
        </section>

        {/* Upcoming IPOs Section */}
        <section>
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-2xl font-bold text-navy-900">Upcoming IPOs</h2>
              <p className="text-navy-500 mt-1">Opening soon</p>
            </div>
            {upcomingIPOs.length > 0 && (
              <a href="/upcoming" className="text-primary-600 hover:text-primary-700 font-medium text-sm">
                View all →
              </a>
            )}
          </div>

          {upcomingIPOs.length === 0 ? (
            <div className="card text-center py-12">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No Upcoming IPOs</h3>
              <p className="text-gray-600">Check back later for new IPO announcements.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {upcomingIPOs.map((ipo) => (
                <IPOCard key={ipo.id} ipo={ipo} />
              ))}
            </div>
          )}
        </section>
      </div>
    </Layout>
  );
}
