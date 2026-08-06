/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
      },
      colors: {
        bg: "#F7F7F5",
        surface: "#FFFFFF",
        "surface-tint": "#FAFAF8",
        line: {
          DEFAULT: "#E7E5E0",
          strong: "#D6D3CB",
        },
        ink: {
          primary: "#1C1B18",
          secondary: "#6B6862",
          muted: "#9C988F",
        },
        // Namespaced under "accent" (not bare "blue"/"teal"/"purple") so this
        // doesn't clobber Tailwind's default palette shades — kept components
        // like ShareBadge/MorningBrief still use bg-blue-100, ring-blue-500, etc.
        accent: {
          blue: { bg: "#EAF2FC", text: "#1D4E89", solid: "#3378C4" },
          coral: { bg: "#FBEAE7", text: "#9C4A2E", solid: "#D2653F" },
          teal: { bg: "#E6F5F1", text: "#1F6F5C", solid: "#2F9C82" },
          purple: { bg: "#F1EEFB", text: "#5A4B96", solid: "#7C6BC4" },
        },
        "green-solid": "#4C9A5B",
      },
      borderRadius: {
        lg: "16px",
        md: "10px",
      },
    },
  },
  plugins: [],
};
