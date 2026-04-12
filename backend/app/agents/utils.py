"""Shared utility functions for agent nodes."""

import json
import re


def extract_json(text: str) -> dict | list:
    """
    Robustly extract the first valid JSON object or array from a string.

    Handles:
    - Clean JSON (direct parse)
    - Markdown code fences (```json ... ```)
    - Extra text after valid JSON (thinking tokens bleeding through)
    - Whitespace padding

    Raises ValueError if no valid JSON can be extracted.
    """
    if not text:
        raise ValueError("Empty response text")

    # 1. Try direct parse first (the happy path)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 2. Strip markdown code fences
    stripped = re.sub(r"```(?:json)?\s*", "", text).strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # 3. Use raw_decode to stop at first complete object — ignores trailing content
    decoder = json.JSONDecoder()
    for start_char, start_idx in [("{", stripped.find("{")), ("[", stripped.find("["))]:
        if start_idx == -1:
            continue
        try:
            obj, _ = decoder.raw_decode(stripped, start_idx)
            return obj
        except json.JSONDecodeError:
            continue

    raise ValueError(f"No valid JSON found in response. First 200 chars: {text[:200]!r}")


def unwrap_list(value: dict | list) -> dict:
    """If the LLM wrapped its response in a list, unwrap the first element."""
    if isinstance(value, list):
        return value[0] if value else {}
    return value
