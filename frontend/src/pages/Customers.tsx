import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Users, Search, Filter, Plus, Mail, Phone,
    Building, ChevronRight, Zap, ExternalLink
} from 'lucide-react';
import { customersApi } from '../services/api';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "../components/ui/table";
import { Button } from "../components/ui/button";

export const Customers = () => {
    const navigate = useNavigate();
    const [customers, setCustomers] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [search, setSearch] = useState('');

    useEffect(() => {
        loadCustomers();
    }, []);

    const loadCustomers = async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await customersApi.list();
            setCustomers(res.data || []);
        } catch (err) {
            console.error('Failed to load customers:', err);
            setError('Unable to load customers. Check that the backend is running and try again.');
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
        <div className="space-y-8">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 tracking-tight">Customers</h1>
                    <p className="text-gray-500 mt-2 text-lg">Manage relationships and intelligent data.</p>
                </div>
                <Button
                    onClick={() => navigate('/quotes/new')}
                    className="bg-orange-600 hover:bg-orange-700 text-white shadow-lg hover:shadow-orange-500/20 transition-all rounded-xl px-6"
                >
                    <Plus className="mr-2 h-4 w-4" /> Add Customer
                </Button>
            </div>

            {/* Content Card */}
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                {/* Toolbar */}
                <div className="p-6 border-b border-gray-100 flex flex-col md:flex-row gap-4 justify-between items-center">
                    <div className="relative w-full md:w-96">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 h-4 w-4" />
                        <input
                            type="text"
                            placeholder="Search customers..."
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            className="w-full pl-10 pr-4 py-2.5 bg-gray-50/50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 transition-all"
                        />
                    </div>
                    <div className="flex gap-2">
                        <Button variant="outline" className="text-gray-600 border-gray-200 rounded-xl">
                            <Filter className="mr-2 h-4 w-4" /> Filter
                        </Button>
                    </div>
                </div>

                {/* Table */}
                <div className="relative">
                    {loading ? (
                        <div className="p-12 flex justify-center">
                            <div className="animate-spin rounded-full h-8 w-8 border-2 border-orange-500 border-t-transparent" />
                        </div>
                    ) : error ? (
                        <div className="p-12 text-center">
                            <p className="text-red-600 mb-4">{error}</p>
                            <Button onClick={loadCustomers} className="bg-orange-600 hover:bg-orange-700 text-white">
                                Retry
                            </Button>
                        </div>
                    ) : filteredCustomers.length === 0 ? (
                        <div className="p-16 text-center">
                            <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
                                <Users className="text-gray-300" size={24} />
                            </div>
                            <h3 className="text-lg font-medium text-gray-900">No customers found</h3>
                            <p className="text-gray-500 mt-1">Try adjusting your search terms.</p>
                        </div>
                    ) : (
                        <Table>
                            <TableHeader className="bg-gray-50/50">
                                <TableRow>
                                    <TableHead className="pl-6 w-[300px] py-4 text-xs uppercase tracking-wider font-semibold text-gray-500">Customer Details</TableHead>
                                    <TableHead className="py-4 text-xs uppercase tracking-wider font-semibold text-gray-500">Contact Info</TableHead>
                                    <TableHead className="py-4 text-xs uppercase tracking-wider font-semibold text-gray-500">Company</TableHead>
                                    <TableHead className="text-right pr-6 py-4 text-xs uppercase tracking-wider font-semibold text-gray-500">Actions</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {filteredCustomers.map((customer) => (
                                    <TableRow key={customer.id} className="group hover:bg-gray-50/50 transition-colors cursor-pointer border-b border-gray-100 last:border-0">
                                        <TableCell className="pl-6 py-4">
                                            <div className="flex items-center gap-4">
                                                <div className="w-10 h-10 rounded-xl bg-orange-100 flex items-center justify-center text-orange-700 font-bold text-sm">
                                                    {customer.name?.charAt(0) || 'C'}
                                                </div>
                                                <div>
                                                    <div className="font-semibold text-gray-900">{customer.name}</div>
                                                    <div className="text-xs text-gray-500 font-mono mt-0.5">ID: {customer.id?.slice(0, 8)}</div>
                                                </div>
                                            </div>
                                        </TableCell>
                                        <TableCell>
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
                                        </TableCell>
                                        <TableCell>
                                            <div className="flex items-center gap-2 text-sm text-gray-600">
                                                <Building size={14} className="text-gray-400" />
                                                {customer.company || 'Private Individual'}
                                            </div>
                                        </TableCell>
                                        <TableCell className="text-right pr-6">
                                            <div className="flex items-center justify-end gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        navigate(`/intelligence/customers/${customer.id}`);
                                                    }}
                                                    className="text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg h-8 px-3"
                                                >
                                                    <Zap size={14} className="mr-1.5" />
                                                    Intelligence
                                                </Button>
                                                <Button
                                                    variant="ghost"
                                                    size="icon"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        navigate(`/quotes/new?customer=${customer.id}`);
                                                    }}
                                                    className="text-gray-400 hover:text-orange-600 hover:bg-orange-50 rounded-lg w-8 h-8"
                                                >
                                                    <Plus size={18} />
                                                </Button>
                                                <ChevronRight className="text-gray-300" size={18} />
                                            </div>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Customers;
