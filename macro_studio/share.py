"""매크로 코드 내보내기/가져오기 — JSON 스니펫 왕복."""

from __future__ import annotations

import json
import re
from typing import Any

from .models import MacroDocument, MacroEvent

_FENCE_RE = re.compile(r"```(?:json|python)?\s*([\s\S]*?)```", re.IGNORECASE)
_DICT_ASSIGN_RE = re.compile(
    r"(?:MACRO|macro|doc|data)\s*=\s*(\{[\s\S]*\})",
    re.IGNORECASE,
)


def document_to_portable_dict(doc: MacroDocument) -> dict[str, Any]:
    data = doc.to_dict()
    data["format"] = "macro-studio"
    data["format_version"] = 1
    return data


def export_json_snippet(doc: MacroDocument, *, fenced: bool = True) -> str:
    """복사 가능한 JSON 스니펫 (기본: 펜스 블록)."""
    text = json.dumps(document_to_portable_dict(doc), ensure_ascii=False, indent=2)
    if fenced:
        return f"```json\n{text}\n```"
    return text


def export_python_snippet(doc: MacroDocument) -> str:
    """작은 Python 할당 가능한 dict 스니펫."""
    text = json.dumps(document_to_portable_dict(doc), ensure_ascii=False, indent=2)
    return f"MACRO = {text}\n"


def _strip_python_noise(raw: str) -> str:
    s = raw.strip()
    m = _DICT_ASSIGN_RE.search(s)
    if m and s.lstrip().startswith(m.group(0)[:20].split("=")[0].strip()[:5] or "M"):
        pass
    if s.startswith("MACRO") or s.startswith("macro") or s.startswith("doc") or s.startswith("data"):
        m2 = _DICT_ASSIGN_RE.search(s)
        if m2:
            return m2.group(1)
    return s


def _extract_json_candidate(text: str) -> str:
    s = text.strip()
    if not s:
        raise ValueError("붙여넣은 텍스트가 비어 있습니다.")
    fence = _FENCE_RE.search(s)
    if fence:
        s = fence.group(1).strip()
    s = _strip_python_noise(s)
    start = s.find("{")
    end = s.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("JSON 객체({...})를 찾을 수 없습니다.")
    return s[start : end + 1]


def parse_import_text(text: str) -> MacroDocument:
    """펜스/JSON/MACRO=dict 텍스트 → MacroDocument. 이벤트 완전 보존."""
    candidate = _extract_json_candidate(text)
    try:
        data = json.loads(candidate)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON 파싱 실패: {e}") from e
    if not isinstance(data, dict):
        raise ValueError("최상위는 JSON 객체여야 합니다.")
    if "events" not in data:
        raise ValueError("'events' 배열이 필요합니다.")
    if not isinstance(data["events"], list):
        raise ValueError("'events'는 배열이어야 합니다.")
    events = [MacroEvent.from_dict(e) if isinstance(e, dict) else None for e in data["events"]]
    if any(e is None for e in events):
        raise ValueError("events 항목은 객체여야 합니다.")
    doc = MacroDocument.from_dict(data)
    doc.events = [e for e in events if e is not None]
    return doc
