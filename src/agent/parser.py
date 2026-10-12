from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class ParseResult:
    tool_calls: list[ToolCall] = field(default_factory=list)
    final_answer: str = ""
    error: str | None = None
    raw_payload: dict[str, Any] | None = None


def _extract_json_payload(text: str) -> str | None:
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped

    fenced = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    if fenced:
        return fenced.group(1)

    first = text.find("{")
    last = text.rfind("}")
    if first >= 0 and last > first:
        return text[first : last + 1]
    return None


def parse_agent_response(text: str) -> ParseResult:
    payload_text = _extract_json_payload(text)
    if not payload_text:
        return ParseResult(error="Response did not include a JSON object")

    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError as exc:
        return ParseResult(error=f"Invalid JSON: {exc}")

    if not isinstance(payload, dict):
        return ParseResult(error="Top-level response must be a JSON object")

    tool_calls_raw = payload.get("tool_calls", [])
    if tool_calls_raw is None:
        tool_calls_raw = []

    if not isinstance(tool_calls_raw, list):
        return ParseResult(error="tool_calls must be a list", raw_payload=payload)

    tool_calls: list[ToolCall] = []
    for idx, row in enumerate(tool_calls_raw):
        if not isinstance(row, dict):
            return ParseResult(error=f"tool_calls[{idx}] must be an object", raw_payload=payload)
        call_id = str(row.get("id", f"call_{idx + 1}"))
        name = row.get("name")
        arguments = row.get("arguments", {})
        if not isinstance(name, str) or not name:
            return ParseResult(error=f"tool_calls[{idx}].name must be a non-empty string", raw_payload=payload)
        if not isinstance(arguments, dict):
            return ParseResult(error=f"tool_calls[{idx}].arguments must be an object", raw_payload=payload)
        tool_calls.append(ToolCall(id=call_id, name=name, arguments=arguments))

    final_answer = payload.get("final_answer", "")
    if final_answer is None:
        final_answer = ""
    if not isinstance(final_answer, str):
        return ParseResult(error="final_answer must be a string", raw_payload=payload)

    return ParseResult(tool_calls=tool_calls, final_answer=final_answer, raw_payload=payload)
