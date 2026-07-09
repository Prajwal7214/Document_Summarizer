import React, { useState } from 'react';
import { Download, ChevronDown, ChevronUp, FileText, ArrowUpDown, Loader2, AlertCircle } from 'lucide-react';
import { API_URL } from '../config/api';

export interface TableRowData {
  id: string;
  documentName: string;
  summary: string;
  keywords: string[];
  highlights: string[];
}

interface ResultsTableProps {
  data: TableRowData[];
}

type SortColumn = 'documentName' | 'summary';
type SortDirection = 'asc' | 'desc';

const ResultsTable: React.FC<ResultsTableProps> = ({ data }) => {
  const [sortCol, setSortCol] = useState<SortColumn>('documentName');
  const [sortDir, setSortDir] = useState<SortDirection>('asc');
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  const [isDownloadingCSV, setIsDownloadingCSV] = useState(false);
  const [isDownloadingPDF, setIsDownloadingPDF] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  // Sorting logic
  const sortedData = [...data].sort((a, b) => {
    const valA = a[sortCol].toLowerCase();
    const valB = b[sortCol].toLowerCase();

    if (valA < valB) return sortDir === 'asc' ? -1 : 1;
    if (valA > valB) return sortDir === 'asc' ? 1 : -1;
    return 0;
  });

  const handleSort = (col: SortColumn) => {
    if (sortCol === col) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortCol(col);
      setSortDir('asc');
    }
  };

  const toggleRow = (id: string) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedRows(newExpanded);
  };

  const downloadFile = async (type: 'csv' | 'table-pdf') => {
    if (type === 'csv') setIsDownloadingCSV(true);
    else setIsDownloadingPDF(true);

    setDownloadError(null);

    try {
      const response = await fetch(`${API_URL}/api/v1/download/${type}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ data: sortedData }),
      });

      if (!response.ok) {
        throw new Error(`Failed to generate ${type.toUpperCase()}`);
      }

      const blob = await response.blob();
      const cleanBlob = new Blob([blob], { type: type === 'csv' ? 'text/csv' : 'application/pdf' });
      const url = window.URL.createObjectURL(cleanBlob);

      // Open the PDF in a new tab for instant viewing/printing if PDF
      if (type === 'table-pdf') {
        window.open(url, '_blank');
      }

      const a = document.createElement('a');
      a.href = url;
      a.download = `documents_summary.${type === 'csv' ? 'csv' : 'pdf'}`;
      document.body.appendChild(a);
      a.click();

      // Delay cleanup to remove the temporary link element.
      // We do NOT revoke the URL so that the PDF preview tab and native browser downloads remain functional.
      setTimeout(() => {
        document.body.removeChild(a);
      }, 15000);
    } catch (error: any) {
      setDownloadError(error.message || `Failed to download ${type.toUpperCase()}`);
    } finally {
      if (type === 'csv') setIsDownloadingCSV(false);
      else setIsDownloadingPDF(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in-up">
      {/* Action Bar */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
        <div className="flex items-center gap-2 text-gray-700">
          <FileText className="text-gray-900" size={20} />
          <span className="font-medium text-gray-800">Processed Documents ({data.length})</span>
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          {downloadError && (
            <span className="text-xs text-red-400 flex items-center gap-1 mr-2">
              <AlertCircle size={14} /> {downloadError}
            </span>
          )}
          <button
            onClick={() => downloadFile('csv')}
            disabled={isDownloadingCSV || isDownloadingPDF}
            className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-2 bg-white hover:bg-gray-50 text-gray-800 rounded-lg transition-colors border border-gray-200 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isDownloadingCSV ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
            CSV
          </button>
          <button
            onClick={() => downloadFile('table-pdf')}
            disabled={isDownloadingCSV || isDownloadingPDF}
            className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-2 bg-black hover:bg-gray-900 text-white rounded-lg transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isDownloadingPDF ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
            Table PDF
          </button>
        </div>
      </div>

      {/* Table Wrapper */}
      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-gray-300">
            <thead className="text-xs uppercase bg-gray-50 text-gray-500 border-b border-gray-200">
              <tr>
                <th className="w-12 px-4 py-4 text-center"></th>
                <th
                  className="px-6 py-4 font-medium cursor-pointer hover:text-gray-200 transition-colors w-1/4"
                  onClick={() => handleSort('documentName')}
                >
                  <div className="flex items-center gap-2">
                    Document Name
                    <ArrowUpDown size={14} className={sortCol === 'documentName' ? 'text-white' : 'text-gray-600'} />
                  </div>
                </th>
                <th
                  className="px-6 py-4 font-medium cursor-pointer hover:text-gray-200 transition-colors w-1/3"
                  onClick={() => handleSort('summary')}
                >
                  <div className="flex items-center gap-2">
                    Summary
                    <ArrowUpDown size={14} className={sortCol === 'summary' ? 'text-white' : 'text-gray-600'} />
                  </div>
                </th>
                <th className="px-6 py-4 font-medium w-1/4">Keywords</th>
                <th className="px-6 py-4 font-medium w-1/6 text-center">Highlights</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {sortedData.map((row, index) => {
                const isExpanded = expandedRows.has(row.id);
                const isEven = index % 2 === 0;

                return (
                  <React.Fragment key={row.id}>
                    <tr
                      className={`hover:bg-gray-50 transition-colors cursor-pointer ${isEven ? 'bg-gray-50/50' : 'bg-white'}`}
                      onClick={() => toggleRow(row.id)}
                    >
                      <td className="px-4 py-4 text-center text-gray-500">
                        {isExpanded ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                      </td>
                      <td className="px-6 py-4 font-medium text-gray-900 break-words">
                        {row.documentName}
                      </td>
                      <td className="px-6 py-4">
                        <p className={`text-sm text-gray-600 ${!isExpanded && 'line-clamp-2'}`}>
                          {row.summary}
                        </p>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex flex-wrap gap-1.5">
                          {(isExpanded ? row.keywords : row.keywords.slice(0, 3)).map((kw, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-0.5 text-[10px] font-medium bg-gray-100 text-gray-700 border border-gray-200 rounded-full whitespace-nowrap"
                            >
                              {kw}
                            </span>
                          ))}
                          {!isExpanded && row.keywords.length > 3 && (
                            <span className="px-2 py-0.5 text-[10px] font-medium bg-gray-700 text-gray-300 rounded-full">
                              +{row.keywords.length - 3}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-center">
                        <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-gray-100 text-gray-700 text-xs font-bold border border-gray-200">
                          {row.highlights.length}
                        </span>
                      </td>
                    </tr>

                    {/* Expanded Details Row */}
                    {isExpanded && (
                      <tr className={`${isEven ? 'bg-gray-50/50' : 'bg-gray-50'}`}>
                        <td colSpan={5} className="px-6 py-6 border-t border-gray-200">
                          <div className="pl-10 space-y-6 animate-fade-in-up">
                            {/* Full Summary */}
                            <div className="space-y-2">
                              <h4 className="text-sm font-semibold text-gray-700 uppercase tracking-wider">Full Summary</h4>
                              <p className="text-gray-600 text-sm leading-relaxed">{row.summary}</p>
                            </div>

                            {/* Highlights */}
                            {row.highlights.length > 0 && (
                              <div className="space-y-3">
                                <h4 className="text-sm font-semibold text-gray-700 uppercase tracking-wider">Key Highlights</h4>
                                <div className="space-y-2">
                                  {row.highlights.map((highlight, idx) => (
                                    <blockquote
                                      key={idx}
                                      className="pl-3 py-1.5 border-l-2 border-gray-400 bg-white text-sm text-gray-600 italic rounded-r-md border border-gray-200"
                                    >
                                      "{highlight}"
                                    </blockquote>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}

              {sortedData.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                    No documents found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default ResultsTable;
