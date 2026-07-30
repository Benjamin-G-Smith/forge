# Forge

A personal AI-powered career pivot dashboard. Tracks daily progress toward an AI engineer role, generates a LangChain-powered morning brief each day, and lives at a public Fly.io URL as a live portfolio piece.

## What this is

Benjamin Smith is a C#/.NET/Angular developer at CCTS (~$99K) pivoting to an AI Application Engineer role ($143K–$220K target) by June 2027. This app is both a personal productivity tool and Stage 1 of a 5-stage career roadmap — it demonstrates Python, FastAPI, LangChain, and Claude API integration in a real deployed application.

The app tracks session logs (daily work), generates a morning brief using a LangChain chain (log → Tavily search → Claude/Gemini → brief), and is shareable with hiring managers via a token URL.

## Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Backend | Python 3.11 + FastAPI | Core skill to build; on every AI engineer job description |
| Database | SQLite via SQLModel | Self-contained, zero ops, sufficient for solo use |
| LLM chain | LangChain + Tavily + Claude Haiku 3.5 | LangChain is the dominant framework in 2026 AI eng postings; Tavily is the standard search pairing |
| Frontend | React 18 + Tailwind CSS + Vite | Portfolio-quality UI; familiar component model |
| Deployment | Fly.io | Free tier, built-in scheduler for nightly brief, easy secrets management |
| LLM fallback | Gemini 1.5 Flash | Free API tier — swap via one env var if Anthropic costs are a concern |

## Project structure

```
forge/
├── api/
│   ├── main.py              # FastAPI app, route registration, middleware
│   ├── routers/
│   │   ├── dashboard.py     # GET /api/dashboard
│   │   ├── log.py           # POST /api/log
│   │   ├── metrics.py       # PATCH /api/metrics, PATCH /api/milestones/{key}
│   │   └── brief.py         # GET /api/brief, POST /api/brief/generate
│   ├── services/
│   │   └── brief_service.py # LangChain chain (see below)
│   ├── models/
│   │   └── models.py        # SQLModel table definitions + Pydantic schemas
│   └── db/
│       └── database.py      # SQLite engine, session factory, init_db()
├── chain/
│   └── morning_brief.py     # LangChain chain: log → search → generate → persist
├── scripts/
│   └── migrate.py           # One-time import from career-metrics.json to SQLite
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js           # Fetch wrapper; appends ?v=VIEW_TOKEN in share mode
│   │   └── components/
│   │       ├── MorningBrief.jsx
│   │       ├── Heatmap.jsx
│   │       ├── MetricsRow.jsx
│   │       ├── StageTrack.jsx
│   │       ├── Milestones.jsx
│   │       └── LogSession.jsx
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
├── Dockerfile
├── fly.toml
├── requirements.txt
├── CLAUDE.md
└── README.md
```

## SQLite schema

```sql
-- Daily session logs (drives the heatmap)
CREATE TABLE sessions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    date       TEXT NOT NULL,        -- YYYY-MM-DD
    type       TEXT NOT NULL,        -- JSON array: ["python","project"]
    notes      TEXT,
    commits    INTEGER DEFAULT 0,
    level      INTEGER NOT NULL,     -- 1=light, 2=solid, 3=deep
    created_at INTEGER               -- unix ms
);

-- Top-level metrics (single row, updated in place)
CREATE TABLE metrics (
    id                INTEGER PRIMARY KEY,
    projects_shipped  INTEGER DEFAULT 0,
    applications_sent INTEGER DEFAULT 0,
    stages_complete   INTEGER DEFAULT 0,
    updated_at        INTEGER
);

-- Milestone boolean flags
CREATE TABLE milestones (
    key          TEXT PRIMARY KEY,
    completed    BOOLEAN DEFAULT FALSE,
    completed_at INTEGER
);

-- Generated morning briefs
CREATE TABLE briefs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    date         TEXT NOT NULL,      -- YYYY-MM-DD
    summary      TEXT,               -- yesterday recap sentence
    focus        TEXT,               -- today's recommended focus
    research     TEXT,               -- JSON: [{title, url, reason}]
    generated_at INTEGER
);
```

## API routes

| Method | Route | Auth | Description |
|--------|-------|------|-------------|
| GET | `/api/dashboard` | view token | Full payload: metrics, log, milestones, brief |
| POST | `/api/log` | admin | Create a session log entry |
| PATCH | `/api/metrics` | admin | Update projects_shipped / applications_sent / stages_complete |
| PATCH | `/api/milestones/{key}` | admin | Toggle a milestone boolean |
| GET | `/api/brief` | view token | Latest generated brief |
| POST | `/api/brief/generate` | admin | Trigger on-demand brief generation |
| GET | `/*` | view token | Serve React frontend (index.html) |

## Auth

Two tokens, both set as Fly.io secrets (env vars):

- `VIEW_TOKEN` — read-only access. Appended to shareable URLs as `?v=<token>`. Hiring managers get this URL. Full dashboard visible, log form hidden.
- `ADMIN_TOKEN` — write access. Used by Benjamin via `Authorization: Bearer <token>` header. All write routes require this.

Middleware checks incoming requests and sets `request.state.is_admin` and `request.state.is_viewer` flags. Unauthenticated requests to any route get a 401.

## LangChain morning brief chain

File: `chain/morning_brief.py`

```
Input: yesterday's Session row from SQLite

Step 1 — Classify
  Map session type + notes → 2-3 Tavily search queries
  e.g. type=["python"] notes="practiced LangChain tool use"
    → ["LangChain tool use tutorial 2026", "LangGraph agent patterns python"]

Step 2 — Search
  TavilySearchResults(max_results=3) per query
  Deduplicate by URL

Step 3 — Generate
  Prompt: yesterday's log + search snippets + current roadmap position
  → ChatAnthropic (claude-haiku-3-5) or ChatGoogleGenerativeAI (gemini-1.5-flash)
  → Structured output via Pydantic: {summary, focus, research[{title, url, reason}]}

Step 4 — Persist
  Write to briefs table

Output: Brief object
```

**Fallback:** If no session logged yesterday, brief uses roadmap position (current stage + next milestone) as context instead of a log entry.

## Data migration

Benjamin has existing data in `/Users/bensmith/Documents/ember-vault/_system/career-metrics.json`.

Run `python scripts/migrate.py` once on first deploy. The script:
1. Reads the JSON file
2. Imports `log[]` → `sessions` table
3. Imports `metrics` → `metrics` table
4. Imports `milestones` → `milestones` table
5. Is idempotent — skips entries that already exist by date

The JSON schema:
```json
{
  "meta": { "north_star": "...", "target_date": "...", "flavor": "..." },
  "metrics": {
    "projects_shipped": 0,
    "applications_sent": 0,
    "stages_complete": 0,
    "milestones": { "stage1_shipped": false, ... }
  },
  "log": [
    { "date": "YYYY-MM-DD", "type": ["python"], "notes": "...", "level": 2 }
  ]
}
```

## Fly.io deployment

```toml
# fly.toml (key sections)
[http_service]
  internal_port = 8000

[[statics]]
  guest_path = "/app/frontend/dist"
  url_prefix = "/"

[processes]
  app = "uvicorn api.main:app --host 0.0.0.0 --port 8000"

[[schedules]]
  schedule = "0 7 * * *"           # 7am daily
  command = "python -m chain.morning_brief --scheduled"
```

Required secrets: `VIEW_TOKEN`, `ADMIN_TOKEN`, `ANTHROPIC_API_KEY`, `TAVILY_API_KEY`

## Environment variables

```
ANTHROPIC_API_KEY=     # From console.anthropic.com
TAVILY_API_KEY=        # From app.tavily.com (free tier: 1000 searches/month)
VIEW_TOKEN=            # Generate: python -c "import secrets; print(secrets.token_urlsafe(24))"
ADMIN_TOKEN=           # Same as above, keep private
GOOGLE_API_KEY=        # Optional — only if using Gemini instead of Claude
```

## Frontend components

| Component | What it shows |
|-----------|---------------|
| `MorningBrief` | Top panel: summary, today's focus recommendation, 2–3 research links with reason tags |
| `Heatmap` | 26-week × 7-day grid. Level 0=empty, 1=light green, 2=medium, 3=dark. Today cell has outline. |
| `MetricsRow` | 4 cards: current streak (days), projects shipped, stages complete (x/5), applications sent |
| `StageTrack` | 5-stage roadmap with connector lines. Stages: Python+wrapper → Memory+state → Ask PSS Data → Agents+MCP → Ship to users |
| `Milestones` | 7 checkboxes with timing badges: stage1_shipped, building_in_public, eval_harness_coded, first_post_published, ten_apps_sent, pss_public_url, second_project_shipped |
| `LogSession` | Form: type selector (python/project/research/application/learning/other), notes textarea, intensity (Light <30m / Solid 1-2h / Deep 2h+), submit. Hidden on shared-link views. |

## Out of scope (v1)

- Per-person invite link management
- Email/calendar integration in the morning brief
- Multi-user support
- Auth UI (login page, cookies, sessions)
- CI/CD pipeline
- LangGraph multi-agent chain
- Mobile-specific UI (responsive Tailwind is sufficient)
