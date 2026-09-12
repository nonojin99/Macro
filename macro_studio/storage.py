"""매크로 JSON 저장/불러오기 — 동적 슬롯(상한 없음) + 이름 기반 호환."""

from __future__ import annotations

import json
import re
from pathlib import Path

from .models import MacroDocument

_PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = _PACKAGE_DIR.parent
MACROS_DIR = PROJECT_ROOT / "macros"

# slot_1.json, slot_01.json, slot_100.json 모두 허용
_SLOT_STEM = re.compile(r"^slot_(\d+)$")
_SAFE_NAME = re.compile(r"^[A-Za-z0-9가-힣_\- .()]+$")
# 실용 상한(파일·UI 보호). 필요 시 조정 가능. 고정 1~10 제한은 제거됨.
MAX_SLOTS_SOFT = 500


def ensure_macros_dir() -> Path:
    MACROS_DIR.mkdir(parents=True, exist_ok=True)
    return MACROS_DIR


def _validate_slot(slot: int) -> int:
    n = int(slot)
    if n < 1 or n > MAX_SLOTS_SOFT:
        raise ValueError(f"슬롯 번호는 1~{MAX_SLOTS_SOFT} 이어야 합니다 (받은 값: {slot}).")
    return n


def slot_filename(slot: int) -> str:
    n = _validate_slot(slot)
    # 1~99: slot_01.json 형식 유지(기존 호환). 100+: slot_100.json
    if n < 100:
        return f"slot_{n:02d}.json"
    return f"slot_{n}.json"


def path_for_slot(slot: int) -> Path:
    return ensure_macros_dir() / slot_filename(slot)


def discover_slot_ids() -> list[int]:
    """macros/ 에서 slot_*.json 번호 목록 (정렬)."""
    ensure_macros_dir()
    ids: set[int] = set()
    for p in MACROS_DIR.glob("slot_*.json"):
        m = _SLOT_STEM.match(p.stem)
        if not m:
            continue
        try:
            n = int(m.group(1))
        except ValueError:
            continue
        if 1 <= n <= MAX_SLOTS_SOFT:
            ids.add(n)
    return sorted(ids)


def ensure_at_least_one_slot() -> list[int]:
    ids = discover_slot_ids()
    if not ids:
        # 디스크에 파일 없이 가상 1번만 — 저장 시 생성
        return [1]
    return ids


def next_slot_id() -> int:
    ids = discover_slot_ids()
    n = (max(ids) + 1) if ids else 1
    if n > MAX_SLOTS_SOFT:
        # 빈 번호 찾기
        for i in range(1, MAX_SLOTS_SOFT + 1):
            if i not in ids:
                return i
        raise ValueError(f"슬롯이 가득 찼습니다 (최대 {MAX_SLOTS_SOFT}).")
    return n


def load_slot(slot: int) -> MacroDocument | None:
    """슬롯 파일 로드. 없거나 비어 있으면 None."""
    path = path_for_slot(slot)
    # 레거시: slot_1.json vs slot_01.json — path_for_slot은 패딩 사용.
    # 패딩 없는 파일도 탐색
    if not path.exists():
        alt = ensure_macros_dir() / f"slot_{int(slot)}.json"
        if alt.exists():
            path = alt
        else:
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
    # 패딩 없는 중복 파일 정리
    alt = ensure_macros_dir() / f"slot_{n}.json"
    if alt != path and alt.exists() and n < 100:
        try:
            alt.unlink()
        except OSError:
            pass
    text = json.dumps(doc.to_dict(), ensure_ascii=False, indent=2)
    path.write_text(text, encoding="utf-8")
    return path


def clear_slot(slot: int) -> None:
    """슬롯 파일 삭제(비우기)."""
    n = _validate_slot(slot)
    for path in (path_for_slot(n), ensure_macros_dir() / f"slot_{n}.json"):
        if path.exists():
            path.unlink()


def delete_slot(slot: int) -> None:
    """슬롯 완전 삭제 (clear 와 동일, API 별칭)."""
    clear_slot(slot)


def duplicate_slot(slot: int) -> int:
    """슬롯을 새 번호로 복제. 이름에 '(복사)' 접미사. 반환: 새 슬롯 번호."""
    src = load_slot(slot)
    if src is None:
        src = MacroDocument.empty_for_slot(slot)
    new_id = next_slot_id()
    suffix = " (복사)"
    base = (src.name or f"{slot}번 매크로").strip()
    if not base.endswith(suffix):
        base = base + suffix
    new_doc = src.clone(new_slot=new_id, name_suffix="")
    new_doc.name = base
    new_doc.slot = new_id
    save_slot(new_id, new_doc)
    return new_id


def add_slot(name: str | None = None) -> int:
    """빈 슬롯 추가 후 번호 반환 (파일 즉시 생성)."""
    n = next_slot_id()
    doc = MacroDocument.empty_for_slot(n)
    if name and name.strip():
        doc.name = name.strip()
    save_slot(n, doc)
    return n


def slot_label(slot: int, doc: MacroDocument | None = None) -> str:
    """UI용 슬롯 라벨."""
    n = _validate_slot(slot)
    if doc is None:
        doc = load_slot(n)
    if doc is None or not doc.events:
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
    """[(slot, label, doc_or_None), ...] 동적 개수."""
    result: list[tuple[int, str, MacroDocument | None]] = []
    for n in ensure_at_least_one_slot():
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
        if _SLOT_STEM.match(p.stem):
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
