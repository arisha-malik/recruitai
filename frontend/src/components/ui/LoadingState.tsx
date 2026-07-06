import React from 'react';

interface LoadingStateProps {
  type?: 'spinner' | 'table' | 'card' | 'page';
  rows?: number;
  message?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({ 
  type = 'spinner', 
  rows = 5, 
  message = 'Loading data...' 
}) => {
  if (type === 'page') {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-slate-300">
        <div className="relative w-16 h-16 mb-4">
          <div className="absolute top-0 left-0 w-full h-full border-4 border-indigo-500/25 rounded-full"></div>
          <div className="absolute top-0 left-0 w-full h-full border-4 border-indigo-500 border-t-transparent rounded-full animate-spin"></div>
        </div>
        <p className="text-sm font-medium animate-pulse">{message}</p>
      </div>
    );
  }

  if (type === 'table') {
    return (
      <div className="w-full space-y-4 animate-pulse">
        <div className="h-10 bg-slate-800/80 rounded-lg w-full"></div>
        {Array.from({ length: rows }).map((_, idx) => (
          <div key={idx} className="flex space-x-4">
            <div className="h-12 bg-slate-800/40 rounded-lg w-1/4"></div>
            <div className="h-12 bg-slate-800/40 rounded-lg w-1/2"></div>
            <div className="h-12 bg-slate-800/40 rounded-lg w-1/4"></div>
          </div>
        ))}
      </div>
    );
  }

  if (type === 'card') {
    return (
      <div className="bg-card border border-border rounded-xl p-6 shadow-lg animate-pulse space-y-4">
        <div className="h-6 bg-slate-800/80 rounded w-1/3"></div>
        <div className="h-4 bg-slate-800/40 rounded w-full"></div>
        <div className="h-4 bg-slate-800/40 rounded w-5/6"></div>
        <div className="h-4 bg-slate-800/40 rounded w-2/3"></div>
      </div>
    );
  }

  return (
    <div className="flex items-center space-x-2 text-indigo-400">
      <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <span className="text-sm font-medium text-slate-300">{message}</span>
    </div>
  );
};
