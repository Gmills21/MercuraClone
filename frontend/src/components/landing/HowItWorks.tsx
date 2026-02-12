/**
 * How It Works Component
 * 
 * 3-step process visualization: Receive -> Match -> ERP
 */

import { Mail, Target, Zap, ArrowRight } from 'lucide-react';
import { motion } from 'framer-motion';

export function HowItWorks() {
    const steps = [
        {
            icon: Mail,
            title: "Receive Request",
            description: "AI understands customer requests from any source instantly—whether it's an email, PDF, or Excel file.",
            color: "text-blue-500",
            bg: "bg-blue-50"
        },
        {
            icon: Target,
            title: "Smart Product Matching",
            description: "AI finds spec-compliant products and prioritizes highest-margin options from your catalog.",
            color: "text-primary",
            bg: "bg-orange-50"
        },
        {
            icon: Zap,
            title: "Send to ERP Instantly",
            description: "Generate an accurate quote ready in minutes, not hours or days. Push directly to your ERP.",
            color: "text-emerald-500",
            bg: "bg-emerald-50"
        }
    ];

    return (
        <section id="how-it-works" className="section-py section-px bg-white">
            <div className="landing-container">
                <div className="text-center mb-16 space-y-4">
                    <h2 className="section-headline">
                        How Mercura Transforms Your Workflow
                    </h2>
                    <p className="section-subline mx-auto">
                        From chaos to clarity in three simple steps.
                    </p>
                </div>

                <div className="grid md:grid-cols-3 gap-8 relative">
                    {/* Connecting Line (Desktop only) */}
                    <div className="hidden md:block absolute top-12 left-[20%] right-[20%] h-0.5 bg-slate-100 -z-10" />

                    {steps.map((step, index) => (
                        <motion.div
                            key={index}
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.5, delay: index * 0.2 }}
                            className="step-card group bg-white"
                        >
                            <div className={`w-16 h-16 mx-auto rounded-2xl flex items-center justify-center mb-6 ${step.bg} transition-transform group-hover:scale-110 duration-300`}>
                                <step.icon className={`h-8 w-8 ${step.color}`} />
                            </div>

                            <h3 className="step-title mb-3">{step.title}</h3>
                            <p className="step-description text-sm px-4">
                                {step.description}
                            </p>

                            {index < steps.length - 1 && (
                                <div className="md:hidden mt-8 flex justify-center text-slate-300">
                                    <ArrowRight className="h-6 w-6 rotate-90" />
                                </div>
                            )}
                        </motion.div>
                    ))}
                </div>
            </div>
        </section>
    );
}
