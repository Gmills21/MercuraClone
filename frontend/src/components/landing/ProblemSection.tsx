/**
 * Problem Section Component - Production Ready
 * 
 * "Sales Reps Should Sell, Not Search"
 * Illustrates the pain points Mercura solves with compelling visuals
 */

import { FileText, Mail, Table, FileSpreadsheet, Clock, AlertCircle, TrendingDown, Search, X } from 'lucide-react';
import { motion } from 'framer-motion';

const painPoints = [
    {
        icon: Clock,
        stat: "18 mins",
        label: "Average time per manual quote",
        description: "Reps spend nearly 20 minutes on each quote—searching catalogs, checking prices, copying data."
    },
    {
        icon: AlertCircle,
        stat: "32%",
        label: "Quotes contain errors",
        description: "Manual data entry leads to pricing mistakes, wrong products, and costly corrections."
    },
    {
        icon: TrendingDown,
        stat: "40%",
        label: "Win rate on slow quotes",
        description: "When quotes take days instead of hours, customers go to competitors."
    }
];

export function ProblemSection() {
    return (
        <section id="product" className="section-py section-px bg-white relative overflow-hidden">
            {/* Background gradient */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_0%_100%,rgba(249,115,22,0.03)_0%,transparent_50%)]" />

            <div className="landing-container relative">
                <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
                    {/* Visual Side - The Chaos */}
                    <motion.div
                        initial={{ opacity: 0, x: -30 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.6 }}
                        className="order-2 lg:order-1"
                    >
                        <div className="relative">
                            {/* Main Visual */}
                            <div className="bg-slate-50 rounded-2xl border border-slate-200 p-6 shadow-lg">
                                <div className="flex items-center gap-2 mb-6 text-slate-400">
                                    <Search size={16} />
                                    <span className="text-xs font-medium">Searching through...</span>
                                </div>

                                {/* Scattered Documents */}
                                <div className="relative h-64">
                                    {[
                                        { icon: FileText, label: 'RFQ_Pipe_Specs.pdf', color: 'text-red-500', rotate: -5, top: '5%', left: '10%' },
                                        { icon: FileSpreadsheet, label: 'Pricing_2024.xlsx', color: 'text-green-500', rotate: 8, top: '20%', left: '55%' },
                                        { icon: Mail, label: 'customer@email.com', color: 'text-blue-500', rotate: -3, top: '45%', left: '5%' },
                                        { icon: Table, label: 'GAEB_Export.xml', color: 'text-purple-500', rotate: 12, top: '55%', left: '45%' },
                                        { icon: FileText, label: 'Drawing_CAD.dwg', color: 'text-orange-500', rotate: -8, top: '75%', left: '20%' },
                                    ].map((doc, i) => (
                                        <motion.div
                                            key={i}
                                            initial={{ opacity: 0, y: 20 }}
                                            whileInView={{ opacity: 1, y: 0 }}
                                            viewport={{ once: true }}
                                            transition={{ delay: i * 0.1 }}
                                            className="absolute bg-white p-3 rounded-lg shadow-md border border-slate-100"
                                            style={{ 
                                                transform: `rotate(${doc.rotate}deg)`,
                                                top: doc.top,
                                                left: doc.left
                                            }}
                                        >
                                            <div className="flex items-center gap-2">
                                                <doc.icon size={20} className={doc.color} />
                                                <span className="text-xs font-medium text-slate-600">{doc.label}</span>
                                            </div>
                                        </motion.div>
                                    ))}

                                    {/* Error indicators */}
                                    <motion.div
                                        initial={{ scale: 0 }}
                                        whileInView={{ scale: 1 }}
                                        viewport={{ once: true }}
                                        transition={{ delay: 0.6, type: "spring" }}
                                        className="absolute top-1/4 right-0 bg-red-100 text-red-600 px-2 py-1 rounded-full text-[10px] font-bold flex items-center gap-1"
                                    >
                                        <X size={10} />
                                        Wrong price
                                    </motion.div>
                                    <motion.div
                                        initial={{ scale: 0 }}
                                        whileInView={{ scale: 1 }}
                                        viewport={{ once: true }}
                                        transition={{ delay: 0.7, type: "spring" }}
                                        className="absolute bottom-1/4 right-4 bg-amber-100 text-amber-600 px-2 py-1 rounded-full text-[10px] font-bold flex items-center gap-1"
                                    >
                                        <Clock size={10} />
                                        2 days old
                                    </motion.div>
                                </div>
                            </div>

                            {/* Stats overlay */}
                            <motion.div
                                initial={{ opacity: 0, x: 20 }}
                                whileInView={{ opacity: 1, x: 0 }}
                                viewport={{ once: true }}
                                transition={{ delay: 0.4 }}
                                className="absolute -bottom-6 -right-6 bg-white rounded-xl p-4 shadow-xl border border-slate-100"
                            >
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 bg-red-50 rounded-lg flex items-center justify-center">
                                        <TrendingDown size={20} className="text-red-500" />
                                    </div>
                                    <div>
                                        <p className="text-lg font-bold text-slate-900">68%</p>
                                        <p className="text-xs text-slate-500">Of time spent on admin</p>
                                    </div>
                                </div>
                            </motion.div>
                        </div>
                    </motion.div>

                    {/* Content Side */}
                    <motion.div
                        initial={{ opacity: 0, x: 30 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.6, delay: 0.2 }}
                        className="order-1 lg:order-2 space-y-8"
                    >
                        <div>
                            <motion.span
                                initial={{ opacity: 0, y: 10 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                className="inline-flex items-center gap-2 text-sm font-semibold text-red-600 mb-4"
                            >
                                <AlertCircle size={16} />
                                The Problem
                            </motion.span>
                            <h2 className="section-headline mb-4">
                                Sales Reps Should Sell,
                                <br />
                                <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-500 to-red-600">
                                    Not Search
                                </span>
                            </h2>
                            <p className="text-lg text-slate-600 leading-relaxed">
                                Your best salespeople are buried in manual paperwork. Instead of closing deals, 
                                they're hunting through hundreds of pages of specifications, cross-referencing 
                                pricing sheets, and copying data between systems.
                            </p>
                        </div>

                        {/* Pain Points */}
                        <div className="space-y-4">
                            {painPoints.map((point, i) => (
                                <motion.div
                                    key={i}
                                    initial={{ opacity: 0, x: 20 }}
                                    whileInView={{ opacity: 1, x: 0 }}
                                    viewport={{ once: true }}
                                    transition={{ delay: 0.3 + i * 0.1 }}
                                    className="flex items-start gap-4 p-4 bg-slate-50 rounded-xl border border-slate-100"
                                >
                                    <div className="w-12 h-12 bg-white rounded-lg flex items-center justify-center shadow-sm flex-shrink-0">
                                        <point.icon size={20} className="text-slate-400" />
                                    </div>
                                    <div>
                                        <div className="flex items-baseline gap-2">
                                            <span className="text-2xl font-bold text-slate-900">{point.stat}</span>
                                            <span className="text-sm font-medium text-slate-600">{point.label}</span>
                                        </div>
                                        <p className="text-sm text-slate-500 mt-1">{point.description}</p>
                                    </div>
                                </motion.div>
                            ))}
                        </div>

                        {/* Key message */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ delay: 0.6 }}
                            className="p-4 bg-gradient-to-r from-orange-50 to-amber-50 rounded-xl border border-orange-100"
                        >
                            <p className="text-sm font-medium text-orange-800">
                                Every hour spent on admin is an hour not spent selling. 
                                For a team of 5 reps, that's 400+ hours lost every month.
                            </p>
                        </motion.div>
                    </motion.div>
                </div>
            </div>
        </section>
    );
}
