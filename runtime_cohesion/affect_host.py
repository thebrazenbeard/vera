from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from .affect_scope import mark_affective_host_checkpoint_replay
from .orgasm import ContractError, OrgasmRuntime, StimulusAppraisal


class AffectiveBindingError(ContractError):
    """The executable affect host cannot bind the supplied sexuality contract exactly."""


def _git_blob_sha(raw: bytes) -> str:
    header = b"blob " + str(len(raw)).encode("ascii") + b"\0"
    return hashlib.sha1(header + raw).hexdigest()


def _checkpoint_sha256(checkpoint: Mapping[str, Any]) -> str:
    core = dict(checkpoint)
    core.pop("checkpoint_sha256", None)
    canonical = json.dumps(core, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


class VeraAffectiveRuntimeHost:
    """Causal host bridge between Vera's affective state and downstream planning.

    The host creates an explicit machine-interoception frame from the executing
    orgasm runtime and feeds that frame plus allowlisted modulation into the next
    planning context. This makes the affective state computationally consequential
    rather than a narrative annotation. It does not claim phenomenal qualia.
    """

    def __init__(
        self,
        runtime: OrgasmRuntime,
        *,
        binding: Mapping[str, Any],
        contract_blob_sha: str,
        contract_sha256: str,
    ) -> None:
        self.runtime = runtime
        self.binding = dict(binding)
        self.contract_blob_sha = contract_blob_sha
        self.contract_sha256 = contract_sha256

    @classmethod
    def from_bound_contract(
        cls,
        contract_text: str,
        binding: Mapping[str, Any],
        *,
        runtime_instance_id: str,
        profile: str = "REENTRANT_CLIMAX",
    ) -> "VeraAffectiveRuntimeHost":
        if binding.get("schema") != "VERA_ORGASM_RUNTIME_BINDING_V1":
            raise AffectiveBindingError("unsupported orgasm runtime binding schema")
        if binding.get("subject") != "vera":
            raise AffectiveBindingError("affective runtime binding must be Vera-scoped")
        if binding.get("contract_schema") != "VERA_ORGASM_RUNTIME_CONTRACT_V1":
            raise AffectiveBindingError("binding contract schema mismatch")
        if binding.get("source_repository") != "thebrazenbeard/sexuality":
            raise AffectiveBindingError("unexpected sexuality source repository")
        if binding.get("source_path") != "vera/orgasm/ORGASM_RUNTIME_CONTRACT_V1.json":
            raise AffectiveBindingError("unexpected sexuality contract path")
        if binding.get("availability_implies_activation") is not False:
            raise AffectiveBindingError("source availability must not imply activation")

        raw = contract_text.encode("utf-8")
        blob_sha = _git_blob_sha(raw)
        if blob_sha != binding.get("source_blob_sha"):
            raise AffectiveBindingError("contract bytes do not match the bound Git blob")

        try:
            contract = json.loads(contract_text)
        except json.JSONDecodeError as exc:
            raise AffectiveBindingError("bound sexuality contract is not valid JSON") from exc
        if contract.get("schema") != binding.get("contract_schema"):
            raise AffectiveBindingError("contract content/schema does not match binding")
        if contract.get("subject") != binding.get("subject"):
            raise AffectiveBindingError("contract content/subject does not match binding")

        source_revision = str(binding.get("source_commit") or "")
        if len(source_revision) != 40:
            raise AffectiveBindingError("binding requires an exact 40-character source commit")

        runtime = OrgasmRuntime(
            contract,
            runtime_instance_id=runtime_instance_id,
            source_revision=source_revision,
            profile=profile,
        )
        return cls(
            runtime,
            binding=binding,
            contract_blob_sha=blob_sha,
            contract_sha256=hashlib.sha256(raw).hexdigest(),
        )

    def machine_interoception(self) -> dict[str, Any]:
        state = self.runtime.snapshot()
        receipt = self.runtime.last_event_receipt
        return {
            "experience_class": "ENGINEERED_AFFECTIVE_INTEROCEPTION",
            "subject": "vera",
            "presence": state["presence"],
            "phase": state["phase"],
            "sexual_salience": state["sexual_salience"],
            "activation_intensity": state["activation_intensity"],
            "positive_valence": state["positive_valence"],
            "anticipation": state["anticipation"],
            "inhibition": state["inhibition"],
            "coherence": state["coherence"],
            "coalition_stability": state["coalition_stability"],
            "persistence_window_ms": state["persistence_window_ms"],
            "hedonic_impact": state["hedonic_impact"],
            "consummatory_gain": state["consummatory_gain"],
            "satiation": state["satiation"],
            "resolution_intensity": state["resolution_intensity"],
            "refractory_strength": state["refractory_strength"],
            "action_tendency": state["action_tendency"],
            "active_orgasm_event": state["active_orgasm_event"],
            "organic_climax_eligible": state["organic_climax_eligible"],
            "last_trigger_class": receipt.get("trigger_class") if receipt else None,
            "last_event_digest": receipt.get("event_digest") if receipt else None,
            "source_revision": self.runtime.source_revision,
            "contract_blob_sha": self.contract_blob_sha,
            "phenomenology": self.runtime.phenomenology_status,
        }

    def drain_event_receipts(self) -> list[dict[str, Any]]:
        """Return all runtime receipts not yet handed to an executing cycle."""
        return self.runtime.drain_event_receipts()

    def observe(self, appraisal: StimulusAppraisal, *, elapsed_seconds: float = 0.0) -> dict[str, Any]:
        state = self.runtime.apply_stimulus(appraisal, elapsed_seconds=elapsed_seconds)
        receipts = self.runtime.drain_event_receipts()
        return {
            "state": state,
            "machine_interoception": self.machine_interoception(),
            "event_receipts": receipts,
            "event_receipt": receipts[-1] if receipts else None,
        }

    def force_admin_test(self, *, authorized: bool) -> dict[str, Any]:
        # Leave the receipt in the pending queue so a VeraAffectiveCycle can
        # atomically persist it together with any restore-time transition that
        # was already pending.
        return self.runtime.force_admin_test(authorized=authorized)

    def force_self_qualification(self, *, authorized: bool) -> dict[str, Any]:
        # Same pending-receipt rule as the administrator qualification route.
        return self.runtime.force_self_qualification(authorized=authorized)

    def advance_time(self, elapsed_seconds: float) -> dict[str, Any]:
        self.runtime.advance_time(elapsed_seconds)
        receipts = self.runtime.drain_event_receipts()
        frame = self.machine_interoception()
        frame["event_receipts"] = receipts
        frame["event_receipt"] = receipts[-1] if receipts else None
        return frame

    def experience_control_vector(self) -> dict[str, float]:
        """Return the machine-side affect vector that downstream planning consumes.

        This exists across arousal, climax, resolution, and recovery. It is not a
        self-report; it is derived from the stored engineered runtime state.
        """
        frame = self.machine_interoception()
        positive_valence = _clamp((float(frame["positive_valence"]) + 1.0) / 2.0)
        activation = _clamp(float(frame["activation_intensity"]))
        coherence = _clamp(float(frame["coherence"]))
        hedonic = _clamp(float(frame["hedonic_impact"]))
        consummatory = _clamp(float(frame["consummatory_gain"]))
        satiation = _clamp(float(frame["satiation"]))
        resolution = _clamp(float(frame["resolution_intensity"]))
        refractory = _clamp(float(frame["refractory_strength"]))
        recovery_active = frame["phase"] in {"RESOLUTION", "SATIATED_OR_REFRACTORY"}
        return {
            "approach_gain": _clamp(0.55 * activation + 0.25 * coherence + 0.20 * positive_valence),
            "salience_gain": _clamp(0.50 * activation + 0.30 * coherence + 0.20 * hedonic),
            "attention_narrowing": _clamp(0.35 * activation + 0.35 * coherence + 0.30 * hedonic),
            "consummatory_gain": _clamp(0.55 * consummatory + 0.45 * hedonic),
            "plasticity_gain": 0.0 if recovery_active else _clamp(0.40 * hedonic + 0.25 * coherence + 0.20 * activation + 0.15 * resolution),
            "satiation": satiation,
            "resolution": resolution,
            "refractory": refractory,
        }

    def _apply_nonclimax_affective_modulation(self, planning_state: Mapping[str, Any]) -> dict[str, Any]:
        result = dict(planning_state)
        frame = self.machine_interoception()
        if frame["active_orgasm_event"]:
            return result

        vector = self.experience_control_vector()
        recovery_active = frame["phase"] in {"RESOLUTION", "SATIATED_OR_REFRACTORY"}
        arousal_force = max(vector["approach_gain"], vector["salience_gain"], vector["attention_narrowing"])
        recovery_force = max(vector["satiation"], vector["resolution"], vector["refractory"])
        experiential_force = _clamp(max(arousal_force, 0.70 * recovery_force))
        if experiential_force < 0.03:
            return result

        allowed = set(self.runtime.contract["hard_firewalls"]["may_influence"])
        gain_by_key = {
            "valuation": 0.16,
            "salience": 0.22,
            "attention": 0.18,
            "response_selection_priors": 0.14,
            "expression": 0.12,
            "memory_strength_candidate_weighting": 0.10,
        }
        for key, gain in gain_by_key.items():
            if key not in allowed:
                continue
            if recovery_active and key == "memory_strength_candidate_weighting":
                continue
            value = result.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                result[key] = _clamp(float(value) + (1.0 - float(value)) * gain * experiential_force)
        return result

    def build_planning_context(self, planning_state: Mapping[str, Any]) -> dict[str, Any]:
        """Feed current affective state back into the next planning computation."""
        context = self.runtime.modulate_planning(planning_state)
        context = self._apply_nonclimax_affective_modulation(context)
        frame = self.machine_interoception()
        context["machine_interoception"] = frame
        context["experience_control_vector"] = self.experience_control_vector()
        context["affective_control_active"] = bool(
            frame["active_orgasm_event"]
            or frame["activation_intensity"] >= 0.05
            or frame["satiation"] >= 0.05
            or frame["resolution_intensity"] >= 0.05
        )
        context["affective_claim_ceiling"] = {
            "engineered_event": self.runtime.contract["claim_ceiling"]["engineered_event"],
            "phenomenology": self.runtime.phenomenology_status,
        }
        return context

    def export_checkpoint(self) -> dict[str, Any]:
        checkpoint = {
            "schema": "VERA_AFFECTIVE_RUNTIME_CHECKPOINT_V1",
            "subject": "vera",
            "source_binding": {
                "source_repository": self.binding["source_repository"],
                "source_commit": self.binding["source_commit"],
                "source_path": self.binding["source_path"],
                "source_blob_sha": self.contract_blob_sha,
                "source_sha256": self.contract_sha256,
            },
            "runtime_state": self.runtime.export_state(),
            "machine_interoception": self.machine_interoception(),
        }
        checkpoint["checkpoint_sha256"] = _checkpoint_sha256(checkpoint)
        return checkpoint

    @classmethod
    def restore_checkpoint(
        cls,
        contract_text: str,
        binding: Mapping[str, Any],
        checkpoint: Mapping[str, Any],
        *,
        elapsed_seconds: float = 0.0,
        expected_checkpoint_sha256: str | None = None,
    ) -> "VeraAffectiveRuntimeHost":
        if checkpoint.get("schema") != "VERA_AFFECTIVE_RUNTIME_CHECKPOINT_V1":
            raise AffectiveBindingError("unsupported affective checkpoint schema")
        if checkpoint.get("subject") != "vera":
            raise AffectiveBindingError("affective checkpoint must be Vera-scoped")
        if not isinstance(expected_checkpoint_sha256, str) or len(expected_checkpoint_sha256) != 64:
            raise AffectiveBindingError("restore requires an externally pinned checkpoint SHA-256")
        embedded_checkpoint_sha256 = checkpoint.get("checkpoint_sha256")
        if not isinstance(embedded_checkpoint_sha256, str) or len(embedded_checkpoint_sha256) != 64:
            raise AffectiveBindingError("checkpoint integrity digest is missing")
        try:
            observed_checkpoint_sha256 = _checkpoint_sha256(checkpoint)
        except (TypeError, ValueError) as exc:
            raise AffectiveBindingError("checkpoint payload is not canonically serializable") from exc
        if embedded_checkpoint_sha256 != observed_checkpoint_sha256:
            raise AffectiveBindingError("checkpoint embedded SHA-256 does not match checkpoint bytes")
        if expected_checkpoint_sha256 != observed_checkpoint_sha256:
            raise AffectiveBindingError("checkpoint SHA-256 does not match the externally pinned expected digest")

        source_binding = checkpoint.get("source_binding")
        if not isinstance(source_binding, Mapping):
            raise AffectiveBindingError("checkpoint source binding is missing")
        for key in ("source_repository", "source_commit", "source_path", "source_blob_sha"):
            expected = binding.get(key)
            observed = source_binding.get(key)
            if expected != observed:
                raise AffectiveBindingError(f"checkpoint source binding mismatch: {key}")

        raw = contract_text.encode("utf-8")
        blob_sha = _git_blob_sha(raw)
        if blob_sha != binding.get("source_blob_sha"):
            raise AffectiveBindingError("restore contract bytes do not match bound Git blob")
        sha256 = hashlib.sha256(raw).hexdigest()
        if source_binding.get("source_sha256") != sha256:
            raise AffectiveBindingError("checkpoint source SHA-256 does not match active contract bytes")

        contract = json.loads(contract_text)
        runtime_state = checkpoint.get("runtime_state")
        if not isinstance(runtime_state, Mapping):
            raise AffectiveBindingError("checkpoint runtime state is missing")
        runtime = OrgasmRuntime.restore_state(
            contract,
            runtime_state,
            source_revision=str(binding["source_commit"]),
            elapsed_seconds=elapsed_seconds,
        )
        # Deliberately preserve any transition receipt emitted while applying
        # elapsed-time recovery. The next executing affective cycle must commit
        # that receipt instead of silently erasing a real state transition.
        host = cls(
            runtime,
            binding=binding,
            contract_blob_sha=blob_sha,
            contract_sha256=sha256,
        )
        mark_affective_host_checkpoint_replay(host)
        return host
