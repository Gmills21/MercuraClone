/**
 * How It Works Component - Production Ready
 * 
 * 3-step process visualization with actual UI mockups
 */

import { Upload, Brain, Send, ArrowRight, FileText, CheckCircle, Sparkles, Zap, Mail, Package, TrendingUp, Clock } from 'lucide-react';
import { motion } from 'framer-motion';

// Step 1: Upload RFQ
const Step1Visual = () => (
    <div className="relative h-64 bg-white rounded-xl border border-slate-200 shadow-lg p-4 overflow-hidden">
        {/* Upload Zone */}
        <div className="h-full border-2 border-dashed border-slate-200 rounded-lg flex flex-col items-center justify-center relative">
            <motion.div
                animate={{ y: [0, -5, 0] }}
                transition={{ duration: 2, repeat: Infinity }}
                className="w-16 h-16 bg-orange-50 rounded-2xl flex items-center justify-center mb-3"
            >
                <Upload size={28} className="text-orange-500" />
            </motion.div>
            <p className="text-sm font-semibold text-slate-700">Drop RFQ files here</p>
            <p className="text-xs text-slate-400 mt-1">PDF, Excel, CSV, or Email</p>

            {/* Floating files */}
            <motion.div
                animate={{ y: [0, -10, 0], rotate: [0, 5, 0] }}
                transition={{ duration: 3, repeat: Infinity, delay: 0.5 }}
                className="absolute top-4 left-4 bg-white p-2 rounded-lg shadow-lg border border-slate-100"
            >
                <FileText size={16} className="text-red-500" />
                <span className="text-[8px] text-slate-500 block mt-0.5">RFQ.pdf</span>
            </motion.div>

            <motion.div
                animate={{ y: [0, -8, 0], rotate: [0, -5, 0] }}
                transition={{ duration: 3.5, repeat: Infinity, delay: 1 }}
                className="absolute top-8 right-6 bg-white p-2 rounded-lg shadow-lg border border-slate-100"
            >
                <Mail size={16} className="text-blue-500" />
                <span className="text-[8px] text-slate-500 block mt-0.5">Email</span>
            </motion.div>

            <motion.div
                animate={{ y: [0, -12, 0] }}
                transition={{ duration: 4, repeat: Infinity, delay: 0 }}
                className="absolute bottom-8 right-4 bg-green-50 p-2 rounded-lg shadow-lg border border-green-100"
            >
                <CheckCircle size={16} className="text-green-500" />
                <span className="text-[8px] text-green-600 block mt-0.5">Scanned</span>
            </motion.div>
        </div>
    </div>
);

// Step 2: AI Processing
const Step2Visual = () => (
    <div className="relative h-64 bg-slate-900 rounded-xl border border-slate-800 shadow-lg p-4 overflow-hidden">
        {/* Neural Network Background */}
        <div className="absolute inset-0 opacity-20">
            {[...Array(6)].map((_, i) => (
                <div key={i} className="absolute w-px h-full bg-gradient-to-b from-transparent via-orange-500/50 to-transparent"
                    style={{ left: `${15 + i * 15}%` }}
                />
            ))}
            {[...Array(4)].map((_, i) => (
                <div key={i} className="absolute h-px w-full bg-gradient-to-r from-transparent via-orange-500/50 to-transparent"
                    style={{ top: `${20 + i * 20}%` }}
                />
            ))}
        </div>

        {/* Processing Animation */}
        <div className="relative z-10 h-full flex flex-col">
            <div className="flex items-center gap-2 mb-4">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-r from-orange-500 to-red-500 flex items-center justify-center">
                    <Brain size={16} className="text-white" />
                </div>
                <div>
                    <p className="text-xs font-bold text-white">AI Processing</p>
                    <p className="text-[10px] text-slate-400">Extracting specifications...</p>
                </div>
            </div>

            {/* Progress Bars */}
            <div className="space-y-3 flex-1">
                {[
                    { label: 'Parsing PDF structure', progress: 100 },
                    { label: 'Extracting line items', progress: 85 },
                    { label: 'Matching to catalog', progress: 60 },
                    { label: 'Calculating pricing', progress: 30 },
                ].map((item, i) => (
                    <div key={i} className="space-y-1">
                        <div className="flex justify-between text-[10px]">
                            <span className="text-slate-300">{item.label}</span>
                            <span className="text-orange-400">{item.progress}%</span>
                        </div>
                        <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                            <motion.div
                                initial={{ width: 0 }}
                                whileInView={{ width: `${item.progress}%` }}
                                viewport={{ once: true }}
                                transition={{ delay: 0.2 + i * 0.1, duration: 0.8 }}
                                className="h-full bg-gradient-to-r from-orange-500 to-red-500 rounded-full"
                            />
                        </div>
                    </div>
                ))}
            </div>

            {/* Product Matches Preview */}
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.6 }}
                className="mt-3 p-2 bg-slate-800/50 rounded-lg border border-slate-700"
            >
                <div className="flex items-center gap-2">
                    <Sparkles size={12} className="text-orange-400" />
                    <span className="text-[10px] text-slate-300">Found <span className="text-white font-semibold">12 products</span> with <span className="text-green-400 font-semibold">94% confidence</span></span>
                </div>
            </motion.div>
        </div>
    </div>
);

// Step 3: Quote Generated
const Step3Visual = () => (
    <div className="relative h-64 bg-white rounded-xl border border-slate-200 shadow-lg overflow-hidden">
        {/* Quote Header */}
        <div className="bg-gradient-to-r from-green-500 to-emerald-600 px-4 py-3 flex items-center justify-between">
            <div className="flex items-center gap-2">
                <CheckCircle size={16} className="text-white" />
                <span className="text-sm font-bold text-white">Quote Ready</span>
            </div>
            <span className="text-[10px] text-white/80 bg-white/20 px-2 py-0.5 rounded-full">Q-2024-0892</span>
        </div>

        {/* Quote Content */}
        <div className="p-4 space-y-3">
            <div className="flex justify-between items-center pb-2 border-b border-slate-100">
                <div>
                    <p className="text-[10px] text-slate-500 uppercase">Customer</p>
                    <p className="text-xs font-semibold text-slate-900">Acme Industrial Supply</p>
                </div>
                <div className="text-right">
                    <p className="text-[10px] text-slate-500 uppercase">Total</p>
                    <p className="text-sm font-bold text-slate-900">$47,250.00</p>
                </div>
            </div>

            {/* Line Items */}
            <div className="space-y-2">
                {[
                    { item: '6" Sch 40 PVC Pipe', qty: '240 ft', price: '$2,400.00' },
                    { item: 'Bronze Ball Valve 4"', qty: '8 ea', price: '$3,200.00' },
                    { item: 'Pressure Gauge 100psi', qty: '12 ea', price: '$1,440.00' },
                ].map((line, i) => (
                    <div key={i} className="flex justify-between text-[10px]">
                        <div className="flex gap-2">
                            <Package size={12} className="text-slate-400" />
                            <span className="text-slate-700">{line.item}</span>
                            <span className="text-slate-400">× {line.qty}</span>
                        </div>
                        <span className="font-medium text-slate-900">{line.price}</span>
                    </div>
                ))}
            </div>

            {/* Actions */}
            <div className="pt-3 flex gap-2">
                <button className="flex-1 bg-slate-900 text-white text-[10px] font-semibold py-2 rounded-lg flex items-center justify-center gap-1">
                    <Send size={10} />
                    Send Quote
                </button>
                <button className="px-3 py-2 border border-slate-200 rounded-lg text-[10px] font-medium text-slate-600">
                    Edit
                </button>
            </div>
        </div>

        {/* Time saved badge */}
        <motion.div
            initial={{ scale: 0, rotate: -10 }}
            whileInView={{ scale: 1, rotate: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.8, type: "spring" }}
            className="absolute -top-2 -right-2 bg-orange-500 text-white px-3 py-1.5 rounded-lg shadow-lg transform rotate-6"
        >
            <div className="flex items-center gap-1">
                <Clock size={12} />
                <span className="text-[10px] font-bold">Saved 45 min</span>
            </div>
        </motion.div>
    </div>
);

export function HowItWorks() {
    const steps = [
        {
            number: "01",
            icon: Upload,
            title: "Upload Any RFQ",
            description: "Drag and drop PDFs, Excel files, or forward emails. Mercura accepts any format—scanned documents, CAD drawings, even handwritten notes.",
            visual: Step1Visual,
            color: "orange",
            features: ["Multi-format support", "Email auto-monitoring", "Mobile camera capture"]
        },
        {
            number: "02",
            icon: Brain,
            title: "AI Extracts & Matches",
            description: "Our AI reads technical specifications, matches products to your catalog, and suggests alternatives. It learns your pricing rules and margin targets.",
            visual: Step2Visual,
            color: "slate",
            features: ["94% match accuracy", "Auto-margin optimization", "Competitor cross-reference"]
        },
        {
            number: "03",
            icon: Send,
            title: "Quote Goes Out",
            description: "Review, approve, and send professional quotes in minutes. Push directly to your ERP or email customers—whatever fits your workflow.",
            visual: Step3Visual,
            color: "emerald",
            features: ["One-click approval", "ERP sync", "Branded PDFs"]
        }
    ];

    return (
        <section id="how-it-works" className="section-py section-px bg-white relative overflow-hidden">
            {/* Background elements */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_50%,rgba(249,115,22,0.03)_0%,transparent_50%)]" />

            <div className="landing-container relative">
                {/* Section Header */}
                <div className="text-center mb-16 max-w-3xl mx-auto">
                    <motion.span
                        initial={{ opacity: 0, y: 10 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="inline-flex items-center gap-2 text-sm font-semibold text-orange-600 mb-4"
                    >
                        <Zap size={16} />
                        Simple Process
                    </motion.span>
                    <motion.h2
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        transition={{ delay: 0.1 }}
                        className="section-headline mb-4"
                    >
                        From Chaos to Quote
                        <br />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-500 to-red-600">
                            in Three Steps
                        </span>
                    </motion.h2>
                    <motion.p
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        transition={{ delay: 0.2 }}
                        className="text-lg text-slate-600"
                    >
                        No training required. Upload your first RFQ and see results in under 2 minutes.
                    </motion.p>
                </div>

                {/* Steps */}
                <div className="space-y-24">
                    {steps.map((step, index) => (
                        <motion.div
                            key={index}
                            initial={{ opacity: 0, y: 40 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true, margin: "-100px" }}
                            transition={{ duration: 0.6 }}
                            className={`grid lg:grid-cols-2 gap-12 items-center ${index % 2 === 1 ? 'lg:flex-row-reverse' : ''}`}
                        >
                            {/* Content */}
                            <div className={`space-y-6 ${index % 2 === 1 ? 'lg:order-2' : ''}`}>
                                <div className="flex items-center gap-4">
                                    <span className="text-6xl font-bold text-slate-100">{step.number}</span>
                                    <div className={`p-3 rounded-xl ${
                                        step.color === 'orange' ? 'bg-orange-100 text-orange-600' :
                                        step.color === 'slate' ? 'bg-slate-100 text-slate-700' :
                                        'bg-emerald-100 text-emerald-600'
                                    }`}>
                                        <step.icon size={24} />
                                    </div>
                                </div>

                                <div>
                                    <h3 className="text-2xl md:text-3xl font-bold text-slate-900 mb-3">
                                        {step.title}
                                    </h3>
                                    <p className="text-lg text-slate-600 leading-relaxed">
                                        {step.description}
                                    </p>
                                </div>

                                <div className="flex flex-wrap gap-3">
                                    {step.features.map((feature, i) => (
                                        <span key={i} className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-lg text-sm text-slate-600">
                                            <CheckCircle size={14} className="text-green-500" />
                                            {feature}
                                        </span>
                                    ))}
                                </div>
                            </div>

                            {/* Visual */}
                            <div className={index % 2 === 1 ? 'lg:order-1' : ''}>
                                <step.visual />
                            </div>
                        </motion.div>
                    ))}
                </div>

                {/* Bottom CTA */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="mt-24 text-center"
                >
                    <div className="inline-flex items-center gap-4 p-6 bg-slate-50 rounded-2xl border border-slate-200">
                        <div className="flex items-center gap-3">
                            <TrendingUp size={24} className="text-green-500" />
                            <div className="text-left">
                                <p className="text-sm font-semibold text-slate-900">Average time to first quote</p>
                                <p className="text-xs text-slate-500">Based on 500+ implementations</p>
                            </div>
                        </div>
                        <div className="text-3xl font-bold text-slate-900">4.2 min</div>
                    </div>
                </motion.div>
            </div>
        </section>
    );
}
