import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Users, Search, Filter, Plus, Mail, Phone,
    Building, ChevronRight, Zap, ExternalLink
} from 'lucide-react';
import { customersApi } from '../services/api';

export const Customers = () => {
    const navigate = useNavigate();
    const [customers, setCustomers] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');

    useEffect(() => {
        loadCustomers();
    }, []);

    const loadCustomers = async () => {
        try {
            const res = await customersApi.list();
            setCustomers(res.data || []);
        } catch (error) {
            console.error('Failed to load customers:', error);
        } finally {
            setLoading(false);
        }
    };

    const filteredCustomers = customers.filter(c =>
        (c.name?.toLowerCase().includes(search.toLowerCase())) ||
        (c.company?.toLowerCase().includes(search.toLowerCase())) ||
        (c.email?.toLowerCase().includes(search.toLowerCase()))
    );

    return (
        <div className="min-h-screen bg-gray-50/50">
            {/* Header */}
            <div className="bg-white border-b border-gray-200">
                <div className="max-w-7xl mx-auto px-8 py-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-2xl font-semibold text-gray-900">Customers</h1>
                            <p className="text-gray-600 mt-1">Manage relationships and view performance intelligence</p>
                        </div>
                        <button
                            className="inline-flex items-center gap-2 px-4 py-2 bg-orange-600 !text-white font-medium rounded-lg hover:bg-orange-700 transition-colors shadow-sm"
                            disabled
                        >
                            <Plus size={18} />
                            Add Customer
                        </button>
                    </div>
                </div>
            </div>

            <div className="max-w-7xl mx-auto px-8 py-8">
                {/* Search and Filters */}
                <div className="flex items-center gap-4 mb-6">
                    <div className="relative flex-1 max-w-md">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                        <input
                            type="text"
                            placeholder="Search by name, company, or email..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            className="w-full pl-10 pr-4 py-2 bg-white border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 transition-all"
                        />
                    </div>
                    <button className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 text-gray-700 transition-colors shadow-sm">
                        <Filter size={18} />
                        Filter
                    </button>
                </div>

                {/* Table Content */}
                <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
                    {loading ? (
                        <div className="p-12 text-center">
                            <div className="animate-spin rounded-full h-8 w-8 border-2 border-orange-500 border-t-transparent mx-auto mb-4"></div>
                            <p className="text-gray-500">Loading your customer base...</p>
                        </div>
                    ) : filteredCustomers.length === 0 ? (
                        <div className="p-12 text-center">
                            <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
                                <Users className="text-gray-300" size={32} />
                            </div>
                            <h3 className="text-lg font-medium text-gray-900 mb-2">No customers found</h3>
                            <p className="text-gray-600">
                                {search ? `No results for "${search}"` : "You haven't added any customers yet."}
                            </p>
                        </div>
                    ) : (
                        <table className="w-full border-collapse">
                            <thead>
                                <tr className="bg-gray-50 border-b border-gray-200">
                                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Customer</th>
                                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Contact</th>
                                    <th className="px-6 py-4 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">Company</th>
                                    <th className="px-6 py-4 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                                {filteredCustomers.map((customer) => (
                                    <tr key={customer.id} className="hover:bg-orange-50/30 transition-colors group">
                                        <td className="px-6 py-4">
                                            <div className="flex items-center gap-3">
                                                <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center text-orange-600 font-bold">
                                                    {customer.name?.charAt(0) || 'C'}
                                                </div>
                                                <div>
                                                    <div className="font-medium text-gray-900">{customer.name}</div>
                                                    <div className="text-xs text-gray-400">ID: {customer.id?.slice(0, 8)}</div>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="space-y-1">
                                                {customer.email && (
                                                    <div className="flex items-center gap-2 text-sm text-gray-600">
                                                        <Mail size={14} className="text-gray-400" />
                                                        {customer.email}
                                                    </div>
                                                )}
                                                {customer.phone && (
                                                    <div className="flex items-center gap-2 text-sm text-gray-600">
                                                        <Phone size={14} className="text-gray-400" />
                                                        {customer.phone}
                                                    </div>
                                                )}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-sm text-gray-600">
                                            <div className="flex items-center gap-2">
                                                <Building size={16} className="text-gray-400" />
                                                {customer.company || 'Private Individual'}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <div className="flex items-center justify-end gap-2">
                                                <button
                                                    onClick={() => navigate(`/intelligence/customers/${customer.id}`)}
                                                    className="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
                                                    title="View Intelligence"
                                                >
                                                    <Zap size={14} />
                                                    Intelligence
                                                </button>
                                                <button
                                                    onClick={() => navigate(`/quotes/new?customer=${customer.id}`)}
                                                    className="p-1.5 text-gray-400 hover:text-orange-600 hover:bg-orange-50 rounded-md transition-all"
                                                    title="New Quote"
                                                >
                                                    <Plus size={18} />
                                                </button>
                                                <ChevronRight className="text-gray-300 group-hover:text-gray-500 transition-colors" size={20} />
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Customers;
