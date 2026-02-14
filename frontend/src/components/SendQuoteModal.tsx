/**
 * SendQuoteModal - Send a quote via email
 */

import React, { useState, useEffect } from 'react';
import { X, Send, Mail, Loader2, CheckCircle, AlertCircle, FileText } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { emailApi } from '../services/api';

interface SendQuoteModalProps {
    quoteId: string;
    quoteNumber: string;
    customerEmail?: string;
    customerName?: string;
    total: number;
    onClose: () => void;
    onSent: () => void;
}

export function SendQuoteModal({ 
    quoteId, 
    quoteNumber, 
    customerEmail, 
    customerName,
    total,
    onClose, 
    onSent 
}: SendQuoteModalProps) {
    const [toEmail, setToEmail] = useState(customerEmail || '');
    const [toName, setToName] = useState(customerName || '');
    const [message, setMessage] = useState('');
    const [includePdf, setIncludePdf] = useState(true);
    const [isSending, setIsSending] = useState(false);
    const [result, setResult] = useState<{success: boolean; message: string} | null>(null);
    const [emailStatus, setEmailStatus] = useState<{enabled: boolean; message: string} | null>(null);

    // Check email status on mount
    useEffect(() => {
        checkEmailStatus();
    }, []);

    const checkEmailStatus = async () => {
        try {
            const response = await emailApi.getStatus();
            setEmailStatus(response.data);
        } catch (err) {
            setEmailStatus({ enabled: false, message: 'Could not check email status' });
        }
    };

    const handleSend = async () => {
        if (!toEmail) return;
        
        setIsSending(true);
        setResult(null);
        
        try {
            const response = await emailApi.sendQuote(quoteId, {
                to_email: toEmail,
                to_name: toName || undefined,
                message: message || undefined,
                include_pdf: includePdf
            });
            
            setResult({ success: true, message: 'Quote sent successfully!' });
            setTimeout(() => {
                onSent();
                onClose();
            }, 1500);
        } catch (err: any) {
            const errorMsg = err.response?.data?.detail || 'Failed to send email';
            setResult({ success: false, message: errorMsg });
        } finally {
            setIsSending(false);
        }
    };

    // If email not configured, show config prompt
    if (emailStatus && !emailStatus.enabled) {
        return (
            <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
                    <div className="flex items-center justify-between mb-4">
                        <h2 className="text-xl font-bold text-slate-900">Email Not Configured</h2>
                        <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
                            <X size={20} />
                        </button>
                    </div>
                    
                    <div className="flex items-start gap-3 p-4 bg-amber-50 border border-amber-200 rounded-lg mb-4">
                        <AlertCircle className="text-amber-600 flex-shrink-0 mt-0.5" size={20} />
                        <div>
                            <p className="text-amber-800 font-medium">SMTP Settings Required</p>
                            <p className="text-amber-700 text-sm mt-1">
                                You need to configure email settings before sending quotes.
                            </p>
                        </div>
                    </div>
                    
                    <div className="flex justify-end gap-3">
                        <Button variant="ghost" onClick={onClose}>
                            Cancel
                        </Button>
                        <Button 
                            onClick={() => window.location.href = '/account/email'}
                            className="bg-orange-500 hover:bg-orange-600"
                        >
                            Configure Email
                        </Button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-xl shadow-xl max-w-lg w-full">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-slate-100">
                    <div>
                        <h2 className="text-xl font-bold text-slate-900">Send Quote</h2>
                        <p className="text-sm text-slate-500 mt-0.5">
                            Quote #{quoteNumber} • ${total.toLocaleString()}
                        </p>
                    </div>
                    <button 
                        onClick={onClose}
                        className="text-slate-400 hover:text-slate-600 p-1 rounded-lg hover:bg-slate-100"
                    >
                        <X size={20} />
                    </button>
                </div>

                {/* Body */}
                <div className="p-6 space-y-4">
                    {/* To Email */}
                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1.5">
                            To Email <span className="text-red-500">*</span>
                        </label>
                        <div className="relative">
                            <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                            <input
                                type="email"
                                value={toEmail}
                                onChange={(e) => setToEmail(e.target.value)}
                                className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none"
                                placeholder="customer@company.com"
                            />
                        </div>
                    </div>

                    {/* To Name */}
                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1.5">
                            Recipient Name
                        </label>
                        <input
                            type="text"
                            value={toName}
                            onChange={(e) => setToName(e.target.value)}
                            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none"
                            placeholder="John Smith"
                        />
                    </div>

                    {/* Custom Message */}
                    <div>
                        <label className="block text-sm font-medium text-slate-700 mb-1.5">
                            Custom Message (Optional)
                        </label>
                        <textarea
                            value={message}
                            onChange={(e) => setMessage(e.target.value)}
                            rows={3}
                            className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none resize-none"
                            placeholder="Add a personal note to your customer..."
                        />
                    </div>

                    {/* Include PDF Toggle */}
                    <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                        <input
                            type="checkbox"
                            id="include_pdf"
                            checked={includePdf}
                            onChange={(e) => setIncludePdf(e.target.checked)}
                            className="w-4 h-4 text-orange-600 border-slate-300 rounded focus:ring-orange-500"
                        />
                        <label htmlFor="include_pdf" className="flex items-center gap-2 text-sm text-slate-700 cursor-pointer">
                            <FileText size={16} className="text-slate-400" />
                            Include PDF attachment
                        </label>
                    </div>

                    {/* Result Message */}
                    {result && (
                        <div className={`flex items-center gap-2 p-3 rounded-lg ${
                            result.success 
                                ? 'bg-green-50 border border-green-200 text-green-800' 
                                : 'bg-red-50 border border-red-200 text-red-800'
                        }`}>
                            {result.success ? (
                                <CheckCircle size={18} className="text-green-600" />
                            ) : (
                                <AlertCircle size={18} className="text-red-600" />
                            )}
                            <span className="text-sm">{result.message}</span>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="flex justify-end gap-3 p-6 border-t border-slate-100">
                    <Button variant="ghost" onClick={onClose}>
                        Cancel
                    </Button>
                    <Button
                        onClick={handleSend}
                        disabled={isSending || !toEmail}
                        className="bg-orange-500 hover:bg-orange-600"
                    >
                        {isSending ? (
                            <>
                                <Loader2 className="animate-spin mr-2" size={16} />
                                Sending...
                            </>
                        ) : (
                            <>
                                <Send size={16} className="mr-2" />
                                Send Quote
                            </>
                        )}
                    </Button>
                </div>
            </div>
        </div>
    );
}
