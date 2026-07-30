# Forge — PRD

## Problem Statement

Benjamin is pivoting from a C#/.NET developer role (~$99K) to an AI engineer role ($143K–$220K target) by June 2027. The pivot requires consistent daily effort across Python practice, project building, research, and job applications — but without a visible scoreboard, motivation degrades and progress becomes invisible. The existing Cowork artifact is a good start but is tied to the Claude ecosystem and can't be shared with hiring managers or used as a portfolio piece. The gap: a beautiful, deployed, shareable app that tracks progress, generates an LLM-powered morning brief, and demonstrates real AI engineering skills to employers.

---

## Solution Overview

A deployed web application with a FastAPI backend, React + Tailwind frontend, and SQLite data layer. The app serves as both a personal productivity tool and a live portfolio piece. A LangChain chain reads yesterday's session log, runs targeted Tavily searches based on the work type, and generates a focused morning brief via the Claude (or Gemini) API. The app is publicly accessible via a shareable link token — anyone with the link sees the full dashboard including the heatmap, stage progress, milestones, and morning brief.

**Stack:**
- Backend: Python 3.11 + FastAPI
- Frontend: React 18 + Tailwind CSS + Vite
- Database: SQLite (via SQLModel / SQLAlchemy)
- LLM chain: LangChain + Tavily search + Anthropic Claude (Haiku 3.5) or Gemini 1.5 Flash (free tier)
- Deployment: Railway (app + scheduled brief generation at 7am daily via a second cron-scheduled service)
- Auth: Single static `VIEW_TOKEN` in URL query param for shared access; `ADMIN_TOKEN` env var for write operations

---

## Deep Module Architecture

### `api/` — FastAPI Backend

**Routes:**
- `GET /api/dashboard` → returns full dashboard payload (metrics, log, milestones, stage progress, latest brief)
- `POST /api/log` → create a session log entry (admin only)
- `PATCH /api/metrics` → update projects_shipped, applications_sent, stages_complete (admin only)
- `PATCH /api/milestones/{key}` → toggle a milestone boolean (admin only)
- `GET /api/brief` → return the latest generated brief
- `POST /api/brief/generate` → trigger on-demand brief generation (admin only)
- `GET /` → serve React frontend (index.html)

**Auth middleware:**
- Read routes: check `?v=VIEW_TOKEN` query param or `Authorization: Bearer ADMIN_TOKEN` header
- Write routes: require `ADMIN_TOKEN` header only
- Both tokens set as Railway variables (env vars)

**Internal dependencies:** SQLite via SQLModel, LangChain chain (brief only)

---

### `db/` — SQLite Schema

**`sessions` table**
```
id          INTEGER PRIMARY KEY
date        TEXT NOT NULL          -- YYYY-MM-DD
type        TEXT NOT NULL          -- JSON array: ["python", "project"]
notes       TEXT
commits     INTEGER DEFAULT 0
level       INTEGER NOT NULL       -- 1 | 2 | 3
created_at  INTEGER                -- unix ms
```

**`metrics` table**
```
id                  INTEGER PRIMARY KEY
projects_shipped    INTEGER DEFAULT 0
applications_sent   INTEGER DEFAULT 0
stages_complete     INTEGER DEFAULT 0
updated_at          INTEGER
```

**`milestones` table**
```
key           TEXT PRIMARY KEY
completed     BOOLEAN DEFAULT FALSE
completed_at  INTEGER
```

**`briefs` table**
```
id            INTEGER PRIMARY KEY
date          TEXT NOT NULL          -- YYYY-MM-DD
summary       TEXT                   -- 1-2 sentence yesterday recap
focus         TEXT                   -- today's recommended focus
research      TEXT                   -- JSON array of {title, url, reason}
generated_at  INTEGER
```

---

### `chain/` — LangChain Morning Brief

**Input:** Yesterday's session log entry (date, type, notes, level)

**Steps:**
1. **Classify** — map session type + notes to 2–3 search queries (e.g., `["python langchain tutorial 2026", "LangGraph agent patterns"]`)
2. **Search** — `TavilySearchResults(max_results=3)` per query, deduplicate
3. **Generate** — prompt Claude/Gemini with: yesterday's log + search results + roadmap position → produce JSON with `summary`, `focus`, `research[]`
4. **Persist** — write to `briefs` table

**Output shape:**
```json
{
  "summary": "Yesterday: solid Python session working through LangChain tool use patterns.",
  "focus": "Build the FastAPI /log endpoint end-to-end today — get one route working with a test.",
  "research": [
    { "title": "LangChain Tool Use in 2026", "url": "...", "reason": "Directly relevant to what you built yesterday" }
  ]
}
```

**Public interface:** `generate_brief(session: Session) -> Brief`
**Internal deps:** LangChain, TavilySearchResults, ChatAnthropic (or ChatGoogleGenerativeAI)

---

### `scripts/migrate.py` — One-Time Data Import

Reads `/Users/bensmith/Documents/ember-vault/_system/career-metrics.json` and seeds SQLite:
- `log[]` entries → `sessions` table
- `metrics` → `metrics` table
- `milestones` → `milestones` table

Run once on first deploy. Idempotent (skip entries that already exist by date).

---

### `frontend/` — React + Tailwind

**Components:**
- `MorningBrief` — top panel: summary sentence, focus recommendation, 2–3 research links with reason tags
- `Heatmap` — 26-week × 7-day GitHub-style grid, colored by session level (0–3), today outlined
- `MetricsRow` — 4 cards: streak, projects shipped, stages complete, applications sent
- `StageTrack` — 5-stage roadmap with connector lines, click to toggle done/active
- `Milestones` — checklist with badge labels (now / sept / dec)
- `LogSession` — form: type selector, notes textarea, intensity picker (Light / Solid / Deep), submit
- `ShareBadge` — small indicator shown on shared-link views (read-only mode, no log form)

**API layer:** `src/api.js` — single fetch wrapper that appends `?v=VIEW_TOKEN` to all requests when in shared-link mode

---

## User Stories & Acceptance Criteria

- [ ] **US-01:** As Benjamin, I want to log a session so my activity appears in the heatmap.
  - The session is saved to SQLite with date, type, notes, level
  - The heatmap cell for today updates without a full page reload
  - Requires admin token; fails gracefully on shared-link views

- [ ] **US-02:** As Benjamin, I want to open the app each morning and see a pre-generated brief so I start focused without waiting.
  - A brief is auto-generated nightly at 7am via a cron-scheduled Railway service
  - The brief shows: yesterday's recap, today's focus, 2–3 research links with reasons
  - If no session was logged yesterday, the brief falls back to roadmap position + general research

- [ ] **US-03:** As Benjamin, I want to regenerate the brief on demand so I can refresh it mid-day.
  - A "Regenerate" button triggers `POST /api/brief/generate`
  - The new brief replaces the old one in the UI within ~15 seconds
  - Button is disabled and shows a spinner during generation

- [ ] **US-04:** As a hiring manager, I want to view Benjamin's full dashboard via a shared link so I can assess his consistency and progress.
  - The link works with `?v=VIEW_TOKEN` appended
  - Full dashboard is visible: heatmap, metrics, stages, milestones, brief
  - Log session form is hidden in shared-link view
  - No login required

- [ ] **US-05:** As Benjamin, I want my existing career-metrics.json data imported into SQLite so I don't lose history.
  - `python scripts/migrate.py` runs successfully
  - Existing sessions, metrics, and milestones appear correctly in the dashboard
  - Re-running the script does not create duplicate entries

---

## Explicitly Out of Scope

- Per-person invite link management (revoke individual viewers) — v2
- Email/calendar integration in the morning brief — v2
- Multi-user support — this is a personal tool
- Mobile-specific UI (responsive Tailwind is sufficient, no native app)
- Auth UI (login page, sessions, cookies) — token-in-URL is sufficient for v1
- CI/CD pipeline — manual `railway up` is fine for a solo project
- LangGraph multi-agent chain — single chain is sufficient for v1 brief quality
