import React from 'react';
import { KnowledgeBaseSearch } from '../components/KnowledgeBaseSearch';
import { BookOpen, Info } from 'lucide-react';

export const KnowledgeBasePage: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Product Knowledge Base</h1>
          <p className="text-gray-500 mt-1">
            AI-powered search across your product catalogs, spec sheets, and pricing documents
          </p>
        </div>
      </div>

      {/* Info Card */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-4">
        <div className="flex items-start gap-3">
          <Info className="text-blue-600 mt-0.5" size={18} />
          <div className="text-sm text-blue-800">
            <p className="font-medium">How it works</p>
            <p className="mt-1">
              Upload your product documentation and ask natural language questions like 
              "What's the lead time on XT-400 valves?" or "Do we have stainless steel fittings in stock?"
            </p>
            <p className="mt-2 text-xs text-blue-600">
              This is an optional feature. If disabled, the rest of OpenMercura works perfectly without it.
            </p>
          </div>
        </div>
      </div>

      {/* Main Search Component */}
      <KnowledgeBaseSearch />

      {/* Use Cases */}
      <div className="grid md:grid-cols-3 gap-4">
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center mb-3">
            <BookOpen className="text-purple-600" size={20} />
          </div>
          <h3 className="font-medium text-gray-900">Product Catalogs</h3>
          <p className="text-sm text-gray-500 mt-1">
            Upload supplier catalogs and instantly find product details, SKUs, and availability.
          </p>
        </div>

        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mb-3">
            <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h3 className="font-medium text-gray-900">Spec Sheets</h3>
          <p className="text-sm text-gray-500 mt-1">
            Technical specs, dimensions, pressure ratings - all searchable in natural language.
          </p>
        </div>

        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center mb-3">
            <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="font-medium text-gray-900">Pricing Sheets</h3>
          <p className="text-sm text-gray-500 mt-1">
            Volume discounts, customer-specific pricing, and price breaks - instantly accessible.
          </p>
        </div>
      </div>
    </div>
  );
};
