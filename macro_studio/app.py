"""Macro Studio — customtkinter 한국어 UI."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog

import customtkinter as ctk
from pynput import keyboard, mouse

from .models import EventType, MacroDocument, MacroEvent
from .player import MacroPlayer
from .recorder import MacroRecorder
from . import storage

APP_TITLE = "매크로 스튜디오 (Macro Studio)"
EVENT_TYPES = [
    EventType.CLICK.value,
    EventType.SCROLL.value,
    EventType.KEY.value,
    EventType.MOVE.value,
    EventType.WAIT.value,
]


class MacroStudioApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.title(APP_TITLE)
        self.geometry("1180x760")
        self.minsize(960, 640)

        self._current_slot: int = 1
        self._doc = MacroDocument.empty_for_slot(1)
        self._dirty = False
        self._selected_index: int | None = None
        self._ctrl_held = False

        self._recorder = MacroRecorder(
            record_mouse_move=False,
            on_event=self._on_record_event,
            on_state_change=self._on_record_state,
        )
        self._player = MacroPlayer(
            countdown_seconds=3,
            on_countdown=self._on_countdown,
            on_progress=self._on_play_progress,
            on_finished=self._on_play_finished,
            on_state_change=self._on_play_state,
        )

        self._hotkey_listener: keyboard.Listener | None = None
        self._build_ui()
        self._refresh_slot_list(select=1)
        self._load_slot_into_editor(1, confirm_dirty=False)
        self._start_global_hotkeys()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
