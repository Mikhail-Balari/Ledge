"""Append-oriented JSONL storage for decision ledger events."""

from __future__ import annotations

import json
from pathlib import Path

from .event import DecisionEvent
from .exceptions import LedgerHashError, LedgerSequenceError, LedgerStoreError


class DecisionLedger:
    """Local append-oriented JSONL store for semantic decision events."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def exists(self) -> bool:
        return self.path.exists()

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.touch(exist_ok=True)

    def append(self, event: DecisionEvent) -> None:
        if not isinstance(event, DecisionEvent):
            raise LedgerStoreError("ledger append requires a DecisionEvent")
        if not event.verify_hash():
            raise LedgerHashError("decision event hash does not verify")

        events = self.read_events() if self.exists() else []
        expected_sequence = len(events) + 1
        if event.sequence != expected_sequence:
            raise LedgerSequenceError(
                f"decision event sequence {event.sequence} does not match expected {expected_sequence}"
            )

        if events:
            expected_previous_hash = events[-1].current_event_hash
            if event.previous_event_hash != expected_previous_hash:
                raise LedgerSequenceError("decision event previous_event_hash does not match last event")
        elif event.previous_event_hash is not None:
            raise LedgerSequenceError("first decision event must not have previous_event_hash")

        self.initialize()
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(event.to_canonical_json())
            handle.write("\n")

    def read_events(self) -> list[DecisionEvent]:
        if not self.exists():
            return []

        events: list[DecisionEvent] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if line in {"\n", "\r\n"} or not line.strip():
                    raise LedgerStoreError(f"blank ledger line at {line_number}")
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise LedgerStoreError(f"malformed JSON ledger line at {line_number}") from exc
                try:
                    event = DecisionEvent.from_dict(payload)
                except Exception as exc:
                    raise LedgerStoreError(f"invalid decision event at ledger line {line_number}") from exc
                events.append(event)

        self._validate_continuity(events)
        return events

    def last_event(self) -> DecisionEvent | None:
        events = self.read_events()
        if not events:
            return None
        return events[-1]

    def next_sequence(self) -> int:
        return len(self.read_events()) + 1

    def expected_previous_hash(self) -> str | None:
        event = self.last_event()
        if event is None:
            return None
        return event.current_event_hash

    @staticmethod
    def _validate_continuity(events: list[DecisionEvent]) -> None:
        previous_hash: str | None = None
        for index, event in enumerate(events, start=1):
            if event.sequence != index:
                raise LedgerSequenceError(
                    f"decision event sequence {event.sequence} does not match expected {index}"
                )
            if event.previous_event_hash != previous_hash:
                raise LedgerSequenceError(
                    f"decision event {event.sequence} previous_event_hash breaks ledger continuity"
                )
            previous_hash = event.current_event_hash
