"""LangChain morning brief chain: yesterday's session -> search -> LLM -> structured brief.

Flow: classify_session -> search -> generate -> parse. Persistence to the
`briefs` table is handled by the caller (api/services/brief_service.py); this
module is standalone and testable without the API/DB layer.
"""

import argparse
import json

from chain.llm_utils import get_llm, parse_json_response

ROADMAP = [
    {"stage": 1, "title": "Python + wrapper project", "target": "Aug 2026"},
    {"stage": 2, "title": "Memory + state", "target": "Sept 2026"},
    {"stage": 3, "title": "Ask PSS Data (text-to-SQL)", "target": "Oct 2026"},
    {"stage": 4, "title": "Agents + MCP", "target": "Nov 2026"},
    {"stage": 5, "title": "Ship to real users", "target": "Dec 2026"},
]


def roadmap_position(stages_complete: int = 0) -> dict:
    idx = min(stages_complete, len(ROADMAP) - 1)
    return ROADMAP[idx]


def classify_session(session: dict | None) -> list[str]:
    """Map session type + notes to 2-3 search queries."""
    if session is None:
        stage = roadmap_position()
        return [f"{stage['title']} tutorial 2026"]

    types = session.get("type", [])
    notes = session.get("notes", "") or ""
    queries = []

    if "python" in types:
        queries.append("python langchain tutorial 2026")
    if "project" in types:
        queries.append("AI engineer portfolio project ideas 2026")
    if "research" in types:
        queries.append(f"{notes[:60]} research 2026" if notes else "AI engineering research trends 2026")
    if "application" in types:
        queries.append("AI engineer job application tips 2026")

    if not queries:
        queries.append("AI engineering skills 2026")

    return queries[:3]


def search(queries: list[str], max_results: int = 3) -> list[dict]:
    """Run Tavily search per query, deduplicated by URL."""
    from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper

    # Use raw_results() rather than the TavilySearchResults tool / .results():
    # both go through clean_results(), which drops the title field Tavily
    # actually returns, keeping only url + content.
    wrapper = TavilySearchAPIWrapper()
    seen_urls: set[str] = set()
    results: list[dict] = []

    for query in queries:
        raw = wrapper.raw_results(query, max_results=max_results)
        for r in raw.get("results", []):
            url = r.get("url")
            if url and url not in seen_urls:
                seen_urls.add(url)
                results.append(r)

    return results


def build_prompt(session: dict | None, search_results: list[dict], stage: dict) -> str:
    session_text = (
        f"Yesterday's session: type={session['type']}, level={session['level']}, "
        f"notes=\"{session['notes']}\""
        if session
        else "No session was logged yesterday."
    )
    results_text = "\n".join(
        f"- {r.get('title')}: {r.get('url')}" for r in search_results
    ) or "(no search results)"

    return f"""You are a career coach helping a developer pivot to AI engineering.

{session_text}

Current roadmap position: Stage {stage['stage']} - {stage['title']} (target: {stage['target']})

Relevant research found:
{results_text}

Respond with ONLY a JSON object in this exact shape:
{{
  "summary": "1-2 sentence recap of yesterday (or roadmap status if nothing logged)",
  "focus": "one concrete, actionable recommendation for today",
  "research": [{{"title": "...", "url": "...", "reason": "why this is relevant"}}]
}}
Include at most 3 research items, drawn from the search results above."""


def generate_brief(session: dict | None, stages_complete: int = 0) -> dict:
    stage = roadmap_position(stages_complete)
    queries = classify_session(session)
    results = search(queries)

    prompt = build_prompt(session, results, stage)
    llm = get_llm()
    response = llm.invoke(prompt)

    return parse_json_response(response.content)


def _main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scheduled", action="store_true")
    parser.parse_args()

    from sqlmodel import Session

    from api.db.database import engine, init_db
    from api.services.brief_service import generate_and_save_brief

    init_db()
    with Session(engine) as session:
        brief = generate_and_save_brief(session)
        print(json.dumps({"date": brief.date, "summary": brief.summary, "focus": brief.focus}))


if __name__ == "__main__":
    _main()
