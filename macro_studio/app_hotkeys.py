"""전역 핫키 F9/F10/Esc · Ctrl+1~0."""

from __future__ import annotations

from pynput import keyboard


class HotkeysUIMixin:
    """MacroStudioApp 믹스인 — 전역 핫키 리스너."""

    def _start_global_hotkeys(self) -> None:
        def on_press(key: keyboard.Key | keyboard.KeyCode) -> None:
            try:
                if key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
                    self._ctrl_held = True
                    return
                if key == keyboard.Key.f9:
                    self.after(0, self._toggle_record)
                    return
                if key == keyboard.Key.f10:
                    if self._player.is_playing:
                        self.after(0, self._abort_play)
                    else:
                        self.after(0, self._play)
                    return
                if self._ctrl_held and isinstance(key, keyboard.KeyCode):
                    ordinal = None
                    ch = key.char
                    if ch and ch in "1234567890":
                        ordinal = 10 if ch == "0" else int(ch)
                    elif getattr(key, "vk", None) is not None:
                        vk = int(key.vk)
                        if 49 <= vk <= 57:
                            ordinal = vk - 48
                        elif vk == 48:
                            ordinal = 10
                        elif 97 <= vk <= 105:
                            ordinal = vk - 96
                        elif vk == 96:
                            ordinal = 10
                    if ordinal is not None:
                        self.after(0, lambda o=ordinal: self._select_slot_hotkey(o))
            except Exception:
                pass

        def on_release(key: keyboard.Key | keyboard.KeyCode) -> None:
            try:
                if key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
                    self._ctrl_held = False
            except Exception:
                pass

        self._hotkey_listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        self._hotkey_listener.daemon = True  # type: ignore[attr-defined]
        self._hotkey_listener.start()
