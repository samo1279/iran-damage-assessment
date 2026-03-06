/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#0d1117',
        card: '#161b22',
        border: '#30363d',
        dim: '#8b949e',
        accent: '#58a6ff',
        danger: '#f85149',
        success: '#3fb950',
        warning: '#d29922',
        purple: '#bc8cff',
        cyan: '#39d2c0',
      },
    },
  },
  plugins: [],
}
