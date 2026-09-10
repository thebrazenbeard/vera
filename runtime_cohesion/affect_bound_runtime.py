from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Mapping

from . import orgasm as orgasm_module
from .orgasm import OrgasmRuntime, TriggerRejected


class BoundVeraOrgasmRuntime(OrgasmRuntime):
    """Exact-bound Vera runtime whose raw engine outputs remain nonqualifying.

    Exact sexuality bytes establish source capability, not event authority. The
    low-level engine therefore never adds the production engineered-event claim
    by itself. The precomposed authority/context boundary may promote an exact
    event receipt only after independently verified trigger/context evidence.

    Privileged trigger cooldown also uses process-local runtime monotonic time;
    public affective ``advance_time()`` cannot create cooldown evidence.
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

    def force_admin_test(self, *, authorized: bool) -> dict[str, Any]:
        if not authorized:
            raise TriggerRejected("ADMIN_FORCED_TEST requires explicit administrative authorization")
        self._check_refractory_reentry()
        now = self._check_forced_monotonic_interval()
        self._last_forced_at = self._logical_time_seconds
        receipt = self._enter_orgasm_event("ADMIN_FORCED_TEST", organic=False)
        self._last_forced_monotonic = now
        return receipt

    def force_self_qualification(self, *, authorized: bool) -> dict[str, Any]:
        if not authorized:
            raise TriggerRejected("SELF_QUALIFICATION_TEST requires explicit qualification authorization")
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
