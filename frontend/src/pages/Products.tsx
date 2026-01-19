import React, { useState } from 'react';
import { productsApi } from '../services/api';
import { Upload, Search, CheckCircle, AlertTriangle } from 'lucide-react';

export const Products = () => {
    const [file, setFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);
    
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<any[]>([]);
    const [searching, setSearching] = useState(false);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
            setMessage(null);
        }
    };

    const handleUpload = async () => {
        if (!file) return;
        
        try {
            setUploading(true);
            setMessage(null);
            const res = await productsApi.upload(file);
            setMessage({ type: 'success', text: res.data.message });
            setFile(null);
            // Reset file input value if possible, or just rely on state
        } catch (error: any) {
            console.error('Upload failed:', error);
            setMessage({ 
                type: 'error', 
                text: error.response?.data?.detail || 'Failed to upload catalog.' 
            });
        } finally {
            setUploading(false);
        }
    };

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!searchQuery.trim()) return;

        try {
            setSearching(true);
            const res = await productsApi.search(searchQuery);
            setSearchResults(res.data);
        } catch (error) {
            console.error('Search failed:', error);
        } finally {
            setSearching(false);
        }
    };

    return (
        <div className="space-y-6 animate-fade-in">
            <h1 className="text-2xl font-bold text-white">Products Catalog</h1>
            
            {/* Import Section */}
            <div className="glass-panel rounded-2xl p-6">
                <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <Upload size={20} /> Import Catalog
                </h2>
                <div className="flex items-center gap-4">
                    <input 
                        type="file" 
                        accept=".csv,.xlsx,.xls"
                        onChange={handleFileChange}
                        className="block w-full text-sm text-slate-400
                            file:mr-4 file:py-2 file:px-4
                            file:rounded-full file:border-0
                            file:text-sm file:font-semibold
                            file:bg-slate-800 file:text-blue-400
                            hover:file:bg-slate-700
                            cursor-pointer"
                    />
                    <button 
                        onClick={handleUpload}
                        disabled={!file || uploading}
                        className="btn-primary whitespace-nowrap"
                    >
                        {uploading ? 'Uploading...' : 'Upload File'}
                    </button>
                </div>
                {message && (
                    <div className={`mt-4 p-3 rounded-lg flex items-center gap-2 text-sm ${
                        message.type === 'success' ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'
                    }`}>
                        {message.type === 'success' ? <CheckCircle size={16} /> : <AlertTriangle size={16} />}
                        {message.text}
                    </div>
                )}
                <p className="mt-4 text-xs text-slate-500">
                    Supported formats: CSV, Excel (XLSX). Columns: SKU, Name, Price, Category, Supplier.
                </p>
            </div>

            {/* Search Section */}
            <div className="glass-panel rounded-2xl p-6">
                <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <Search size={20} /> Search Catalog
                </h2>
                <form onSubmit={handleSearch} className="flex gap-2 mb-6">
                    <input 
                        type="text" 
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Search by SKU or Name..."
                        className="input-field flex-1"
                    />
                    <button type="submit" className="btn-secondary" disabled={searching}>
                        {searching ? 'Searching...' : 'Search'}
                    </button>
                </form>

                {searchResults.length > 0 ? (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm">
                            <thead>
                                <tr className="text-slate-400 border-b border-slate-700/50">
                                    <th className="px-4 py-2">SKU</th>
                                    <th className="px-4 py-2">Name</th>
                                    <th className="px-4 py-2">Price</th>
                                    <th className="px-4 py-2">Category</th>
                                    <th className="px-4 py-2">Supplier</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800/50">
                                {searchResults.map((item: any) => (
                                    <tr key={item.id} className="hover:bg-slate-800/30">
                                        <td className="px-4 py-3 text-slate-300">{item.sku}</td>
                                        <td className="px-4 py-3 text-slate-300">{item.item_name}</td>
                                        <td className="px-4 py-3 text-slate-300">${item.expected_price?.toFixed(2)}</td>
                                        <td className="px-4 py-3 text-slate-400">{item.category || '-'}</td>
                                        <td className="px-4 py-3 text-slate-400">{item.supplier || '-'}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div className="text-center text-slate-500 py-8">
                        {searching ? 'Searching...' : 'No results found'}
                    </div>
                )}
            </div>
        </div>
    );
};
