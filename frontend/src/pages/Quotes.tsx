import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Search, Filter, ArrowRight, FileText } from 'lucide-react';
import { quotesApi } from '../services/api';

const statusBadge = (status: string) => {
  const styles: any = {
    draft: 'bg-gray-100 text-gray-700',
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
  const [search, setSearch] = useState('');

  useEffect(() => {
    loadQuotes();
  }, []);

  const loadQuotes = async () => {
    try {
      const res = await quotesApi.list(50);
      setQuotes(res.data || []);
    } catch (error) {
      console.error('Failed to load quotes:', error);
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
              <span>Create Quote</span>
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
        ) : filteredQuotes.length === 0 ? (
          <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
            <FileText className="mx-auto h-12 w-12 text-gray-300 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No quotes yet</h3>
            <p className="text-gray-600 mb-4">Create your first quote to get started</p>
            <Link
              to="/quotes/new"
              className="inline-flex items-center gap-2 px-6 py-2.5 bg-orange-600 text-white font-medium rounded-lg hover:bg-orange-700 transition-all shadow-md active:scale-[0.98]"
            >
              <span className="text-white">Create Quote</span> <ArrowRight size={16} className="text-white" />
            </Link>
          </div>
        ) : (
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Quote #</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Customer</th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-600 uppercase">Amount</th>
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
                    <td className="px-6 py-4 text-sm text-gray-900 font-medium">
                      ${quote.total?.toFixed(2) || '0.00'}
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
