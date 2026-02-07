import React, { useState, useEffect, useRef } from 'react';
import { Search, FileText, Upload, Brain, CheckCircle, ChevronRight, FileCheck, AlertCircle } from 'lucide-react';
import { knowledgeBaseApi } from '../services/api';

interface KnowledgeBaseStatus {
  enabled: boolean;
  available: boolean;
  document_count: number;
  ai_enhanced: boolean;
  message?: string;
}

interface Source {
  content: string;
  source: string;
  doc_type: string;
  relevance_score: number;
  page?: number;
}

interface QueryResult {
  answer: string;
  sources: Source[];
  confidence: number;
  query_time_ms: number;
}

export const KnowledgeBaseSearch: React.FC = () => {
  const [status, setStatus] = useState<KnowledgeBaseStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState('');
  const [result, setResult] = useState<QueryResult | null>(null);
  const [showUpload, setShowUpload] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadDocType, setUploadDocType] = useState('catalog');
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    checkStatus();
  }, []);

  const checkStatus = async () => {
    try {
      const response = await knowledgeBaseApi.getStatus();
      setStatus(response.data);
    } catch (e) {
      setStatus({
        enabled: false,
        available: false,
        document_count: 0,
        ai_enhanced: false,
        message: 'Knowledge base service unavailable'
      });
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setResult(null);

    try {
      const response = await knowledgeBaseApi.query(query);
      setResult(response.data);
    } catch (e) {
      console.error('Query failed:', e);
    } finally {
      setLoading(false);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) return;

    setUploading(true);
    setUploadSuccess(false);

    try {
      await knowledgeBaseApi.ingest(uploadFile, uploadDocType);
      setUploadSuccess(true);
      setUploadFile(null);
      if (inputRef.current) inputRef.current.value = '';
      checkStatus(); // Refresh count
      setTimeout(() => setUploadSuccess(false), 3000);
    } catch (e) {
      console.error('Upload failed:', e);
    } finally {
      setUploading(false);
    }
  };

  // Don't render if KB is not enabled
  if (status && !status.enabled && !status.available) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-xl p-6">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-gray-200 rounded-lg">
            <Brain className="text-gray-400" size={24} />
          </div>
          <div className="flex-1">
            <h3 className="font-semibold text-gray-700">Product Knowledge Base</h3>
            <p className="text-sm text-gray-500 mt-1">
              Optional feature for searching product catalogs, spec sheets, and pricing docs.
            </p>
            <div className="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-lg">
              <p className="text-sm text-amber-800">
                <AlertCircle size={16} className="inline mr-1" />
                To enable: Set <code className="bg-amber-100 px-1 rounded">KNOWLEDGE_BASE_ENABLED=true</code> and install dependencies.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm transition-all duration-300 hover:shadow-md">
      {/* Header */}
      <div className="px-6 py-5 border-b border-gray-100 bg-gradient-to-r from-gray-50 to-white flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-gradient-to-br from-orange-500 to-orange-600 rounded-lg shadow-sm text-white">
            <Brain size={20} />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 leading-tight">Technical Knowledge Base</h3>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-xs font-medium text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
                SME Engine Active
              </span>
              <span className="text-xs text-gray-400">
                {status?.document_count || 0} docs indexed
              </span>
            </div>
          </div>
        </div>
        <button
          onClick={() => setShowUpload(!showUpload)}
          className="text-sm font-medium text-orange-600 hover:text-orange-700 hover:bg-orange-50 px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5"
        >
          <Upload size={16} />
          {showUpload ? 'Close' : 'Add Catalog'}
        </button>
      </div>

      {/* Upload Panel */}
      {showUpload && (
        <div className="px-6 py-5 bg-orange-50/50 border-b border-orange-100 animate-in slide-in-from-top-2">
          <form onSubmit={handleUpload} className="space-y-4">
            <div className="flex flex-col sm:flex-row gap-3">
              <select
                value={uploadDocType}
                onChange={(e) => setUploadDocType(e.target.value)}
                className="px-3 py-2.5 border border-orange-200 rounded-lg text-sm bg-white focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 outline-none"
              >
                <option value="catalog">Product Catalog</option>
                <option value="spec_sheet">Technical Spec Sheet</option>
                <option value="pricing">Pricing Matrix</option>
                <option value="manual">Installation Manual</option>
              </select>
              <input
                ref={inputRef}
                type="file"
                accept=".txt,.md,.pdf"
                onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                className="flex-1 text-sm file:mr-3 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-orange-500 file:text-white file:font-medium hover:file:bg-orange-600 transition-colors cursor-pointer"
              />
            </div>
            <div className="flex items-center gap-3">
              <button
                type="submit"
                disabled={!uploadFile || uploading}
                className="px-5 py-2.5 bg-orange-600 text-white rounded-lg text-sm font-medium shadow-sm hover:shadow hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                {uploading ? 'Ingesting...' : 'Upload & Index'}
              </button>
              {uploadSuccess && (
                <span className="text-sm text-green-700 flex items-center gap-1.5 font-medium bg-green-50 px-3 py-1.5 rounded-lg border border-green-200">
                  <CheckCircle size={16} />
                  Knowledge successfully integrated
                </span>
              )}
            </div>
            <p className="text-xs text-gray-500">
              Note: PDFs are processed securely. Page numbers and technical tables are preserved.
            </p>
          </form>
        </div>
      )}

      {/* Main Content Area */}
      <div className="p-6">
        {/* Search Bar */}
        <form onSubmit={handleSearch} className="relative max-w-2xl mx-auto mb-8">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <Search className="text-gray-400 group-focus-within:text-orange-500 transition-colors" size={20} />
          </div>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask a technical question... (e.g., 'What is the specific pressure rating for Nitra cylinders?')"
            className="w-full pl-11 pr-24 py-3.5 border border-gray-200 rounded-xl bg-gray-50/50 focus:bg-white focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 outline-none transition-all shadow-sm text-gray-900 placeholder:text-gray-400"
          />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="absolute right-2 top-1.5 px-4 py-2 bg-orange-600 text-white text-sm font-medium rounded-lg shadow-sm hover:bg-orange-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {loading ? 'Analyzing...' : 'Ask SME'}
          </button>
        </form>

        {/* Results - Side by Side Layout for Grade A Trust Signal */}
        {result && (
          <div className="grid lg:grid-cols-2 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500">

            {/* Left Column: AI Answer */}
            <div className="bg-gradient-to-br from-white to-gray-50 border border-gray-200 rounded-xl p-6 shadow-sm">
              <div className="flex items-center gap-2.5 mb-4 pb-4 border-b border-gray-100">
                <Brain size={18} className="text-orange-600" />
                <h4 className="font-semibold text-gray-900">SME Insight</h4>
                <div className={`ml-auto text-xs font-semibold px-2.5 py-1 rounded-full border ${result.confidence >= 0.7
                    ? 'bg-green-50 text-green-700 border-green-200'
                    : result.confidence >= 0.4
                      ? 'bg-amber-50 text-amber-700 border-amber-200'
                      : 'bg-red-50 text-red-700 border-red-200'
                  }`}>
                  {Math.round(result.confidence * 100)}% Confidence
                </div>
              </div>

              <div className="prose prose-sm prose-orange max-w-none">
                <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                  {result.answer}
                </p>
              </div>
            </div>

            {/* Right Column: Evidence & Citations */}
            <div className="space-y-4">
              <div className="flex items-center justify-between px-1">
                <h4 className="text-sm font-semibold text-gray-500 uppercase tracking-wider flex items-center gap-2">
                  <FileCheck size={16} />
                  Technical Evidence
                </h4>
                <span className="text-xs text-gray-400">
                  {result.sources.length} sources found
                </span>
              </div>

              <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
                {result.sources.map((source, idx) => (
                  <div
                    key={idx}
                    className="group bg-white border border-gray-200 rounded-xl p-4 hover:border-orange-300 hover:shadow-md transition-all duration-200"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div className="p-1.5 bg-blue-50 text-blue-600 rounded">
                          <FileText size={14} />
                        </div>
                        <span className="text-xs font-semibold text-gray-700 truncate max-w-[200px]" title={source.source}>
                          {source.source}
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        {source.page && (
                          <span className="text-xs font-mono font-medium text-gray-500 bg-gray-100 px-1.5 py-0.5 rounded border border-gray-200">
                            Page {source.page}
                          </span>
                        )}
                        {source.relevance_score > 0.7 && (
                          <span className="bg-green-100 text-green-700 text-[10px] font-bold px-1.5 py-0.5 rounded uppercase">
                            Match
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="relative pl-3 border-l-2 border-orange-200">
                      <p className="text-xs text-gray-600 leading-relaxed line-clamp-4 group-hover:line-clamp-none transition-all">
                        {/* Highlight key terms? For now just show text */}
                        "{source.content}"
                      </p>
                    </div>

                    <div className="mt-3 flex items-center justify-end">
                      <button className="text-[10px] font-medium text-orange-600 flex items-center gap-0.5 hover:underline opacity-0 group-hover:opacity-100 transition-opacity">
                        View Full Spec <ChevronRight size={10} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Empty State / Suggestions */}
        {!result && !loading && (
          <div className="mt-8 text-center pb-6">
            <div className="inline-flex items-center justify-center p-4 bg-orange-50 rounded-full mb-4">
              <Brain className="text-orange-400" size={32} />
            </div>
            <h4 className="text-lg font-medium text-gray-900">Unlock your Product Data</h4>
            <p className="text-gray-500 max-w-md mx-auto mt-2 mb-8">
              The Knowledge Base analyzes your technical documents to answer complex quoting questions instantly.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-2xl mx-auto">
              {[
                'What is the pressure rating for Nitra cylinders?',
                'Lead time for XT-400 valves?',
                'Price break for 100 units of SKU ABC?',
                'Do we have stainless steel fittings in stock?'
              ].map((q) => (
                <button
                  key={q}
                  onClick={() => {
                    setQuery(q);
                    inputRef.current?.focus();
                  }}
                  className="text-left p-3 text-sm text-gray-600 bg-white border border-gray-200 rounded-xl hover:border-orange-300 hover:shadow-sm transition-all"
                >
                  <span className="block text-xs font-medium text-orange-600 mb-0.5">Ask SME:</span>
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

