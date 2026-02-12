/**
 * Problem Section Component
 * 
 * "Sales Reps Should Sell, Not Search"
 * Illustrates the pain points Mercura solves
 */

import { FileText, Mail, Table, FileSpreadsheet } from 'lucide-react';
import { motion } from 'framer-motion';

export function ProblemSection() {
    const dataSources = [
        { icon: FileText, label: 'PDFs' },
        { icon: FileSpreadsheet, label: 'Excel' },
        { icon: Mail, label: 'Email' },
        { icon: Table, label: 'GAEB' },
    ];

    return (
        <section id="product" className="section-py section-px bg-slate-50">
            <div className="landing-container">
                <div className="grid md:grid-cols-2 gap-12 md:gap-16 items-center">
                    {/* Visual Side */}
                    <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.8 }}
                        className="order-2 md:order-1"
                    >
                        <div className="bento-card p-8 md:p-12 text-center space-y-6">
                            {/* Frustrated Rep Illustration */}
                            <div className="text-6xl mb-4">😓</div>
                            <p className="text-lg font-semibold text-muted-foreground">
                                Buried in manual paperwork
                            </p>

                            {/* Data Source Icons */}
                            <div className="grid grid-cols-4 gap-4 pt-6">
                                {dataSources.map((source, index) => (
                                    <div
                                        key={index}
                                        className="flex flex-col items-center gap-2 p-3 bg-slate-100 rounded-lg"
                                    >
                                        <source.icon className="h-6 w-6 text-muted-foreground" />
                                        <span className="text-xs text-muted-foreground">{source.label}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </motion.div>

                    {/* Content Side */}
                    <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.8, delay: 0.2 }}
                        className="order-1 md:order-2 space-y-6"
                    >
                        <h2 className="section-headline">
                            Sales Reps Should Sell,
                            <br />
                            <span className="text-primary">Not Search</span>
                        </h2>

                        <div className="space-y-4 body-large">
                            <p>
                                Your best salespeople are buried in manual paperwork.
                            </p>
                            <p>
                                Instead of closing deals, they're searching through hundreds of
                                pages of specifications.
                            </p>
                            <p className="font-semibold text-foreground">
                                Every hour wasted on admin is an hour not spent selling.
                            </p>
                        </div>
                    </motion.div>
                </div>
            </div>
        </section>
    );
}
