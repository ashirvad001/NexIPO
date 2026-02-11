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
    <div className="py-12 flex flex-col items-center justify-center">
      <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mb-4">
        <svg className="w-8 h-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">Error</h3>
      <p className="text-sm text-gray-600 mb-4 text-center max-w-md">{message}</p>
      {retry && (
        <button onClick={retry} className="btn-primary">
          Try Again
        </button>
      )}
    </div>
  );
};

export default Error;
