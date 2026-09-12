"""멀티 모니터 — 가상 데스크톱 절대 좌표 + 모니터 인덱스.

pynput 마우스 좌표는 OS 가상 데스크톱(모든 모니터를 잇는 전역) 절대 좌표입니다.
재생도 동일 절대 좌표를 사용하므로, 레이아웃이 같으면 화면 1·2 어디서든 동작합니다.
레이아웃이 바뀌면 UI의 [현재 마우스 위치로 X/Y 채우기]로 재지정하세요.
"""

from __future__ import annotations

from typing import Any

from pynput import mouse

_screens_cache: list[Any] | None = None
_screens_ok = False


def _load_screens() -> list[Any]:
    global _screens_cache, _screens_ok
    if _screens_ok:
        return _screens_cache or []
    _screens_ok = True
    try:
        from screeninfo import get_monitors  # type: ignore[import-untyped]

        _screens_cache = list(get_monitors())
    except Exception:
        _screens_cache = []
    return _screens_cache or []


def refresh_monitors() -> list[Any]:
    global _screens_cache, _screens_ok
    _screens_ok = False
    _screens_cache = None
    return _load_screens()


def monitor_count() -> int:
    return len(_load_screens())


def monitor_index_at(x: int, y: int) -> int | None:
    """절대 좌표 (x,y)가 속한 모니터 인덱스(0-based). 없으면 None."""
    screens = _load_screens()
    for i, m in enumerate(screens):
        left = int(getattr(m, "x", 0))
        top = int(getattr(m, "y", 0))
        width = int(getattr(m, "width", 0))
        height = int(getattr(m, "height", 0))
        if left <= x < left + width and top <= y < top + height:
            return i
    return None


def mouse_position() -> tuple[int, int]:
    ctrl = mouse.Controller()
    x, y = ctrl.position
    return int(x), int(y)


def mouse_status_text() -> str:
    """UI용: '마우스 (x, y) · 모니터 N/M' 또는 모니터 미검출 시 좌표만."""
    try:
        x, y = mouse_position()
    except Exception:
        return "마우스: (읽기 실패)"
    idx = monitor_index_at(x, y)
    n = monitor_count()
    if idx is not None and n > 0:
        return f"마우스 ({x}, {y}) · 모니터 {idx + 1}/{n} (절대좌표)"
    if n > 0:
        return f"마우스 ({x}, {y}) · 모니터 ?/{n} (절대좌표)"
    return f"마우스 ({x}, {y}) · 절대좌표 (모니터 정보 없음)"


def annotate_monitor(x: int | None, y: int | None) -> int | None:
    if x is None or y is None:
        return None
    return monitor_index_at(int(x), int(y))
