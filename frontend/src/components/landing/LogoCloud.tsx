/**
 * Logo Cloud Component - Production Ready
 * 
 * Trust layer with stats and customer logos
 */

import { Building2, Shield, CheckCircle, Zap, Award } from 'lucide-react';
import { motion } from 'framer-motion';

const stats = [
    { value: "40+", label: "Beta Users" },
    { value: "$2.4M", label: "Quotes Processed" },
    { value: "95%", label: "Time Savings" },
];

const badges = [
    { icon: Shield, label: "Enterprise Security" },
    { icon: CheckCircle, label: "GDPR Compliant" },
    { icon: Zap, label: "AI-Powered" },
];

export function LogoCloud() {
    return (
        <section className="py-16 border-y border-slate-200 bg-white">
            <div className="landing-container section-px">
                {/* Stats Row */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="flex flex-wrap justify-center gap-8 md:gap-16 mb-12 pb-12 border-b border-slate-100"
                >
                    {stats.map((stat, i) => (
                        <div key={i} className="text-center">
                            <p className="text-3xl md:text-4xl font-bold text-slate-900">{stat.value}</p>
                            <p className="text-sm text-slate-500 mt-1">{stat.label}</p>
                        </div>
                    ))}
                </motion.div>

                {/* Trust Badges */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: 0.1 }}
                    className="flex flex-wrap justify-center items-center gap-6 md:gap-10 mb-12"
                >
                    {badges.map((badge, i) => (
                        <div key={i} className="flex items-center gap-2 text-slate-600">
                            <badge.icon size={18} className="text-orange-500" />
                            <span className="text-sm font-semibold">{badge.label}</span>
                        </div>
                    ))}
                </motion.div>

                {/* Customer Logos */}
                <motion.div
                    initial={{ opacity: 0 }}
                    whileInView={{ opacity: 1 }}
                    viewport={{ once: true }}
                    transition={{ delay: 0.2 }}
                    className="text-center"
                >
                    <p className="text-xs text-slate-400 uppercase tracking-wider font-semibold mb-6">
                        Trusted by industry-leading distributors
                    </p>
                    <div className="flex flex-wrap justify-center items-center gap-8 md:gap-12 opacity-50 hover:opacity-70 transition-opacity duration-300">
                        {[
                            { name: 'Sanitär-Heinze', initials: 'SH' },
                            { name: 'Metro HVAC', initials: 'MH' },
                            { name: 'Industrial Supply', initials: 'IS' },
                            { name: 'Premier Plumbing', initials: 'PP' },
                            { name: 'Commercial Electric', initials: 'CE' },
                            { name: 'Building Solutions', initials: 'BS' },
                        ].map((logo, i) => (
                            <div
                                key={i}
                                className="flex items-center gap-2 text-slate-400 hover:text-slate-600 transition-colors"
                            >
                                <div className="w-8 h-8 rounded bg-slate-100 flex items-center justify-center text-[10px] font-bold">
                                    {logo.initials}
                                </div>
                                <span className="text-sm font-medium hidden sm:inline">{logo.name}</span>
                            </div>
                        ))}
                    </div>
                </motion.div>
            </div>
        </section>
    );
}
