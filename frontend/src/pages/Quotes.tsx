import React, { useEffect, useState } from 'react';
import { quotesApi } from '../services/api';
import { Link, useNavigate } from 'react-router-dom';
import { FileText, Plus, Search } from 'lucide-react';

export const Quotes = () => {
    const navigate = useNavigate();
    const [quotes, setQuotes] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        quotesApi.list()
            .then(res => setQuotes(res.data))
            .catch(console.error)
            .finally(() => setLoading(false));
    }, []);

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-white">Quotes</h1>
                    <p className="text-slate-400">Manage your sales quotes</p>
                </div>
                <Link to="/quotes/new" className="btn-primary flex items-center gap-2">
                    <Plus size={18} /> New Quote
                </Link>
            </div>

            <div className="glass-panel rounded-2xl overflow-hidden">
                <div className="p-4 border-b border-slate-700/50 flex items-center gap-4">
                    <div className="relative flex-1 max-w-md">
                        <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                        <input type="text" placeholder="Search quotes..." className="input-field w-full pl-10" />
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead>
                            <tr className="bg-slate-800/30 text-slate-400 border-b border-slate-700/50">
                                <th className="px-6 py-4">Quote Number</th>
                                <th className="px-6 py-4">Customer</th>
                                <th className="px-6 py-4">Total Amount</th>
                                <th className="px-6 py-4">Status</th>
                                <th className="px-6 py-4">Created At</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/50">
                            {loading ? (
                                <tr><td colSpan={5} className="text-center py-8 text-slate-500">Loading...</td></tr>
                            ) : quotes.length === 0 ? (
                                <tr><td colSpan={5} className="text-center py-8 text-slate-500">No quotes found.</td></tr>
                            ) : (
                                quotes.map((quote) => (
                                    <tr 
                                        key={quote.id} 
                                        onClick={() => navigate(`/quotes/${quote.id}`)}
                                        className="group hover:bg-slate-800/30 transition-colors cursor-pointer"
                                    >
                                        <td className="px-6 py-4 font-medium text-white">{quote.quote_number}</td>
                                        <td className="px-6 py-4 text-slate-300">{quote.customers?.name || 'Unknown'}</td>
                                        <td className="px-6 py-4 text-white font-medium">${quote.total_amount}</td>
                                        <td className="px-6 py-4">
                                            <span className="px-2.5 py-1 rounded-full text-xs font-medium bg-blue-500/10 text-blue-400 border border-blue-500/20 capitalize">
                                                {quote.status.replace('_', ' ')}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-slate-400">
                                            {new Date(quote.created_at).toLocaleDateString()}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};
