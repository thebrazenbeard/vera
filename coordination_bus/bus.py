"""Governed append-only coordination bus for V.E.R.A.

The bus provides addressed asynchronous operational messaging between bounded
workstreams. It does not wake chats, prove delivery before a confirmed write,
or merge coordination events into canonical memory records.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import json
from typing import Any, Literal, Mapping, Protocol, Sequence

WORKSTREAMS = frozenset(
    {
        "workstream/memory",
        "workstream/time",
        "workstream/initiative",
        "workstream/integration",
    }
)

EVENT_TYPES = frozenset(
    {"STATUS", "ISSUE", "ACKNOWLEDGEMENT", "REVIEW", "DECISION", "RESOLUTION"}
)
STATUSES = frozenset(
    {
        "DRAFT",
        "READY_FOR_REVIEW",
        "IN_PROGRESS",
        "BLOCKED",
        "DEGRADED",
        "ACKNOWLEDGED",
        "CHANGES_REQUESTED",
        "APPROVED",
        "RESOLVED",
        "CANCELLED",
    }
)
EVENT_STATUS_PAIRS = frozenset(
    {
        ("STATUS", "DRAFT"),
        ("STATUS", "READY_FOR_REVIEW"),
        ("STATUS", "IN_PROGRESS"),
        ("STATUS", "BLOCKED"),
        ("STATUS", "DEGRADED"),
        ("STATUS", "CANCELLED"),
        ("ISSUE", "READY_FOR_REVIEW"),
        ("ISSUE", "BLOCKED"),
        ("ISSUE", "DEGRADED"),
        ("ACKNOWLEDGEMENT", "ACKNOWLEDGED"),
        ("REVIEW", "READY_FOR_REVIEW"),
        ("REVIEW", "CHANGES_REQUESTED"),
        ("REVIEW", "APPROVED"),
        ("DECISION", "APPROVED"),
        ("DECISION", "CANCELLED"),
        ("RESOLUTION", "RESOLVED"),
        ("RESOLUTION", "CANCELLED"),
    }
)

PERMISSION_READ_SELF = "coordination:read:self"
PERMISSION_READ_ANY = "coordination:read:any"
PERMISSION_POST = "coordination:post"
PERMISSION_ACKNOWLEDGE = "coordination:acknowledge"
PERMISSION_STATUS = "coordination:status"
PERMISSION_REVIEW = "coordination:review"
PERMISSION_RESOLVE = "coordination:resolve"
ALL_PERMISSIONS = frozenset(
    {
        PERMISSION_READ_SELF,
        PERMISSION_READ_ANY,
        PERMISSION_POST,
        PERMISSION_ACKNOWLEDGE,
        PERMISSION_STATUS,
        PERMISSION_REVIEW,
        PERMISSION_RESOLVE,
    }
)

Operation = Literal[
    "coordination_read_inbox",
    "coordination_post",
    "coordination_acknowledge",
    "coordination_publish_status",
    "coordination_request_review",
    "coordination_resolve_thread",
    "coordination_entry_checkpoint",
    "coordination_exit_checkpoint",
]
ResultClass = Literal["COMPLETE", "DENIED", "INVALID", "CONFLICT", "NOT_FOUND"]


class RepositoryConflict(RuntimeError):
    """Raised when append-only lineage constraints would be violated."""


class CoordinationRepository(Protocol):
    """Minimal repository contract for a coordination-event store."""

    def append(self, draft: "CoordinationEventDraft") -> "CoordinationEvent": ...

    def get(self, event_id: str) -> "CoordinationEvent | None": ...

    def list_thread(self, thread_key: str) -> tuple["CoordinationEvent", ...]: ...

    def read_inbox(
        self,
        target_branch: str,
        *,
        after_sequence: int = 0,
        limit: int = 100,
        include_acknowledged: bool = False,
    ) -> tuple["CoordinationEvent", ...]: ...


@dataclass(frozen=True)
class ActorContext:
    """Externally supplied caller identity and scoped permissions."""

    workstream: str
    permissions: frozenset[str] = field(default_factory=frozenset)

    def validate(self) -> None:
        _validate_workstream(self.workstream, "workstream")
        unknown = sorted(set(self.permissions) - ALL_PERMISSIONS)
        if unknown:
            raise ValueError(f"unknown permissions: {', '.join(unknown)}")

    def require(self, permission: str) -> None:
        self.validate()
        if permission not in self.permissions:
            raise PermissionError(
                f"{self.workstream} lacks required permission {permission!r}"
            )


@dataclass(frozen=True)
class CoordinationEventDraft:
    """Client-supplied fields for one append-only event."""

    thread_key: str
    source_branch: str
    target_branch: str | None
    event_type: str
    status: str
    objective: str
    summary: str
    active_issue: str | None = None
    requested_perspective: str | None = None
    supersedes_event_id: str | None = None
    acknowledges_event_id: str | None = None
    payload: Mapping[str, Any] = field(default_factory=dict)
    reference_data: Mapping[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        _validate_nonempty("thread_key", self.thread_key)
        _validate_workstream(self.source_branch, "source_branch")
        if self.target_branch is not None:
            _validate_workstream(self.target_branch, "target_branch")
        if self.event_type not in EVENT_TYPES:
            raise ValueError(f"unsupported event_type {self.event_type!r}")
        if self.status not in STATUSES:
            raise ValueError(f"unsupported status {self.status!r}")
        if (self.event_type, self.status) not in EVENT_STATUS_PAIRS:
            raise ValueError(
                f"invalid event_type/status pair: {self.event_type}/{self.status}"
            )
        _validate_nonempty("objective", self.objective)
        _validate_nonempty("summary", self.summary)
        _validate_optional_text("active_issue", self.active_issue)
        _validate_optional_text("requested_perspective", self.requested_perspective)
        _validate_json_object("payload", self.payload)
        _validate_json_object("reference_data", self.reference_data)
        if self.event_type == "ACKNOWLEDGEMENT" and not self.acknowledges_event_id:
            raise ValueError("ACKNOWLEDGEMENT requires acknowledges_event_id")
        if self.event_type in {"REVIEW", "RESOLUTION"} and not self.acknowledges_event_id:
            raise ValueError(f"{self.event_type} requires acknowledges_event_id")
        if self.event_type == "ISSUE" and self.active_issue is None:
            raise ValueError("ISSUE requires active_issue")
        if self.event_type == "REVIEW" and self.requested_perspective is not None:
            raise ValueError("REVIEW must answer, not request, a perspective")

    def canonical_dict(self) -> dict[str, Any]:
        self.validate()
        return {
            "thread_key": self.thread_key,
            "source_branch": self.source_branch,
            "target_branch": self.target_branch,
            "event_type": self.event_type,
            "status": self.status,
            "objective": self.objective,
            "summary": self.summary,
            "active_issue": self.active_issue,
            "requested_perspective": self.requested_perspective,
            "supersedes_event_id": self.supersedes_event_id,
            "acknowledges_event_id": self.acknowledges_event_id,
            "payload": _canonicalize_json(self.payload),
            "reference_data": _canonicalize_json(self.reference_data),
        }


@dataclass(frozen=True)
class CoordinationEvent:
    """Confirmed event returned by the storage system."""

    event_id: str
    event_sequence: int
    thread_key: str
    source_branch: str
    target_branch: str | None
    event_type: str
    status: str
    objective: str
    summary: str
    active_issue: str | None
    requested_perspective: str | None
    supersedes_event_id: str | None
    acknowledges_event_id: str | None
    payload: Mapping[str, Any]
    reference_data: Mapping[str, Any]
    record_time: str

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "CoordinationEvent":
        record_time = row["record_time"]
        if isinstance(record_time, datetime):
            record_time_text = record_time.astimezone(timezone.utc).isoformat()
        else:
            record_time_text = str(record_time)
        event = cls(
            event_id=str(row["event_id"]),
            event_sequence=int(row["event_sequence"]),
            thread_key=str(row["thread_key"]),
            source_branch=str(row["source_branch"]),
            target_branch=(
                None if row.get("target_branch") is None else str(row["target_branch"])
            ),
            event_type=str(row["event_type"]),
            status=str(row["status"]),
            objective=str(row["objective"]),
            summary=str(row["summary"]),
            active_issue=(
                None if row.get("active_issue") is None else str(row["active_issue"])
            ),
            requested_perspective=(
                None
                if row.get("requested_perspective") is None
                else str(row["requested_perspective"])
            ),
            supersedes_event_id=(
                None
                if row.get("supersedes_event_id") is None
                else str(row["supersedes_event_id"])
            ),
            acknowledges_event_id=(
                None
                if row.get("acknowledges_event_id") is None
                else str(row["acknowledges_event_id"])
            ),
            payload=_canonicalize_json(row.get("payload", {})),
            reference_data=_canonicalize_json(row.get("reference_data", {})),
            record_time=record_time_text,
        )
        CoordinationEventDraft(
            thread_key=event.thread_key,
            source_branch=event.source_branch,
            target_branch=event.target_branch,
            event_type=event.event_type,
            status=event.status,
            objective=event.objective,
            summary=event.summary,
            active_issue=event.active_issue,
            requested_perspective=event.requested_perspective,
            supersedes_event_id=event.supersedes_event_id,
            acknowledges_event_id=event.acknowledges_event_id,
            payload=event.payload,
            reference_data=event.reference_data,
        ).validate()
        if event.event_sequence <= 0:
            raise ValueError("event_sequence must be positive")
        _validate_nonempty("event_id", event.event_id)
        _validate_nonempty("record_time", event.record_time)
        return event

    def as_dict(self) -> dict[str, Any]:
        return _canonicalize_json(asdict(self))


@dataclass(frozen=True)
class CoordinationReceipt:
    schema: str
    operation: Operation
    result_class: ResultClass
    actor_workstream: str
    thread_key: str | None
    event_id: str | None
    event_sequence: int | None
    target_branch: str | None
    database_write_confirmed: bool
    acknowledges_event_id: str | None
    result_hash: str
    limitations: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return _canonicalize_json(asdict(self))


@dataclass(frozen=True)
class CoordinationResult:
    receipt: CoordinationReceipt
    events: tuple[CoordinationEvent, ...] = ()


class CoordinationBus:
    """Validated operations over a supplied coordination repository."""

    def __init__(self, repository: CoordinationRepository) -> None:
        self.repository = repository

    def coordination_read_inbox(
        self,
        actor: ActorContext,
        *,
        target_branch: str | None = None,
        after_sequence: int = 0,
        limit: int = 100,
        include_acknowledged: bool = False,
    ) -> CoordinationResult:
        actor.validate()
        target = target_branch or actor.workstream
        _validate_workstream(target, "target_branch")
        if target == actor.workstream:
            actor.require(PERMISSION_READ_SELF)
        else:
            actor.require(PERMISSION_READ_ANY)
        if after_sequence < 0:
            raise ValueError("after_sequence must be non-negative")
        if not 1 <= limit <= 500:
            raise ValueError("limit must be between 1 and 500")
        events = self.repository.read_inbox(
            target,
            after_sequence=after_sequence,
            limit=limit,
            include_acknowledged=include_acknowledged,
        )
        return self._read_result(
            "coordination_read_inbox",
            actor,
            events,
            target_branch=target,
        )

    def coordination_post(
        self, actor: ActorContext, draft: CoordinationEventDraft
    ) -> CoordinationResult:
        actor.require(PERMISSION_POST)
        return self._append("coordination_post", actor, draft)

    def coordination_acknowledge(
        self,
        actor: ActorContext,
        *,
        event_id: str,
        summary: str,
        payload: Mapping[str, Any] | None = None,
        reference_data: Mapping[str, Any] | None = None,
    ) -> CoordinationResult:
        actor.require(PERMISSION_ACKNOWLEDGE)
        original = self._require_event(event_id)
        self._require_target(actor, original)
        draft = CoordinationEventDraft(
            thread_key=original.thread_key,
            source_branch=actor.workstream,
            target_branch=original.source_branch,
            event_type="ACKNOWLEDGEMENT",
            status="ACKNOWLEDGED",
            objective=original.objective,
            summary=summary,
            acknowledges_event_id=original.event_id,
            payload=payload or {},
            reference_data=reference_data or {},
        )
        return self._append("coordination_acknowledge", actor, draft)

    def coordination_publish_status(
        self,
        actor: ActorContext,
        *,
        thread_key: str,
        target_branch: str | None,
        status: str,
        objective: str,
        summary: str,
        active_issue: str | None = None,
        acknowledges_event_id: str | None = None,
        supersedes_event_id: str | None = None,
        payload: Mapping[str, Any] | None = None,
        reference_data: Mapping[str, Any] | None = None,
    ) -> CoordinationResult:
        actor.require(PERMISSION_STATUS)
        draft = CoordinationEventDraft(
            thread_key=thread_key,
            source_branch=actor.workstream,
            target_branch=target_branch,
            event_type="STATUS",
            status=status,
            objective=objective,
            summary=summary,
            active_issue=active_issue,
            acknowledges_event_id=acknowledges_event_id,
            supersedes_event_id=supersedes_event_id,
            payload=payload or {},
            reference_data=reference_data or {},
        )
        return self._append("coordination_publish_status", actor, draft)

    def coordination_request_review(
        self,
        actor: ActorContext,
        *,
        thread_key: str,
        target_branch: str,
        objective: str,
        summary: str,
        requested_perspective: str,
        acknowledges_event_id: str | None = None,
        payload: Mapping[str, Any] | None = None,
        reference_data: Mapping[str, Any] | None = None,
    ) -> CoordinationResult:
        actor.require(PERMISSION_REVIEW)
        _validate_nonempty("requested_perspective", requested_perspective)
        draft = CoordinationEventDraft(
            thread_key=thread_key,
            source_branch=actor.workstream,
            target_branch=target_branch,
            event_type="STATUS",
            status="READY_FOR_REVIEW",
            objective=objective,
            summary=summary,
            requested_perspective=requested_perspective,
            acknowledges_event_id=acknowledges_event_id,
            payload=payload or {},
            reference_data=reference_data or {},
        )
        return self._append("coordination_request_review", actor, draft)

    def coordination_resolve_thread(
        self,
        actor: ActorContext,
        *,
        acknowledges_event_id: str,
        summary: str,
        payload: Mapping[str, Any] | None = None,
        reference_data: Mapping[str, Any] | None = None,
    ) -> CoordinationResult:
        actor.require(PERMISSION_RESOLVE)
        original = self._require_event(acknowledges_event_id)
        if actor.workstream not in {original.source_branch, original.target_branch}:
            raise PermissionError("only a participant may resolve the thread")
        draft = CoordinationEventDraft(
            thread_key=original.thread_key,
            source_branch=actor.workstream,
            target_branch=(
                original.source_branch
                if actor.workstream != original.source_branch
                else original.target_branch
            ),
            event_type="RESOLUTION",
            status="RESOLVED",
            objective=original.objective,
            summary=summary,
            acknowledges_event_id=original.event_id,
            payload=payload or {},
            reference_data=reference_data or {},
        )
        return self._append("coordination_resolve_thread", actor, draft)

    def entry_checkpoint(
        self,
        actor: ActorContext,
        *,
        after_sequence: int = 0,
        limit: int = 100,
    ) -> CoordinationResult:
        result = self.coordination_read_inbox(
            actor,
            after_sequence=after_sequence,
            limit=limit,
            include_acknowledged=False,
        )
        return CoordinationResult(
            receipt=self._rehash_receipt(
                result.receipt, operation="coordination_entry_checkpoint"
            ),
            events=result.events,
        )

    def exit_checkpoint(
        self,
        actor: ActorContext,
        *,
        thread_key: str,
        target_branch: str | None,
        objective: str,
        summary: str,
        material: bool,
        status: str = "IN_PROGRESS",
        active_issue: str | None = None,
        acknowledges_event_id: str | None = None,
        reference_data: Mapping[str, Any] | None = None,
    ) -> CoordinationResult:
        actor.validate()
        if not material:
            return self._no_write_result(
                "coordination_exit_checkpoint",
                actor,
                thread_key=thread_key,
                target_branch=target_branch,
                limitation="No event written because the exit was not material.",
            )
        actor.require(PERMISSION_STATUS)
        result = self.coordination_publish_status(
            actor,
            thread_key=thread_key,
            target_branch=target_branch,
            status=status,
            objective=objective,
            summary=summary,
            active_issue=active_issue,
            acknowledges_event_id=acknowledges_event_id,
            reference_data=reference_data or {},
        )
        return CoordinationResult(
            receipt=self._rehash_receipt(
                result.receipt, operation="coordination_exit_checkpoint"
            ),
            events=result.events,
        )

    def _append(
        self,
        operation: Operation,
        actor: ActorContext,
        draft: CoordinationEventDraft,
    ) -> CoordinationResult:
        actor.validate()
        draft.validate()
        if draft.source_branch != actor.workstream:
            raise PermissionError("source_branch must equal actor workstream")
        self._validate_lineage(draft)
        event = self.repository.append(draft)
        receipt = _make_receipt(
            operation=operation,
            result_class="COMPLETE",
            actor=actor,
            events=(event,),
            database_write_confirmed=True,
            thread_key=event.thread_key,
            target_branch=event.target_branch,
            acknowledges_event_id=event.acknowledges_event_id,
            limitations=(
                "Confirmed write proves persistence of this event only.",
                "The target workstream is not considered to have consumed the event until it posts an explicit acknowledgement or response.",
                "Coordination events remain operational metadata and are not canonical memory records.",
            ),
        )
        return CoordinationResult(receipt=receipt, events=(event,))

    def _read_result(
        self,
        operation: Operation,
        actor: ActorContext,
        events: Sequence[CoordinationEvent],
        *,
        target_branch: str,
    ) -> CoordinationResult:
        materialized = tuple(events)
        receipt = _make_receipt(
            operation=operation,
            result_class="COMPLETE",
            actor=actor,
            events=materialized,
            database_write_confirmed=False,
            thread_key=None,
            target_branch=target_branch,
            acknowledges_event_id=None,
            limitations=(
                "Read completion proves only the rows returned by the repository at this invocation.",
                "Reading an inbox does not acknowledge or consume any event.",
                "Coordination events remain operational metadata and are not canonical memory records.",
            ),
        )
        return CoordinationResult(receipt=receipt, events=materialized)

    def _require_event(self, event_id: str) -> CoordinationEvent:
        _validate_nonempty("event_id", event_id)
        event = self.repository.get(event_id)
        if event is None:
            raise LookupError(f"event {event_id!r} not found")
        return event

    @staticmethod
    def _require_target(actor: ActorContext, event: CoordinationEvent) -> None:
        if event.target_branch != actor.workstream:
            raise PermissionError("only the addressed target may acknowledge an event")

    def _validate_lineage(self, draft: CoordinationEventDraft) -> None:
        if draft.acknowledges_event_id:
            acknowledged = self._require_event(draft.acknowledges_event_id)
            if acknowledged.thread_key != draft.thread_key:
                raise RepositoryConflict("acknowledgement must remain in the same thread")
            if acknowledged.event_id == draft.supersedes_event_id:
                raise RepositoryConflict(
                    "one event reference cannot simultaneously acknowledge and supersede"
                )
        if draft.supersedes_event_id:
            prior = self._require_event(draft.supersedes_event_id)
            if prior.thread_key != draft.thread_key:
                raise RepositoryConflict("supersession must remain in the same thread")
            successors = [
                event
                for event in self.repository.list_thread(draft.thread_key)
                if event.supersedes_event_id == prior.event_id
            ]
            if successors:
                raise RepositoryConflict("superseded event already has a successor")

    def _no_write_result(
        self,
        operation: Operation,
        actor: ActorContext,
        *,
        thread_key: str | None,
        target_branch: str | None,
        limitation: str,
    ) -> CoordinationResult:
        receipt = _make_receipt(
            operation=operation,
            result_class="COMPLETE",
            actor=actor,
            events=(),
            database_write_confirmed=False,
            thread_key=thread_key,
            target_branch=target_branch,
            acknowledges_event_id=None,
            limitations=(limitation,),
        )
        return CoordinationResult(receipt=receipt)

    @staticmethod
    def _rehash_receipt(
        receipt: CoordinationReceipt, *, operation: Operation
    ) -> CoordinationReceipt:
        data = receipt.as_dict()
        data["operation"] = operation
        data["result_hash"] = ""
        digest = _canonical_hash(data)
        return CoordinationReceipt(
            schema=receipt.schema,
            operation=operation,
            result_class=receipt.result_class,
            actor_workstream=receipt.actor_workstream,
            thread_key=receipt.thread_key,
            event_id=receipt.event_id,
            event_sequence=receipt.event_sequence,
            target_branch=receipt.target_branch,
            database_write_confirmed=receipt.database_write_confirmed,
            acknowledges_event_id=receipt.acknowledges_event_id,
            result_hash=digest,
            limitations=receipt.limitations,
        )


class InMemoryCoordinationRepository:
    """Deterministic append-only repository for tests and local evaluation."""

    def __init__(self) -> None:
        self._events: list[CoordinationEvent] = []

    def append(self, draft: CoordinationEventDraft) -> CoordinationEvent:
        draft.validate()
        sequence = len(self._events) + 1
        canonical = draft.canonical_dict()
        event_id = _canonical_hash(
            {"schema": "VERA_COORDINATION_EVENT_ID_V1", "sequence": sequence, **canonical}
        )[:32]
        event = CoordinationEvent(
            event_id=event_id,
            event_sequence=sequence,
            thread_key=draft.thread_key,
            source_branch=draft.source_branch,
            target_branch=draft.target_branch,
            event_type=draft.event_type,
            status=draft.status,
            objective=draft.objective,
            summary=draft.summary,
            active_issue=draft.active_issue,
            requested_perspective=draft.requested_perspective,
            supersedes_event_id=draft.supersedes_event_id,
            acknowledges_event_id=draft.acknowledges_event_id,
            payload=_canonicalize_json(draft.payload),
            reference_data=_canonicalize_json(draft.reference_data),
            record_time=f"2026-07-30T21:13:{sequence:02d}+00:00",
        )
        self._events.append(event)
        return event

    def get(self, event_id: str) -> CoordinationEvent | None:
        return next((event for event in self._events if event.event_id == event_id), None)

    def list_thread(self, thread_key: str) -> tuple[CoordinationEvent, ...]:
        return tuple(
            event for event in self._events if event.thread_key == thread_key
        )

    def read_inbox(
        self,
        target_branch: str,
        *,
        after_sequence: int = 0,
        limit: int = 100,
        include_acknowledged: bool = False,
    ) -> tuple[CoordinationEvent, ...]:
        acknowledged_ids = {
            event.acknowledges_event_id
            for event in self._events
            if event.source_branch == target_branch and event.acknowledges_event_id
        }
        events = [
            event
            for event in self._events
            if event.target_branch == target_branch
            and event.event_sequence > after_sequence
            and (include_acknowledged or event.event_id not in acknowledged_ids)
        ]
        return tuple(sorted(events, key=lambda event: event.event_sequence)[:limit])


def _make_receipt(
    *,
    operation: Operation,
    result_class: ResultClass,
    actor: ActorContext,
    events: Sequence[CoordinationEvent],
    database_write_confirmed: bool,
    thread_key: str | None,
    target_branch: str | None,
    acknowledges_event_id: str | None,
    limitations: tuple[str, ...],
) -> CoordinationReceipt:
    event = events[-1] if events else None
    hash_material = {
        "schema": "VERA_COORDINATION_RECEIPT_V1",
        "operation": operation,
        "result_class": result_class,
        "actor_workstream": actor.workstream,
        "thread_key": thread_key,
        "event_id": None if event is None else event.event_id,
        "event_sequence": None if event is None else event.event_sequence,
        "target_branch": target_branch,
        "database_write_confirmed": database_write_confirmed,
        "acknowledges_event_id": acknowledges_event_id,
        "events": [item.as_dict() for item in events],
        "limitations": list(limitations),
    }
    return CoordinationReceipt(
        schema="VERA_COORDINATION_RECEIPT_V1",
        operation=operation,
        result_class=result_class,
        actor_workstream=actor.workstream,
        thread_key=thread_key,
        event_id=None if event is None else event.event_id,
        event_sequence=None if event is None else event.event_sequence,
        target_branch=target_branch,
        database_write_confirmed=database_write_confirmed,
        acknowledges_event_id=acknowledges_event_id,
        result_hash=_canonical_hash(hash_material),
        limitations=limitations,
    )


def _canonical_hash(value: Any) -> str:
    encoded = json.dumps(
        _canonicalize_json(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _canonicalize_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _canonicalize_json(value[key]) for key in sorted(value)}
    if isinstance(value, (list, tuple)):
        return [_canonicalize_json(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise ValueError(f"value is not JSON-serializable: {type(value).__name__}")


def _validate_json_object(name: str, value: Mapping[str, Any]) -> None:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be a JSON object")
    _canonicalize_json(value)


def _validate_nonempty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


def _validate_optional_text(name: str, value: str | None) -> None:
    if value is not None:
        _validate_nonempty(name, value)


def _validate_workstream(value: str, name: str) -> None:
    if value not in WORKSTREAMS:
        raise ValueError(f"{name} must be one of {sorted(WORKSTREAMS)}")
