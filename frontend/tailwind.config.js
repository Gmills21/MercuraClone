/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
        "./components/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: {
                    50: '#f8fafc',
                    100: '#f1f5f9',
                    200: '#e2e8f0',
                    300: '#cbd5e1',
                    400: '#94a3b8',
                    500: '#64748b', // Zinc-inspired, professional
                    600: '#475569',
                    700: '#334155',
                    800: '#1e293b',
                    900: '#0f172a',
                },
                zinc: {
                    50: '#fafafa',
                    100: '#f4f4f5',
                    200: '#e4e4e7',
                    300: '#d4d4d8',
                    400: '#a1a1aa',
                    500: '#71717a',
                    600: '#52525b',
                    700: '#3f3f46',
                    800: '#27272a',
                    900: '#18181b',
                },
                accent: {
                    500: '#22d3ee', // Cyan accent for highlights
                },
                background: '#0f172a',
                foreground: '#f8fafc',
                muted: '#1e293b',
                border: '#334155',
            },
            fontFamily: {
                sans: ['Inter', 'Segoe UI', 'sans-serif'],
                display: ['Poppins', 'Inter', 'Segoe UI', 'sans-serif'],
            },
            borderRadius: {
                lg: '1rem',
                xl: '1.5rem',
            },
            boxShadow: {
                card: '0 4px 32px 0 rgba(16, 30, 54, 0.10)',
                b2b: '0 2px 8px 0 rgba(40, 60, 90, 0.08)',
            },
            animation: {
                'fade-in': 'fadeIn 0.5s ease-out',
                'slide-up': 'slideUp 0.5s ease-out',
            },
            keyframes: {
                fadeIn: {
                    '0%': { opacity: '0' },
                    '100%': { opacity: '1' },
                },
                slideUp: {
                    '0%': { transform: 'translateY(20px)', opacity: '0' },
                    '100%': { transform: 'translateY(0)', opacity: '1' },
                }
            }
        },
    },
    plugins: [],
}
