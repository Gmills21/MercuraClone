/**
 * Landing Page - Main Container (Production Ready)
 * 
 * Complete landing page for Mercura
 * Implements Linear.app aesthetic with high-conversion design
 */

import { useEffect } from 'react';
import '../styles/landing.css';

// Import landing components
import { LandingHeader } from '../components/landing/LandingHeader';
import { HeroSection } from '../components/landing/HeroSection';
import { LogoCloud } from '../components/landing/LogoCloud';
import { ProblemSection } from '../components/landing/ProblemSection';
import { HowItWorks } from '../components/landing/HowItWorks';
import { FeatureBento } from '../components/landing/FeatureBento';
import { ROICalculator } from '../components/landing/ROICalculator';
import { TestimonialsSection } from '../components/landing/TestimonialsSection';
import { FounderStory } from '../components/landing/FounderStory';
import { CaseStudy } from '../components/landing/CaseStudy';
import { LandingFooter } from '../components/landing/LandingFooter';

export default function LandingPage() {
    // Set page title and meta tags
    useEffect(() => {
        document.title = 'Mercura - AI Inside Sales Agent for Industrial Distributors';

        // Add meta description
        const metaDescription = document.querySelector('meta[name="description"]');
        if (metaDescription) {
            metaDescription.setAttribute('content',
                'Mercura is an AI-powered inside sales agent for industrial distributors. Automate RFQ extraction, product matching, and quote generation. Save 16 hours per rep, per week.'
            );
        } else {
            const meta = document.createElement('meta');
            meta.name = 'description';
            meta.content = 'Mercura is an AI-powered inside sales agent for industrial distributors. Automate RFQ extraction, product matching, and quote generation. Save 16 hours per rep, per week.';
            document.head.appendChild(meta);
        }

        // Add Open Graph meta tags
        const ogTags = [
            { property: 'og:title', content: 'Mercura - AI Inside Sales Agent for Industrial Distributors' },
            { property: 'og:description', content: 'Automate RFQ extraction, product matching, and quote generation. Save 16 hours per rep, per week.' },
            { property: 'og:type', content: 'website' },
            { property: 'twitter:card', content: 'summary_large_image' },
        ];

        ogTags.forEach(tag => {
            const existing = document.querySelector(`meta[property="${tag.property}"]`);
            if (existing) {
                existing.setAttribute('content', tag.content);
            } else {
                const meta = document.createElement('meta');
                meta.setAttribute('property', tag.property);
                meta.content = tag.content;
                document.head.appendChild(meta);
            }
        });
    }, []);

    return (
        <div className="landing-page bg-white min-h-screen">
            {/* Sticky Navigation Header */}
            <LandingHeader />

            {/* Main Content Sections */}
            <main>
                {/* 1. Hero Section - Above the fold */}
                <HeroSection />

                {/* 2. Trust Layer - Logo Cloud & Stats */}
                <LogoCloud />

                {/* 3. Problem Section - Pain Points */}
                <ProblemSection />

                {/* 4. How It Works - 3 Steps */}
                <HowItWorks />

                {/* 5. Feature Bento Grid - 2x2 */}
                <FeatureBento />

                {/* 6. ROI Calculator - Interactive */}
                <ROICalculator />

                {/* 7. Testimonials - Social Proof */}
                <TestimonialsSection />

                {/* 8. Case Study - Featured Customer */}
                <CaseStudy />

                {/* 9. Founder Story - Human Touch */}
                <FounderStory />
            </main>

            {/* Footer with Final CTA */}
            <LandingFooter />
        </div>
    );
}
