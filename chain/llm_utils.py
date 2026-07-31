"""Shared LLM plumbing for the chain modules: model selection + JSON parsing."""

import json
import os


def get_llm():
    if os.environ.get("GOOGLE_API_KEY") and not os.environ.get("ANTHROPIC_API_KEY"):
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(model="gemini-1.5-flash")

    from langchain_anthropic import ChatAnthropic

    return ChatAnthropic(model="claude-haiku-4-5")


def parse_json_response(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        text = text.removeprefix("json").strip()
    return json.loads(text)
