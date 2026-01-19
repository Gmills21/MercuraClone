import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { quotesApi, productsApi } from '../services/api';
import { Save, ChevronLeft, CheckCircle, AlertTriangle, Lightbulb, Check, Copy, TrendingDown, Info } from 'lucide-react';

export const QuoteReview = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [quote, setQuote] = useState<any>(null);
    const [lineItems, setLineItems] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    
    // Suggestions state
    const [suggestions, setSuggestions] = useState<{[key: number]: any[]}>({});
    const [showSuggestions, setShowSuggestions] = useState<{[key: number]: boolean}>({});
    const [loadingSuggestions, setLoadingSuggestions] = useState(false);

    useEffect(() => {
        if (id) {
            fetchQuote(id);
        }
    }, [id]);

    const fetchQuote = async (quoteId: string) => {
        try {
            setLoading(true);
            const res = await quotesApi.get(quoteId);
            setQuote(res.data);
            setLineItems(res.data.items || []);
            
            // Fetch suggestions if it's a draft
            if (res.data.status === 'draft' && res.data.items?.length > 0) {
                fetchSuggestions(res.data.items);
            }
        } catch (error) {
            console.error('Error fetching quote:', error);
        } finally {
            setLoading(false);
        }
    };

    const fetchSuggestions = async (items: any[]) => {
        try {
            setLoadingSuggestions(true);
            const res = await productsApi.suggest(items);
            setSuggestions(res.data.suggestions);
        } catch (error) {
            console.error('Error fetching suggestions:', error);
        } finally {
            setLoadingSuggestions(false);
        }
    };

    const updateItem = (index: number, field: string, value: any) => {
        const newItems = [...lineItems];
        newItems[index] = { ...newItems[index], [field]: value };
        
        if (field === 'quantity' || field === 'unit_price') {
             const qty = field === 'quantity' ? value : newItems[index].quantity;
             const price = field === 'unit_price' ? value : newItems[index].unit_price;
             newItems[index].total_price = Number(qty) * Number(price);
        }
        setLineItems(newItems);
    };

    const calculateTotal = () => {
        return lineItems.reduce((sum, item) => sum + (Number(item.quantity) * Number(item.unit_price)), 0);
    };

    const handleSave = async (approve = false) => {
        try {
            setSaving(true);
            const total = calculateTotal();
            
            const updateData = {
                ...quote,
                total_amount: total,
                status: approve ? 'pending_approval' : quote.status,
                items: lineItems.map(item => ({
                    ...item,
                    total_price: Number(item.quantity) * Number(item.unit_price)
                }))
            };

            await quotesApi.update(id!, updateData);
            
            if (approve) {
                navigate('/quotes');
            } else {
                fetchQuote(id!);
            }
        } catch (error) {
            console.error('Error updating quote:', error);
            alert('Failed to update quote');
        } finally {
            setSaving(false);
        }
    };

    const copyForERP = () => {
        const header = "SKU\tDescription\tQuantity\tPrice";
        const rows = lineItems.map(item => 
            `${item.sku || ''}\t${item.description || ''}\t${item.quantity || 1}\t${item.unit_price || 0}`
        ).join('\n');
        
        navigator.clipboard.writeText(`${header}\n${rows}`);
        alert("Quote copied to clipboard in ERP-ready Tab-Separated format!");
    };

    const applySuggestion = (index: number, match: any) => {
        const newItems = [...lineItems];
        newItems[index] = {
            ...newItems[index],
            sku: match.catalog_item.sku,
            description: match.catalog_item.item_name,
            unit_price: match.catalog_item.expected_price || newItems[index].unit_price,
            metadata: {
                ...newItems[index].metadata,
                matched_catalog_id: match.catalog_item.id,
                match_score: match.score,
                match_type: match.match_type
            }
        };
        // Recalculate total
        newItems[index].total_price = Number(newItems[index].quantity) * Number(newItems[index].unit_price);
        
        setLineItems(newItems);
        setShowSuggestions({...showSuggestions, [index]: false});
    };

    const applyAllBestMatches = () => {
        const newItems = [...lineItems];
        let appliedCount = 0;
        
        Object.entries(suggestions).forEach(([idxStr, matches]) => {
            const idx = parseInt(idxStr);
            if (matches && matches.length > 0) {
                const bestMatch = matches[0];
                if (bestMatch.score > 0.6) { // Only apply reasonably good matches
                    newItems[idx] = {
                        ...newItems[idx],
                        sku: bestMatch.catalog_item.sku,
                        description: bestMatch.catalog_item.item_name,
                        unit_price: bestMatch.catalog_item.expected_price || newItems[idx].unit_price,
                        metadata: {
                            ...newItems[idx].metadata,
                            matched_catalog_id: bestMatch.catalog_item.id,
                            match_score: bestMatch.score,
                            match_type: bestMatch.match_type
                        }
                    };
                    newItems[idx].total_price = Number(newItems[idx].quantity) * Number(newItems[idx].unit_price);
                    appliedCount++;
                }
            }
        });
        
        if (appliedCount > 0) {
            setLineItems(newItems);
            alert(`Applied ${appliedCount} best matches automatically.`);
        } else {
            alert("No high-confidence matches found to apply.");
        }
    };

    if (loading) {
        return <div className="text-center py-12 text-slate-500">Loading...</div>;
    }

    if (!quote) {
        return <div className="text-center py-12 text-slate-500">Quote not found</div>;
    }

    return (
        <div className="space-y-6 animate-fade-in">
            <div className="flex items-center gap-4">
                <Link to="/quotes" className="p-2 hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-white">
                    <ChevronLeft size={24} />
                </Link>
                <div>
                    <h1 className="text-2xl font-bold text-white flex items-center gap-3">
                        {quote.quote_number}
                        <span className="text-xs px-2 py-1 rounded-full bg-slate-800 text-slate-400 border border-slate-700 uppercase">
                            {quote.status.replace('_', ' ')}
                        </span>
                    </h1>
                    <p className="text-slate-400 text-sm">
                        From: {quote.metadata?.source_sender || quote.customers?.email || 'Unknown'}
                    </p>
                </div>
                <div className="ml-auto flex gap-3">
                    {Object.keys(suggestions).length > 0 && (
                        <button 
                            onClick={applyAllBestMatches}
                            className="btn-secondary flex items-center gap-2"
                            title="Apply best matches for all items (>60% confidence)"
                        >
                            <Lightbulb size={18} className="text-yellow-400" /> Auto-Match
                        </button>
                    )}
                    <button 
                        onClick={copyForERP}
                        className="btn-secondary flex items-center gap-2"
                        title="Copy to clipboard for ERP paste"
                    >
                        <Copy size={18} /> Copy for ERP
                    </button>
                    <button 
                        onClick={() => handleSave(false)}
                        disabled={saving}
                        className="btn-secondary flex items-center gap-2"
                    >
                        <Save size={18} /> Save Draft
                    </button>
                    <button 
                        onClick={() => handleSave(true)}
                        disabled={saving}
                        className="btn-primary flex items-center gap-2"
                    >
                        <CheckCircle size={18} /> Approve & Process
                    </button>
                </div>
            </div>

            {quote.metadata?.source_email_id && (
                <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-300 text-sm flex items-center gap-2">
                    <AlertTriangle size={16} />
                    <span>
                        This draft was automatically generated from an email. 
                        Please review all extracted line items carefully before approving.
                    </span>
                </div>
            )}

            <div className="glass-panel rounded-2xl overflow-hidden">
                <div className="p-6 border-b border-slate-700/50 flex justify-between items-center">
                    <div>
                        <h3 className="text-lg font-semibold text-white mb-1">Line Items</h3>
                        <p className="text-slate-400 text-sm">Review and edit extracted items</p>
                    </div>
                </div>
                
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead>
                            <tr className="bg-slate-800/30 text-slate-400 border-b border-slate-700/50">
                                <th className="px-6 py-4 w-1/4">Description</th>
                                <th className="px-6 py-4 w-1/6">SKU</th>
                                <th className="px-6 py-4 w-24">Qty</th>
                                <th className="px-6 py-4 w-32">Unit Price</th>
                                <th className="px-6 py-4 w-32 text-right">Total</th>
                                <th className="px-6 py-4 w-24 text-center">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/50">
                            {lineItems.map((item, index) => (
                                <React.Fragment key={index}>
                                    <tr key={index} className={`group hover:bg-slate-800/30 transition-colors ${
                                        item.metadata?.match_score ? 'bg-green-500/5' : 
                                        (item.metadata?.original_extraction?.confidence_score < 0.7 ? 'bg-red-500/5' : '')
                                    }`}>
                                        <td className="px-6 py-4">
                                            <div className="flex flex-col gap-1">
                                                <div className="flex items-center gap-2">
                                                    <input 
                                                        type="text" 
                                                        value={item.description || ''}
                                                        onChange={(e) => updateItem(index, 'description', e.target.value)}
                                                        className="bg-transparent border-none w-full text-slate-200 focus:ring-0 p-0 placeholder-slate-600"
                                                        placeholder="Item description"
                                                    />
                                                    {item.margin !== undefined && item.margin < 0.15 && (
                                                        <TrendingDown size={14} className="text-red-400" title={`Low Margin Alert: ${(item.margin * 100).toFixed(1)}%`} />
                                                    )}
                                                </div>
                                                {item.validation_warnings?.length > 0 && (
                                                    <div className="flex items-center gap-1 text-[10px] text-amber-400">
                                                        <Info size={10} />
                                                        {item.validation_warnings[0]}
                                                    </div>
                                                )}
                                                {suggestions[index] && suggestions[index].length > 0 && (
                                                    <button 
                                                        onClick={() => setShowSuggestions({...showSuggestions, [index]: !showSuggestions[index]})}
                                                        className="text-xs text-blue-400 flex items-center gap-1 hover:text-blue-300 w-fit"
                                                    >
                                                        <Lightbulb size={12} />
                                                        {suggestions[index].length} suggestions found
                                                    </button>
                                                )}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <input 
                                                type="text" 
                                                value={item.sku || ''}
                                                onChange={(e) => updateItem(index, 'sku', e.target.value)}
                                                className="bg-transparent border-none w-full text-slate-300 focus:ring-0 p-0 placeholder-slate-600"
                                                placeholder="SKU"
                                            />
                                        </td>
                                        <td className="px-6 py-4">
                                            <input 
                                                type="number" 
                                                value={item.quantity}
                                                onChange={(e) => updateItem(index, 'quantity', Number(e.target.value))}
                                                className="bg-transparent border-none w-full text-slate-300 focus:ring-0 p-0"
                                                min="1"
                                            />
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="flex items-center">
                                                <span className="text-slate-500 mr-1">$</span>
                                                <input 
                                                    type="number" 
                                                    value={item.unit_price}
                                                    onChange={(e) => updateItem(index, 'unit_price', Number(e.target.value))}
                                                    className="bg-transparent border-none w-full text-slate-300 focus:ring-0 p-0"
                                                    step="0.01"
                                                />
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-right font-medium text-white">
                                            ${(Number(item.quantity) * Number(item.unit_price)).toFixed(2)}
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            {item.metadata?.original_extraction?.confidence_score && (
                                                <div className="flex justify-center" title="Extraction Confidence">
                                                    <span className={`text-xs px-2 py-1 rounded-full ${
                                                        item.metadata.original_extraction.confidence_score > 0.8 
                                                            ? 'bg-emerald-500/10 text-emerald-400' 
                                                            : item.metadata.original_extraction.confidence_score < 0.7
                                                                ? 'bg-red-500/10 text-red-400 border border-red-500/20'
                                                                : 'bg-amber-500/10 text-amber-400'
                                                    }`}>
                                                        {Math.round(item.metadata.original_extraction.confidence_score * 100)}%
                                                    </span>
                                                </div>
                                            )}
                                        </td>
                                    </tr>
                                    {/* Suggestions Row */}
                                    {showSuggestions[index] && suggestions[index] && (
                                        <tr className="bg-slate-900/50">
                                            <td colSpan={6} className="px-6 py-3">
                                                <div className="text-xs font-semibold text-slate-400 mb-2">Suggested Matches:</div>
                                                <div className="space-y-2">
                                                    {suggestions[index].map((match: any, mIdx: number) => (
                                                        <div key={mIdx} className="flex items-center justify-between bg-slate-800 p-2 rounded border border-slate-700">
                                                            <div className="flex-1 grid grid-cols-3 gap-4">
                                                                <div className="text-slate-300">
                                                                    <span className="text-slate-500 mr-2">SKU:</span>
                                                                    {match.catalog_item.sku}
                                                                </div>
                                                                <div className="text-slate-300 truncate" title={match.catalog_item.item_name}>
                                                                    {match.catalog_item.item_name}
                                                                </div>
                                                                <div className="text-slate-300">
                                                                    <span className="text-slate-500 mr-2">Price:</span>
                                                                    ${match.catalog_item.expected_price}
                                                                </div>
                                                            </div>
                                                            <div className="flex items-center gap-3">
                                                                <span className="text-xs text-slate-500 uppercase tracking-wider font-medium">
                                                                    {match.match_type?.replace('_', ' ')}
                                                                </span>
                                                                <span className={`text-xs px-2 py-0.5 rounded ${
                                                                    match.score > 0.8 ? 'bg-green-900 text-green-300' : 'bg-yellow-900 text-yellow-300'
                                                                }`}>
                                                                    {Math.round(match.score * 100)}% Match
                                                                </span>
                                                                <button 
                                                                    onClick={() => applySuggestion(index, match)}
                                                                    className="btn-xs bg-blue-600 hover:bg-blue-500 text-white px-2 py-1 rounded text-xs flex items-center gap-1"
                                                                >
                                                                    <Check size={12} /> Apply
                                                                </button>
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            </td>
                                        </tr>
                                    )}
                                </React.Fragment>
                            ))}
                            <tr className="bg-slate-800/50 font-bold">
                                <td colSpan={4} className="px-6 py-4 text-right text-slate-300">Total Amount:</td>
                                <td className="px-6 py-4 text-right text-white text-lg">
                                    ${calculateTotal().toFixed(2)}
                                </td>
                                <td></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};
