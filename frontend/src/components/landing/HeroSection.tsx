/**
 * Hero Section Component
 * 
 * Above-the-fold hero with headline, subheadline, CTAs, and dashboard mockup
 */

import { Button } from '../ui/button';
import { ArrowRight } from 'lucide-react';
import { motion } from 'framer-motion';

export function HeroSection() {
    return (
        <motion.section
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="relative section-py section-px tech-grid gradient-mesh pt-32 md:pt-40"
        >
            <div className="landing-container">
                <div className="text-center space-y-8 max-w-5xl mx-auto">
                    {/* Headline */}
                    <motion.h1
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2, duration: 0.8 }}
                        className="hero-headline"
                    >
                        Silicon Valley technology,
                        <br />
                        <span className="text-primary">for the backbone of our economy</span>
                    </motion.h1>

                    {/* Subheadline */}
                    <motion.p
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.4, duration: 0.8 }}
                        className="hero-subheadline max-w-3xl mx-auto"
                    >
                        Automate your inside sales processes with AI that understands customer requests,
                        matches products, and wins more business.
                    </motion.p>

                    {/* CTAs */}
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.6, duration: 0.8 }}
                        className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4"
                    >
                        <Button
                            size="lg"
                            className="cta-primary"
                            onClick={() => window.location.href = '#demo'}
                        >
                            Get a Demo
                        </Button>
                        <Button
                            size="lg"
                            variant="outline"
                            className="cta-secondary"
                            onClick={() => {
                                const element = document.getElementById('how-it-works');
                                element?.scrollIntoView({ behavior: 'smooth' });
                            }}
                        >
                            See How It Works
                            <ArrowRight className="ml-2 h-5 w-5" />
                        </Button>
                    </motion.div>

                    {/* Dashboard Mockup */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ delay: 0.8, duration: 1 }}
                        className="pt-12 md:pt-16"
                    >
                        <div className="bento-card p-4 shadow-soft-lg">
                            <div className="aspect-video bg-gradient-to-br from-slate-100 to-slate-200 rounded-lg flex items-center justify-center">
                                <div className="text-center space-y-2">
                                    <div className="text-4xl">📊</div>
                                    <p className="text-muted-foreground text-sm">Dashboard Mockup</p>
                                    <p className="text-xs text-muted-foreground/70">
                                        Screenshot will be added here
                                    </p>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                </div>
            </div>
        </motion.section>
    );
}
