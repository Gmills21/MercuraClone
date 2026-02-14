/**
 * Login Page
 */

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Sparkles, Loader2, ArrowRight, Mail, Lock } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuth } from '../contexts/AuthContext';

export default function LoginPage() {
    const navigate = useNavigate();
    const { login, isAuthenticated } = useAuth();
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [deletedMessage, setDeletedMessage] = useState(false);
    const [formData, setFormData] = useState({
        email: '',
        password: '',
    });

    // Show message if user just deactivated account
    React.useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        if (params.get('deleted') === '1') {
            setDeletedMessage(true);
            window.history.replaceState({}, '', window.location.pathname);
        }
    }, []);

    // Redirect if already authenticated
    React.useEffect(() => {
        if (isAuthenticated) {
            navigate('/dashboard');
        }
    }, [isAuthenticated, navigate]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');

        try {
            await login(formData.email, formData.password);
            navigate('/dashboard');
        } catch (err: any) {
            setError(err.message || 'Invalid email or password');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
            <div className="w-full max-w-md">
                {/* Logo */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-orange-500 to-red-600 text-white mb-4">
                        <Sparkles size={24} />
                    </div>
                    <h1 className="text-2xl font-bold text-slate-900">Welcome back</h1>
                    <p className="text-slate-600 mt-1">Sign in to your account</p>
                </div>

                {/* Form */}
                <div className="bg-white rounded-2xl shadow-xl border border-slate-200 p-8">
                    {deletedMessage && (
                        <div className="mb-4 p-4 bg-slate-100 border border-slate-200 rounded-lg text-slate-700 text-sm">
                            Your account has been deactivated. For full data removal, contact support.
                        </div>
                    )}
                    {error && (
                        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-5">
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1.5">
                                Work Email
                            </label>
                            <div className="relative">
                                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                                <input
                                    type="email"
                                    required
                                    value={formData.email}
                                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                    className="w-full pl-10 pr-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none transition-all"
                                    placeholder="john@company.com"
                                />
                            </div>
                        </div>

                        <div>
                            <div className="flex items-center justify-between mb-1.5">
                                <label className="block text-sm font-medium text-slate-700">
                                    Password
                                </label>
                                <Link
                                    to="/forgot-password"
                                    className="text-sm text-orange-600 hover:text-orange-700 font-medium"
                                >
                                    Forgot password?
                                </Link>
                            </div>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                                <input
                                    type="password"
                                    required
                                    value={formData.password}
                                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                                    className="w-full pl-10 pr-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none transition-all"
                                    placeholder="••••••••"
                                />
                            </div>
                        </div>

                        <Button
                            type="submit"
                            disabled={isLoading}
                            className="w-full bg-slate-900 hover:bg-slate-800 text-white py-3 rounded-lg font-semibold flex items-center justify-center gap-2"
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 className="animate-spin" size={18} />
                                    Signing in...
                                </>
                            ) : (
                                <>
                                    Sign In
                                    <ArrowRight size={18} />
                                </>
                            )}
                        </Button>
                    </form>

                    <div className="mt-6 text-center">
                        <p className="text-sm text-slate-600">
                            Don't have an account?{' '}
                            <button
                                type="button"
                                onClick={() => navigate('/signup')}
                                className="text-orange-600 hover:text-orange-700 font-medium cursor-pointer"
                            >
                                Get started free
                            </button>
                        </p>
                    </div>
                </div>

                {/* Back to home */}
                <div className="mt-6 text-center">
                    <button
                        type="button"
                        onClick={() => navigate('/')}
                        className="text-sm text-slate-500 hover:text-slate-700 cursor-pointer"
                    >
                        ← Back to home
                    </button>
                </div>
            </div>
        </div>
    );
}
