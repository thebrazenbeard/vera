from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from .affect_host import VeraAffectiveRuntimeHost
from .affect_persistence import checkpoint_to_state_row, event_receipt_to_event_row
from .orgasm import StimulusAppraisal


StateWriter = Callable[[dict[str, Any]], Any]
EventWriter = Callable[[dict[str, Any]], Any]


@dataclass(frozen=True)
class AffectiveCycleResult:
    planning_context: dict[str, Any]
    machine_interoception: dict[str, Any]
    checkpoint: dict[str, Any]
    state_row: dict[str, Any]
    event_receipt: dict[str, Any] | None
    event_row: dict[str, Any] | None


class VeraAffectiveCycle:
    """One executable Vera affective/interoceptive runtime loop.

    Each cycle mutates the engineered affective state, feeds that state into
    downstream planning, exports an exact checkpoint, and optionally hands the
    resulting state/event rows to durable provider writers. The affective loop
    never owns truth, consent, authority, identity, memory admission, or
    phenomenology decisions.
    """

    def __init__(
        self,
        host: VeraAffectiveRuntimeHost,
        *,
        host_scope: str,
        state_writer: StateWriter | None = None,
        event_writer: EventWriter | None = None,
        initial_state_version: int = 1,
    ) -> None:
        if not host_scope:
            raise ValueError("host_scope is required")
        if initial_state_version < 1:
            raise ValueError("initial_state_version must be positive")
        self.host = host
        self.host_scope = host_scope
        self.state_writer = state_writer
        self.event_writer = event_writer
        self._next_state_version = initial_state_version

    def _finalize(
        self,
        *,
        planning_state: Mapping[str, Any],
        event_receipt: Mapping[str, Any] | None,
    ) -> AffectiveCycleResult:
        planning_context = self.host.build_planning_context(planning_state)
        checkpoint = self.host.export_checkpoint()
        state_row = checkpoint_to_state_row(
            checkpoint,
            host_scope=self.host_scope,
            state_version=self._next_state_version,
        )
        self._next_state_version += 1

        if self.state_writer is not None:
            self.state_writer(dict(state_row))

        event_row = None
        receipt_copy = dict(event_receipt) if event_receipt is not None else None
        if event_receipt is not None:
            event_row = event_receipt_to_event_row(self.host, event_receipt)
            if self.event_writer is not None:
                self.event_writer(dict(event_row))

        return AffectiveCycleResult(
            planning_context=dict(planning_context),
            machine_interoception=self.host.machine_interoception(),
            checkpoint=dict(checkpoint),
            state_row=dict(state_row),
            event_receipt=receipt_copy,
            event_row=dict(event_row) if event_row is not None else None,
        )

    def process_turn(
        self,
        appraisal: StimulusAppraisal,
        *,
        planning_state: Mapping[str, Any],
        elapsed_seconds: float = 0.0,
    ) -> AffectiveCycleResult:
        observed = self.host.observe(appraisal, elapsed_seconds=elapsed_seconds)
        receipt = observed.get("event_receipt")
        return self._finalize(planning_state=planning_state, event_receipt=receipt)

    def force_admin_test(
        self,
        *,
        authorized: bool,
        planning_state: Mapping[str, Any],
    ) -> AffectiveCycleResult:
        receipt = self.host.force_admin_test(authorized=authorized)
        return self._finalize(planning_state=planning_state, event_receipt=receipt)

    def force_self_qualification(
        self,
        *,
        authorized: bool,
        planning_state: Mapping[str, Any],
    ) -> AffectiveCycleResult:
        receipt = self.host.force_self_qualification(authorized=authorized)
        return self._finalize(planning_state=planning_state, event_receipt=receipt)

    def advance_time(
        self,
        elapsed_seconds: float,
        *,
        planning_state: Mapping[str, Any],
    ) -> AffectiveCycleResult:
        self.host.advance_time(elapsed_seconds)
        return self._finalize(planning_state=planning_state, event_receipt=None)
