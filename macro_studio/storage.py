"""매크로 JSON 저장/불러오기 — 고정 슬롯(1~10) + 이름 기반 호환."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .models import MacroDocument

# 패키지 기준이 아니라 프로젝트 루트의 macros/ 사용
_PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = _PACKAGE_DIR.parent
MACROS_DIR = PROJECT_ROOT / "macros"

SLOT_COUNT = 10
_SAFE_NAME = re.compile(r"^[A-Za-z0-9가-힣_\- .()]+$")


def ensure_macros_dir() -> Path:
    MACROS_DIR.mkdir(parents=True, exist_ok=True)
    return MACROS_DIR


def _validate_slot(slot: int) -> int:
    n = int(slot)
    if n < 1 or n > SLOT_COUNT:
        raise ValueError(f"슬롯 번호는 1~{SLOT_COUNT} 이어야 합니다 (받은 값: {slot}).")
    return n


def slot_filename(slot: int) -> str:
    n = _validate_slot(slot)
    return f"slot_{n:02d}.json"


def path_for_slot(slot: int) -> Path:
    return ensure_macros_dir() / slot_filename(slot)


def load_slot(slot: int) -> MacroDocument | None:
    """슬롯 파일 로드. 없거나 비어 있으면 None."""
    path = path_for_slot(slot)
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    doc = MacroDocument.from_dict(data)
    doc.slot = _validate_slot(slot)
    if not doc.name:
        doc.name = f"{slot}번 매크로"
    return doc


def save_slot(slot: int, doc: MacroDocument) -> Path:
    """현재 문서를 지정 슬롯 파일에 저장."""
    n = _validate_slot(slot)
    doc.slot = n
    path = path_for_slot(n)
    ensure_macros_dir()
    text = json.dumps(doc.to_dict(), ensure_ascii=False, indent=2)
    path.write_text(text, encoding="utf-8")
    return path


def clear_slot(slot: int) -> None:
    """슬롯 파일 삭제(비우기)."""
    path = path_for_slot(slot)
    if path.exists():
        path.unlink()


def slot_label(slot: int, doc: MacroDocument | None = None) -> str:
    """UI용 슬롯 라벨: '1번 매크로 — 이름' 또는 '1번 매크로 (비어있음)'."""
    n = _validate_slot(slot)
    if doc is None:
        doc = load_slot(n)
    if doc is None or not doc.events:
        # 파일은 있지만 이벤트 없고 기본 이름만이면 비어있음으로 표시
        if doc is None:
            return f"{n}번 매크로 (비어있음)"
        name = (doc.name or "").strip()
        default = f"{n}번 매크로"
        if not name or name == default:
            return f"{n}번 매크로 (비어있음)"
        return f"{n}번 매크로 — {name}"
    name = (doc.name or "").strip() or f"{n}번 매크로"
    if name == f"{n}번 매크로":
        return f"{n}번 매크로 ({len(doc.events)}개)"
    return f"{n}번 매크로 — {name}"


def list_slot_summaries() -> list[tuple[int, str, MacroDocument | None]]:
    """[(slot, label, doc_or_None), ...] 항상 SLOT_COUNT개."""
    result: list[tuple[int, str, MacroDocument | None]] = []
    for n in range(1, SLOT_COUNT + 1):
        doc = load_slot(n)
        result.append((n, slot_label(n, doc), doc))
    return result


# ── 이름 기반 API (호환 유지) ─────────────────────────────────

def _safe_filename(name: str) -> str:
    name = name.strip()
    if not name:
        raise ValueError("매크로 이름이 비어 있습니다.")
    if not _SAFE_NAME.match(name):
        raise ValueError("이름에 사용할 수 없는 문자가 있습니다.")
    return f"{name}.json"


def path_for(name: str) -> Path:
    return ensure_macros_dir() / _safe_filename(name)


def list_macros() -> list[str]:
    """이름 기반 목록 — slot_XX.json 제외."""
    ensure_macros_dir()
    names: list[str] = []
    for p in sorted(MACROS_DIR.glob("*.json")):
        if re.match(r"^slot_\d{2}$", p.stem):
            continue
        names.append(p.stem)
    return names


def save_macro(doc: MacroDocument, overwrite: bool = True) -> Path:
    path = path_for(doc.name)
    if path.exists() and not overwrite:
        raise FileExistsError(f"이미 존재합니다: {path.name}")
    ensure_macros_dir()
    text = json.dumps(doc.to_dict(), ensure_ascii=False, indent=2)
    path.write_text(text, encoding="utf-8")
    return path


def load_macro(name: str) -> MacroDocument:
    path = path_for(name)
    if not path.exists():
        raise FileNotFoundError(f"매크로를 찾을 수 없습니다: {name}")
    data = json.loads(path.read_text(encoding="utf-8"))
    doc = MacroDocument.from_dict(data)
    if not doc.name:
        doc.name = name
    return doc


def delete_macro(name: str) -> None:
    path = path_for(name)
    if path.exists():
        path.unlink()


def rename_macro(old_name: str, new_name: str) -> Path:
    old_path = path_for(old_name)
    if not old_path.exists():
        raise FileNotFoundError(f"매크로를 찾을 수 없습니다: {old_name}")
    new_path = path_for(new_name)
    if new_path.exists():
        raise FileExistsError(f"이미 존재합니다: {new_name}")
    doc = load_macro(old_name)
    doc.name = new_name.strip()
    save_macro(doc, overwrite=True)
    old_path.unlink(missing_ok=True)
    return new_path
