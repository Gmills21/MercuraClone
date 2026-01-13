import React, { useState, useEffect } from 'react';
import { Search, Plus, Trash2, Save, FileText, ChevronLeft } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { quotesApi, productsApi, customersApi } from '../services/api';

export const CreateQuote = () => {
    const navigate = useNavigate();
    const [customers, setCustomers] = useState<any[]>([]);
    const [selectedCustomerId, setSelectedCustomerId] = useState('');

    const [lineItems, setLineItems] = useState<any[]>([]);

    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<any[]>([]);
    const [isSearching, setIsSearching] = useState(false);

    useEffect(() => {
        // Load customers
        customersApi.list().then(res => setCustomers(res.data)).catch(console.error);
    }, []);

    useEffect(() => {
        // Debounced search
        const timer = setTimeout(() => {
            if (searchQuery.length > 2) {
                setIsSearching(true);
                productsApi.search(searchQuery)
                    .then(res => setSearchResults(res.data))
                    .catch(console.error)
                    .finally(() => setIsSearching(false));
            } else {
                setSearchResults([]);
            }
        }, 300);
        return () => clearTimeout(timer);
    }, [searchQuery]);

    const addItem = (product: any) => {
        setLineItems(prev => [
            ...prev,
            { ...product, product_id: product.id, quantity: 1, unit_price: product.expected_price || 0 }
        ]);
        setSearchQuery('');
        setSearchResults([]);
    };

    const updateQuantity = (index: number, qty: number) => {
        const newItems = [...lineItems];
        newItems[index].quantity = qty;
        setLineItems(newItems);
    };

    const removeItem = (index: number) => {
        setLineItems(prev => prev.filter((_, i) => i !== index));
    };

    const calculateTotal = () => {
        return lineItems.reduce((sum, item) => sum + (item.quantity * item.unit_price), 0);
    };

    const handleSave = async () => {
        try {
            if (!selectedCustomerId) {
                alert('Please select a customer');
                return;
            }
            const quoteData = {
                user_id: 'test-user', // Handled by API client header usually, but model asks for it? No model ignores if not passed? Wait, model in backend sets it.
                customer_id: selectedCustomerId,
                quote_number: `QT-${Date.now()}`,
                items: lineItems.map(item => ({
                    product_id: item.product_id,
                    sku: item.sku,
                    description: item.item_name,
                    quantity: item.quantity,
                    unit_price: item.unit_price,
                    total_price: item.quantity * item.unit_price
                })),
                total_amount: calculateTotal()
            };

            await quotesApi.create(quoteData);
            navigate('/quotes');
        } catch (e) {
            console.error(e);
            alert('Failed to save quote');
        }
    };

    return (
        <div className="space-y-6 animate-fade-in">
            <div className="flex items-center gap-4">
                <Link to="/" className="p-2 hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-white">
                    <ChevronLeft size={24} />
                </Link>
                <div>
                    <h1 className="text-2xl font-bold text-white">New Quote</h1>
                    <p className="text-slate-400 text-sm">Create a new sales quote for a customer</p>
                </div>
                <div className="ml-auto flex gap-3">
                    <button className="btn-secondary" onClick={() => navigate('/')}>Cancel</button>
                    <button className="btn-primary flex items-center gap-2" onClick={handleSave}>
                        <Save size={18} /> Save Quote
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left Column: Customer & Details */}
                <div className="space-y-6">
                    <div className="glass-panel p-6 rounded-2xl space-y-4">
                        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                            <Users size={20} className="text-primary-400" /> Customer Details
                        </h2>

                        <div className="space-y-2">
                            <label className="text-sm font-medium text-slate-300">Select Customer</label>
                            <select
                                className="w-full input-field text-slate-300"
                                value={selectedCustomerId}
                                onChange={e => setSelectedCustomerId(e.target.value)}
                            >
                                <option value="">Select a customer...</option>
                                {customers.map(c => (
                                    <option key={c.id} value={c.id}>{c.name} - {c.company}</option>
                                ))}
                            </select>
                        </div>
                    </div>
                </div>

                {/* Right Column: Line Items */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="glass-panel p-6 rounded-2xl min-h-[500px] flex flex-col">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                                <ShoppingBag size={20} className="text-primary-400" /> Line Items
                            </h2>
                            <div className="text-2xl font-bold text-white">
                                Total: ${calculateTotal().toFixed(2)}
                            </div>
                        </div>

                        {/* Product Search */}
                        <div className="relative mb-6 z-20">
                            <div className="relative">
                                <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                                <input
                                    type="text"
                                    placeholder="Search products by SKU or Name..."
                                    className="w-full input-field pl-10"
                                    value={searchQuery}
                                    onChange={e => setSearchQuery(e.target.value)}
                                />
                            </div>

                            {/* Search Results Dropdown */}
                            {(searchResults.length > 0 || isSearching) && (
                                <div className="absolute top-full left-0 right-0 mt-2 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl overflow-hidden max-h-60 overflow-y-auto">
                                    {isSearching ? (
                                        <div className="p-4 text-center text-slate-500">Searching...</div>
                                    ) : (
                                        searchResults.map(prod => (
                                            <button
                                                key={prod.id}
                                                className="w-full text-left p-3 hover:bg-slate-800 flex items-center justify-between border-b border-slate-800/50 last:border-0"
                                                onClick={() => addItem(prod)}
                                            >
                                                <div>
                                                    <p className="font-medium text-white">{prod.item_name}</p>
                                                    <p className="text-xs text-slate-400">SKU: {prod.sku}</p>
                                                </div>
                                                <span className="font-bold text-primary-400">${prod.expected_price}</span>
                                            </button>
                                        ))
                                    )}
                                </div>
                            )}
                        </div>

                        {/* Items Table */}
                        <div className="flex-1 overflow-x-auto">
                            <table className="w-full text-left text-sm">
                                <thead>
                                    <tr className="border-b border-slate-700 text-slate-400">
                                        <th className="pb-3 pl-2 w-1/2">Item</th>
                                        <th className="pb-3 w-24">Price</th>
                                        <th className="pb-3 w-24">Qty</th>
                                        <th className="pb-3 w-24 text-right">Total</th>
                                        <th className="pb-3 w-10"></th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-800/50">
                                    {lineItems.length === 0 ? (
                                        <tr>
                                            <td colSpan={5} className="py-12 text-center text-slate-500 italic">
                                                No items added yet. Search products above.
                                            </td>
                                        </tr>
                                    ) : (
                                        lineItems.map((item, idx) => (
                                            <tr key={idx} className="group hover:bg-slate-800/30">
                                                <td className="py-3 pl-2">
                                                    <p className="font-medium text-white">{item.item_name}</p>
                                                    <p className="text-xs text-slate-400">{item.sku}</p>
                                                </td>
                                                <td className="py-3 text-slate-300">${item.unit_price}</td>
                                                <td className="py-3">
                                                    <input
                                                        type="number"
                                                        min="1"
                                                        className="w-16 bg-slate-900 border border-slate-700 rounded px-2 py-1 text-center"
                                                        value={item.quantity}
                                                        onChange={(e) => updateQuantity(idx, parseInt(e.target.value))}
                                                    />
                                                </td>
                                                <td className="py-3 text-right font-medium text-white">
                                                    ${(item.quantity * item.unit_price).toFixed(2)}
                                                </td>
                                                <td className="py-3 text-right">
                                                    <button
                                                        className="text-slate-500 hover:text-rose-400 transition-colors p-1"
                                                        onClick={() => removeItem(idx)}
                                                    >
                                                        <Trash2 size={16} />
                                                    </button>
                                                </td>
                                            </tr>
                                        ))
                                    )}
                                </tbody>
                            </table>
                        </div>

                    </div>
                </div>
            </div>
        </div>
    );
};
