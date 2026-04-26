export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['Bebas Neue', 'cursive'],
        body: ['DM Sans', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        pitch: {
          950: '#020b06',
          900: '#041a0c',
          800: '#072e15',
          700: '#0a4520',
        },
        goal: {
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
        },
        card: '#0d2318',
        border: '#1a3d28',
      },
    },
  },
  plugins: [],
}
