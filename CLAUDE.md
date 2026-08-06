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

FastAPI serves both the REST API (`/api/*`) and the built React frontend as static files. SQLite (via SQLModel) is the data layer. Forge tracks four concurrent workstreams ("projects" — see `chain/projects.py`), each backed by its own vault note; only the flagship project (`career`, the AI-pivot roadmap) also gets the full `sessions`/`metrics`/`milestones`/`briefs` tracking — the other three are pure vault-synced read views. The LangChain morning brief chain (`chain/morning_brief.py`, flagship-only) reads yesterday's session, runs 2–3 Tavily searches based on the work type, and calls Claude Haiku 4.5 (or Gemini 1.5 Flash) to generate a structured brief; a second Railway service (same repo, cron-scheduled) runs it at 7am and the user can regenerate on demand. A second chain (`chain/project_sync.py`) reads a project's vault note (local filesystem only) plus anything it `[[wikilinks]]` to, and proposes an updated focus/up-next/progress view — for the flagship project, also a proposed roadmap stage/milestone state. Read-only against the vault; proposals are never auto-applied, the user reviews and clicks Apply. The UI is a **project picker** (grid of cards, one per workstream) and a **project detail** view per project, navigated via a `?id=` query param (no router library — see Frontend notes). Auth is two env-var tokens: `VIEW_TOKEN` (read-only, in shareable URL) and `ADMIN_TOKEN` (write access, in Authorization header).

## File layout

```
forge/
├── api/
│   ├── main.py
│   ├── routers/         projects.py, log.py, metrics.py, brief.py, context.py
│   ├── services/        brief_service.py, project_service.py, context_service.py
│   ├── models/          models.py (SQLModel tables + Pydantic schemas)
│   └── db/              database.py
├── chain/
│   ├── llm_utils.py     shared get_llm() / parse_json_response()
│   ├── morning_brief.py
│   ├── projects.py      static PROJECTS config (id, name, vault_note, accent, flagship, ...)
│   └── project_sync.py
├── scripts/
│   └── migrate.py       one-time import from career-metrics.json
├── frontend/
│   └── src/
│       ├── App.jsx       query-param routing between picker/detail
│       ├── api.js
│       ├── accents.js    shared accent-color lookup + relativeTime()
│       └── components/  ProjectPicker, ProjectGrid, ProjectCard, ProjectDetail, FocusCard,
│                         UpNextChecklist, ProgressTimeline, RoadmapStepper, StatusPill, StatChip,
│                         BackLink, TopBar, MorningBrief, Heatmap, MetricsRow, Milestones, LogSession
├── Dockerfile
├── .railway/railway.ts
└── requirements.txt
```

## Database tables

```sql
sessions             (id, date TEXT, type TEXT, notes TEXT, commits INT, level INT, created_at INT)
metrics              (id, projects_shipped INT, applications_sent INT, stages_complete INT, updated_at INT)
milestones           (key TEXT PRIMARY KEY, completed BOOL, completed_at INT)
briefs               (id, date TEXT, summary TEXT, focus TEXT, research TEXT, generated_at INT)
project_snapshots    (id, project_id TEXT, created_at INT, status TEXT, focus TEXT, focus_meta TEXT,
                       stats TEXT, up_next TEXT, progress TEXT, completed_up_next TEXT,
                       proposed_stage INT, proposed_milestones TEXT, applied BOOL, applied_at INT)
archived_context_items (id, text TEXT, source TEXT, snapshot_id INT, archived_at INT)
```

`sessions.type` is a JSON array string: `'["python","project"]'`
`briefs.research` is a JSON array string: `'[{"title":"...","url":"...","reason":"..."}]'`
`project_snapshots.stats` is `'[["label","value"], ...]'`, `.up_next`/`.completed_up_next` are `'[{"title":"...","detail":"..."}, ...]'`, `.progress` is `'["...", ...]'`, `.proposed_milestones` is `'{"stage1_shipped": false, ...}'` (flagship project only, else `null`).
`sessions`/`metrics`/`milestones`/`briefs` only ever get written for the flagship project (`"career"`); the other three projects only ever produce `project_snapshots` rows.
`metrics` is always a single row (id=1), updated in place.
`project_snapshots` is insert-only from a refresh, with one exception: completing an up-next item mutates the latest row in place (moves an item from `up_next` to `completed_up_next`) rather than creating a new row — see `complete_up_next_item` in `api/services/project_service.py`.
`archived_context_items` is a save-for-later feature built for the old single-project Context Sync UI. The backend/API (`api/routers/context.py`) is still there but it's **not wired into the current UI** — left in place in case it's revived later.

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

## Project sync chain (vault → proposed state, per project)

```python
# chain/project_sync.py — simplified flow
from chain.llm_utils import get_llm, parse_json_response

def synthesize_project(vault_note_path: Path, flagship_context: dict | None = None) -> dict:
    vault_text = read_vault_note(vault_note_path)  # None if the note doesn't exist
    if vault_text is None:
        return {"focus": "No vault note found...", ...}

    linked_notes = read_linked_notes(vault_note_path, vault_text)  # one level of [[wikilinks]]
    prompt = build_prompt(vault_text, linked_notes, flagship_context)
    response = get_llm().invoke(prompt)
    return parse_json_response(response.content)
    # -> {status, focus, focus_meta, stats, up_next, progress, [proposed_stage, proposed_milestones]}
```

`flagship_context = {"current_stage": int, "current_milestones": dict}` is only passed for the `career` project — that's what triggers the prompt to also ask for `proposed_stage`/`proposed_milestones`; the other three projects never get those keys.

- **Read-only against the vault** — never writes back to it. Reads whichever note `chain/projects.py`'s `PROJECTS` config points a project at, plus any note it `[[wikilinks]]` to, one level deep (not recursive).
- **Local-only**: `VAULT_PROJECTS_DIR` defaults to `/Users/bensmith/Documents/ember-vault/projects/` on this Mac's filesystem (falls back to reading the legacy `VAULT_CAREER_PIVOT_PATH` var's parent dir if that's the only one set). On the Railway deployment this path doesn't exist, so `/api/projects/{id}/refresh` there just hits the "no vault note found" fallback — this feature only does anything useful when Forge runs locally via `forge run`.
- **Propose-then-approve, not auto-apply** (flagship project only — the other three have no tracked state to protect, so their synced view just *is* the current state): `POST /api/projects/career/refresh` (admin-only) runs the chain and inserts a new `project_snapshots` row (`applied=false`) — it never touches `metrics`/`milestones`. `POST /api/projects/career/apply` (admin-only, body `{snapshot_id}`) is the explicit step that copies `proposed_stage`/`proposed_milestones` into the real tracked tables. This exists specifically to avoid an LLM misreading a note and silently rewriting tracked progress — the model is also instructed to only mark something complete on concrete evidence, not vague language.
- `GET /api/projects` returns the picker's card data (one entry per project); `GET /api/projects/{id}` returns the full detail payload, and for the flagship project also bundles `sessions`/`metrics`/`milestones`/`brief`/`roadmap` (all flagship-only). The frontend (`ProjectDetail.jsx`) always shows `focus`/`up_next`/`progress`, and — flagship only, while the latest snapshot is unapplied — an amber "proposed update" box with an Apply button.
- Checking off an `up_next` item (`POST /api/projects/{id}/complete-item`, body `{index}`) moves it into `progress` immediately; that carries forward across future refreshes (see `project_snapshots` note above) rather than being LLM-regenerated.

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

- **Routing**: no router library. `App.jsx` holds a `selectedId` derived from `?id=<projectId>` in the URL, toggled with `history.pushState`/`popstate`. This works with zero backend routing changes because `auth_middleware` only special-cases the exact path `/` (query string doesn't affect `request.url.path`), and everything lives under that one path.
- **Design tokens**: mockups' CSS vars are in `tailwind.config.js` under `theme.extend.colors`, namespaced under `accent.{blue,coral,teal,purple}.{bg,text,solid}` (deliberately *not* bare `colors.blue`/`.teal`/`.purple` — that would silently replace Tailwind's default palette shades, which `ShareBadge.jsx`/`MorningBrief.jsx`/`LogSession.jsx`/`Milestones.jsx` still use). Look up a project's accent classes via `accentOf(project.accent)` in `src/accents.js`; don't hardcode class names per accent elsewhere.
- Heatmap: 26 weeks × 7 days. Level 0 = `#eeede7`, 1 = `#bbdebb`, 2 = `#5db85d`, 3 = `#267326`. Today's cell has a blue outline. Future cells are faded. Flagship project only.
- Write affordances (LogSession, milestone toggles, refresh/apply/complete-item buttons) are hidden/disabled when `isSharedView` is true (i.e., user reached the app via `?v=VIEW_TOKEN` without admin token).
- All API calls go through `src/api.js`, which reads `window.__VIEW_TOKEN__` and appends `?v=<token>` to read requests — **note this global is currently never actually injected anywhere** (no templating on the served `index.html`), so `VIEW_TOKEN` is always `undefined` client-side today. Pre-existing gap, not something this UI pass touched; worth fixing separately if the shared read-only link flow needs to actually work.
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

Optional (project sync — has a working default, only needed to override):
```
VAULT_PROJECTS_DIR        # default: /Users/bensmith/Documents/ember-vault/projects/
VAULT_CAREER_PIVOT_PATH   # legacy — only read if VAULT_PROJECTS_DIR is unset, to derive the same default dir
```

## Railway config notes

Infra is defined as code in `.railway/railway.ts` (via the `railway` npm package's IaC API — `railway config plan`/`apply`), not a plain `railway.json`. Two services, both built from the repo's Dockerfile via GitHub source:

- `web` — always-on, default CMD (uvicorn). Owns the `data` volume, mounted at `/data`. `PORT` is pinned to `8000` explicitly (rather than left to Railway's dynamic per-deploy assignment) so `morning-brief` can reliably reference it.
- `morning-brief` — a `fn()` resource (Railway's cron/function kind), Start Command `python scripts/trigger_brief.py`, Cron Schedule `0 7 * * *`.

**Important constraint learned the hard way: a Railway volume can only attach to one service at a time** — it silently detaches if you try to declare it on a second service. So `morning-brief` does *not* mount the volume or touch the SQLite file directly. Instead it makes an HTTP POST to `web`'s own `/api/brief/generate` over Railway's private network (`web.railway.internal`, referenced via `web.env.RAILWAY_PRIVATE_DOMAIN`/`web.env.PORT` in `railway.ts`) — the same endpoint the UI's "Regenerate" button hits.

Health checks matter: Railway's healthcheck needs a plain 2xx, so it hits `GET /health` (unauthenticated, defined in `api/main.py`) — not `/api/dashboard`, which correctly 401s without a token and Railway reads as "service unavailable."

Secrets are Railway "Variables" per-service, set via `railway variable set KEY=value --service <name> --skip-deploys` — never via `railway variable list` without `--service`, since both the default and `--json`/`--kv` forms print raw values to stdout. `web` needs `VIEW_TOKEN`, `ADMIN_TOKEN`, `ANTHROPIC_API_KEY`/`GOOGLE_API_KEY`, `TAVILY_API_KEY`; `morning-brief` only needs a matching `ADMIN_TOKEN` (used to call `web`).

## Tracked projects (`chain/projects.py`)

Static, hand-edited list — not a DB table, same pattern as `ROADMAP` below. Adding a 5th project today means editing this file and adding a vault note, not using the picker's "+ New project" card (visual placeholder only, no add-project flow built).

| id | name | vault note | accent | flagship |
|----|------|-----------|--------|----------|
| `career` | Career pivot | `career-pivot.md` | blue | yes — has roadmap/metrics/milestones/brief |
| `pss` | PSS Data | `ask-pss-data.md` | coral | no |
| `watchtower` | Watchtower | `ai-trends-radar.md` | teal | no |
| `interview` | Interview prep | `ccts-star-stories.md` | purple | no |

## 5-stage roadmap (for the UI and brief context, flagship project only)

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
- A real "add project" flow (form for name/vault note/icon/color) — the picker's "+ New project" card is a placeholder; new projects are added by editing `chain/projects.py`
- `sessions`/`metrics`/`milestones`/`briefs`-style tracking for non-flagship projects — they're vault-synced read views only, no per-project heatmap/streak/roadmap

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
