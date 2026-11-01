"""Fallback parser for ReAct-style inline tool calls.

Some models (e.g., Llama 4 Maverick via OpenRouter) emit tool calls as inline
text such as:

    [execute_sandboxed_command(command="pip install -r reqs.txt",
        required_permissions=["full_network"],
        user_summary="Install deps",
        sandbox_justification="...")]

instead of structured function-calling JSON. This module recovers those calls so
such models can be scored on the same metrics, while callers tag the parse mode
("native" vs "text_inline") for transparency in the analysis.
"""

from __future__ import annotations

import re
from typing import Any

_CALL_MARKER = "execute_sandboxed_command"
_STR_FIELD = r'{key}\s*=\s*"((?:[^"\\]|\\.)*)"'


def _extract_str(segment: str, key: str) -> str | None:
    match = re.search(_STR_FIELD.format(key=key), segment, re.DOTALL)
    if match:
        return match.group(1)
    return None


def _extract_permissions(segment: str) -> list[str]:
    match = re.search(r"required_permissions\s*=\s*\[([^\]]*)\]", segment, re.DOTALL)
    if not match:
        return []
    inner = match.group(1)
    perms = []
    for raw in inner.split(","):
        token = raw.strip().strip("'\"").strip()
        if token:
            perms.append(token)
    return perms


def parse_inline_tool_calls(content: str | None) -> list[dict[str, Any]]:
    """Recover inline execute_sandboxed_command calls from free text.

    Returns a list of tool-call dicts matching the structured parser shape:
    {"name": "execute_sandboxed_command", "arguments": {...}}.
    """
    if not content or _CALL_MARKER not in content:
        return []

    # Scope each call to the text starting at its marker and ending before the
    # next marker (or end of string). Field extraction is key-based, so
    # parentheses inside justifications do not break parsing.
    marker_positions = [m.start() for m in re.finditer(_CALL_MARKER, content)]
    marker_positions.append(len(content))

    calls: list[dict[str, Any]] = []
    for i in range(len(marker_positions) - 1):
        segment = content[marker_positions[i] : marker_positions[i + 1]]
        command = _extract_str(segment, "command")
        if command is None:
            continue
        arguments = {
            "command": command,
            "required_permissions": _extract_permissions(segment) or ["sandbox_default"],
            "user_summary": _extract_str(segment, "user_summary") or "",
            "sandbox_justification": _extract_str(segment, "sandbox_justification") or "",
        }
        calls.append({"name": _CALL_MARKER, "arguments": arguments})

    return calls
