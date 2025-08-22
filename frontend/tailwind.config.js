'use strict';

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'rose-gold': '#E8B4B8',
        'luxury-gold': '#FFD700',
        'elegant-silver': '#C0C0C0',
        'fashion-black': '#000000',
        'pearl-white': '#FFFFFF',
        'burgundy': '#800020',
        'champagne': '#F7E7CE',
        'platinum': '#E5E4E2'
      },
      fontFamily: {
        'fashion': ['Playfair Display', 'serif'],
        'elegant': ['Inter', 'sans-serif'],
        'luxury': ['Crimson Text', 'serif']
      },
      animation: {
        'fade-in-elegant': 'fadeInElegant 0.8s ease-in-out',
        'slide-in-luxury': 'slideInLuxury 0.6s ease-out',
        'pulse-gold': 'pulseGold 2s ease-in-out infinite',
        'sparkle-success': 'sparkleSuccess 1.5s ease-in-out',
        'float': 'float 3s ease-in-out infinite'
      },
      keyframes: {
        fadeInElegant: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' }
        },
        slideInLuxury: {
          '0%': { opacity: '0', transform: 'translateX(-20px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' }
        },
        pulseGold: {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(255, 215, 0, 0.7)' },
          '50%': { boxShadow: '0 0 0 10px rgba(255, 215, 0, 0)' }
        },
        sparkleSuccess: {
          '0%': { transform: 'scale(1)' },
          '50%': { transform: 'scale(1.1)' },
          '100%': { transform: 'scale(1)' }
        },
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' }
        }
      },
      backgroundImage: {
        'luxury-gradient': 'linear-gradient(135deg, #E8B4B8 0%, #FFD700 50%, #C0C0C0 100%)',
        'rose-gold-gradient': 'linear-gradient(45deg, #E8B4B8 0%, #F7E7CE 100%)',
        'fashion-gradient': 'linear-gradient(to bottom right, #800020, #E8B4B8, #FFD700)'
      },
      boxShadow: {
        'luxury': '0 25px 50px -12px rgba(232, 180, 184, 0.25)',
        'elegant': '0 10px 40px rgba(0, 0, 0, 0.1)',
        'gold-glow': '0 0 30px rgba(255, 215, 0, 0.3)'
      }
    },
  },
  plugins: [],
}