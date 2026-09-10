from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence

from .affect_host import VeraAffectiveRuntimeHost
from .affect_persistence import (
    build_affective_resume_token,
    build_atomic_commit_request,
    checkpoint_to_state_row,
    event_receipt_to_event_row,
    restore_host_from_state_row,
)
from .affect_scope import (
    _provider_bound_atomic_writer_matches,
    bind_affective_host_scope,
    require_affective_host_cycle_eligible,
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
    resume_token: dict[str, Any] | None
    commit_request: dict[str, Any] | None
    commit_result: Any
    atomic_commit_used: bool
    durability_mode: str


class VeraAffectiveCycle:
    """One executable Vera affective/interoceptive runtime loop.

    Production ``ATOMIC_DURABLE`` status is not inferred from a truthy callback.
    It requires an internal provider-bound writer capability tied to the exact
    provider-CURRENT host attestation. Arbitrary callbacks are accepted only via
    an explicit non-qualifying atomic test seam and cannot mint provider resume
    tokens, production commit schemas, or CURRENT provider-state evidence.
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
        non_atomic_test_mode: bool = False,
        non_qualifying_atomic_test_mode: bool = False,
    ) -> None:
        if not host_scope:
            raise ValueError("host_scope is required")
        if initial_state_version < 1:
            raise ValueError("initial_state_version must be positive")
        if not isinstance(non_atomic_test_mode, bool):
            raise ValueError("non_atomic_test_mode must be boolean")
        if not isinstance(non_qualifying_atomic_test_mode, bool):
            raise ValueError("non_qualifying_atomic_test_mode must be boolean")
        for label, writer in (
            ("state_writer", state_writer),
            ("event_writer", event_writer),
            ("atomic_commit_writer", atomic_commit_writer),
        ):
            if writer is not None and not callable(writer):
                raise TypeError(f"{label} must be callable when supplied")

        split_writer_requested = state_writer is not None or event_writer is not None
        provider_bound_atomic = (
            atomic_commit_writer is not None
            and _provider_bound_atomic_writer_matches(atomic_commit_writer, host, host_scope)
        )

        if atomic_commit_writer is not None and split_writer_requested:
            raise ValueError("atomic mode cannot be combined with split state/event writers")
        if split_writer_requested and not non_atomic_test_mode:
            raise ValueError(
                "split state/event writers are non-atomic; explicitly enable non_atomic_test_mode for bounded tests"
            )
        if non_atomic_test_mode and not split_writer_requested:
            raise ValueError("non_atomic_test_mode requires at least one split state/event writer")
        if non_qualifying_atomic_test_mode and atomic_commit_writer is None:
            raise ValueError("non_qualifying_atomic_test_mode requires atomic_commit_writer")
        if non_qualifying_atomic_test_mode and split_writer_requested:
            raise ValueError("non-qualifying atomic test mode cannot mix split writers")
        if provider_bound_atomic and non_qualifying_atomic_test_mode:
            raise ValueError("provider-bound production writer cannot be downgraded to test mode")
        if atomic_commit_writer is not None and not provider_bound_atomic and not non_qualifying_atomic_test_mode:
            raise ValueError(
                "production atomic durability requires a runtime-owned provider-bound writer; arbitrary callbacks require explicit non_qualifying_atomic_test_mode"
            )

        require_affective_host_cycle_eligible(host)
        bind_affective_host_scope(host, host_scope)
        self.host = host
        self.host_scope = host_scope
        self.state_writer = state_writer
        self.event_writer = event_writer
        self.atomic_commit_writer = atomic_commit_writer
        self.non_atomic_test_mode = non_atomic_test_mode
        self.non_qualifying_atomic_test_mode = non_qualifying_atomic_test_mode
        self._provider_qualified_atomic_writer = provider_bound_atomic

        if provider_bound_atomic:
            self.durability_mode = "ATOMIC_DURABLE"
        elif atomic_commit_writer is not None:
            self.durability_mode = "NON_QUALIFYING_ATOMIC_TEST"
        elif split_writer_requested:
            self.durability_mode = "NON_ATOMIC_TEST"
        else:
            self.durability_mode = "EPHEMERAL"
        self._next_state_version = initial_state_version
        self._durability_uncertain = False

    @classmethod
    def restore_from_state_row(
        cls,
        contract_text: str,
        binding: Mapping[str, Any],
        row: Mapping[str, Any],
        *,
        host_scope: str,
        expected_checkpoint_sha256: str,
        elapsed_seconds: float = 0.0,
        state_writer: StateWriter | None = None,
        event_writer: EventWriter | None = None,
        atomic_commit_writer: AtomicCommitWriter | None = None,
        non_qualifying_atomic_test_mode: bool = False,
    ) -> "VeraAffectiveCycle":
        """Low-level replay restore; never a provider-current production path.

        Durable row bytes, embedded lifecycle labels, checkpoint pins, and a
        caller callback cannot establish provider CURRENT provenance. The host
        reconstructed here remains replay-only and therefore cannot enter a live
        cycle. Production continuation uses ``restore_current_affective_cycle``
        from runtime-owned provider composition.
        """
        split_writer_requested = state_writer is not None or event_writer is not None
        if split_writer_requested:
            raise ValueError("low-level row restore cannot become a live cycle through split writers")
        if atomic_commit_writer is None:
            raise ValueError(
                "low-level row restore is replay-only; production live restore requires runtime-owned provider composition"
            )
        if not callable(atomic_commit_writer):
            raise TypeError("atomic_commit_writer must be callable when supplied")

        state_version = row.get("state_version")
        if isinstance(state_version, bool) or not isinstance(state_version, int) or state_version < 1:
            raise ValueError("durable state row requires a positive integer state_version")
        if row.get("lifecycle_status") != "CURRENT":
            raise ValueError("row replay restore requires lifecycle_status CURRENT bytes")
        row_host_scope = row.get("host_scope")
        if not isinstance(row_host_scope, str) or not row_host_scope:
            raise ValueError("durable state row requires a bound host_scope")
        if host_scope != row_host_scope:
            raise ValueError("row restore host_scope does not match durable bytes")
        host = restore_host_from_state_row(
            contract_text,
            binding,
            row,
            expected_host_scope=host_scope,
            elapsed_seconds=elapsed_seconds,
            expected_checkpoint_sha256=expected_checkpoint_sha256,
        )
        return cls(
            host,
            host_scope=row_host_scope,
            atomic_commit_writer=atomic_commit_writer,
            initial_state_version=state_version + 1,
            non_qualifying_atomic_test_mode=non_qualifying_atomic_test_mode,
        )

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
        """Build one result without promoting test/ephemeral artifacts.

        Only an internally provider-bound ``ATOMIC_DURABLE`` cycle emits CURRENT
        state rows, the production atomic-commit schema, and a durable resume
        token. Test and ephemeral paths remain causally useful diagnostics but
        cannot manufacture provider-current evidence.
        """
        try:
            planning_context = self.host.build_planning_context(planning_state)
            checkpoint = self.host.export_checkpoint()
            state_version = self._next_state_version
            lifecycle_status = "CURRENT" if self.durability_mode == "ATOMIC_DURABLE" else "HISTORICAL"
            state_row = checkpoint_to_state_row(
                checkpoint,
                host_scope=self.host_scope,
                state_version=state_version,
                lifecycle_status=lifecycle_status,
            )

            receipt_copies = [dict(receipt) for receipt in (event_receipts or ())]
            event_rows = [event_receipt_to_event_row(self.host, receipt) for receipt in receipt_copies]
            commit_request: dict[str, Any] | None = None
            resume_token: dict[str, Any] | None = None
            commit_result: Any = None
            atomic_commit_used = self.atomic_commit_writer is not None

            if self.atomic_commit_writer is not None:
                expected_prior_version = state_version - 1
                commit_request = build_atomic_commit_request(
                    state_row,
                    event_rows,
                    expected_prior_version=expected_prior_version,
                )
                if self._provider_qualified_atomic_writer:
                    resume_token = build_affective_resume_token(state_row)
                else:
                    commit_request = dict(commit_request)
                    commit_request["schema"] = "VERA_AFFECTIVE_RUNTIME_ATOMIC_COMMIT_TEST_V1"
                commit_result = self.atomic_commit_writer(dict(commit_request))
                self._validate_atomic_commit_ack(
                    commit_result,
                    state_version=state_version,
                    checkpoint_sha256=state_row["checkpoint_sha256"],
                    event_count=len(event_rows),
                )
            else:
                if self.state_writer is not None:
                    self.state_writer(dict(state_row))
                if self.event_writer is not None:
                    for row in event_rows:
                        self.event_writer(dict(row))
        except Exception:
            self._durability_uncertain = True
            raise

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
            resume_token=dict(resume_token) if resume_token is not None else None,
            commit_request=dict(commit_request) if commit_request is not None else None,
            commit_result=commit_result,
            atomic_commit_used=atomic_commit_used,
            durability_mode=self.durability_mode,
        )

    def process_turn(
        self,
        appraisal: StimulusAppraisal,
        *,
        planning_state: Mapping[str, Any],
        context_subject: Mapping[str, Any] | None = None,
        elapsed_seconds: float = 0.0,
    ) -> AffectiveCycleResult:
        self._require_usable_frontier()
        if context_subject is None:
            observed = self.host.observe(appraisal, elapsed_seconds=elapsed_seconds)
        else:
            observed = self.host._authority_boundary.observe(
                self.host,
                appraisal,
                context_subject=context_subject,
                elapsed_seconds=elapsed_seconds,
            )
        receipts = observed.get("event_receipts") or []
        return self._finalize(planning_state=planning_state, event_receipts=receipts)

    def force_admin_test(
        self,
        *,
        authorization_subject: Mapping[str, Any],
        planning_state: Mapping[str, Any],
    ) -> AffectiveCycleResult:
        self._require_usable_frontier()
        self.host.force_admin_test(authorization_subject=authorization_subject)
        receipts = self.host.drain_event_receipts()
        return self._finalize(planning_state=planning_state, event_receipts=receipts)

    def force_self_qualification(
        self,
        *,
        authorization_subject: Mapping[str, Any],
        planning_state: Mapping[str, Any],
    ) -> AffectiveCycleResult:
        self._require_usable_frontier()
        self.host.force_self_qualification(authorization_subject=authorization_subject)
        receipts = self.host.drain_event_receipts()
        return self._finalize(planning_state=planning_state, event_receipts=receipts)

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
