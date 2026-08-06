"""Static config for Forge's tracked projects/workstreams.

Mirrors the pattern of ROADMAP in chain/morning_brief.py — a fixed, hand-edited
list rather than a DB table, since adding a project today is a code change
(the picker's "+ New project" card is a placeholder, not a real add-project flow).
"""

PROJECTS = [
    {
        "id": "career",
        "name": "Career pivot",
        "subtitle": "Python + wrapper project → ship to real users",
        "icon": "◎",
        "accent": "blue",
        "vault_note": "career-pivot.md",
        "flagship": True,
    },
    {
        "id": "pss",
        "name": "PSS Data",
        "subtitle": "Text-to-SQL architecture, fully specced and ready to build",
        "icon": "◫",
        "accent": "coral",
        "vault_note": "ask-pss-data.md",
        "flagship": False,
    },
    {
        "id": "watchtower",
        "name": "Watchtower",
        "subtitle": "Ember signal dashboard, live via Claude + web search",
        "icon": "◉",
        "accent": "teal",
        "vault_note": "ai-trends-radar.md",
        "flagship": False,
    },
    {
        "id": "interview",
        "name": "Interview prep",
        "subtitle": "STAR stories drafted from CCTS work",
        "icon": "✦",
        "accent": "purple",
        "vault_note": "ccts-star-stories.md",
        "flagship": False,
    },
]

PROJECTS_BY_ID = {p["id"]: p for p in PROJECTS}
