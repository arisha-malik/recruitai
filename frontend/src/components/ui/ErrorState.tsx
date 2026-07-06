import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({ 
  title = 'Something went wrong', 
  message, 
  onRetry 
}) => {
  return (
    <div className="bg-rose-950/20 border border-rose-500/30 rounded-xl p-6 shadow-md max-w-md mx-auto my-4 text-center">
      <div className="inline-flex p-3 rounded-full bg-rose-500/10 text-rose-400 mb-4">
        <AlertCircle size={28} />
      </div>
      <h4 className="text-base font-semibold text-rose-200 mb-1">{title}</h4>
      <p className="text-sm text-slate-300 mb-5">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-2 bg-rose-500/15 hover:bg-rose-500/25 border border-rose-500/40 hover:border-rose-500/60 text-rose-200 text-sm font-medium px-4 py-2 rounded-lg transition-all duration-150 active:scale-95"
        >
          <RefreshCw size={16} />
          Retry Request
        </button>
      )}
    </div>
  );
};
