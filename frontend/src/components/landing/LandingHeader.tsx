/**
 * Landing Header Component - Production Ready
 * 
 * Sticky navigation with glass effect on scroll
 * Implements Linear.app aesthetic
 */

import { useState, useEffect } from 'react';
import { Button } from '../ui/button';
import { Menu, X, Sparkles } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export function LandingHeader() {
    const [isScrolled, setIsScrolled] = useState(false);
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    useEffect(() => {
        const handleScroll = () => {
            setIsScrolled(window.scrollY > 20);
        };

        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    const scrollToSection = (id: string) => {
        const element = document.getElementById(id);
        if (element) {
            element.scrollIntoView({ behavior: 'smooth' });
            setIsMobileMenuOpen(false);
        }
    };

    const navLinks = [
        { label: 'Product', id: 'product' },
        { label: 'Features', id: 'features' },
        { label: 'How It Works', id: 'how-it-works' },
        { label: 'ROI', id: 'roi' },
        { label: 'Customers', id: 'customers' },
    ];

    return (
        <>
            <header
                className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
                    isScrolled 
                        ? 'bg-white/80 backdrop-blur-xl border-b border-slate-200/50 shadow-sm' 
                        : 'bg-transparent'
                }`}
            >
                <nav className="landing-container section-px py-4 flex justify-between items-center">
                    {/* Logo */}
                    <a href="/" className="flex items-center gap-2 group">
                        <div className="w-9 h-9 bg-gradient-to-r from-orange-500 to-red-500 rounded-xl flex items-center justify-center shadow-lg shadow-orange-500/20 group-hover:shadow-orange-500/30 transition-shadow">
                            <span className="text-white font-bold text-lg">M</span>
                        </div>
                        <span className="text-xl font-bold tracking-tight text-slate-900">Mercura</span>
                    </a>

                    {/* Navigation Links - Desktop */}
                    <div className="hidden md:flex items-center gap-1">
                        {navLinks.map((link) => (
                            <button
                                type="button"
                                key={link.id}
                                onClick={() => scrollToSection(link.id)}
                                className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-all cursor-pointer"
                            >
                                {link.label}
                            </button>
                        ))}
                    </div>

                    {/* CTA Buttons */}
                    <div className="flex items-center gap-3">
                        <Button
                            onClick={() => window.location.href = '/app/dashboard'}
                            variant="ghost"
                            className="hidden md:inline-flex text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                        >
                            Sign In
                        </Button>
                        <Button
                            onClick={() => scrollToSection('demo')}
                            className="hidden md:inline-flex bg-slate-900 hover:bg-slate-800 text-white shadow-lg shadow-slate-900/20 hover:shadow-slate-900/30 transition-all"
                        >
                            <Sparkles size={16} className="mr-2 text-orange-400" />
                            Get a Demo
                        </Button>

                        {/* Mobile Menu Button */}
                        <button
                            type="button"
                            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                            className="md:hidden p-2 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
                        >
                            {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
                        </button>
                    </div>
                </nav>
            </header>

            {/* Mobile Menu */}
            <AnimatePresence>
                {isMobileMenuOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        transition={{ duration: 0.2 }}
                        className="fixed inset-x-0 top-[72px] z-40 md:hidden"
                    >
                        <div className="bg-white border-b border-slate-200 shadow-xl mx-4 rounded-2xl overflow-hidden">
                            <div className="p-4 space-y-2">
                                {navLinks.map((link) => (
                                    <button
                                        type="button"
                                        key={link.id}
                                        onClick={() => scrollToSection(link.id)}
                                        className="w-full text-left px-4 py-3 text-slate-600 hover:text-slate-900 hover:bg-slate-50 rounded-lg transition-colors font-medium cursor-pointer"
                                    >
                                        {link.label}
                                    </button>
                                ))}
                                <div className="pt-4 border-t border-slate-100 space-y-2">
                                    <Button
                                        onClick={() => window.location.href = '/app/dashboard'}
                                        variant="outline"
                                        className="w-full justify-center"
                                    >
                                        Sign In
                                    </Button>
                                    <Button
                                        onClick={() => scrollToSection('demo')}
                                        className="w-full justify-center bg-slate-900 text-white"
                                    >
                                        Get a Demo
                                    </Button>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </>
    );
}
