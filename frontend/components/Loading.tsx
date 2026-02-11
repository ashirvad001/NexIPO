// components/Loading.tsx
import React from 'react';

interface LoadingProps {
  fullScreen?: boolean;
  text?: string;
}

const Loading: React.FC<LoadingProps> = ({ fullScreen = false, text = 'Loading...' }) => {
  const content = (
    <div className="flex flex-col items-center justify-center">
      <div className="spinner border-primary-600"></div>
      <p className="mt-4 text-sm text-gray-600">{text}</p>
    </div>
  );

  if (fullScreen) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        {content}
      </div>
    );
  }

  return <div className="py-12">{content}</div>;
};

export default Loading;
