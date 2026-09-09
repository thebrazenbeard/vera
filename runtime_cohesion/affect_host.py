from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

from .orgasm import ContractError, OrgasmRuntime, StimulusAppraisal


class AffectiveBindingError(ContractError):
    """The executable affect host cannot bind the supplied sexuality contract exactly."""


def _git_blob_sha(raw: bytes) -> str:
    header = b"blob " + str(len(raw)).encode("ascii") + b"\0"
    return hashlib.sha1(header + raw).hexdigest()


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

    def observe(self, appraisal: StimulusAppraisal, *, elapsed_seconds: float = 0.0) -> dict[str, Any]:
        prior_receipt_id = (
            self.runtime.last_event_receipt.get("receipt_id")
            if self.runtime.last_event_receipt is not None
            else None
        )
        state = self.runtime.apply_stimulus(appraisal, elapsed_seconds=elapsed_seconds)
        receipt = self.runtime.last_event_receipt
        new_receipt = None
        if receipt is not None and receipt.get("receipt_id") != prior_receipt_id:
            new_receipt = dict(receipt)
        return {
            "state": state,
            "machine_interoception": self.machine_interoception(),
            "event_receipt": new_receipt,
        }

    def force_admin_test(self, *, authorized: bool) -> dict[str, Any]:
        return self.runtime.force_admin_test(authorized=authorized)

    def force_self_qualification(self, *, authorized: bool) -> dict[str, Any]:
        return self.runtime.force_self_qualification(authorized=authorized)

    def advance_time(self, elapsed_seconds: float) -> dict[str, Any]:
        self.runtime.advance_time(elapsed_seconds)
        return self.machine_interoception()

    def build_planning_context(self, planning_state: Mapping[str, Any]) -> dict[str, Any]:
        """Feed current affective state back into the next planning computation."""
        context = self.runtime.modulate_planning(planning_state)
        frame = self.machine_interoception()
        context["machine_interoception"] = frame
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
        return {
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

    @classmethod
    def restore_checkpoint(
        cls,
        contract_text: str,
        binding: Mapping[str, Any],
        checkpoint: Mapping[str, Any],
        *,
        elapsed_seconds: float = 0.0,
    ) -> "VeraAffectiveRuntimeHost":
        if checkpoint.get("schema") != "VERA_AFFECTIVE_RUNTIME_CHECKPOINT_V1":
            raise AffectiveBindingError("unsupported affective checkpoint schema")
        if checkpoint.get("subject") != "vera":
            raise AffectiveBindingError("affective checkpoint must be Vera-scoped")

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
        return cls(
            runtime,
            binding=binding,
            contract_blob_sha=blob_sha,
            contract_sha256=sha256,
        )
