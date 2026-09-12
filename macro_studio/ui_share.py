"""코드로 내보내기 / 붙여넣어 가져오기 다이얼로그."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

from . import storage
from .share import export_json_snippet, parse_import_text


class ShareUIMixin:
    """MacroStudioApp 믹스인 — 공유 스니펫 I/O."""

    def _export_code(self) -> None:
        self._collect_meta()
        snippet = export_json_snippet(self._doc, fenced=True)
        dlg = ctk.CTkToplevel(self)
        dlg.title("코드로 내보내기")
        dlg.geometry("560x480")
        dlg.transient(self)
        ctk.CTkLabel(dlg, text="아래 JSON을 복사해 다른 PC/슬롯에 붙여넣으세요.", wraplength=520).pack(
            padx=12, pady=(12, 4), anchor="w"
        )
        box = ctk.CTkTextbox(dlg, font=ctk.CTkFont(family="Consolas", size=12))
        box.pack(fill="both", expand=True, padx=12, pady=8)
        box.insert("1.0", snippet)

        def copy_all() -> None:
            try:
                self.clipboard_clear()
                self.clipboard_append(snippet)
                self._set_status("내보내기 코드를 클립보드에 복사했습니다.")
            except Exception as e:
                messagebox.showerror("복사", str(e))

        ctk.CTkButton(dlg, text="전체 복사", command=copy_all).pack(padx=12, pady=(0, 12))

    def _import_code(self) -> None:
        if self._recorder.is_recording or self._player.is_playing:
            self._set_status("녹화/재생 중에는 가져올 수 없습니다.")
            return
        dlg = ctk.CTkToplevel(self)
        dlg.title("코드/텍스트 붙여넣어 가져오기")
        dlg.geometry("560x480")
        dlg.transient(self)
        ctk.CTkLabel(
            dlg,
            text="내보낸 JSON(또는 ```json 펜스 / MACRO={...})을 붙여넣으세요.\n"
            "확인 시 새 슬롯으로 추가합니다. (현재 슬롯 덮어쓰기는 체크)",
            wraplength=520,
            justify="left",
        ).pack(padx=12, pady=(12, 4), anchor="w")
        box = ctk.CTkTextbox(dlg, font=ctk.CTkFont(family="Consolas", size=12))
        box.pack(fill="both", expand=True, padx=12, pady=8)
        overwrite_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(dlg, text="현재 슬롯에 덮어쓰기", variable=overwrite_var).pack(padx=12, anchor="w")

        def do_import() -> None:
            raw = box.get("1.0", "end").strip()
            try:
                doc = parse_import_text(raw)
            except ValueError as e:
                messagebox.showerror("가져오기", str(e))
                return
            if overwrite_var.get():
                if self._dirty and not messagebox.askyesno("가져오기", "저장하지 않은 변경을 버리고 덮어쓸까요?"):
                    return
                doc.slot = self._current_slot
                if not doc.name:
                    doc.name = f"{self._current_slot}번 매크로"
                self._doc = doc
                self.name_entry.delete(0, tk.END)
                self.name_entry.insert(0, doc.name)
                self.desc_entry.delete(0, tk.END)
                self.desc_entry.insert(0, doc.description)
                self._dirty = True
                self._refresh_event_list()
                self._set_status(f"가져오기 → 현재 {self._current_slot}번 (미저장). [슬롯 저장] 하세요.")
                dlg.destroy()
                return
            try:
                n = storage.next_slot_id()
                doc.slot = n
                if not doc.name:
                    doc.name = f"{n}번 매크로"
                storage.save_slot(n, doc)
            except (ValueError, OSError) as e:
                messagebox.showerror("가져오기", str(e))
                return
            self._refresh_slot_list(select=n)
            self._load_slot_into_editor(n, confirm_dirty=True)
            self._set_status(f"가져오기 → {n}번 슬롯 생성.")
            dlg.destroy()

        ctk.CTkButton(dlg, text="가져오기", command=do_import).pack(padx=12, pady=(4, 12))
