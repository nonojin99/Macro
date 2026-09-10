"""매크로 이벤트·문서 데이터 모델."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class EventType(str, Enum):
    CLICK = "click"
    SCROLL = "scroll"
    KEY = "key"
    MOVE = "move"
    WAIT = "wait"


@dataclass
class MacroEvent:
    """단일 매크로 이벤트.

    delay_ms: 이전 이벤트(또는 시작) 이후 대기 시간(ms).
    """

    type: str
    delay_ms: int = 0
    # click / move / scroll
    x: int | None = None
    y: int | None = None
    button: str | None = None  # left, right, middle
    action: str | None = None  # press, release
    # scroll
    dx: int | None = None
    dy: int | None = None
    # key
    key: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        # JSON에 null 필드 최소화 (가독성)
        return {k: v for k, v in data.items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MacroEvent:
        known = {f.name for f in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        filtered = {k: v for k, v in data.items() if k in known}
        if "delay_ms" in filtered:
            filtered["delay_ms"] = int(filtered["delay_ms"])
        for coord in ("x", "y", "dx", "dy"):
            if coord in filtered and filtered[coord] is not None:
                filtered[coord] = int(filtered[coord])
        return cls(**filtered)

    def details_text(self) -> str:
        t = self.type
        if t == EventType.CLICK.value:
            return f"{self.button} {self.action} @ ({self.x}, {self.y})"
        if t == EventType.SCROLL.value:
            return f"dx={self.dx} dy={self.dy} @ ({self.x}, {self.y})"
        if t == EventType.KEY.value:
            return f"{self.key} {self.action}"
        if t == EventType.MOVE.value:
            return f"→ ({self.x}, {self.y})"
        if t == EventType.WAIT.value:
            return f"대기 {self.delay_ms} ms"
        return str(self.to_dict())


@dataclass
class MacroDocument:
    name: str
    description: str = ""
    version: int = 1
    events: list[MacroEvent] = field(default_factory=list)
    slot: int | None = None  # 1~10 슬롯 번호 (선택)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "events": [e.to_dict() for e in self.events],
        }
        if self.slot is not None:
            data["slot"] = int(self.slot)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MacroDocument:
        events = [MacroEvent.from_dict(e) for e in data.get("events", [])]
        slot_raw = data.get("slot")
        slot: int | None = None
        if slot_raw is not None:
            try:
                slot = int(slot_raw)
            except (TypeError, ValueError):
                slot = None
        return cls(
            name=str(data.get("name", "untitled")),
            description=str(data.get("description", "")),
            version=int(data.get("version", 1)),
            events=events,
            slot=slot,
        )

    def summary(self) -> str:
        return f"{self.name} ({len(self.events)} events)"

    @classmethod
    def empty_for_slot(cls, slot: int) -> MacroDocument:
        """빈 슬롯용 템플릿."""
        return cls(name=f"{slot}번 매크로", description="", events=[], slot=slot)
