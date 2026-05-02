import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Layout from '@/components/Layout';
import FileUpload from '@/components/FileUpload';
import ProspectusViewer from '@/components/ProspectusViewer';
import Loading from '@/components/Loading';
import Error from '@/components/Error';
import { apiService } from '@/services/api';
import { IPO } from '@/types/ipo';

export default function UploadProspectus() {
  const router = useRouter();
  const { id } = router.query;
  const [ipo, setIPO] = useState<IPO | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const [hasProspectus, setHasProspectus] = useState(false);

  const fetchIPO = async () => {
    if (!id) return;

    setLoading(true);
    setError(null);

    try {
      const data = await apiService.getIPOById(Number(id));
      setIPO(data);
      setHasProspectus(!!data.prospectus_file_id);
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

  const handleUploadSuccess = async (result: any) => {
    setUploadSuccess(true);
    setUploadError(null);
    setHasProspectus(true);
    fetchIPO();
    
    // Automatically process ML risk analysis
    try {
      await apiService.predictRisk(Number(id));
    } catch (err) {
      console.error('Auto ML risk analysis failed:', err);
    }

    setTimeout(() => setUploadSuccess(false), 5000);
  };

  const handleUploadError = (errorMessage: string) => {
    setUploadError(errorMessage);
    setUploadSuccess(false);
  };

  const handleDeleteProspectus = async () => {
    if (!id || !confirm('Are you sure you want to delete this prospectus?')) {
      return;
    }

    try {
      await apiService.deleteProspectus(Number(id));
      setHasProspectus(false);
      fetchIPO();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete prospectus');
    }
  };

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
        <div className="page-container">
          <Error message={error || 'IPO not found'} retry={fetchIPO} />
        </div>
      </Layout>
    );
  }

  return (
    <Layout title={`Upload Prospectus - ${ipo.company_name}`}>
      <div className="page-container">
        <div className="mb-6 sm:mb-8">
          <button
            onClick={() => router.push(`/ipo/${id}`)}
            className="text-primary-600 hover:text-primary-700 mb-4 flex items-center gap-1.5 text-sm transition-colors"
            aria-label="Back to IPO details"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to IPO Details
          </button>

          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
            <div>
              <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold text-navy-900 mb-1">
                Prospectus Management
              </h1>
              <p className="text-sm sm:text-base text-navy-500">{ipo.company_name}</p>
            </div>

            {hasProspectus && (
              <button
                onClick={handleDeleteProspectus}
                className="btn-danger flex items-center gap-2 flex-shrink-0"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Delete Prospectus
              </button>
            )}
          </div>
        </div>

        {uploadSuccess && (
          <div className="alert-success mb-4 sm:mb-6 flex items-center gap-2" role="status">
            <svg className="w-5 h-5 text-success-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <p>Prospectus uploaded and processed successfully!</p>
          </div>
        )}

        {uploadError && (
          <div className="alert-error mb-4 sm:mb-6 flex items-center gap-2" role="alert">
            <svg className="w-5 h-5 text-danger-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <p>{uploadError}</p>
          </div>
        )}

        {!hasProspectus ? (
          <div className="card max-w-2xl mx-auto p-5 sm:p-8">
            <h2 className="text-lg sm:text-xl font-semibold text-navy-900 mb-5 sm:mb-6">
              Upload Prospectus
            </h2>
            <FileUpload
              ipoId={Number(id)}
              onUploadSuccess={handleUploadSuccess}
              onUploadError={handleUploadError}
            />
            <div className="mt-5 sm:mt-6 p-3 sm:p-4 bg-accent-50 rounded-lg border border-accent-200">
              <h3 className="text-xs sm:text-sm font-medium text-navy-900 mb-2">
                What happens after upload?
              </h3>
              <ul className="text-xs sm:text-sm text-navy-600 space-y-1">
                <li>• PDF file is validated and saved securely</li>
                <li>• Text is extracted from all pages</li>
                <li>• Key sections are automatically identified</li>
                <li>• Data is stored for ML risk analysis</li>
                <li>• Processing typically takes 10-30 seconds</li>
              </ul>
            </div>
          </div>
        ) : (
          <div>
            <div className="alert-success mb-4 sm:mb-6 flex items-center gap-2" role="status">
              <svg className="w-5 h-5 text-success-600 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <p>Prospectus available and processed</p>
            </div>

            <ProspectusViewer ipoId={Number(id)} companyName={ipo.company_name} />
          </div>
        )}
      </div>
    </Layout>
  );
}
