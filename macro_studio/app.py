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
from .ui_slots import SlotsUIMixin
from .ui_slots_ops import SlotsOpsUIMixin

APP_TITLE = "매크로 스튜디오 (Macro Studio)"

class MacroStudioApp(SlotsUIMixin, SlotsOpsUIMixin, ShareUIMixin, ClipboardUIMixin, EventsUIMixin, EventsEditUIMixin, HotkeysUIMixin, ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")

        self.title(APP_TITLE)
        self.geometry("1180x780")
        self.minsize(960, 640)

        self._current_slot: int = 1
        self._doc = MacroDocument.empty_for_slot(1)
        self._dirty = False
        self._selected_index: int | None = None
        self._ctrl_held = False
        self._slot_ids: list[int] = []
        self._event_clipboard: list[MacroEvent] = []

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
        first = (self._slot_ids[0] if self._slot_ids else 1)
        self._load_slot_into_editor(first, confirm_dirty=False)
        self._start_global_hotkeys()
        self._poll_mouse_status()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        left = ctk.CTkFrame(self, width=260)
        left.grid(row=0, column=0, sticky="nsew", padx=(12, 6), pady=12)
        self._build_left_slot_panel(left)

        right = ctk.CTkFrame(self)
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 12), pady=12)
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(3, weight=1)

        meta = ctk.CTkFrame(right)
        meta.grid(row=0, column=0, sticky="ew", padx=8, pady=(8, 4))
        meta.grid_columnconfigure(1, weight=1)

        self.slot_badge = ctk.CTkLabel(
            meta,
            text="현재 슬롯: 1번",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.slot_badge.grid(row=0, column=0, columnspan=2, padx=8, pady=(6, 2), sticky="w")

        ctk.CTkLabel(meta, text="이름").grid(row=1, column=0, padx=8, pady=6, sticky="w")
        self.name_entry = ctk.CTkEntry(meta, placeholder_text="매크로 이름")
        self.name_entry.grid(row=1, column=1, padx=8, pady=6, sticky="ew")
        self.name_entry.insert(0, self._doc.name)

        ctk.CTkLabel(meta, text="설명").grid(row=2, column=0, padx=8, pady=6, sticky="w")
        self.desc_entry = ctk.CTkEntry(meta, placeholder_text="설명 (선택)")
        self.desc_entry.grid(row=2, column=1, padx=8, pady=6, sticky="ew")

        self.status_label = ctk.CTkLabel(
            meta,
            text="대기 중 — F9 녹화 / F10 재생 / Ctrl+1~0 앞 슬롯",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.status_label.grid(row=3, column=0, columnspan=2, padx=8, pady=(4, 4), sticky="w")

        self.mouse_label = ctk.CTkLabel(
            meta,
            text="마우스 (—, —)",
            font=ctk.CTkFont(size=12),
            text_color="#888",
        )
        self.mouse_label.grid(row=4, column=0, columnspan=2, padx=8, pady=(0, 4), sticky="w")

        self.rec_indicator = ctk.CTkLabel(
            meta,
            text="",
            text_color="#e33",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.rec_indicator.grid(row=5, column=0, columnspan=2, padx=8, pady=(0, 8), sticky="w")

        controls = ctk.CTkFrame(right)
        controls.grid(row=1, column=0, sticky="ew", padx=8, pady=4)
        for i in range(7):
            controls.grid_columnconfigure(i, weight=1)

        self.btn_record = ctk.CTkButton(
            controls, text="● 녹화 시작 (F9)", command=self._toggle_record, fg_color="#c33", hover_color="#a22"
        )
        self.btn_record.grid(row=0, column=0, padx=4, pady=8, sticky="ew")

        self.btn_play = ctk.CTkButton(controls, text="▶ 재생 (F10)", command=self._play)
        self.btn_play.grid(row=0, column=1, padx=4, pady=8, sticky="ew")

        self.btn_abort = ctk.CTkButton(
            controls, text="■ 중단 (Esc)", command=self._abort_play, fg_color="#555", hover_color="#444"
        )
        self.btn_abort.grid(row=0, column=2, padx=4, pady=8, sticky="ew")

        self.btn_save = ctk.CTkButton(controls, text="💾 슬롯 저장", command=self._save)
        self.btn_save.grid(row=0, column=3, padx=4, pady=8, sticky="ew")

        self.btn_new = ctk.CTkButton(
            controls, text="슬롯 초기화", command=self._new_macro, fg_color="#555", hover_color="#444"
        )
        self.btn_new.grid(row=0, column=4, padx=4, pady=8, sticky="ew")

        self.move_var = ctk.BooleanVar(value=False)
        self.move_check = ctk.CTkCheckBox(
            controls,
            text="마우스 이동 녹화",
            variable=self.move_var,
            command=self._sync_move_option,
        )
        self.move_check.grid(row=0, column=5, padx=8, pady=8, sticky="w")

        self._build_play_from_controls(controls)

        hint = ctk.CTkLabel(
            right,
            text="녹화 중지 후 이벤트 목록을 편집하세요. 디스크 저장은 [슬롯 저장]을 눌렀을 때만 수행됩니다. "
            "잘라내기/복사/붙여넣기로 동작을 원하는 위치에 옮길 수 있습니다. "
            "좌표는 가상 데스크톱 절대좌표(멀티 모니터)입니다.",
            font=ctk.CTkFont(size=12),
            wraplength=860,
            justify="left",
        )
        hint.grid(row=2, column=0, sticky="w", padx=12, pady=(0, 4))

        editor = ctk.CTkFrame(right)
        editor.grid(row=3, column=0, sticky="nsew", padx=8, pady=8)
        self._build_event_editor(editor)

    def _poll_mouse_status(self) -> None:
        try:
            self.mouse_label.configure(text=monitors.mouse_status_text())
        except Exception:
            pass
        self.after(250, self._poll_mouse_status)

    def _set_status(self, text: str) -> None:
        self.status_label.configure(text=text)

    def _sync_move_option(self) -> None:
        self._recorder.record_mouse_move = bool(self.move_var.get())

    def _mark_dirty(self) -> None:
        self._dirty = True

    def _toggle_record(self) -> None:
        if self._player.is_playing:
            self._set_status("재생 중에는 녹화할 수 없습니다.")
            return
        self._sync_move_option()
        if self._recorder.is_recording:
            events = self._recorder.stop()
            self._doc.events = list(events)
            self._mark_dirty()
            self._refresh_event_list()
            self.rec_indicator.configure(text="")
            self.btn_record.configure(text="● 녹화 시작 (F9)")
            self._set_status(f"녹화 중지 — {len(events)}개 이벤트. 목록을 편집한 뒤 [슬롯 저장]하세요.")
            messagebox.showinfo(
                "녹화 완료",
                f"{len(events)}개 이벤트가 기록되었습니다.\n"
                "오른쪽 편집기에서 수정·잘라내기/붙여넣기·대기 삽입 후\n"
                f"[슬롯 저장]을 눌러 {self._current_slot}번 슬롯에 쓰세요.",
            )
        else:
            if self._doc.events:
                if not messagebox.askyesno("녹화 시작", "기존 이벤트 목록을 지우고 새로 녹화할까요?"):
                    return
            self._recorder.start()
            self.rec_indicator.configure(text="● 녹화 중… (F9로 중지)")
            self.btn_record.configure(text="■ 녹화 중지 (F9)")
            self._set_status("녹화 중 — 마우스/키보드 입력이 기록됩니다 (절대좌표).")

    def _on_record_event(self, _event: MacroEvent) -> None:
        def update() -> None:
            n = len(self._recorder.events)
            self.rec_indicator.configure(text=f"● 녹화 중… {n} events (F9로 중지)")

        self.after(0, update)

    def _on_record_state(self, recording: bool) -> None:
        def update() -> None:
            if recording:
                self.rec_indicator.configure(text="● 녹화 중… (F9로 중지)")
            else:
                self.rec_indicator.configure(text="")

        self.after(0, update)

    def _play(self) -> None:
        self._start_play(start_1based=1)

    def _start_play(self, *, start_1based: int) -> None:
        if self._recorder.is_recording:
            self._set_status("녹화 중에는 재생할 수 없습니다.")
            return
        if self._player.is_playing:
            return
        if not self._doc.events:
            messagebox.showwarning("재생", "재생할 이벤트가 없습니다.")
            return
        if start_1based < 1 or start_1based > len(self._doc.events):
            messagebox.showwarning(
                "재생",
                f"시작 번호는 1~{len(self._doc.events)} 사이여야 합니다.",
            )
            return
        start_idx = start_1based - 1
        if start_1based == 1:
            self._set_status("재생 준비 — 3초 카운트다운… (Esc/F10 중단)")
        else:
            self._set_status(f"{start_1based}번부터 재생 준비 — 3초 카운트다운… (Esc/F10 중단)")
        self._player.play(self._doc.events, loop=False, start_index=start_idx)

    def _abort_play(self) -> None:
        if self._player.is_playing:
            self._player.abort()
            self._set_status("재생 중단 요청…")

    def _on_countdown(self, remaining: int) -> None:
        def update() -> None:
            if remaining > 0:
                self._set_status(f"재생 카운트다운: {remaining}… (Esc/F10 중단)")
            else:
                self._set_status("재생 중… (Esc/F10 중단)")

        self.after(0, update)

    def _on_play_progress(self, current: int, total: int) -> None:
        def update() -> None:
            self._set_status(f"재생 중… 동작 {current}/{total} (Esc/F10 중단)")

        self.after(0, update)

    def _on_play_finished(self, aborted: bool) -> None:
        def update() -> None:
            if aborted:
                self._set_status("재생이 중단되었습니다.")
            else:
                self._set_status("재생 완료 (1회).")

        self.after(0, update)

    def _on_play_state(self, playing: bool) -> None:
        def update() -> None:
            state = "disabled" if playing else "normal"
            try:
                self.btn_record.configure(state=state)
                self.btn_save.configure(state=state)
            except Exception:
                pass

        self.after(0, update)

    def _on_close(self) -> None:
        if self._recorder.is_recording:
            self._recorder.stop()
        if self._player.is_playing:
            self._player.abort()
        if self._hotkey_listener is not None:
            try:
                self._hotkey_listener.stop()
            except Exception:
                pass
        if self._dirty:
            if not messagebox.askyesno("종료", "저장하지 않은 변경이 있습니다. 종료할까요?"):
                return
        self.destroy()


def run_app() -> None:
    storage.ensure_macros_dir()
    app = MacroStudioApp()
    app.mainloop()
