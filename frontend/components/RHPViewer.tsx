import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import { FiDownload, FiSearch, FiFileText, FiRefreshCw, FiAlertCircle } from 'react-icons/fi';

interface RHPViewerProps {
    ipoId: number;
    companyName: string;
    hasProspectusInitially?: boolean;
}

export default function RHPViewer({ ipoId, companyName, hasProspectusInitially = false }: RHPViewerProps) {
    const [hasProspectus, setHasProspectus] = useState(hasProspectusInitially);
    const [isDownloading, setIsDownloading] = useState(false);
    const [isSearching, setIsSearching] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [downloadResult, setDownloadResult] = useState<any>(null);

    // Determine the viewer URL based on NEXT_PUBLIC_API_BASE_URL
    const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';
    const viewerUrl = `${baseUrl}/files/rhp/view/${ipoId}`;

    const handleAutoDownload = async () => {
        setIsDownloading(true);
        setError(null);
        setDownloadResult(null);

        try {
            const res = await apiService.downloadRHP(ipoId);
            if (res && res.status === 'success') {
                setHasProspectus(true);
            }
            setDownloadResult(res);
        } catch (err: any) {
            console.error("Failed to auto download RHP:", err);
            setError(err.response?.data?.detail || err.message || "Failed to download RHP automatically");
        } finally {
            setIsDownloading(false);
        }
    };

    const handleManualSearch = async () => {
        setIsSearching(true);
        try {
            const res = await apiService.searchRHP(companyName);
            if (res && res.search_url) {
                window.open(res.search_url, '_blank');
            }
        } catch (err: any) {
            console.error("Search failed:", err);
        } finally {
            setIsSearching(false);
        }
    };

    if (!hasProspectus) {
        return (
            <div className="bg-white/60 backdrop-blur-xl border border-gray-200 rounded-2xl p-6 mb-6 mt-6 shadow-sm">
                <h3 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
                    <FiFileText className="mr-2 text-indigo-600" />
                    Red Herring Prospectus (RHP)
                </h3>

                <div className="flex flex-col items-center justify-center py-10 text-center border-2 border-dashed border-gray-300 rounded-xl bg-gray-50/80">
                    <FiFileText className="text-5xl text-gray-400 mb-4" />
                    <h4 className="text-lg font-medium text-gray-900 mb-2">No RHP Document Available</h4>
                    <p className="text-gray-600 max-w-md mx-auto mb-6">
                        The Red Herring Prospectus for {companyName} hasn't been downloaded to our system yet.
                    </p>

                    <div className="flex flex-wrap items-center justify-center gap-4">
                        <button
                            onClick={handleAutoDownload}
                            disabled={isDownloading}
                            className="px-6 py-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-medium rounded-lg transition-colors flex items-center justify-center shadow-lg shadow-indigo-500/30"
                        >
                            {isDownloading ? (
                                <><FiRefreshCw className="mr-2 animate-spin" /> Downloading...</>
                            ) : (
                                <><FiDownload className="mr-2" /> Auto-Fetch Standard RHP</>
                            )}
                        </button>

                        <a
                            href={`/ipo/${ipoId}/upload`}
                            className="px-6 py-2.5 bg-teal-600 hover:bg-teal-700 text-white font-medium rounded-lg transition-colors flex items-center justify-center border border-teal-500/30 shadow-lg shadow-teal-500/20"
                        >
                            <FiFileText className="mr-2" /> Upload RHP Manually
                        </a>

                        <button
                            onClick={handleManualSearch}
                            disabled={isSearching}
                            className="px-6 py-2.5 bg-gray-700 hover:bg-gray-800 disabled:bg-gray-400 text-white font-medium rounded-lg transition-colors flex items-center justify-center border border-gray-600"
                        >
                            <FiSearch className="mr-2" /> Search Web Manually
                        </button>
                    </div>

                    {(error || (downloadResult && downloadResult.status === 'failed')) && (
                        <div className="mt-6 flex items-start text-amber-800 bg-amber-100 border border-amber-200 px-4 py-3 rounded-lg text-sm w-full max-w-md text-left">
                            <FiAlertCircle className="shrink-0 mr-3 mt-0.5 text-amber-600" />
                            <div>
                                <span className="font-semibold block mb-1 text-amber-900">RHP Fetch Status</span>
                                {error ? (
                                    <span className="text-amber-800">{error}</span>
                                ) : (
                                    <span className="text-amber-800">{downloadResult.error || "The prospectus could not be found automatically. Please try uploading it manually."}</span>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        );
    }

    // If we have the prospectus, show the viewer inline
    return (
        <div className="bg-white/60 backdrop-blur-xl border border-gray-200 rounded-2xl p-6 mb-6 mt-6 shadow-sm">
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-xl font-semibold text-gray-900 flex items-center">
                    <FiFileText className="mr-2 text-indigo-600" />
                    Red Herring Prospectus Preview
                </h3>
                <a
                    href={viewerUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm px-4 py-2 bg-indigo-100 hover:bg-indigo-200 text-indigo-700 rounded-lg flex items-center transition-colors border border-indigo-200"
                    title="Open PDF in new tab"
                >
                    <FiDownload className="mr-2" /> Download File
                </a>
            </div>

            <div className="w-full h-[600px] rounded-xl overflow-hidden border border-gray-300 bg-gray-100 shadow-inner">
                <iframe
                    src={viewerUrl}
                    className="w-full h-full border-none"
                    title={`${companyName} RHP Prospectus`}
                />
            </div>

            {downloadResult && downloadResult.pages && (
                <div className="mt-4 flex gap-4 text-sm text-gray-500 justify-end">
                    <span>Pages: {downloadResult.pages}</span>
                    {downloadResult.size_mb > 0 && <span>Size: {downloadResult.size_mb} MB</span>}
                </div>
            )}
        </div>
    );
}
