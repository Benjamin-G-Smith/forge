"""Context-sync chain: read the Ember vault's career-pivot note and synthesize
Forge's own understanding of roadmap stage + milestone state.

Read-only — never writes back to the vault. Persistence of the proposed
snapshot (and applying it to the official tracked state) is handled by the
caller (api/services/context_service.py); this module is standalone.
"""

import os
from pathlib import Path

from chain.llm_utils import get_llm, parse_json_response
from chain.morning_brief import ROADMAP

VAULT_CAREER_PIVOT_PATH = Path(
    os.environ.get(
        "VAULT_CAREER_PIVOT_PATH",
        "/Users/bensmith/Documents/ember-vault/projects/career-pivot.md",
    )
)

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


def read_vault_note() -> str | None:
    if not VAULT_CAREER_PIVOT_PATH.exists():
        return None
    return VAULT_CAREER_PIVOT_PATH.read_text()


def build_prompt(vault_text: str, current_stage: int, current_milestones: dict[str, bool]) -> str:
    roadmap_text = "\n".join(f"{r['stage']}: {r['title']}" for r in ROADMAP)
    milestones_text = "\n".join(f"- {key}: {label}" for key, label in MILESTONE_LABELS.items())
    current_milestones_text = "\n".join(
        f"- {key}: {'done' if current_milestones.get(key) else 'not done'}"
        for key in MILESTONE_LABELS
    )

    return f"""You are reconciling a career-tracker app's state against the user's own notes.

Forge's 5-stage roadmap:
{roadmap_text}

Forge's tracked milestones:
{milestones_text}

Forge's CURRENT tracked state:
- Stage: {current_stage}
- Milestones:
{current_milestones_text}

The user's own notes (from their Obsidian vault, career-pivot.md — this is their
real source of truth, more current and detailed than what Forge has tracked so far):

---
{vault_text}
---

Based on the notes, determine what Forge's tracked state SHOULD be. Only mark a
milestone or stage complete if the notes give clear, concrete evidence (a shipped
artifact, a stated completion) — do not guess or infer from vague language.

Respond with ONLY a JSON object in this exact shape:
{{
  "summary": "2-3 sentence synthesis of where things actually stand right now",
  "next_action": "the single most important next step, from the notes",
  "proposed_stage": <int 0-5>,
  "proposed_milestones": {{"<key>": true|false, ...}},
  "reasoning": "1-2 sentences on what changed vs Forge's current tracked state, if anything"
}}"""


def synthesize_context(current_stage: int, current_milestones: dict[str, bool]) -> dict:
    vault_text = read_vault_note()
    if vault_text is None:
        return {
            "summary": f"No vault note found at {VAULT_CAREER_PIVOT_PATH}.",
            "next_action": "",
            "proposed_stage": current_stage,
            "proposed_milestones": current_milestones,
            "reasoning": "",
        }

    prompt = build_prompt(vault_text, current_stage, current_milestones)
    llm = get_llm()
    response = llm.invoke(prompt)

    return parse_json_response(response.content)
