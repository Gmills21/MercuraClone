/**
 * Landing Footer Component
 * 
 * Final CTA and Footer Structure
 * Compliance Badges: SOC 2, GDPR, YC
 */

import { Button } from '../ui/button';
import { ShieldCheck, Globe, Trophy } from 'lucide-react';

export function LandingFooter() {
    const currentYear = new Date().getFullYear();

    return (
        <footer className="pt-24 pb-12 bg-slate-50 border-t border-slate-200">
            <div className="landing-container section-px">

                {/* Main CTA */}
                <div id="demo" className="text-center mb-24 max-w-4xl mx-auto space-y-8">
                    <h2 className="text-4xl md:text-5xl font-bold tracking-tight text-slate-900">
                        Save 16 hours. <span className="text-muted-foreground">Per rep, per week.</span>
                    </h2>
                    <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                        <Button
                            size="lg"
                            className="cta-primary text-xl px-12 py-8 h-auto w-full sm:w-auto"
                            onClick={() => window.location.href = '#demo'}
                        >
                            Get a Demo
                        </Button>
                        <Button
                            size="lg"
                            variant="outline"
                            className="cta-secondary text-xl px-12 py-8 h-auto w-full sm:w-auto"
                            onClick={() => window.location.href = '/app/dashboard'}
                        >
                            Start Free Trial
                        </Button>
                    </div>
                </div>

                {/* Compliance & Trust Badges */}
                <div className="flex flex-wrap justify-center gap-8 md:gap-16 mb-24 border-y border-slate-200 py-12">
                    <div className="flex items-center gap-3 text-slate-600 font-semibold">
                        <ShieldCheck className="h-6 w-6 text-emerald-600" />
                        SOC 2 Type II Certified
                    </div>
                    <div className="flex items-center gap-3 text-slate-600 font-semibold">
                        <Globe className="h-6 w-6 text-blue-600" />
                        GDPR Compliant
                    </div>
                    <div className="flex items-center gap-3 text-slate-600 font-semibold">
                        <Trophy className="h-6 w-6 text-orange-500" />
                        Backed by Y Combinator
                    </div>
                </div>

                {/* Links Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-12 mb-16">
                    <div className="col-span-2 lg:col-span-2">
                        <div className="flex items-center gap-2 mb-6">
                            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                                <span className="text-white font-bold text-lg">M</span>
                            </div>
                            <span className="text-xl font-bold tracking-tight">Mercura</span>
                        </div>
                        <p className="text-muted-foreground text-sm max-w-xs">
                            Silicon Valley technology for the backbone of our economy.
                            Automating inside sales for industrial distributors.
                        </p>
                    </div>

                    <div className="footer-section">
                        <h4 className="footer-heading">Product</h4>
                        <ul className="space-y-3">
                            <li><a href="#" className="footer-link">Features</a></li>
                            <li><a href="#" className="footer-link">Integrations</a></li>
                            <li><a href="#" className="footer-link">Pricing</a></li>
                            <li><a href="#" className="footer-link">Changelog</a></li>
                        </ul>
                    </div>

                    <div className="footer-section">
                        <h4 className="footer-heading">Company</h4>
                        <ul className="space-y-3">
                            <li><a href="#" className="footer-link">About Us</a></li>
                            <li><a href="#" className="footer-link">Careers</a></li>
                            <li><a href="#" className="footer-link">Blog</a></li>
                            <li><a href="#" className="footer-link">Contact</a></li>
                        </ul>
                    </div>

                    <div className="footer-section">
                        <h4 className="footer-heading">Legal</h4>
                        <ul className="space-y-3">
                            <li><a href="#" className="footer-link">Privacy Policy</a></li>
                            <li><a href="#" className="footer-link">Terms of Service</a></li>
                            <li><a href="#" className="footer-link">Security</a></li>
                            <li><a href="#" className="footer-link">DPA</a></li>
                        </ul>
                    </div>
                </div>

                {/* Copyright */}
                <div className="border-t border-slate-200 pt-8 flex flex-col md:flex-row justify-between items-center gap-4 text-sm text-muted-foreground">
                    <p>© {currentYear} Mercura Inc. All rights reserved.</p>
                    <div className="flex items-center gap-6">
                        <a href="#" className="hover:text-slate-900 transition-colors">Twitter</a>
                        <a href="#" className="hover:text-slate-900 transition-colors">LinkedIn</a>
                        <a href="#" className="hover:text-slate-900 transition-colors">GitHub</a>
                    </div>
                </div>

            </div>
        </footer>
    );
}
