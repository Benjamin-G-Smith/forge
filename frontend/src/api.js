const VIEW_TOKEN = typeof window !== "undefined" ? window.__VIEW_TOKEN__ : undefined;

// Dev-only: seed the admin token forge run started the backend with, so
// there's no manual localStorage step just to unblock local development.
// VITE_DEV_ADMIN_TOKEN is only ever set by `forge run`, never by `forge
// build`, so it's never baked into a production bundle.
const DEV_ADMIN_TOKEN = import.meta.env.VITE_DEV_ADMIN_TOKEN;
if (import.meta.env.DEV && DEV_ADMIN_TOKEN && !localStorage.getItem("ADMIN_TOKEN")) {
  localStorage.setItem("ADMIN_TOKEN", DEV_ADMIN_TOKEN);
}

export function isSharedView() {
  return Boolean(VIEW_TOKEN) && !localStorage.getItem("ADMIN_TOKEN");
}

function withViewToken(path) {
  if (!VIEW_TOKEN) return path;
  const separator = path.includes("?") ? "&" : "?";
  return `${path}${separator}v=${VIEW_TOKEN}`;
}

async function request(path, options = {}) {
  const adminToken = localStorage.getItem("ADMIN_TOKEN");
  const headers = { "Content-Type": "application/json", ...options.headers };
  if (adminToken) headers.Authorization = `Bearer ${adminToken}`;

  const res = await fetch(withViewToken(path), { ...options, headers });
  if (!res.ok) throw new Error(`${options.method || "GET"} ${path} failed: ${res.status}`);
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  getDashboard: () => request("/api/dashboard"),
  getBrief: () => request("/api/brief"),
  generateBrief: () => request("/api/brief/generate", { method: "POST" }),
  logSession: (payload) =>
    request("/api/log", { method: "POST", body: JSON.stringify(payload) }),
  updateMetrics: (payload) =>
    request("/api/metrics", { method: "PATCH", body: JSON.stringify(payload) }),
  toggleMilestone: (key, completed) =>
    request(`/api/milestones/${key}`, {
      method: "PATCH",
      body: JSON.stringify({ completed }),
    }),
  getContext: () => request("/api/context"),
  refreshContext: () => request("/api/context/refresh", { method: "POST" }),
  applyContextSnapshot: (id) => request(`/api/context/${id}/apply`, { method: "POST" }),
};
