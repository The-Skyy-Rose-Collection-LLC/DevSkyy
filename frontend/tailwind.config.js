/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ['class'],
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './lib/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // SkyyRose brand colors
        brand: {
          primary: '#B76E79',
          secondary: '#1A1A1A',
          accent: '#FFFFFF',
          rose: {
            50: '#fdf2f4',
            100: '#fce7ea',
            200: '#f9d0d7',
            300: '#f4a9b6',
            400: '#ec7a8f',
            500: '#B76E79',
            600: '#c73e5a',
            700: '#a72f47',
            800: '#8c2a3f',
            900: '#77283b',
          },
        },
        // Agent type colors
        agent: {
          commerce: '#10b981',
          creative: '#8b5cf6',
          marketing: '#f59e0b',
          support: '#3b82f6',
          operations: '#ef4444',
          analytics: '#06b6d4',
        },
        // LLM provider colors
        llm: {
          anthropic: '#d97757',
          openai: '#10a37f',
          google: '#4285f4',
          mistral: '#ff7000',
          cohere: '#39594d',
          groq: '#f55036',
        },
      },
      fontFamily: {
        sans: ['var(--font-inter)', 'system-ui', 'sans-serif'],
        mono: ['var(--font-jetbrains-mono)', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 3s linear infinite',
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
      },
      keyframes: {
        'pulse-glow': {
          '0%, 100%': {
            opacity: '1',
            boxShadow: '0 0 10px currentColor',
          },
          '50%': {
            opacity: '0.8',
            boxShadow: '0 0 20px currentColor, 0 0 30px currentColor',
          },
        },
      },
    },
  },
  plugins: [],
};
