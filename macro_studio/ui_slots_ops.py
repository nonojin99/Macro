"""슬롯 추가/복제/삭제/비우기/저장/초기화."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog

from . import storage
from .models import MacroDocument


class SlotsOpsUIMixin:
    """MacroStudioApp 믹스인 — 슬롯 변경 연산."""

    def _add_slot(self) -> None:
        if self._recorder.is_recording or self._player.is_playing:
            self._set_status("녹화/재생 중에는 슬롯을 추가할 수 없습니다.")
            return
        name = simpledialog.askstring("슬롯 추가", "새 슬롯 이름 (선택):", parent=self)
        try:
            n = storage.add_slot(name)
        except ValueError as e:
            messagebox.showerror("슬롯 추가", str(e))
            return
        self._refresh_slot_list(select=n)
        self._load_slot_into_editor(n, confirm_dirty=True)
        self._set_status(f"{n}번 슬롯 추가됨.")

    def _duplicate_slot(self) -> None:
        slot = self._selected_slot_number() or self._current_slot
        if self._dirty and slot == self._current_slot:
            if not messagebox.askyesno("슬롯 복제", "저장하지 않은 변경이 있습니다. 디스크 기준으로 복제할까요?"):
                return
        try:
            new_id = storage.duplicate_slot(slot)
        except (ValueError, OSError) as e:
            messagebox.showerror("슬롯 복제", str(e))
            return
        self._refresh_slot_list(select=new_id)
        self._load_slot_into_editor(new_id, confirm_dirty=True)
        self._set_status(f"{slot}번 → {new_id}번 복제 완료.")

    def _delete_selected_slot(self) -> None:
        slot = self._selected_slot_number() or self._current_slot
        if not messagebox.askyesno("슬롯 삭제", f"{slot}번 슬롯을 완전히 삭제할까요?"):
            return
        try:
            storage.delete_slot(slot)
        except OSError as e:
            messagebox.showerror("슬롯 삭제", str(e))
            return
        remaining = storage.ensure_at_least_one_slot()
        next_slot = remaining[0]
        if slot == self._current_slot:
            self._load_slot_into_editor(next_slot, confirm_dirty=False)
        else:
            self._refresh_slot_list(select=self._current_slot)
        self._set_status(f"{slot}번 슬롯 삭제됨.")

    def _clear_selected_slot(self) -> None:
        slot = self._selected_slot_number() or self._current_slot
        if not messagebox.askyesno(
            "슬롯 비우기",
            f"{slot}번 슬롯 파일을 삭제(비우기)할까요?\n(슬롯 번호는 유지, 빈 템플릿)",
        ):
            return
        try:
            storage.clear_slot(slot)
        except OSError as e:
            messagebox.showerror("슬롯 비우기", str(e))
            return
        storage.save_slot(slot, MacroDocument.empty_for_slot(slot))
        if slot == self._current_slot:
            self._doc = MacroDocument.empty_for_slot(slot)
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, self._doc.name)
            self.desc_entry.delete(0, tk.END)
            self._dirty = False
            self._refresh_event_list()
        self._refresh_slot_list(select=slot)
        self._set_status(f"{slot}번 슬롯 비움.")

    def _save(self) -> None:
        if self._recorder.is_recording:
            messagebox.showwarning("저장", "녹화 중에는 저장할 수 없습니다. 먼저 중지하세요.")
            return
        self._collect_meta()
        try:
            path = storage.save_slot(self._current_slot, self._doc)
        except ValueError as e:
            messagebox.showerror("저장", str(e))
            return
        except OSError as e:
            messagebox.showerror("저장", f"저장 실패: {e}")
            return
        self._dirty = False
        self._refresh_slot_list(select=self._current_slot)
        self._set_status(f"{self._current_slot}번 슬롯 저장 완료: {path.name}")
        messagebox.showinfo("저장", f"{self._current_slot}번 슬롯에 저장되었습니다:\n{path}")

    def _new_macro(self) -> None:
        if self._dirty:
            if not messagebox.askyesno("슬롯 초기화", "저장하지 않은 변경이 있습니다. 계속할까요?"):
                return
        self._doc = MacroDocument.empty_for_slot(self._current_slot)
        self.name_entry.delete(0, tk.END)
        self.name_entry.insert(0, self._doc.name)
        self.desc_entry.delete(0, tk.END)
        self._dirty = False
        self.play_from_var.set("1")
        self._refresh_event_list()
        self._set_status(f"{self._current_slot}번 슬롯 편집기 초기화 — 녹화 후 [슬롯 저장]하세요.")
