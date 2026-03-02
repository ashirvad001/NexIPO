// components/Loading.tsx
import React from 'react';

interface LoadingProps {
  fullScreen?: boolean;
  text?: string;
}

const Loading: React.FC<LoadingProps> = ({ fullScreen = false, text = 'Loading...' }) => {
  const content = (
    <div className="flex flex-col items-center justify-center" role="status" aria-label={text}>
      <div className="spinner" aria-hidden="true"></div>
      <p className="mt-4 text-sm text-navy-500 font-medium">{text}</p>
    </div>
  );

  if (fullScreen) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center animate-fade-in">
        {content}
      </div>
    );
  }

  return <div className="py-10 sm:py-12 animate-fade-in">{content}</div>;
};

export default Loading;
