import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { emailsApi, quotesApiExtended } from '../services/api';
import { Mail, CheckCircle, XCircle, Clock, AlertCircle, FileText, Send, Download, Eye, ArrowRight, Sparkles, Search, Package } from 'lucide-react';

export const Emails = () => {
    const navigate = useNavigate();
    const [emails, setEmails] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [statusFilter, setStatusFilter] = useState<string>('');
    const [emailQuotes, setEmailQuotes] = useState<{[key: string]: any[]}>({});
    const [loadingQuotes, setLoadingQuotes] = useState<{[key: string]: boolean}>({});
    const [draftReplies, setDraftReplies] = useState<{[key: string]: any}>({});
    const [generatingDraft, setGeneratingDraft] = useState<string | null>(null);

    useEffect(() => {
        fetchEmails();
    }, [statusFilter]);

    const fetchEmails = () => {
        setLoading(true);
        emailsApi.list(statusFilter)
            .then(res => {
                const emailList = res.data.emails || [];
                setEmails(emailList);
                // Fetch quotes for processed emails
                emailList.forEach((email: any) => {
                    if (email.status === 'processed') {
                        fetchQuotesForEmail(email.id);
                    }
                });
            })
            .catch(console.error)
            .finally(() => setLoading(false));
    };

    const fetchQuotesForEmail = async (emailId: string) => {
        if (loadingQuotes[emailId]) return;
        setLoadingQuotes({...loadingQuotes, [emailId]: true});
        try {
            const res = await quotesApiExtended.getByEmail(emailId);
            setEmailQuotes({...emailQuotes, [emailId]: res.data.quotes || []});
        } catch (error) {
            console.error('Error fetching quotes for email:', error);
        } finally {
            setLoadingQuotes({...loadingQuotes, [emailId]: false});
        }
    };

    const handleGenerateQuote = async (email: any) => {
        // Navigate to create quote page with email context
        navigate(`/quotes/new?email_id=${email.id}&sender=${encodeURIComponent(email.sender_email)}&subject=${encodeURIComponent(email.subject_line || '')}`);
    };

    const handleDraftReply = async (quoteId: string, emailId: string) => {
        setGeneratingDraft(quoteId);
        try {
            const res = await quotesApiExtended.draftReply(quoteId);
            setDraftReplies({...draftReplies, [quoteId]: res.data});
            
            // Open email client with draft
            const mailtoLink = `mailto:${res.data.to_email}?subject=${encodeURIComponent(res.data.subject)}&body=${encodeURIComponent(res.data.body)}`;
            window.open(mailtoLink);
        } catch (error) {
            console.error('Error generating draft reply:', error);
            alert('Failed to generate draft reply');
        } finally {
            setGeneratingDraft(null);
        }
    };

    const handleDownloadQuote = async (quoteId: string, quoteNumber: string) => {
        try {
            const res = await quotesApiExtended.generateExport(quoteId, 'excel');
            const blob = new Blob([res.data], { 
                type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
            });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `Quote_${quoteNumber}.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            console.error('Error downloading quote:', error);
            alert('Failed to download quote');
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'processed': return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
            case 'failed': return 'bg-red-500/10 text-red-400 border-red-500/20';
            case 'processing': return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
            default: return 'bg-slate-500/10 text-slate-400 border-slate-500/20';
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'processed': return <CheckCircle size={14} />;
            case 'failed': return <XCircle size={14} />;
            case 'processing': return <Clock size={14} />;
            default: return <AlertCircle size={14} />;
        }
    };

    // Phase 3: Progress Stepper Component
    const getProgressSteps = (email: any) => {
        const steps = [
            { 
                id: 'extracting', 
                label: 'Extracting Specs', 
                icon: FileText,
                status: 'pending' as 'pending' | 'active' | 'completed'
            },
            { 
                id: 'matching', 
                label: 'Matching SKUs', 
                icon: Search,
                status: 'pending' as 'pending' | 'active' | 'completed'
            },
            { 
                id: 'ready', 
                label: 'Ready for Review', 
                icon: CheckCircle,
                status: 'pending' as 'pending' | 'active' | 'completed'
            }
        ];

        if (email.status === 'processing') {
            // Determine which step based on whether quotes exist
            if (emailQuotes[email.id] && emailQuotes[email.id].length > 0) {
                steps[0].status = 'completed';
                steps[1].status = 'completed';
                steps[2].status = 'active';
            } else {
                steps[0].status = 'active';
                steps[1].status = 'pending';
                steps[2].status = 'pending';
            }
        } else if (email.status === 'processed') {
            steps[0].status = 'completed';
            steps[1].status = 'completed';
            steps[2].status = 'completed';
        } else if (email.status === 'failed') {
            // Find the step that failed (usually extraction)
            steps[0].status = 'completed';
            steps[1].status = 'pending';
            steps[2].status = 'pending';
        }

        return steps;
    };

    const ProgressStepper = ({ email }: { email: any }) => {
        const steps = getProgressSteps(email);
        
        return (
            <div className="flex items-center gap-2 py-2">
                {steps.map((step, index) => {
                    const Icon = step.icon;
                    const isLast = index === steps.length - 1;
                    
                    return (
                        <React.Fragment key={step.id}>
                            <div className="flex flex-col items-center gap-1">
                                <div className={`flex items-center justify-center w-8 h-8 rounded-full border-2 transition-colors ${
                                    step.status === 'completed' 
                                        ? 'bg-emerald-500/20 border-emerald-500 text-emerald-400' 
                                        : step.status === 'active'
                                        ? 'bg-blue-500/20 border-blue-500 text-blue-400 animate-pulse'
                                        : 'bg-slate-800/50 border-slate-600 text-slate-500'
                                }`}>
                                    <Icon size={14} />
                                </div>
                                <span className={`text-xs font-medium ${
                                    step.status === 'completed' 
                                        ? 'text-emerald-400' 
                                        : step.status === 'active'
                                        ? 'text-blue-400'
                                        : 'text-slate-500'
                                }`}>
                                    {step.label}
                                </span>
                            </div>
                            {!isLast && (
                                <div className={`w-8 h-0.5 mx-1 transition-colors ${
                                    step.status === 'completed' 
                                        ? 'bg-emerald-500' 
                                        : 'bg-slate-700'
                                }`} />
                            )}
                        </React.Fragment>
                    );
                })}
            </div>
        );
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-white">Inbound Emails</h1>
                    <p className="text-slate-400">Monitor email ingestion and processing status</p>
                </div>
                <div className="flex gap-2">
                    {['', 'processed', 'failed', 'pending'].map((status) => (
                        <button
                            key={status}
                            onClick={() => setStatusFilter(status)}
                            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors border ${
                                statusFilter === status
                                    ? 'bg-primary-500/20 text-primary-400 border-primary-500/30'
                                    : 'bg-slate-800/50 text-slate-400 border-slate-700 hover:bg-slate-800 hover:text-slate-200'
                            }`}
                        >
                            {status === '' ? 'All' : status.charAt(0).toUpperCase() + status.slice(1)}
                        </button>
                    ))}
                </div>
            </div>

            <div className="glass-panel rounded-2xl overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead>
                            <tr className="bg-slate-800/30 text-slate-400 border-b border-slate-700/50">
                                <th className="px-6 py-4">Status</th>
                                <th className="px-6 py-4">Progress</th>
                                <th className="px-6 py-4">Sender</th>
                                <th className="px-6 py-4">Subject</th>
                                <th className="px-6 py-4">Received</th>
                                <th className="px-6 py-4">Quotes</th>
                                <th className="px-6 py-4 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/50">
                            {loading ? (
                                <tr><td colSpan={7} className="text-center py-8 text-slate-500">Loading...</td></tr>
                            ) : emails.length === 0 ? (
                                <tr><td colSpan={7} className="text-center py-8 text-slate-500">No emails found.</td></tr>
                            ) : (
                                emails.map((email) => {
                                    const quotes = emailQuotes[email.id] || [];
                                    const hasQuotes = quotes.length > 0;
                                    
                                    return (
                                        <React.Fragment key={email.id}>
                                            <tr className="group hover:bg-slate-800/30 transition-colors">
                                                <td className="px-6 py-4">
                                                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border capitalize ${getStatusColor(email.status)}`}>
                                                        {getStatusIcon(email.status)}
                                                        {email.status}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <ProgressStepper email={email} />
                                                </td>
                                                <td className="px-6 py-4 text-white font-medium">{email.sender_email}</td>
                                                <td className="px-6 py-4 text-slate-300 max-w-xs truncate" title={email.subject_line}>
                                                    {email.subject_line || '(No subject)'}
                                                </td>
                                                <td className="px-6 py-4 text-slate-400">
                                                    {new Date(email.received_at).toLocaleString()}
                                                </td>
                                                <td className="px-6 py-4">
                                                    {loadingQuotes[email.id] ? (
                                                        <span className="text-xs text-slate-500">Loading...</span>
                                                    ) : hasQuotes ? (
                                                        <div className="flex items-center gap-2">
                                                            <FileText size={14} className="text-blue-400" />
                                                            <span className="text-sm text-blue-400 font-medium">{quotes.length}</span>
                                                        </div>
                                                    ) : email.status === 'processed' ? (
                                                        <button
                                                            onClick={() => handleGenerateQuote(email)}
                                                            className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"
                                                        >
                                                            <Sparkles size={12} />
                                                            Create Quote
                                                        </button>
                                                    ) : (
                                                        <span className="text-xs text-slate-500">-</span>
                                                    )}
                                                </td>
                                                <td className="px-6 py-4">
                                                    <div className="flex items-center justify-end gap-2">
                                                        {hasQuotes && (
                                                            <>
                                                                {quotes.map((quote: any) => (
                                                                    <div key={quote.id} className="flex items-center gap-1">
                                                                        <button
                                                                            onClick={() => navigate(`/quotes/${quote.id}`)}
                                                                            className="p-1.5 hover:bg-slate-700 rounded text-slate-400 hover:text-white transition-colors"
                                                                            title="View Quote"
                                                                        >
                                                                            <Eye size={14} />
                                                                        </button>
                                                                        <button
                                                                            onClick={() => handleDownloadQuote(quote.id, quote.quote_number)}
                                                                            className="p-1.5 hover:bg-slate-700 rounded text-slate-400 hover:text-white transition-colors"
                                                                            title="Download Quote"
                                                                        >
                                                                            <Download size={14} />
                                                                        </button>
                                                                        <button
                                                                            onClick={() => handleDraftReply(quote.id, email.id)}
                                                                            disabled={generatingDraft === quote.id}
                                                                            className="p-1.5 hover:bg-slate-700 rounded text-slate-400 hover:text-white transition-colors disabled:opacity-50"
                                                                            title="Draft Reply Email"
                                                                        >
                                                                            {generatingDraft === quote.id ? (
                                                                                <Clock size={14} className="animate-spin" />
                                                                            ) : (
                                                                                <Send size={14} />
                                                                            )}
                                                                        </button>
                                                                    </div>
                                                                ))}
                                                            </>
                                                        )}
                                                        {email.status === 'processed' && !hasQuotes && (
                                                            <button
                                                                onClick={() => handleGenerateQuote(email)}
                                                                className="btn-primary text-xs py-1.5 px-3 flex items-center gap-1"
                                                            >
                                                                <Sparkles size={12} />
                                                                Quick Quote
                                                            </button>
                                                        )}
                                                    </div>
                                                </td>
                                            </tr>
                                            {/* Expanded Quote Details */}
                                            {hasQuotes && quotes.length > 0 && (
                                                <tr className="bg-slate-900/30">
                                                    <td colSpan={7} className="px-6 py-4">
                                                        <div className="space-y-3">
                                                            <div className="text-xs font-semibold text-slate-400 mb-2">Generated Quotes:</div>
                                                            {quotes.map((quote: any) => (
                                                                <div key={quote.id} className="flex items-center justify-between p-3 bg-slate-800/50 rounded-lg border border-slate-700/50">
                                                                    <div className="flex-1">
                                                                        <div className="flex items-center gap-3 mb-1">
                                                                            <span className="text-sm font-medium text-white">{quote.quote_number}</span>
                                                                            <span className={`text-xs px-2 py-0.5 rounded-full ${
                                                                                quote.status === 'draft' ? 'bg-amber-500/10 text-amber-400' :
                                                                                quote.status === 'sent' ? 'bg-blue-500/10 text-blue-400' :
                                                                                'bg-slate-500/10 text-slate-400'
                                                                            }`}>
                                                                                {quote.status.replace('_', ' ')}
                                                                            </span>
                                                                        </div>
                                                                        <div className="text-xs text-slate-400">
                                                                            Total: ${quote.total_amount?.toFixed(2) || '0.00'} • {quote.items?.length || 0} items
                                                                        </div>
                                                                    </div>
                                                                    <div className="flex items-center gap-2">
                                                                        <button
                                                                            onClick={() => navigate(`/quotes/${quote.id}`)}
                                                                            className="btn-secondary text-xs py-1.5 px-3 flex items-center gap-1"
                                                                        >
                                                                            <Eye size={12} />
                                                                            Review
                                                                        </button>
                                                                        <button
                                                                            onClick={() => handleDownloadQuote(quote.id, quote.quote_number)}
                                                                            className="btn-secondary text-xs py-1.5 px-3 flex items-center gap-1"
                                                                        >
                                                                            <Download size={12} />
                                                                            Download
                                                                        </button>
                                                                        <button
                                                                            onClick={() => handleDraftReply(quote.id, email.id)}
                                                                            disabled={generatingDraft === quote.id}
                                                                            className="btn-primary text-xs py-1.5 px-3 flex items-center gap-1"
                                                                        >
                                                                            {generatingDraft === quote.id ? (
                                                                                <Clock size={12} className="animate-spin" />
                                                                            ) : (
                                                                                <>
                                                                                    <Send size={12} />
                                                                                    Draft Reply
                                                                                </>
                                                                            )}
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
                                })
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};
