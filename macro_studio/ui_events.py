"""이벤트 목록 · 편집 · 범위 삭제 · N번부터 재생 · 커서 XY 채우기."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog

import customtkinter as ctk
from pynput import mouse

from .models import EventType, MacroEvent

EVENT_TYPES = [
    EventType.CLICK.value,
    EventType.SCROLL.value,
    EventType.KEY.value,
    EventType.MOVE.value,
    EventType.WAIT.value,
]


class EventsUIMixin:
    """MacroStudioApp 에 믹스인 — 이벤트 에디터/재생-from/좌표."""

    def _build_event_editor(self, parent: ctk.CTkFrame) -> None:
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
        range_bar.grid(row=2, column=0, sticky="ew", padx=4, pady=(0, 8))
        ctk.CTkLabel(range_bar, text="범위 삭제:").pack(side="left", padx=(0, 4))
        self.range_from_var = ctk.StringVar(value="1")
        self.range_to_var = ctk.StringVar(value="1")
        ctk.CTkEntry(range_bar, textvariable=self.range_from_var, width=44).pack(side="left", padx=2)
        ctk.CTkLabel(range_bar, text="~").pack(side="left")
        ctk.CTkEntry(range_bar, textvariable=self.range_to_var, width=44).pack(side="left", padx=2)
        ctk.CTkLabel(range_bar, text="번").pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            range_bar, text="범위 삭제", command=self._delete_range, width=90, height=28, fg_color="#a33", hover_color="#822"
        ).pack(side="left", padx=2)

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
        ]
        for row_i, (key, label) in enumerate(fields, start=1):
            ctk.CTkLabel(edit_panel, text=label).grid(row=row_i, column=0, padx=8, pady=3, sticky="w")
            var = ctk.StringVar(value="")
            self._edit_vars[key] = var
            if key == "type":
                entry: ctk.CTkBaseClass = ctk.CTkOptionMenu(
                    edit_panel, variable=var, values=EVENT_TYPES, width=160
                )
            else:
                entry = ctk.CTkEntry(edit_panel, textvariable=var)
            entry.grid(row=row_i, column=1, padx=8, pady=3, sticky="ew")

        apply_btn = ctk.CTkButton(edit_panel, text="필드 적용", command=self._apply_edit)
        apply_btn.grid(row=len(fields) + 1, column=0, columnspan=2, padx=8, pady=(12, 4), sticky="ew")

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
        play_from.grid(row=0, column=6, padx=4, pady=4, sticky="ew")
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
        }
        for k, v in mapping.items():
            self._edit_vars[k].set(v)

    def _optional_int(self, raw: str) -> int | None:
        raw = raw.strip()
        if raw == "":
            return None
        return int(raw)

    def _apply_edit(self) -> None:
        if self._selected_index is None:
            messagebox.showinfo("편집", "이벤트를 먼저 선택하세요.")
            return
        idx = self._selected_index
        try:
            delay = int(self._edit_vars["delay_ms"].get().strip() or "0")
            ev = MacroEvent(
                type=self._edit_vars["type"].get().strip() or EventType.WAIT.value,
                delay_ms=max(0, delay),
                x=self._optional_int(self._edit_vars["x"].get()),
                y=self._optional_int(self._edit_vars["y"].get()),
                button=(self._edit_vars["button"].get().strip() or None),
                action=(self._edit_vars["action"].get().strip() or None),
                dx=self._optional_int(self._edit_vars["dx"].get()),
                dy=self._optional_int(self._edit_vars["dy"].get()),
                key=(self._edit_vars["key"].get().strip() or None),
            )
        except ValueError:
            messagebox.showerror("편집", "숫자 필드 형식이 올바르지 않습니다.")
            return
        self._doc.events[idx] = ev
        self._mark_dirty()
        self._refresh_event_list(select=idx)
        self._set_status(f"동작 {idx + 1} 수정됨 (아직 디스크 미저장).")

    def _fill_xy_from_cursor(self) -> None:
        """현재 커서 좌표를 선택 이벤트(및 X/Y 필드)에 채운다."""
        if self._selected_index is None:
            messagebox.showinfo("좌표", "이벤트를 먼저 선택하세요.")
            return
        try:
            ctrl = mouse.Controller()
            x, y = ctrl.position
            x_i, y_i = int(x), int(y)
        except Exception as e:
            messagebox.showerror("좌표", f"마우스 위치를 읽을 수 없습니다: {e}")
            return
        self._edit_vars["x"].set(str(x_i))
        self._edit_vars["y"].set(str(y_i))
        idx = self._selected_index
        ev = self._doc.events[idx]
        if ev.type not in (
            EventType.CLICK.value,
            EventType.MOVE.value,
            EventType.SCROLL.value,
        ):
            self._set_status(f"커서 ({x_i}, {y_i}) — 필드에 채움. [필드 적용]을 누르세요.")
            messagebox.showinfo(
                "좌표",
                f"현재 마우스 위치 ({x_i}, {y_i}) 를 X/Y 필드에 넣었습니다.\n"
                f"선택 이벤트 유형은 '{ev.type}' 입니다. [필드 적용]으로 반영하세요.",
            )
            return
        ev.x = x_i
        ev.y = y_i
        self._mark_dirty()
        self._refresh_event_list(select=idx)
        self._set_status(f"동작 {idx + 1} 좌표 → ({x_i}, {y_i}) (아직 디스크 미저장).")

    def _delete_event(self) -> None:
        if self._selected_index is None:
            return
        idx = self._selected_index
        del self._doc.events[idx]
        self._mark_dirty()
        new_sel = min(idx, len(self._doc.events) - 1) if self._doc.events else None
        self._refresh_event_list(select=new_sel)
        self._set_status("이벤트 삭제됨 (아직 디스크 미저장).")

    def _delete_range(self) -> None:
        """1-based 포함 범위 A~B 삭제. 이후 동작이 앞으로 당겨짐."""
        if not self._doc.events:
            messagebox.showinfo("범위 삭제", "삭제할 이벤트가 없습니다.")
            return
        try:
            a = int(self.range_from_var.get().strip())
            b = int(self.range_to_var.get().strip())
        except ValueError:
            messagebox.showerror("범위 삭제", "시작/끝 번호가 올바르지 않습니다.")
            return
        if a > b:
            a, b = b, a
        n = len(self._doc.events)
        if a < 1 or b > n:
            messagebox.showwarning("범위 삭제", f"범위는 1~{n} 사이여야 합니다.")
            return
        if not messagebox.askyesno("범위 삭제", f"동작 {a}~{b} 를 삭제할까요? ({b - a + 1}개)"):
            return
        del self._doc.events[a - 1 : b]
        self._mark_dirty()
        new_sel = min(a - 1, len(self._doc.events) - 1) if self._doc.events else None
        self._refresh_event_list(select=new_sel)
        self._set_status(f"동작 {a}~{b} 삭제됨 (아직 디스크 미저장).")

    def _move_up(self) -> None:
        if self._selected_index is None or self._selected_index <= 0:
            return
        i = self._selected_index
        self._doc.events[i - 1], self._doc.events[i] = self._doc.events[i], self._doc.events[i - 1]
        self._mark_dirty()
        self._refresh_event_list(select=i - 1)

    def _move_down(self) -> None:
        if self._selected_index is None or self._selected_index >= len(self._doc.events) - 1:
            return
        i = self._selected_index
        self._doc.events[i + 1], self._doc.events[i] = self._doc.events[i], self._doc.events[i + 1]
        self._mark_dirty()
        self._refresh_event_list(select=i + 1)

    def _insert_wait(self) -> None:
        ms = simpledialog.askinteger("대기 삽입", "대기 시간 (ms):", minvalue=0, initialvalue=500, parent=self)
        if ms is None:
            return
        insert_at = (self._selected_index + 1) if self._selected_index is not None else len(self._doc.events)
        ev = MacroEvent(type=EventType.WAIT.value, delay_ms=int(ms))
        self._doc.events.insert(insert_at, ev)
        self._mark_dirty()
        self._refresh_event_list(select=insert_at)
        self._set_status(f"대기 {ms}ms 삽입됨 (아직 디스크 미저장).")
