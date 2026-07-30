import { defineRailway, fn, github, preserve, project, service, volume } from "railway/iac";

export default defineRailway(() => {
  const data = volume("data", { sizeMB: 500, region: "sfo" });

  const source = github("Benjamin-G-Smith/forge", { branch: "main" });
  const build = { builder: "DOCKERFILE" as const, dockerfilePath: "Dockerfile" };

  const web = service("web", {
    source,
    build,
    healthcheck: "/health",
    volumeMounts: { "/data": data },
    env: {
      DB_PATH: "/data/career.db",
      // Pinned rather than left to Railway's dynamic assignment, so
      // morning-brief can reliably reference it for the private-network call.
      PORT: "8000",
      VIEW_TOKEN: preserve(),
      ADMIN_TOKEN: preserve(),
      ANTHROPIC_API_KEY: preserve(),
      TAVILY_API_KEY: preserve(),
    },
  });

  // Railway volumes attach to a single service, so this doesn't touch the
  // SQLite file directly — it calls web's own /api/brief/generate over the
  // private network instead, the same place the "Regenerate" button hits.
  const morningBrief = fn("morning-brief", {
    source,
    build,
    startCommand: "python scripts/trigger_brief.py",
    deploy: { cronSchedule: "0 7 * * *", restartPolicyType: "NEVER" },
    env: {
      WEB_HOST: web.env.RAILWAY_PRIVATE_DOMAIN,
      WEB_PORT: web.env.PORT,
      ADMIN_TOKEN: preserve(),
    },
  });

  return project("forge", { resources: [web, morningBrief, data] });
});
