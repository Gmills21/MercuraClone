/**
 * Onboarding Wizard - 3-step setup for new users
 * Step 1: Upload Product Catalog
 * Step 2: Connect QuickBooks (optional)
 * Step 3: Upload Sample RFQ
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
    Upload, FileSpreadsheet, CheckCircle, ArrowRight, 
    ArrowLeft, Loader2, Sparkles, Building2, Mail,
    SkipForward, Database
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { productsApi, importApi, uploadApi, demoDataApi } from '../services/api';

interface StepProps {
    onNext: () => void;
    onSkip: () => void;
    isLoading: boolean;
}

function Step1Catalog({ onNext, onSkip, isLoading }: StepProps) {
    const [uploaded, setUploaded] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState('');

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setUploading(true);
        setError('');

        try {
            await productsApi.upload(file);
            setUploaded(true);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to upload file');
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-blue-100 text-blue-600 mb-4">
                    <Database size={32} />
                </div>
                <h2 className="text-2xl font-bold text-slate-900">Upload Your Product Catalog</h2>
                <p className="text-slate-600 mt-2">
                    Upload your products so Mercura can match RFQ items to your catalog
                </p>
            </div>

            {error && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                    {error}
                </div>
            )}

            {!uploaded ? (
                <div className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center hover:border-orange-400 transition-colors">
                    <input
                        type="file"
                        accept=".csv,.xlsx,.xls"
                        onChange={handleFileUpload}
                        className="hidden"
                        id="catalog-upload"
                        disabled={uploading}
                    />
                    <label htmlFor="catalog-upload" className="cursor-pointer">
                        <Upload className="mx-auto mb-4 text-slate-400" size={48} />
                        <p className="text-lg font-medium text-slate-700">
                            {uploading ? 'Uploading...' : 'Click to upload CSV or Excel'}
                        </p>
                        <p className="text-sm text-slate-500 mt-1">
                            Supports CSV, XLSX files
                        </p>
                    </label>
                    {uploading && (
                        <Loader2 className="mx-auto mt-4 animate-spin text-orange-500" size={24} />
                    )}
                </div>
            ) : (
                <div className="p-6 bg-green-50 border border-green-200 rounded-xl text-center">
                    <CheckCircle className="mx-auto mb-2 text-green-600" size={48} />
                    <p className="text-lg font-medium text-green-800">Catalog uploaded successfully!</p>
                </div>
            )}

            <div className="flex justify-between pt-4">
                <Button variant="ghost" onClick={onSkip} disabled={isLoading}>
                    <SkipForward size={18} className="mr-2" />
                    Skip for now
                </Button>
                <Button onClick={onNext} disabled={isLoading || !uploaded} className="bg-slate-900">
                    {isLoading ? (
                        <>
                            <Loader2 className="animate-spin mr-2" size={18} />
                            Saving...
                        </>
                    ) : (
                        <>
                            Continue
                            <ArrowRight size={18} className="ml-2" />
                        </>
                    )}
                </Button>
            </div>
        </div>
    );
}

function Step2QuickBooks({ onNext, onSkip, isLoading }: StepProps) {
    const [connected, setConnected] = useState(false);

    return (
        <div className="space-y-6">
            <div className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-green-100 text-green-600 mb-4">
                    <Building2 size={32} />
                </div>
                <h2 className="text-2xl font-bold text-slate-900">Connect QuickBooks</h2>
                <p className="text-slate-600 mt-2">
                    Optional: Connect QuickBooks to sync quotes and invoices automatically
                </p>
            </div>

            {!connected ? (
                <div className="space-y-4">
                    <div className="p-6 border border-slate-200 rounded-xl bg-slate-50">
                        <div className="flex items-center gap-4">
                            <div className="w-12 h-12 bg-[#2CA01C] rounded-lg flex items-center justify-center text-white font-bold text-lg">
                                QB
                            </div>
                            <div className="flex-1">
                                <h3 className="font-semibold text-slate-900">QuickBooks Online</h3>
                                <p className="text-sm text-slate-500">Sync customers, products, and invoices</p>
                            </div>
                            <Button 
                                onClick={() => setConnected(true)}
                                variant="outline"
                                className="border-[#2CA01C] text-[#2CA01C] hover:bg-[#2CA01C]/5"
                            >
                                Connect
                            </Button>
                        </div>
                    </div>

                    <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                        <p className="text-sm text-amber-800">
                            <strong>Note:</strong> QuickBooks connection is optional. You can skip this and connect later from Settings.
                        </p>
                    </div>
                </div>
            ) : (
                <div className="p-6 bg-green-50 border border-green-200 rounded-xl text-center">
                    <CheckCircle className="mx-auto mb-2 text-green-600" size={48} />
                    <p className="text-lg font-medium text-green-800">QuickBooks connected!</p>
                    <p className="text-sm text-green-600 mt-1">Your data will sync automatically</p>
                </div>
            )}

            <div className="flex justify-between pt-4">
                <Button variant="ghost" onClick={onSkip} disabled={isLoading}>
                    <SkipForward size={18} className="mr-2" />
                    Skip for now
                </Button>
                <Button onClick={onNext} disabled={isLoading} className="bg-slate-900">
                    {isLoading ? (
                        <>
                            <Loader2 className="animate-spin mr-2" size={18} />
                            Saving...
                        </>
                    ) : (
                        <>
                            Continue
                            <ArrowRight size={18} className="ml-2" />
                        </>
                    )}
                </Button>
            </div>
        </div>
    );
}

function Step3RFQUpload({ onNext, onSkip, isLoading }: StepProps) {
    const [uploaded, setUploaded] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [error, setError] = useState('');

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setUploading(true);
        setError('');

        try {
            await uploadApi.upload(file);
            setUploaded(true);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to upload file');
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="space-y-6">
            <div className="text-center">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-orange-100 text-orange-600 mb-4">
                    <Mail size={32} />
                </div>
                <h2 className="text-2xl font-bold text-slate-900">Upload a Sample RFQ</h2>
                <p className="text-slate-600 mt-2">
                    Upload a sample RFQ email or PDF so we can show you how extraction works
                </p>
            </div>

            {error && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                    {error}
                </div>
            )}

            {!uploaded ? (
                <div className="border-2 border-dashed border-slate-300 rounded-xl p-8 text-center hover:border-orange-400 transition-colors">
                    <input
                        type="file"
                        accept=".pdf,.eml,.msg,.txt,.png,.jpg,.jpeg"
                        onChange={handleFileUpload}
                        className="hidden"
                        id="rfq-upload"
                        disabled={uploading}
                    />
                    <label htmlFor="rfq-upload" className="cursor-pointer">
                        <Mail className="mx-auto mb-4 text-slate-400" size={48} />
                        <p className="text-lg font-medium text-slate-700">
                            {uploading ? 'Uploading...' : 'Upload RFQ email or PDF'}
                        </p>
                        <p className="text-sm text-slate-500 mt-1">
                            Supports PDF, email files, images
                        </p>
                    </label>
                    {uploading && (
                        <Loader2 className="mx-auto mt-4 animate-spin text-orange-500" size={24} />
                    )}
                </div>
            ) : (
                <div className="p-6 bg-green-50 border border-green-200 rounded-xl text-center">
                    <CheckCircle className="mx-auto mb-2 text-green-600" size={48} />
                    <p className="text-lg font-medium text-green-800">RFQ uploaded!</p>
                    <p className="text-sm text-green-600 mt-1">We'll extract the items automatically</p>
                </div>
            )}

            <div className="flex justify-between pt-4">
                <Button variant="ghost" onClick={onSkip} disabled={isLoading}>
                    <SkipForward size={18} className="mr-2" />
                    Skip for now
                </Button>
                <Button onClick={onNext} disabled={isLoading} className="bg-slate-900">
                    {isLoading ? (
                        <>
                            <Loader2 className="animate-spin mr-2" size={18} />
                            Finishing...
                        </>
                    ) : (
                        <>
                            Go to Dashboard
                            <ArrowRight size={18} className="ml-2" />
                        </>
                    )}
                </Button>
            </div>
        </div>
    );
}

export default function OnboardingWizard() {
    const navigate = useNavigate();
    const [step, setStep] = useState(1);
    const [isLoading, setIsLoading] = useState(false);

    const totalSteps = 3;

    const handleNext = async () => {
        if (step < totalSteps) {
            setStep(step + 1);
        } else {
            // Finish onboarding
            setIsLoading(true);
            localStorage.removeItem('mercura_onboarding_required');
            navigate('/dashboard');
        }
    };

    const handleSkip = async () => {
        if (step < totalSteps) {
            setStep(step + 1);
        } else {
            localStorage.removeItem('mercura_onboarding_required');
            navigate('/dashboard');
        }
    };

    const handleDemoData = async () => {
        setIsLoading(true);
        try {
            await demoDataApi.load();
            localStorage.removeItem('mercura_onboarding_required');
            navigate('/dashboard');
        } catch (err) {
            console.error('Failed to load demo data:', err);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 py-12 px-4">
            <div className="max-w-2xl mx-auto">
                {/* Header */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-orange-500 to-red-600 text-white mb-4">
                        <Sparkles size={24} />
                    </div>
                    <h1 className="text-2xl font-bold text-slate-900">Let's get you set up</h1>
                    <p className="text-slate-600 mt-1">
                        Step {step} of {totalSteps}
                    </p>
                </div>

                {/* Progress bar */}
                <div className="mb-8">
                    <div className="flex gap-2">
                        {[1, 2, 3].map((s) => (
                            <div
                                key={s}
                                className={`h-2 flex-1 rounded-full transition-colors ${
                                    s <= step ? 'bg-orange-500' : 'bg-slate-200'
                                }`}
                            />
                        ))}
                    </div>
                </div>

                {/* Main content card */}
                <div className="bg-white rounded-2xl shadow-xl border border-slate-200 p-8">
                    {step === 1 && (
                        <Step1Catalog onNext={handleNext} onSkip={handleSkip} isLoading={isLoading} />
                    )}
                    {step === 2 && (
                        <Step2QuickBooks onNext={handleNext} onSkip={handleSkip} isLoading={isLoading} />
                    )}
                    {step === 3 && (
                        <Step3RFQUpload onNext={handleNext} onSkip={handleSkip} isLoading={isLoading} />
                    )}
                </div>

                {/* Try demo data option */}
                <div className="mt-8 text-center">
                    <p className="text-sm text-slate-500 mb-3">
                        Want to see how it works first?
                    </p>
                    <Button
                        variant="outline"
                        onClick={handleDemoData}
                        disabled={isLoading}
                        className="border-slate-300"
                    >
                        {isLoading ? (
                            <>
                                <Loader2 className="animate-spin mr-2" size={18} />
                                Loading demo...
                            </>
                        ) : (
                            <>
                                <Sparkles size={18} className="mr-2" />
                                Try with demo data
                            </>
                        )}
                    </Button>
                </div>
            </div>
        </div>
    );
}
