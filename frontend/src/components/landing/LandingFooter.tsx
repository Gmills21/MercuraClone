/**
 * Landing Footer Component - Production Ready
 * 
 * Final CTA and comprehensive footer
 */

import { Button } from '../ui/button';
import { ShieldCheck, Globe, Trophy, ArrowRight, Sparkles, Mail, MapPin, Phone } from 'lucide-react';
import { motion } from 'framer-motion';

export function LandingFooter() {
    const currentYear = new Date().getFullYear();

    const footerLinks = {
        product: [
            { label: 'Features', href: '#features' },
            { label: 'Integrations', href: '#' },
            { label: 'Pricing', href: '#' },
            { label: 'Security', href: '#' },
            { label: 'Changelog', href: '#' },
        ],
        company: [
            { label: 'About Us', href: '#' },
            { label: 'Careers', href: '#' },
            { label: 'Blog', href: '#' },
            { label: 'Press Kit', href: '#' },
            { label: 'Contact', href: '#' },
        ],
        resources: [
            { label: 'Documentation', href: '#' },
            { label: 'API Reference', href: '#' },
            { label: 'Help Center', href: '#' },
            { label: 'Case Studies', href: '#' },
            { label: 'Webinars', href: '#' },
        ],
        legal: [
            { label: 'Privacy Policy', href: '#' },
            { label: 'Terms of Service', href: '#' },
            { label: 'Cookie Policy', href: '#' },
            { label: 'DPA', href: '#' },
        ],
    };

    return (
        <footer className="bg-slate-900 text-white">
            {/* CTA Section */}
            <div className="border-b border-white/10">
                <div className="landing-container section-px py-20">
                    <motion.div
                        initial={{ opacity: 0, y: 30 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="text-center max-w-4xl mx-auto"
                    >
                        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-orange-500/20 text-orange-400 text-sm font-medium mb-6">
                            <Sparkles size={16} />
                            Start your free trial today
                        </div>
                        <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight mb-6">
                            Ready to save
                            <br />
                            <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-400 to-red-400">
                                16 hours per week?
                            </span>
                        </h2>
                        <p className="text-lg text-white/60 mb-10 max-w-2xl mx-auto">
                            Join 40+ industrial distributors already using Mercura to automate their quoting process. 
                            Get started in minutes, not months.
                        </p>
                        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                            <Button
                                size="lg"
                                className="bg-white text-slate-900 hover:bg-slate-100 px-8 py-6 text-base font-semibold rounded-xl shadow-xl w-full sm:w-auto"
                                onClick={() => window.location.href = '#demo'}
                            >
                                Get a Demo
                                <ArrowRight className="ml-2 h-5 w-5" />
                            </Button>
                            <Button
                                size="lg"
                                variant="outline"
                                className="border-white/20 text-white hover:bg-white/10 px-8 py-6 text-base font-semibold rounded-xl w-full sm:w-auto"
                                onClick={() => window.location.href = '/app/dashboard'}
                            >
                                Start Free Trial
                            </Button>
                        </div>
                        <p className="text-sm text-white/40 mt-6">
                            No credit card required. 14-day free trial.
                        </p>
                    </motion.div>
                </div>
            </div>

            {/* Trust Badges */}
            <div className="border-b border-white/10">
                <div className="landing-container section-px py-8">
                    <div className="flex flex-wrap justify-center items-center gap-8 md:gap-16">
                        {[
                            { icon: ShieldCheck, label: "SOC 2 Type II Certified" },
                            { icon: Globe, label: "GDPR Compliant" },
                            { icon: Trophy, label: "Backed by Y Combinator" },
                        ].map((badge, i) => (
                            <div key={i} className="flex items-center gap-2 text-white/60">
                                <badge.icon size={20} className="text-orange-400" />
                                <span className="text-sm font-medium">{badge.label}</span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {/* Main Footer Content */}
            <div className="landing-container section-px py-16">
                <div className="grid grid-cols-2 md:grid-cols-6 gap-8 mb-16">
                    {/* Brand Column */}
                    <div className="col-span-2">
                        <div className="flex items-center gap-2 mb-4">
                            <div className="w-10 h-10 bg-gradient-to-r from-orange-500 to-red-500 rounded-xl flex items-center justify-center">
                                <span className="text-white font-bold text-xl">M</span>
                            </div>
                            <span className="text-2xl font-bold tracking-tight">Mercura</span>
                        </div>
                        <p className="text-sm text-white/60 mb-6 max-w-xs leading-relaxed">
                            Silicon Valley technology for the backbone of our economy. 
                            Automating inside sales for industrial distributors.
                        </p>
                        <div className="space-y-2 text-sm text-white/40">
                            <div className="flex items-center gap-2">
                                <Mail size={14} />
                                <span>hello@mercura.ai</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <Phone size={14} />
                                <span>+1 (555) 123-4567</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <MapPin size={14} />
                                <span>San Francisco, CA</span>
                            </div>
                        </div>
                    </div>

                    {/* Links Columns */}
                    <div>
                        <h4 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">Product</h4>
                        <ul className="space-y-3">
                            {footerLinks.product.map((link, i) => (
                                <li key={i}>
                                    <a href={link.href} className="text-sm text-white/60 hover:text-white transition-colors">
                                        {link.label}
                                    </a>
                                </li>
                            ))}
                        </ul>
                    </div>

                    <div>
                        <h4 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">Company</h4>
                        <ul className="space-y-3">
                            {footerLinks.company.map((link, i) => (
                                <li key={i}>
                                    <a href={link.href} className="text-sm text-white/60 hover:text-white transition-colors">
                                        {link.label}
                                    </a>
                                </li>
                            ))}
                        </ul>
                    </div>

                    <div>
                        <h4 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">Resources</h4>
                        <ul className="space-y-3">
                            {footerLinks.resources.map((link, i) => (
                                <li key={i}>
                                    <a href={link.href} className="text-sm text-white/60 hover:text-white transition-colors">
                                        {link.label}
                                    </a>
                                </li>
                            ))}
                        </ul>
                    </div>

                    <div>
                        <h4 className="text-sm font-semibold text-white uppercase tracking-wider mb-4">Legal</h4>
                        <ul className="space-y-3">
                            {footerLinks.legal.map((link, i) => (
                                <li key={i}>
                                    <a href={link.href} className="text-sm text-white/60 hover:text-white transition-colors">
                                        {link.label}
                                    </a>
                                </li>
                            ))}
                        </ul>
                    </div>
                </div>

                {/* Bottom Bar */}
                <div className="pt-8 border-t border-white/10 flex flex-col md:flex-row justify-between items-center gap-4">
                    <p className="text-sm text-white/40">
                        © {currentYear} Mercura Inc. All rights reserved.
                    </p>
                    <div className="flex items-center gap-6">
                        {['Twitter', 'LinkedIn', 'YouTube'].map((social, i) => (
                            <a 
                                key={i} 
                                href="#" 
                                className="text-sm text-white/40 hover:text-white transition-colors"
                            >
                                {social}
                            </a>
                        ))}
                    </div>
                </div>
            </div>
        </footer>
    );
}
