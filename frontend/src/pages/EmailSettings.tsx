/**
 * Email Settings Page
 * Configure SMTP settings for sending quotes via email
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
    Mail, Server, Lock, User, CheckCircle, AlertCircle, 
    Send, ChevronDown, ChevronUp, Loader2, Eye, EyeOff,
    HelpCircle, ArrowLeft
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { settingsApi } from '../services/api';

interface EmailProvider {
    name: string;
    smtp_host: string;
    smtp_port: number;
    use_tls: boolean;
    notes: string;
}

export default function EmailSettingsPage() {
    const navigate = useNavigate();
    const [isLoading, setIsLoading] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [isTesting, setIsTesting] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const [showProviders, setShowProviders] = useState(false);
    const [providers, setProviders] = useState<EmailProvider[]>([]);
    const [testEmail, setTestEmail] = useState('');
    const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);
    
    const [formData, setFormData] = useState({
        smtp_host: 'smtp.gmail.com',
        smtp_port: 587,
        smtp_username: '',
        smtp_password: '',
        from_email: '',
        from_name: 'Mercura',
        use_tls: true,
        is_enabled: false,
    });

    // Load existing settings
    useEffect(() => {
        loadSettings();
        loadProviders();
    }, []);

    const loadSettings = async () => {
        setIsLoading(true);
        try {
            const response = await settingsApi.getEmailSettings();
            const data = response.data;
            if (data.configured) {
                setFormData({
                    smtp_host: data.smtp_host || 'smtp.gmail.com',
                    smtp_port: data.smtp_port || 587,
                    smtp_username: data.smtp_username || '',
                    smtp_password: '', // Don't show password
                    from_email: data.from_email || '',
                    from_name: data.from_name || 'Mercura',
                    use_tls: data.use_tls !== false,
                    is_enabled: data.is_enabled || false,
                });
            }
        } catch (err) {
            console.error('Failed to load email settings:', err);
        } finally {
            setIsLoading(false);
        }
    };

    const loadProviders = async () => {
        try {
            const response = await settingsApi.getEmailProviders();
            setProviders(response.data.providers || []);
        } catch (err) {
            console.error('Failed to load providers:', err);
        }
    };

    const handleSave = async () => {
        setIsSaving(true);
        setMessage(null);
        
        try {
            await settingsApi.updateEmailSettings(formData);
            setMessage({ type: 'success', text: 'Email settings saved successfully!' });
        } catch (err: any) {
            setMessage({ 
                type: 'error', 
                text: err.response?.data?.detail || 'Failed to save settings' 
            });
        } finally {
            setIsSaving(false);
        }
    };

    const handleTest = async () => {
        if (!testEmail) {
            setMessage({ type: 'error', text: 'Please enter a test email address' });
            return;
        }
        
        setIsTesting(true);
        setMessage(null);
        
        try {
            await settingsApi.testEmailConfig(testEmail);
            setMessage({ type: 'success', text: `Test email sent to ${testEmail}! Check your inbox.` });
        } catch (err: any) {
            setMessage({ 
                type: 'error', 
                text: err.response?.data?.detail || 'Failed to send test email' 
            });
        } finally {
            setIsTesting(false);
        }
    };

    const selectProvider = (provider: EmailProvider) => {
        setFormData({
            ...formData,
            smtp_host: provider.smtp_host,
            smtp_port: provider.smtp_port,
            use_tls: provider.use_tls,
        });
        setShowProviders(false);
    };

    const isConfigured = formData.smtp_username && (formData.smtp_password || formData.is_enabled);

    return (
        <div className="min-h-screen bg-slate-50 py-8">
            <div className="max-w-3xl mx-auto px-4 sm:px-6">
                {/* Header */}
                <div className="mb-8">
                    <button 
                        type="button"
                        onClick={() => navigate('/account/billing')}
                        className="flex items-center text-slate-500 hover:text-slate-700 mb-4 cursor-pointer"
                    >
                        <ArrowLeft size={18} className="mr-1" />
                        Back to Account
                    </button>
                    <h1 className="text-2xl font-bold text-slate-900">Email Settings</h1>
                    <p className="text-slate-600 mt-1">
                        Configure SMTP to send quotes directly to customers
                    </p>
                </div>

                {/* Status Card */}
                <div className={`rounded-xl p-4 mb-6 flex items-center gap-3 ${
                    formData.is_enabled 
                        ? 'bg-green-50 border border-green-200' 
                        : 'bg-amber-50 border border-amber-200'
                }`}>
                    {formData.is_enabled ? (
                        <CheckCircle className="text-green-600" size={24} />
                    ) : (
                        <AlertCircle className="text-amber-600" size={24} />
                    )}
                    <div>
                        <p className={`font-medium ${
                            formData.is_enabled ? 'text-green-800' : 'text-amber-800'
                        }`}>
                            {formData.is_enabled ? 'Email is enabled' : 'Email is not configured'}
                        </p>
                        <p className={`text-sm ${
                            formData.is_enabled ? 'text-green-600' : 'text-amber-600'
                        }`}>
                            {formData.is_enabled 
                                ? 'You can send quotes to customers via email' 
                                : 'Configure SMTP settings below to enable email sending'}
                        </p>
                    </div>
                </div>

                {/* Message */}
                {message && (
                    <div className={`rounded-xl p-4 mb-6 ${
                        message.type === 'success' 
                            ? 'bg-green-50 border border-green-200 text-green-800' 
                            : 'bg-red-50 border border-red-200 text-red-800'
                    }`}>
                        {message.text}
                    </div>
                )}

                {/* Main Form */}
                <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
                    <div className="p-6 border-b border-slate-100">
                        <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
                            <Server className="text-orange-500" size={20} />
                            SMTP Configuration
                        </h2>
                        <p className="text-sm text-slate-500 mt-1">
                            Your email provider's SMTP server details
                        </p>
                    </div>

                    <div className="p-6 space-y-6">
                        {/* Quick Provider Select */}
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-2">
                                Quick Setup (Optional)
                            </label>
                            <button
                                type="button"
                                onClick={() => setShowProviders(!showProviders)}
                                className="w-full flex items-center justify-between px-4 py-2 border border-slate-300 rounded-lg text-left hover:bg-slate-50 cursor-pointer"
                            >
                                <span className="text-slate-600">
                                    {showProviders ? 'Hide providers' : 'Select your email provider...'}
                                </span>
                                {showProviders ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                            </button>
                            
                            {showProviders && (
                                <div className="mt-2 border border-slate-200 rounded-lg overflow-hidden">
                                    {providers.map((provider, idx) => (
                                        <button
                                            type="button"
                                            key={idx}
                                            onClick={() => selectProvider(provider)}
                                            className="w-full px-4 py-3 text-left hover:bg-slate-50 border-b border-slate-100 last:border-b-0 cursor-pointer"
                                        >
                                            <p className="font-medium text-slate-900">{provider.name}</p>
                                            <p className="text-xs text-slate-500 mt-0.5">{provider.notes}</p>
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* SMTP Host */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                                    SMTP Host
                                </label>
                                <input
                                    type="text"
                                    value={formData.smtp_host}
                                    onChange={(e) => setFormData({...formData, smtp_host: e.target.value})}
                                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none"
                                    placeholder="smtp.gmail.com"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                                    SMTP Port
                                </label>
                                <input
                                    type="number"
                                    value={formData.smtp_port}
                                    onChange={(e) => setFormData({...formData, smtp_port: parseInt(e.target.value) || 587})}
                                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none"
                                    placeholder="587"
                                />
                            </div>
                        </div>

                        {/* Username */}
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1.5">
                                SMTP Username / Email
                            </label>
                            <div className="relative">
                                <User className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                                <input
                                    type="email"
                                    value={formData.smtp_username}
                                    onChange={(e) => setFormData({...formData, smtp_username: e.target.value})}
                                    className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none"
                                    placeholder="your@email.com"
                                />
                            </div>
                        </div>

                        {/* Password */}
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1.5">
                                SMTP Password
                                {isConfigured && (
                                    <span className="text-slate-400 font-normal ml-2">
                                        (leave blank to keep current)
                                    </span>
                                )}
                            </label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                                <input
                                    type={showPassword ? 'text' : 'password'}
                                    value={formData.smtp_password}
                                    onChange={(e) => setFormData({...formData, smtp_password: e.target.value})}
                                    className="w-full pl-10 pr-12 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none"
                                    placeholder={isConfigured ? '••••••••' : 'Your SMTP password'}
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword(!showPassword)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                                >
                                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                                </button>
                            </div>
                            <p className="text-xs text-slate-500 mt-1">
                                For Gmail, use an <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noopener noreferrer" className="text-orange-600 hover:underline">App Password</a>
                            </p>
                        </div>

                        {/* From Name & Email */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                                    From Name
                                </label>
                                <input
                                    type="text"
                                    value={formData.from_name}
                                    onChange={(e) => setFormData({...formData, from_name: e.target.value})}
                                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none"
                                    placeholder="Your Company Name"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                                    From Email (Optional)
                                </label>
                                <input
                                    type="email"
                                    value={formData.from_email}
                                    onChange={(e) => setFormData({...formData, from_email: e.target.value})}
                                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none"
                                    placeholder={formData.smtp_username || 'same as username'}
                                />
                            </div>
                        </div>

                        {/* TLS Toggle */}
                        <div className="flex items-center gap-3">
                            <input
                                type="checkbox"
                                id="use_tls"
                                checked={formData.use_tls}
                                onChange={(e) => setFormData({...formData, use_tls: e.target.checked})}
                                className="w-4 h-4 text-orange-600 border-slate-300 rounded focus:ring-orange-500"
                            />
                            <label htmlFor="use_tls" className="text-sm text-slate-700">
                                Use TLS encryption (recommended)
                            </label>
                        </div>

                        {/* Enable Toggle */}
                        <div className="flex items-center gap-3 p-4 bg-slate-50 rounded-lg">
                            <input
                                type="checkbox"
                                id="is_enabled"
                                checked={formData.is_enabled}
                                onChange={(e) => setFormData({...formData, is_enabled: e.target.checked})}
                                className="w-4 h-4 text-orange-600 border-slate-300 rounded focus:ring-orange-500"
                            />
                            <div>
                                <label htmlFor="is_enabled" className="text-sm font-medium text-slate-900">
                                    Enable email sending
                                </label>
                                <p className="text-xs text-slate-500">
                                    Turn this on after testing your configuration
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Test Section */}
                    <div className="p-6 border-t border-slate-100 bg-slate-50/50">
                        <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
                            <Send className="text-orange-500" size={16} />
                            Test Configuration
                        </h3>
                        <div className="flex gap-3">
                            <input
                                type="email"
                                value={testEmail}
                                onChange={(e) => setTestEmail(e.target.value)}
                                className="flex-1 px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none"
                                placeholder="Enter email to send test"
                            />
                            <Button
                                onClick={handleTest}
                                disabled={isTesting || !testEmail}
                                variant="outline"
                                className="whitespace-nowrap"
                            >
                                {isTesting ? (
                                    <>
                                        <Loader2 className="animate-spin mr-2" size={16} />
                                        Sending...
                                    </>
                                ) : (
                                    <>
                                        <Send size={16} className="mr-2" />
                                        Send Test
                                    </>
                                )}
                            </Button>
                        </div>
                    </div>

                    {/* Actions */}
                    <div className="p-6 border-t border-slate-100 flex justify-between">
                        <Button
                            variant="ghost"
                            onClick={() => navigate('/account/billing')}
                        >
                            Cancel
                        </Button>
                        <Button
                            onClick={handleSave}
                            disabled={isSaving}
                            className="bg-slate-900 hover:bg-slate-800"
                        >
                            {isSaving ? (
                                <>
                                    <Loader2 className="animate-spin mr-2" size={16} />
                                    Saving...
                                </>
                            ) : (
                                'Save Settings'
                            )}
                        </Button>
                    </div>
                </div>

                {/* Help Section */}
                <div className="mt-8 p-6 bg-blue-50 rounded-xl border border-blue-100">
                    <h3 className="text-sm font-semibold text-blue-900 flex items-center gap-2 mb-2">
                        <HelpCircle size={16} />
                        Need Help?
                    </h3>
                    <ul className="text-sm text-blue-800 space-y-1">
                        <li>• <strong>Gmail users:</strong> Use an <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noopener noreferrer" className="underline">App Password</a> instead of your regular password</li>
                        <li>• <strong>Microsoft 365:</strong> Use your full email as the username</li>
                        <li>• <strong>SendGrid:</strong> Use "apikey" as the username and your API key as the password</li>
                        <li>• Make sure IMAP/POP is enabled in your email settings</li>
                    </ul>
                </div>
            </div>
        </div>
    );
}
