import type { Config } from "tailwindcss";

const config: Config = {
  // Enable class-based dark mode
  darkMode: "class",

  // Configure files to scan for Tailwind classes
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./hooks/**/*.{js,ts,jsx,tsx}",
    "./utils/**/*.{js,ts,jsx,tsx}",
  ],

  // Extend the default theme with custom healthcare colors
  theme: {
    extend: {
      colors: {
        // Primary color palette (professional blue)
        primary: {
          light: "#E6F0FF", // Lightest shade for backgrounds
          DEFAULT: "#0066FF", // Main brand color
          dark: "#0044CC",   // Darker shade for hover/active states
        },
        // Secondary color palette (calming green)
        secondary: {
          light: "#E3F9F0",
          DEFAULT: "#1ABC9C",
          dark: "#16A085",
        },
        // Accent color for highlights and CTAs
        accent: {
          light: "#FFF4E6",
          DEFAULT: "#F39C12",
          dark: "#E67E22",
        },
        // Neutral colors for text, backgrounds, and borders
        neutral: {
          100: "#F8F9FA", // Light background
          200: "#E9ECEF", // Borders
          300: "#DEE2E6",
          400: "#CED4DA",
          500: "#ADB5BD",
          600: "#6C757D", // Secondary text
          700: "#495057",
          800: "#343A40", // Primary text
          900: "#212529",
        },
        // Status colors
        success: "#28A745",
        warning: "#FFC107",
        danger: "#DC3545",
      },
      backgroundImage: {
        "gradient-radial": "radial-gradient(var(--tw-gradient-stops))",
        "gradient-conic":
          "conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))",
      },
    },
  },

  // No plugins needed for the base setup
  plugins: [],
};

export default config;
