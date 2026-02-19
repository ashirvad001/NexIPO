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

  const handleUploadSuccess = (result: any) => {
    setUploadSuccess(true);
    setUploadError(null);
    setHasProspectus(true);
    fetchIPO();
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
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <Error message={error || 'IPO not found'} retry={fetchIPO} />
        </div>
      </Layout>
    );
  }

  return (
    <Layout title={`Upload Prospectus - ${ipo.company_name}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <button
            onClick={() => router.push(`/ipo/${id}`)}
            className="text-primary-600 hover:text-primary-700 mb-4 flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Back to IPO Details
          </button>

          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Prospectus Management
              </h1>
              <p className="text-lg text-gray-600">{ipo.company_name}</p>
            </div>
            
            {hasProspectus && (
              <button
                onClick={handleDeleteProspectus}
                className="btn-danger flex items-center gap-2"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
                Delete Prospectus
              </button>
            )}
          </div>
        </div>

        {uploadSuccess && (
          <div className="mb-6 bg-green-50 border border-green-200 rounded-lg p-4">
            <div className="flex items-center">
              <svg className="w-5 h-5 text-green-600 mr-3" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <p className="text-sm font-medium text-green-800">
                Prospectus uploaded and processed successfully!
              </p>
            </div>
          </div>
        )}

        {uploadError && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center">
              <svg className="w-5 h-5 text-red-600 mr-3" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
              <p className="text-sm font-medium text-red-800">{uploadError}</p>
            </div>
          </div>
        )}

        {!hasProspectus ? (
          <div className="card max-w-2xl mx-auto">
            <h2 className="text-xl font-semibold text-gray-900 mb-6">
              Upload Prospectus
            </h2>
            <FileUpload
              ipoId={Number(id)}
              onUploadSuccess={handleUploadSuccess}
              onUploadError={handleUploadError}
            />
            <div className="mt-6 p-4 bg-blue-50 rounded-lg">
              <h3 className="text-sm font-medium text-blue-900 mb-2">
                What happens after upload?
              </h3>
              <ul className="text-sm text-blue-700 space-y-1">
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
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <svg className="w-5 h-5 text-green-600 mr-3" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  <p className="text-sm font-medium text-green-800">
                    Prospectus available and processed
                  </p>
                </div>
              </div>
            </div>
            
            <ProspectusViewer ipoId={Number(id)} companyName={ipo.company_name} />
          </div>
        )}
      </div>
    </Layout>
  );
}
