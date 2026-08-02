
import { useLocation, Link } from 'react-router-dom';
import { FileText, ArrowLeft } from 'lucide-react';
import SummaryCard, { type SummaryData } from '../components/SummaryCard';

const Summary = () => {
  const location = useLocation();
  const state = location.state as { data: SummaryData, document_id?: string, filename?: string } | null;

  if (!state || !state.data) {
    return (
      <div className="max-w-3xl mx-auto py-20 flex flex-col items-center justify-center text-center space-y-6 animate-fade-in-up">
        <div className="w-20 h-20 bg-gray-200 rounded-full flex items-center justify-center">
          <FileText size={40} className="text-gray-500" />
        </div>
        <div className="space-y-2">
          <h2 className="text-2xl font-bold text-gray-800">No Summary Data</h2>
          <p className="text-gray-500">Please upload a document from the home page to view its summary.</p>
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

  return (
    <div className="max-w-5xl mx-auto py-8">
      <SummaryCard 
        data={state.data} 
        documentId={state.document_id} 
        filename={state.filename} 
      />
    </div>
  );
};

export default Summary;
