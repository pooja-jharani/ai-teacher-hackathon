"""
Thin, provider-agnostic LLM wrapper. Every other module calls `chat()` or
`chat_json()` and doesn't care whether Anthropic or OpenAI is configured.
"""
from __future__ import annotations
import json
import re
import time
from typing import Optional

import config


def _anthropic_client():
    import anthropic
    if not config.ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY is not set. Add it to your .env file.")
    return anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


def _openai_client():
    import openai
    if not config.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to your .env file.")
    return openai.OpenAI(api_key=config.OPENAI_API_KEY)


def _gemini_client():
    from google import genai
    if not config.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set. Add it to your .env file. "
                            "Get a free key at https://aistudio.google.com/apikey")
    return genai.Client(api_key=config.GEMINI_API_KEY)


def chat(system: str, user: str, max_tokens: int = 1500, temperature: float = 0.4) -> str:
    """Send a single-turn system+user prompt, return raw text response.
    Retries a few times with backoff on transient server overload (503),
    which happens occasionally on free-tier Gemini during peak demand."""
    last_error = None
    for attempt in range(4):
        try:
            return _chat_once(system, user, max_tokens, temperature)
        except Exception as e:
            is_overloaded = "503" in str(e) or "UNAVAILABLE" in str(e) or "overloaded" in str(e).lower()
            if is_overloaded and attempt < 3:
                wait = 2 ** attempt  # 1s, 2s, 4s
                print(f"  (model overloaded, retrying in {wait}s...)")
                time.sleep(wait)
                last_error = e
                continue
            raise
    raise last_error


def _chat_once(system: str, user: str, max_tokens: int, temperature: float) -> str:
    if config.LLM_PROVIDER == "anthropic":
        client = _anthropic_client()
        resp = client.messages.create(
            model=config.ANTHROPIC_MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return "".join(block.text for block in resp.content if block.type == "text")

    elif config.LLM_PROVIDER == "openai":
        client = _openai_client()
        resp = client.chat.completions.create(
            model=config.OPENAI_MODEL,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return resp.choices[0].message.content or ""

    elif config.LLM_PROVIDER == "gemini":
        client = _gemini_client()
        from google.genai import types
        resp = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=user,
            config=types.GenerateContentConfig(
                system_instruction=system,
                max_output_tokens=max_tokens,
                temperature=temperature,
            ),
        )
        return resp.text or ""

    raise ValueError(f"Unknown LLM_PROVIDER: {config.LLM_PROVIDER}")


def _extract_json(text: str) -> str:
    """Strips markdown code fences if the model wrapped its JSON output."""
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        return fence.group(1).strip()
    return text


def chat_json(system: str, user: str, max_tokens: int = 2000, temperature: float = 0.3) -> dict:
    """
    Calls chat() with an instruction to return ONLY JSON, then parses it.
    Retries once with a stricter instruction if parsing fails.
    """
    json_system = system + "\n\nIMPORTANT: Respond with ONLY valid JSON. No preamble, no markdown fences, no commentary."
    raw = chat(json_system, user, max_tokens=max_tokens, temperature=temperature)
    try:
        return json.loads(_extract_json(raw))
    except json.JSONDecodeError:
        retry_user = user + "\n\nYour previous response was not valid JSON. Return ONLY a valid JSON object, nothing else."
        raw2 = chat(json_system, retry_user, max_tokens=max_tokens, temperature=0.1)
        return json.loads(_extract_json(raw2))
