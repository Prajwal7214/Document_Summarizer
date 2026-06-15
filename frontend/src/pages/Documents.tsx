import React from 'react';
import { useLocation, Link } from 'react-router-dom';
import { Files, ArrowLeft } from 'lucide-react';
import ResultsTable, { type TableRowData } from '../components/ResultsTable';

const Documents = () => {
  const location = useLocation();
  const state = location.state as { data: any[] } | null;

  if (!state || !state.data || state.data.length === 0) {
    return (
      <div className="max-w-3xl mx-auto py-20 flex flex-col items-center justify-center text-center space-y-6 animate-fade-in-up">
        <div className="w-20 h-20 bg-gray-200 rounded-full flex items-center justify-center">
          <Files size={40} className="text-gray-500" />
        </div>
        <div className="space-y-2">
          <h2 className="text-2xl font-bold text-gray-800">No Documents Found</h2>
          <p className="text-gray-500">No documents summarized yet. Go to Home to upload files.</p>
        </div>
        <Link 
          to="/" 
          className="flex items-center gap-2 px-6 py-3 bg-white hover:bg-gray-100 text-black rounded-xl transition-all shadow-lg font-medium"
        >
          <ArrowLeft size={18} />
          Go to Home
        </Link>
      </div>
    );
  }

  const mappedData: TableRowData[] = state.data.map((item: any, index: number) => ({
    id: item.id || `doc-${index}`,
    documentName: item.name || item.documentName || 'Unknown Document',
    summary: item.summary || '',
    keywords: item.keywords || [],
    highlights: item.highlights || []
  }));

  return (
    <div className="max-w-6xl mx-auto space-y-6 py-8">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Files className="text-gray-900" />
          Document Library
        </h2>
      </div>

      <ResultsTable data={mappedData} />
    </div>
  );
};

export default Documents;
