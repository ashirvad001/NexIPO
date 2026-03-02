// components/Error.tsx
import React from 'react';

interface ErrorProps {
  message?: string;
  retry?: () => void;
}

const Error: React.FC<ErrorProps> = ({
  message = 'Something went wrong. Please try again.',
  retry
}) => {
  return (
    <div className="py-10 sm:py-14 flex flex-col items-center justify-center animate-fade-in" role="alert">
      <div className="empty-state-icon bg-danger-50">
        <svg className="w-7 h-7 sm:w-8 sm:h-8 text-danger-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
      <h3 className="text-lg font-semibold text-navy-900 mb-2">Error</h3>
      <p className="text-sm text-navy-500 mb-5 text-center max-w-md px-4">{message}</p>
      {retry && (
        <button onClick={retry} className="btn-primary">
          Try Again
        </button>
      )}
    </div>
  );
};

export default Error;
