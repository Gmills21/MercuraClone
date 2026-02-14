/**
 * Hero Section Component - Production Ready
 * 
 * Above-the-fold hero with compelling headline, CTAs, and actual app mockups
 * Positioning: "AI Inside Sales Agent for Industrial Distributors"
 */

import { Button } from '../ui/button';
import { ArrowRight, Sparkles, TrendingUp, Mail, Clock, Zap, FileText, Users, ArrowUpRight } from 'lucide-react';
import { motion } from 'framer-motion';

// Dashboard Preview Components
const TodayViewMock = () => (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {/* Header */}
        <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
            <div>
                <p className="text-[10px] text-slate-400 font-medium uppercase tracking-wider">Today</p>
                <p className="text-xs font-bold text-slate-900">Monday, January 13</p>
            </div>
            <button className="bg-gradient-to-r from-orange-500 to-red-500 text-white text-[10px] font-semibold px-3 py-1.5 rounded-lg flex items-center gap-1">
                <Sparkles size={10} />
                New Request
            </button>
        </div>

        {/* Bento Grid */}
        <div className="p-3 grid grid-cols-3 gap-2">
            {/* Pipeline Card */}
            <div className="col-span-2 bg-white rounded-lg border border-slate-100 p-3 shadow-sm">
                <div className="flex items-center gap-1.5 mb-2">
                    <TrendingUp size={10} className="text-green-600" />
                    <span className="text-[9px] font-semibold text-slate-500 uppercase">Pipeline Value</span>
                </div>
                <p className="text-lg font-bold text-slate-900 tracking-tight">$1,247,500</p>
                <div className="flex items-center gap-1 mt-1">
                    <span className="text-[8px] text-green-600 bg-green-50 px-1.5 py-0.5 rounded-full font-medium">+12.5%</span>
                    <span className="text-[8px] text-slate-400">vs last week</span>
                </div>
            </div>

            {/* Inbox Card */}
            <div className="bg-blue-50 rounded-lg border border-blue-100 p-3">
                <Mail size={14} className="text-blue-600 mb-2" />
                <p className="text-lg font-bold text-slate-900">8</p>
                <p className="text-[9px] text-slate-600">Pending RFQs</p>
            </div>

            {/* Follow-ups */}
            <div className="bg-amber-50 rounded-lg border border-amber-100 p-3">
                <Clock size={14} className="text-amber-600 mb-2" />
                <p className="text-lg font-bold text-slate-900">5</p>
                <p className="text-[9px] text-slate-600">Follow-ups</p>
            </div>

            {/* AI Priorities */}
            <div className="col-span-2 bg-gradient-to-br from-orange-50 to-amber-50 rounded-lg border border-orange-100 p-3">
                <div className="flex items-center gap-1.5 mb-2">
                    <Zap size={10} className="text-orange-600 fill-orange-500" />
                    <span className="text-[9px] font-semibold text-slate-700 uppercase">AI Priorities</span>
                </div>
                <div className="space-y-1.5">
                    <div className="bg-white rounded-md p-1.5 border border-orange-100/50">
                        <div className="flex items-center justify-between">
                            <span className="text-[8px] font-medium text-slate-700">3 RFQs need extraction</span>
                            <span className="text-[7px] text-red-500 font-semibold bg-red-50 px-1 rounded">HIGH</span>
                        </div>
                    </div>
                    <div className="bg-white rounded-md p-1.5 border border-orange-100/50">
                        <div className="flex items-center justify-between">
                            <span className="text-[8px] font-medium text-slate-700">Acme Corp follow-up</span>
                            <span className="text-[7px] text-amber-500 font-semibold bg-amber-50 px-1 rounded">DUE</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
);

const QuoteTableMock = () => (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
            <p className="text-xs font-bold text-slate-900">Recent Quotes</p>
            <span className="text-[10px] text-orange-600 font-medium">View all →</span>
        </div>
        <div className="p-2">
            {[
                { customer: 'Industrial Supply Co.', status: 'sent', value: '$45,200', color: 'blue' },
                { customer: 'Metro HVAC Systems', status: 'approved', value: '$128,500', color: 'green' },
                { customer: 'Premier Plumbing', status: 'draft', value: '$23,800', color: 'gray' },
            ].map((quote, i) => (
                <div key={i} className="flex items-center justify-between py-2 px-2 hover:bg-slate-50 rounded-lg group cursor-pointer">
                    <div className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded-full bg-slate-100 flex items-center justify-center text-[8px] font-bold text-slate-600">
                            {quote.customer.split(' ').map(n => n[0]).join('').slice(0, 2)}
                        </div>
                        <div>
                            <p className="text-[10px] font-semibold text-slate-900">{quote.customer}</p>
                            <span className={`text-[8px] px-1.5 py-0.5 rounded-full ${
                                quote.status === 'sent' ? 'bg-blue-50 text-blue-600' :
                                quote.status === 'approved' ? 'bg-green-50 text-green-600' :
                                'bg-gray-100 text-gray-600'
                            }`}>
                                {quote.status}
                            </span>
                        </div>
                    </div>
                    <span className="text-[10px] font-mono font-medium text-slate-700">{quote.value}</span>
                </div>
            ))}
        </div>
    </div>
);

const SmartQuoteMock = () => (
    <div className="bg-white rounded-xl border border-slate-200 shadow-lg overflow-hidden">
        <div className="px-4 py-3 bg-gradient-to-r from-orange-500 to-red-500 flex items-center justify-between">
            <div className="flex items-center gap-2">
                <Sparkles size={12} className="text-white" />
                <span className="text-xs font-bold text-white">Smart Quote AI</span>
            </div>
            <span className="text-[9px] text-white/80 bg-white/20 px-2 py-0.5 rounded-full">Processing...</span>
        </div>
        <div className="p-4 space-y-3">
            {/* Extracted Items */}
            <div className="space-y-2">
                <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">Extracted Products</p>
                {[
                    { name: '6" PVC Schedule 40 Pipe', qty: '240 ft', match: '98%' },
                    { name: 'Ball Valve 2" Bronze', qty: '12 ea', match: '95%' },
                    { name: 'Pressure Gauge 0-100 PSI', qty: '6 ea', match: '100%' },
                ].map((item, i) => (
                    <div key={i} className="flex items-center justify-between py-1.5 px-2 bg-green-50/50 border border-green-100 rounded-lg">
                        <div className="flex items-center gap-2">
                            <div className="w-5 h-5 rounded bg-green-100 flex items-center justify-center">
                                <FileText size={10} className="text-green-600" />
                            </div>
                            <div>
                                <p className="text-[9px] font-semibold text-slate-800">{item.name}</p>
                                <p className="text-[8px] text-slate-500">Qty: {item.qty}</p>
                            </div>
                        </div>
                        <span className="text-[8px] font-bold text-green-600 bg-green-100 px-1.5 py-0.5 rounded">{item.match}</span>
                    </div>
                ))}
            </div>

            {/* AI Suggestion */}
            <div className="p-2.5 bg-blue-50 border border-blue-100 rounded-lg">
                <div className="flex items-start gap-2">
                    <Zap size={10} className="text-blue-500 mt-0.5" />
                    <div>
                        <p className="text-[9px] font-semibold text-blue-800">AI Recommendation</p>
                        <p className="text-[8px] text-blue-600 mt-0.5">Suggest upgraded brass valves for better margins (+$2,400)</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
);

const CustomerHealthMock = () => (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-100">
            <div className="flex items-center gap-1.5">
                <Users size={12} className="text-blue-600" />
                <span className="text-xs font-bold text-slate-900">Customer Health</span>
            </div>
        </div>
        <div className="p-3 space-y-2">
            <div className="flex items-center justify-between p-2 bg-green-50 rounded-lg border border-green-100">
                <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-[10px] font-medium text-slate-700">VIP Customers</span>
                </div>
                <span className="text-xs font-bold text-green-700">12</span>
            </div>
            <div className="flex items-center justify-between p-2 bg-red-50 rounded-lg border border-red-100">
                <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                    <span className="text-[10px] font-medium text-slate-700">At Risk</span>
                </div>
                <span className="text-xs font-bold text-red-700">3</span>
            </div>
            <div className="pt-2 border-t border-slate-100">
                <div className="flex items-center justify-between">
                    <span className="text-[10px] text-slate-500">Avg Health Score</span>
                    <span className="text-xs font-bold text-green-600">87/100</span>
                </div>
            </div>
        </div>
    </div>
);

export function HeroSection() {
    return (
        <motion.section
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.8 }}
            className="relative section-py section-px pt-32 md:pt-40 overflow-hidden"
        >
            {/* Background gradient mesh */}
            <div className="absolute inset-0 gradient-mesh pointer-events-none" />
            
            {/* Subtle grid pattern */}
            <div className="absolute inset-0 bg-[linear-gradient(rgba(0,0,0,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(0,0,0,0.02)_1px,transparent_1px)] bg-[size:64px_64px] pointer-events-none" />

            <div className="landing-container relative">
                <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
                    {/* Left: Content */}
                    <div className="space-y-8">
                        {/* Badge */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.1, duration: 0.6 }}
                        >
                            <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-orange-100 text-orange-700 text-sm font-semibold border border-orange-200">
                                <Sparkles size={14} className="text-orange-600" />
                                AI-Powered RFQ Processing
                            </span>
                        </motion.div>

                        {/* Headline */}
                        <motion.h1
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.2, duration: 0.6 }}
                            className="hero-headline text-slate-900"
                        >
                            An AI Inside Sales Agent
                            <br />
                            <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-500 to-red-600">
                                for Industrial Distributors
                            </span>
                        </motion.h1>

                        {/* Subheadline */}
                        <motion.p
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.3, duration: 0.6 }}
                            className="text-lg md:text-xl text-slate-600 leading-relaxed max-w-xl"
                        >
                            Mercura reads complex RFQs from emails and PDFs, matches products to your catalog, 
                            and generates quotes in minutes—not hours. Your team can finally focus on selling.
                        </motion.p>

                        {/* Stats row */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.4, duration: 0.6 }}
                            className="flex flex-wrap gap-6"
                        >
                            {[
                                { value: '75%', label: 'Faster Turnaround' },
                                { value: '5hrs+', label: 'Saved Per Rep/Week' },
                                { value: '3x', label: 'More Quotes' },
                            ].map((stat, i) => (
                                <div key={i} className="flex items-center gap-3">
                                    <span className="text-2xl md:text-3xl font-bold text-slate-900">{stat.value}</span>
                                    <span className="text-xs text-slate-500 leading-tight max-w-[60px]">{stat.label}</span>
                                </div>
                            ))}
                        </motion.div>

                        {/* CTAs */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.5, duration: 0.6 }}
                            className="flex flex-col sm:flex-row items-start sm:items-center gap-4"
                        >
                            <Button
                                size="lg"
                                className="bg-slate-900 text-white hover:bg-slate-800 px-8 py-6 text-base font-semibold rounded-xl shadow-lg shadow-slate-900/20 hover:shadow-xl hover:shadow-slate-900/30 transition-all duration-300 hover:-translate-y-0.5"
                                onClick={() => window.location.href = '/signup'}
                            >
                                Get Started Free
                                <ArrowRight className="ml-2 h-5 w-5" />
                            </Button>
                            <Button
                                size="lg"
                                variant="ghost"
                                className="text-slate-600 hover:text-slate-900 px-6 py-6 text-base font-medium"
                                onClick={() => {
                                    const element = document.getElementById('how-it-works');
                                    element?.scrollIntoView({ behavior: 'smooth' });
                                }}
                            >
                                See How It Works
                            </Button>
                        </motion.div>

                        {/* Trust microcopy */}
                        <motion.p
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.7, duration: 0.6 }}
                            className="text-xs text-slate-400 flex items-center gap-2"
                        >
                            <span className="inline-flex items-center gap-1">
                                <span className="w-1.5 h-1.5 bg-green-500 rounded-full"></span>
                                GDPR Compliant
                            </span>
                            <span>•</span>
                            <span>Enterprise Security</span>
                            <span>•</span>
                            <span>Free Trial</span>
                        </motion.p>
                    </div>

                    {/* Right: App Mockups */}
                    <motion.div
                        initial={{ opacity: 0, x: 40 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.4, duration: 0.8 }}
                        className="relative"
                    >
                        <div className="relative z-10 grid grid-cols-12 gap-3">
                            {/* Main dashboard */}
                            <div className="col-span-7">
                                <TodayViewMock />
                            </div>
                            
                            {/* Quote table */}
                            <div className="col-span-5 pt-8">
                                <QuoteTableMock />
                            </div>

                            {/* Smart Quote - overlapping */}
                            <div className="col-span-6 col-start-4 -mt-4">
                                <motion.div
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: 0.8, duration: 0.6 }}
                                >
                                    <SmartQuoteMock />
                                </motion.div>
                            </div>

                            {/* Customer Health */}
                            <div className="col-span-5 col-start-1 -mt-8">
                                <motion.div
                                    initial={{ opacity: 0, y: 20 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    transition={{ delay: 1, duration: 0.6 }}
                                >
                                    <CustomerHealthMock />
                                </motion.div>
                            </div>
                        </div>

                        {/* Decorative blur */}
                        <div className="absolute -top-20 -right-20 w-64 h-64 bg-orange-200/30 rounded-full blur-[80px] pointer-events-none" />
                        <div className="absolute -bottom-20 -left-20 w-64 h-64 bg-blue-200/30 rounded-full blur-[80px] pointer-events-none" />
                    </motion.div>
                </div>
            </div>
        </motion.section>
    );
}
