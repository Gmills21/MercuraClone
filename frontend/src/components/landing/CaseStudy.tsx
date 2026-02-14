/**
 * Case Study Component - Production Ready
 * 
 * Featured customer story with compelling results
 */

import { Quote, ArrowRight, TrendingUp, Clock, CheckCircle, Building2, Award } from 'lucide-react';
import { Button } from '../ui/button';
import { motion } from 'framer-motion';

const results = [
    {
        icon: TrendingUp,
        value: "+45%",
        label: "Quote Volume",
        description: "More quotes sent per rep",
        color: "emerald"
    },
    {
        icon: Clock,
        value: "75%",
        label: "Time Reduction",
        description: "From hours to minutes",
        color: "blue"
    },
    {
        icon: CheckCircle,
        value: "Zero",
        label: "Pricing Errors",
        description: "Since implementation",
        color: "purple"
    }
];

export function CaseStudy() {
    return (
        <section id="customers" className="section-py section-px bg-slate-900 text-white relative overflow-hidden">
            {/* Background decorations */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_80%,rgba(249,115,22,0.15)_0%,transparent_50%)]" />
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_20%,rgba(59,130,246,0.1)_0%,transparent_50%)]" />

            <div className="landing-container relative">
                <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
                    {/* Left Content */}
                    <motion.div
                        initial={{ opacity: 0, x: -30 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.6 }}
                        className="space-y-8"
                    >
                        {/* Company Badge */}
                        <div className="flex items-center gap-3">
                            <div className="w-12 h-12 rounded-xl bg-white/10 backdrop-blur flex items-center justify-center">
                                <Building2 size={24} className="text-orange-400" />
                            </div>
                            <div>
                                <p className="text-sm font-semibold text-white">Featured Case Study</p>
                                <p className="text-xs text-white/60">Sanitär-Heinze • Plumbing & HVAC</p>
                            </div>
                        </div>

                        {/* Quote */}
                        <div className="relative">
                            <Quote className="h-12 w-12 text-orange-500/20 mb-4" />
                            <h3 className="text-2xl md:text-3xl font-bold leading-relaxed">
                                "Mercura allows us to significantly increase productivity in the quotation department. 
                                Finding qualified staff is hard—AI ensures technical knowledge is never lost."
                            </h3>
                        </div>

                        {/* Context */}
                        <p className="text-lg text-white/70 leading-relaxed">
                            Sanitär-Heinze processes over 3,000 quotes annually across a catalog of 50,000+ products. 
                            Before Mercura, their 8-person quoting team struggled with seasonal spikes and knowledge 
                            transfer as senior staff retired.
                        </p>

                        {/* Author */}
                        <div className="flex items-center gap-4 pt-6 border-t border-white/10">
                            <div className="w-14 h-14 rounded-full bg-gradient-to-br from-orange-400 to-red-500 flex items-center justify-center text-white font-bold text-lg">
                                MS
                            </div>
                            <div>
                                <p className="font-bold text-white">Maria Schmidt</p>
                                <p className="text-sm text-white/60">Head of Sales</p>
                                <div className="flex items-center gap-2 mt-1">
                                    <Award size={14} className="text-orange-400" />
                                    <span className="text-xs text-orange-400 font-medium">15+ years in distribution</span>
                                </div>
                            </div>
                        </div>

                        {/* CTA */}
                        <Button
                            variant="outline"
                            size="lg"
                            className="text-white border-white/20 hover:bg-white/10 bg-transparent mt-4"
                        >
                            Read Full Case Study
                            <ArrowRight className="ml-2 h-4 w-4" />
                        </Button>
                    </motion.div>

                    {/* Right Stats Card */}
                    <motion.div
                        initial={{ opacity: 0, x: 30 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.6, delay: 0.2 }}
                    >
                        <div className="bg-slate-800/50 backdrop-blur rounded-2xl p-8 border border-white/10 shadow-2xl">
                            <h4 className="text-sm font-semibold text-white/60 uppercase tracking-wider mb-8">
                                Results After 6 Months
                            </h4>

                            <div className="space-y-6">
                                {results.map((result, i) => (
                                    <motion.div
                                        key={i}
                                        initial={{ opacity: 0, x: 20 }}
                                        whileInView={{ opacity: 1, x: 0 }}
                                        viewport={{ once: true }}
                                        transition={{ delay: 0.3 + i * 0.1 }}
                                        className={`p-5 rounded-xl bg-${result.color}-500/10 border border-${result.color}-500/20`}
                                    >
                                        <div className="flex items-start gap-4">
                                            <div className={`w-12 h-12 rounded-xl bg-${result.color}-500/20 flex items-center justify-center flex-shrink-0`}>
                                                <result.icon className={`h-6 w-6 text-${result.color}-400`} />
                                            </div>
                                            <div className="flex-1">
                                                <div className="flex items-baseline gap-2 mb-1">
                                                    <span className="text-3xl font-bold text-white">{result.value}</span>
                                                    <span className="text-sm font-medium text-white/80">{result.label}</span>
                                                </div>
                                                <p className="text-sm text-white/60">{result.description}</p>
                                            </div>
                                        </div>
                                    </motion.div>
                                ))}
                            </div>

                            {/* Additional context */}
                            <div className="mt-8 pt-6 border-t border-white/10">
                                <div className="grid grid-cols-2 gap-4 text-center">
                                    <div>
                                        <p className="text-2xl font-bold text-white">3,200+</p>
                                        <p className="text-xs text-white/60">Quotes processed</p>
                                    </div>
                                    <div>
                                        <p className="text-2xl font-bold text-white">$12M</p>
                                        <p className="text-xs text-white/60">Annual quote value</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                </div>
            </div>
        </section>
    );
}
