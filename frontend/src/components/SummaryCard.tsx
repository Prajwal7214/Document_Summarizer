import React, { useState } from 'react';
import { Download, FileText, CheckCircle2, ChevronRight, Loader2, AlertCircle, MessageSquare } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { API_URL } from '../config/api';

export interface SummaryData {
  title: string;
  summary: string;
  bullets: string[];
  highlights: string[];
  keywords: string[];
}

interface SummaryCardProps {
  data: SummaryData;
  documentId?: string;
  filename?: string;
}

const SummaryCard: React.FC<SummaryCardProps> = ({ data, documentId, filename }) => {
  const [isDownloading, setIsDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const navigate = useNavigate();

  const handleDownloadPDF = async () => {
    setIsDownloading(true);
    setDownloadError(null);

    try {
      const response = await fetch(`${API_URL}/api/v1/download/pdf`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error('Failed to generate PDF');
      }

      // Handle the blob response for download
      const blob = await response.blob();
      const pdfBlob = new Blob([blob], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(pdfBlob);

      // Open the PDF in a new tab for instant viewing/printing
      window.open(url, '_blank');

      const a = document.createElement('a');
      a.href = url;
      a.download = `${data.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_summary.pdf`;
      document.body.appendChild(a);
      a.click();

      // Delay cleanup to remove the temporary link element.
      // We do NOT revoke the URL so that the PDF preview tab and native browser downloads remain functional.
      setTimeout(() => {
        document.body.removeChild(a);
      }, 15000);
    } catch (error: any) {
      setDownloadError(error.message || 'An error occurred while downloading the PDF.');
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden animate-fade-in-up">
      {/* Header Section */}
      <div className="p-8 border-b border-gray-100 bg-gray-50">
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6">
          <div className="space-y-4 flex-1">
            <h1 className="text-3xl font-bold text-gray-900 leading-tight">
              {data.title}
            </h1>

            <div className="flex flex-wrap gap-2 pt-2">
              {data.keywords.map((keyword, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 text-xs font-semibold bg-gray-900 text-white border border-gray-900 rounded-full"
                >
                  {keyword}
                </span>
              ))}
            </div>
          </div>

          <div className="flex-shrink-0 flex flex-col gap-3">
            <button
              onClick={handleDownloadPDF}
              disabled={isDownloading}
              className="flex items-center justify-center gap-2 px-5 py-2.5 bg-black hover:bg-gray-900 text-white rounded-xl transition-all shadow-sm font-medium min-w-[160px] disabled:opacity-70 disabled:cursor-not-allowed"
            >
              {isDownloading ? (
                <Loader2 size={18} className="animate-spin" />
              ) : (
                <Download size={18} />
              )}
              {isDownloading ? 'Generating...' : 'Download PDF'}
            </button>
            {documentId && (
              <button
                onClick={() => navigate('/chat', { state: { document_id: documentId, filename: filename } })}
                className="flex items-center justify-center gap-2 px-5 py-2.5 bg-white hover:bg-gray-50 text-gray-800 rounded-xl transition-all font-medium min-w-[160px] border border-gray-200 shadow-sm"
              >
                <MessageSquare size={18} />
                Chat with Doc
              </button>
            )}
            {downloadError && (
              <p className="text-xs text-red-500 flex items-center gap-1">
                <AlertCircle size={12} /> {downloadError}
              </p>
            )}
          </div>
        </div>
      </div>

      <div className="p-8 space-y-10">
        {/* Abstract / Main Summary */}
        <section className="space-y-4">
          <h2 className="text-xl font-semibold text-gray-800 flex items-center gap-2">
            <FileText className="text-gray-900" size={20} />
            Executive Summary
          </h2>
          <p className="text-gray-600 leading-relaxed text-lg">
            {data.summary}
          </p>
        </section>

        <div className="grid md:grid-cols-2 gap-10">
          {/* Key Points (Bullets) */}
          <section className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
              <CheckCircle2 className="text-gray-900" size={18} />
              Key Takeaways
            </h2>
            <ul className="space-y-3">
              {data.bullets.map((bullet, idx) => (
                <li key={idx} className="flex items-start gap-3 text-gray-700">
                  <div className="mt-1 flex-shrink-0 w-1.5 h-1.5 rounded-full bg-gray-900" />
                  <span className="leading-relaxed">{bullet}</span>
                </li>
              ))}
            </ul>
          </section>

          {/* Highlights */}
          <section className="space-y-4">
            <h2 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
              <ChevronRight className="text-gray-900" size={18} />
              Highlights
            </h2>
            <div className="space-y-4">
              {data.highlights.map((highlight, idx) => (
                <blockquote
                  key={idx}
                  className="pl-4 py-2 border-l-4 border-gray-400 bg-gray-50 rounded-r-lg text-gray-700 italic"
                >
                  "{highlight}"
                </blockquote>
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};

export default SummaryCard;
