/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        aegis: {
          bg: "#070a13",
          surface: "#0e1526",
          card: "rgba(16, 24, 44, 0.75)",
          border: "#1e293b",
          cyan: "#00f0ff",
          purple: "#8b5cf6",
          benign: "#10b981",
          elevated: "#f59e0b",
          critical: "#ef4444",
        }
      },
      fontFamily: {
        mono: ['"JetBrains Mono"', 'monospace'],
        sans: ['Inter', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
