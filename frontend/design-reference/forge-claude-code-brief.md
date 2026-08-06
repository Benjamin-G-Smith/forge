# Forge UI overhaul — build brief for Claude Code

## How to use this

1. Copy `forge-redesign.html`, `forge-project-picker.html`, and `forge-project.html` into the repo (e.g. a temporary `design-reference/` folder) so Claude Code can open them directly and read the exact markup, CSS, and JS.
2. Paste the prompt below into Claude Code as the opening instruction, then let it read the rest of this brief for the details it needs.

### Prompt to paste into Claude Code

> I'm rebuilding the UI of my Forge focus tracker app. There are three static HTML mockups in `design-reference/` (`forge-redesign.html` — the single-project dashboard, `forge-project-picker.html` — a grid to switch between projects, `forge-project.html` — a per-project detail page with client-side routing via a `?id=` param) and a spec at `forge-claude-code-brief.md`. First, inspect my existing codebase to understand the current framework, routing, component structure, and where project/task data currently lives. Then propose a plan to restructure the UI to match the mockups — new information architecture (project picker as home, per-project detail view, back navigation), the design tokens and component breakdown in the brief, and real data wired in instead of the mockups' hardcoded objects. Don't start writing code until I've confirmed the plan.

---

## Why this overhaul

The current UI (single scrolling page: Today's Focus, Next Milestone, Context Sync, Morning Brief, Activity, Roadmap) has three problems: everything is flat body text with no hierarchy, so nothing signals what to do next; it mixes multiple concurrent workstreams (career pivot roadmap, PSS Data, Watchtower, interview prep) into one undifferentiated feed; and there's no way to focus on a single project without scrolling past the others.

The new structure fixes this by splitting "what am I working on" (project picker) from "what's the state of this one thing" (project detail), and by promoting the actionable "next steps" out of the log and into their own checklist at the top of each project.

---

## Information architecture

Three views, not one:

1. **Project picker** (home/landing view) — a grid of project cards, one per active workstream, each showing status, a one-line description, a key stat, and last-active time. Clicking a card opens that project's detail view.
2. **Project detail** — the per-project dashboard: current focus, up-next checklist, recent progress timeline, and (for the flagship project only) a roadmap stepper. A persistent "← All projects" link returns to the picker.
3. Optional stretch: a compact project switcher (dropdown from the header) so users can jump between projects without going back to the picker — not built in the mockups, but the data model below supports it.

---

## Design tokens

Pull these directly from the `<style>` block in any of the three mockup files — they're already consistent across all three.

**Typography**: Inter (400/500/600/700 weights), loaded from Google Fonts. Body copy 13.5–16.5px at line-height 1.5–1.7. Headings 17–22px, weight 600–700, letter-spacing -0.01em. Eyebrow labels 11.5–12px, weight 700, uppercase, letter-spacing 0.06em, in a muted or accent color depending on context.

**Neutral palette**:
- `--bg: #F7F7F5` (page background)
- `--surface: #FFFFFF` (card background)
- `--border: #E7E5E0`, `--border-strong: #D6D3CB`
- `--text-primary: #1C1B18`, `--text-secondary: #6B6862`, `--text-muted: #9C988F`

**Per-project accent colors** (used for icon chips, status pills, and focus-card backgrounds — pick by project category, not sequentially):
- Blue `#EAF2FC / #1D4E89 / #3378C4` — primary/on-track
- Coral `#FBEAE7 / #9C4A2E / #D2653F` — blocked/needs attention
- Teal `#E6F5F1 / #1F6F5C / #2F9C82` — in progress
- Purple `#F1EEFB / #5A4B96 / #7C6BC4` — warm/lower urgency
- Green solid `#4C9A5B` — completed states only (checkmarks, done dots)

**Layout**: cards use 16px border-radius, 1px `--border`, subtle `box-shadow: 0 1px 2px rgba(28,27,24,0.03)` (no heavier shadows). Small elements (icon chips, buttons) use 10–12px radius; pills use 20px (full round). Page max-width 920–960px, centered. Spacing scale in multiples of 2px between 8 and 28.

---

## Component breakdown

Build these as reusable components regardless of framework:

- **TopBar** — Forge wordmark/logo mark + current date. Same on every view.
- **BackLink** — "← All projects", only on project detail view.
- **ProjectCard** — used in the picker grid. Props: icon glyph, accent color set, name, subtitle, status label, 1–2 key stats, last-active string, click handler.
- **ProjectGrid** — responsive 2-column grid of ProjectCard, collapses to 1 column under ~640px, plus a dashed "+ New project" card at the end.
- **StatusPill** — colored pill, text/bg pulled from the project's accent set.
- **FocusCard** — large tinted card, eyebrow label + one paragraph of body text. This is the single most important piece of real estate on a project detail page — it should always answer "what do I do right now."
- **UpNextChecklist** — list of 2–3 actionable items, each with a circular checkbox affordance, a bold title, and a muted one-line detail. This replaces the old buried "Next:" bullets in Context Sync.
- **ProgressTimeline** — list of completed items, each with a filled green checkmark circle and a single line of text. This is where the old Context Sync "done" bullets go — kept short, one fact per line, no run-on sentences.
- **RoadmapStepper** — horizontal 5-step progress indicator with a connecting line, used only on the flagship career-pivot project (or wherever the overarching multi-stage plan lives).
- **StatChip** — small pill-shaped metric used in the stats row (e.g. "Open questions: 12").
- **ResourceList / ActivityHeatmap** — carried over from the original dashboard redesign (`forge-redesign.html`); reuse if the app still wants a single combined view for one primary project, otherwise fold ResourceList into a project's detail view as a fourth card.

---

## Data model

Both the picker and the detail view should read from one shared project object shape (see the `PROJECTS` object in `forge-project.html` for a working example):

```
Project {
  id: string
  name: string
  subtitle: string
  icon: string            // glyph or icon name
  accentBg, accentText, accentSolid: string   // one of the 4 accent sets above
  status: "On track" | "Blocked" | "In progress" | "Warm" | ...
  lastActive: string | Date
  stats: [ [label, value], ... ]
  focus: string            // current single most important thing to do
  focusMeta: string        // e.g. "30–60 min · Stage 1"
  upNext: [ { title, detail }, ... ]
  progress: [ string, ... ]   // completed items, most recent first
  roadmap?: [ { label, date, state: "done" | "current" | "todo" }, ... ]  // optional, flagship project only
}
```

This maps cleanly onto the current Context Sync data — the "done" bullets become `progress`, the "Next:" bullets get split across projects into each project's `upNext`, and Today's Focus / Next Milestone become `focus`/`focusMeta` and the roadmap's current stage.

---

## Migration steps (suggested order)

1. Introduce the design tokens (colors, type scale, radius, spacing) as CSS variables or a theme file, without touching layout yet.
2. Build ProjectCard + ProjectGrid and wire the picker view to real project data, even if there's only one project today — this validates the data model.
3. Build FocusCard, UpNextChecklist, ProgressTimeline, StatusPill, StatChip and assemble the project detail view, with routing (`/projects/:id` or equivalent) and a back link to the picker.
4. Split the existing single Context Sync feed into per-project `progress` and `upNext` arrays, and retire the old flat page.
5. Move RoadmapStepper onto whichever project represents the overarching plan.
6. Decide whether ResourceList/Morning Brief and ActivityHeatmap live on every project or only a default/home project, and place accordingly.

## Acceptance criteria

- From the picker, every project card is clickable and opens the correct project's detail view.
- Every project detail view has a working back link to the picker.
- The most urgent unresolved action for the currently open project is visible without scrolling (FocusCard + first UpNextChecklist item above the fold).
- No component relies on hardcoded copy — all content comes from the Project data model.
- Colors carry meaning consistently: coral only for blocked/attention states, green only for completed states, never used interchangeably.
