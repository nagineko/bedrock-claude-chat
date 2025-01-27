/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    fontFamily: {
      body: ['M PLUS Rounded 1c'],
    },
    extend: {
      transitionProperty: {
        width: 'width',
        height: 'height',
      },
      animation: {
        fastPulse: 'pulse 0.5s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      colors: {
        'aws-white': {
          DEFAULT: '#ffffff',
          smoke: '#f1f3f3',
          silver: '#ececec',
        },
        'aws-red': {
          DEFAULT: '#dc2626',
        },
        'aws-yellow': {
          DEFAULT: '#f59e0b',
        },
        'aws-blue': {
          DEFAULT: '#005276',
          deepteal: '#003550',
          cerulean: '#007faa',
          navy: '#232F3E',
          cobalt: '#276cc6',
        },
        'aws-gray': {
          DEFAULT: '#757575',
          slate: '#5b5b5b',
          grayish: '#6b7280',
          ash: '#909193',
          french: '#9ca3af',
          light: '#cacaca',
          ice: '#e5e7eb',
        },
        'aws-black': {
          DEFAULT: '#000000',
          jet: '#151515',
          smoke: '#171717',
          graphite: '#212121',
        },
      },
    },
  },
  // eslint-disable-next-line no-undef
  plugins: [require('@tailwindcss/typography'), require('tailwind-scrollbar')],
};
