/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        navy: "#1B365D",
        "navy-light": "#2A4A7A",
        maroon: "#C8102E",
        "maroon-light": "#E33E56",
      },
      fontFamily: {
        sans: ["Inter", "Segoe UI", "system-ui", "sans-serif"],
      },
      boxShadow: {
        glass: "0 8px 32px rgba(27, 54, 93, 0.08)",
        "glass-lg": "0 16px 48px rgba(27, 54, 93, 0.12)",
        glow: "0 0 24px rgba(200, 16, 46, 0.25)",
      },
      animation: {
        shimmer: "shimmer 2.5s linear infinite",
        float: "float 8s ease-in-out infinite",
        "float-slow": "float 12s ease-in-out infinite",
        "gradient-x": "gradient-x 6s ease infinite",
      },
      keyframes: {
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
        float: {
          "0%, 100%": { transform: "translateY(0) translateX(0)" },
          "33%": { transform: "translateY(-24px) translateX(16px)" },
          "66%": { transform: "translateY(12px) translateX(-12px)" },
        },
        "gradient-x": {
          "0%, 100%": { backgroundPosition: "0% 50%" },
          "50%": { backgroundPosition: "100% 50%" },
        },
      },
    },
  },
  plugins: [],
}
