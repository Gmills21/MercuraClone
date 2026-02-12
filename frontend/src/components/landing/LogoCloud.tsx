/**
 * Logo Cloud Component
 * 
 * Trust layer showing customer logos
 */

export function LogoCloud() {
    // Placeholder logos - will be replaced with actual customer logos
    const logos = [
        { name: 'HVAC Distributor 1', placeholder: 'H1' },
        { name: 'Plumbing Supplier 1', placeholder: 'P1' },
        { name: 'Electrical Wholesaler 1', placeholder: 'E1' },
        { name: 'Manufacturing Partner 1', placeholder: 'M1' },
        { name: 'HVAC Distributor 2', placeholder: 'H2' },
        { name: 'Plumbing Supplier 2', placeholder: 'P2' },
    ];

    return (
        <section className="py-16 border-y border-minimal">
            <div className="landing-container section-px">
                <div className="text-center space-y-8">
                    <p className="text-muted-foreground text-sm md:text-base">
                        40+ industrial distributors trust Mercura
                    </p>

                    <div className="logo-cloud">
                        {logos.map((logo, index) => (
                            <div
                                key={index}
                                className="w-24 h-12 bg-slate-200 rounded flex items-center justify-center"
                            >
                                <span className="text-slate-400 font-semibold text-sm">
                                    {logo.placeholder}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </section>
    );
}
