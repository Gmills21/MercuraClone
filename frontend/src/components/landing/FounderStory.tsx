/**
 * Founder Story Component
 * 
 * "From the Industry, For the Industry"
 */

import { Quote } from 'lucide-react';
import { motion } from 'framer-motion';

export function FounderStory() {
    return (
        <section className="section-py section-px bg-white border-t border-minimal">
            <div className="landing-container">
                <div className="founder-section">
                    {/* Founder Photo */}
                    <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.8 }}
                        className="md:w-1/3 flex justify-center md:justify-end"
                    >
                        <div className="relative">
                            <div className="w-64 h-64 bg-slate-200 rounded-2xl overflow-hidden shadow-soft-lg rotate-3 hover:rotate-0 transition-transform duration-500">
                                {/* Placeholder for founder photo */}
                                <img
                                    src="https://placehold.co/400x400/e2e8f0/94a3b8?text=Founder"
                                    alt="Founder"
                                    className="w-full h-full object-cover"
                                />
                            </div>
                            <div className="absolute -bottom-6 -right-6 bg-white p-4 rounded-xl shadow-soft border border-slate-100 flex items-center gap-3">
                                <div className="text-4xl">🏗️</div>
                                <div className="text-sm font-semibold text-slate-700">
                                    115 Years<br />in Distribution
                                </div>
                            </div>
                        </div>
                    </motion.div>

                    {/* Story Content */}
                    <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.8, delay: 0.2 }}
                        className="md:w-2/3 space-y-8"
                    >
                        <h2 className="section-headline">
                            From the Industry, For the Industry
                        </h2>

                        <div className="bg-slate-50 p-8 rounded-2xl relative border border-slate-100">
                            <Quote className="h-12 w-12 text-primary/10 absolute top-6 left-6 -z-0" />

                            <div className="relative z-10 space-y-6 text-lg md:text-xl leading-relaxed text-slate-700">
                                <p>
                                    "We're not just technologists. Our family has <span className="font-semibold text-primary">115 years in plumbing and electrical distribution</span>."
                                </p>
                                <p>
                                    "We built Mercura because we've seen firsthand how much time gets wasted on quoting.
                                    Combined with engineering experience from Google, we created an AI that's not just smart—it's a
                                    <span className="italic font-medium text-slate-900 mx-1">Subject Matter Expert</span>
                                    coworker built for hard-working people in the trades."
                                </p>
                            </div>

                            <div className="mt-8 flex items-center gap-4 border-t border-slate-200 pt-6">
                                <div className="h-12 w-12 rounded-full bg-slate-200 flex items-center justify-center font-bold text-slate-500">
                                    F
                                </div>
                                <div>
                                    <div className="font-bold text-slate-900">Founder Name</div>
                                    <div className="text-sm text-slate-500">CEO & Co-Founder</div>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                </div>
            </div>
        </section>
    );
}
