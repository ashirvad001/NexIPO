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
        <div className="page-container">
          <Error message={error} retry={fetchData} />
        </div>
      </Layout>
    );
  }

  return (
    <Layout title="Dashboard - NexIPO">
      <div className="page-container">
        {/* Hero Section */}
        <div className="bg-gradient-to-br from-navy-800 via-navy-900 to-navy-950 rounded-xl sm:rounded-2xl p-5 sm:p-8 mb-6 sm:mb-8 text-white relative overflow-hidden">
          {/* Decorative element */}
          <div className="absolute top-0 right-0 w-48 h-48 sm:w-64 sm:h-64 bg-primary-500/10 rounded-full -translate-y-1/2 translate-x-1/4 blur-2xl" aria-hidden="true" />
          <div className="relative">
            <h1 className="text-2xl sm:text-3xl font-bold mb-2 sm:mb-3">
              Welcome to NexIPO
            </h1>
            <p className="text-navy-300 text-sm sm:text-lg max-w-2xl leading-relaxed">
              ML-powered analysis and risk assessment for Initial Public Offerings.
              Make informed investment decisions with data-driven insights.
            </p>
            <div className="mt-5 sm:mt-6 flex flex-wrap gap-3 sm:gap-4">
              <div className="bg-white/10 backdrop-blur-sm rounded-lg sm:rounded-xl px-4 sm:px-6 py-2.5 sm:py-3 border border-white/10">
                <p className="text-xl sm:text-2xl font-bold">{activeIPOs.length}</p>
                <p className="text-xs sm:text-sm text-navy-300">Active IPOs</p>
              </div>
              <div className="bg-white/10 backdrop-blur-sm rounded-lg sm:rounded-xl px-4 sm:px-6 py-2.5 sm:py-3 border border-white/10">
                <p className="text-xl sm:text-2xl font-bold">{upcomingIPOs.length}</p>
                <p className="text-xs sm:text-sm text-navy-300">Upcoming</p>
              </div>
            </div>
          </div>
        </div>

        {/* Active IPOs Section */}
        <section className="mb-8 sm:mb-12" aria-labelledby="active-heading">
          <div className="flex items-center justify-between mb-4 sm:mb-6">
            <div>
              <h2 id="active-heading" className="text-xl sm:text-2xl font-bold text-navy-900">Active IPOs</h2>
              <p className="text-navy-500 text-sm mt-0.5">Currently open for subscription</p>
            </div>
            {activeIPOs.length > 0 && (
              <a href="/active" className="text-primary-600 hover:text-primary-700 font-medium text-sm whitespace-nowrap">
                View all →
              </a>
            )}
          </div>

          {activeIPOs.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">
                <svg className="w-7 h-7 text-navy-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-navy-900 mb-2">No Active IPOs</h3>
              <p className="text-navy-500 text-sm">There are currently no IPOs open for subscription.</p>
            </div>
          ) : (
            <div className="ipo-grid">
              {activeIPOs.map((ipo) => (
                <IPOCard key={ipo.id} ipo={ipo} />
              ))}
            </div>
          )}
        </section>

        {/* Upcoming IPOs Section */}
        <section aria-labelledby="upcoming-heading">
          <div className="flex items-center justify-between mb-4 sm:mb-6">
            <div>
              <h2 id="upcoming-heading" className="text-xl sm:text-2xl font-bold text-navy-900">Upcoming IPOs</h2>
              <p className="text-navy-500 text-sm mt-0.5">Opening soon</p>
            </div>
            {upcomingIPOs.length > 0 && (
              <a href="/upcoming" className="text-primary-600 hover:text-primary-700 font-medium text-sm whitespace-nowrap">
                View all →
              </a>
            )}
          </div>

          {upcomingIPOs.length === 0 ? (
            <div className="empty-state">
              <div className="empty-state-icon">
                <svg className="w-7 h-7 text-navy-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-navy-900 mb-2">No Upcoming IPOs</h3>
              <p className="text-navy-500 text-sm">Check back later for new IPO announcements.</p>
            </div>
          ) : (
            <div className="ipo-grid">
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
