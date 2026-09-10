"""매크로 재생 — 3초 카운트다운, Escape/F10 중단, 기본 1회 재생."""

from __future__ import annotations

import threading
import time
from typing import Callable

from pynput import keyboard, mouse
from pynput.keyboard import Key, KeyCode
from pynput.mouse import Button

from .models import EventType, MacroEvent

_BUTTON_MAP = {
    "left": Button.left,
    "right": Button.right,
    "middle": Button.middle,
}

_SPECIAL_KEYS: dict[str, Key] = {k.name: k for k in Key}  # type: ignore[attr-defined]


def _parse_key(key_str: str) -> Key | KeyCode:
    if key_str in _SPECIAL_KEYS:
        return _SPECIAL_KEYS[key_str]
    if key_str.startswith("vk_"):
        try:
            return KeyCode.from_vk(int(key_str[3:]))
        except ValueError:
            return KeyCode.from_char("?")
    if len(key_str) == 1:
        return KeyCode.from_char(key_str)
    # fallback: try special name
    return _SPECIAL_KEYS.get(key_str, KeyCode.from_char(key_str[:1] if key_str else "?"))


class MacroPlayer:
    """백그라운드 스레드에서 이벤트 재생."""

    def __init__(
        self,
        *,
        countdown_seconds: int = 3,
        on_countdown: Callable[[int], None] | None = None,
        on_progress: Callable[[int, int], None] | None = None,
        on_finished: Callable[[bool], None] | None = None,  # aborted?
        on_state_change: Callable[[bool], None] | None = None,
    ) -> None:
        self.countdown_seconds = countdown_seconds
        self.on_countdown = on_countdown
        self.on_progress = on_progress
        self.on_finished = on_finished
        self.on_state_change = on_state_change

        self._thread: threading.Thread | None = None
        self._abort = threading.Event()
        self._playing = False
        self._mouse = mouse.Controller()
        self._keyboard = keyboard.Controller()
        self._hotkey_listener: keyboard.Listener | None = None

    @property
    def is_playing(self) -> bool:
        return self._playing

    def abort(self) -> None:
        self._abort.set()

    def play(
        self,
        events: list[MacroEvent],
        *,
        loop: bool = False,
        start_index: int = 0,
    ) -> None:
        """재생 시작. 이미 재생 중이면 무시. loop 기본 False (무한 루프 없음).

        start_index: 0-based 시작 인덱스. 이전 이벤트는 건너뛴다.
        """
        if self._playing:
            return
        self._abort.clear()
        self._playing = True
        if self.on_state_change:
            self.on_state_change(True)

        self._hotkey_listener = keyboard.Listener(on_press=self._on_abort_key)
        self._hotkey_listener.start()

        start = max(0, min(int(start_index), len(events)))
        sliced = list(events)[start:]

        self._thread = threading.Thread(
            target=self._run,
            args=(sliced, loop, start),
            daemon=True,
        )
        self._thread.start()

    def _on_abort_key(self, key: Key | KeyCode) -> None:
        if key in (Key.esc, Key.f10):
            self.abort()

    def _run(self, events: list[MacroEvent], loop: bool, start_offset: int = 0) -> None:
        aborted = False
        try:
            # 카운트다운
            for remaining in range(self.countdown_seconds, 0, -1):
                if self._abort.is_set():
                    aborted = True
                    return
                if self.on_countdown:
                    try:
                        self.on_countdown(remaining)
                    except Exception:
                        pass
                time.sleep(1.0)
            if self.on_countdown:
                try:
                    self.on_countdown(0)
                except Exception:
                    pass

            while True:
                total = len(events)
                for idx, ev in enumerate(events):
                    if self._abort.is_set():
                        aborted = True
                        return
                    delay_s = max(0, ev.delay_ms) / 1000.0
                    # 대기는 작은 조각으로 쪼개 중단 가능하도록
                    end = time.perf_counter() + delay_s
                    while time.perf_counter() < end:
                        if self._abort.is_set():
                            aborted = True
                            return
                        time.sleep(min(0.02, end - time.perf_counter()))

                    if self._abort.is_set():
                        aborted = True
                        return

                    try:
                        self._execute(ev)
                    except Exception:
                        pass

                    if self.on_progress:
                        try:
                            # 원본 문서 기준 1-based 번호로 보고 (start_offset 반영)
                            self.on_progress(start_offset + idx + 1, start_offset + total)
                        except Exception:
                            pass

                if not loop or self._abort.is_set():
                    if self._abort.is_set():
                        aborted = True
                    break
        finally:
            self._playing = False
            if self._hotkey_listener is not None:
                try:
                    self._hotkey_listener.stop()
                except Exception:
                    pass
                self._hotkey_listener = None
            if self.on_state_change:
                try:
                    self.on_state_change(False)
                except Exception:
                    pass
            if self.on_finished:
                try:
                    self.on_finished(aborted)
                except Exception:
                    pass

    def _execute(self, ev: MacroEvent) -> None:
        t = ev.type
        if t == EventType.WAIT.value:
            return  # delay already applied
        if t == EventType.MOVE.value:
            if ev.x is not None and ev.y is not None:
                self._mouse.position = (ev.x, ev.y)
            return
        if t == EventType.CLICK.value:
            if ev.x is not None and ev.y is not None:
                self._mouse.position = (ev.x, ev.y)
            btn = _BUTTON_MAP.get(ev.button or "left", Button.left)
            if ev.action == "release":
                self._mouse.release(btn)
            else:
                self._mouse.press(btn)
            return
        if t == EventType.SCROLL.value:
            if ev.x is not None and ev.y is not None:
                self._mouse.position = (ev.x, ev.y)
            self._mouse.scroll(ev.dx or 0, ev.dy or 0)
            return
        if t == EventType.KEY.value:
            if not ev.key:
                return
            k = _parse_key(ev.key)
            if ev.action == "release":
                self._keyboard.release(k)
            else:
                self._keyboard.press(k)
            return
