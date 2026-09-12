"""범위 삭제 · 잘라내기/복사/붙여넣기."""

from __future__ import annotations

from tkinter import messagebox

from .models import MacroEvent


class ClipboardUIMixin:
    """MacroStudioApp 믹스인 — 이벤트 범위 클립보드."""

    _event_clipboard: list[MacroEvent]

    def _parse_range(self) -> tuple[int, int] | None:
        if not self._doc.events:
            messagebox.showinfo("범위", "이벤트가 없습니다.")
            return None
        try:
            a = int(self.range_from_var.get().strip())
            b = int(self.range_to_var.get().strip())
        except ValueError:
            messagebox.showerror("범위", "시작/끝 번호가 올바르지 않습니다.")
            return None
        if a > b:
            a, b = b, a
        n = len(self._doc.events)
        if a < 1 or b > n:
            messagebox.showwarning("범위", f"범위는 1~{n} 사이여야 합니다.")
            return None
        return a, b

    def _delete_range(self) -> None:
        parsed = self._parse_range()
        if parsed is None:
            return
        a, b = parsed
        if not messagebox.askyesno("범위 삭제", f"동작 {a}~{b} 를 삭제할까요? ({b - a + 1}개)"):
            return
        del self._doc.events[a - 1 : b]
        self._mark_dirty()
        new_sel = min(a - 1, len(self._doc.events) - 1) if self._doc.events else None
        self._refresh_event_list(select=new_sel)
        self._set_status(f"동작 {a}~{b} 삭제됨 (아직 디스크 미저장).")

    def _copy_range(self) -> None:
        parsed = self._parse_range()
        if parsed is None:
            return
        a, b = parsed
        self._event_clipboard = [e.clone() for e in self._doc.events[a - 1 : b]]
        self._set_status(f"동작 {a}~{b} 복사 ({len(self._event_clipboard)}개). 붙여넣기 가능.")

    def _cut_range(self) -> None:
        parsed = self._parse_range()
        if parsed is None:
            return
        a, b = parsed
        self._event_clipboard = [e.clone() for e in self._doc.events[a - 1 : b]]
        del self._doc.events[a - 1 : b]
        self._mark_dirty()
        new_sel = min(a - 1, len(self._doc.events) - 1) if self._doc.events else None
        self._refresh_event_list(select=new_sel)
        self._set_status(f"동작 {a}~{b} 잘라내기 ({len(self._event_clipboard)}개).")

    def _paste_events(self) -> None:
        if not self._event_clipboard:
            messagebox.showinfo("붙여넣기", "클립보드가 비어 있습니다. 먼저 복사/잘라내기를 하세요.")
            return
        if self._selected_index is not None:
            insert_at = self._selected_index
        else:
            insert_at = len(self._doc.events)
        clones = [e.clone() for e in self._event_clipboard]
        self._doc.events[insert_at:insert_at] = clones
        self._mark_dirty()
        self._refresh_event_list(select=insert_at)
        self._set_status(f"{len(clones)}개 붙여넣기 @ 동작 {insert_at + 1} (미저장).")
