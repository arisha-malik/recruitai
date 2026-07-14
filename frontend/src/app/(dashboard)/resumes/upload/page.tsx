'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { api } from '@/lib/api';
import { Card } from '@/components/ui/Card';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { UploadCloud, FileText, CheckCircle2, AlertCircle, X, File as FileIcon, Loader2 } from 'lucide-react';
import axios from 'axios';

type ParsingStatus = 'IDLE' | 'UPLOADED' | 'PARSING' | 'PARSED' | 'FAILED';

interface FileUploadState {
  file: File;
  status: ParsingStatus;
  message: string;
  error: string | null;
  candidateId: string | null;
  resumeId: string | null;
}

export default function ResumeUploadPage() {
  const router = useRouter();
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [files, setFiles] = useState<FileUploadState[]>([]);
  const [loading, setLoading] = useState(false);
  
  // Poll status interval
  useEffect(() => {
    const parsingFiles = files.filter(f => f.status === 'PARSING' && f.resumeId);
    if (parsingFiles.length === 0) return;

    const intervalId = setInterval(async () => {
      let hasChanges = false;
      const newFiles = [...files];

      await Promise.all(parsingFiles.map(async (fileState) => {
        try {
          const res = await api.get(`/resumes/${fileState.resumeId}/status`);
          const status = res.data.status;
          
          if (status === 'PARSED' || status === 'FAILED') {
            const index = newFiles.findIndex(f => f.resumeId === fileState.resumeId);
            if (index !== -1) {
              if (status === 'PARSED') {
                newFiles[index] = { ...newFiles[index], status: 'PARSED', message: 'Parsed successfully!' };
              } else {
                newFiles[index] = { ...newFiles[index], status: 'FAILED', error: res.data.failure_reason || 'Parsing failed.' };
              }
              hasChanges = true;
            }
          }
        } catch (err) {
          console.error(`Error polling resume status for ${fileState.resumeId}:`, err);
        }
      }));

      if (hasChanges) {
        setFiles(newFiles);
      }
    }, 3000);

    return () => clearInterval(intervalId);
  }, [files]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const newFilesArray = Array.from(e.target.files).map(f => ({
        file: f,
        status: 'IDLE' as ParsingStatus,
        message: 'Pending upload...',
        error: null,
        candidateId: null,
        resumeId: null,
      }));
      setFiles(prev => [...prev, ...newFilesArray]);
    }
    // reset input value so the same file can be selected again if removed
    e.target.value = '';
  };

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleSingleUpload = async () => {
    const fileState = files[0];
    
    // Update state to loading
    setFiles(prev => {
      const newArr = [...prev];
      newArr[0] = { ...newArr[0], status: 'IDLE', message: 'Uploading file to server...', error: null };
      return newArr;
    });

    try {
      const formData = new FormData();
      if (firstName) formData.append('first_name', firstName);
      if (lastName) formData.append('last_name', lastName);
      if (email) formData.append('email', email);
      formData.append('file', fileState.file);

      const res = await api.post('/resumes/upload', formData, {
        headers: { 'Content-Type': undefined }
      });
      
      const { resumeId } = res.data;
      
      setFiles(prev => {
        const newArr = [...prev];
        newArr[0] = { 
          ...newArr[0], 
          status: 'PARSING', 
          resumeId: resumeId, 
          message: 'AI Parsing pipeline is working in the background...' 
        };
        return newArr;
      });
    } catch (err: any) {
      console.error(err);
      let errorMsg = 'Resume upload failed. Please verify files and credentials.';
      if (err.response && err.response.data && err.response.data.detail) {
        errorMsg = err.response.data.detail;
      }
      setFiles(prev => {
        const newArr = [...prev];
        newArr[0] = { ...newArr[0], status: 'FAILED', error: errorMsg };
        return newArr;
      });
    }
  };

  const handleBulkUpload = async () => {
    // Collect all IDLE or FAILED files
    const filesToUpload = files.filter(f => f.status === 'IDLE' || f.status === 'FAILED');
    if (filesToUpload.length === 0) return;

    // Mark them as uploading
    setFiles(prev => prev.map(f => 
      (f.status === 'IDLE' || f.status === 'FAILED') ? { ...f, message: 'Uploading to bulk endpoint...', error: null } : f
    ));

    const formData = new FormData();
    filesToUpload.forEach(f => {
      formData.append('files', f.file);
    });

    try {
      console.log('Sending bulk upload to:', '/resumes/bulk-upload');
      const res = await api.post('/resumes/bulk-upload', formData, {
        headers: { 'Content-Type': undefined }
      });
      console.log('Bulk upload success:', res.data);

      const results = res.data.results;
      
      setFiles(prev => {
        const newArr = [...prev];
        results.forEach((result: any) => {
          const fileIndex = newArr.findIndex(f => f.file.name === result.filename && (f.status === 'IDLE' || f.message === 'Uploading to bulk endpoint...'));
          if (fileIndex !== -1) {
            if (result.status === 'FAILED') {
              newArr[fileIndex] = { ...newArr[fileIndex], status: 'FAILED', error: result.error };
            } else {
              newArr[fileIndex] = { 
                ...newArr[fileIndex], 
                status: 'PARSING', 
                resumeId: result.resume_id, 
                message: 'AI Parsing pipeline is working in the background...' 
              };
            }
          }
        });
        return newArr;
      });
    } catch (err: any) {
      console.error('Bulk upload failed entirely:', err);
      console.error('Error config:', err.config);
      console.error('Error response status:', err.response?.status);
      console.error('Error response data:', err.response?.data);
      
      let errorMsg = 'Bulk upload failed entirely.';
      if (err.response?.data?.detail) {
        if (typeof err.response.data.detail === 'string') {
          errorMsg = err.response.data.detail;
        } else if (Array.isArray(err.response.data.detail)) {
          errorMsg = 'Validation error: Invalid request payload.';
        }
      }
      
      setFiles(prev => prev.map(f => 
        (f.message === 'Uploading to bulk endpoint...') ? { ...f, status: 'FAILED', error: errorMsg } : f
      ));
    }
  };

  const handleUploadSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (files.length === 0) {
      return;
    }

    setLoading(true);

    if (files.length === 1) {
      await handleSingleUpload();
    } else {
      await handleBulkUpload();
    }

    setLoading(false);
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-slate-900">
          Upload Resumes
        </h1>
        <p className="text-sm text-slate-500 mt-1.5">
          Submit one or multiple resumes directly. Our AI parsing model will automatically extract profile details.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload Form */}
        <Card className="lg:col-span-2">
          <form onSubmit={handleUploadSubmit} className="space-y-5">
            
            {files.length <= 1 && (
              <>
                <h3 className="text-base font-bold text-slate-900">Candidate Information</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-2">
                      First Name <span className="text-slate-500 font-normal lowercase tracking-normal">(Optional)</span>
                    </label>
                    <input
                      type="text"
                      value={firstName}
                      onChange={(e) => setFirstName(e.target.value)}
                      className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2.5 px-3 text-sm text-[#191c1a] placeholder-[#a0aba5] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
                      placeholder="Auto-extract from resume"
                      disabled={loading || (files.length === 1 && files[0].status === 'PARSING')}
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-2">
                      Last Name <span className="text-slate-500 font-normal lowercase tracking-normal">(Optional)</span>
                    </label>
                    <input
                      type="text"
                      value={lastName}
                      onChange={(e) => setLastName(e.target.value)}
                      className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2.5 px-3 text-sm text-[#191c1a] placeholder-[#a0aba5] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
                      placeholder="Auto-extract from resume"
                      disabled={loading || (files.length === 1 && files[0].status === 'PARSING')}
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-2">
                    Email Address <span className="text-slate-500 font-normal lowercase tracking-normal">(Optional)</span>
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full bg-white border border-[#e6e9e4] rounded-lg py-2.5 px-3 text-sm text-[#191c1a] placeholder-[#a0aba5] focus:outline-none focus:border-[#476353] focus:ring-1 focus:ring-[#476353]"
                    placeholder="Auto-extract from resume"
                    disabled={loading || (files.length === 1 && files[0].status === 'PARSING')}
                  />
                </div>
              </>
            )}

            {files.length > 1 && (
              <div className="bg-indigo-50 border border-indigo-100 rounded-lg p-4 text-sm text-indigo-800">
                Multiple files selected. Manual candidate information entry is disabled. Profiles will be automatically created using extracted details.
              </div>
            )}

            {/* Drag & Drop File Upload */}
            <div>
              <label className="block text-xs font-semibold text-[#424844] uppercase tracking-wider mb-2">
                Upload Resume(s) (PDF, DOCX) *
              </label>
              <div className="border-2 border-dashed border-[#223049] hover:border-indigo-500/50 rounded-xl p-8 flex flex-col items-center justify-center transition-colors bg-slate-900/30 text-center relative cursor-pointer">
                <input
                  type="file"
                  multiple
                  onChange={handleFileChange}
                  accept=".pdf,.docx,.doc,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  disabled={loading}
                />
                <UploadCloud size={40} className="text-slate-500 mb-3" />
                <p className="text-sm font-semibold text-slate-700">
                  Click to select or drag resume files here
                </p>
                <p className="text-xs text-slate-500 mt-1">PDF or Word Documents up to 10MB</p>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || files.length === 0}
              className="w-full bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-650 hover:to-purple-750 text-white font-semibold py-3 rounded-lg shadow-lg hover:shadow-indigo-500/10 transition-all duration-200 active:scale-[0.98] disabled:opacity-55 flex items-center justify-center gap-2"
            >
              {loading ? <Loader2 size={18} className="animate-spin" /> : <UploadCloud size={16} />}
              {loading ? 'Processing...' : `Upload & Parse ${files.length > 0 ? files.length : ''} Resume${files.length > 1 ? 's' : ''}`}
            </button>
          </form>
        </Card>

        {/* Upload Status Sidebar */}
        <div className="space-y-6 lg:col-span-1">
          <Card title="Upload Progress">
            {files.length === 0 && (
              <p className="text-sm text-slate-500 py-6 text-center">
                Select one or more files to begin uploading.
              </p>
            )}

            <div className="space-y-4 max-h-[600px] overflow-y-auto pr-2">
              {files.map((fileState, index) => (
                <div key={`${fileState.file.name}-${index}`} className="border border-slate-200 rounded-lg p-3 bg-white">
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex items-center gap-2 overflow-hidden">
                      <FileIcon size={16} className="text-indigo-500 shrink-0" />
                      <span className="text-sm font-semibold text-slate-700 truncate" title={fileState.file.name}>
                        {fileState.file.name}
                      </span>
                    </div>
                    {fileState.status === 'IDLE' && !loading && (
                      <button 
                        onClick={() => removeFile(index)}
                        className="text-slate-400 hover:text-rose-500 transition-colors"
                        title="Remove file"
                      >
                        <X size={16} />
                      </button>
                    )}
                  </div>
                  
                  <div className="flex items-center justify-between mb-2">
                    <StatusBadge status={fileState.status} />
                  </div>

                  {fileState.message && fileState.status !== 'FAILED' && (
                    <p className="text-xs text-slate-500">{fileState.message}</p>
                  )}

                  {fileState.error && (
                    <div className="p-2 bg-rose-50 border border-rose-100 rounded text-xs text-rose-600 mt-2 flex gap-1 items-start">
                      <AlertCircle size={14} className="shrink-0 mt-0.5" />
                      <span>{fileState.error}</span>
                    </div>
                  )}

                  {fileState.status === 'PARSED' && fileState.resumeId && (
                    <div className="mt-3">
                      <button
                        onClick={() => router.push(`/candidates`)} 
                        className="w-full bg-emerald-50 text-emerald-600 hover:bg-emerald-100 border border-emerald-200 text-xs font-bold py-1.5 rounded transition-colors text-center"
                      >
                        View in Candidate Pool
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
