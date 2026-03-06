import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { apiService } from '@/services/api';
import Loading from './Loading';

interface BulkImportProps {
    onSuccess: () => void;
    onClose: () => void;
}

export default function BulkImport({ onSuccess, onClose }: BulkImportProps) {
    const [file, setFile] = useState<File | null>(null);
    const [loading, setLoading] = useState(false);
    const [report, setReport] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);

    const onDrop = useCallback((acceptedFiles: File[]) => {
        if (acceptedFiles.length > 0) {
            setFile(acceptedFiles[0]);
            setError(null);
            setReport(null);
        }
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'text/csv': ['.csv'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
            'application/vnd.ms-excel': ['.xls'],
        },
        multiple: false,
    });

    const handleImport = async () => {
        if (!file) return;

        setLoading(true);
        setError(null);
        try {
            const result = await apiService.bulkImportIPOs(file);
            setReport(result.report);
            if (result.status === 'success' || result.status === 'partial_success') {
                onSuccess();
            }
        } catch (err: any) {
            console.error('Import error:', err);
            setError(err.response?.data?.detail || 'An error occurred during import');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="card max-w-2xl mx-auto">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold text-navy-900">Bulk Import IPOs</h2>
                <button onClick={onClose} className="text-navy-400 hover:text-navy-600">
                    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>
            </div>

            {!report ? (
                <div className="space-y-6">
                    <div
                        {...getRootProps()}
                        className={`cursor-pointer border-2 border-dashed rounded-xl p-10 text-center transition-colors ${isDragActive ? 'border-primary-500 bg-primary-50' : 'border-navy-200 hover:border-primary-400 hover:bg-navy-50'
                            }`}
                    >
                        <input {...getInputProps()} />
                        <div className="mb-4">
                            <svg className="mx-auto h-12 w-12 text-navy-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                            </svg>
                        </div>
                        <p className="text-navy-700 font-medium">
                            {file ? file.name : isDragActive ? 'Drop file here' : 'Click or drag CSV/Excel file to upload'}
                        </p>
                        <p className="mt-1 text-xs text-navy-500">Supports .csv, .xlsx, .xls</p>
                    </div>

                    {error && (
                        <div className="p-3 bg-danger-50 text-danger-700 text-sm rounded-lg border border-danger-100 italic">
                            {error}
                        </div>
                    )}

                    <div className="flex gap-3 justify-end">
                        <button onClick={onClose} className="btn-secondary" disabled={loading}>
                            Cancel
                        </button>
                        <button
                            onClick={handleImport}
                            className="btn-primary"
                            disabled={!file || loading}
                        >
                            {loading ? 'Importing...' : 'Start Import'}
                        </button>
                    </div>
                </div>
            ) : (
                <div className="space-y-4">
                    <div className={`p-4 rounded-lg border ${report.failed === 0 ? 'bg-success-50 border-success-200 text-success-800' : 'bg-warning-50 border-warning-200 text-warning-800'}`}>
                        <p className="font-semibold">Import Summary</p>
                        <p className="text-sm">Processed: {report.total_rows} | Success: {report.success} | Failed: {report.failed}</p>
                    </div>

                    {report.errors && report.errors.length > 0 && (
                        <div className="space-y-2">
                            <p className="text-sm font-semibold text-navy-900">Errors Details:</p>
                            <div className="max-h-60 overflow-y-auto border border-navy-100 rounded-lg">
                                <table className="min-w-full text-xs text-left">
                                    <thead className="bg-navy-50 text-navy-700 uppercase">
                                        <tr>
                                            <th className="px-3 py-2">Row</th>
                                            <th className="px-3 py-2">Company</th>
                                            <th className="px-3 py-2">Error</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-navy-50">
                                        {report.errors.map((err: any, idx: number) => (
                                            <tr key={idx} className="hover:bg-navy-50">
                                                <td className="px-3 py-2 tabular-nums">{err.row}</td>
                                                <td className="px-3 py-2 font-medium">{err.company}</td>
                                                <td className="px-3 py-2 text-danger-600">{err.error}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}

                    <div className="flex justify-end pt-4">
                        <button onClick={onClose} className="btn-primary">
                            Done
                        </button>
                    </div>
                </div>
            )}
            {loading && <Loading text="Processing import..." />}
        </div>
    );
}
