/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      colors: {
        bg0:    "#0d1117",
        bg1:    "#161b22",
        bg2:    "#1c2128",
        border: "#30363d",
        muted:  "#7d8590",
        blue:   "#58a6ff",
        green:  "#3fb950",
        red:    "#f85149",
        purple: "#d2a8ff",
        yellow: "#e3b341",
      },
      backgroundImage: {
        "hero-gradient": "linear-gradient(135deg, #1c2541 0%, #0d1117 50%, #1a1f35 100%)",
      },
    },
  },
  plugins: [],
};
