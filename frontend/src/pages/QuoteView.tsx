import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { quotesApiExtended } from '../services/api';
import { CheckCircle, AlertCircle, Loader2, Building2, Mail, Phone, FileText, DollarSign } from 'lucide-react';

export const QuoteView = () => {
    const { token } = useParams<{ token: string }>();
    const [quote, setQuote] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [confirming, setConfirming] = useState(false);
    const [confirmed, setConfirmed] = useState(false);
    
    // Form state for confirmation
    const [customerName, setCustomerName] = useState('');
    const [customerEmail, setCustomerEmail] = useState('');
    const [customerPhone, setCustomerPhone] = useState('');
    const [notes, setNotes] = useState('');

    useEffect(() => {
        if (token) {
            fetchQuote(token);
        }
    }, [token]);

    const fetchQuote = async (quoteToken: string) => {
        try {
            setLoading(true);
            setError(null);
            const res = await quotesApiExtended.getPublicQuote(quoteToken);
            setQuote(res.data);
        } catch (err: any) {
            console.error('Error fetching quote:', err);
            if (err.response?.status === 404) {
                setError('Quote not found. The link may be invalid or expired.');
            } else if (err.response?.status === 410) {
                setError('This quote link has expired. Please contact your sales representative for a new quote.');
            } else {
                setError('Failed to load quote. Please try again later.');
            }
        } finally {
            setLoading(false);
        }
    };

    const handleConfirm = async () => {
        if (!token) return;
        
        if (!customerName.trim() || !customerEmail.trim()) {
            alert('Please provide your name and email address.');
            return;
        }

        try {
            setConfirming(true);
            await quotesApiExtended.confirmQuote(token, {
                customer_name: customerName,
                customer_email: customerEmail,
                customer_phone: customerPhone,
                notes: notes
            });
            setConfirmed(true);
        } catch (err: any) {
            console.error('Error confirming quote:', err);
            alert('Failed to confirm quote. Please try again or contact support.');
        } finally {
            setConfirming(false);
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
                <div className="text-center">
                    <Loader2 className="w-12 h-12 text-blue-400 animate-spin mx-auto mb-4" />
                    <p className="text-slate-400">Loading quote...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-4">
                <div className="max-w-md w-full glass-panel rounded-2xl p-8 text-center">
                    <AlertCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
                    <h1 className="text-2xl font-bold text-white mb-2">Quote Not Available</h1>
                    <p className="text-slate-400">{error}</p>
                </div>
            </div>
        );
    }

    if (!quote) {
        return null;
    }

    const totalAmount = quote.items?.reduce((sum: number, item: any) => 
        sum + (Number(item.quantity || 0) * Number(item.unit_price || 0)), 0
    ) || quote.total_amount || 0;

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 py-12 px-4">
            <div className="max-w-4xl mx-auto">
                {/* Header */}
                <div className="glass-panel rounded-2xl p-8 mb-6">
                    <div className="flex items-start justify-between mb-6">
                        <div>
                            <h1 className="text-3xl font-bold text-white mb-2">Quote #{quote.quote_number}</h1>
                            <p className="text-slate-400">
                                {quote.created_at && new Date(quote.created_at).toLocaleDateString('en-US', {
                                    year: 'numeric',
                                    month: 'long',
                                    day: 'numeric'
                                })}
                            </p>
                        </div>
                        <div className="text-right">
                            <div className="text-sm text-slate-400 mb-1">Total Amount</div>
                            <div className="text-3xl font-bold text-white">${totalAmount.toFixed(2)}</div>
                        </div>
                    </div>

                    {/* Customer Info */}
                    {quote.customer && (
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-6 border-t border-slate-700">
                            {quote.customer.name && (
                                <div className="flex items-center gap-2 text-slate-300">
                                    <Building2 size={18} className="text-slate-500" />
                                    <span>{quote.customer.name}</span>
                                </div>
                            )}
                            {quote.customer.email && (
                                <div className="flex items-center gap-2 text-slate-300">
                                    <Mail size={18} className="text-slate-500" />
                                    <span>{quote.customer.email}</span>
                                </div>
                            )}
                            {quote.customer.phone && (
                                <div className="flex items-center gap-2 text-slate-300">
                                    <Phone size={18} className="text-slate-500" />
                                    <span>{quote.customer.phone}</span>
                                </div>
                            )}
                        </div>
                    )}

                    {quote.valid_until && (
                        <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                            <p className="text-sm text-blue-300">
                                <strong>Valid Until:</strong> {new Date(quote.valid_until).toLocaleDateString('en-US', {
                                    year: 'numeric',
                                    month: 'long',
                                    day: 'numeric'
                                })}
                            </p>
                        </div>
                    )}
                </div>

                {/* Line Items */}
                <div className="glass-panel rounded-2xl p-8 mb-6">
                    <h2 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
                        <FileText size={20} />
                        Line Items
                    </h2>
                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead>
                                <tr className="border-b border-slate-700">
                                    <th className="pb-3 text-slate-400 font-medium">Description</th>
                                    <th className="pb-3 text-slate-400 font-medium">SKU</th>
                                    <th className="pb-3 text-slate-400 font-medium text-center">Quantity</th>
                                    <th className="pb-3 text-slate-400 font-medium text-right">Unit Price</th>
                                    <th className="pb-3 text-slate-400 font-medium text-right">Total</th>
                                </tr>
                            </thead>
                            <tbody>
                                {quote.items?.map((item: any, index: number) => (
                                    <tr key={index} className="border-b border-slate-800/50">
                                        <td className="py-4 text-white">{item.description || 'N/A'}</td>
                                        <td className="py-4 text-slate-400 font-mono text-sm">{item.sku || 'N/A'}</td>
                                        <td className="py-4 text-slate-300 text-center">{item.quantity || 1}</td>
                                        <td className="py-4 text-slate-300 text-right">${Number(item.unit_price || 0).toFixed(2)}</td>
                                        <td className="py-4 text-white font-medium text-right">
                                            ${(Number(item.quantity || 0) * Number(item.unit_price || 0)).toFixed(2)}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                            <tfoot>
                                <tr>
                                    <td colSpan={4} className="pt-4 text-right text-lg font-semibold text-slate-300">
                                        Total:
                                    </td>
                                    <td className="pt-4 text-right text-2xl font-bold text-white">
                                        ${totalAmount.toFixed(2)}
                                    </td>
                                </tr>
                            </tfoot>
                        </table>
                    </div>
                </div>

                {/* Confirmation Section */}
                {confirmed ? (
                    <div className="glass-panel rounded-2xl p-8 text-center">
                        <CheckCircle className="w-16 h-16 text-emerald-400 mx-auto mb-4" />
                        <h2 className="text-2xl font-bold text-white mb-2">Quote Confirmed!</h2>
                        <p className="text-slate-400 mb-4">
                            Thank you for confirming this quote. Our sales team will be in touch shortly to process your order.
                        </p>
                        <p className="text-sm text-slate-500">
                            Confirmation Number: {quote.quote_number}
                        </p>
                    </div>
                ) : quote.status === 'accepted' ? (
                    <div className="glass-panel rounded-2xl p-8 text-center">
                        <CheckCircle className="w-16 h-16 text-emerald-400 mx-auto mb-4" />
                        <h2 className="text-2xl font-bold text-white mb-2">Quote Already Confirmed</h2>
                        <p className="text-slate-400">
                            This quote has already been confirmed. Our sales team is processing your order.
                        </p>
                    </div>
                ) : (
                    <div className="glass-panel rounded-2xl p-8">
                        <h2 className="text-xl font-semibold text-white mb-6 flex items-center gap-2">
                            <CheckCircle size={20} />
                            Confirm & Order
                        </h2>
                        <p className="text-slate-400 mb-6">
                            Please provide your contact information to confirm this quote. Our sales team will process your order.
                        </p>
                        
                        <div className="space-y-4 mb-6">
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-2">
                                    Name <span className="text-red-400">*</span>
                                </label>
                                <input
                                    type="text"
                                    value={customerName}
                                    onChange={(e) => setCustomerName(e.target.value)}
                                    className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="Your full name"
                                    required
                                />
                            </div>
                            
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-2">
                                    Email <span className="text-red-400">*</span>
                                </label>
                                <input
                                    type="email"
                                    value={customerEmail}
                                    onChange={(e) => setCustomerEmail(e.target.value)}
                                    className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="your.email@example.com"
                                    required
                                />
                            </div>
                            
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-2">
                                    Phone (Optional)
                                </label>
                                <input
                                    type="tel"
                                    value={customerPhone}
                                    onChange={(e) => setCustomerPhone(e.target.value)}
                                    className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="(555) 123-4567"
                                />
                            </div>
                            
                            <div>
                                <label className="block text-sm font-medium text-slate-300 mb-2">
                                    Additional Notes (Optional)
                                </label>
                                <textarea
                                    value={notes}
                                    onChange={(e) => setNotes(e.target.value)}
                                    rows={4}
                                    className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                                    placeholder="Any special instructions or questions..."
                                />
                            </div>
                        </div>
                        
                        <button
                            onClick={handleConfirm}
                            disabled={confirming || !customerName.trim() || !customerEmail.trim()}
                            className="w-full py-4 bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white font-semibold rounded-lg transition-all duration-200 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {confirming ? (
                                <>
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                    Confirming...
                                </>
                            ) : (
                                <>
                                    <CheckCircle size={20} />
                                    Confirm & Order
                                </>
                            )}
                        </button>
                        
                        <p className="text-xs text-slate-500 text-center mt-4">
                            By confirming, you agree to proceed with this quote. Our sales team will contact you to finalize the order.
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
};
