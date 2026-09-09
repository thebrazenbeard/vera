from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from .affect_host import VeraAffectiveRuntimeHost
from .affect_persistence import (
    build_affective_resume_token,
    build_atomic_commit_request,
    checkpoint_to_state_row,
    event_receipt_to_event_row,
)
from .orgasm import StimulusAppraisal


StateWriter = Callable[[dict[str, Any]], Any]
EventWriter = Callable[[dict[str, Any]], Any]
AtomicCommitWriter = Callable[[dict[str, Any]], Any]


@dataclass(frozen=True)
class AffectiveCycleResult:
    planning_context: dict[str, Any]
    machine_interoception: dict[str, Any]
    checkpoint: dict[str, Any]
    state_row: dict[str, Any]
    event_receipt: dict[str, Any] | None
    event_row: dict[str, Any] | None
    event_receipts: list[dict[str, Any]]
    event_rows: list[dict[str, Any]]
    resume_token: dict[str, Any]
    commit_request: dict[str, Any]
    commit_result: Any
    atomic_commit_used: bool


class VeraAffectiveCycle:
    """One executable Vera affective/interoceptive runtime loop.

    Each cycle mutates the engineered affective state, feeds that state into
    downstream planning, exports an exact checkpoint, and can hand one atomic
    state-plus-events commit envelope to a durable provider writer. Separate
    state/event callbacks remain available for bounded in-memory tests but are
    not the qualified durable-provider path. The affective loop never owns
    truth, consent, authority, identity, memory admission, or phenomenology.
    """

    def __init__(
        self,
        host: VeraAffectiveRuntimeHost,
        *,
        host_scope: str,
        state_writer: StateWriter | None = None,
        event_writer: EventWriter | None = None,
        atomic_commit_writer: AtomicCommitWriter | None = None,
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
        self.atomic_commit_writer = atomic_commit_writer
        self._next_state_version = initial_state_version
        self._durability_uncertain = False

    def _require_usable_frontier(self) -> None:
        if self._durability_uncertain:
            raise RuntimeError(
                "affective cycle durable frontier is uncertain; restore from exact provider readback before continuing"
            )

    def _validate_atomic_commit_ack(
        self,
        commit_result: Any,
        *,
        state_version: int,
        checkpoint_sha256: str,
        event_count: int,
    ) -> Mapping[str, Any]:
        if not isinstance(commit_result, Mapping):
            raise RuntimeError("atomic durable commit returned no structured acknowledgement")
        if commit_result.get("state_version") != state_version:
            raise RuntimeError("atomic durable commit returned an unexpected state_version")
        if commit_result.get("checkpoint_sha256") != checkpoint_sha256:
            raise RuntimeError("atomic durable commit returned an unexpected checkpoint_sha256")
        if commit_result.get("event_count") != event_count:
            raise RuntimeError("atomic durable commit returned an unexpected event_count")
        return commit_result

    def _finalize(
        self,
        *,
        planning_state: Mapping[str, Any],
        event_receipts: Sequence[Mapping[str, Any]] | None,
    ) -> AffectiveCycleResult:
        planning_context = self.host.build_planning_context(planning_state)
        checkpoint = self.host.export_checkpoint()
        state_version = self._next_state_version
        state_row = checkpoint_to_state_row(
            checkpoint,
            host_scope=self.host_scope,
            state_version=state_version,
        )

        receipt_copies = [dict(receipt) for receipt in (event_receipts or ())]
        event_rows = [event_receipt_to_event_row(self.host, receipt) for receipt in receipt_copies]
        expected_prior_version = state_version - 1
        commit_request = build_atomic_commit_request(
            state_row,
            event_rows,
            expected_prior_version=expected_prior_version,
        )
        resume_token = build_affective_resume_token(state_row)

        commit_result: Any = None
        atomic_commit_used = self.atomic_commit_writer is not None
        if self.atomic_commit_writer is not None:
            try:
                commit_result = self.atomic_commit_writer(dict(commit_request))
                self._validate_atomic_commit_ack(
                    commit_result,
                    state_version=state_version,
                    checkpoint_sha256=state_row["checkpoint_sha256"],
                    event_count=len(event_rows),
                )
            except Exception:
                # The host has already advanced in memory. Without an exact
                # provider acknowledgement, the durable outcome/frontier is not
                # known well enough to continue from this object safely.
                self._durability_uncertain = True
                raise
        else:
            # Backward-compatible in-memory/test path only. A qualified durable
            # provider must bind atomic_commit_writer so stale state and event
            # append cannot split across transactions.
            if self.state_writer is not None:
                self.state_writer(dict(state_row))
            if self.event_writer is not None:
                for row in event_rows:
                    self.event_writer(dict(row))

        self._next_state_version += 1
        last_receipt = receipt_copies[-1] if receipt_copies else None
        last_event_row = event_rows[-1] if event_rows else None
        return AffectiveCycleResult(
            planning_context=dict(planning_context),
            machine_interoception=self.host.machine_interoception(),
            checkpoint=dict(checkpoint),
            state_row=dict(state_row),
            event_receipt=dict(last_receipt) if last_receipt is not None else None,
            event_row=dict(last_event_row) if last_event_row is not None else None,
            event_receipts=receipt_copies,
            event_rows=[dict(row) for row in event_rows],
            resume_token=dict(resume_token),
            commit_request=dict(commit_request),
            commit_result=commit_result,
            atomic_commit_used=atomic_commit_used,
        )

    def process_turn(
        self,
        appraisal: StimulusAppraisal,
        *,
        planning_state: Mapping[str, Any],
        elapsed_seconds: float = 0.0,
    ) -> AffectiveCycleResult:
        self._require_usable_frontier()
        observed = self.host.observe(appraisal, elapsed_seconds=elapsed_seconds)
        receipts = observed.get("event_receipts") or []
        return self._finalize(planning_state=planning_state, event_receipts=receipts)

    def force_admin_test(
        self,
        *,
        authorized: bool,
        planning_state: Mapping[str, Any],
    ) -> AffectiveCycleResult:
        self._require_usable_frontier()
        receipt = self.host.force_admin_test(authorized=authorized)
        return self._finalize(planning_state=planning_state, event_receipts=[receipt])

    def force_self_qualification(
        self,
        *,
        authorized: bool,
        planning_state: Mapping[str, Any],
    ) -> AffectiveCycleResult:
        self._require_usable_frontier()
        receipt = self.host.force_self_qualification(authorized=authorized)
        return self._finalize(planning_state=planning_state, event_receipts=[receipt])

    def advance_time(
        self,
        elapsed_seconds: float,
        *,
        planning_state: Mapping[str, Any],
    ) -> AffectiveCycleResult:
        self._require_usable_frontier()
        advanced = self.host.advance_time(elapsed_seconds)
        receipts = advanced.get("event_receipts") or []
        return self._finalize(planning_state=planning_state, event_receipts=receipts)
