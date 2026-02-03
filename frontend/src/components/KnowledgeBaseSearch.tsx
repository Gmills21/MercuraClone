import React, { useState, useEffect, useRef } from 'react';
import { Search, FileText, Upload, X, Brain, AlertCircle, CheckCircle } from 'lucide-react';
import { knowledgeBaseApi } from '../services/api';

interface KnowledgeBaseStatus {
  enabled: boolean;
  available: boolean;
  document_count: number;
  ai_enhanced: boolean;
  message?: string;
}

interface QueryResult {
  answer: string;
  sources: Array<{
    content: string;
    source: string;
    doc_type: string;
    relevance_score: number;
  }>;
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
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-gray-200 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-100 rounded-lg">
            <Brain className="text-purple-600" size={20} />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">Product Knowledge Base</h3>
            <p className="text-xs text-gray-500">
              {status?.document_count || 0} documents indexed
              {status?.ai_enhanced && ' • AI-enhanced'}
            </p>
          </div>
        </div>
        <button
          onClick={() => setShowUpload(!showUpload)}
          className="text-sm text-purple-600 hover:text-purple-700 flex items-center gap-1"
        >
          <Upload size={16} />
          {showUpload ? 'Cancel' : 'Add Document'}
        </button>
      </div>

      {/* Upload Panel */}
      {showUpload && (
        <div className="px-5 py-4 bg-purple-50 border-b border-purple-100">
          <form onSubmit={handleUpload} className="space-y-3">
            <div className="flex gap-3">
              <select
                value={uploadDocType}
                onChange={(e) => setUploadDocType(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white"
              >
                <option value="catalog">Product Catalog</option>
                <option value="spec_sheet">Spec Sheet</option>
                <option value="pricing">Pricing Sheet</option>
                <option value="manual">Manual/Guide</option>
                <option value="datasheet">Datasheet</option>
              </select>
              <input
                ref={inputRef}
                type="file"
                accept=".txt,.md,.pdf"
                onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                className="flex-1 text-sm file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border-0 file:bg-purple-600 file:text-white hover:file:bg-purple-700"
              />
            </div>
            <div className="flex items-center gap-3">
              <button
                type="submit"
                disabled={!uploadFile || uploading}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed hover:bg-purple-700"
              >
                {uploading ? 'Uploading...' : 'Upload & Index'}
              </button>
              {uploadSuccess && (
                <span className="text-sm text-green-600 flex items-center gap-1">
                  <CheckCircle size={16} />
                  Document indexed!
                </span>
              )}
            </div>
            <p className="text-xs text-gray-500">
              Note: For PDFs and images, OCR preprocessing required before upload.
            </p>
          </form>
        </div>
      )}

      {/* Search */}
      <div className="p-5">
        <form onSubmit={handleSearch} className="relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask about products, specs, pricing... (e.g., 'What's the lead time on XT-400 valves?')"
            className="w-full pl-11 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500"
          />
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="absolute right-2 top-1/2 -translate-y-1/2 px-4 py-1.5 bg-purple-600 text-white text-sm font-medium rounded-lg disabled:opacity-50 hover:bg-purple-700"
          >
            {loading ? 'Searching...' : 'Ask'}
          </button>
        </form>

        {/* Results */}
        {result && (
          <div className="mt-5 space-y-4">
            {/* Answer */}
            <div className="bg-purple-50 border border-purple-200 rounded-xl p-4">
              <div className="flex items-center gap-2 mb-2">
                <Brain size={16} className="text-purple-600" />
                <span className="text-sm font-medium text-purple-900">Answer</span>
                <span className={`text-xs px-2 py-0.5 rounded-full ${
                  result.confidence >= 0.7 ? 'bg-green-100 text-green-700' :
                  result.confidence >= 0.4 ? 'bg-amber-100 text-amber-700' :
                  'bg-red-100 text-red-700'
                }`}>
                  {Math.round(result.confidence * 100)}% confident
                </span>
              </div>
              <p className="text-gray-800 whitespace-pre-wrap">{result.answer}</p>
            </div>

            {/* Sources */}
            {result.sources.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                  <FileText size={16} />
                  Sources ({result.sources.length})
                </h4>
                <div className="space-y-2">
                  {result.sources.map((source, idx) => (
                    <div key={idx} className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-medium text-gray-600 capitalize">
                          {source.doc_type.replace('_', ' ')}
                        </span>
                        <span className="text-xs text-gray-400">
                          {Math.round(source.relevance_score * 100)}% match
                        </span>
                      </div>
                      <p className="text-sm text-gray-700 line-clamp-2">{source.content}</p>
                      <p className="text-xs text-gray-500 mt-1 truncate">{source.source}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <p className="text-xs text-gray-400 text-right">
              Query time: {result.query_time_ms}ms
            </p>
          </div>
        )}

        {/* Empty State */}
        {!result && !loading && status && status.document_count === 0 && (
          <div className="mt-8 text-center py-8">
            <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <FileText className="text-purple-400" size={32} />
            </div>
            <h4 className="font-medium text-gray-900">No documents yet</h4>
            <p className="text-sm text-gray-500 mt-1 max-w-md mx-auto">
              Upload product catalogs, spec sheets, or pricing documents to start searching with AI.
            </p>
            <button
              onClick={() => setShowUpload(true)}
              className="mt-4 text-purple-600 text-sm font-medium hover:text-purple-700"
            >
              Upload your first document →
            </button>
          </div>
        )}

        {/* Example Questions */}
        {!result && !loading && status && status.document_count > 0 && (
          <div className="mt-6 pt-6 border-t border-gray-200">
            <p className="text-xs text-gray-500 mb-2">Try asking:</p>
            <div className="flex flex-wrap gap-2">
              {['What is the lead time on XT-400?', 'Do we have stainless steel fittings?', 'What is the price break for 100 units?', 'What are the specs for valve ABC-123?'].map((q) => (
                <button
                  key={q}
                  onClick={() => {
                    setQuery(q);
                    inputRef.current?.focus();
                  }}
                  className="text-xs px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-full transition-colors"
                >
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
