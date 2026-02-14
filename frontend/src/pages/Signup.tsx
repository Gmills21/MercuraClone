/**
 * Signup Page - Self-service registration
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, Loader2, ArrowRight, Building2, User, Mail, Lock, Check, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAuth } from '../contexts/AuthContext';

export default function SignupPage() {
    const navigate = useNavigate();
    const { register, isAuthenticated } = useAuth();
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');
    const [formData, setFormData] = useState({
        name: '',
        email: '',
        password: '',
        companyName: '',
    });

    // Redirect if already authenticated
    React.useEffect(() => {
        if (isAuthenticated) {
            navigate('/dashboard');
        }
    }, [isAuthenticated, navigate]);

    // Password strength validation
    const passwordRequirements = [
        { label: 'At least 8 characters', test: (p: string) => p.length >= 8 },
        { label: 'One uppercase letter', test: (p: string) => /[A-Z]/.test(p) },
        { label: 'One lowercase letter', test: (p: string) => /[a-z]/.test(p) },
        { label: 'One number', test: (p: string) => /[0-9]/.test(p) },
        { label: 'One special character', test: (p: string) => /[!@#$%^&*(),.?":{}|<>]/.test(p) },
    ];

    const getPasswordStrength = (password: string) => {
        const passed = passwordRequirements.filter(r => r.test(password)).length;
        if (passed <= 2) return { level: 'weak', color: 'text-red-500', bar: 'bg-red-500', width: '20%' };
        if (passed <= 3) return { level: 'fair', color: 'text-yellow-500', bar: 'bg-yellow-500', width: '40%' };
        if (passed <= 4) return { level: 'good', color: 'text-blue-500', bar: 'bg-blue-500', width: '60%' };
        return { level: 'strong', color: 'text-green-500', bar: 'bg-green-500', width: '100%' };
    };

    const passwordStrength = getPasswordStrength(formData.password);
    const isPasswordValid = passwordRequirements.every(r => r.test(formData.password));

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');

        // Validate password strength
        if (!isPasswordValid) {
            setError('Please meet all password requirements');
            setIsLoading(false);
            return;
        }

        try {
            await register(formData.email, formData.password, formData.name, formData.companyName);
            navigate('/onboarding');
        } catch (err: any) {
            setError(err.message || 'Failed to create account. Please try again.');
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
                    <h1 className="text-2xl font-bold text-slate-900">Create your account</h1>
                    <p className="text-slate-600 mt-1">Start processing RFQs in minutes</p>
                </div>

                {/* Form */}
                <div className="bg-white rounded-2xl shadow-xl border border-slate-200 p-8">
                    {error && (
                        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                            {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-5">
                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1.5">
                                Full Name
                            </label>
                            <div className="relative">
                                <User className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                                <input
                                    type="text"
                                    required
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    className="w-full pl-10 pr-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none transition-all"
                                    placeholder="John Smith"
                                />
                            </div>
                        </div>

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
                            <label className="block text-sm font-medium text-slate-700 mb-1.5">
                                Company Name
                            </label>
                            <div className="relative">
                                <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                                <input
                                    type="text"
                                    required
                                    value={formData.companyName}
                                    onChange={(e) => setFormData({ ...formData, companyName: e.target.value })}
                                    className="w-full pl-10 pr-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none transition-all"
                                    placeholder="Acme Industrial Supply"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-700 mb-1.5">
                                Password
                            </label>
                            <div className="relative">
                                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                                <input
                                    type="password"
                                    required
                                    minLength={8}
                                    value={formData.password}
                                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                                    className="w-full pl-10 pr-4 py-2.5 border border-slate-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500 outline-none transition-all"
                                    placeholder="••••••••"
                                />
                            </div>
                            
                            {/* Password Strength Indicator */}
                            {formData.password && (
                                <div className="mt-3 space-y-2">
                                    <div className="flex items-center justify-between">
                                        <span className="text-xs font-medium text-slate-600">Strength:</span>
                                        <span className={`text-xs font-semibold capitalize ${passwordStrength.color}`}>
                                            {passwordStrength.level}
                                        </span>
                                    </div>
                                    <div className="h-1.5 bg-slate-200 rounded-full overflow-hidden">
                                        <div 
                                            className={`h-full transition-all duration-300 ${passwordStrength.bar}`}
                                            style={{ width: passwordStrength.width }}
                                        />
                                    </div>
                                    
                                    {/* Requirements Checklist */}
                                    <ul className="space-y-1">
                                        {passwordRequirements.map((req, idx) => (
                                            <li key={idx} className="flex items-center gap-1.5 text-xs">
                                                {req.test(formData.password) ? (
                                                    <Check size={12} className="text-green-500" />
                                                ) : (
                                                    <X size={12} className="text-slate-400" />
                                                )}
                                                <span className={req.test(formData.password) ? 'text-slate-600' : 'text-slate-400'}>
                                                    {req.label}
                                                </span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>

                        <Button
                            type="submit"
                            disabled={isLoading}
                            className="w-full bg-slate-900 hover:bg-slate-800 text-white py-3 rounded-lg font-semibold flex items-center justify-center gap-2"
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 className="animate-spin" size={18} />
                                    Creating account...
                                </>
                            ) : (
                                <>
                                    Get Started Free
                                    <ArrowRight size={18} />
                                </>
                            )}
                        </Button>
                    </form>

                    <div className="mt-6 text-center">
                        <p className="text-sm text-slate-600">
                            Already have an account?{' '}
                            <button
                                type="button"
                                onClick={() => navigate('/login')}
                                className="text-orange-600 hover:text-orange-700 font-medium cursor-pointer"
                            >
                                Sign in
                            </button>
                        </p>
                    </div>
                </div>

                {/* Trust indicators */}
                <div className="mt-8 flex items-center justify-center gap-6 text-xs text-slate-500">
                    <span className="flex items-center gap-1">
                        <svg className="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        Free 14-day trial
                    </span>
                    <span className="flex items-center gap-1">
                        <svg className="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        No credit card required
                    </span>
                </div>
            </div>
        </div>
    );
}
