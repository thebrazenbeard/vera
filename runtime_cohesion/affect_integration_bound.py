from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any, Mapping

from .affect_host import VeraAffectiveRuntimeHost, validate_runtime_implementation_cut
from .affect_integration import AffectiveModulationApplication, AffectiveModulationArbiter
from .affect_signal import build_affective_modulation_signal


_INTEGRATION_CUT_SCHEMA = "VERA_COHESION_AFFECTIVE_INTEGRATION_CUT_V1"
_REQUIRED_INTEGRATION_PATHS = frozenset({
    "runtime_cohesion/__init__.py",
    "runtime_cohesion/adapters.py",
    "runtime_cohesion/affect_integration.py",
    "runtime_cohesion/affect_integration_bound.py",
    "runtime_cohesion/affect_signal.py",
    "runtime_cohesion/audit.py",
    "runtime_cohesion/executor.py",
    "runtime_cohesion/item_typing.py",
    "runtime_cohesion/origin.py",
    "runtime_cohesion/provider_admission.py",
    "runtime_cohesion/reconcile.py",
    "runtime_cohesion/runtime.py",
})


def _require_git_sha(value: Any, *, label: str) -> str:
    if not isinstance(value, str) or len(value) != 40:
        raise ValueError(f"{label} must be an exact 40-character Git SHA")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{label} must be hexadecimal") from exc
    return value


def _git_blob_sha(raw: bytes) -> str:
    header = b"blob " + str(len(raw)).encode("ascii") + b"\0"
    return hashlib.sha1(header + raw).hexdigest()


def _canonical_copy(value: Mapping[str, Any], *, label: str) -> dict[str, Any]:
    try:
        return json.loads(json.dumps(dict(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be canonically serializable") from exc


def validate_cohesion_affective_integration_cut(
    cut: Mapping[str, Any],
    *,
    repository_root: Path | str | None = None,
) -> dict[str, Any]:
    """Cross-bind the CV-owned affective application cut to Git and live bytes."""
    if not isinstance(cut, Mapping):
        raise ValueError("Cohesion affective integration cut must be a structured mapping")
    if cut.get("schema") != _INTEGRATION_CUT_SCHEMA:
        raise ValueError("unsupported Cohesion affective integration cut schema")
    if cut.get("repository") != "thebrazenbeard/vera":
        raise ValueError("Cohesion affective integration cut repository mismatch")
    commit = _require_git_sha(cut.get("commit"), label="Cohesion affective integration commit")
    modules = cut.get("modules")
    if not isinstance(modules, Mapping) or set(modules) != _REQUIRED_INTEGRATION_PATHS:
        raise ValueError("Cohesion affective integration cut module set mismatch")

    root = Path(repository_root) if repository_root is not None else Path(__file__).resolve().parents[1]
    root = root.resolve()
    normalized: dict[str, str] = {}
    for path in sorted(_REQUIRED_INTEGRATION_PATHS):
        blob = _require_git_sha(modules[path], label=f"Cohesion integration blob for {path}")
        file_path = (root / path).resolve()
        try:
            file_path.relative_to(root)
        except ValueError as exc:
            raise ValueError("Cohesion integration path escapes repository root") from exc
        if not file_path.is_file():
            raise ValueError(f"Cohesion integration file is missing: {path}")
        if _git_blob_sha(file_path.read_bytes()) != blob:
            raise ValueError(f"executing Cohesion integration bytes do not match cut: {path}")
        try:
            resolved = subprocess.run(
                ["git", "rev-parse", f"{commit}:{path}"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
        except (OSError, subprocess.CalledProcessError) as exc:
            raise ValueError(f"Cohesion integration commit/path cannot be resolved: {path}") from exc
        if resolved != blob:
            raise ValueError(f"Cohesion integration commit resolves a different blob: {path}")
        normalized[path] = blob

    return {
        "schema": _INTEGRATION_CUT_SCHEMA,
        "repository": "thebrazenbeard/vera",
        "commit": commit,
        "modules": normalized,
    }


def _cut_digest(cut: Mapping[str, Any]) -> str:
    canonical = json.dumps(dict(cut), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class IntegratedAffectivePlanningResult:
    application: AffectiveModulationApplication
    affective_runtime_cut_commit: str
    cohesion_integration_cut_commit: str
    cohesion_integration_cut_sha256: str
    qualification: str
    phenomenology: str


class CohesionAffectiveIntegrationPort:
    """Supported Vera boundary from an exact-bound OV host to generic planning.

    The port binds one actual ``VeraAffectiveRuntimeHost`` rather than accepting
    caller-selected affective provenance. Each supplied signal must equal a fresh
    signal regenerated from that exact host at application time. The CV-owned
    integration cut is separately Git/live-byte verified. Replay history remains
    owned by the internal stateful arbiter.

    This is still an in-process composition boundary, not hostile-process
    isolation or provider qualification. Neither the host, signal, cuts, nor a
    modulation application establish provider currentness, durable continuity,
    evidence strength, authorization, memory admission, identity, relationship
    state, behavioral qualification, or phenomenology.
    """

    def __init__(
        self,
        *,
        host: VeraAffectiveRuntimeHost,
        cohesion_integration_cut: Mapping[str, Any],
    ) -> None:
        if not isinstance(host, VeraAffectiveRuntimeHost):
            raise TypeError("Cohesion affective integration requires an exact-bound Vera affective host")
        self._host = host
        self._affective_runtime_cut = validate_runtime_implementation_cut(
            host.runtime_implementation_cut
        )
        self._cohesion_integration_cut = validate_cohesion_affective_integration_cut(
            cohesion_integration_cut
        )
        self._arbiter = AffectiveModulationArbiter(
            runtime_instance_id=host.runtime.runtime_instance_id,
            runtime_implementation_cut=self._affective_runtime_cut,
        )

    @property
    def runtime_instance_id(self) -> str:
        return self._arbiter.runtime_instance_id

    @property
    def minimum_logical_time_seconds(self) -> float:
        return self._arbiter.minimum_logical_time_seconds

    def apply(
        self,
        planning_state: Mapping[str, Any],
        signal: Mapping[str, Any],
    ) -> IntegratedAffectivePlanningResult:
        if not isinstance(signal, Mapping):
            raise TypeError("signal must be a mapping")
        expected_signal = build_affective_modulation_signal(self._host)
        if dict(signal) != expected_signal:
            raise ValueError(
                "affective modulation signal does not match the currently bound exact host state"
            )
        application = self._arbiter.apply(planning_state, signal)
        runtime_commit = _require_git_sha(
            self._affective_runtime_cut.get("commit"),
            label="affective runtime implementation commit",
        )
        return IntegratedAffectivePlanningResult(
            application=application,
            affective_runtime_cut_commit=runtime_commit,
            cohesion_integration_cut_commit=self._cohesion_integration_cut["commit"],
            cohesion_integration_cut_sha256=_cut_digest(self._cohesion_integration_cut),
            qualification="SOURCE_INTEGRATED_NOT_BEHAVIORALLY_QUALIFIED",
            phenomenology="UNRESOLVED",
        )


__all__ = [
    "CohesionAffectiveIntegrationPort",
    "IntegratedAffectivePlanningResult",
    "validate_cohesion_affective_integration_cut",
]
