/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Manrope', 'Segoe UI', 'sans-serif'],
        display: ['Newsreader', 'Georgia', 'serif'],
      },
      colors: {
        ink: {
          50: '#f6f7fb',
          100: '#ebedf4',
          200: '#d8ddea',
          300: '#afb8d1',
          400: '#7d8aa9',
          500: '#5c6781',
          600: '#444d65',
          700: '#30384d',
          800: '#1d2435',
          900: '#101624',
        },
        accent: {
          50: '#eef4ff',
          100: '#dbe8ff',
          200: '#bfd5ff',
          300: '#95b8ff',
          400: '#6796ff',
          500: '#426ff7',
          600: '#3056d6',
          700: '#2643a8',
          800: '#233987',
          900: '#223369',
        },
      },
      boxShadow: {
        panel: '0 14px 40px -26px rgba(16, 22, 36, 0.28)',
      },
      backgroundImage: {
        grain:
          'radial-gradient(circle at top left, rgba(66, 111, 247, 0.08), transparent 28%), radial-gradient(circle at bottom right, rgba(16, 22, 36, 0.08), transparent 24%)',
      },
    },
  },
  plugins: [],
};
