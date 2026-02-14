/**
 * Founder Story Component - Production Ready
 * 
 * "From the Industry, For the Industry"
 */

import { Quote, Award, Factory, HardHat, Wrench, TrendingUp, Users } from 'lucide-react';
import { motion } from 'framer-motion';

const credentials = [
    { icon: Factory, label: "115 Years", sublabel: "Family in Distribution" },
    { icon: Users, label: "Google", sublabel: "Engineering Alumni" },
    { icon: TrendingUp, label: "Y Combinator", sublabel: "W24 Batch" },
];

export function FounderStory() {
    return (
        <section className="section-py section-px bg-slate-50 border-y border-slate-200 relative overflow-hidden">
            {/* Background decorations */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_50%,rgba(249,115,22,0.05)_0%,transparent_50%)]" />

            <div className="landing-container relative">
                <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">
                    {/* Founder Image Side */}
                    <motion.div
                        initial={{ opacity: 0, x: -30 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.6 }}
                        className="relative"
                    >
                        <div className="relative inline-block">
                            {/* Main Image Container */}
                            <div className="w-72 h-72 md:w-80 md:h-80 bg-gradient-to-br from-slate-200 to-slate-300 rounded-2xl overflow-hidden shadow-2xl rotate-2 hover:rotate-0 transition-transform duration-500 relative">
                                {/* Placeholder for founder photo - using a nice gradient pattern */}
                                <div className="absolute inset-0 bg-gradient-to-br from-slate-700 to-slate-900 flex items-center justify-center">
                                    <div className="text-center">
                                        <HardHat size={64} className="text-slate-400 mx-auto mb-4" />
                                        <p className="text-slate-500 text-sm">Founder Photo</p>
                                    </div>
                                </div>
                            </div>

                            {/* Experience Badge */}
                            <motion.div
                                initial={{ scale: 0 }}
                                whileInView={{ scale: 1 }}
                                viewport={{ once: true }}
                                transition={{ delay: 0.3, type: "spring" }}
                                className="absolute -bottom-4 -right-4 bg-white p-4 rounded-xl shadow-xl border border-slate-100"
                            >
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                                        <Factory size={20} className="text-orange-600" />
                                    </div>
                                    <div>
                                        <p className="text-lg font-bold text-slate-900">115 Years</p>
                                        <p className="text-xs text-slate-500">in Distribution</p>
                                    </div>
                                </div>
                            </motion.div>

                            {/* YC Badge */}
                            <motion.div
                                initial={{ scale: 0 }}
                                whileInView={{ scale: 1 }}
                                viewport={{ once: true }}
                                transition={{ delay: 0.5, type: "spring" }}
                                className="absolute -top-4 -left-4 bg-orange-500 text-white px-4 py-2 rounded-lg shadow-xl"
                            >
                                <div className="flex items-center gap-2">
                                    <span className="font-bold">Y Combinator</span>
                                    <span className="text-orange-200">W24</span>
                                </div>
                            </motion.div>
                        </div>
                    </motion.div>

                    {/* Story Content */}
                    <motion.div
                        initial={{ opacity: 0, x: 30 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.6, delay: 0.2 }}
                        className="space-y-8"
                    >
                        <div>
                            <motion.span
                                initial={{ opacity: 0, y: 10 }}
                                whileInView={{ opacity: 1, y: 0 }}
                                viewport={{ once: true }}
                                className="inline-flex items-center gap-2 text-sm font-semibold text-orange-600 mb-4"
                            >
                                <Wrench size={16} />
                                Our Story
                            </motion.span>
                            <h2 className="section-headline mb-4">
                                From the Industry,
                                <br />
                                <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-500 to-red-600">
                                    For the Industry
                                </span>
                            </h2>
                        </div>

                        {/* Quote Box */}
                        <div className="bg-white p-6 md:p-8 rounded-2xl border border-slate-200 shadow-lg relative">
                            <Quote className="h-10 w-10 text-orange-100 absolute top-4 left-4" />
                            
                            <div className="relative z-10 space-y-4 text-slate-700 leading-relaxed">
                                <p>
                                    "We're not just technologists. Our family has <span className="font-semibold text-slate-900">115 years in plumbing and electrical distribution</span>. 
                                    We grew up in warehouses, worked the counter, and understand the pain of manual quoting firsthand."
                                </p>
                                <p>
                                    "We built Mercura because we watched our best salespeople spend their days copy-pasting between spreadsheets 
                                    instead of building relationships. Combined with engineering experience from Google, we created an AI that's 
                                    not just smart—it's a <span className="font-semibold text-slate-900">Subject Matter Expert coworker</span> built for hard-working people in the trades."
                                </p>
                            </div>

                            {/* Founder Info */}
                            <div className="mt-6 pt-6 border-t border-slate-100 flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <div className="w-12 h-12 rounded-full bg-slate-200 flex items-center justify-center font-bold text-slate-500">
                                        F
                                    </div>
                                    <div>
                                        <p className="font-bold text-slate-900">Founder Name</p>
                                        <p className="text-sm text-slate-500">CEO & Co-Founder</p>
                                    </div>
                                </div>
                                <div className="hidden sm:flex items-center gap-1 text-orange-600">
                                    <Award size={16} />
                                    <span className="text-sm font-medium">Y Combinator W24</span>
                                </div>
                            </div>
                        </div>

                        {/* Credentials */}
                        <div className="grid grid-cols-3 gap-4">
                            {credentials.map((cred, i) => (
                                <motion.div
                                    key={i}
                                    initial={{ opacity: 0, y: 20 }}
                                    whileInView={{ opacity: 1, y: 0 }}
                                    viewport={{ once: true }}
                                    transition={{ delay: 0.4 + i * 0.1 }}
                                    className="text-center p-4 bg-white rounded-xl border border-slate-200"
                                >
                                    <cred.icon size={20} className="text-orange-500 mx-auto mb-2" />
                                    <p className="font-bold text-slate-900 text-sm">{cred.label}</p>
                                    <p className="text-[10px] text-slate-500">{cred.sublabel}</p>
                                </motion.div>
                            ))}
                        </div>
                    </motion.div>
                </div>
            </div>
        </section>
    );
}
