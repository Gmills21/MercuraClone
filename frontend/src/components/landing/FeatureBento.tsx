/**
 * Feature Bento Grid Component
 * 
 * 2x2 Feature Grid: Specs AI | Voice Agents | Email Requests | Integrations
 */

import { FileText, Mic, Mail, Blocks } from 'lucide-react';
import { motion } from 'framer-motion';

export function FeatureBento() {
    const features = [
        {
            icon: FileText,
            title: "Specifications AI",
            description: "Reads complex technical specs and tender texts provided in PDFs and Excel files.",
            iconBg: "bg-blue-50",
            iconColor: "text-blue-600",
            preview: "Spec preview visual"
        },
        {
            icon: Mic,
            title: "AI Voice Agents",
            description: "Intelligent assistants handle inquiries and provide real-time quotes via phone.",
            iconBg: "bg-orange-50",
            iconColor: "text-orange-600",
            preview: "Voice wave animation"
        },
        {
            icon: Mail,
            title: "Email Automation",
            description: "Turn inbox requests directly into CRM/ERP entries without human intervention.",
            iconBg: "bg-emerald-50",
            iconColor: "text-emerald-600",
            preview: "Email to CRM visual"
        },
        {
            icon: Blocks,
            title: "Enterprise Integrations",
            description: "Enterprise-ready connections to SAP, Oracle, QuickBooks, and P21.",
            iconBg: "bg-purple-50",
            iconColor: "text-purple-600",
            preview: "Integration logos stack"
        }
    ];

    return (
        <section id="features" className="section-py section-px bg-slate-50 relative overflow-hidden">
            <div className="absolute inset-0 tech-grid-fine opacity-30" />

            <div className="landing-container relative">
                <div className="text-center mb-12">
                    <h2 className="section-headline mb-4">Powerful Features</h2>
                    <p className="section-subline mx-auto">
                        Built to handle the complexity of industrial distribution.
                    </p>
                </div>

                <div className="feature-grid">
                    {features.map((feature, i) => (
                        <motion.div
                            key={i}
                            initial={{ opacity: 0, scale: 0.95 }}
                            whileInView={{ opacity: 1, scale: 1 }}
                            viewport={{ once: true }}
                            transition={{ delay: i * 0.1 }}
                            className="bento-card p-6 md:p-8 hover-lift"
                        >
                            <div className="flex items-start justify-between mb-8">
                                <div className={`p-3 rounded-lg ${feature.iconBg} ${feature.iconColor}`}>
                                    <feature.icon className="h-6 w-6" />
                                </div>
                                {/* Visual placeholder */}
                                <div className="h-24 w-32 bg-slate-100 rounded-lg flex items-center justify-center text-xs text-muted-foreground/50 border border-dashed border-slate-200">
                                    {feature.preview}
                                </div>
                            </div>

                            <h3 className="text-xl font-bold tracking-tight mb-2">{feature.title}</h3>
                            <p className="text-muted-foreground">{feature.description}</p>
                        </motion.div>
                    ))}
                </div>
            </div>
        </section>
    );
}
