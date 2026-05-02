import React, { useState, useRef } from 'react';
import { apiService } from '@/services/api';

interface FileUploadProps {
  ipoId: number;
  onUploadSuccess?: (result: any) => void;
  onUploadError?: (error: string) => void;
}

const FileUpload: React.FC<FileUploadProps> = ({
  ipoId,
  onUploadSuccess,
  onUploadError,
}) => {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();

    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      handleFile(e.target.files[0]);
    }
  };

  const handleFile = (file: File) => {
    if (file.type !== 'application/pdf') {
      onUploadError?.('Please upload a PDF file');
      return;
    }

    const maxSize = 50 * 1024 * 1024;
    if (file.size > maxSize) {
      onUploadError?.('File size exceeds 50MB limit');
      return;
    }

    setSelectedFile(file);
  };

  const uploadFile = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setProgress(0);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const xhr = new XMLHttpRequest();

      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const percentComplete = (e.loaded / e.total) * 100;
          setProgress(Math.round(percentComplete));
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status === 200) {
          const result = JSON.parse(xhr.responseText);
          setUploading(false);
          setProgress(100);
          setSelectedFile(null);
          onUploadSuccess?.(result);
        } else {
          setUploading(false);
          try {
            const error = JSON.parse(xhr.responseText);
            onUploadError?.(error.detail || 'Upload failed');
          } catch {
            onUploadError?.(`Upload failed with status ${xhr.status}`);
          }
        }
      });

      xhr.addEventListener('error', () => {
        setUploading(false);
        onUploadError?.('Network error during upload');
      });

      const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000/api/v1';
      xhr.open('POST', `${baseUrl}/files/upload/prospectus/${ipoId}`);
      xhr.send(formData);

    } catch (error: any) {
      setUploading(false);
      onUploadError?.(error.message || 'Upload failed');
    }
  };

  const clearFile = () => {
    setSelectedFile(null);
    setProgress(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="space-y-4">
      <div
        className={`relative border-2 border-dashed rounded-xl p-6 sm:p-8 text-center transition-all duration-200 ${dragActive
            ? 'border-primary-500 bg-primary-50/50'
            : 'border-navy-300 hover:border-navy-400 bg-white'
          } ${uploading ? 'pointer-events-none opacity-50' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,application/pdf"
          onChange={handleChange}
          className="hidden"
          disabled={uploading}
          aria-label="Upload prospectus PDF"
        />

        {!selectedFile ? (
          <div>
            <svg
              className="mx-auto h-10 w-10 sm:h-12 sm:w-12 text-navy-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
            <p className="mt-3 sm:mt-4 text-xs sm:text-sm text-navy-600">
              Drag and drop prospectus PDF here, or{' '}
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="text-primary-600 hover:text-primary-700 font-medium"
              >
                browse
              </button>
            </p>
            <p className="mt-1.5 sm:mt-2 text-2xs sm:text-xs text-navy-400">
              PDF files only, max 50MB
            </p>
          </div>
        ) : (
          <div>
            <svg
              className="mx-auto h-10 w-10 sm:h-12 sm:w-12 text-success-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <p className="mt-3 sm:mt-4 text-xs sm:text-sm font-medium text-navy-900">
              {selectedFile.name}
            </p>
            <p className="mt-1 text-2xs sm:text-xs text-navy-500">
              {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
            </p>
            {!uploading && (
              <button
                type="button"
                onClick={clearFile}
                className="mt-3 text-xs sm:text-sm text-danger-600 hover:text-danger-700 font-medium transition-colors"
              >
                Remove
              </button>
            )}
          </div>
        )}
      </div>

      {uploading && (
        <div className="space-y-2">
          <div className="flex justify-between text-xs sm:text-sm">
            <span className="text-navy-600">Uploading and processing...</span>
            <span className="font-medium text-navy-900">{progress}%</span>
          </div>
          <div className="w-full bg-navy-100 rounded-full h-1.5 sm:h-2" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}>
            <div
              className="bg-primary-600 h-1.5 sm:h-2 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="text-2xs sm:text-xs text-navy-400">
            Please wait while we extract and analyze the prospectus...
          </p>
        </div>
      )}

      {selectedFile && !uploading && (
        <button
          onClick={uploadFile}
          className="w-full btn-primary py-2.5 sm:py-3"
        >
          Upload and Process Prospectus
        </button>
      )}
    </div>
  );
};

export default FileUpload;
