/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        bg: "#0d1117",
        surface: "#161b22",
        border: "#21262d",
        text: "#e6edf3",
        muted: "#7d8590",
        accent: "#3fb950",
      },
      fontFamily: {
        mono: ["Space Mono", "ui-monospace", "monospace"],
        sans: ["Space Grotesk", "-apple-system", "sans-serif"],
      },
    },
  },
  plugins: [],
};
