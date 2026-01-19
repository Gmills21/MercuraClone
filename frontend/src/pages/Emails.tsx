import React, { useEffect, useState } from 'react';
import { emailsApi } from '../services/api';
import { Mail, CheckCircle, XCircle, Clock, AlertCircle } from 'lucide-react';

export const Emails = () => {
    const [emails, setEmails] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [statusFilter, setStatusFilter] = useState<string>('');

    useEffect(() => {
        fetchEmails();
    }, [statusFilter]);

    const fetchEmails = () => {
        setLoading(true);
        emailsApi.list(statusFilter)
            .then(res => setEmails(res.data.emails || []))
            .catch(console.error)
            .finally(() => setLoading(false));
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
                                <th className="px-6 py-4">Sender</th>
                                <th className="px-6 py-4">Subject</th>
                                <th className="px-6 py-4">Received</th>
                                <th className="px-6 py-4">Attachments</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/50">
                            {loading ? (
                                <tr><td colSpan={5} className="text-center py-8 text-slate-500">Loading...</td></tr>
                            ) : emails.length === 0 ? (
                                <tr><td colSpan={5} className="text-center py-8 text-slate-500">No emails found.</td></tr>
                            ) : (
                                emails.map((email) => (
                                    <tr key={email.id} className="group hover:bg-slate-800/30 transition-colors">
                                        <td className="px-6 py-4">
                                            <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border capitalize ${getStatusColor(email.status)}`}>
                                                {getStatusIcon(email.status)}
                                                {email.status}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-white font-medium">{email.sender_email}</td>
                                        <td className="px-6 py-4 text-slate-300 max-w-xs truncate">{email.subject_line}</td>
                                        <td className="px-6 py-4 text-slate-400">
                                            {new Date(email.received_at).toLocaleString()}
                                        </td>
                                        <td className="px-6 py-4 text-slate-400">
                                            {email.attachment_count > 0 ? (
                                                <span className="flex items-center gap-1">
                                                    <Mail size={14} /> {email.attachment_count}
                                                </span>
                                            ) : '-'}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};
