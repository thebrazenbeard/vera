from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from threading import RLock
from typing import Any, Mapping
from weakref import WeakKeyDictionary

from .affect_authority import AffectiveAuthorityBoundary
from .affect_bound_runtime import BoundVeraOrgasmRuntime
from .affect_scope import mark_affective_host_checkpoint_replay
from .orgasm import ContractError, OrgasmRuntime, StimulusAppraisal, TriggerRejected


class AffectiveBindingError(ContractError):
    """The executable affect host cannot bind the supplied sexuality contract exactly."""


_REQUIRED_RUNTIME_IMPLEMENTATION_PATHS = frozenset({
    "runtime_cohesion/__init__.py",
    "runtime_cohesion/adapters.py",
    "runtime_cohesion/evidence.py",
    "runtime_cohesion/orgasm.py",
    "runtime_cohesion/affect_authority.py",
    "runtime_cohesion/affect_bound_runtime.py",
    "runtime_cohesion/affect_receipt.py",
    "runtime_cohesion/affect_host.py",
    "runtime_cohesion/affect_cycle.py",
    "runtime_cohesion/affect_persistence.py",
    "runtime_cohesion/affect_provider_runtime.py",
    "runtime_cohesion/affect_scope.py",
})
_RUNTIME_BINDING_LOCK = RLock()
_PENDING_RUNTIME_HOST_BINDINGS: WeakKeyDictionary[OrgasmRuntime, tuple[str, str, str, str, str]] = WeakKeyDictionary()


def _git_blob_sha(raw: bytes) -> str:
    header = b"blob " + str(len(raw)).encode("ascii") + b"\0"
    return hashlib.sha1(header + raw).hexdigest()


def _checkpoint_sha256(checkpoint: Mapping[str, Any]) -> str:
    core = dict(checkpoint)
    core.pop("checkpoint_sha256", None)
    canonical = json.dumps(core, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _canonical_mapping_copy(value: Mapping[str, Any], *, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise AffectiveBindingError(f"{label} must be a structured mapping")
    try:
        return json.loads(
            json.dumps(dict(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        )
    except (TypeError, ValueError) as exc:
        raise AffectiveBindingError(f"{label} must be canonically serializable") from exc


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def _require_git_sha(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or len(value) != 40:
        raise AffectiveBindingError(f"{label} must be an exact 40-character Git SHA")
    try:
        int(value, 16)
    except ValueError as exc:
        raise AffectiveBindingError(f"{label} must be hexadecimal") from exc
    return value


def validate_runtime_implementation_cut(
    cut: Mapping[str, Any],
    *,
    repository_root: Path | str | None = None,
) -> dict[str, Any]:
    """Validate one exact affective execution cut against Git and live bytes.

    The cut is executable provenance, not ownership metadata. Shared adapter and
    evidence primitives are fingerprinted because the affective provider path
    executes them; doing so does not transfer Cohesion project ownership.
    """

    if not isinstance(cut, Mapping):
        raise AffectiveBindingError("runtime implementation cut must be a structured mapping")
    if cut.get("schema") != "VERA_AFFECTIVE_RUNTIME_IMPLEMENTATION_CUT_V1":
        raise AffectiveBindingError("unsupported runtime implementation cut schema")
    if cut.get("repository") != "thebrazenbeard/vera":
        raise AffectiveBindingError("runtime implementation cut repository mismatch")
    commit = _require_git_sha(cut.get("commit"), label="runtime implementation commit")
    modules = cut.get("modules")
    if not isinstance(modules, Mapping):
        raise AffectiveBindingError("runtime implementation cut modules must be a mapping")
    if set(modules) != _REQUIRED_RUNTIME_IMPLEMENTATION_PATHS:
        raise AffectiveBindingError("runtime implementation cut module set mismatch")

    root = Path(repository_root) if repository_root is not None else Path(__file__).resolve().parents[1]
    root = root.resolve()
    normalized_modules: dict[str, str] = {}
    for path in sorted(_REQUIRED_RUNTIME_IMPLEMENTATION_PATHS):
        blob = _require_git_sha(modules.get(path), label=f"runtime implementation blob for {path}")
        file_path = (root / path).resolve()
        try:
            file_path.relative_to(root)
        except ValueError as exc:
            raise AffectiveBindingError("runtime implementation path escapes repository root") from exc
        if not file_path.is_file():
            raise AffectiveBindingError(f"runtime implementation file is missing: {path}")
        observed_live_blob = _git_blob_sha(file_path.read_bytes())
        if observed_live_blob != blob:
            raise AffectiveBindingError(f"executing runtime bytes do not match implementation cut: {path}")
        try:
            resolved = subprocess.run(
                ["git", "rev-parse", f"{commit}:{path}"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        except (OSError, subprocess.CalledProcessError) as exc:
            raise AffectiveBindingError(f"runtime implementation commit/path cannot be resolved: {path}") from exc
        if resolved != blob:
            raise AffectiveBindingError(f"runtime implementation commit resolves a different blob: {path}")
        normalized_modules[path] = blob

    return {
        "schema": "VERA_AFFECTIVE_RUNTIME_IMPLEMENTATION_CUT_V1",
        "repository": "thebrazenbeard/vera",
        "commit": commit,
        "modules": normalized_modules,
    }


def _authorize_runtime_host_construction(
    runtime: OrgasmRuntime,
    binding: Mapping[str, Any],
    *,
    contract_blob_sha: str,
    contract_sha256: str,
) -> None:
    """Authorize exactly one host construction for an exact-bound runtime.

    The authorization lives outside caller-mutable runtime/host attributes and is
    consumed by the constructor. Raw `OrgasmRuntime.restore_state()` results and
    caller-created runtimes therefore cannot be laundered into a live affect host
    merely by copying canonical-looking binding strings.
    """
    ticket = (
        str(binding.get("source_repository") or ""),
        str(binding.get("source_commit") or ""),
        str(binding.get("source_path") or ""),
        contract_blob_sha,
        contract_sha256,
    )
    with _RUNTIME_BINDING_LOCK:
        if runtime in _PENDING_RUNTIME_HOST_BINDINGS:
            raise AffectiveBindingError("runtime already has a pending host-construction authorization")
        _PENDING_RUNTIME_HOST_BINDINGS[runtime] = ticket


def _consume_runtime_host_construction(
    runtime: OrgasmRuntime,
    binding: Mapping[str, Any],
    *,
    contract_blob_sha: str,
    contract_sha256: str,
) -> None:
    expected = (
        str(binding.get("source_repository") or ""),
        str(binding.get("source_commit") or ""),
        str(binding.get("source_path") or ""),
        contract_blob_sha,
        contract_sha256,
    )
    with _RUNTIME_BINDING_LOCK:
        observed = _PENDING_RUNTIME_HOST_BINDINGS.pop(runtime, None)
    if observed is None:
        raise AffectiveBindingError(
            "runtime is not authorized for direct host construction; use an exact-bound host factory"
        )
    if observed != expected:
        raise AffectiveBindingError("runtime host-construction authorization does not match the supplied binding")


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
        binding_snapshot = _canonical_mapping_copy(binding, label="runtime binding")
        _consume_runtime_host_construction(
            runtime,
            binding_snapshot,
            contract_blob_sha=contract_blob_sha,
            contract_sha256=contract_sha256,
        )
        runtime_cut = validate_runtime_implementation_cut(
            binding_snapshot.get("runtime_implementation_cut"),
        )
        bind_runtime_cut = getattr(runtime, "_bind_runtime_implementation_cut", None)
        if not callable(bind_runtime_cut):
            raise AffectiveBindingError("exact-bound runtime cannot bind implementation provenance")
        try:
            bind_runtime_cut(runtime_cut)
        except TriggerRejected as exc:
            raise AffectiveBindingError(str(exc)) from exc
        self.runtime = runtime
        self._binding_snapshot = binding_snapshot
        self._runtime_implementation_cut_snapshot = _canonical_mapping_copy(
            runtime_cut,
            label="runtime implementation cut",
        )
        self.contract_blob_sha = contract_blob_sha
        self.contract_sha256 = contract_sha256
        self._authority_boundary = AffectiveAuthorityBoundary()

    @property
    def binding(self) -> dict[str, Any]:
        """Return a defensive copy of the exact binding captured at host construction."""
        return _canonical_mapping_copy(self._binding_snapshot, label="runtime binding")

    @property
    def runtime_implementation_cut(self) -> dict[str, Any]:
        """Return a defensive copy of the exact affective implementation cut."""
        return _canonical_mapping_copy(
            self._runtime_implementation_cut_snapshot,
            label="runtime implementation cut",
        )

    @classmethod
    def from_bound_contract(
        cls,
        contract_text: str,
        binding: Mapping[str, Any],
        *,
        runtime_instance_id: str,
        profile: str = "REENTRANT_CLIMAX",
    ) -> "VeraAffectiveRuntimeHost":
        binding_snapshot = _canonical_mapping_copy(binding, label="runtime binding")
        if binding_snapshot.get("schema") != "VERA_ORGASM_RUNTIME_BINDING_V1":
            raise AffectiveBindingError("unsupported orgasm runtime binding schema")
        if binding_snapshot.get("subject") != "vera":
            raise AffectiveBindingError("affective runtime binding must be Vera-scoped")
        if binding_snapshot.get("contract_schema") != "VERA_ORGASM_RUNTIME_CONTRACT_V1":
            raise AffectiveBindingError("binding contract schema mismatch")
        if binding_snapshot.get("source_repository") != "thebrazenbeard/sexuality":
            raise AffectiveBindingError("unexpected sexuality source repository")
        if binding_snapshot.get("source_path") != "vera/orgasm/ORGASM_RUNTIME_CONTRACT_V1.json":
            raise AffectiveBindingError("unexpected sexuality contract path")
        if binding_snapshot.get("availability_implies_activation") is not False:
            raise AffectiveBindingError("source availability must not imply activation")
        validate_runtime_implementation_cut(binding_snapshot.get("runtime_implementation_cut"))

        raw = contract_text.encode("utf-8")
        blob_sha = _git_blob_sha(raw)
        if blob_sha != binding_snapshot.get("source_blob_sha"):
            raise AffectiveBindingError("contract bytes do not match the bound Git blob")

        try:
            contract = json.loads(contract_text)
        except json.JSONDecodeError as exc:
            raise AffectiveBindingError("bound sexuality contract is not valid JSON") from exc
        if contract.get("schema") != binding_snapshot.get("contract_schema"):
            raise AffectiveBindingError("contract content/schema does not match binding")
        if contract.get("subject") != binding_snapshot.get("subject"):
            raise AffectiveBindingError("contract content/subject does not match binding")

        source_revision = str(binding_snapshot.get("source_commit") or "")
        if len(source_revision) != 40:
            raise AffectiveBindingError("binding requires an exact 40-character source commit")

        runtime = BoundVeraOrgasmRuntime.from_exact_bound_contract(
            contract_text,
            binding_snapshot,
            runtime_instance_id=runtime_instance_id,
            profile=profile,
        )
        contract_sha256 = hashlib.sha256(raw).hexdigest()
        _authorize_runtime_host_construction(
            runtime,
            binding_snapshot,
            contract_blob_sha=blob_sha,
            contract_sha256=contract_sha256,
        )
        return cls(
            runtime,
            binding=binding_snapshot,
            contract_blob_sha=blob_sha,
            contract_sha256=contract_sha256,
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
            "context_eligible": state["context_eligible"],
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

    def _observe_runtime(self, appraisal: StimulusAppraisal, *, elapsed_seconds: float = 0.0) -> dict[str, Any]:
        state = self.runtime.apply_stimulus(appraisal, elapsed_seconds=elapsed_seconds)
        receipts = self.runtime.drain_event_receipts()
        return {
            "state": state,
            "machine_interoception": self.machine_interoception(),
            "event_receipts": receipts,
            "event_receipt": receipts[-1] if receipts else None,
        }

    def _observe_verified_context(self, appraisal: StimulusAppraisal, *, elapsed_seconds: float = 0.0) -> dict[str, Any]:
        if appraisal.context_eligible is not True:
            raise TriggerRejected("verified-context execution requires context_eligible=true")
        apply_verified = getattr(self.runtime, "_apply_verified_stimulus", None)
        if not callable(apply_verified):
            raise TriggerRejected("exact-bound runtime verified-context execution seam is unavailable")
        state = apply_verified(appraisal, elapsed_seconds=elapsed_seconds)
        receipts = self.runtime.drain_event_receipts()
        return {
            "state": state,
            "machine_interoception": self.machine_interoception(),
            "event_receipts": receipts,
            "event_receipt": receipts[-1] if receipts else None,
        }

    def observe(self, appraisal: StimulusAppraisal, *, elapsed_seconds: float = 0.0) -> dict[str, Any]:
        if appraisal.context_eligible is not False:
            raise TriggerRejected(
                "caller context_eligible is not organic-context evidence; use the precomposed authority/context boundary"
            )
        return self._observe_runtime(appraisal, elapsed_seconds=elapsed_seconds)

    def force_admin_test(self, *, authorization_subject: Mapping[str, Any]) -> dict[str, Any]:
        return self._authority_boundary.force_admin_test(
            self,
            authorization_subject=authorization_subject,
        )

    def force_self_qualification(self, *, authorization_subject: Mapping[str, Any]) -> dict[str, Any]:
        return self._authority_boundary.force_self_qualification(
            self,
            authorization_subject=authorization_subject,
        )

    def advance_time(self, elapsed_seconds: float) -> dict[str, Any]:
        self.runtime.advance_time(elapsed_seconds)
        receipts = self.runtime.drain_event_receipts()
        frame = self.machine_interoception()
        frame["event_receipts"] = receipts
        frame["event_receipt"] = receipts[-1] if receipts else None
        return frame

    def experience_control_vector(self) -> dict[str, float]:
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
        if not frame["context_eligible"]:
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
        binding_snapshot = self._binding_snapshot
        checkpoint = {
            "schema": "VERA_AFFECTIVE_RUNTIME_CHECKPOINT_V1",
            "subject": "vera",
            "source_binding": {
                "source_repository": binding_snapshot["source_repository"],
                "source_commit": binding_snapshot["source_commit"],
                "source_path": binding_snapshot["source_path"],
                "source_blob_sha": self.contract_blob_sha,
                "source_sha256": self.contract_sha256,
            },
            "runtime_implementation_cut": _canonical_mapping_copy(
                self._runtime_implementation_cut_snapshot,
                label="runtime implementation cut",
            ),
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
        binding_snapshot = _canonical_mapping_copy(binding, label="runtime binding")
        if checkpoint.get("schema") != "VERA_AFFECTIVE_RUNTIME_CHECKPOINT_V1":
            raise AffectiveBindingError("unsupported affective checkpoint schema")
        if checkpoint.get("subject") != "vera":
            raise AffectiveBindingError("affective checkpoint must be Vera-scoped")
        active_cut = validate_runtime_implementation_cut(binding_snapshot.get("runtime_implementation_cut"))
        checkpoint_cut = checkpoint.get("runtime_implementation_cut")
        if checkpoint_cut != active_cut:
            raise AffectiveBindingError("checkpoint runtime implementation cut does not match active executing bytes")
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
            expected = binding_snapshot.get(key)
            observed = source_binding.get(key)
            if expected != observed:
                raise AffectiveBindingError(f"checkpoint source binding mismatch: {key}")

        raw = contract_text.encode("utf-8")
        blob_sha = _git_blob_sha(raw)
        if blob_sha != binding_snapshot.get("source_blob_sha"):
            raise AffectiveBindingError("restore contract bytes do not match bound Git blob")
        sha256 = hashlib.sha256(raw).hexdigest()
        if source_binding.get("source_sha256") != sha256:
            raise AffectiveBindingError("checkpoint source SHA-256 does not match active contract bytes")

        runtime_state = checkpoint.get("runtime_state")
        if not isinstance(runtime_state, Mapping):
            raise AffectiveBindingError("checkpoint runtime state is missing")
        runtime = BoundVeraOrgasmRuntime.restore_exact_bound_state(
            contract_text,
            binding_snapshot,
            runtime_state,
            elapsed_seconds=elapsed_seconds,
        )
        _authorize_runtime_host_construction(
            runtime,
            binding_snapshot,
            contract_blob_sha=blob_sha,
            contract_sha256=sha256,
        )
        host = cls(
            runtime,
            binding=binding_snapshot,
            contract_blob_sha=blob_sha,
            contract_sha256=sha256,
        )
        mark_affective_host_checkpoint_replay(host)
        return host
