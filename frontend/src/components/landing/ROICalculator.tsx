/**
 * ROI Calculator Component
 * 
 * Interactive calculator simulating business impact
 */

import { useState, useEffect } from 'react';
import { Card, CardHeader, CardContent } from '../ui/card';
import { Calculator, Zap, Building, Clock, DollarSign } from 'lucide-react';
import { Button } from '../ui/button';
import { roiApi } from '../../services/roiApi';

// ROI Constants
const HOURLY_LABOR_COST = 50.0;
const MANUAL_QUOTE_TIME_MINS = 18;
const SMART_QUOTE_TIME_MINS = 4;
const WEEKS_PER_YEAR = 50;

export function ROICalculator() {
    const [requestsPerYear, setRequestsPerYear] = useState(1000);
    const [numReps, setNumReps] = useState(3);
    const [manualTime, setManualTime] = useState(18);

    const [savings, setSavings] = useState<any>({
        annualSavings: 0,
        revenueUpside: 0,
        hoursPerRepWeek: "0.0"
    });

    // Initial calculation and update on change
    useEffect(() => {
        const calculate = async () => {
            try {
                // Determine average value based on industry standard or input if we had it
                // For now use default
                const result = await roiApi.calculateROI({
                    requestsPerYear,
                    employees: numReps,
                    manualTimeMins: manualTime
                });

                // Calculate hours per rep per week from the total annual hours saved
                const totalHours = result.hours_saved_annually;
                const hoursPerRep = totalHours / numReps / WEEKS_PER_YEAR;

                setSavings({
                    annualSavings: Math.round(result.potential_savings),
                    revenueUpside: Math.round(result.revenue_upside),
                    hoursPerRepWeek: hoursPerRep.toFixed(1)
                });
            } catch (error) {
                console.error("Failed to calculate ROI:", error);
                // Fallback to local calculation if API fails

                const timeSavedMins = requestsPerYear * (manualTime - SMART_QUOTE_TIME_MINS);
                const laborSavings = (timeSavedMins / 60) * HOURLY_LABOR_COST;
                const revenueUpside = laborSavings * 6.5;
                const timeSavedPerRep = (timeSavedMins / 60) / numReps / WEEKS_PER_YEAR;

                setSavings({
                    annualSavings: Math.round(laborSavings),
                    revenueUpside: Math.round(revenueUpside),
                    hoursPerRepWeek: timeSavedPerRep.toFixed(1)
                });
            }
        };

        const timeoutId = setTimeout(calculate, 500); // 500ms debounce
        return () => clearTimeout(timeoutId);
    }, [requestsPerYear, numReps, manualTime]);

    return (
        <section id="roi" className="section-py section-px bg-white tech-grid">
            <div className="landing-container">
                <div className="text-center mb-16">
                    <h2 className="section-headline mb-4">Calculate Your ROI</h2>
                    <p className="section-subline mx-auto">
                        See exactly how much time and money Mercura can save your team.
                    </p>
                </div>

                <div className="grid md:grid-cols-2 gap-12 items-start">
                    {/* Inputs */}
                    <Card className="bento-card border-none shadow-soft-lg p-6">
                        <CardHeader>
                            <h3 className="text-xl font-bold flex items-center gap-2">
                                <Calculator className="h-5 w-5 text-primary" />
                                Input Your Numbers
                            </h3>
                        </CardHeader>
                        <CardContent className="space-y-8">
                            {/* Requests Slider */}
                            <div className="space-y-4">
                                <div className="flex justify-between font-medium">
                                    <label>Annual Quote Requests</label>
                                    <span className="text-primary font-bold">{requestsPerYear.toLocaleString()}</span>
                                </div>
                                <input
                                    type="range"
                                    min="500"
                                    max="10000"
                                    step="100"
                                    value={requestsPerYear}
                                    onChange={(e) => setRequestsPerYear(Number(e.target.value))}
                                    className="roi-slider"
                                />
                                <p className="text-xs text-muted-foreground">Volume of RFQs your team processes annually.</p>
                            </div>

                            {/* Reps Slider */}
                            <div className="space-y-4">
                                <div className="flex justify-between font-medium">
                                    <label>Number of Sales Reps</label>
                                    <span className="text-primary font-bold">{numReps}</span>
                                </div>
                                <input
                                    type="range"
                                    min="1"
                                    max="50"
                                    step="1"
                                    value={numReps}
                                    onChange={(e) => setNumReps(Number(e.target.value))}
                                    className="roi-slider"
                                />
                                <p className="text-xs text-muted-foreground">Size of your inside sales team.</p>
                            </div>

                            {/* Time Slider */}
                            <div className="space-y-4">
                                <div className="flex justify-between font-medium">
                                    <label>Current Time per Quote (mins)</label>
                                    <span className="text-primary font-bold">{manualTime} m</span>
                                </div>
                                <input
                                    type="range"
                                    min="10"
                                    max="60"
                                    step="1"
                                    value={manualTime}
                                    onChange={(e) => setManualTime(Number(e.target.value))}
                                    className="roi-slider"
                                />
                                <p className="text-xs text-muted-foreground">Average time to manually process one request.</p>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Results */}
                    <div className="space-y-6">
                        <div className="bento-card bg-primary text-white p-8 border-none transform md:-translate-y-4 shadow-xl">
                            <div className="flex items-start justify-between mb-8 opacity-90">
                                <Building className="h-8 w-8" />
                                <span className="bg-white/20 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider backdrop-blur-sm">
                                    Projected Impact
                                </span>
                            </div>

                            <div className="space-y-2 mb-8">
                                <div className="text-5xl font-bold tracking-tight">
                                    ${savings.annualSavings.toLocaleString()}
                                </div>
                                <div className="text-lg opacity-90 font-medium">
                                    Annual Labor Savings
                                </div>
                            </div>

                            <div className="pt-8 border-t border-white/20 space-y-2">
                                <div className="text-3xl font-bold tracking-tight opacity-90">
                                    ${savings.revenueUpside.toLocaleString()}
                                </div>
                                <div className="text-sm opacity-75">
                                    Potential Revenue Upside
                                </div>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="bg-slate-50 p-6 rounded-xl border border-slate-100">
                                <Clock className="h-6 w-6 text-blue-500 mb-3" />
                                <div className="text-2xl font-bold text-slate-900 mb-1">
                                    {savings.hoursPerRepWeek} hrs
                                </div>
                                <div className="text-xs text-muted-foreground font-medium">
                                    Saved per rep / week
                                </div>
                            </div>

                            <div className="bg-slate-50 p-6 rounded-xl border border-slate-100">
                                <DollarSign className="h-6 w-6 text-emerald-500 mb-3" />
                                <div className="text-2xl font-bold text-slate-900 mb-1">
                                    {(manualTime / SMART_QUOTE_TIME_MINS).toFixed(1)}x
                                </div>
                                <div className="text-xs text-muted-foreground font-medium">
                                    Faster Turnaround
                                </div>
                            </div>
                        </div>

                        <div className="text-center pt-4">
                            <Button variant="link" className="text-primary hover:text-primary/80" onClick={() => window.location.href = '#demo'}>
                                Get your custom analysis →
                            </Button>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    );
}
