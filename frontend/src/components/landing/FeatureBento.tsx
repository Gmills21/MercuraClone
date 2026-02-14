/**
 * Feature Bento Grid Component - Production Ready
 * 
 * Feature Grid with animated/demo content
 * Smart Quote AI | Email Automation | ERP Integrations
 */

import { FileText, Mail, Blocks, Sparkles, Check, ArrowRight, Zap, Database, Cpu } from 'lucide-react';
import { motion } from 'framer-motion';

// Feature 1: Smart Quote AI Demo
const SpecAIDemo = () => (
    <div className="relative h-48 bg-slate-900 rounded-xl overflow-hidden">
        {/* PDF Preview */}
        <div className="absolute inset-0 p-4">
            <div className="h-full bg-white rounded-lg shadow-2xl p-4 transform rotate-[-2deg] scale-95">
                <div className="flex items-center gap-2 mb-3 pb-2 border-b border-slate-100">
                    <FileText size={12} className="text-red-500" />
                    <span className="text-[10px] font-semibold text-slate-700">RFQ_Industrial_Project.pdf</span>
                </div>
                <div className="space-y-1.5">
                    <div className="h-2 bg-slate-100 rounded w-full"></div>
                    <div className="h-2 bg-slate-100 rounded w-4/5"></div>
                    <div className="h-2 bg-slate-100 rounded w-3/5"></div>
                </div>
                <div className="mt-4 p-2 bg-slate-50 rounded border border-slate-100">
                    <p className="text-[8px] text-slate-500 font-mono">Line 247: 6" Sch 40 PVC Pipe x 240ft</p>
                </div>
            </div>
        </div>
        
        {/* AI Extraction Overlay */}
        <motion.div 
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.3, duration: 0.5 }}
            className="absolute bottom-4 right-4 bg-gradient-to-r from-orange-500 to-red-500 rounded-xl p-3 shadow-xl"
        >
            <div className="flex items-center gap-2 mb-2">
                <Sparkles size={12} className="text-white" />
                <span className="text-[10px] font-bold text-white">AI Extracted</span>
            </div>
            <div className="space-y-1.5">
                <div className="flex items-center gap-2 text-[9px] text-white/90">
                    <Check size={8} className="text-green-300" />
                    <span>6" PVC Pipe (240ft)</span>
                </div>
                <div className="flex items-center gap-2 text-[9px] text-white/90">
                    <Check size={8} className="text-green-300" />
                    <span>Ball Valves (12x)</span>
                </div>
                <div className="flex items-center gap-2 text-[9px] text-white/90">
                    <Check size={8} className="text-green-300" />
                    <span>Pressure Gauges (6x)</span>
                </div>
            </div>
        </motion.div>

        {/* Scanning animation */}
        <motion.div
            animate={{ top: ['0%', '100%', '0%'] }}
            transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
            className="absolute left-0 right-0 h-0.5 bg-gradient-to-r from-transparent via-orange-400 to-transparent opacity-50"
        />
    </div>
);

// Feature 2: Email Automation Demo
const EmailAutomationDemo = () => (
    <div className="relative h-48 bg-slate-50 rounded-xl overflow-hidden p-4">
        {/* Email List */}
        <div className="space-y-2">
            {[
                { from: 'john@acme.com', subject: 'Quote Request - Project Delta', time: '2m ago', unread: true },
                { from: 'sarah@metrosupply.com', subject: 'RFQ: HVAC Components', time: '15m ago', unread: true },
                { from: 'orders@industrial.com', subject: 'Re: Valve pricing', time: '1h ago', unread: false },
            ].map((email, i) => (
                <motion.div
                    key={i}
                    initial={{ x: -20, opacity: 0 }}
                    whileInView={{ x: 0, opacity: 1 }}
                    viewport={{ once: true }}
                    transition={{ delay: i * 0.1 }}
                    className={`p-2.5 rounded-lg border ${email.unread ? 'bg-white border-emerald-200 shadow-sm' : 'bg-slate-100/50 border-transparent'}`}
                >
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            {email.unread && (
                                <motion.div
                                    animate={{ scale: [1, 1.2, 1] }}
                                    transition={{ duration: 2, repeat: Infinity }}
                                    className="w-2 h-2 bg-emerald-500 rounded-full"
                                />
                            )}
                            <span className="text-[10px] font-semibold text-slate-700">{email.from}</span>
                        </div>
                        <span className="text-[8px] text-slate-400">{email.time}</span>
                    </div>
                    <p className="text-[9px] text-slate-600 mt-1 truncate">{email.subject}</p>
                </motion.div>
            ))}
        </div>

        {/* AI Processing Badge */}
        <motion.div
            initial={{ scale: 0 }}
            whileInView={{ scale: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.4, type: "spring" }}
            className="absolute bottom-4 right-4 bg-emerald-500 text-white px-3 py-2 rounded-lg shadow-lg flex items-center gap-2"
        >
            <Zap size={12} className="fill-white" />
            <span className="text-[10px] font-bold">Auto-processed 2 RFQs</span>
        </motion.div>
    </div>
);

// Feature 3: Integrations Demo
const IntegrationsDemo = () => (
    <div className="relative h-48 bg-gradient-to-br from-purple-900 to-indigo-900 rounded-xl overflow-hidden p-4">
        {/* Central Hub */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
            <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                className="w-32 h-32 border-2 border-dashed border-white/20 rounded-full"
            />
            <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-12 h-12 bg-white rounded-xl shadow-xl flex items-center justify-center">
                    <span className="text-lg font-bold text-purple-600">M</span>
                </div>
            </div>
        </div>

        {/* QuickBooks Integration - Only one currently implemented */}
        <motion.div
            initial={{ opacity: 0, scale: 0 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.1, type: "spring" }}
            className="absolute top-1/2 left-1/2"
            style={{ transform: `translate(calc(-50% + 60px), calc(-50% - 20px))` }}
        >
            <div className="w-12 h-12 bg-green-500 rounded-xl shadow-lg flex items-center justify-center text-white text-xs font-bold">
                QB
            </div>
            <span className="absolute -bottom-5 left-1/2 -translate-x-1/2 text-[9px] text-white/80 whitespace-nowrap">QuickBooks</span>
        </motion.div>

        {/* Coming Soon placeholders */}
        {[
            { name: 'SAP', angle: 45 },
            { name: 'P21', angle: 135 },
            { name: 'More', angle: 225 },
        ].map((item, i) => {
            const angle = item.angle * (Math.PI / 180);
            const x = Math.cos(angle) * 55;
            const y = Math.sin(angle) * 45;
            
            return (
                <motion.div
                    key={i}
                    initial={{ opacity: 0, scale: 0 }}
                    whileInView={{ opacity: 1, scale: 1 }}
                    viewport={{ once: true }}
                    transition={{ delay: 0.2 + i * 0.1, type: "spring" }}
                    className="absolute top-1/2 left-1/2"
                    style={{ transform: `translate(calc(-50% + ${x}px), calc(-50% + ${y}px))` }}
                >
                    <div className="w-10 h-10 bg-white/10 border border-white/20 rounded-lg flex items-center justify-center text-white/40 text-[8px] font-medium">
                        {item.name}
                    </div>
                </motion.div>
            );
        })}

        {/* Connection Lines */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none">
            <motion.line
                initial={{ pathLength: 0 }}
                whileInView={{ pathLength: 1 }}
                viewport={{ once: true }}
                transition={{ delay: 0.3, duration: 0.5 }}
                x1="50%"
                y1="50%"
                x2="65%"
                y2="38%"
                stroke="rgba(255,255,255,0.3)"
                strokeWidth="2"
            />
        </svg>

        {/* Data Flow Animation */}
        <div className="absolute bottom-4 left-4 right-4 flex items-center gap-2">
            <Database size={12} className="text-white/60" />
            <div className="flex-1 h-1 bg-white/10 rounded-full overflow-hidden">
                <motion.div
                    animate={{ x: ['-100%', '100%'] }}
                    transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                    className="h-full w-1/3 bg-gradient-to-r from-transparent via-white/50 to-transparent"
                />
            </div>
            <Cpu size={12} className="text-white/60" />
        </div>
    </div>
);

export function FeatureBento() {
    const features = [
        {
            icon: FileText,
            title: "Smart Quote AI",
            subtitle: "Extract & Match Instantly",
            description: "Upload any RFQ—PDF, Excel, or email. Our AI extracts line items, matches them to your catalog, and suggests alternatives with better margins.",
            iconBg: "bg-blue-500",
            iconColor: "text-white",
            demo: SpecAIDemo,
            stat: "98%",
            statLabel: "Extraction Accuracy"
        },
        {
            icon: Mail,
            title: "Email Automation",
            subtitle: "Zero-Touch RFQ Processing",
            description: "Emails arrive, quotes go out. Mercura monitors your inbox, extracts RFQs automatically, and routes them for approval.",
            iconBg: "bg-emerald-500",
            iconColor: "text-white",
            demo: EmailAutomationDemo,
            stat: "0",
            statLabel: "Manual Data Entry"
        },
        {
            icon: Blocks,
            title: "ERP Integrations",
            subtitle: "Works With Your Stack",
            description: "Native QuickBooks integration with more ERPs coming soon. Sync products, customers, and quotes bi-directionally.",
            iconBg: "bg-gradient-to-r from-purple-600 to-indigo-600",
            iconColor: "text-white",
            demo: IntegrationsDemo,
            stat: "1",
            statLabel: "Integration (more coming)"
        }
    ];

    return (
        <section id="features" className="section-py section-px bg-slate-50/50 relative overflow-hidden">
            {/* Background decoration */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(249,115,22,0.03)_0%,transparent_50%)]" />
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_80%,rgba(99,102,241,0.03)_0%,transparent_50%)]" />

            <div className="landing-container relative">
                {/* Section Header */}
                <div className="text-center mb-16 max-w-3xl mx-auto">
                    <motion.span
                        initial={{ opacity: 0, y: 10 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="inline-flex items-center gap-2 text-sm font-semibold text-orange-600 mb-4"
                    >
                        <Sparkles size={16} />
                        Powerful Features
                    </motion.span>
                    <motion.h2
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        transition={{ delay: 0.1 }}
                        className="section-headline mb-4"
                    >
                        Everything You Need to
                        <br />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-500 to-red-600">
                            Quote at Lightning Speed
                        </span>
                    </motion.h2>
                    <motion.p
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        transition={{ delay: 0.2 }}
                        className="text-lg text-slate-600"
                    >
                        Built specifically for industrial distributors. No more copy-paste between systems.
                    </motion.p>
                </div>

                {/* Bento Grid */}
                <div className="grid md:grid-cols-2 gap-6">
                    {features.map((feature, i) => (
                        <motion.div
                            key={i}
                            initial={{ opacity: 0, y: 30 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true, margin: "-50px" }}
                            transition={{ delay: i * 0.1, duration: 0.5 }}
                            className="group bg-white rounded-2xl border border-slate-200 overflow-hidden hover:shadow-xl hover:shadow-slate-900/5 hover:border-slate-300 transition-all duration-500"
                        >
                            {/* Demo Area */}
                            <div className="relative">
                                <feature.demo />
                                
                                {/* Hover overlay */}
                                <div className="absolute inset-0 bg-gradient-to-t from-white via-transparent to-transparent opacity-60" />
                            </div>

                            {/* Content */}
                            <div className="p-6 pt-4">
                                <div className="flex items-start justify-between mb-4">
                                    <div className="flex items-center gap-3">
                                        <div className={`p-2.5 rounded-xl ${feature.iconBg} shadow-lg shadow-slate-900/10 group-hover:scale-110 transition-transform duration-300`}>
                                            <feature.icon className={`h-5 w-5 ${feature.iconColor}`} />
                                        </div>
                                        <div>
                                            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{feature.subtitle}</p>
                                            <h3 className="text-lg font-bold text-slate-900">{feature.title}</h3>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <p className="text-2xl font-bold text-slate-900">{feature.stat}</p>
                                        <p className="text-[10px] text-slate-500 uppercase tracking-wider">{feature.statLabel}</p>
                                    </div>
                                </div>
                                
                                <p className="text-sm text-slate-600 leading-relaxed">
                                    {feature.description}
                                </p>

                                <button className="mt-4 flex items-center gap-1 text-sm font-semibold text-orange-600 hover:text-orange-700 transition-colors group/btn">
                                    Learn more
                                    <ArrowRight size={14} className="group-hover/btn:translate-x-1 transition-transform" />
                                </button>
                            </div>
                        </motion.div>
                    ))}
                </div>
            </div>
        </section>
    );
}
