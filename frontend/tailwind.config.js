/** @type {import('tailwindcss').Config} */
const config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["system-ui", "-apple-system", '"Segoe UI"', "sans-serif"],
      },
      colors: {
        // Categorical slots (fixed order, never cycled) — see the dataviz
        // skill's reference palette. Only the slots actually used ship here.
        series: {
          1: "#2a78d6", // blue
          2: "#eb6834", // orange
          3: "#1baf7a", // aqua
          4: "#eda100", // yellow
        },
        ink: {
          primary: "#0b0b0b",
          secondary: "#52514e",
          muted: "#898781",
        },
        surface: {
          card: "#fcfcfb",
          page: "#f9f9f7",
        },
        line: {
          grid: "#e1e0d9",
          axis: "#c3c2b7",
        },
      },
    },
  },
  plugins: [],
};

module.exports = config;
