/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/**/*.js"
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#000080', // Navy
          light: '#0000A0',
        },
        contrast: {
          DEFAULT: '#FFFFFF', // White
        }
      }
    },
  },
  plugins: [],
}
