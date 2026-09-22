"""이벤트 목록 · 편집 · 범위 삭제 · 잘라내기/복사/붙여넣기 · N번부터 재생 · 좌표."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

from .models import EventType, MacroEvent

EVENT_TYPES = [
    EventType.CLICK.value,
    EventType.SCROLL.value,
    EventType.KEY.value,
    EventType.MOVE.value,
    EventType.WAIT.value,
]


class EventsUIMixin:
    """MacroStudioApp 에 믹스인 — 이벤트 에디터/클립보드/재생-from/좌표."""

    _event_clipboard: list[MacroEvent]

    def _build_event_editor(self, parent: ctk.CTkFrame) -> None:
        self._event_clipboard = []
        parent.grid_columnconfigure(0, weight=3)
        parent.grid_columnconfigure(1, weight=2)
        parent.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(parent, text="이벤트 목록 (편집) — 동작 1, 2, 3…", font=ctk.CTkFont(size=15, weight="bold")).grid(
            row=0, column=0, padx=8, pady=(8, 4), sticky="w"
        )

        list_frame = ctk.CTkFrame(parent)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=(8, 4), pady=8)
        list_frame.grid_rowconfigure(1, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        cols_header = ctk.CTkLabel(
            list_frame,
            text="동작#   유형          지연(ms)     상세",
            anchor="w",
            font=ctk.CTkFont(family="Consolas", size=12),
        )
        cols_header.grid(row=0, column=0, sticky="ew", padx=4, pady=(4, 0))

        self.event_listbox = tk.Listbox(
            list_frame,
            exportselection=False,
            font=("Consolas", 11),
            activestyle="dotbox",
        )
        self.event_listbox.grid(row=1, column=0, sticky="nsew", padx=4, pady=4)
        self.event_listbox.bind("<<ListboxSelect>>", self._on_event_select)

        range_bar = ctk.CTkFrame(list_frame, fg_color="transparent")
        range_bar.grid(row=2, column=0, sticky="ew", padx=4, pady=(0, 4))
        ctk.CTkLabel(range_bar, text="범위:").pack(side="left", padx=(0, 4))
        self.range_from_var = ctk.StringVar(value="1")
        self.range_to_var = ctk.StringVar(value="1")
        ctk.CTkEntry(range_bar, textvariable=self.range_from_var, width=40).pack(side="left", padx=1)
        ctk.CTkLabel(range_bar, text="~").pack(side="left")
        ctk.CTkEntry(range_bar, textvariable=self.range_to_var, width=40).pack(side="left", padx=1)
        ctk.CTkLabel(range_bar, text="번").pack(side="left", padx=(0, 4))
        ctk.CTkButton(
            range_bar, text="범위 삭제", command=self._delete_range, width=72, height=26, fg_color="#a33", hover_color="#822"
        ).pack(side="left", padx=1)

        clip_bar = ctk.CTkFrame(list_frame, fg_color="transparent")
        clip_bar.grid(row=3, column=0, sticky="ew", padx=4, pady=(0, 8))
        ctk.CTkButton(clip_bar, text="잘라내기", command=self._cut_range, width=72, height=26).pack(side="left", padx=1)
        ctk.CTkButton(clip_bar, text="복사", command=self._copy_range, width=56, height=26).pack(side="left", padx=1)
        ctk.CTkButton(clip_bar, text="붙여넣기", command=self._paste_events, width=72, height=26).pack(side="left", padx=1)
        ctk.CTkLabel(clip_bar, text="(선택 위치 앞 / 없으면 끝)", font=ctk.CTkFont(size=11)).pack(side="left", padx=6)

        edit_panel = ctk.CTkFrame(parent)
        edit_panel.grid(row=1, column=1, sticky="nsew", padx=(4, 8), pady=8)
        edit_panel.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(edit_panel, text="선택 이벤트 편집", font=ctk.CTkFont(size=14, weight="bold")).grid(
            row=0, column=0, columnspan=2, padx=8, pady=(8, 10), sticky="w"
        )

        self._edit_vars: dict[str, ctk.StringVar] = {}
        fields = [
            ("type", "유형"),
            ("delay_ms", "지연 ms"),
            ("x", "X"),
            ("y", "Y"),
            ("button", "버튼"),
            ("action", "액션"),
            ("dx", "dx"),
            ("dy", "dy"),
            ("key", "키"),
            ("monitor", "모니터#"),
        ]
        for row_i, (key, label) in enumerate(fields, start=1):
            ctk.CTkLabel(edit_panel, text=label).grid(row=row_i, column=0, padx=8, pady=2, sticky="w")
            var = ctk.StringVar(value="")
            self._edit_vars[key] = var
            if key == "type":
                entry: ctk.CTkBaseClass = ctk.CTkOptionMenu(
                    edit_panel, variable=var, values=EVENT_TYPES, width=160
                )
            else:
                entry = ctk.CTkEntry(edit_panel, textvariable=var)
            entry.grid(row=row_i, column=1, padx=8, pady=2, sticky="ew")

        apply_btn = ctk.CTkButton(edit_panel, text="필드 적용", command=self._apply_edit)
        apply_btn.grid(row=len(fields) + 1, column=0, columnspan=2, padx=8, pady=(10, 4), sticky="ew")

        ctk.CTkButton(
            edit_panel,
            text="현재 마우스 위치로 X/Y 채우기",
            command=self._fill_xy_from_cursor,
        ).grid(row=len(fields) + 2, column=0, columnspan=2, padx=8, pady=4, sticky="ew")

        reorder = ctk.CTkFrame(edit_panel, fg_color="transparent")
        reorder.grid(row=len(fields) + 3, column=0, columnspan=2, padx=4, pady=4, sticky="ew")
        for i in range(2):
            reorder.grid_columnconfigure(i, weight=1)
        ctk.CTkButton(reorder, text="▲ 위로", command=self._move_up, height=30).grid(
            row=0, column=0, padx=4, pady=2, sticky="ew"
        )
        ctk.CTkButton(reorder, text="▼ 아래로", command=self._move_down, height=30).grid(
            row=0, column=1, padx=4, pady=2, sticky="ew"
        )
        ctk.CTkButton(edit_panel, text="삭제", command=self._delete_event, fg_color="#a33", hover_color="#822").grid(
            row=len(fields) + 4, column=0, columnspan=2, padx=8, pady=4, sticky="ew"
        )
        ctk.CTkButton(edit_panel, text="+ 대기(Wait) 삽입", command=self._insert_wait).grid(
            row=len(fields) + 5, column=0, columnspan=2, padx=8, pady=(4, 12), sticky="ew"
        )

    def _build_play_from_controls(self, parent: ctk.CTkFrame) -> None:
        play_from = ctk.CTkFrame(parent, fg_color="transparent")
        play_from.grid(row=0, column=3, padx=4, pady=4, sticky="ew")
        ctk.CTkLabel(play_from, text="부터").grid(row=0, column=2, padx=(2, 0))
        self.play_from_var = ctk.StringVar(value="1")
        self.play_from_entry = ctk.CTkEntry(play_from, textvariable=self.play_from_var, width=48)
        self.play_from_entry.grid(row=0, column=0, padx=2)
        ctk.CTkLabel(play_from, text="번").grid(row=0, column=1, padx=0)
        ctk.CTkButton(play_from, text="N번부터 재생", command=self._play_from, width=110, height=28).grid(
            row=0, column=3, padx=4
        )

    def _play_from(self) -> None:
        try:
            n = int(self.play_from_var.get().strip() or "1")
        except ValueError:
            messagebox.showerror("재생", "시작 동작 번호가 올바르지 않습니다.")
            return
        self._start_play(start_1based=n)

    def _format_row(self, idx0: int, ev: MacroEvent) -> str:
        n = idx0 + 1
        return f"동작 {n:<3d}  {ev.type:<10}  {ev.delay_ms:>8}   {ev.details_text()}"

    def _refresh_event_list(self, select: int | None = None) -> None:
        self.event_listbox.delete(0, tk.END)
        for i, ev in enumerate(self._doc.events):
            self.event_listbox.insert(tk.END, self._format_row(i, ev))
        if self._doc.events:
            self.range_to_var.set(str(len(self._doc.events)))
        else:
            self.range_from_var.set("1")
            self.range_to_var.set("1")
        if select is not None and 0 <= select < len(self._doc.events):
            self.event_listbox.selection_clear(0, tk.END)
            self.event_listbox.selection_set(select)
            self.event_listbox.see(select)
            self._selected_index = select
            self._load_edit_fields(self._doc.events[select])
        elif not self._doc.events:
            self._selected_index = None

    def _on_event_select(self, _event: object | None = None) -> None:
        sel = self.event_listbox.curselection()
        if not sel:
            self._selected_index = None
            return
        idx = int(sel[0])
        self._selected_index = idx
        if 0 <= idx < len(self._doc.events):
            self._load_edit_fields(self._doc.events[idx])
            self.range_from_var.set(str(idx + 1))
            self.range_to_var.set(str(idx + 1))
            self.play_from_var.set(str(idx + 1))

    def _load_edit_fields(self, ev: MacroEvent) -> None:
        mapping = {
            "type": ev.type,
            "delay_ms": str(ev.delay_ms),
            "x": "" if ev.x is None else str(ev.x),
            "y": "" if ev.y is None else str(ev.y),
            "button": ev.button or "",
            "action": ev.action or "",
            "dx": "" if ev.dx is None else str(ev.dx),
            "dy": "" if ev.dy is None else str(ev.dy),
            "key": ev.key or "",
            "monitor": "" if ev.monitor is None else str(ev.monitor),
        }
        for k, v in mapping.items():
            self._edit_vars[k].set(v)

    def _optional_int(self, raw: str) -> int | None:
        raw = raw.strip()
        if raw == "":
            return None
        return int(raw)

