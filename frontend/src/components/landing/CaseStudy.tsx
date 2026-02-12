/**
 * Case Study Component
 * 
 * Featured customer story: Sanitär-Heinze
 */

import { Quote, ArrowRight, TrendingUp, Clock, CheckCircle } from 'lucide-react';
import { Button } from '../ui/button';
import { motion } from 'framer-motion';

export function CaseStudy() {
    return (
        <section id="customers" className="section-py section-px bg-slate-900 text-white">
            <div className="landing-container">

                <div className="grid md:grid-cols-2 gap-12 md:gap-24 items-center">

                    {/* Left Content */}
                    <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.8 }}
                        className="space-y-8"
                    >
                        <h2 className="text-3xl md:text-4xl font-bold tracking-tight">
                            "Mercura allows us to significantly increase productivity in the quotation department."
                        </h2>

                        <div className="space-y-6 text-slate-300 text-lg leading-relaxed">
                            <p>
                                <Quote className="h-8 w-8 mb-4 text-primary" />
                                Finding qualified staff is hard. AI ensures that technical
                                knowledge is never lost when seniors retire or people change roles.
                            </p>
                        </div>

                        <div className="flex items-center gap-4 pt-4 border-t border-slate-700">
                            <div className="h-12 w-12 rounded-full bg-slate-700 overflow-hidden flex items-center justify-center">
                                {/* Placeholder for customer photo */}
                                <span className="font-bold text-white">MS</span>
                            </div>
                            <div>
                                <div className="font-bold text-white">Maria Schmidt</div>
                                <div className="text-sm text-slate-400">Head of Sales</div>
                                <div className="text-xs text-primary font-semibold mt-1 uppercase tracking-wider">Sanitär-Heinze</div>
                            </div>
                        </div>

                        <div className="pt-8">
                            <Button
                                variant="outline"
                                className="text-white border-white/20 hover:bg-white/10"
                            >
                                Read Full Case Study
                                <ArrowRight className="ml-2 h-4 w-4" />
                            </Button>
                        </div>
                    </motion.div>

                    {/* Right Stats Card */}
                    <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.8, delay: 0.2 }}
                        className="bg-slate-800 rounded-2xl p-8 border border-slate-700 shadow-2xl transform rotate-1 hover:rotate-0 transition-transform duration-500"
                    >
                        <div className="space-y-8">
                            <div className="flex items-start gap-4 p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                                <div className="bg-emerald-500/20 p-2 rounded-lg text-emerald-400">
                                    <TrendingUp className="h-6 w-6" />
                                </div>
                                <div>
                                    <div className="text-2xl font-bold text-white">+30%</div>
                                    <div className="text-sm text-slate-400">More quotes processed per rep</div>
                                </div>
                            </div>

                            <div className="flex items-start gap-4 p-4 rounded-xl bg-blue-500/10 border border-blue-500/20">
                                <div className="bg-blue-500/20 p-2 rounded-lg text-blue-400">
                                    <Clock className="h-6 w-6" />
                                </div>
                                <div>
                                    <div className="text-2xl font-bold text-white">75% Faster</div>
                                    <div className="text-sm text-slate-400">Turnaround time on complex RFQs</div>
                                </div>
                            </div>

                            <div className="flex items-start gap-4 p-4 rounded-xl bg-purple-500/10 border border-purple-500/20">
                                <div className="bg-purple-500/20 p-2 rounded-lg text-purple-400">
                                    <CheckCircle className="h-6 w-6" />
                                </div>
                                <div>
                                    <div className="text-2xl font-bold text-white">Zero Error</div>
                                    <div className="text-sm text-slate-400">Reduction in pricing mistakes</div>
                                </div>
                            </div>
                        </div>
                    </motion.div>

                </div>

            </div>
        </section>
    );
}
