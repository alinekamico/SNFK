/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        kami: {
          red:        '#E2042A',
          'red-light':'#F03554',
          charcoal:   '#463E3F',
          cream:      '#EFEEE8',
        },
      },
      fontFamily: {
        heading: ['Ramabhadra', 'sans-serif'],
        body:    ['Poppins', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
