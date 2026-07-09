/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#fff1f2',
          100: '#ffe4e6',
          400: '#fb7185',
          500: '#e11d48',
          600: '#be123c',
          700: '#9f1239', // Maroon
          800: '#881337', // Darker Maroon
          900: '#4c0519', // Very dark maroon
        },
        surface: {
          900: '#fcf6f5', // Pale peach background
          800: '#fdf8f6', // Inputs / alternate background
          700: '#ffffff', // White cards
          600: '#f7ece9', 
          500: '#f4e4e0', 
          400: '#d7c2bc', 
          300: '#b89f98',
          200: '#7a5a52', 
          100: '#4a3029', 
        },
        accent: {
          cyan: '#06b6d4',
          teal: '#14b8a6',
          emerald: '#10b981',
          amber: '#f59e0b',
          rose: '#f43f5e',
          violet: '#8b5cf6',
        },
      },
      fontFamily: {
        sans: ['Roboto', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'glass': 'linear-gradient(135deg, rgba(255,255,255,0.9) 0%, rgba(255,255,255,0.6) 100%)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-in': 'slideIn 0.3s ease-out',
      },
      keyframes: {
        fadeIn: { from: { opacity: '0' }, to: { opacity: '1' } },
        slideIn: { from: { transform: 'translateY(10px)', opacity: '0' }, to: { transform: 'translateY(0)', opacity: '1' } },
      },
    },
  },
  plugins: [],
}
