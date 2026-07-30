const VIEW_TOKEN = typeof window !== "undefined" ? window.__VIEW_TOKEN__ : undefined;

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
};
