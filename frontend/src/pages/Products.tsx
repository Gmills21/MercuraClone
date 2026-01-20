import React, { useState } from 'react';
import { productsApi } from '../services/api';
import { Upload, Search, CheckCircle, AlertTriangle, MessageCircle, X, Send, ArrowRight, RefreshCw } from 'lucide-react';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription, SheetTrigger } from '../components/ui/sheet';

export const Products = () => {
    const [file, setFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);
    
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState<any[]>([]);
    const [searching, setSearching] = useState(false);
    
    // Chat state
    const [chatOpen, setChatOpen] = useState(false);
    const [chatQuery, setChatQuery] = useState('');
    const [chatHistory, setChatHistory] = useState<Array<{role: 'user' | 'assistant', content: string, products?: any[]}>>([]);
    const [chatting, setChatting] = useState(false);
    
    // Competitor mapping state
    const [competitorSku, setCompetitorSku] = useState('');
    const [ourSku, setOurSku] = useState('');
    const [mappingCompetitor, setMappingCompetitor] = useState(false);

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

    const handleChat = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!chatQuery.trim() || chatting) return;

        const userMessage = chatQuery;
        setChatQuery('');
        setChatHistory([...chatHistory, { role: 'user', content: userMessage }]);
        setChatting(true);

        try {
            const res = await productsApi.chat(userMessage);
            setChatHistory([
                ...chatHistory,
                { role: 'user', content: userMessage },
                { role: 'assistant', content: res.data.response, products: res.data.products }
            ]);
        } catch (error) {
            console.error('Chat failed:', error);
            setChatHistory([
                ...chatHistory,
                { role: 'user', content: userMessage },
                { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }
            ]);
        } finally {
            setChatting(false);
        }
    };

    const handleMapCompetitor = async () => {
        if (!competitorSku.trim() || !ourSku.trim()) {
            alert('Please enter both competitor SKU and our SKU');
            return;
        }

        setMappingCompetitor(true);
        try {
            // Create a temporary CSV-like structure and upload
            const csvContent = `Competitor SKU,Our SKU\n${competitorSku},${ourSku}`;
            const blob = new Blob([csvContent], { type: 'text/csv' });
            const file = new File([blob], 'competitor_map.csv', { type: 'text/csv' });
            
            await productsApi.uploadCompetitorMap(file);
            alert('Competitor mapping added successfully!');
            setCompetitorSku('');
            setOurSku('');
        } catch (error: any) {
            console.error('Mapping failed:', error);
            alert(error.response?.data?.detail || 'Failed to add competitor mapping');
        } finally {
            setMappingCompetitor(false);
        }
    };

    return (
        <div className="space-y-6 animate-fade-in">
            <div className="flex items-center justify-between">
                <h1 className="text-2xl font-bold text-white">Products Catalog</h1>
                <Sheet open={chatOpen} onOpenChange={setChatOpen}>
                    <SheetTrigger asChild>
                        <button className="btn-primary flex items-center gap-2">
                            <MessageCircle size={18} />
                            Chat with Catalog
                        </button>
                    </SheetTrigger>
                    <SheetContent className="w-full sm:max-w-lg bg-slate-900 border-slate-800">
                        <SheetHeader>
                            <SheetTitle className="text-white">Catalog Chat</SheetTitle>
                            <SheetDescription className="text-slate-400">
                                Ask questions about your catalog. Try: "Do we have a cheaper 2-inch pump in stock?"
                            </SheetDescription>
                        </SheetHeader>
                        <div className="mt-6 flex flex-col h-[calc(100vh-200px)]">
                            <div className="flex-1 overflow-y-auto space-y-4 mb-4">
                                {chatHistory.length === 0 ? (
                                    <div className="text-center text-slate-500 py-8">
                                        <MessageCircle size={48} className="mx-auto mb-4 opacity-50" />
                                        <p>Start a conversation about your catalog</p>
                                        <p className="text-xs mt-2">Example: "Show me all pumps under $500"</p>
                                    </div>
                                ) : (
                                    chatHistory.map((msg, idx) => (
                                        <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                            <div className={`max-w-[80%] rounded-lg p-3 ${
                                                msg.role === 'user' 
                                                    ? 'bg-blue-500/20 text-blue-100' 
                                                    : 'bg-slate-800 text-slate-200'
                                            }`}>
                                                <div className="whitespace-pre-wrap text-sm">{msg.content}</div>
                                                {msg.products && msg.products.length > 0 && (
                                                    <div className="mt-3 space-y-2">
                                                        {msg.products.map((product: any, pIdx: number) => (
                                                            <div key={pIdx} className="p-2 bg-slate-900/50 rounded text-xs">
                                                                <div className="font-medium text-white">{product.item_name}</div>
                                                                <div className="text-slate-400">SKU: {product.sku} • ${product.expected_price?.toFixed(2)}</div>
                                                            </div>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    ))
                                )}
                                {chatting && (
                                    <div className="flex justify-start">
                                        <div className="bg-slate-800 rounded-lg p-3">
                                            <div className="flex items-center gap-2 text-slate-400 text-sm">
                                                <RefreshCw size={14} className="animate-spin" />
                                                Thinking...
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                            <form onSubmit={handleChat} className="flex gap-2">
                                <input
                                    type="text"
                                    value={chatQuery}
                                    onChange={(e) => setChatQuery(e.target.value)}
                                    placeholder="Ask about products..."
                                    className="input-field flex-1"
                                    disabled={chatting}
                                />
                                <button type="submit" disabled={chatting || !chatQuery.trim()} className="btn-primary">
                                    <Send size={18} />
                                </button>
                            </form>
                        </div>
                    </SheetContent>
                </Sheet>
            </div>
            
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
                                    <th className="px-4 py-2">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800/50">
                                {searchResults.map((item: any) => (
                                    <tr key={item.id} className="hover:bg-slate-800/30 group">
                                        <td className="px-4 py-3 text-slate-300 font-mono">{item.sku}</td>
                                        <td className="px-4 py-3 text-slate-300">{item.item_name}</td>
                                        <td className="px-4 py-3 text-slate-300">${item.expected_price?.toFixed(2)}</td>
                                        <td className="px-4 py-3 text-slate-400">{item.category || '-'}</td>
                                        <td className="px-4 py-3 text-slate-400">{item.supplier || '-'}</td>
                                        <td className="px-4 py-3">
                                            <button
                                                onClick={() => {
                                                    setCompetitorSku('');
                                                    setOurSku(item.sku);
                                                    document.getElementById('competitor-mapping')?.scrollIntoView({ behavior: 'smooth' });
                                                }}
                                                className="text-xs text-blue-400 hover:text-blue-300 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1"
                                                title="Map Competitor Part"
                                            >
                                                <ArrowRight size={12} />
                                                Map Competitor
                                            </button>
                                        </td>
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

            {/* Competitor Swap UI */}
            <div id="competitor-mapping" className="glass-panel rounded-2xl p-6">
                <h2 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                    <ArrowRight size={20} /> Map Competitor Part Numbers
                </h2>
                <p className="text-slate-400 text-sm mb-4">
                    Map competitor or customer part numbers to your internal SKUs for automatic matching in quotes.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            Competitor/Customer SKU
                        </label>
                        <input
                            type="text"
                            value={competitorSku}
                            onChange={(e) => setCompetitorSku(e.target.value)}
                            placeholder="e.g., COMP-12345"
                            className="input-field w-full"
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-2">
                            Our SKU
                        </label>
                        <input
                            type="text"
                            value={ourSku}
                            onChange={(e) => setOurSku(e.target.value)}
                            placeholder="e.g., OUR-67890"
                            className="input-field w-full"
                        />
                    </div>
                </div>
                <button
                    onClick={handleMapCompetitor}
                    disabled={mappingCompetitor || !competitorSku.trim() || !ourSku.trim()}
                    className="btn-primary flex items-center gap-2"
                >
                    {mappingCompetitor ? (
                        <>
                            <RefreshCw size={16} className="animate-spin" />
                            Mapping...
                        </>
                    ) : (
                        <>
                            <CheckCircle size={16} />
                            Add Mapping
                        </>
                    )}
                </button>
                <p className="mt-4 text-xs text-slate-500">
                    Tip: You can also bulk upload competitor mappings using the Competitor Mapping page.
                </p>
            </div>
        </div>
    );
};
