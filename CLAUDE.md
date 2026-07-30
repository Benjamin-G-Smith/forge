# CLAUDE.md — Forge

This file gives you everything you need to work on this project without asking clarifying questions.

## What this project is

A personal career progress tracker + AI-powered morning brief app. Built by Benjamin Smith as both a daily productivity tool and a portfolio piece demonstrating Python, FastAPI, LangChain, and Claude API skills.

Benjamin is a C#/.NET/Angular developer pivoting to an AI Application Engineer role ($143K–$220K). This app is his Stage 1 project — it needs to be deployed at a real public URL so he can link to it in job applications.

## Non-negotiables

- **Python only on the backend.** Benjamin is building Python skills. Do not suggest C# or Node for backend work.
- **Keep it shippable.** Prefer simple working code over clever abstractions. This is a solo portfolio project, not a team codebase.
- **LangChain for the brief chain.** Even if raw API calls would be simpler — the point is to build LangChain experience.
- **SQLite only.** No Postgres, no Redis, no external databases. SQLite lives in a Railway volume.
- **React + Tailwind for the frontend.** Beautiful UI matters — this is a portfolio piece. Don't suggest plain HTML/JS.

## Architecture in one paragraph

FastAPI serves both the REST API (`/api/*`) and the built React frontend as static files. SQLite (via SQLModel) is the data layer — one DB file with four tables: `sessions`, `metrics`, `milestones`, `briefs`. The LangChain morning brief chain (`chain/morning_brief.py`) reads yesterday's session, runs 2–3 Tavily searches based on the work type, and calls Claude Haiku 3.5 (or Gemini 1.5 Flash) to generate a structured brief. A second Railway service (same repo, cron-scheduled) runs the chain at 7am and the user can regenerate on demand. Auth is two env-var tokens: `VIEW_TOKEN` (read-only, in shareable URL) and `ADMIN_TOKEN` (write access, in Authorization header).

## File layout

```
forge/
├── api/
│   ├── main.py
│   ├── routers/         dashboard.py, log.py, metrics.py, brief.py
│   ├── services/        brief_service.py
│   ├── models/          models.py (SQLModel tables + Pydantic schemas)
│   └── db/              database.py
├── chain/
│   └── morning_brief.py
├── scripts/
│   └── migrate.py       one-time import from career-metrics.json
├── frontend/
│   └── src/
│       ├── App.jsx
│       ├── api.js
│       └── components/  MorningBrief, Heatmap, MetricsRow, StageTrack, Milestones, LogSession
├── Dockerfile
├── railway.json
└── requirements.txt
```

## Database tables

```sql
sessions   (id, date TEXT, type TEXT, notes TEXT, commits INT, level INT, created_at INT)
metrics    (id, projects_shipped INT, applications_sent INT, stages_complete INT, updated_at INT)
milestones (key TEXT PRIMARY KEY, completed BOOL, completed_at INT)
briefs     (id, date TEXT, summary TEXT, focus TEXT, research TEXT, generated_at INT)
```

`sessions.type` is a JSON array string: `'["python","project"]'`
`briefs.research` is a JSON array string: `'[{"title":"...","url":"...","reason":"..."}]'`
`metrics` is always a single row (id=1), updated in place.

## Auth middleware pattern

```python
# In main.py — applied to all routes
VIEW_TOKEN = os.environ["VIEW_TOKEN"]
ADMIN_TOKEN = os.environ["ADMIN_TOKEN"]

async def auth_middleware(request: Request, call_next):
    token = request.query_params.get("v")
    auth_header = request.headers.get("Authorization", "")
    bearer = auth_header.removeprefix("Bearer ").strip()

    request.state.is_admin = bearer == ADMIN_TOKEN
    request.state.is_viewer = token == VIEW_TOKEN or request.state.is_admin

    if not request.state.is_viewer and not request.url.path == "/":
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    return await call_next(request)
```

Write routes call `require_admin(request)` as a dependency — raises 403 if not admin.

## LangChain brief chain

```python
# chain/morning_brief.py — simplified flow
from langchain_anthropic import ChatAnthropic
from langchain_community.tools.tavily_search import TavilySearchResults

def generate_brief(session: dict | None) -> dict:
    # 1. Build search queries from session type + notes
    queries = classify_session(session)  # returns list[str]

    # 2. Search
    tool = TavilySearchResults(max_results=3)
    results = []
    for q in queries:
        results.extend(tool.invoke(q))

    # 3. Generate
    llm = ChatAnthropic(model="claude-haiku-3-5")
    prompt = build_prompt(session, results, roadmap_position())
    response = llm.invoke(prompt)

    # 4. Parse structured output (JSON in the response)
    brief = parse_brief_json(response.content)

    # 5. Persist to DB
    save_brief(brief)
    return brief
```

Fallback: if `session` is None (no log entry yesterday), use roadmap position as context.

## Existing data to migrate

The user has a JSON file at:
`/Users/bensmith/Documents/ember-vault/_system/career-metrics.json`

Schema:
```json
{
  "meta": { "north_star": "...", "target_date": "2027-06-11", "flavor": "..." },
  "metrics": {
    "projects_shipped": 0,
    "applications_sent": 0,
    "stages_complete": 0,
    "milestones": {
      "stage1_shipped": false,
      "building_in_public": false,
      "eval_harness_coded": false,
      "first_post_published": false,
      "ten_apps_sent": false,
      "pss_public_url": false,
      "second_project_shipped": false
    }
  },
  "log": []
}
```

`scripts/migrate.py` reads this file and seeds SQLite. It is idempotent.

## Frontend notes

- Heatmap: 26 weeks × 7 days. Level 0 = `#eeede7`, 1 = `#bbdebb`, 2 = `#5db85d`, 3 = `#267326`. Today's cell has a blue outline. Future cells are faded.
- LogSession form is hidden when `isSharedView` is true (i.e., user reached the app via `?v=VIEW_TOKEN` without admin token).
- All API calls go through `src/api.js` which reads `window.__VIEW_TOKEN__` (injected by FastAPI into index.html) and appends `?v=<token>` to read requests.
- For admin writes, the frontend sends `Authorization: Bearer <ADMIN_TOKEN>` — Benjamin sets this in localStorage on first login (no auth UI needed, he can use the browser console or a simple settings input).

## Environment variables (all required)

```
ANTHROPIC_API_KEY    # console.anthropic.com
TAVILY_API_KEY       # app.tavily.com — free tier is 1000/month, enough
VIEW_TOKEN           # python -c "import secrets; print(secrets.token_urlsafe(24))"
ADMIN_TOKEN          # same, keep private
```

Optional (if switching to Gemini):
```
GOOGLE_API_KEY
```
To swap: change `ChatAnthropic` → `ChatGoogleGenerativeAI(model="gemini-1.5-flash")` in `morning_brief.py`.

## Railway config notes

- Dockerfile: multi-stage — Node stage builds the React frontend, Python stage runs FastAPI
- FastAPI serves the React `dist/` folder as static files on `/`
- The Dockerfile CMD reads `$PORT` (Railway assigns this dynamically, unlike Fly's fixed port) — don't hardcode a port
- SQLite DB file lives at `/data/career.db` — attach a Railway volume at `/data` (Volumes are set up per-service in the Railway dashboard, not in `railway.json`)
- Two Railway services from this same repo:
  - `web` — always-on, runs the Dockerfile's default CMD (uvicorn)
  - `morning-brief` — same image, Start Command overridden to `python -m chain.morning_brief --scheduled`, with a Cron Schedule of `0 7 * * *` set in that service's Settings. It needs the same volume mounted at `/data` so it reads/writes the same SQLite file as `web`.
- Secrets/env vars are set as Railway "Variables" per-service (both services need `ANTHROPIC_API_KEY`/`GOOGLE_API_KEY`, `TAVILY_API_KEY`, `DB_PATH`; only `web` needs `VIEW_TOKEN`/`ADMIN_TOKEN`)

## 5-stage roadmap (for the UI and brief context)

| Stage | Title | Target |
|-------|-------|--------|
| 1 | Python + wrapper project | Aug 2026 |
| 2 | Memory + state | Sept 2026 |
| 3 | Ask PSS Data (text-to-SQL) | Oct 2026 |
| 4 | Agents + MCP | Nov 2026 |
| 5 | Ship to real users | Dec 2026 |

`stages_complete` in the metrics table stores how many stages are done (0–5).

## Milestone keys (in order)

```
stage1_shipped
building_in_public
eval_harness_coded
first_post_published
ten_apps_sent
pss_public_url
second_project_shipped
```

## What is explicitly out of scope

- Per-person invite link management (v2)
- Email or calendar integration in the brief (v2)
- Multi-user support
- Auth UI (login page, sessions, cookies)
- CI/CD pipeline
- LangGraph multi-agent chain
- Postgres or any external database

## Suggested build order

1. SQLite schema + SQLModel models (`api/models/models.py`, `api/db/database.py`)
2. Migration script (`scripts/migrate.py`)
3. FastAPI routes — `GET /api/dashboard` first (read-only, tests the DB)
4. `POST /api/log` + `PATCH /api/metrics` + `PATCH /api/milestones/{key}`
5. LangChain brief chain (`chain/morning_brief.py`) — hardest piece, build standalone first
6. `GET /api/brief` + `POST /api/brief/generate`
7. React frontend — Heatmap + MetricsRow first (data display), then LogSession (writes)
8. MorningBrief component
9. Dockerfile + railway.json
10. Deploy to Railway, add variables, run migration script, test
