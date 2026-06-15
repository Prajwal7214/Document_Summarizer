import React, { useState, useRef, useEffect } from 'react';
import { MessageSquare, Send, Upload, FileText, Loader2, ChevronDown, ChevronUp } from 'lucide-react';
import { useLocation } from 'react-router-dom';
import { useToast } from '../contexts/ToastContext';

interface SourceChunk {
  content: string;
  page?: number;
}

interface Message {
  id: string;
  role: 'user' | 'ai';
  content: string;
  sources?: SourceChunk[];
}

const Chat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  
  const [documentId, setDocumentId] = useState<string | null>(null);
  const [filename, setFilename] = useState<string | null>(null);
  
  const [isIngesting, setIsIngesting] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  
  const [expandedSources, setExpandedSources] = useState<Set<string>>(new Set());
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  
  const location = useLocation();
  const { error, info } = useToast();

  useEffect(() => {
    const state = location.state as { document_id?: string, filename?: string } | null;
    if (state?.document_id && state?.filename && !documentId) {
      setDocumentId(state.document_id);
      setFilename(state.filename);
      setMessages([
        {
          id: Date.now().toString(),
          role: 'ai',
          content: `I'm ready to answer questions about "${state.filename}". What would you like to know?`
        }
      ]);
    }
  }, [location.state, documentId]);

  // Auto-scroll to bottom of chat
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsIngesting(true);
    setFilename(file.name);
    setDocumentId(null);
    setMessages([]);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/api/v1/chat/ingest', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to ingest document');
      }

      const data = await response.json();
      setDocumentId(data.document_id);
      
      // Add initial greeting message
      setMessages([
        {
          id: Date.now().toString(),
          role: 'ai',
          content: `I've successfully analyzed "${file.name}". What would you like to know about it?`
        }
      ]);
    } catch (err: any) {
      error(err.message || 'Error uploading document.');
      setFilename(null);
    } finally {
      setIsIngesting(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!inputValue.trim() || !documentId) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue.trim()
    };

    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setIsTyping(true);

    try {
      const response = await fetch('http://localhost:8000/api/v1/chat/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          document_id: documentId,
          question: userMsg.content,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get answer');
      }

      const data = await response.json();
      
      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'ai',
        content: data.answer,
        sources: data.sources || []
      };

      setMessages(prev => [...prev, aiMsg]);
    } catch (err: any) {
      error(err.message || 'Error communicating with AI.');
    } finally {
      setIsTyping(false);
    }
  };

  const toggleSource = (msgId: string) => {
    const newExpanded = new Set(expandedSources);
    if (newExpanded.has(msgId)) {
      newExpanded.delete(msgId);
    } else {
      newExpanded.add(msgId);
    }
    setExpandedSources(newExpanded);
  };

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-6rem)] flex flex-col py-4">
      {/* Header */}
      <div className="mb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <MessageSquare className="text-gray-900" />
          Document Q&A
        </h2>
        
        <div className="flex items-center gap-3">
          {filename && (
            <div className="text-sm text-gray-700 bg-white px-4 py-2 rounded-full border border-gray-200 flex items-center gap-2 shadow-sm">
              <FileText size={14} className="text-gray-500" />
              <span className="truncate max-w-[200px]">{filename}</span>
            </div>
          )}
          
          <div>
            <input 
              type="file" 
              ref={fileInputRef} 
              className="hidden" 
              onChange={handleFileUpload}
              accept=".pdf,.docx,.txt"
            />
            <button 
              onClick={() => fileInputRef.current?.click()}
              disabled={isIngesting}
              className="flex items-center gap-2 px-4 py-2 bg-white hover:bg-gray-50 text-gray-800 border border-gray-200 rounded-lg transition-colors text-sm font-medium disabled:opacity-50 shadow-sm"
            >
              {isIngesting ? <Loader2 size={16} className="animate-spin" /> : <Upload size={16} />}
              {documentId ? 'Change Document' : 'Upload Document'}
            </button>
          </div>
        </div>
      </div>

      {/* Status Messages removed to prefer global Toasts */}

      {/* Main Chat Area */}
      <div className="flex-1 bg-white border border-gray-200 rounded-2xl overflow-hidden shadow-sm flex flex-col relative">
        
        {/* Messages */}
        <div className="flex-1 p-4 sm:p-6 overflow-y-auto space-y-6">
          {!documentId && !isIngesting && messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-gray-500 space-y-4 animate-fade-in-up">
              <div className="w-16 h-16 rounded-full bg-gray-100 flex items-center justify-center">
                <Upload size={32} className="text-gray-400" />
              </div>
              <p className="text-gray-400">Upload a document to start chatting.</p>
            </div>
          )}

          {isIngesting && (
            <div className="h-full flex flex-col items-center justify-center text-gray-400 space-y-4 animate-fade-in-up">
              <Loader2 size={32} className="animate-spin text-gray-500" />
              <p className="text-gray-500">Reading and ingesting document...</p>
            </div>
          )}

          {messages.map((msg) => {
            const isAI = msg.role === 'ai';
            const showSources = msg.sources && msg.sources.length > 0;
            const isExpanded = expandedSources.has(msg.id);

            return (
              <div key={msg.id} className={`flex gap-3 sm:gap-4 ${isAI ? '' : 'flex-row-reverse'} animate-fade-in-up`}>
                <div className={`w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-xs font-bold text-white shadow-sm mt-1
                  ${isAI ? 'bg-gray-100 text-gray-900' : 'bg-black text-white'}`}>
                  {isAI ? 'AI' : 'U'}
                </div>
                
                <div className={`max-w-[85%] sm:max-w-[75%] flex flex-col ${isAI ? 'items-start' : 'items-end'}`}>
                  {/* Chat Bubble */}
                  <div className={`px-4 py-3 text-[15px] leading-relaxed shadow-sm
                    ${isAI 
                      ? 'bg-gray-100 text-gray-800 rounded-2xl rounded-tl-none border border-gray-200' 
                      : 'bg-black text-white rounded-2xl rounded-tr-none'
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                  </div>
                  
                  {/* Sources Section */}
                  {isAI && showSources && (
                    <div className="mt-2 w-full max-w-sm">
                      <button 
                        onClick={() => toggleSource(msg.id)}
                        className="flex items-center gap-1 text-xs text-gray-400 hover:text-gray-900 transition-colors"
                      >
                        {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                        {isExpanded ? 'Hide Sources' : `${msg.sources!.length} Source${msg.sources!.length > 1 ? 's' : ''}`}
                      </button>
                      
                      {isExpanded && (
                        <div className="mt-2 space-y-2">
                          {msg.sources!.map((source, idx) => (
                            <div key={idx} className="p-3 bg-gray-50 rounded-xl border border-gray-200 text-xs text-gray-600 shadow-inner">
                              <p className="italic leading-relaxed">"{source.content}"</p>
                              {source.page && (
                                <span className="block mt-2 font-medium text-gray-700">Page {source.page}</span>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
          
          {/* Typing Indicator */}
          {isTyping && (
            <div className="flex gap-4 animate-fade-in-up">
              <div className="w-8 h-8 rounded-full bg-gray-100 border border-gray-200 flex-shrink-0 flex items-center justify-center text-xs font-bold text-gray-700 shadow-sm mt-1">
                AI
              </div>
              <div className="bg-gray-100 px-4 py-4 rounded-2xl rounded-tl-none border border-gray-200 flex items-center gap-1 shadow-sm h-[46px]">
                <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          )}
          
          {/* Invisible div to scroll to */}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 bg-gray-50 border-t border-gray-200">
          <form onSubmit={handleSendMessage} className="relative flex items-center">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              disabled={!documentId || isTyping}
              placeholder={documentId ? "Ask a question about the document..." : "Upload a document first to start chatting"}
              className="w-full bg-white border border-gray-300 text-gray-800 rounded-xl pl-4 pr-14 py-3.5 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-gray-900 transition-all placeholder-gray-400 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
            />
            <button 
              type="submit"
              disabled={!inputValue.trim() || !documentId || isTyping}
              className="absolute right-2 p-2.5 bg-white hover:bg-gray-100 text-black rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-white shadow-md shadow-white/10"
            >
              <Send size={18} className={!inputValue.trim() || !documentId || isTyping ? 'opacity-50' : 'opacity-100'} />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Chat;
