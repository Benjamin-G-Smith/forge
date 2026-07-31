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

FastAPI serves both the REST API (`/api/*`) and the built React frontend as static files. SQLite (via SQLModel) is the data layer — one DB file with five tables: `sessions`, `metrics`, `milestones`, `briefs`, `context_snapshots`. The LangChain morning brief chain (`chain/morning_brief.py`) reads yesterday's session, runs 2–3 Tavily searches based on the work type, and calls Claude Haiku 4.5 (or Gemini 1.5 Flash) to generate a structured brief. A second Railway service (same repo, cron-scheduled) runs the chain at 7am and the user can regenerate on demand. A second chain (`chain/context_sync.py`) reads Benjamin's Obsidian vault (`career-pivot.md`, local filesystem only) and proposes updates to the tracked roadmap stage/milestones — read-only against the vault, and the proposal is never auto-applied; he reviews and clicks Apply. Auth is two env-var tokens: `VIEW_TOKEN` (read-only, in shareable URL) and `ADMIN_TOKEN` (write access, in Authorization header).

## File layout

```
forge/
├── api/
│   ├── main.py
│   ├── routers/         dashboard.py, log.py, metrics.py, brief.py, context.py
│   ├── services/        brief_service.py, context_service.py
│   ├── models/          models.py (SQLModel tables + Pydantic schemas)
│   └── db/              database.py
├── chain/
│   ├── llm_utils.py     shared get_llm() / parse_json_response()
│   ├── morning_brief.py
│   └── context_sync.py
├── scripts/
│   └── migrate.py       one-time import from career-metrics.json
├── frontend/
│   └── src/
│       ├── App.jsx
│       ├── api.js
│       └── components/  MorningBrief, ContextSync, Focus, Heatmap, MetricsRow, StageTrack, Milestones, LogSession
├── Dockerfile
├── .railway/railway.ts
└── requirements.txt
```

## Database tables

```sql
sessions          (id, date TEXT, type TEXT, notes TEXT, commits INT, level INT, created_at INT)
metrics           (id, projects_shipped INT, applications_sent INT, stages_complete INT, updated_at INT)
milestones        (key TEXT PRIMARY KEY, completed BOOL, completed_at INT)
briefs            (id, date TEXT, summary TEXT, focus TEXT, research TEXT, generated_at INT)
context_snapshots (id, created_at INT, source TEXT, summary TEXT, next_action TEXT, reasoning TEXT,
                    proposed_stage INT, proposed_milestones TEXT, applied BOOL, applied_at INT)
```

`sessions.type` is a JSON array string: `'["python","project"]'`
`briefs.research` is a JSON array string: `'[{"title":"...","url":"...","reason":"..."}]'`
`context_snapshots.proposed_milestones` is a JSON object string: `'{"stage1_shipped": false, ...}'`
`metrics` is always a single row (id=1), updated in place.
`context_snapshots` is insert-only — each refresh adds a new row rather than updating one. `applied`/`applied_at` are the only fields ever changed after insert.

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
from chain.llm_utils import get_llm, parse_json_response
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper

def generate_brief(session: dict | None) -> dict:
    # 1. Build search queries from session type + notes
    queries = classify_session(session)  # returns list[str]

    # 2. Search — use raw_results(), not the TavilySearchResults tool /
    # .results(): both route through clean_results(), which silently drops
    # the title field Tavily actually returns (keeps only url + content).
    wrapper = TavilySearchAPIWrapper()
    results = []
    for q in queries:
        results.extend(wrapper.raw_results(q, max_results=3)["results"])

    # 3. Generate
    llm = get_llm()  # ChatAnthropic(claude-haiku-4-5), or Gemini if only GOOGLE_API_KEY is set
    prompt = build_prompt(session, results, roadmap_position())
    response = llm.invoke(prompt)

    # 4. Parse structured output (JSON in the response)
    brief = parse_json_response(response.content)

    # 5. Persist to DB
    save_brief(brief)
    return brief
```

Fallback: if `session` is None (no log entry yesterday), use roadmap position as context.

## Context sync chain (vault → proposed state)

```python
# chain/context_sync.py — simplified flow
from chain.llm_utils import get_llm, parse_json_response

def synthesize_context(current_stage: int, current_milestones: dict[str, bool]) -> dict:
    vault_text = read_vault_note()  # reads VAULT_CAREER_PIVOT_PATH, or None if missing
    if vault_text is None:
        return {"summary": "No vault note found...", "proposed_stage": current_stage, ...}

    prompt = build_prompt(vault_text, current_stage, current_milestones)
    response = get_llm().invoke(prompt)
    return parse_json_response(response.content)
    # -> {summary, next_action, proposed_stage, proposed_milestones, reasoning}
```

- **Read-only against the vault** — never writes back to it. Reads only `career-pivot.md` (v1 — other vault project files are out of scope for now).
- **Local-only**: `VAULT_CAREER_PIVOT_PATH` defaults to `/Users/bensmith/Documents/ember-vault/projects/career-pivot.md`, on this Mac's filesystem. On the Railway deployment this path doesn't exist, so `/api/context/refresh` there just hits the "no vault note found" fallback — this feature only does anything useful when Forge runs locally via `forge run`.
- **Propose-then-approve, not auto-apply**: `POST /api/context/refresh` (admin-only) runs the chain and inserts a new `context_snapshots` row (`applied=false`) — it never touches `metrics`/`milestones`. `POST /api/context/{id}/apply` (admin-only) is the explicit step that copies `proposed_stage`/`proposed_milestones` into the real tracked tables. This exists specifically to avoid an LLM misreading a note and silently rewriting tracked progress — the model is also instructed to only mark something complete on concrete evidence, not vague language.
- `GET /api/context` returns the latest snapshot (applied or not); the dashboard payload includes it under `context`. The frontend (`ContextSync.jsx`) shows the summary/next_action always, and an amber "proposed update" box with an Apply button only while the latest snapshot is unapplied.

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
To swap: change `ChatAnthropic` → `ChatGoogleGenerativeAI(model="gemini-1.5-flash")` in `chain/llm_utils.py`'s `get_llm()`.

Optional (context sync — has a working default, only needed to override):
```
VAULT_CAREER_PIVOT_PATH   # default: /Users/bensmith/Documents/ember-vault/projects/career-pivot.md
```

## Railway config notes

Infra is defined as code in `.railway/railway.ts` (via the `railway` npm package's IaC API — `railway config plan`/`apply`), not a plain `railway.json`. Two services, both built from the repo's Dockerfile via GitHub source:

- `web` — always-on, default CMD (uvicorn). Owns the `data` volume, mounted at `/data`. `PORT` is pinned to `8000` explicitly (rather than left to Railway's dynamic per-deploy assignment) so `morning-brief` can reliably reference it.
- `morning-brief` — a `fn()` resource (Railway's cron/function kind), Start Command `python scripts/trigger_brief.py`, Cron Schedule `0 7 * * *`.

**Important constraint learned the hard way: a Railway volume can only attach to one service at a time** — it silently detaches if you try to declare it on a second service. So `morning-brief` does *not* mount the volume or touch the SQLite file directly. Instead it makes an HTTP POST to `web`'s own `/api/brief/generate` over Railway's private network (`web.railway.internal`, referenced via `web.env.RAILWAY_PRIVATE_DOMAIN`/`web.env.PORT` in `railway.ts`) — the same endpoint the UI's "Regenerate" button hits.

Health checks matter: Railway's healthcheck needs a plain 2xx, so it hits `GET /health` (unauthenticated, defined in `api/main.py`) — not `/api/dashboard`, which correctly 401s without a token and Railway reads as "service unavailable."

Secrets are Railway "Variables" per-service, set via `railway variable set KEY=value --service <name> --skip-deploys` — never via `railway variable list` without `--service`, since both the default and `--json`/`--kv` forms print raw values to stdout. `web` needs `VIEW_TOKEN`, `ADMIN_TOKEN`, `ANTHROPIC_API_KEY`/`GOOGLE_API_KEY`, `TAVILY_API_KEY`; `morning-brief` only needs a matching `ADMIN_TOKEN` (used to call `web`).

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
9. Dockerfile + .railway/railway.ts
10. Deploy to Railway, add variables, run migration script, test
