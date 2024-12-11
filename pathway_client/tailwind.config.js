/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        bluecolor: "#191E96",
        pinkcolor: "#C5198D",
        graycolor: "#F5F5F5",
        blackcolor: "#33363F",
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
};
