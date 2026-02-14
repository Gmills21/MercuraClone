/**
 * ROI Calculator Component - Production Ready
 * 
 * Interactive calculator with polished UI and realistic projections
 */

import { useState, useEffect, useMemo } from 'react';
import { Calculator, Building, Clock, DollarSign, TrendingUp, Users, ArrowRight, Sparkles, CheckCircle } from 'lucide-react';
import { Button } from '../ui/button';
import { motion, AnimatePresence } from 'framer-motion';

// Constants for calculations
const HOURLY_LABOR_COST = 55;
const MANUAL_QUOTE_TIME_MINS = 18;
const SMART_QUOTE_TIME_MINS = 3;
const WEEKS_PER_YEAR = 50;
const REVENUE_MULTIPLIER = 6.5;

interface ROISliderProps {
    label: string;
    value: number;
    min: number;
    max: number;
    step: number;
    onChange: (value: number) => void;
    format?: (value: number) => string;
    description?: string;
}

const ROISlider = ({ label, value, min, max, step, onChange, format, description }: ROISliderProps) => {
    const percentage = ((value - min) / (max - min)) * 100;
    
    return (
        <div className="space-y-3">
            <div className="flex justify-between items-center">
                <label className="text-sm font-semibold text-slate-700">{label}</label>
                <span className="text-lg font-bold text-slate-900">{format ? format(value) : value}</span>
            </div>
            {description && <p className="text-xs text-slate-500">{description}</p>}
            <div className="relative h-2 bg-slate-100 rounded-full overflow-hidden">
                <div 
                    className="absolute inset-y-0 left-0 bg-gradient-to-r from-orange-500 to-red-500 rounded-full transition-all duration-150"
                    style={{ width: `${percentage}%` }}
                />
                <input
                    type="range"
                    min={min}
                    max={max}
                    step={step}
                    value={value}
                    onChange={(e) => onChange(Number(e.target.value))}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
            </div>
            <div className="flex justify-between text-xs text-slate-400">
                <span>{format ? format(min) : min}</span>
                <span>{format ? format(max) : max}</span>
            </div>
        </div>
    );
};

const StatCard = ({ icon: Icon, value, label, subtext, color }: { icon: any, value: string, label: string, subtext?: string, color: string }) => (
    <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm"
    >
        <div className={`w-10 h-10 rounded-lg ${color} flex items-center justify-center mb-3`}>
            <Icon size={20} className="text-white" />
        </div>
        <div className="text-2xl font-bold text-slate-900 mb-1">{value}</div>
        <div className="text-sm font-medium text-slate-600">{label}</div>
        {subtext && <div className="text-xs text-slate-400 mt-1">{subtext}</div>}
    </motion.div>
);

export function ROICalculator() {
    const [requestsPerYear, setRequestsPerYear] = useState(2500);
    const [numReps, setNumReps] = useState(5);
    const [avgDealSize, setAvgDealSize] = useState(15000);
    const [currentWinRate, setCurrentWinRate] = useState(25);

    // Calculate savings
    const calculations = useMemo(() => {
        const timeSavedPerQuote = MANUAL_QUOTE_TIME_MINS - SMART_QUOTE_TIME_MINS;
        const totalMinutesSaved = requestsPerYear * timeSavedPerQuote;
        const totalHoursSaved = totalMinutesSaved / 60;
        const laborSavings = totalHoursSaved * HOURLY_LABOR_COST;
        
        // Hours per rep per week
        const hoursPerRep = totalHoursSaved / numReps / WEEKS_PER_YEAR;
        
        // Revenue upside: faster quotes = more quotes sent = more wins
        const additionalCapacity = Math.floor(totalHoursSaved / (MANUAL_QUOTE_TIME_MINS / 60));
        const additionalWins = Math.floor(additionalCapacity * (currentWinRate / 100));
        const revenueUpside = additionalWins * avgDealSize;
        
        // Total ROI
        const annualBenefit = laborSavings + (revenueUpside * 0.3); // Conservative 30% of upside
        const roi = ((annualBenefit - 12000) / 12000) * 100; // Assuming $12k/year cost
        
        return {
            laborSavings: Math.round(laborSavings),
            revenueUpside: Math.round(revenueUpside),
            hoursPerRepWeek: hoursPerRep.toFixed(1),
            totalHoursSaved: Math.round(totalHoursSaved),
            additionalQuotes: additionalCapacity,
            speedIncrease: (MANUAL_QUOTE_TIME_MINS / SMART_QUOTE_TIME_MINS).toFixed(0),
            annualBenefit: Math.round(annualBenefit),
            roi: Math.round(roi)
        };
    }, [requestsPerYear, numReps, avgDealSize, currentWinRate]);

    return (
        <section id="roi" className="section-py section-px bg-slate-50 relative overflow-hidden">
            {/* Background decoration */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_30%,rgba(249,115,22,0.05)_0%,transparent_50%)]" />
            
            <div className="landing-container relative">
                {/* Section Header */}
                <div className="text-center mb-12 max-w-3xl mx-auto">
                    <motion.span
                        initial={{ opacity: 0, y: 10 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="inline-flex items-center gap-2 text-sm font-semibold text-orange-600 mb-4"
                    >
                        <Calculator size={16} />
                        ROI Calculator
                    </motion.span>
                    <motion.h2
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        transition={{ delay: 0.1 }}
                        className="section-headline mb-4"
                    >
                        Calculate Your
                        <br />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-500 to-red-600">
                            Annual Savings
                        </span>
                    </motion.h2>
                    <motion.p
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        transition={{ delay: 0.2 }}
                        className="text-lg text-slate-600"
                    >
                        See exactly how much time and money Mercura can save your team with our interactive calculator.
                    </motion.p>
                </div>

                <div className="grid lg:grid-cols-5 gap-8">
                    {/* Inputs Panel */}
                    <motion.div
                        initial={{ opacity: 0, x: -30 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                        className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-lg p-6 space-y-8"
                    >
                        <div className="flex items-center gap-3 pb-4 border-b border-slate-100">
                            <div className="w-10 h-10 rounded-xl bg-slate-900 flex items-center justify-center">
                                <Building size={20} className="text-white" />
                            </div>
                            <div>
                                <h3 className="font-bold text-slate-900">Your Business</h3>
                                <p className="text-xs text-slate-500">Adjust the sliders to match your operation</p>
                            </div>
                        </div>

                        <ROISlider
                            label="Annual Quote Requests"
                            value={requestsPerYear}
                            min={500}
                            max={10000}
                            step={100}
                            onChange={setRequestsPerYear}
                            format={(v) => v.toLocaleString()}
                            description="Total RFQs your team processes each year"
                        />

                        <ROISlider
                            label="Inside Sales Reps"
                            value={numReps}
                            min={1}
                            max={50}
                            step={1}
                            onChange={setNumReps}
                            description="Number of reps handling quotes"
                        />

                        <ROISlider
                            label="Average Deal Size"
                            value={avgDealSize}
                            min={5000}
                            max={100000}
                            step={1000}
                            onChange={setAvgDealSize}
                            format={(v) => `$${(v/1000).toFixed(0)}k`}
                            description="Typical quote value in dollars"
                        />

                        <ROISlider
                            label="Current Win Rate"
                            value={currentWinRate}
                            min={10}
                            max={60}
                            step={1}
                            onChange={setCurrentWinRate}
                            format={(v) => `${v}%`}
                            description="Percentage of quotes that convert to orders"
                        />
                    </motion.div>

                    {/* Results Panel */}
                    <motion.div
                        initial={{ opacity: 0, x: 30 }}
                        whileInView={{ opacity: 1, x: 0 }}
                        viewport={{ once: true }}
                        className="lg:col-span-3 space-y-6"
                    >
                        {/* Primary Savings Card */}
                        <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl p-8 text-white shadow-xl relative overflow-hidden">
                            {/* Decorative elements */}
                            <div className="absolute top-0 right-0 w-64 h-64 bg-orange-500/10 rounded-full blur-[60px]" />
                            <div className="absolute bottom-0 left-0 w-48 h-48 bg-blue-500/10 rounded-full blur-[40px]" />
                            
                            <div className="relative z-10">
                                <div className="flex items-center justify-between mb-6">
                                    <div className="flex items-center gap-3">
                                        <div className="w-12 h-12 rounded-xl bg-white/10 backdrop-blur flex items-center justify-center">
                                            <TrendingUp size={24} className="text-orange-400" />
                                        </div>
                                        <div>
                                            <p className="text-sm font-medium text-white/60">Projected Annual Savings</p>
                                            <p className="text-xs text-white/40">Based on industry averages</p>
                                        </div>
                                    </div>
                                    <span className="bg-white/10 backdrop-blur px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider">
                                        Estimated Impact
                                    </span>
                                </div>

                                <AnimatePresence mode="wait">
                                    <motion.div
                                        key={calculations.annualBenefit}
                                        initial={{ opacity: 0, scale: 0.95 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        exit={{ opacity: 0, scale: 0.95 }}
                                        transition={{ duration: 0.2 }}
                                    >
                                        <div className="text-6xl md:text-7xl font-bold tracking-tight mb-2">
                                            ${calculations.annualBenefit.toLocaleString()}
                                        </div>
                                        <div className="flex items-center gap-2 text-white/70">
                                            <Sparkles size={16} className="text-orange-400" />
                                            <span className="text-lg">
                                                {calculations.roi}% ROI in year one
                                            </span>
                                        </div>
                                    </motion.div>
                                </AnimatePresence>

                                <div className="mt-8 pt-8 border-t border-white/10 grid grid-cols-2 gap-6">
                                    <div>
                                        <div className="flex items-center gap-2 mb-1">
                                            <DollarSign size={16} className="text-green-400" />
                                            <span className="text-sm text-white/60">Labor Savings</span>
                                        </div>
                                        <p className="text-2xl font-bold">${calculations.laborSavings.toLocaleString()}</p>
                                    </div>
                                    <div>
                                        <div className="flex items-center gap-2 mb-1">
                                            <TrendingUp size={16} className="text-blue-400" />
                                            <span className="text-sm text-white/60">Revenue Upside</span>
                                        </div>
                                        <p className="text-2xl font-bold">${calculations.revenueUpside.toLocaleString()}</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Secondary Stats Grid */}
                        <div className="grid sm:grid-cols-3 gap-4">
                            <StatCard
                                icon={Clock}
                                value={`${calculations.hoursPerRepWeek}h`}
                                label="Per Rep / Week"
                                subtext="Time saved on quoting"
                                color="bg-blue-500"
                            />
                            <StatCard
                                icon={TrendingUp}
                                value={`${calculations.speedIncrease}x`}
                                label="Faster Turnaround"
                                subtext="Quote-to-send time"
                                color="bg-orange-500"
                            />
                            <StatCard
                                icon={Users}
                                value={calculations.additionalQuotes.toLocaleString()}
                                label="Additional Quotes"
                                subtext="Extra capacity per year"
                                color="bg-emerald-500"
                            />
                        </div>

                        {/* CTA */}
                        <div className="bg-white rounded-xl border border-slate-200 p-6 flex flex-col sm:flex-row items-center justify-between gap-4">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                                    <CheckCircle size={20} className="text-green-600" />
                                </div>
                                <div>
                                    <p className="font-semibold text-slate-900">Want a detailed breakdown?</p>
                                    <p className="text-sm text-slate-500">Get a custom ROI report for your business</p>
                                </div>
                            </div>
                            <Button 
                                className="bg-slate-900 hover:bg-slate-800 text-white px-6 py-3 rounded-xl font-semibold shadow-lg shadow-slate-900/20 whitespace-nowrap"
                                onClick={() => window.location.href = '#demo'}
                            >
                                Get Full Report
                                <ArrowRight size={16} className="ml-2" />
                            </Button>
                        </div>
                    </motion.div>
                </div>

                {/* Trust indicators */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-6 text-center"
                >
                    {[
                        { value: '$240k', label: 'Customer savings (beta)' },
                        { value: '12k+', label: 'Hours saved annually' },
                        { value: '3x', label: 'Average productivity gain' },
                        { value: '40+', label: 'Active beta users' },
                    ].map((stat, i) => (
                        <div key={i} className="p-4">
                            <p className="text-2xl md:text-3xl font-bold text-slate-900">{stat.value}</p>
                            <p className="text-sm text-slate-500 mt-1">{stat.label}</p>
                        </div>
                    ))}
                </motion.div>
            </div>
        </section>
    );
}
