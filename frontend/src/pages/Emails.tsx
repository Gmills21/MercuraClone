import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { emailsApi, quotesApiExtended, organizationsApi } from '../services/api';
import { queryKeys } from '../lib/queryClient';
import { 
  Mail, CheckCircle, XCircle, Clock, AlertCircle, FileText, Send, Download, Eye, 
  ArrowRight, Sparkles, Search, Copy, RefreshCw
} from 'lucide-react';
import { SkeletonTable, SkeletonText } from '../components/SkeletonScreen';
import { FadeIn, StaggerContainer, StaggerItem } from '../components/PageTransition';

// Hook for organization data
const useOrganization = () => {
  return useQuery({
    queryKey: queryKeys.organization.me,
    queryFn: () => organizationsApi.getMe().then(res => res.data),
    staleTime: 5 * 60 * 1000,
  });
};

// Hook for emails data
const useEmails = (statusFilter: string) => {
  return useQuery({
    queryKey: queryKeys.emails.list(statusFilter, 50),
    queryFn: () => emailsApi.list(statusFilter, 50).then(res => res.data),
    staleTime: 2 * 60 * 1000,
  });
};

export const Emails = () => {
    const navigate = useNavigate();
    const queryClient = useQueryClient();
    const [statusFilter, setStatusFilter] = useState<string>('');
    const [emailQuotes, setEmailQuotes] = useState<{ [key: string]: any[] }>({});
    const [loadingQuotes, setLoadingQuotes] = useState<{ [key: string]: boolean }>({});
    const [draftReplies, setDraftReplies] = useState<{ [key: string]: any }>({});
    const [generatingDraft, setGeneratingDraft] = useState<string | null>(null);

    const { data: org } = useOrganization();
    const { data: emailsData, isLoading, isError, error, refetch } = useEmails(statusFilter);
    const emails = emailsData?.emails || [];

    const fetchQuotesForEmail = useCallback(async (emailId: string) => {
        if (loadingQuotes[emailId]) return;
        setLoadingQuotes(prev => ({ ...prev, [emailId]: true }));
        try {
            const res = await quotesApiExtended.getByEmail(emailId);
            setEmailQuotes(prev => ({ ...prev, [emailId]: res.data.quotes || [] }));
        } catch (error) {
            console.error('Error fetching quotes for email:', error);
        } finally {
            setLoadingQuotes(prev => ({ ...prev, [emailId]: false }));
        }
    }, [loadingQuotes]);

    const handleGenerateQuote = async (email: any) => {
        navigate(`/quotes/new?email_id=${email.id}&sender=${encodeURIComponent(email.sender_email)}&subject=${encodeURIComponent(email.subject_line || '')}`);
    };

    const handleDraftReply = async (quoteId: string, emailId: string) => {
        setGeneratingDraft(quoteId);
        try {
            const res = await quotesApiExtended.draftReply(quoteId);
            setDraftReplies(prev => ({ ...prev, [quoteId]: res.data }));
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

    // Progress Stepper Component
    const getProgressSteps = (email: any) => {
        const steps = [
            { id: 'extracting', label: 'Extracting Specs', icon: FileText, status: 'pending' as const },
            { id: 'matching', label: 'Matching SKUs', icon: Search, status: 'pending' as const },
            { id: 'ready', label: 'Ready for Review', icon: CheckCircle, status: 'pending' as const },
        ];

        if (email.status === 'processing') {
            if (emailQuotes[email.id] && emailQuotes[email.id].length > 0) {
                steps[0].status = 'completed';
                steps[1].status = 'completed';
                steps[2].status = 'active';
            } else {
                steps[0].status = 'active';
            }
        } else if (email.status === 'processed') {
            steps[0].status = 'completed';
            steps[1].status = 'completed';
            steps[2].status = 'completed';
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
                            <div className="flex flex-col items-center gap-1.5">
                                <div
                                    className={`flex items-center justify-center w-10 h-10 rounded-full border-2 transition-all duration-500 ease-out ${
                                        step.status === 'completed'
                                            ? 'bg-emerald-500/20 border-emerald-500 text-emerald-400 scale-100'
                                            : step.status === 'active'
                                                ? 'bg-blue-500/20 border-blue-500 text-blue-400 scale-110 shadow-lg shadow-blue-500/20'
                                                : 'bg-slate-800/50 border-slate-600 text-slate-500 scale-95 opacity-60'
                                    }`}
                                >
                                    <Icon size={18} className={step.status === 'active' ? 'animate-pulse' : ''} />
                                </div>
                                <span className={`text-xs font-medium transition-all duration-300 ${
                                    step.status === 'completed'
                                        ? 'text-emerald-400'
                                        : step.status === 'active'
                                            ? 'text-blue-400 font-semibold'
                                            : 'text-slate-500'
                                }`}>
                                    {step.label}
                                </span>
                                {step.status === 'completed' && isLast && (
                                    <span className="text-[10px] text-emerald-400 font-bold uppercase tracking-wider animate-in fade-in slide-in-from-bottom-2">
                                        Ready to Quote!
                                    </span>
                                )}
                            </div>
                            {!isLast && (
                                <div className="relative w-12 h-1 mx-1 overflow-hidden rounded-full bg-slate-700">
                                    <div
                                        className={`absolute left-0 top-0 h-full bg-emerald-500 rounded-full transition-all duration-700 ease-out ${
                                            step.status === 'completed' ? 'w-full' : 'w-0'
                                        }`}
                                    />
                                </div>
                            )}
                        </React.Fragment>
                    );
                })}
            </div>
        );
    };

    // Show skeleton on first load
    if (isLoading && emails.length === 0) {
        return (
            <div className="space-y-6 p-8">
                <div className="flex items-center justify-between">
                    <div>
                        <SkeletonText className="w-48" lineHeight="h-8" />
                        <div className="mt-1">
                            <SkeletonText className="w-64" lines={1} />
                        </div>
                    </div>
                    <div className="flex gap-2">
                        {['All', 'Processed', 'Failed', 'Pending'].map((_, i) => (
                            <div key={i} className="h-8 w-20 bg-gray-100 rounded-lg animate-pulse" />
                        ))}
                    </div>
                </div>
                <SkeletonTable rows={6} columns={7} />
            </div>
        );
    }

    // Error state
    if (isError) {
        return (
            <div className="space-y-6 p-8">
                <FadeIn>
                    <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
                        <p className="text-red-600 mb-4">
                            {error instanceof Error ? error.message : 'Unable to load inbox. Check that the backend is running and try again.'}
                        </p>
                        <button 
                            onClick={() => refetch()} 
                            className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700"
                        >
                            Retry
                        </button>
                    </div>
                </FadeIn>
            </div>
        );
    }

    return (
        <div className="space-y-6 p-8">
            <FadeIn>
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">Inbound Emails</h1>
                        <p className="text-gray-500">Monitor email ingestion and processing status</p>
                    </div>
                    <div className="flex gap-2">
                        {['', 'processed', 'failed', 'pending'].map((status) => (
                            <button
                                key={status || 'all'}
                                onClick={() => setStatusFilter(status)}
                                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors border ${
                                    statusFilter === status
                                        ? 'bg-slate-800 text-slate-200 border-slate-700'
                                        : 'bg-white text-slate-900 border-slate-200 hover:bg-slate-100'
                                }`}
                            >
                                {status === '' ? 'All' : status.charAt(0).toUpperCase() + status.slice(1)}
                            </button>
                        ))}
                    </div>
                </div>
            </FadeIn>

            {/* Dedicated Inbound Banner */}
            <FadeIn delay={0.05}>
                <div className="bg-gradient-to-r from-orange-600/20 to-orange-500/5 border border-orange-500/20 rounded-2xl p-6 mb-6">
                    <div className="flex flex-col md:flex-row items-center justify-between gap-6">
                        <div className="flex items-start gap-4">
                            <div className="p-3 bg-orange-500 rounded-xl text-white shadow-lg shadow-orange-500/20">
                                <Sparkles size={24} />
                            </div>
                            <div>
                                <h2 className="text-xl font-bold text-gray-900 mb-1">Dedicated Email Inbound</h2>
                                <p className="text-gray-500 text-sm max-w-md">
                                    Forward your customer RFQs directly to this address. Our AI will automatically extract details, deadlines, and populate your inbox.
                                </p>
                            </div>
                        </div>
                        <div className="flex flex-col items-center md:items-end gap-2">
                            <div className="flex items-center gap-2 bg-slate-900/80 border border-slate-700 px-4 py-3 rounded-xl">
                                <code className="text-orange-400 font-mono font-bold">
                                    requests@{org?.slug || 'yourcompany'}.mercura.io
                                </code>
                                <button
                                    onClick={() => {
                                        navigator.clipboard.writeText(`requests@${org?.slug || 'yourcompany'}.mercura.io`);
                                        alert('Copied to clipboard!');
                                    }}
                                    className="p-1.5 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition-colors"
                                >
                                    <Copy size={16} />
                                </button>
                            </div>
                            <span className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">
                                Active & Ready for Intake
                            </span>
                        </div>
                    </div>
                </div>
            </FadeIn>

            {/* Emails Table */}
            <FadeIn delay={0.1}>
                <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
                    <div className="overflow-x-auto">
                        <table className="w-full text-left text-sm">
                            <thead>
                                <tr className="bg-gray-50/50 border-b border-gray-100">
                                    <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase">Status</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase">Progress</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase">Sender</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase">Subject</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase">Received</th>
                                    <th className="px-6 py-4 text-xs font-semibold text-gray-500 uppercase">Quotes</th>
                                    <th className="px-6 py-4 text-right text-xs font-semibold text-gray-500 uppercase">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                                {emails.length === 0 ? (
                                    <tr>
                                        <td colSpan={7} className="text-center py-12 text-gray-500">
                                            No emails found.
                                        </td>
                                    </tr>
                                ) : (
                                    emails.map((email: any) => {
                                        const quotes = emailQuotes[email.id] || [];
                                        const hasQuotes = quotes.length > 0;

                                        return (
                                            <React.Fragment key={email.id}>
                                                <tr className="group hover:bg-gray-50/50 transition-colors">
                                                    <td className="px-6 py-4">
                                                        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border capitalize ${
                                                            getStatusColor(email.status)
                                                        }`}>
                                                            {getStatusIcon(email.status)}
                                                            {email.status}
                                                        </span>
                                                    </td>
                                                    <td className="px-6 py-4">
                                                        <ProgressStepper email={email} />
                                                    </td>
                                                    <td className="px-6 py-4 font-medium text-gray-900">{email.sender_email}</td>
                                                    <td className="px-6 py-4 text-gray-600 max-w-xs truncate" title={email.subject_line}>
                                                        {email.subject_line || '(No subject)'}
                                                    </td>
                                                    <td className="px-6 py-4 text-gray-500">
                                                        {new Date(email.received_at).toLocaleString()}
                                                    </td>
                                                    <td className="px-6 py-4">
                                                        {loadingQuotes[email.id] ? (
                                                            <span className="text-xs text-gray-500">Loading...</span>
                                                        ) : hasQuotes ? (
                                                            <div className="flex items-center gap-2">
                                                                <FileText size={14} className="text-blue-500" />
                                                                <span className="text-sm text-blue-500 font-medium">{quotes.length}</span>
                                                            </div>
                                                        ) : email.status === 'processed' ? (
                                                            <button
                                                                onClick={() => handleGenerateQuote(email)}
                                                                className="text-xs text-blue-500 hover:text-blue-600 flex items-center gap-1"
                                                            >
                                                                <Sparkles size={12} />
                                                                Create Quote
                                                            </button>
                                                        ) : (
                                                            <span className="text-xs text-gray-500">-</span>
                                                        )}
                                                    </td>
                                                    <td className="px-6 py-4">
                                                        <div className="flex items-center justify-end gap-2">
                                                            {hasQuotes && (
                                                                <>
                                                                    {quotes.map((quote: any) => (
                                                                        <div key={quote.id} className="flex items-center gap-1">
                                                                            <button
                                                                                type="button"
                                                                                onClick={() => navigate(`/quotes/${quote.id}`)}
                                                                                className="p-1.5 hover:bg-gray-100 rounded text-gray-400 hover:text-gray-600 transition-colors cursor-pointer"
                                                                                title="View Quote"
                                                                            >
                                                                                <Eye size={14} />
                                                                            </button>
                                                                            <button
                                                                                type="button"
                                                                                onClick={() => handleDownloadQuote(quote.id, quote.quote_number)}
                                                                                className="p-1.5 hover:bg-gray-100 rounded text-gray-400 hover:text-gray-600 transition-colors cursor-pointer"
                                                                                title="Download Quote"
                                                                            >
                                                                                <Download size={14} />
                                                                            </button>
                                                                            <button
                                                                                onClick={() => handleDraftReply(quote.id, email.id)}
                                                                                disabled={generatingDraft === quote.id}
                                                                                className="p-1.5 hover:bg-gray-100 rounded text-gray-400 hover:text-gray-600 transition-colors disabled:opacity-50"
                                                                                title="Draft Reply Email"
                                                                            >
                                                                                {generatingDraft === quote.id ? (
                                                                                    <RefreshCw size={14} className="animate-spin" />
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
                                                                    className="px-3 py-1.5 bg-orange-600 hover:bg-orange-700 text-white text-xs font-medium rounded-lg flex items-center gap-1 transition-colors"
                                                                >
                                                                    <Sparkles size={12} />
                                                                    Quick Quote
                                                                </button>
                                                            )}
                                                        </div>
                                                    </td>
                                                </tr>
                                            </React.Fragment>
                                        );
                                    })
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            </FadeIn>
        </div>
    );
};

export default Emails;
