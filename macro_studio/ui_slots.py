"""동적 슬롯 UI — 추가/삭제/복제/이름 · Ctrl+1~0(앞 10개) · 코드 가져오기."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

from . import storage
from .models import MacroDocument


class SlotsUIMixin:
    """MacroStudioApp 에 믹스인 — 슬롯 목록/로드/저장/추가/삭제/복제."""

    # listbox index → slot number
    _slot_ids: list[int]

    def _build_left_slot_panel(self, parent: ctk.CTkFrame) -> None:
        parent.grid_propagate(False)
        parent.grid_rowconfigure(2, weight=1)
        self._slot_ids = []

        ctk.CTkLabel(parent, text="매크로 슬롯", font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, padx=12, pady=(12, 4), sticky="w"
        )
        ctk.CTkLabel(
            parent,
            text=f"저장: {storage.MACROS_DIR}/slot_NN.json\n"
            "슬롯 추가·삭제·복제 가능 · Ctrl+1~0 = 앞 10개",
            font=ctk.CTkFont(size=11),
            wraplength=230,
            justify="left",
        ).grid(row=1, column=0, padx=12, pady=(0, 4), sticky="w")

        self.slot_listbox = tk.Listbox(
            parent,
            exportselection=False,
            activestyle="dotbox",
            font=("Segoe UI", 11),
            height=16,
        )
        self.slot_listbox.grid(row=2, column=0, sticky="nsew", padx=12, pady=4)
        self.slot_listbox.bind("<<ListboxSelect>>", self._on_slot_select)
        self.slot_listbox.bind("<Double-Button-1>", lambda _e: self._load_selected_slot())

        btn_row = ctk.CTkFrame(parent, fg_color="transparent")
        btn_row.grid(row=3, column=0, padx=8, pady=8, sticky="ew")
        for i in range(2):
            btn_row.grid_columnconfigure(i, weight=1)

        ctk.CTkButton(btn_row, text="슬롯 추가", command=self._add_slot, height=30).grid(
            row=0, column=0, padx=2, pady=2, sticky="ew"
        )
        ctk.CTkButton(btn_row, text="슬롯 복제", command=self._duplicate_slot, height=30).grid(
            row=0, column=1, padx=2, pady=2, sticky="ew"
        )
        ctk.CTkButton(btn_row, text="슬롯 불러오기", command=self._load_selected_slot, height=30).grid(
            row=1, column=0, columnspan=2, padx=2, pady=2, sticky="ew"
        )
        ctk.CTkButton(
            btn_row, text="슬롯 삭제", command=self._delete_selected_slot, height=30, fg_color="#a33", hover_color="#822"
        ).grid(row=2, column=0, padx=2, pady=2, sticky="ew")
        ctk.CTkButton(
            btn_row, text="슬롯 비우기", command=self._clear_selected_slot, height=30, fg_color="#a33", hover_color="#822"
        ).grid(row=2, column=1, padx=2, pady=2, sticky="ew")
        ctk.CTkButton(btn_row, text="코드로 내보내기", command=self._export_code, height=30).grid(
            row=3, column=0, padx=2, pady=2, sticky="ew"
        )
        ctk.CTkButton(btn_row, text="코드 붙여넣기", command=self._import_code, height=30).grid(
            row=3, column=1, padx=2, pady=2, sticky="ew"
        )
        ctk.CTkButton(btn_row, text="목록 새로고침", command=self._refresh_slot_list, height=28).grid(
            row=4, column=0, columnspan=2, padx=2, pady=2, sticky="ew"
        )

    def _select_slot_hotkey(self, ordinal: int) -> None:
        """Ctrl+1…0 → 목록의 1~10번째 슬롯(있을 때만)."""
        if self._recorder.is_recording or self._player.is_playing:
            self._set_status("녹화/재생 중에는 슬롯을 바꿀 수 없습니다.")
            return
        ids = list(self._slot_ids) or storage.ensure_at_least_one_slot()
        if ordinal < 1 or ordinal > len(ids) or ordinal > 10:
            self._set_status(f"빠른 슬롯 {ordinal}번(목록 앞쪽)이 없습니다.")
            return
        slot = ids[ordinal - 1]
        self._refresh_slot_list(select=slot)
        self._load_slot_into_editor(slot, confirm_dirty=True)

    def _collect_meta(self) -> None:
        self._doc.name = self.name_entry.get().strip() or f"{self._current_slot}번 매크로"
        self._doc.description = self.desc_entry.get().strip()
        self._doc.slot = self._current_slot

    def _update_slot_badge(self) -> None:
        self.slot_badge.configure(text=f"현재 슬롯: {self._current_slot}번")

    def _refresh_slot_list(self, select: int | None = None) -> None:
        keep = select if select is not None else self._current_slot
        summaries = storage.list_slot_summaries()
        self._slot_ids = [n for n, _lab, _d in summaries]
        self.slot_listbox.delete(0, tk.END)
        for _n, label, _doc in summaries:
            self.slot_listbox.insert(tk.END, label)
        if keep in self._slot_ids:
            idx = self._slot_ids.index(keep)
            self.slot_listbox.selection_clear(0, tk.END)
            self.slot_listbox.selection_set(idx)
            self.slot_listbox.see(idx)

    def _selected_slot_number(self) -> int | None:
        sel = self.slot_listbox.curselection()
        if not sel:
            return None
        i = int(sel[0])
        if 0 <= i < len(self._slot_ids):
            return self._slot_ids[i]
        return None

    def _on_slot_select(self, _event: object | None = None) -> None:
        slot = self._selected_slot_number()
        if slot is None or slot == self._current_slot:
            return
        if self._recorder.is_recording or self._player.is_playing:
            self._refresh_slot_list(select=self._current_slot)
            self._set_status("녹화/재생 중에는 슬롯을 바꿀 수 없습니다.")
            return
        self._load_slot_into_editor(slot, confirm_dirty=True)

    def _load_selected_slot(self) -> None:
        slot = self._selected_slot_number()
        if slot is None:
            messagebox.showinfo("슬롯", "왼쪽에서 슬롯을 선택하세요.")
            return
        self._load_slot_into_editor(slot, confirm_dirty=True)

    def _load_slot_into_editor(self, slot: int, *, confirm_dirty: bool) -> None:
        if confirm_dirty and self._dirty and slot != self._current_slot:
            if not messagebox.askyesno("슬롯 불러오기", "저장하지 않은 변경이 있습니다. 불러올까요?"):
                self._refresh_slot_list(select=self._current_slot)
                return
        doc = storage.load_slot(slot)
        if doc is None:
            doc = MacroDocument.empty_for_slot(slot)
        self._current_slot = slot
        self._doc = doc
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, doc.name)
        self.desc_entry.delete(0, tk.END)
        self.desc_entry.insert(0, doc.description)
        self._dirty = False
        self.play_from_var.set("1")
        self._update_slot_badge()
        self._refresh_event_list()
        self._refresh_slot_list(select=slot)
        self._set_status(f"{slot}번 슬롯 로드 — {doc.summary()}")
