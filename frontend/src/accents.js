export const ACCENTS = {
  blue: { bg: "bg-accent-blue-bg", text: "text-accent-blue-text", solid: "bg-accent-blue-solid" },
  coral: { bg: "bg-accent-coral-bg", text: "text-accent-coral-text", solid: "bg-accent-coral-solid" },
  teal: { bg: "bg-accent-teal-bg", text: "text-accent-teal-text", solid: "bg-accent-teal-solid" },
  purple: { bg: "bg-accent-purple-bg", text: "text-accent-purple-text", solid: "bg-accent-purple-solid" },
};

export function accentOf(key) {
  return ACCENTS[key] || ACCENTS.blue;
}

export function relativeTime(ms) {
  if (!ms) return "";
  const days = Math.floor((Date.now() - ms) / 86400000);
  if (days <= 0) return "Active today";
  if (days === 1) return "Yesterday";
  return `${days} days ago`;
}
