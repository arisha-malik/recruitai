import React, { useEffect, useState } from 'react';
import { X, Server, Database, CheckCircle2, AlertCircle } from 'lucide-react';

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export default function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const [apiStatus, setApiStatus] = useState<'checking' | 'connected' | 'error'>('checking');
  const [apiUrl, setApiUrl] = useState<string>('');

  useEffect(() => {
    if (isOpen) {
      setApiUrl(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1');
      checkApiHealth();
    }
  }, [isOpen]);

  const checkApiHealth = async () => {
    setApiStatus('checking');
    try {
      // The health check is at the root level, so we strip /api/v1
      const baseUrl = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1').replace('/api/v1', '');
      const res = await fetch(`${baseUrl}/`);
      if (res.ok) {
        setApiStatus('connected');
      } else {
        setApiStatus('error');
      }
    } catch (err) {
      setApiStatus('error');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-2xl relative overflow-hidden flex flex-col">
        <div className="flex justify-between items-center p-5 border-b border-[#e6e9e4] bg-[#f7faf5]">
          <h3 className="text-lg font-bold text-[#191c1a]">Application Settings</h3>
          <button onClick={onClose} className="text-[#727973] hover:text-[#191c1a] transition-colors">
            <X size={20} />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Theme setting - purely informational as requested */}
          <div>
            <h4 className="text-sm font-bold text-[#191c1a] mb-2">Theme Preference</h4>
            <div className="flex items-center justify-between p-3 bg-[#f1f4f0] border border-[#e6e9e4] rounded-xl">
              <span className="text-sm text-[#424844]">Light Mode</span>
              <span className="text-xs bg-[#e6e9e4] text-[#727973] px-2 py-1 rounded font-semibold">Active</span>
            </div>
            <p className="text-[11px] text-[#727973] mt-1.5 ml-1">Dark mode is currently disabled in this environment.</p>
          </div>

          {/* API Status */}
          <div>
            <h4 className="text-sm font-bold text-[#191c1a] mb-2">API Connection Status</h4>
            <div className="p-4 bg-[#f1f4f0] border border-[#e6e9e4] rounded-xl space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-sm text-[#424844]">
                  <Server size={16} className="text-[#476353]" />
                  <span>Backend Server</span>
                </div>
                {apiStatus === 'checking' && <span className="text-xs text-amber-500 font-semibold animate-pulse">Checking...</span>}
                {apiStatus === 'connected' && (
                  <span className="flex items-center gap-1 text-xs text-emerald-600 font-bold">
                    <CheckCircle2 size={14} /> Connected
                  </span>
                )}
                {apiStatus === 'error' && (
                  <span className="flex items-center gap-1 text-xs text-rose-500 font-bold">
                    <AlertCircle size={14} /> Unreachable
                  </span>
                )}
              </div>
              <div className="text-xs text-[#727973] font-mono bg-white p-2 rounded border border-[#e6e9e4] break-all">
                {apiUrl}
              </div>
            </div>
          </div>

          {/* Storage Mode */}
          <div>
            <h4 className="text-sm font-bold text-[#191c1a] mb-2">Storage Configuration</h4>
            <div className="flex items-center justify-between p-3 bg-[#f1f4f0] border border-[#e6e9e4] rounded-xl">
              <div className="flex items-center gap-2 text-sm text-[#424844]">
                <Database size={16} className="text-[#476353]" />
                <span>Resume Storage</span>
              </div>
              <span className="text-xs bg-[#caead6] text-[#314d3e] border border-[#476353]/20 px-2 py-0.5 rounded font-bold uppercase tracking-wider">
                {process.env.NEXT_PUBLIC_STORAGE_MODE || 'AWS S3 / Local'}
              </span>
            </div>
          </div>
        </div>

        <div className="p-4 border-t border-[#e6e9e4] bg-[#f7faf5] flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 bg-[#476353] hover:bg-[#314d3e] text-white text-sm font-semibold rounded-lg shadow-sm transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
