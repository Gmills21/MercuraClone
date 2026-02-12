/**
 * Landing Header Component
 * 
 * Sticky navigation with glass effect on scroll
 * Implements Linear.app aesthetic
 */

import { useState, useEffect } from 'react';
import { Button } from '../ui/button';

export function LandingHeader() {
    const [isScrolled, setIsScrolled] = useState(false);

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
        }
    };

    return (
        <header
            className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${isScrolled ? 'header-scrolled' : 'bg-transparent'
                }`}
        >
            <nav className="landing-container section-px py-4 flex justify-between items-center">
                {/* Logo */}
                <div className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                        <span className="text-white font-bold text-lg">M</span>
                    </div>
                    <span className="text-xl font-bold tracking-tight">Mercura</span>
                </div>

                {/* Navigation Links - Desktop */}
                <div className="hidden md:flex items-center gap-8">
                    <button
                        onClick={() => scrollToSection('product')}
                        className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                    >
                        Product
                    </button>
                    <button
                        onClick={() => scrollToSection('features')}
                        className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                    >
                        Features
                    </button>
                    <button
                        onClick={() => scrollToSection('roi')}
                        className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                    >
                        ROI Calculator
                    </button>
                    <button
                        onClick={() => scrollToSection('customers')}
                        className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                    >
                        Customers
                    </button>
                </div>

                {/* CTA Button */}
                <div className="flex items-center gap-4">
                    <Button
                        onClick={() => window.location.href = '/app/dashboard'}
                        variant="ghost"
                        className="hidden md:inline-flex"
                    >
                        Sign In
                    </Button>
                    <Button
                        onClick={() => window.location.href = '#demo'}
                        className="bg-primary text-primary-foreground hover:opacity-90"
                    >
                        Get a Demo
                    </Button>
                </div>
            </nav>
        </header>
    );
}
