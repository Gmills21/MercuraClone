/**
 * Landing Page - Main Container
 * 
 * Silicon Valley-grade landing page for Mercura
 * Implements Linear.app aesthetic with high-conversion design
 */

import { useEffect } from 'react';
import '../styles/landing.css';

// Import landing components (will be created in next phase)
import { LandingHeader } from '../components/landing/LandingHeader';
import { HeroSection } from '../components/landing/HeroSection';
import { LogoCloud } from '../components/landing/LogoCloud';
import { ProblemSection } from '../components/landing/ProblemSection';
import { HowItWorks } from '../components/landing/HowItWorks';
import { FeatureBento } from '../components/landing/FeatureBento';
import { ROICalculator } from '../components/landing/ROICalculator';
import { FounderStory } from '../components/landing/FounderStory';
import { CaseStudy } from '../components/landing/CaseStudy';
import { LandingFooter } from '../components/landing/LandingFooter';

export default function LandingPage() {
    // Set page title and meta tags
    useEffect(() => {
        document.title = 'Mercura - AI-Powered Quoting for Industrial Distributors';

        // Add meta description
        const metaDescription = document.querySelector('meta[name="description"]');
        if (metaDescription) {
            metaDescription.setAttribute('content',
                'Automate your inside sales processes with AI that understands customer requests, matches products, and wins more business. Save 16 hours per rep, per week.'
            );
        } else {
            const meta = document.createElement('meta');
            meta.name = 'description';
            meta.content = 'Automate your inside sales processes with AI that understands customer requests, matches products, and wins more business. Save 16 hours per rep, per week.';
            document.head.appendChild(meta);
        }
    }, []);

    return (
        <div className="landing-page bg-background min-h-screen">
            {/* Sticky Navigation Header */}
            <LandingHeader />

            {/* Main Content Sections */}
            <main>
                {/* 1. Hero Section - Above the fold */}
                <HeroSection />

                {/* 2. Trust Layer - Logo Cloud */}
                <LogoCloud />

                {/* 3. Problem Section - Pain Points */}
                <ProblemSection />

                {/* 4. How It Works - 3 Steps */}
                <HowItWorks />

                {/* 5. Feature Bento Grid - 2x2 */}
                <FeatureBento />

                {/* 6. ROI Calculator - Interactive */}
                <ROICalculator />

                {/* 7. Founder Story - Human Touch */}
                <FounderStory />

                {/* 8. Case Study - Social Proof */}
                <CaseStudy />
            </main>

            {/* Footer with Final CTA */}
            <LandingFooter />
        </div>
    );
}
