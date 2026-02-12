import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { quotesApi, productsApi, quotesApiExtended, erpApi, quickbooksApi } from '../services/api';
import { SmartEditor } from '../components/ui/SmartEditor';
import { Save, ChevronLeft, CheckCircle, AlertTriangle, Lightbulb, Check, Copy, TrendingDown, Info, TrendingUp, ArrowRight, X, Zap, Shield, DollarSign, Link as LinkIcon, CheckCircle2, Sparkles, RefreshCw, UploadCloud, Download } from 'lucide-react';
import { trackEvent } from '../posthog';

export const QuoteReview = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [quote, setQuote] = useState<any>(null);
    const [lineItems, setLineItems] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [syncingQB, setSyncingQB] = useState(false);
    const [exporting, setExporting] = useState(false);
    const [showExportMenu, setShowExportMenu] = useState(false);
    const [hasBeenEdited, setHasBeenEdited] = useState(false);

    // Suggestions state
    const [suggestions, setSuggestions] = useState<{ [key: number]: any[] }>({});
    const [showSuggestions, setShowSuggestions] = useState<{ [key: number]: boolean }>({});
    const [loadingSuggestions, setLoadingSuggestions] = useState(false);
    const [optimizedItems, setOptimizedItems] = useState<{ [key: number]: any }>({});
    const [showMarginOptimizer, setShowMarginOptimizer] = useState(true);
    const [shareLink, setShareLink] = useState<string | null>(null);
    const [generatingLink, setGeneratingLink] = useState(false);

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
        setHasBeenEdited(true);
    };

    const calculateTotal = () => {
        return lineItems.reduce((sum, item) => sum + (Number(item.quantity) * Number(item.unit_price)), 0);
    };

    // Calculate margin for an item
    const calculateMargin = (item: any) => {
        if (!item.unit_price || item.unit_price === 0) return 0;
        // If we have cost_price from catalog match, use it
        const costPrice = item.metadata?.matched_catalog_cost_price ||
            item.metadata?.original_cost_price ||
            (item.unit_price * 0.7); // Default 30% margin assumption
        return ((item.unit_price - costPrice) / item.unit_price) * 100;
    };

    // Calculate total margin gained from optimizations
    const totalMarginGained = useMemo(() => {
        let total = 0;
        lineItems.forEach((item, index) => {
            const optimized = optimizedItems[index];
            if (optimized && optimized.catalog_item) {
                const originalMargin = calculateMargin(item);
                const optimizedMargin = calculateMargin({
                    ...item,
                    unit_price: optimized.catalog_item.expected_price,
                    metadata: {
                        ...item.metadata,
                        matched_catalog_cost_price: optimized.catalog_item.cost_price
                    }
                });
                const marginGain = (optimizedMargin - originalMargin) / 100 * (item.unit_price * item.quantity);
                total += marginGain;
            }
        });
        return total;
    }, [lineItems, optimizedItems]);

    // Find high-margin alternatives for each item
    const findHighMarginAlternatives = (item: any, matches: any[]) => {
        if (!matches || matches.length === 0) return null;

        const currentMargin = calculateMargin(item);
        const currentCost = item.unit_price * (1 - currentMargin / 100);

        // Find alternatives with better margin or lower cost
        return matches.filter(match => {
            const matchPrice = match.catalog_item.expected_price || 0;
            const matchCost = match.catalog_item.cost_price || (matchPrice * 0.7);
            const matchMargin = matchPrice > 0 ? ((matchPrice - matchCost) / matchPrice) * 100 : 0;

            // Consider it a good alternative if:
            // 1. Margin is at least 5% better, OR
            // 2. Cost is at least 10% lower with similar margin
            return (matchMargin > currentMargin + 5) ||
                (matchCost < currentCost * 0.9 && matchMargin >= currentMargin - 2);
        }).sort((a, b) => {
            const marginA = a.catalog_item.expected_price > 0 ?
                ((a.catalog_item.expected_price - (a.catalog_item.cost_price || a.catalog_item.expected_price * 0.7)) / a.catalog_item.expected_price) * 100 : 0;
            const marginB = b.catalog_item.expected_price > 0 ?
                ((b.catalog_item.expected_price - (b.catalog_item.cost_price || b.catalog_item.expected_price * 0.7)) / b.catalog_item.expected_price) * 100 : 0;
            return marginB - marginA;
        })[0]; // Return best match
    };

    // Check spec compliance (simplified - checks for common spec keywords)
    const checkSpecCompliance = (item: any, requirements?: string[]) => {
        if (!requirements || requirements.length === 0) return { compliant: true, reason: 'No requirements specified' };

        const description = (item.description || item.item_name || '').toLowerCase();
        const sku = (item.sku || '').toLowerCase();
        const searchText = `${description} ${sku}`;

        const missingSpecs: string[] = [];
        requirements.forEach(req => {
            const reqLower = req.toLowerCase();
            // Check for common spec patterns
            if (!searchText.includes(reqLower) &&
                !searchText.includes(reqLower.replace(/\s+/g, '')) &&
                !searchText.includes(reqLower.replace(/\s+/g, '-'))) {
                missingSpecs.push(req);
            }
        });

        return {
            compliant: missingSpecs.length === 0,
            missingSpecs,
            reason: missingSpecs.length > 0 ? `Missing: ${missingSpecs.join(', ')}` : 'All specs met'
        };
    };

    const handleSave = async (approve = false) => {
        try {
            setSaving(true);
            const total = calculateTotal();

            const updateData = {
                ...quote,
                total_amount: total,
                status: approve ? 'approved' : quote.status,
                items: lineItems.map(item => ({
                    ...item,
                    total_price: Number(item.quantity) * Number(item.unit_price)
                }))
            };

            await quotesApi.update(id!, updateData);

            if (approve) {
                trackEvent(hasBeenEdited ? 'extraction_edited' : 'extraction_verified', {
                    quote_id: id,
                    item_count: lineItems.length,
                    total_amount: total
                });
            }

            fetchQuote(id!);
            if (approve) {
                alert('Quote approved! You can now sink to QuickBooks.');
            }
        } catch (error) {
            console.error('Error updating quote:', error);
            alert('Failed to update quote');
        } finally {
            setSaving(false);
        }
    };

    const handleSyncToQuickBooks = async () => {
        if (!id) return;
        setSyncingQB(true);
        try {
            await quickbooksApi.exportQuote(id);
            alert('Safely synced to QuickBooks as an Estimate!');
        } catch (error: any) {
            console.error('QuickBooks sync failed:', error);
            if (error.response?.status === 401) {
                alert('QuickBooks is not connected. Please connect in the setup page.');
                navigate('/quickbooks');
            } else {
                alert('Failed to sync to QuickBooks: ' + (error.response?.data?.detail || error.message));
            }
        } finally {
            setSyncingQB(false);
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

    const handleExport = async (format: string) => {
        if (!id) return;
        setExporting(true);
        setShowExportMenu(false);
        try {
            await erpApi.exportQuote(id, format);
            alert(`Successfully sent quote to ERP (${format}) via Legacy Bridge!`);
            trackEvent('erp_export', { format, quote_id: id });
        } catch (error) {
            console.error('Export failed:', error);
            alert('Failed to send to ERP. Please try again.');
        } finally {
            setExporting(false);
        }
    };

    const generateQuoteLink = async () => {
        if (!id) return;

        try {
            setGeneratingLink(true);
            const res = await quotesApiExtended.generateLink(id);
            const publicUrl = res.data.public_url;
            setShareLink(publicUrl);

            // Copy to clipboard
            navigator.clipboard.writeText(publicUrl);
            alert("Quote link generated and copied to clipboard!");
        } catch (error) {
            console.error('Error generating quote link:', error);
            alert('Failed to generate quote link');
        } finally {
            setGeneratingLink(false);
        }
    };

    const applySuggestion = (index: number, match: any) => {
        const newItems = [...lineItems];
        const originalItem = newItems[index];

        newItems[index] = {
            ...newItems[index],
            sku: match.catalog_item.sku,
            description: match.catalog_item.item_name,
            unit_price: match.catalog_item.expected_price || newItems[index].unit_price,
            metadata: {
                ...newItems[index].metadata,
                matched_catalog_id: match.catalog_item.id,
                match_score: match.score,
                match_type: match.match_type,
                matched_catalog_cost_price: match.catalog_item.cost_price,
                original_cost_price: originalItem.metadata?.matched_catalog_cost_price ||
                    (originalItem.unit_price * 0.7)
            }
        };
        // Recalculate total
        newItems[index].total_price = Number(newItems[index].quantity) * Number(newItems[index].unit_price);

        setLineItems(newItems);
        setShowSuggestions({ ...showSuggestions, [index]: false });

        // Track optimization
        if (match.catalog_item.cost_price) {
            setOptimizedItems({ ...optimizedItems, [index]: match });
        }
    };

    const swapAndOptimize = (index: number, match: any) => {
        applySuggestion(index, match);
        trackEvent('smart_product_matching', {
            type: 'manual_swap',
            quote_id: id,
            match_score: match.score,
            match_type: match.match_type
        });
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
            trackEvent('smart_product_matching', {
                type: 'auto_matched',
                quote_id: id,
                count: appliedCount
            });
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
                        <span className={`text-xs px-2 py-1 rounded-full uppercase border ${quote.status === 'approved'
                            ? 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30'
                            : 'bg-slate-800 text-slate-400 border-slate-700'
                            }`}>
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

                    {quote.status === 'approved' ? (
                        <>
                            <div className="relative">
                                <button
                                    onClick={() => setShowExportMenu(!showExportMenu)}
                                    disabled={exporting}
                                    className="flex items-center gap-2 px-4 py-2.5 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-500 transition-all shadow-md active:scale-[0.98] disabled:opacity-70 disabled:cursor-not-allowed"
                                    title="Send to ERP System (Legacy Bridge)"
                                >
                                    {exporting ? <RefreshCw className="animate-spin" size={18} /> : <UploadCloud size={18} />}
                                    Export to ERP
                                </button>

                                {showExportMenu && (
                                    <div className="absolute right-0 mt-2 w-48 bg-slate-800 border border-slate-700 rounded-xl shadow-xl z-50 overflow-hidden animate-fade-in-up">
                                        <div className="p-2 border-b border-slate-700/50 text-xs text-slate-400 font-semibold uppercase tracking-wider">
                                            Select Format
                                        </div>
                                        <div className="flex flex-col p-1">
                                            {[
                                                { id: 'generic', label: 'Universal CSV' },
                                                { id: 'sap', label: 'SAP ERP' },
                                                { id: 'netsuite', label: 'NetSuite' },
                                                { id: 'quickbooks', label: 'QuickBooks CSV' },
                                                { id: 'gaeb', label: 'GAEB (European)' }
                                            ].map((fmt) => (
                                                <button
                                                    key={fmt.id}
                                                    onClick={() => handleExport(fmt.id)}
                                                    className="text-left px-3 py-2 text-sm text-slate-300 hover:bg-slate-700/50 hover:text-white rounded-lg transition-colors flex items-center justify-between group"
                                                >
                                                    {fmt.label}
                                                    {fmt.id === 'gaeb' && <span className="text-[10px] px-1.5 py-0.5 bg-blue-500/20 text-blue-300 rounded border border-blue-500/30">XML</span>}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>

                            <button
                                onClick={handleSyncToQuickBooks}
                                disabled={syncingQB}
                                className="flex items-center gap-2 px-4 py-2.5 bg-[#2CA01C] text-white font-medium rounded-lg hover:bg-[#238116] transition-all shadow-md active:scale-[0.98] disabled:opacity-70 disabled:cursor-not-allowed"
                                title="Sync valid quote to QuickBooks (API)"
                            >
                                {syncingQB ? <RefreshCw className="animate-spin" size={18} /> : <CheckCircle size={18} />}
                                Sync to QB
                            </button>
                        </>
                    ) : (
                        <>
                            <button
                                onClick={copyForERP}
                                className="btn-secondary flex items-center gap-2"
                                title="Copy to clipboard for ERP paste"
                            >
                                <Copy size={18} /> Copy Data
                            </button>
                            <button
                                onClick={generateQuoteLink}
                                disabled={generatingLink}
                                className="btn-secondary flex items-center gap-2 bg-blue-600 hover:bg-blue-500"
                                title="Generate shareable link for customer approval"
                            >
                                <LinkIcon size={18} /> {shareLink ? 'Link Generated' : 'Generate Quote Link'}
                            </button>
                            {shareLink && (
                                <div className="flex items-center gap-2 px-3 py-2 bg-emerald-500/20 border border-emerald-500/30 rounded-lg">
                                    <CheckCircle2 size={16} className="text-emerald-400" />
                                    <span className="text-xs text-emerald-300">Link ready</span>
                                </div>
                            )}
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
                                <CheckCircle size={18} /> Review & Approve
                            </button>
                        </>
                    )}
                </div>
            </div>

            {/* Total Margin Gained Counter - Pinned to Top */}
            {totalMarginGained > 0 && (
                <div className="p-6 rounded-2xl bg-gradient-to-r from-emerald-500/20 to-green-500/20 border border-emerald-500/30">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <div className="p-3 bg-emerald-500/20 rounded-xl">
                                <DollarSign size={24} className="text-emerald-400" />
                            </div>
                            <div>
                                <div className="text-sm text-emerald-300 font-medium">Total Margin Gained</div>
                                <div className="text-3xl font-bold text-white">+${totalMarginGained.toFixed(2)}</div>
                                <div className="text-xs text-emerald-400 mt-1">Additional profit from AI optimizations</div>
                            </div>
                        </div>
                        <button
                            onClick={() => setShowMarginOptimizer(!showMarginOptimizer)}
                            className="btn-secondary flex items-center gap-2"
                        >
                            {showMarginOptimizer ? <X size={18} /> : <Zap size={18} />}
                            {showMarginOptimizer ? 'Hide Optimizer' : 'Show Optimizer'}
                        </button>
                    </div>
                </div>
            )}

            {quote.metadata?.source_email_id && (
                <div className="p-4 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-300 text-sm flex items-center gap-2">
                    <AlertTriangle size={16} />
                    <span>
                        This draft was automatically generated from an email.
                        Please review all extracted line items carefully before approving.
                    </span>
                </div>
            )}

            {/* Split View: Extracted Data vs AI Recommendations */}
            {showMarginOptimizer ? (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Left: Extracted Data */}
                    <div className="glass-panel rounded-2xl overflow-hidden">
                        <div className="p-6 border-b border-slate-700/50">
                            <h3 className="text-lg font-semibold text-white mb-1">Extracted RFQ</h3>
                            <p className="text-slate-400 text-sm">Original items from source</p>
                        </div>
                        <div className="overflow-y-auto max-h-[600px]">
                            <div className="divide-y divide-slate-800/50">
                                {lineItems.map((item, index) => {
                                    const highMarginAlt = findHighMarginAlternatives(item, suggestions[index]);
                                    const specCheck = checkSpecCompliance(item, quote.metadata?.tender_requirements);
                                    const currentMargin = calculateMargin(item);

                                    return (
                                        <div key={index} className={`p-4 hover:bg-slate-800/30 transition-colors ${highMarginAlt ? 'bg-amber-500/5 border-l-2 border-amber-500/50' : ''
                                            }`}>
                                            <div className="flex items-start justify-between gap-4">
                                                <div className="flex-1">
                                                    <div className="flex items-center gap-2 mb-2">
                                                        <div className="flex-1">
                                                            <div className="text-sm font-medium text-white mb-1">
                                                                {item.description || item.item_name || 'Unnamed Item'}
                                                            </div>
                                                            <div className="flex items-center gap-3 text-xs text-slate-400">
                                                                <span>SKU: {item.sku || 'N/A'}</span>
                                                                <span>•</span>
                                                                <span>Qty: {item.quantity}</span>
                                                                <span>•</span>
                                                                <span>${item.unit_price?.toFixed(2)}/unit</span>
                                                            </div>
                                                        </div>
                                                        {/* Spec Compliance Badge */}
                                                        {specCheck && (
                                                            <div className="flex-shrink-0">
                                                                {specCheck.compliant ? (
                                                                    <div className="flex items-center gap-1 px-2 py-1 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" title={specCheck.reason}>
                                                                        <Shield size={12} />
                                                                        <span className="text-xs">Compliant</span>
                                                                    </div>
                                                                ) : (
                                                                    <div className="flex items-center gap-1 px-2 py-1 rounded-full bg-red-500/10 text-red-400 border border-red-500/20" title={specCheck.reason}>
                                                                        <AlertTriangle size={12} />
                                                                        <span className="text-xs">Non-Compliant</span>
                                                                    </div>
                                                                )}
                                                            </div>
                                                        )}
                                                    </div>

                                                    {/* Semantic SKU Matcher Display */}
                                                    {item.metadata?.original_extraction && (
                                                        <div className="mt-2 p-2 bg-slate-900/50 rounded text-xs">
                                                            <div className="text-slate-500 mb-1">Extracted Input:</div>
                                                            <div className="text-slate-300 font-mono">
                                                                "{item.metadata.original_extraction.item_name || item.metadata.original_extraction.description || 'N/A'}"
                                                            </div>
                                                            {item.sku && item.metadata?.matched_catalog_id && (
                                                                <>
                                                                    <div className="text-slate-500 mt-2 mb-1">Mapped to ERP SKU:</div>
                                                                    <div className="text-emerald-400 font-mono font-semibold">
                                                                        {item.sku}
                                                                    </div>
                                                                </>
                                                            )}
                                                        </div>
                                                    )}

                                                    {/* Margin Boost Badge - Phase 2 Enhancement */}
                                                    <div className="mt-2 flex items-center gap-2 flex-wrap">
                                                        <span className="text-xs text-slate-500">Margin:</span>
                                                        <span className={`text-xs font-medium ${currentMargin > 20 ? 'text-emerald-400' :
                                                            currentMargin > 10 ? 'text-amber-400' : 'text-red-400'
                                                            }`}>
                                                            {currentMargin.toFixed(1)}%
                                                        </span>
                                                        {highMarginAlt && (
                                                            <div className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-gradient-to-r from-amber-500/20 to-yellow-500/20 border border-amber-500/30">
                                                                <Sparkles size={10} className="text-amber-400" />
                                                                <span className="text-xs font-semibold text-amber-300">
                                                                    Margin Boost Available
                                                                </span>
                                                                <span className="text-xs text-amber-400 font-bold">
                                                                    +{(
                                                                        ((highMarginAlt.catalog_item.expected_price - (highMarginAlt.catalog_item.cost_price || highMarginAlt.catalog_item.expected_price * 0.7)) / highMarginAlt.catalog_item.expected_price * 100) - currentMargin
                                                                    ).toFixed(1)}%
                                                                </span>
                                                            </div>
                                                        )}
                                                        {currentMargin > 20 && !highMarginAlt && (
                                                            <div className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-500/20 border border-emerald-500/30">
                                                                <TrendingUp size={10} className="text-emerald-400" />
                                                                <span className="text-xs font-semibold text-emerald-300">High Margin</span>
                                                            </div>
                                                        )}
                                                    </div>

                                                    {/* High Margin Alternative Alert */}
                                                    {highMarginAlt && (
                                                        <div className="mt-3 p-3 bg-gradient-to-r from-amber-500/10 to-yellow-500/10 border border-amber-500/30 rounded-lg">
                                                            <div className="flex items-center gap-2 mb-2">
                                                                <Zap size={14} className="text-amber-400" />
                                                                <span className="text-sm font-semibold text-amber-300">Margin Optimization Available</span>
                                                            </div>
                                                            <div className="text-xs text-amber-200/80 mb-2">
                                                                We found a cheaper Private Label alternative that increases margin by +{(
                                                                    ((highMarginAlt.catalog_item.expected_price - (highMarginAlt.catalog_item.cost_price || highMarginAlt.catalog_item.expected_price * 0.7)) / highMarginAlt.catalog_item.expected_price * 100) - currentMargin
                                                                ).toFixed(1)}%
                                                            </div>
                                                            <button
                                                                onClick={() => swapAndOptimize(index, highMarginAlt)}
                                                                className="btn-primary text-xs py-1.5 px-3 flex items-center gap-1 w-full justify-center"
                                                            >
                                                                <TrendingUp size={12} />
                                                                Swap & Optimize
                                                            </button>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    </div>

                    {/* Right: AI Recommendations */}
                    <div className="glass-panel rounded-2xl overflow-hidden">
                        <div className="p-6 border-b border-slate-700/50">
                            <h3 className="text-lg font-semibold text-white mb-1 flex items-center gap-2">
                                <Lightbulb size={20} className="text-yellow-400" />
                                AI Recommendations
                            </h3>
                            <p className="text-slate-400 text-sm">High-margin alternatives and optimizations</p>
                        </div>
                        <div className="overflow-y-auto max-h-[600px] p-4 space-y-4">
                            {lineItems.map((item, index) => {
                                const matches = suggestions[index] || [];
                                const highMarginAlt = findHighMarginAlternatives(item, matches);

                                if (!highMarginAlt && matches.length === 0) {
                                    return null;
                                }

                                const currentMargin = calculateMargin(item);
                                const altMargin = highMarginAlt ?
                                    ((highMarginAlt.catalog_item.expected_price - (highMarginAlt.catalog_item.cost_price || highMarginAlt.catalog_item.expected_price * 0.7)) / highMarginAlt.catalog_item.expected_price * 100) : 0;
                                const marginGain = altMargin - currentMargin;

                                return (
                                    <div key={index} className="p-4 bg-slate-800/50 rounded-xl border border-slate-700/50">
                                        <div className="text-sm font-medium text-white mb-2">
                                            {item.description || `Item ${index + 1}`}
                                        </div>

                                        {highMarginAlt ? (
                                            <div className="space-y-3">
                                                <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-lg">
                                                    <div className="flex items-center justify-between mb-2">
                                                        <span className="text-xs font-semibold text-emerald-400">Recommended Alternative</span>
                                                        <span className="text-xs px-2 py-0.5 bg-emerald-500/20 text-emerald-300 rounded">
                                                            +{marginGain.toFixed(1)}% margin
                                                        </span>
                                                    </div>
                                                    <div className="space-y-1 text-xs">
                                                        <div className="flex justify-between">
                                                            <span className="text-slate-400">SKU:</span>
                                                            <span className="text-white font-mono">{highMarginAlt.catalog_item.sku}</span>
                                                        </div>
                                                        <div className="flex justify-between">
                                                            <span className="text-slate-400">Name:</span>
                                                            <span className="text-white">{highMarginAlt.catalog_item.item_name}</span>
                                                        </div>
                                                        <div className="flex justify-between">
                                                            <span className="text-slate-400">Price:</span>
                                                            <span className="text-white">${highMarginAlt.catalog_item.expected_price?.toFixed(2)}</span>
                                                        </div>
                                                        <div className="flex justify-between">
                                                            <span className="text-slate-400">Margin:</span>
                                                            <span className="text-emerald-400 font-semibold">{altMargin.toFixed(1)}%</span>
                                                        </div>
                                                    </div>
                                                    <button
                                                        onClick={() => swapAndOptimize(index, highMarginAlt)}
                                                        className="mt-3 w-full btn-primary text-xs py-2 flex items-center justify-center gap-2"
                                                    >
                                                        <ArrowRight size={14} />
                                                        Apply This Alternative
                                                    </button>
                                                </div>

                                                {matches.length > 1 && (
                                                    <details className="text-xs">
                                                        <summary className="text-slate-400 cursor-pointer hover:text-slate-300">
                                                            View {matches.length - 1} more alternatives
                                                        </summary>
                                                        <div className="mt-2 space-y-2">
                                                            {matches.slice(1, 4).map((match: any, mIdx: number) => (
                                                                <div key={mIdx} className="p-2 bg-slate-900/50 rounded border border-slate-700/30">
                                                                    <div className="flex justify-between items-center">
                                                                        <div>
                                                                            <div className="text-slate-300 font-mono text-xs">{match.catalog_item.sku}</div>
                                                                            <div className="text-slate-400 text-xs truncate max-w-[200px]">{match.catalog_item.item_name}</div>
                                                                        </div>
                                                                        <button
                                                                            onClick={() => applySuggestion(index, match)}
                                                                            className="btn-secondary text-xs py-1 px-2"
                                                                        >
                                                                            Use
                                                                        </button>
                                                                    </div>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </details>
                                                )}
                                            </div>
                                        ) : matches.length > 0 ? (
                                            <div className="text-xs text-slate-400">
                                                {matches.length} match(es) found, but no significant margin improvement available.
                                            </div>
                                        ) : null}
                                    </div>
                                );
                            })}

                            {lineItems.every((item, index) => !suggestions[index] || suggestions[index].length === 0) && (
                                <div className="text-center py-8 text-slate-500 text-sm">
                                    No recommendations available yet. Suggestions will appear after analysis.
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            ) : (
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
                                {lineItems.map((item, index) => {
                                    const specCheck = checkSpecCompliance(item, quote.metadata?.tender_requirements);
                                    const currentMargin = calculateMargin(item);

                                    return (
                                        <React.Fragment key={index}>
                                            <tr className={`group hover:bg-slate-800/30 transition-colors ${item.metadata?.match_score ? 'bg-green-500/5' :
                                                (item.metadata?.original_extraction?.confidence_score < 0.7 ? 'bg-red-500/5' : '')
                                                }`}>
                                                <td className="px-6 py-4">
                                                    <div className="flex flex-col gap-1">
                                                        <div className="flex items-center gap-2">
                                                            <SmartEditor
                                                                content={item.description || ''}
                                                                onChange={(html) => updateItem(index, 'description', html)}
                                                                className="w-full bg-slate-900/20"
                                                                minHeight="80px"
                                                                placeholder="Item description & technical specs..."
                                                            />
                                                            {/* Phase 2: Margin Boost Badge in Table View */}
                                                            {suggestions[index] && suggestions[index].length > 0 && (() => {
                                                                const highMarginAlt = findHighMarginAlternatives(item, suggestions[index]);
                                                                if (highMarginAlt) {
                                                                    const altMargin = ((highMarginAlt.catalog_item.expected_price - (highMarginAlt.catalog_item.cost_price || highMarginAlt.catalog_item.expected_price * 0.7)) / highMarginAlt.catalog_item.expected_price * 100);
                                                                    const marginGain = altMargin - currentMargin;
                                                                    return (
                                                                        <div className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-gradient-to-r from-amber-500/20 to-yellow-500/20 border border-amber-500/30">
                                                                            <Sparkles size={12} className="text-amber-400" />
                                                                            <span className="text-xs font-semibold text-amber-300">+{marginGain.toFixed(1)}%</span>
                                                                        </div>
                                                                    );
                                                                }
                                                                return null;
                                                            })()}
                                                            {currentMargin < 10 && (
                                                                <span title={`Low Margin: ${currentMargin.toFixed(1)}%`}>
                                                                    <TrendingDown size={14} className="text-red-400" />
                                                                </span>
                                                            )}
                                                            {specCheck && (
                                                                specCheck.compliant ? (
                                                                    <span title={specCheck.reason}>
                                                                        <Shield size={14} className="text-emerald-400" />
                                                                    </span>
                                                                ) : (
                                                                    <span title={specCheck.reason}>
                                                                        <AlertTriangle size={14} className="text-red-400" />
                                                                    </span>
                                                                )
                                                            )}
                                                        </div>
                                                        {item.metadata?.original_extraction && (
                                                            <div className="text-[10px] text-slate-500">
                                                                Extracted: "{item.metadata.original_extraction.item_name || item.metadata.original_extraction.description || 'N/A'}"
                                                                {item.sku && item.metadata?.matched_catalog_id && (
                                                                    <span className="text-emerald-400 ml-2">→ {item.sku}</span>
                                                                )}
                                                            </div>
                                                        )}
                                                        {suggestions[index] && suggestions[index].length > 0 && (
                                                            <button
                                                                onClick={() => setShowSuggestions({ ...showSuggestions, [index]: !showSuggestions[index] })}
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
                                                            <span className={`text-xs px-2 py-1 rounded-full ${item.metadata.original_extraction.confidence_score > 0.8
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
                                                                        <span className={`text-xs px-2 py-0.5 rounded ${match.score > 0.8 ? 'bg-green-900 text-green-300' : 'bg-yellow-900 text-yellow-300'
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
                                    );
                                })}
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
            )}
        </div>
    );
};

export default QuoteReview;
