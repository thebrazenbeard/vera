"""Strict role-, operation-, and subject-bound temporal coordination facade."""

from __future__ import annotations

from hashlib import sha256
import json
from typing import Any, Mapping

from .contracts import (
    ActorContext,
    PERMISSION_ACKNOWLEDGE,
    PERMISSION_READ_SELF,
    PERMISSION_STATUS,
    canonicalize,
)
from .core import _receipted
from .temporal import (
    CoordinationBus as _TemporalCoordinationBus,
    TemporalCoordinationResult,
)
from .verified_temporal import (
    CoordinationBus as _VerifierBoundCoordinationBus,
    TemporalEvidenceInput,
)


def _subject(prefix: str, body: Mapping[str, Any]) -> str:
    digest = sha256(json.dumps(
        canonicalize(body), sort_keys=True, separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")).hexdigest()
    return f"{prefix}:{digest}"


def entry_checkpoint_subject(
    workstream: str,
    after_sequence: int,
    limit: int,
) -> str:
    return _subject("coordination-entry-v2", {
        "operation": "coordination_entry_checkpoint",
        "actor_workstream": workstream,
        "target_branch": workstream,
        "after_sequence": after_sequence,
        "limit": limit,
        "include_acknowledged": False,
    })


def acknowledgement_subject(
    event_id: str,
    *,
    actor_workstream: str,
    thread_key: str,
    summary: str,
    payload: Mapping[str, Any] | None = None,
    reference_data: Mapping[str, Any] | None = None,
) -> str:
    return _subject("coordination-acknowledgement-v2", {
        "operation": "coordination_acknowledge",
        "actor_workstream": actor_workstream,
        "source_event_id": event_id,
        "thread_key": thread_key,
        "summary": summary,
        "payload": canonicalize(payload or {}),
        "reference_data": canonicalize(reference_data or {}),
    })


def exit_checkpoint_subject(
    workstream: str,
    thread_key: str,
    target_branch: str | None,
    *,
    objective: str,
    summary: str,
    material: bool,
    status: str = "IN_PROGRESS",
    active_issue: str | None = None,
    acknowledges_event_id: str | None = None,
    reference_data: Mapping[str, Any] | None = None,
) -> str:
    return _subject("coordination-exit-v2", {
        "operation": "coordination_exit_checkpoint",
        "actor_workstream": workstream,
        "thread_key": thread_key,
        "target_branch": target_branch,
        "objective": objective,
        "summary": summary,
        "material": material,
        "status": status,
        "active_issue": active_issue,
        "acknowledges_event_id": acknowledges_event_id,
        "reference_data": canonicalize(reference_data or {}),
    })


class CoordinationBus(_VerifierBoundCoordinationBus):
    """Public bus enforcing exact operation-subject temporal bindings."""

    @_receipted("coordination_entry_checkpoint")
    def entry_checkpoint(
        self,
        actor: ActorContext,
        *,
        after_sequence: int = 0,
        limit: int = 100,
        entry_time: TemporalEvidenceInput = None,
        retrieval_time: TemporalEvidenceInput = None,
    ) -> TemporalCoordinationResult:
        actor.validate()
        actor.require(PERMISSION_READ_SELF)
        subject = entry_checkpoint_subject(actor.workstream, after_sequence, limit)
        entry = self._verified_claim(
            entry_time, role="entry_time", subject=subject
        )
        retrieval = self._verified_claim(
            retrieval_time, role="retrieval_time", subject=subject
        )
        return _TemporalCoordinationBus.entry_checkpoint(
            self,
            actor,
            after_sequence=after_sequence,
            limit=limit,
            entry_time=entry,
            retrieval_time=retrieval,
        )

    @_receipted("coordination_acknowledge")
    def coordination_acknowledge(
        self,
        actor: ActorContext,
        *,
        event_id: str,
        summary: str,
        acknowledgement_time: TemporalEvidenceInput = None,
        consumption_time: TemporalEvidenceInput = None,
        payload: Mapping[str, Any] | None = None,
        reference_data: Mapping[str, Any] | None = None,
    ) -> TemporalCoordinationResult:
        actor.require(PERMISSION_ACKNOWLEDGE)
        original = self._event(event_id)
        self._addressed_target(actor, original)
        subject = acknowledgement_subject(
            event_id,
            actor_workstream=actor.workstream,
            thread_key=original.thread_key,
            summary=summary,
            payload=payload,
            reference_data=reference_data,
        )
        acknowledgement = self._verified_claim(
            acknowledgement_time,
            role="acknowledgement_time",
            subject=subject,
        )
        consumption = self._verified_claim(
            consumption_time,
            role="consumption_time",
            subject=subject,
        )
        return _TemporalCoordinationBus.coordination_acknowledge(
            self,
            actor,
            event_id=event_id,
            summary=summary,
            acknowledgement_time=acknowledgement,
            consumption_time=consumption,
            payload=payload,
            reference_data=reference_data,
        )

    @_receipted("coordination_exit_checkpoint")
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
        event_time: TemporalEvidenceInput = None,
        state_time: TemporalEvidenceInput = None,
        reference_data: Mapping[str, Any] | None = None,
    ) -> TemporalCoordinationResult:
        actor.validate()
        if material:
            actor.require(PERMISSION_STATUS)
        subject = exit_checkpoint_subject(
            actor.workstream,
            thread_key,
            target_branch,
            objective=objective,
            summary=summary,
            material=material,
            status=status,
            active_issue=active_issue,
            acknowledges_event_id=acknowledges_event_id,
            reference_data=reference_data,
        )
        event = self._verified_claim(
            event_time, role="event_time", subject=subject
        )
        state = self._verified_claim(
            state_time, role="state_time", subject=subject
        )
        return _TemporalCoordinationBus.exit_checkpoint(
            self,
            actor,
            thread_key=thread_key,
            target_branch=target_branch,
            objective=objective,
            summary=summary,
            material=material,
            status=status,
            active_issue=active_issue,
            acknowledges_event_id=acknowledges_event_id,
            event_time=event,
            state_time=state,
            reference_data=reference_data,
        )
