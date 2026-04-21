import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: "#eef2f6",
        ink: "#17202d",
        panel: "#ffffff",
        line: "#d8e0ea",
        brand: {
          DEFAULT: "#0b4fd9",
          soft: "#e8f0ff",
          strong: "#083a9d",
        },
        success: {
          DEFAULT: "#1f7a53",
          soft: "#eaf7ef",
        },
        warning: {
          DEFAULT: "#a76b00",
          soft: "#fff2d9",
        },
        danger: {
          DEFAULT: "#b02a37",
          soft: "#ffedf0",
        },
        neutral: {
          DEFAULT: "#516173",
          soft: "#eef2f5",
        },
      },
      boxShadow: {
        panel: "0 18px 40px rgba(22, 30, 43, 0.08)",
      },
      borderRadius: {
        panel: "0.75rem",
      },
      fontFamily: {
        sans: ["Aptos", "Segoe UI", "Arial", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
