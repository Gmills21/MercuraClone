/**
 * Testimonials Section - Production Ready
 * 
 * Social proof with customer quotes and stats
 */

import { Quote, Star, TrendingUp, Clock, Building2, Wrench, Zap } from 'lucide-react';
import { motion } from 'framer-motion';

const testimonials = [
    {
        quote: "Mercura allows us to significantly increase productivity in the quotation department. Finding qualified staff is hard—AI ensures technical knowledge is never lost when seniors retire.",
        author: "Maria Schmidt",
        title: "Head of Sales",
        company: "Sanitär-Heinze",
        industry: "Plumbing & HVAC",
        results: [
            { icon: TrendingUp, value: "+30%", label: "Quotes processed" },
            { icon: Clock, value: "75%", label: "Faster turnaround" },
        ],
        image: "MS",
        rating: 5
    },
    {
        quote: "We were skeptical about AI handling our complex product catalog. Within a week, Mercura was matching products faster than our most experienced rep. The ROI was obvious.",
        author: "David Chen",
        title: "VP of Operations",
        company: "Industrial Supply Co.",
        industry: "Industrial Distribution",
        results: [
            { icon: Zap, value: "4x", label: "Quote volume" },
            { icon: Building2, value: "$480k", label: "Annual savings" },
        ],
        image: "DC",
        rating: 5
    },
    {
        quote: "The email automation is a game-changer. RFQs come in and quotes go out without anyone touching a keyboard. Our reps can finally focus on relationship building instead of data entry.",
        author: "Jennifer Walsh",
        title: "Owner",
        company: "Metro HVAC Systems",
        industry: "HVAC Distribution",
        results: [
            { icon: Wrench, value: "-80%", label: "Data entry time" },
            { icon: TrendingUp, value: "+22%", label: "Win rate" },
        ],
        image: "JW",
        rating: 5
    }
];

export function TestimonialsSection() {
    return (
        <section id="testimonials" className="section-py section-px bg-white relative overflow-hidden">
            {/* Background decorations */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_10%_20%,rgba(249,115,22,0.03)_0%,transparent_50%)]" />
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_90%_80%,rgba(59,130,246,0.03)_0%,transparent_50%)]" />

            <div className="landing-container relative">
                {/* Section Header */}
                <div className="text-center mb-16 max-w-3xl mx-auto">
                    <motion.span
                        initial={{ opacity: 0, y: 10 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        className="inline-flex items-center gap-2 text-sm font-semibold text-orange-600 mb-4"
                    >
                        <Star size={16} className="fill-orange-600" />
                        Customer Stories
                    </motion.span>
                    <motion.h2
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        transition={{ delay: 0.1 }}
                        className="section-headline mb-4"
                    >
                        Trusted by 40+ Industrial
                        <br />
                        <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-500 to-red-600">
                            Distributors Nationwide
                        </span>
                    </motion.h2>
                    <motion.p
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        transition={{ delay: 0.2 }}
                        className="text-lg text-slate-600"
                    >
                        See how distributors like yours are transforming their quoting process.
                    </motion.p>
                </div>

                {/* Testimonials Grid */}
                <div className="grid md:grid-cols-3 gap-8">
                    {testimonials.map((testimonial, index) => (
                        <motion.div
                            key={index}
                            initial={{ opacity: 0, y: 30 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true, margin: "-50px" }}
                            transition={{ delay: index * 0.15, duration: 0.5 }}
                            className="group bg-slate-50 rounded-2xl border border-slate-200 overflow-hidden hover:shadow-xl hover:shadow-slate-900/5 hover:border-slate-300 transition-all duration-500"
                        >
                            {/* Quote Content */}
                            <div className="p-6 md:p-8">
                                {/* Rating */}
                                <div className="flex items-center gap-1 mb-4">
                                    {[...Array(testimonial.rating)].map((_, i) => (
                                        <Star key={i} size={16} className="text-orange-400 fill-orange-400" />
                                    ))}
                                </div>

                                {/* Quote */}
                                <div className="relative mb-6">
                                    <Quote size={24} className="text-orange-200 absolute -top-2 -left-2" />
                                    <p className="text-slate-700 leading-relaxed relative z-10 text-sm">
                                        "{testimonial.quote}"
                                    </p>
                                </div>

                                {/* Results */}
                                <div className="grid grid-cols-2 gap-3 mb-6">
                                    {testimonial.results.map((result, i) => (
                                        <div key={i} className="bg-white rounded-lg p-3 border border-slate-100">
                                            <result.icon size={16} className="text-orange-500 mb-1" />
                                            <p className="text-lg font-bold text-slate-900">{result.value}</p>
                                            <p className="text-[10px] text-slate-500 uppercase tracking-wider">{result.label}</p>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Author */}
                            <div className="px-6 md:px-8 py-4 bg-white border-t border-slate-100">
                                <div className="flex items-center gap-3">
                                    <div className="w-12 h-12 rounded-full bg-gradient-to-br from-orange-100 to-orange-50 flex items-center justify-center text-orange-600 font-bold text-sm border-2 border-white shadow-sm">
                                        {testimonial.image}
                                    </div>
                                    <div>
                                        <p className="font-semibold text-slate-900">{testimonial.author}</p>
                                        <p className="text-xs text-slate-500">{testimonial.title}</p>
                                        <p className="text-[10px] text-orange-600 font-medium mt-0.5">{testimonial.company}</p>
                                    </div>
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </div>

                {/* Stats Bar */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    className="mt-16 bg-slate-900 rounded-2xl p-8 md:p-12"
                >
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
                        {[
                            { value: "40+", label: "Distributors", sublabel: "Across the US & Canada" },
                            { value: "$2.4B", label: "Quotes Processed", sublabel: "Annual volume" },
                            { value: "98%", label: "Customer Satisfaction", sublabel: "NPS Score: 72" },
                            { value: "125k+", label: "Hours Saved", sublabel: "Per year" },
                        ].map((stat, i) => (
                            <div key={i} className="space-y-2">
                                <p className="text-3xl md:text-4xl font-bold text-white">{stat.value}</p>
                                <p className="text-sm font-medium text-slate-300">{stat.label}</p>
                                <p className="text-xs text-slate-500">{stat.sublabel}</p>
                            </div>
                        ))}
                    </div>
                </motion.div>

                {/* Logo Cloud */}
                <motion.div
                    initial={{ opacity: 0 }}
                    whileInView={{ opacity: 1 }}
                    viewport={{ once: true }}
                    className="mt-16 text-center"
                >
                    <p className="text-sm text-slate-400 mb-8 uppercase tracking-wider font-medium">Trusted by industry leaders</p>
                    <div className="flex flex-wrap justify-center items-center gap-8 md:gap-12 opacity-60">
                        {['HVAC Supply Co.', 'Plumbing Plus', 'Industrial Direct', 'Metro Electric', 'Commercial Systems', 'Building Supply'].map((logo, i) => (
                            <div key={i} className="flex items-center gap-2 text-slate-400">
                                <Building2 size={20} />
                                <span className="font-semibold text-sm">{logo}</span>
                            </div>
                        ))}
                    </div>
                </motion.div>
            </div>
        </section>
    );
}
