/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        dark: {
          900: '#0f172a',
          800: '#1e1b4b',
          950: '#020617',
        },
        neon: {
          cyan: '#06b6d4',
          magenta: '#d946ef',
          amber: '#f59e0b',
        },
        // Keep primary for backward compatibility if needed, or update to match neon theme
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#06b6d4', // Updated to neon cyan
          600: '#0891b2',
          700: '#0e7490',
          800: '#155e75',
          900: '#164e63',
        },
      },
      fontFamily: {
        sans: ['Outfit', 'Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'neon-cyan': '0 0 15px rgba(6, 182, 212, 0.5)',
        'neon-magenta': '0 0 15px rgba(217, 70, 239, 0.5)',
        'neon-amber': '0 0 15px rgba(245, 158, 11, 0.5)',
      },
    },
  },
  plugins: [],
}
