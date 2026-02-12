import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Search, Filter, ArrowRight, FileText } from 'lucide-react';
import { quotesApi } from '../services/api';

const statusBadge = (status: string) => {
  const styles: any = {
    draft: 'bg-gray-100 text-gray-700',
    pending_approval: 'bg-orange-50 text-orange-700',
    approved: 'bg-indigo-50 text-indigo-700',
    sent: 'bg-blue-50 text-blue-700',
    accepted: 'bg-emerald-50 text-emerald-700',
    rejected: 'bg-red-50 text-red-700',
    expired: 'bg-amber-50 text-amber-700',
  };
  return (
    <span className={`inline-flex px-2.5 py-1 text-xs font-medium rounded ${styles[status] || styles.draft}`}>
      {status}
    </span>
  );
};

export const Quotes = () => {
  const [quotes, setQuotes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');

  useEffect(() => {
    loadQuotes();
  }, []);

  const loadQuotes = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await quotesApi.list(50);
      setQuotes(res.data || []);
    } catch (err) {
      console.error('Failed to load quotes:', err);
      setError('Unable to load quotes. Check that the backend is running and try again.');
    } finally {
      setLoading(false);
    }
  };

  const filteredQuotes = quotes.filter(q =>
    q.customer_name?.toLowerCase().includes(search.toLowerCase()) ||
    q.token?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-gray-900">Quotes</h1>
              <p className="text-gray-600 mt-1">Manage and track customer quotes</p>
            </div>
            <Link
              to="/quotes/new"
              className="inline-flex items-center gap-2 px-4 py-2 bg-white text-orange-600 font-medium rounded-lg border border-orange-200 hover:bg-orange-50 transition-all shadow-sm active:scale-[0.98]"
            >
              <Plus size={18} className="text-orange-600" />
              <span>New Request</span>
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-8 py-8">
        {/* Filters */}
        <div className="flex items-center gap-4 mb-6">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" size={18} />
            <input
              type="text"
              placeholder="Search quotes..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-shadow outline-none"
            />
          </div>
          <button className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700">
            <Filter size={18} />
            Filter
          </button>
        </div>

        {/* Quotes Table */}
        {loading ? (
          <div className="bg-white border border-gray-200 rounded-lg p-12 text-center text-gray-500">
            Loading quotes...
          </div>
        ) : error ? (
          <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
            <p className="text-red-600 mb-4">{error}</p>
            <button
              onClick={loadQuotes}
              className="inline-flex items-center gap-2 px-6 py-2.5 bg-orange-600 text-white font-medium rounded-lg hover:bg-orange-700 transition-all shadow-md active:scale-[0.98]"
            >
              Retry
            </button>
          </div>
        ) : filteredQuotes.length === 0 ? (
          <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
            {/* Hero empty state with drag-drop zone */}
            <div className="p-12 text-center bg-gradient-to-b from-orange-50/50 to-white">
              <div className="max-w-md mx-auto">
                <div className="w-16 h-16 bg-orange-100 rounded-2xl flex items-center justify-center mx-auto mb-6">
                  <FileText className="h-8 w-8 text-orange-600" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">No quotes yet</h3>
                <p className="text-gray-600 mb-8">Upload your first RFQ and let AI extract products, quantities, and pricing automatically.</p>

                {/* Drop Zone */}
                <Link
                  to="/quotes/new"
                  className="block border-2 border-dashed border-orange-200 hover:border-orange-400 rounded-xl p-8 transition-all hover:bg-orange-50/50 group cursor-pointer"
                >
                  <div className="flex flex-col items-center gap-3 text-gray-500 group-hover:text-orange-600 transition-colors">
                    <div className="w-12 h-12 bg-orange-100 group-hover:bg-orange-200 rounded-full flex items-center justify-center transition-colors">
                      <Plus size={24} className="text-orange-600" />
                    </div>
                    <div>
                      <p className="font-semibold text-gray-900 group-hover:text-orange-700">Create a New Request</p>
                      <p className="text-sm text-gray-500 mt-1">PDF, Excel, CSV, or paste text</p>
                    </div>
                  </div>
                </Link>

                {/* Quick Stats */}
                <div className="flex justify-center gap-6 mt-8 text-sm text-gray-500">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span>AI-powered extraction</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <span>Auto-match products</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Quote #</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Customer</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Project</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Amount</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Assignee</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Date</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredQuotes.map((quote) => (
                  <tr key={quote.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm font-medium text-gray-900">
                      #{quote.token?.slice(0, 8)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {quote.customer_name || 'Unknown'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-600 italic">
                      {quote.project_name || '—'}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900 font-medium">
                      ${quote.total?.toFixed(2) || '0.00'}
                    </td>
                    <td className="px-6 py-4">
                      {quote.assignee_name ? (
                        <div className="flex items-center gap-2">
                          <div className="w-6 h-6 rounded-full bg-orange-100 text-orange-600 flex items-center justify-center text-[10px] font-bold">
                            {quote.assignee_name.split(' ').map((n: string) => n[0]).join('').toUpperCase()}
                          </div>
                          <span className="text-sm text-gray-700">{quote.assignee_name}</span>
                        </div>
                      ) : (
                        <span className="text-sm text-gray-400">Unassigned</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      {statusBadge(quote.status)}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {new Date(quote.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4">
                      <Link
                        to={`/quotes/${quote.id}`}
                        className="text-sm font-medium text-orange-600 hover:text-orange-700"
                      >
                        View →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default Quotes;
