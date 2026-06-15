import React, { useState, useRef } from 'react';
import type { DragEvent, ChangeEvent } from 'react';
import { UploadCloud, File as FileIcon, X, Loader2, AlertCircle, CheckCircle2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useToast } from '../contexts/ToastContext';

type UploadMode = 'single' | 'multiple';
type SummaryType = 'short' | 'detailed' | 'academic';

const FileUpload = () => {
  const [files, setFiles] = useState<File[]>([]);
  const [mode, setMode] = useState<UploadMode>('single');
  const [summaryType, setSummaryType] = useState<SummaryType>('short');
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const { toast, success, error } = useToast();

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFiles(Array.from(e.target.files));
    }
  };

  const processFiles = (newFiles: File[]) => {
    // Filter for accepted types
    const validTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
    const validFiles = newFiles.filter(file => validTypes.includes(file.type) || file.name.endsWith('.pdf') || file.name.endsWith('.docx') || file.name.endsWith('.txt'));
    
    if (validFiles.length !== newFiles.length) {
      toast("Some files were rejected. Only PDF, DOCX, and TXT are supported.", 'error');
    }
    
    if (validFiles.length > 0) {
      if (mode === 'single') {
        setFiles([validFiles[0]]);
      } else {
        setFiles(prev => [...prev, ...validFiles]);
      }
    }
    
    // Reset file input so same file can be selected again
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const removeFile = (indexToRemove: number) => {
    setFiles(files.filter((_, index) => index !== indexToRemove));
  };

  const handleSubmit = async () => {
    if (files.length === 0) return;
    
    setIsLoading(true);
    
    const formData = new FormData();
    const endpoint = mode === 'single' 
      ? `http://localhost:8000/api/v1/summarize?summary_type=${summaryType}`
      : `http://localhost:8000/api/v1/summarize-multiple?summary_type=${summaryType}`;
      
    if (mode === 'single') {
      formData.append('file', files[0]);
    } else {
      files.forEach(file => formData.append('files', file));
    }

    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }

      const data = await response.json();
      success("Documents processed successfully!");
      
      // Navigate to respective pages and pass data
      if (mode === 'single') {
        navigate('/summary', { 
          state: { 
            data, 
            document_id: data.document_id || Date.now().toString(), // fallback
            filename: files[0].name 
          } 
        });
      } else {
        navigate('/documents', { state: { data } });
      }
      
    } catch (err: any) {
      error(err.message || "An error occurred during upload. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto space-y-6">
      {/* Controls: Mode and Type Selection */}
      <div className="flex flex-col sm:flex-row justify-between gap-4 bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
        <div className="flex bg-gray-100 rounded-lg p-1 border border-gray-200">
          <button
            onClick={() => {
              setMode('single');
              if (files.length > 1) setFiles([files[0]]);
            }}
            className={`px-4 py-2 text-sm font-medium rounded-md transition-all ${
              mode === 'single' 
                ? 'bg-black text-white shadow-sm' 
                : 'text-gray-500 hover:text-gray-800'
            }`}
          >
            Single File
          </button>
          <button
            onClick={() => setMode('multiple')}
            className={`px-4 py-2 text-sm font-medium rounded-md transition-all ${
              mode === 'multiple' 
                ? 'bg-black text-white shadow-sm' 
                : 'text-gray-500 hover:text-gray-800'
            }`}
          >
            Multiple Files
          </button>
        </div>

        <div className="flex items-center gap-3">
          <label className="text-sm text-gray-600 font-medium">Summary Type:</label>
          <select
            value={summaryType}
            onChange={(e) => setSummaryType(e.target.value as SummaryType)}
            className="bg-white border border-gray-300 text-gray-800 text-sm rounded-lg focus:ring-gray-900 focus:border-gray-900 block px-3 py-2 outline-none"
          >
            <option value="short">Short</option>
            <option value="detailed">Detailed</option>
            <option value="academic">Academic</option>
          </select>
        </div>
      </div>

      {/* Drag & Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`flex flex-col items-center justify-center w-full h-56 border-2 border-dashed rounded-2xl cursor-pointer transition-all duration-300 ${
          isDragging 
            ? 'bg-gray-100 border-gray-900' 
            : 'bg-white border-gray-300 hover:bg-gray-50 hover:border-gray-500'
        }`}
      >
        <div className="flex flex-col items-center justify-center pt-5 pb-6 space-y-4">
          <div className={`p-4 rounded-full transition-colors duration-300 ${isDragging ? 'bg-gray-200' : 'bg-gray-100'}`}>
            <UploadCloud className={`w-10 h-10 ${isDragging ? 'text-gray-900' : 'text-gray-500'}`} />
          </div>
          <div className="space-y-1 text-center">
            <p className="text-lg text-gray-700">
              <span className="font-semibold text-gray-900">Click to upload</span> or drag and drop
            </p>
            <p className="text-sm text-gray-400">PDF, DOCX, TXT (Max: 50MB)</p>
          </div>
        </div>
        <input 
          ref={fileInputRef}
          type="file" 
          className="hidden" 
          multiple={mode === 'multiple'}
          accept=".pdf,.docx,.txt,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
          onChange={handleFileChange}
        />
      </div>

      {/* Status Messages removed to prefer global Toasts */}

      {/* Selected Files List */}
      {files.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
          <div className="px-4 py-3 border-b border-gray-200 bg-gray-50 flex justify-between items-center">
            <h3 className="text-sm font-medium text-gray-700">Selected Files ({files.length})</h3>
            {files.length > 0 && mode === 'multiple' && (
              <button onClick={() => setFiles([])} className="text-xs text-gray-500 hover:text-red-400 transition-colors">
                Clear all
              </button>
            )}
          </div>
          <ul className="divide-y divide-gray-200 max-h-48 overflow-y-auto">
            {files.map((file, idx) => (
              <li key={`${file.name}-${idx}`} className="flex items-center justify-between px-4 py-3 hover:bg-gray-750 transition-colors">
                <div className="flex items-center gap-3 overflow-hidden">
                  <FileIcon className="text-gray-500 flex-shrink-0" size={18} />
                  <span className="text-sm text-gray-800 truncate">{file.name}</span>
                  <span className="text-xs text-gray-400 flex-shrink-0">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </span>
                </div>
                <button 
                  onClick={(e) => { e.stopPropagation(); removeFile(idx); }}
                  className="p-1 text-gray-500 hover:text-red-400 hover:bg-red-400/10 rounded transition-all"
                  disabled={isLoading}
                >
                  <X size={16} />
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Submit Button */}
      <button
        onClick={handleSubmit}
        disabled={files.length === 0 || isLoading}
        className={`w-full py-3.5 rounded-xl font-semibold flex items-center justify-center gap-2 transition-all ${
          files.length === 0 || isLoading
            ? 'bg-gray-200 text-gray-400 cursor-not-allowed border border-gray-300'
            : 'bg-black hover:bg-gray-900 text-white shadow-lg'
        }`}
      >
        {isLoading ? (
          <>
            <Loader2 className="animate-spin" size={20} />
            Processing Document{files.length > 1 ? 's' : ''}...
          </>
        ) : (
          `Generate Summary`
        )}
      </button>
    </div>
  );
};

export default FileUpload;
