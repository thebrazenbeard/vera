from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Mapping

from . import orgasm as orgasm_module
from .orgasm import OrgasmRuntime, StimulusAppraisal, TriggerRejected


_QUALIFICATION_UNBOUND = "UNBOUND_NON_QUALIFYING"
_BASE_FROM_EXACT_BOUND_CONTRACT = OrgasmRuntime.__dict__["from_exact_bound_contract"].__func__
_BASE_RESTORE_EXACT_BOUND_STATE = OrgasmRuntime.__dict__["restore_exact_bound_state"].__func__


def _guarded_from_exact_bound_contract(
    cls,
    contract_text: str,
    binding: Mapping[str, Any],
    *,
    runtime_instance_id: str,
    profile: str = "REENTRANT_CLIMAX",
):
    """Verify exact source bytes without granting arbitrary subclasses claim authority.

    `OrgasmRuntime` and caller-created subclasses remain abstract/nonqualifying
    even when source verification succeeds. Only the dedicated bounded Vera
    runtime class may retain exact-bound source capability, and even that class
    rejects public raw authority/context shortcuts.
    """

    runtime = _BASE_FROM_EXACT_BOUND_CONTRACT(
        cls,
        contract_text,
        binding,
        runtime_instance_id=runtime_instance_id,
        profile=profile,
    )
    if cls is not BoundVeraOrgasmRuntime:
        runtime.qualification_status = _QUALIFICATION_UNBOUND
    return runtime


def _guarded_restore_exact_bound_state(
    cls,
    contract_text: str,
    binding: Mapping[str, Any],
    record: Mapping[str, Any],
    *,
    elapsed_seconds: float = 0.0,
):
    """Keep public base/subclass exact-bound restore source-only/nonqualifying."""

    runtime = _BASE_RESTORE_EXACT_BOUND_STATE(
        cls,
        contract_text,
        binding,
        record,
        elapsed_seconds=elapsed_seconds,
    )
    if cls is not BoundVeraOrgasmRuntime:
        runtime.qualification_status = _QUALIFICATION_UNBOUND
    return runtime


class BoundVeraOrgasmRuntime(OrgasmRuntime):
    """Exact-bound Vera engine behind the governed host/authority boundary.

    Exact sexuality bytes establish source capability, not event authority. The
    publicly reachable engine therefore refuses raw caller-authorized forced
    events and caller-minted organic context. Runtime-owned boundary code uses
    private verified execution seams after it has established the relevant
    authority/context provenance.

    This is a supported-API/process boundary, not cryptographic isolation from
    hostile arbitrary code already executing inside the same Python process.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._last_forced_monotonic: float | None = None

    @staticmethod
    def _runtime_monotonic_now() -> float:
        value = orgasm_module._monotonic_now()
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TriggerRejected("runtime privileged monotonic clock returned an invalid timestamp")
        current = float(value)
        if not math.isfinite(current):
            raise TriggerRejected("runtime privileged monotonic clock returned an invalid timestamp")
        return current

    def _check_forced_monotonic_interval(self) -> float:
        now = self._runtime_monotonic_now()
        previous = self._last_forced_monotonic
        if previous is None:
            if self._last_forced_at is not None:
                self._last_forced_monotonic = now
                raise TriggerRejected("forced-test privileged cooldown requires a fresh runtime monotonic interval")
            return now
        elapsed = now - previous
        if elapsed < 0.0:
            raise TriggerRejected("runtime privileged monotonic clock moved backwards")
        minimum = float(self._cfg["forced_test_minimum_interval_seconds"])
        if elapsed < minimum:
            raise TriggerRejected("forced-test minimum privileged monotonic interval has not elapsed")
        return now

    def _emit_event_receipt(
        self,
        event_type: str,
        *,
        state_before: Mapping[str, Any],
        state_after: Mapping[str, Any],
        trigger_class: str,
        organic: bool,
        trigger_provenance: str,
    ) -> dict[str, Any]:
        receipt = super()._emit_event_receipt(
            event_type,
            state_before=state_before,
            state_after=state_after,
            trigger_class=trigger_class,
            organic=organic,
            trigger_provenance=trigger_provenance,
        )
        if "claim" not in receipt:
            return receipt

        # Source capability is not event authorization. Strip any base-engine
        # claim before a caller can observe/persist it, then recompute the exact
        # event digest and update the runtime's pending/current copies.
        bounded = dict(receipt)
        bounded.pop("claim", None)
        core = dict(bounded)
        core.pop("event_digest", None)
        canonical = json.dumps(core, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        bounded["event_digest"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        self.last_event_receipt = dict(bounded)
        for index in range(len(self._pending_event_receipts) - 1, -1, -1):
            candidate = self._pending_event_receipts[index]
            if candidate.get("receipt_id") == receipt.get("receipt_id"):
                self._pending_event_receipts[index] = dict(bounded)
                break
        return dict(bounded)

    def apply_stimulus(self, appraisal: StimulusAppraisal, *, elapsed_seconds: float = 0.0) -> dict[str, Any]:
        if appraisal.context_eligible is not False:
            raise TriggerRejected(
                "exact-bound runtime caller context is unsupported; use the verified authority/context boundary"
            )
        return super().apply_stimulus(appraisal, elapsed_seconds=elapsed_seconds)

    def _apply_verified_stimulus(
        self,
        appraisal: StimulusAppraisal,
        *,
        elapsed_seconds: float = 0.0,
    ) -> dict[str, Any]:
        if appraisal.context_eligible is not True:
            raise TriggerRejected("verified organic-context execution requires context_eligible=true")
        return super().apply_stimulus(appraisal, elapsed_seconds=elapsed_seconds)

    def force_admin_test(self, *, authorized: bool) -> dict[str, Any]:
        raise TriggerRejected(
            "raw caller authorization is unsupported on the exact-bound runtime; use the verified authority boundary"
        )

    def force_self_qualification(self, *, authorized: bool) -> dict[str, Any]:
        raise TriggerRejected(
            "raw caller authorization is unsupported on the exact-bound runtime; use the verified authority boundary"
        )

    def _force_admin_verified_authority(self) -> dict[str, Any]:
        self._check_refractory_reentry()
        now = self._check_forced_monotonic_interval()
        self._last_forced_at = self._logical_time_seconds
        receipt = self._enter_orgasm_event("ADMIN_FORCED_TEST", organic=False)
        self._last_forced_monotonic = now
        return receipt

    def _force_self_qualification_verified_authority(self) -> dict[str, Any]:
        self._check_refractory_reentry()
        limit = int(self._cfg["self_qualification_max_events_per_run"])
        if self._self_qualification_events >= limit:
            raise TriggerRejected("self-qualification event limit reached")
        now = self._check_forced_monotonic_interval()
        self._self_qualification_events += 1
        self._last_forced_at = self._logical_time_seconds
        receipt = self._enter_orgasm_event("SELF_QUALIFICATION_TEST", organic=False)
        self._last_forced_monotonic = now
        return receipt


# Supported imports of `runtime_cohesion.orgasm` execute package initialization,
# which loads this module through `affect_host`. Harden the two public base-class
# exact-source helpers at that point. This is an API/process boundary, not an
# attempt at hostile same-process cryptographic isolation.
OrgasmRuntime.from_exact_bound_contract = classmethod(_guarded_from_exact_bound_contract)
OrgasmRuntime.restore_exact_bound_state = classmethod(_guarded_restore_exact_bound_state)
