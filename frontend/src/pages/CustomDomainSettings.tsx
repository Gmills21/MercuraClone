import React, { useEffect, useState } from 'react';
import { 
    Globe, CheckCircle, XCircle, AlertCircle, 
    Copy, ExternalLink, RefreshCw, Trash2, Shield,
    Server, BookOpen
} from 'lucide-react';
import { api } from '../services/api';

interface DNSRecord {
    type: string;
    name: string;
    value: string;
    ttl: string;
    notes: string;
}

interface DomainStatus {
    domain: string;
    status: 'pending' | 'verified' | 'active' | 'failed';
    ssl_status: 'pending' | 'active' | 'failed';
    dns_records: DNSRecord[];
    created_at: string;
    verified_at?: string;
    is_active: boolean;
}

export const CustomDomainSettings = () => {
    const [domain, setDomain] = useState('');
    const [domainStatus, setDomainStatus] = useState<DomainStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [verifying, setVerifying] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [copiedRecord, setCopiedRecord] = useState<number | null>(null);

    useEffect(() => {
        loadDomainStatus();
    }, []);

    const loadDomainStatus = async () => {
        try {
            const response = await api.get('/custom-domains/status');
            if (response.data.has_custom_domain) {
                setDomainStatus(response.data);
                setDomain(response.data.domain);
            }
        } catch (error) {
            console.error('Failed to load domain status:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setSuccess('');
        setSubmitting(true);

        try {
            const response = await api.post('/custom-domains/register', { domain });
            setDomainStatus({
                domain: response.data.domain.domain,
                status: 'pending',
                ssl_status: 'pending',
                dns_records: response.data.dns_records,
                created_at: new Date().toISOString(),
                is_active: false
            });
            setSuccess('Domain registered! Add the DNS records below to verify ownership.');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to register domain');
        } finally {
            setSubmitting(false);
        }
    };

    const handleVerify = async () => {
        setVerifying(true);
        setError('');
        setSuccess('');

        try {
            const response = await api.post('/custom-domains/verify');
            if (response.data.success) {
                setSuccess(response.data.message);
                await loadDomainStatus();
            } else {
                setError(response.data.message);
            }
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Verification failed');
        } finally {
            setVerifying(false);
        }
    };

    const handleRemove = async () => {
        if (!confirm('Are you sure you want to remove this custom domain?')) return;

        try {
            await api.post('/custom-domains/remove');
            setDomainStatus(null);
            setDomain('');
            setSuccess('Domain removed successfully');
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to remove domain');
        }
    };

    const copyToClipboard = (text: string, index: number) => {
        navigator.clipboard.writeText(text);
        setCopiedRecord(index);
        setTimeout(() => setCopiedRecord(null), 2000);
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'active':
                return <CheckCircle className="text-green-500" size={20} />;
            case 'verified':
                return <CheckCircle className="text-blue-500" size={20} />;
            case 'pending':
                return <AlertCircle className="text-yellow-500" size={20} />;
            case 'failed':
                return <XCircle className="text-red-500" size={20} />;
            default:
                return null;
        }
    };

    const getStatusText = (status: string) => {
        switch (status) {
            case 'active':
                return 'Active - Your domain is ready to use';
            case 'verified':
                return 'Verified - SSL certificate being provisioned';
            case 'pending':
                return 'Pending - Add DNS records to verify';
            case 'failed':
                return 'Failed - Check DNS configuration';
            default:
                return status;
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-2 border-orange-500 border-t-transparent"></div>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            {/* Header */}
            <div>
                <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
                    <Globe className="text-orange-500" />
                    Custom Domain
                </h2>
                <p className="text-gray-600 mt-2">
                    Use your own domain for a branded experience. Your team and customers can access Mercura through your domain.
                </p>
            </div>

            {/* Error/Success Messages */}
            {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
                    <XCircle className="text-red-500 flex-shrink-0 mt-0.5" size={20} />
                    <p className="text-red-700">{error}</p>
                </div>
            )}
            {success && (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-start gap-3">
                    <CheckCircle className="text-green-500 flex-shrink-0 mt-0.5" size={20} />
                    <p className="text-green-700">{success}</p>
                </div>
            )}

            {/* Domain Registration Form */}
            {!domainStatus && (
                <div className="bg-white border border-gray-200 rounded-xl p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Set Up Your Domain</h3>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                                Domain
                            </label>
                            <input
                                type="text"
                                value={domain}
                                onChange={(e) => setDomain(e.target.value)}
                                placeholder="crm.yourcompany.com"
                                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                                required
                            />
                            <p className="text-sm text-gray-500 mt-1">
                                Enter a subdomain like "crm.yourcompany.com" or your apex domain "yourcompany.com"
                            </p>
                        </div>
                        <button
                            type="submit"
                            disabled={submitting}
                            className="px-6 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors disabled:opacity-50"
                        >
                            {submitting ? 'Registering...' : 'Register Domain'}
                        </button>
                    </form>

                    {/* Instructions */}
                    <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                        <h4 className="font-medium text-blue-900 flex items-center gap-2">
                            <BookOpen size={18} />
                            How it works
                        </h4>
                        <ol className="mt-3 space-y-2 text-sm text-blue-800 list-decimal list-inside">
                            <li>Enter your domain above</li>
                            <li>Add the DNS records we provide to your DNS provider (Cloudflare, GoDaddy, etc.)</li>
                            <li>Click "Verify Domain" to confirm ownership</li>
                            <li>SSL certificate is provisioned automatically</li>
                            <li>Your team can log in at your custom domain!</li>
                        </ol>
                    </div>
                </div>
            )}

            {/* Domain Status */}
            {domainStatus && (
                <div className="space-y-6">
                    {/* Status Card */}
                    <div className="bg-white border border-gray-200 rounded-xl p-6">
                        <div className="flex items-start justify-between">
                            <div>
                                <h3 className="text-lg font-semibold text-gray-900">{domainStatus.domain}</h3>
                                <div className="flex items-center gap-2 mt-2">
                                    {getStatusIcon(domainStatus.status)}
                                    <span className="text-gray-700">{getStatusText(domainStatus.status)}</span>
                                </div>
                            </div>
                            <div className="flex items-center gap-2">
                                {domainStatus.status === 'pending' && (
                                    <button
                                        onClick={handleVerify}
                                        disabled={verifying}
                                        className="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors disabled:opacity-50 flex items-center gap-2"
                                    >
                                        <RefreshCw size={18} className={verifying ? 'animate-spin' : ''} />
                                        {verifying ? 'Verifying...' : 'Verify Domain'}
                                    </button>
                                )}
                                <button
                                    onClick={handleRemove}
                                    className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                                    title="Remove domain"
                                >
                                    <Trash2 size={18} />
                                </button>
                            </div>
                        </div>

                        {/* SSL Status */}
                        {domainStatus.status !== 'pending' && (
                            <div className="mt-4 flex items-center gap-2 text-sm">
                                <Shield size={16} className={domainStatus.ssl_status === 'active' ? 'text-green-500' : 'text-yellow-500'} />
                                <span className="text-gray-600">
                                    SSL: {domainStatus.ssl_status === 'active' ? 'Secured with HTTPS' : 'Provisioning...'}
                                </span>
                            </div>
                        )}

                        {/* Visit Link */}
                        {domainStatus.is_active && (
                            <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
                                <p className="text-sm text-green-800">
                                    Your domain is ready! Visit:
                                </p>
                                <a 
                                    href={`https://${domainStatus.domain}`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="inline-flex items-center gap-2 mt-1 text-green-700 hover:text-green-800 font-medium"
                                >
                                    https://{domainStatus.domain}
                                    <ExternalLink size={14} />
                                </a>
                            </div>
                        )}
                    </div>

                    {/* DNS Records */}
                    {domainStatus.dns_records && domainStatus.dns_records.length > 0 && (
                        <div className="bg-white border border-gray-200 rounded-xl p-6">
                            <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                                <Server size={20} />
                                DNS Records
                            </h3>
                            <p className="text-gray-600 mt-1 text-sm">
                                Add these records to your DNS provider. Changes can take 5-30 minutes to propagate.
                            </p>

                            <div className="mt-4 space-y-3">
                                {domainStatus.dns_records.map((record, index) => (
                                    <div 
                                        key={index}
                                        className="p-4 bg-gray-50 border border-gray-200 rounded-lg"
                                    >
                                        <div className="flex items-start justify-between">
                                            <div className="flex-1">
                                                <div className="flex items-center gap-2">
                                                    <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded">
                                                        {record.type}
                                                    </span>
                                                    <span className="font-medium text-gray-900">{record.name}</span>
                                                </div>
                                                <div className="mt-2 flex items-center gap-2">
                                                    <code className="flex-1 px-3 py-2 bg-white border border-gray-200 rounded text-sm text-gray-700 font-mono">
                                                        {record.value}
                                                    </code>
                                                    <button
                                                        onClick={() => copyToClipboard(record.value, index)}
                                                        className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-200 rounded transition-colors"
                                                        title="Copy value"
                                                    >
                                                        {copiedRecord === index ? (
                                                            <CheckCircle size={18} className="text-green-500" />
                                                        ) : (
                                                            <Copy size={18} />
                                                        )}
                                                    </button>
                                                </div>
                                                <p className="text-xs text-gray-500 mt-2">{record.notes}</p>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>

                            <div className="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                                <h4 className="font-medium text-yellow-900 flex items-center gap-2">
                                    <AlertCircle size={16} />
                                    Common DNS Providers
                                </h4>
                                <ul className="mt-2 space-y-1 text-sm text-yellow-800">
                                    <li>• <strong>Cloudflare:</strong> DNS → Records → Add Record</li>
                                    <li>• <strong>GoDaddy:</strong> My Products → DNS Management</li>
                                    <li>• <strong>Namecheap:</strong> Domain List → Manage → Advanced DNS</li>
                                    <li>• <strong>Google Domains:</strong> DNS → Custom resource records</li>
                                </ul>
                            </div>
                        </div>
                    )}

                    {/* Troubleshooting */}
                    {domainStatus.status === 'pending' && (
                        <div className="bg-gray-50 border border-gray-200 rounded-xl p-6">
                            <h3 className="font-semibold text-gray-900">Troubleshooting</h3>
                            <ul className="mt-3 space-y-2 text-sm text-gray-600">
                                <li>• DNS changes can take up to 24 hours to propagate worldwide</li>
                                <li>• Make sure you don't have conflicting records (e.g., another CNAME for the same subdomain)</li>
                                <li>• For apex domains (example.com), use an ALIAS/ANAME record if available, or A record</li>
                                <li>• The TXT verification record must remain in place permanently</li>
                            </ul>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default CustomDomainSettings;
