"""Macro Studio — customtkinter 한국어 UI 셸."""

from __future__ import annotations

from tkinter import messagebox

import customtkinter as ctk
from pynput import keyboard

from . import monitors, storage
from .models import MacroDocument, MacroEvent
from .player import MacroPlayer
from .recorder import MacroRecorder
from .ui_clipboard import ClipboardUIMixin
from .ui_events import EventsUIMixin
from .ui_events_edit import EventsEditUIMixin
from .app_hotkeys import HotkeysUIMixin
from .ui_share import ShareUIMixin
from .ui_slots import SpotsUIMixin
from .ui_slots_ops import SlotsOpsUIMixin

APP_TITLE = "매크로 스튜디오 (Macro Studio)"


class MacroStudioApp(SlotsUIMixin, SlotsOpsUIMixin, ShareUIMixin, ClipboardUIMixin, EventsUIMixin, EventsEditUIMixin, HotkeysUIMixin, ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
