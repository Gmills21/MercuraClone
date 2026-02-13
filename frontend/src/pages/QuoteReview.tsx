import React, { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { quotesApi, productsApi, quotesApiExtended, erpApi, quickbooksApi, pdfApi, emailApi } from '../services/api';
import { SmartEditor } from '../components/ui/SmartEditor';
import { CopilotCommandBar } from '../components/CopilotCommandBar';
import { SourceDocumentViewer } from '../components/SourceDocumentViewer';
import { 
  Save, ChevronLeft, CheckCircle, AlertTriangle, Lightbulb, Check, Copy, 
  TrendingDown, Info, TrendingUp, ArrowRight, X, Zap, Shield, DollarSign, 
  Link as LinkIcon, CheckCircle2, Sparkles, RefreshCw, UploadCloud, Download,
  Eye, FileText, Split, Maximize2, Minimize2, MapPin, Mail, FileDown
} from 'lucide-react';
import { trackEvent } from '../posthog';

// View modes for the quote review
 type ViewMode = 'autopilot' | 'split' | 'table';

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
    const [viewMode, setViewMode] = useState<ViewMode>('autopilot');
    const [selectedItemIndex, setSelectedItemIndex] = useState<number | null>(null);

    // Suggestions state
    const [suggestions, setSuggestions] = useState<{ [key: number]: any[] }>({});
    const [showSuggestions, setShowSuggestions] = useState<{ [key: number]: boolean }>({});
    const [loadingSuggestions, setLoadingSuggestions] = useState(false);
    const [optimizedItems, setOptimizedItems] = useState<{ [key: number]: any }>({});
    const [shareLink, setShareLink] = useState<string | null>(null);
    const [generatingLink, setGeneratingLink] = useState(false);
    
    // PDF & Email state
    const [downloadingPdf, setDownloadingPdf] = useState(false);
    const [showEmailDialog, setShowEmailDialog] = useState(false);
    const [sendingEmail, setSendingEmail] = useState(false);
    const [emailData, setEmailData] = useState({
        to_email: '',
        to_name: '',
        message: ''
    });

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
        const costPrice = item.metadata?.matched_catalog_cost_price ||
            item.metadata?.original_cost_price ||
            (item.unit_price * 0.7);
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

        return matches.filter(match => {
            const matchPrice = match.catalog_item.expected_price || 0;
            const matchCost = match.catalog_item.cost_price || (matchPrice * 0.7);
            const matchMargin = matchPrice > 0 ? ((matchPrice - matchCost) / matchPrice) * 100 : 0;

            return (matchMargin > currentMargin + 5) ||
                (matchCost < currentCost * 0.9 && matchMargin >= currentMargin - 2);
        }).sort((a, b) => {
            const marginA = a.catalog_item.expected_price > 0 ?
                ((a.catalog_item.expected_price - (a.catalog_item.cost_price || a.catalog_item.expected_price * 0.7)) / a.catalog_item.expected_price) * 100 : 0;
            const marginB = b.catalog_item.expected_price > 0 ?
                ((b.catalog_item.expected_price - (b.catalog_item.cost_price || b.catalog_item.expected_price * 0.7)) / b.catalog_item.expected_price) * 100 : 0;
            return marginB - marginA;
        })[0];
    };

    // Check spec compliance
    const checkSpecCompliance = (item: any, requirements?: string[]) => {
        if (!requirements || requirements.length === 0) return { compliant: true, reason: 'No requirements specified' };

        const description = (item.description || item.item_name || '').toLowerCase();
        const sku = (item.sku || '').toLowerCase();
        const searchText = `${description} ${sku}`;

        const missingSpecs: string[] = [];
        requirements.forEach(req => {
            const reqLower = req.toLowerCase();
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
                alert('Quote approved! You can now sync to QuickBooks.');
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
            alert('Successfully synced to QuickBooks as an Estimate!');
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
        newItems[index].total_price = Number(newItems[index].quantity) * Number(newItems[index].unit_price);

        setLineItems(newItems);
        setShowSuggestions({ ...showSuggestions, [index]: false });

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
                if (bestMatch.score > 0.6) {
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

    // Handle item selection for source anchoring
    const handleItemSelect = (index: number) => {
        setSelectedItemIndex(index);
        // Scroll item into view if needed
        const element = document.getElementById(`quote-item-${index}`);
        element?.scrollIntoView({ behavior: 'smooth', block: 'center' });
    };

    // Download PDF
    const handleDownloadPdf = async () => {
        if (!id) return;
        try {
            setDownloadingPdf(true);
            const response = await pdfApi.downloadQuote(id);
            
            // Create download link
            const blob = new Blob([response.data], { type: 'application/pdf' });
            const url = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `Quote_${quote?.quote_number || id}.pdf`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);
            
            trackEvent('quote_pdf_downloaded', { quote_id: id });
        } catch (error) {
            console.error('PDF download failed:', error);
            alert('Failed to download PDF. Please try again.');
        } finally {
            setDownloadingPdf(false);
        }
    };

    // Send email
    const handleSendEmail = async () => {
        if (!id || !emailData.to_email) return;
        try {
            setSendingEmail(true);
            await emailApi.sendQuote(id, {
                to_email: emailData.to_email,
                to_name: emailData.to_name,
                message: emailData.message,
                include_pdf: true
            });
            
            alert('Quote sent successfully!');
            setShowEmailDialog(false);
            setEmailData({ to_email: '', to_name: '', message: '' });
            trackEvent('quote_email_sent', { quote_id: id });
        } catch (error) {
            console.error('Email send failed:', error);
            alert('Failed to send email. Please check your email configuration.');
        } finally {
            setSendingEmail(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="text-center">
                    <RefreshCw className="animate-spin mx-auto mb-4 text-orange-500" size={32} />
                    <p className="text-slate-400">Loading quote...</p>
                </div>
            </div>
        );
    }

    if (!quote) {
        return (
            <div className="flex items-center justify-center h-screen">
                <div className="text-center">
                    <AlertTriangle className="mx-auto mb-4 text-red-500" size={32} />
                    <p className="text-slate-400">Quote not found</p>
                </div>
            </div>
        );
    }

    // Determine source type from metadata
    const sourceType = quote.metadata?.source_type?.includes('pdf') ? 'pdf' :
        quote.metadata?.source_type?.includes('email') ? 'email' :
            quote.metadata?.source_type?.includes('image') ? 'image' : 'pdf';

    return (
        <div className="min-h-screen bg-slate-950">
            {/* Header */}
            <header className="sticky top-0 z-40 bg-slate-900/80 backdrop-blur-xl border-b border-slate-800">
                <div className="max-w-[1920px] mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between h-16">
                        {/* Left: Back + Title */}
                        <div className="flex items-center gap-4">
                            <Link 
                                to="/quotes" 
                                className="p-2 hover:bg-slate-800 rounded-lg transition-colors text-slate-400 hover:text-white"
                            >
                                <ChevronLeft size={20} />
                            </Link>
                            <div>
                                <div className="flex items-center gap-3">
                                    <h1 className="text-lg font-semibold text-white tracking-tight">
                                        {quote.quote_number}
                                    </h1>
                                    <span className={`text-[10px] px-2 py-0.5 rounded-full uppercase font-bold tracking-wider ${quote.status === 'approved'
                                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                                        : 'bg-slate-800 text-slate-400 border border-slate-700'
                                        }`}>
                                        {quote.status.replace('_', ' ')}
                                    </span>
                                </div>
                                <p className="text-xs text-slate-500">
                                    From: {quote.metadata?.source_sender || quote.customers?.email || 'Unknown'}
                                </p>
                            </div>
                        </div>

                        {/* Center: View Mode Toggle */}
                        <div className="hidden md:flex items-center bg-slate-800/50 rounded-lg p-1">
                            <button
                                onClick={() => setViewMode('autopilot')}
                                className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                                    viewMode === 'autopilot' 
                                        ? 'bg-slate-700 text-white' 
                                        : 'text-slate-400 hover:text-slate-200'
                                }`}
                            >
                                <Split size={14} />
                                Autopilot
                            </button>
                            <button
                                onClick={() => setViewMode('split')}
                                className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                                    viewMode === 'split' 
                                        ? 'bg-slate-700 text-white' 
                                        : 'text-slate-400 hover:text-slate-200'
                                }`}
                            >
                                <Eye size={14} />
                                Review
                            </button>
                            <button
                                onClick={() => setViewMode('table')}
                                className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                                    viewMode === 'table' 
                                        ? 'bg-slate-700 text-white' 
                                        : 'text-slate-400 hover:text-slate-200'
                                }`}
                            >
                                <FileText size={14} />
                                Table
                            </button>
                        </div>

                        {/* Right: Actions */}
                        <div className="flex items-center gap-2">
                            {/* AI Copilot */}
                            <CopilotCommandBar
                                quoteId={id}
                                onApplyChange={(change) => {
                                    if (change.item_index !== undefined && change.new_item) {
                                        const newItems = [...lineItems];
                                        if (change.item_index < newItems.length) {
                                            newItems[change.item_index] = {
                                                ...newItems[change.item_index],
                                                ...change.new_item,
                                                total_price: change.new_item.unit_price * newItems[change.item_index].quantity
                                            };
                                            setLineItems(newItems);
                                            setHasBeenEdited(true);
                                        }
                                    }
                                }}
                            />

                            {/* PDF Download */}
                            <button
                                onClick={handleDownloadPdf}
                                disabled={downloadingPdf}
                                className="flex items-center gap-2 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm font-medium transition-all"
                                title="Download PDF"
                            >
                                {downloadingPdf ? <RefreshCw className="animate-spin" size={16} /> : <FileDown size={16} />}
                                <span className="hidden lg:inline">PDF</span>
                            </button>

                            {/* Email Send */}
                            <button
                                onClick={() => setShowEmailDialog(true)}
                                className="flex items-center gap-2 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm font-medium transition-all"
                                title="Email Quote"
                            >
                                <Mail size={16} />
                                <span className="hidden lg:inline">Email</span>
                            </button>

                            {Object.keys(suggestions).length > 0 && (
                                <button
                                    onClick={applyAllBestMatches}
                                    className="hidden sm:flex items-center gap-2 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm font-medium transition-all"
                                    title="Apply best matches for all items (>60% confidence)"
                                >
                                    <Lightbulb size={16} className="text-yellow-400" />
                                    <span className="hidden lg:inline">Auto-Match</span>
                                </button>
                            )}

                            {quote.status === 'approved' ? (
                                <>
                                    <div className="relative">
                                        <button
                                            onClick={() => setShowExportMenu(!showExportMenu)}
                                            disabled={exporting}
                                            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-500 transition-all text-sm"
                                        >
                                            {exporting ? <RefreshCw className="animate-spin" size={16} /> : <UploadCloud size={16} />}
                                            Export to ERP
                                        </button>
                                        {showExportMenu && (
                                            <div className="absolute right-0 mt-2 w-48 bg-slate-800 border border-slate-700 rounded-xl shadow-xl z-50 overflow-hidden">
                                                <div className="p-2 border-b border-slate-700/50 text-xs text-slate-400 font-semibold uppercase">
                                                    Select Format
                                                </div>
                                                {['generic', 'sap', 'netsuite', 'quickbooks', 'gaeb'].map((fmt) => (
                                                    <button
                                                        key={fmt}
                                                        onClick={() => handleExport(fmt)}
                                                        className="w-full text-left px-3 py-2 text-sm text-slate-300 hover:bg-slate-700 hover:text-white transition-colors"
                                                    >
                                                        {fmt === 'generic' ? 'Universal CSV' : fmt.toUpperCase()}
                                                    </button>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                    <button
                                        onClick={handleSyncToQuickBooks}
                                        disabled={syncingQB}
                                        className="flex items-center gap-2 px-4 py-2 bg-[#2CA01C] text-white font-medium rounded-lg hover:bg-[#238116] transition-all text-sm"
                                    >
                                        {syncingQB ? <RefreshCw className="animate-spin" size={16} /> : <CheckCircle size={16} />}
                                        Sync to QB
                                    </button>
                                </>
                            ) : (
                                <>
                                    <button
                                        onClick={copyForERP}
                                        className="hidden sm:flex items-center gap-2 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm"
                                    >
                                        <Copy size={16} />
                                    </button>
                                    <button
                                        onClick={() => handleSave(false)}
                                        disabled={saving}
                                        className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm font-medium"
                                    >
                                        <Save size={16} />
                                        Save
                                    </button>
                                    <button
                                        onClick={() => handleSave(true)}
                                        disabled={saving}
                                        className="flex items-center gap-2 px-4 py-2 bg-orange-600 hover:bg-orange-500 text-white rounded-lg text-sm font-medium"
                                    >
                                        <CheckCircle size={16} />
                                        Approve
                                    </button>
                                </>
                            )}
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Content */}
            <main className="max-w-[1920px] mx-auto p-4 sm:p-6 lg:p-8">
                {/* Margin Alert Banner */}
                {totalMarginGained > 0 && (
                    <div className="mb-6 p-4 rounded-xl bg-gradient-to-r from-emerald-500/10 to-green-500/10 border border-emerald-500/20">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-emerald-500/20 rounded-lg">
                                    <TrendingUp size={20} className="text-emerald-400" />
                                </div>
                                <div>
                                    <p className="text-sm text-emerald-300 font-medium">Margin Optimization Active</p>
                                    <p className="text-2xl font-bold text-white">+${totalMarginGained.toFixed(2)}</p>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* Source Warning */}
                {quote.metadata?.source_email_id && (
                    <div className="mb-6 p-4 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-300 text-sm flex items-center gap-3">
                        <Info size={18} />
                        <span>This draft was automatically generated from an email. Please review all extracted items carefully.</span>
                    </div>
                )}

                {/* AUTOPILOT VIEW - Side by Side with Source */}
                {viewMode === 'autopilot' && (
                    <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 h-[calc(100vh-240px)]">
                        {/* Left: Source Document */}
                        <SourceDocumentViewer
                            sourceType={sourceType}
                            sourceUrl={quote.metadata?.source_url}
                            sourceContent={quote.metadata?.source_content}
                            sourceMetadata={{
                                filename: quote.metadata?.source_filename,
                                sender: quote.metadata?.source_sender,
                                subject: quote.metadata?.source_subject,
                                date: quote.metadata?.source_date,
                                total_pages: quote.metadata?.total_pages || 1,
                                extraction_anchors: true
                            }}
                            extractedItems={lineItems}
                            selectedItemIndex={selectedItemIndex}
                            onItemClick={handleItemSelect}
                            className="h-full"
                        />

                        {/* Right: Extracted Quote Data */}
                        <div className="flex flex-col h-full bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
                            <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-slate-900/50">
                                <div className="flex items-center gap-2">
                                    <CheckCircle size={18} className="text-emerald-400" />
                                    <span className="font-medium text-slate-200">Verified Extraction</span>
                                    <span className="text-xs text-slate-500">({lineItems.length} items)</span>
                                </div>
                                <div className="flex items-center gap-2 text-xs text-slate-500">
                                    <span>Click item to see source</span>
                                    <MapPin size={12} />
                                </div>
                            </div>
                            
                            <div className="flex-1 overflow-y-auto p-4 space-y-3">
                                {lineItems.map((item, index) => {
                                    const highMarginAlt = findHighMarginAlternatives(item, suggestions[index]);
                                    const specCheck = checkSpecCompliance(item, quote.metadata?.tender_requirements);
                                    const currentMargin = calculateMargin(item);
                                    const isSelected = selectedItemIndex === index;

                                    return (
                                        <div
                                            key={index}
                                            id={`quote-item-${index}`}
                                            onClick={() => handleItemSelect(index)}
                                            className={`p-4 rounded-xl border transition-all cursor-pointer ${
                                                isSelected 
                                                    ? 'bg-orange-500/10 border-orange-500/50 ring-1 ring-orange-500/30' 
                                                    : 'bg-slate-800/50 border-slate-700/50 hover:border-slate-600'
                                            }`}
                                        >
                                            {/* Item Header */}
                                            <div className="flex items-start justify-between gap-3 mb-3">
                                                <div className="flex items-center gap-3">
                                                    <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                                                        isSelected ? 'bg-orange-500 text-white' : 'bg-slate-700 text-slate-400'
                                                    }`}>
                                                        {index + 1}
                                                    </span>
                                                    <div>
                                                        <p className="text-sm font-medium text-white">{item.description || 'Unnamed Item'}</p>
                                                        <p className="text-xs text-slate-500">SKU: {item.sku || 'N/A'}</p>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    {specCheck.compliant ? (
                                                        <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 text-xs">
                                                            <Shield size={10} /> Spec OK
                                                        </span>
                                                    ) : (
                                                        <span className="flex items-center gap-1 px-2 py-0.5 rounded-full bg-red-500/10 text-red-400 text-xs">
                                                            <AlertTriangle size={10} /> Spec Issue
                                                        </span>
                                                    )}
                                                </div>
                                            </div>

                                            {/* Item Details */}
                                            <div className="grid grid-cols-3 gap-4 mb-3">
                                                <div>
                                                    <p className="text-xs text-slate-500 mb-1">Quantity</p>
                                                    <input
                                                        type="number"
                                                        value={item.quantity}
                                                        onChange={(e) => updateItem(index, 'quantity', Number(e.target.value))}
                                                        className="w-full px-2 py-1 bg-slate-900 border border-slate-700 rounded text-sm text-white focus:border-orange-500 focus:outline-none"
                                                        min="1"
                                                        onClick={(e) => e.stopPropagation()}
                                                    />
                                                </div>
                                                <div>
                                                    <p className="text-xs text-slate-500 mb-1">Unit Price</p>
                                                    <div className="flex items-center px-2 py-1 bg-slate-900 border border-slate-700 rounded">
                                                        <span className="text-slate-500 text-sm mr-1">$</span>
                                                        <input
                                                            type="number"
                                                            value={item.unit_price}
                                                            onChange={(e) => updateItem(index, 'unit_price', Number(e.target.value))}
                                                            className="w-full bg-transparent border-0 text-sm text-white focus:outline-none"
                                                            step="0.01"
                                                            onClick={(e) => e.stopPropagation()}
                                                        />
                                                    </div>
                                                </div>
                                                <div>
                                                    <p className="text-xs text-slate-500 mb-1">Total</p>
                                                    <p className="text-sm font-semibold text-white">
                                                        ${(item.quantity * item.unit_price).toFixed(2)}
                                                    </p>
                                                </div>
                                            </div>

                                            {/* Margin & Confidence */}
                                            <div className="flex items-center justify-between pt-3 border-t border-slate-700/50">
                                                <div className="flex items-center gap-4">
                                                    <div className="flex items-center gap-2">
                                                        <span className="text-xs text-slate-500">Margin:</span>
                                                        <span className={`text-xs font-semibold ${
                                                            currentMargin > 20 ? 'text-emerald-400' :
                                                            currentMargin > 10 ? 'text-amber-400' : 'text-red-400'
                                                        }`}>
                                                            {currentMargin.toFixed(1)}%
                                                        </span>
                                                    </div>
                                                    {item.metadata?.original_extraction?.confidence_score && (
                                                        <div className="flex items-center gap-2">
                                                            <span className="text-xs text-slate-500">Confidence:</span>
                                                            <span className={`text-xs ${
                                                                item.metadata.original_extraction.confidence_score > 0.8 ? 'text-emerald-400' :
                                                                item.metadata.original_extraction.confidence_score > 0.6 ? 'text-amber-400' : 'text-red-400'
                                                            }`}>
                                                                {Math.round(item.metadata.original_extraction.confidence_score * 100)}%
                                                            </span>
                                                        </div>
                                                    )}
                                                </div>
                                                
                                                {/* High Margin Alternative */}
                                                {highMarginAlt && (
                                                    <button
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            swapAndOptimize(index, highMarginAlt);
                                                        }}
                                                        className="flex items-center gap-1 px-2 py-1 bg-gradient-to-r from-amber-500/20 to-yellow-500/20 border border-amber-500/30 rounded-lg text-xs text-amber-300 hover:bg-amber-500/30 transition-colors"
                                                    >
                                                        <Zap size={12} />
                                                        +{(
                                                            ((highMarginAlt.catalog_item.expected_price - (highMarginAlt.catalog_item.cost_price || highMarginAlt.catalog_item.expected_price * 0.7)) / highMarginAlt.catalog_item.expected_price * 100) - currentMargin
                                                        ).toFixed(1)}% margin boost
                                                    </button>
                                                )}
                                            </div>

                                            {/* Original Extraction (if different) */}
                                            {item.metadata?.original_extraction && (
                                                <div className="mt-3 p-2 bg-slate-950 rounded text-xs">
                                                    <span className="text-slate-500">Extracted: </span>
                                                    <span className="text-slate-400 font-mono">
                                                        "{item.metadata.original_extraction.item_name || item.metadata.original_extraction.description}"
                                                    </span>
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>

                            {/* Footer Summary */}
                            <div className="px-4 py-3 border-t border-slate-800 bg-slate-900/50">
                                <div className="flex items-center justify-between">
                                    <span className="text-sm text-slate-400">{lineItems.length} items</span>
                                    <div className="flex items-center gap-4">
                                        <span className="text-sm text-slate-400">Total:</span>
                                        <span className="text-xl font-bold text-white">${calculateTotal().toFixed(2)}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* SPLIT VIEW - Recommendations */}
                {viewMode === 'split' && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Left: Extracted Data */}
                        <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
                            <div className="px-4 py-3 border-b border-slate-800 bg-slate-900/50">
                                <h3 className="text-sm font-semibold text-white">Extracted RFQ</h3>
                            </div>
                            <div className="p-4 space-y-3">
                                {lineItems.map((item, index) => (
                                    <div key={index} className="p-3 bg-slate-800/50 rounded-lg border border-slate-700/50">
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="text-sm font-medium text-white">{item.description}</span>
                                            <span className="text-xs text-slate-500">Qty: {item.quantity}</span>
                                        </div>
                                        <div className="text-xs text-slate-400">SKU: {item.sku || 'N/A'} | ${item.unit_price}/unit</div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Right: AI Recommendations */}
                        <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
                            <div className="px-4 py-3 border-b border-slate-800 bg-slate-900/50">
                                <h3 className="text-sm font-semibold text-white flex items-center gap-2">
                                    <Sparkles size={16} className="text-orange-400" />
                                    AI Recommendations
                                </h3>
                            </div>
                            <div className="p-4 space-y-4">
                                {lineItems.map((item, index) => {
                                    const matches = suggestions[index] || [];
                                    const highMarginAlt = findHighMarginAlternatives(item, matches);

                                    if (!highMarginAlt && matches.length === 0) return null;

                                    return (
                                        <div key={index} className="p-3 bg-slate-800/50 rounded-lg border border-slate-700/50">
                                            <p className="text-sm font-medium text-white mb-2">{item.description}</p>
                                            {highMarginAlt && (
                                                <div className="p-2 bg-emerald-500/10 border border-emerald-500/30 rounded">
                                                    <div className="flex items-center justify-between">
                                                        <span className="text-xs text-emerald-400">{highMarginAlt.catalog_item.sku}</span>
                                                        <button
                                                            onClick={() => swapAndOptimize(index, highMarginAlt)}
                                                            className="text-xs px-2 py-1 bg-emerald-600 text-white rounded hover:bg-emerald-500"
                                                        >
                                                            Apply
                                                        </button>
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    </div>
                )}

                {/* TABLE VIEW */}
                {viewMode === 'table' && (
                    <div className="bg-slate-900 rounded-xl border border-slate-800 overflow-hidden">
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead>
                                    <tr className="bg-slate-800/50 text-slate-400 border-b border-slate-800">
                                        <th className="px-4 py-3 text-left">Description</th>
                                        <th className="px-4 py-3 text-left">SKU</th>
                                        <th className="px-4 py-3 text-right">Qty</th>
                                        <th className="px-4 py-3 text-right">Price</th>
                                        <th className="px-4 py-3 text-right">Total</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-800">
                                    {lineItems.map((item, index) => (
                                        <tr key={index} className="hover:bg-slate-800/30">
                                            <td className="px-4 py-3">
                                                <SmartEditor
                                                    content={item.description || ''}
                                                    onChange={(html) => updateItem(index, 'description', html)}
                                                    className="w-full bg-transparent"
                                                    minHeight="60px"
                                                />
                                            </td>
                                            <td className="px-4 py-3">
                                                <input
                                                    type="text"
                                                    value={item.sku || ''}
                                                    onChange={(e) => updateItem(index, 'sku', e.target.value)}
                                                    className="bg-transparent border-0 w-full text-slate-300 focus:ring-0"
                                                />
                                            </td>
                                            <td className="px-4 py-3 text-right">
                                                <input
                                                    type="number"
                                                    value={item.quantity}
                                                    onChange={(e) => updateItem(index, 'quantity', Number(e.target.value))}
                                                    className="bg-transparent border-0 w-20 text-right text-slate-300 focus:ring-0"
                                                    min="1"
                                                />
                                            </td>
                                            <td className="px-4 py-3 text-right">
                                                <input
                                                    type="number"
                                                    value={item.unit_price}
                                                    onChange={(e) => updateItem(index, 'unit_price', Number(e.target.value))}
                                                    className="bg-transparent border-0 w-24 text-right text-slate-300 focus:ring-0"
                                                    step="0.01"
                                                />
                                            </td>
                                            <td className="px-4 py-3 text-right font-medium text-white">
                                                ${(item.quantity * item.unit_price).toFixed(2)}
                                            </td>
                                        </tr>
                                    ))}
                                    <tr className="bg-slate-800/50 font-bold">
                                        <td colSpan={4} className="px-4 py-3 text-right text-slate-300">Total:</td>
                                        <td className="px-4 py-3 text-right text-white text-lg">
                                            ${calculateTotal().toFixed(2)}
                                        </td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}
            </main>

            {/* Email Send Dialog */}
            {showEmailDialog && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
                    <div className="bg-slate-900 rounded-xl border border-slate-800 p-6 w-full max-w-md mx-4">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-semibold text-white">Email Quote</h3>
                            <button
                                onClick={() => setShowEmailDialog(false)}
                                className="p-1 text-slate-400 hover:text-white"
                            >
                                <X size={20} />
                            </button>
                        </div>
                        
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm text-slate-400 mb-1">Customer Email *</label>
                                <input
                                    type="email"
                                    value={emailData.to_email}
                                    onChange={(e) => setEmailData({ ...emailData, to_email: e.target.value })}
                                    placeholder="customer@company.com"
                                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:border-orange-500 focus:outline-none"
                                />
                            </div>
                            
                            <div>
                                <label className="block text-sm text-slate-400 mb-1">Customer Name</label>
                                <input
                                    type="text"
                                    value={emailData.to_name}
                                    onChange={(e) => setEmailData({ ...emailData, to_name: e.target.value })}
                                    placeholder="John Smith"
                                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:border-orange-500 focus:outline-none"
                                />
                            </div>
                            
                            <div>
                                <label className="block text-sm text-slate-400 mb-1">Message (Optional)</label>
                                <textarea
                                    value={emailData.message}
                                    onChange={(e) => setEmailData({ ...emailData, message: e.target.value })}
                                    placeholder="Add a personal message..."
                                    rows={3}
                                    className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:border-orange-500 focus:outline-none resize-none"
                                />
                            </div>
                            
                            <div className="flex items-center gap-3 pt-2">
                                <button
                                    onClick={handleSendEmail}
                                    disabled={!emailData.to_email || sendingEmail}
                                    className="flex-1 px-4 py-2 bg-orange-600 hover:bg-orange-500 disabled:bg-slate-700 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-all"
                                >
                                    {sendingEmail ? 'Sending...' : 'Send Quote'}
                                </button>
                                <button
                                    onClick={() => setShowEmailDialog(false)}
                                    className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg font-medium transition-all"
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default QuoteReview;
