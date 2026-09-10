"""마우스/키보드 이벤트 녹화 (Record 모드에서만)."""

from __future__ import annotations

import threading
import time
from typing import Callable

from pynput import keyboard, mouse

from .models import EventType, MacroEvent

# 앱 자체 핫키 — 녹화에서 제외
_HOTKEY_VK = {
    keyboard.Key.f9,
    keyboard.Key.f10,
    keyboard.Key.esc,
}


def _key_to_str(key: keyboard.Key | keyboard.KeyCode) -> str:
    if isinstance(key, keyboard.KeyCode):
        if key.char is not None:
            return key.char
        if key.vk is not None:
            return f"vk_{key.vk}"
        return "unknown"
    # Special keys: Key.space -> "space"
    name = str(key)
    if name.startswith("Key."):
        return name[4:]
    return name


def _button_to_str(button: mouse.Button) -> str:
    mapping = {
        mouse.Button.left: "left",
        mouse.Button.right: "right",
        mouse.Button.middle: "middle",
    }
    return mapping.get(button, str(button).replace("Button.", ""))


class MacroRecorder:
    """pynput 리스너로 이벤트를 수집한다.

    mouse_move 샘플링은 기본 OFF. record_mouse_move=True 일 때만
    move_sample_interval_ms 간격으로 좌표를 기록한다.
    """

    def __init__(
        self,
        *,
        record_mouse_move: bool = False,
        move_sample_interval_ms: int = 50,
        on_event: Callable[[MacroEvent], None] | None = None,
        on_state_change: Callable[[bool], None] | None = None,
    ) -> None:
        self.record_mouse_move = record_mouse_move
        self.move_sample_interval_ms = max(10, int(move_sample_interval_ms))
        self.on_event = on_event
        self.on_state_change = on_state_change

        self._events: list[MacroEvent] = []
        self._recording = False
        self._lock = threading.Lock()
        self._last_ts: float | None = None
        self._last_move_ts: float = 0.0

        self._mouse_listener: mouse.Listener | None = None
        self._keyboard_listener: keyboard.Listener | None = None

    @property
    def is_recording(self) -> bool:
        return self._recording

    @property
    def events(self) -> list[MacroEvent]:
        with self._lock:
            return list(self._events)

    def clear(self) -> None:
        with self._lock:
            self._events.clear()
            self._last_ts = None

    def start(self) -> None:
        if self._recording:
            return
        with self._lock:
            self._events.clear()
            self._last_ts = time.perf_counter()
            self._last_move_ts = 0.0
            self._recording = True

        self._mouse_listener = mouse.Listener(
            on_click=self._on_click,
            on_scroll=self._on_scroll,
            on_move=self._on_move if self.record_mouse_move else None,
        )
        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._mouse_listener.start()
        self._keyboard_listener.start()
        if self.on_state_change:
            self.on_state_change(True)

    def stop(self) -> list[MacroEvent]:
        if not self._recording:
            return self.events
        self._recording = False
        for listener in (self._mouse_listener, self._keyboard_listener):
            if listener is not None:
                try:
                    listener.stop()
                except Exception:
                    pass
        self._mouse_listener = None
        self._keyboard_listener = None
        if self.on_state_change:
            self.on_state_change(False)
        return self.events

    def toggle(self) -> bool:
        if self._recording:
            self.stop()
            return False
        self.start()
        return True

    def _elapsed_ms(self) -> int:
        now = time.perf_counter()
        if self._last_ts is None:
            self._last_ts = now
            return 0
        ms = int((now - self._last_ts) * 1000)
        self._last_ts = now
        return max(0, ms)

    def _append(self, event: MacroEvent) -> None:
        with self._lock:
            if not self._recording:
                return
            self._events.append(event)
        if self.on_event:
            try:
                self.on_event(event)
            except Exception:
                pass

    def _on_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        if not self._recording:
            return
        delay = self._elapsed_ms()
        ev = MacroEvent(
            type=EventType.CLICK.value,
            delay_ms=delay,
            x=int(x),
            y=int(y),
            button=_button_to_str(button),
            action="press" if pressed else "release",
        )
        self._append(ev)

    def _on_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        if not self._recording:
            return
        delay = self._elapsed_ms()
        ev = MacroEvent(
            type=EventType.SCROLL.value,
            delay_ms=delay,
            x=int(x),
            y=int(y),
            dx=int(dx),
            dy=int(dy),
        )
        self._append(ev)

    def _on_move(self, x: int, y: int) -> None:
        if not self._recording or not self.record_mouse_move:
            return
        now = time.perf_counter()
        if (now - self._last_move_ts) * 1000 < self.move_sample_interval_ms:
            return
        self._last_move_ts = now
        delay = self._elapsed_ms()
        ev = MacroEvent(
            type=EventType.MOVE.value,
            delay_ms=delay,
            x=int(x),
            y=int(y),
        )
        self._append(ev)

    def _is_hotkey(self, key: keyboard.Key | keyboard.KeyCode) -> bool:
        return key in _HOTKEY_VK

    def _on_press(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        if not self._recording or self._is_hotkey(key):
            return
        delay = self._elapsed_ms()
        ev = MacroEvent(
            type=EventType.KEY.value,
            delay_ms=delay,
            key=_key_to_str(key),
            action="press",
        )
        self._append(ev)

    def _on_release(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        if not self._recording or self._is_hotkey(key):
            return
        delay = self._elapsed_ms()
        ev = MacroEvent(
            type=EventType.KEY.value,
            delay_ms=delay,
            key=_key_to_str(key),
            action="release",
        )
        self._append(ev)
