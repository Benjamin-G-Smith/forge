"""Project-sync chain: read a vault note (plus any notes it [[wikilinks]] to)
and synthesize Forge's understanding of that project's current focus, up-next
steps, and recent progress — and, for the flagship project only, the overall
roadmap stage + milestone state.

Read-only — never writes back to the vault. Persistence of the proposed
snapshot (and applying it to tracked state) is handled by the caller
(api/services/project_service.py); this module is standalone.
"""

import os
import re
from pathlib import Path

from chain.llm_utils import get_llm, parse_json_response
from chain.morning_brief import ROADMAP

VAULT_PROJECTS_DIR = Path(
    os.environ.get(
        "VAULT_PROJECTS_DIR",
        os.environ.get(
            "VAULT_CAREER_PIVOT_PATH",
            "/Users/bensmith/Documents/ember-vault/projects/career-pivot.md",
        ),
    )
).parent

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)")

# Mirrors frontend/src/milestones.js — there's no existing backend-side
# canonical milestone list since rows are created ad hoc by migrate.py/PATCH.
MILESTONE_LABELS = {
    "stage1_shipped": "Stage 1 shipped",
    "building_in_public": "Building in public",
    "eval_harness_coded": "Eval harness coded",
    "first_post_published": "First post published",
    "ten_apps_sent": "10 applications sent",
    "pss_public_url": "PSS Data public URL",
    "second_project_shipped": "Second project shipped",
}


def read_vault_note(vault_note_path: Path) -> str | None:
    if not vault_note_path.exists():
        return None
    return vault_note_path.read_text()


def read_linked_notes(vault_note_path: Path, vault_text: str) -> list[tuple[str, str]]:
    """Notes the given note [[wikilinks]] to, one level deep, that exist on disk."""
    names = dict.fromkeys(m.strip() for m in WIKILINK_RE.findall(vault_text))
    notes = []
    for name in names:
        path = vault_note_path.parent / f"{name}.md"
        if path.exists():
            notes.append((name, path.read_text()))
    return notes


def _flagship_block(flagship_context: dict | None) -> tuple[str, str]:
    """Returns (context_block, response_fields) for the flagship-only roadmap/milestone ask."""
    if flagship_context is None:
        return "", ""

    current_stage = flagship_context["current_stage"]
    current_milestones = flagship_context["current_milestones"]
    roadmap_text = "\n".join(f"{r['stage']}: {r['title']}" for r in ROADMAP)
    milestones_text = "\n".join(f"- {key}: {label}" for key, label in MILESTONE_LABELS.items())
    current_milestones_text = "\n".join(
        f"- {key}: {'done' if current_milestones.get(key) else 'not done'}"
        for key in MILESTONE_LABELS
    )

    context_block = f"""
This is Forge's flagship project — it also tracks an overarching 5-stage roadmap:
{roadmap_text}

Forge's tracked milestones:
{milestones_text}

Forge's CURRENT tracked state:
- Stage: {current_stage}
- Milestones:
{current_milestones_text}

Only mark a milestone or stage complete if the notes give clear, concrete evidence
(a shipped artifact, a stated completion) — do not guess or infer from vague language.
"""
    response_fields = """,
  "proposed_stage": <int 0-5>,
  "proposed_milestones": {"<key>": true|false, ...}"""
    return context_block, response_fields


def build_prompt(
    vault_text: str,
    linked_notes: list[tuple[str, str]] | None = None,
    flagship_context: dict | None = None,
) -> str:
    linked_notes_text = "\n\n".join(
        f"### Linked note: {name}\n---\n{text}\n---" for name, text in (linked_notes or [])
    )
    linked_notes_block = (
        f"\nThis note links to the following notes — treat them as part of the same "
        f"source of truth, especially for concrete evidence of shipped work:\n\n{linked_notes_text}\n"
        if linked_notes_text
        else ""
    )
    flagship_context_block, flagship_response_fields = _flagship_block(flagship_context)

    return f"""You are reconciling a project-tracker app's state against the user's own notes.
{flagship_context_block}
The user's own notes (from their Obsidian vault — this is their real source of
truth, more current and detailed than what Forge has tracked so far):

---
{vault_text}
---
{linked_notes_block}
Be concrete, not generic. Name specific artifacts, files, dates, and blockers as they
appear in the notes — "log_analytics.py, review_aggregator.py shipped" beats "made
progress." Every bullet/list item is a single short clause, max ~12 words — a fact
plus its evidence, not a full sentence with sub-clauses. Cut connective tissue
("which shows that...", "this means..."). If a fact needs more than 12 words, split
it into two items or drop the less important half.

Respond with ONLY a JSON object in this exact shape. The item counts and length caps
are hard limits, not suggestions — pick only the most important items and cut the
rest, don't try to fit everything in:
{{
  "status": "On track" | "Blocked" | "In progress" | "Warm",
  "focus": "1-2 sentences: the single most important thing to do right now, concrete and actionable",
  "focus_meta": "max 4 words, e.g. 'Blocked · waiting on IT' or '30-60 min today'",
  "stats": [["label", "value"], ["label", "value"]] — EXACTLY 2 entries, no more,
  "up_next": [{{"title": "...", "detail": "..."}}, ...] — EXACTLY 2 or 3 entries, no more,
  "progress": ["...", "..."] — EXACTLY 2 to 4 entries, no more, most recent/important first{flagship_response_fields}
}}"""


def synthesize_project(vault_note_path: Path, flagship_context: dict | None = None) -> dict:
    vault_text = read_vault_note(vault_note_path)
    if vault_text is None:
        fallback = {
            "status": "Warm",
            "focus": f"No vault note found at {vault_note_path}.",
            "focus_meta": "",
            "stats": [],
            "up_next": [],
            "progress": [],
        }
        if flagship_context is not None:
            fallback["proposed_stage"] = flagship_context["current_stage"]
            fallback["proposed_milestones"] = flagship_context["current_milestones"]
        return fallback

    linked_notes = read_linked_notes(vault_note_path, vault_text)
    prompt = build_prompt(vault_text, linked_notes, flagship_context)
    llm = get_llm()
    response = llm.invoke(prompt)

    return parse_json_response(response.content)
