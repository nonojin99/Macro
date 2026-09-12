"""선택 이벤트 필드 적용 · 좌표 채우기 · 순서/대기."""

from __future__ import annotations

from tkinter import messagebox, simpledialog

from . import monitors
from .models import EventType, MacroEvent


class EventsEditUIMixin:
    """MacroStudioApp 믹스인 — 이벤트 필드/좌표/순서."""

    def _apply_edit(self) -> None:
        if self._selected_index is None:
            messagebox.showinfo("편집", "이벤트를 먼저 선택하세요.")
            return
        idx = self._selected_index
        try:
            delay = int(self._edit_vars["delay_ms"].get().strip() or "0")
            mon = self._optional_int(self._edit_vars["monitor"].get())
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
                monitor=mon,
            )
        except ValueError:
            messagebox.showerror("편집", "숫자 필드 형식이 올바르지 않습니다.")
            return
        self._doc.events[idx] = ev
        self._mark_dirty()
        self._refresh_event_list(select=idx)
        self._set_status(f"동작 {idx + 1} 수정됨 (아직 디스크 미저장).")

    def _fill_xy_from_cursor(self) -> None:
        if self._selected_index is None:
            messagebox.showinfo("좌표", "이벤트를 먼저 선택하세요.")
            return
        try:
            x_i, y_i = monitors.mouse_position()
            mon = monitors.monitor_index_at(x_i, y_i)
        except Exception as e:
            messagebox.showerror("좌표", f"마우스 위치를 읽을 수 없습니다: {e}")
            return
        self._edit_vars["x"].set(str(x_i))
        self._edit_vars["y"].set(str(y_i))
        if mon is not None:
            self._edit_vars["monitor"].set(str(mon))
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
        ev.monitor = mon
        self._mark_dirty()
        self._refresh_event_list(select=idx)
        mon_txt = f", 모니터 {mon}" if mon is not None else ""
        self._set_status(f"동작 {idx + 1} 좌표 → ({x_i}, {y_i}){mon_txt} (미저장).")

    def _delete_event(self) -> None:
        if self._selected_index is None:
            return
        idx = self._selected_index
        del self._doc.events[idx]
        self._mark_dirty()
        new_sel = min(idx, len(self._doc.events) - 1) if self._doc.events else None
        self._refresh_event_list(select=new_sel)
        self._set_status("이벤트 삭제됨 (아직 디스크 미저장).")

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
