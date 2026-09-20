from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Any, Iterable


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_EXPECTED_DISCOVERY_V0_GIT_BLOB = "b5d85ba31a33ad7192fd4a08934628a72e593312"


@dataclass(frozen=True)
class EffectAttentionContract:
    required_fields: frozenset[str]
    allowed_fields: frozenset[str]
    phases: frozenset[str]
    retry_dispositions: frozenset[str]
    target_required: frozenset[str]
    target_allowed: frozenset[str]
    receipt_required: frozenset[str]
    receipt_allowed: frozenset[str]

    @classmethod
    def from_schema(cls, schema: dict[str, Any]) -> "EffectAttentionContract":
        if schema.get("title") != "Discovery Effect Attempt Envelope V0":
            raise ValueError("unexpected effect-envelope schema title")
        props = schema["properties"]
        target = props["target"]
        receipt = props["receipts"]["items"]
        return cls(
            required_fields=frozenset(schema["required"]),
            allowed_fields=frozenset(props),
            phases=frozenset(props["normalized_phase"]["enum"]),
            retry_dispositions=frozenset(props["retry_disposition"]["enum"]),
            target_required=frozenset(target["required"]),
            target_allowed=frozenset(target["properties"]),
            receipt_required=frozenset(receipt["required"]),
            receipt_allowed=frozenset(receipt["properties"]),
        )


def _git_blob_sha1(payload: bytes) -> str:
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()


def load_effect_attention_contract(path: str | Path) -> EffectAttentionContract:
    raw = Path(path).read_bytes()
    observed_blob = _git_blob_sha1(raw)
    if observed_blob != _EXPECTED_DISCOVERY_V0_GIT_BLOB:
        raise ValueError(
            "effect-envelope schema is not the exact Discovery V0 Git blob: "
            f"expected {_EXPECTED_DISCOVERY_V0_GIT_BLOB}, observed {observed_blob}"
        )
    value = json.loads(raw.decode("utf-8"))
    if type(value) is not dict:
        raise ValueError("effect-envelope schema must be a JSON object")
    return EffectAttentionContract.from_schema(value)


def _exact_keys(
    value: dict[str, Any],
    *,
    required: frozenset[str],
    allowed: frozenset[str],
    label: str,
) -> None:
    keys = set(value)
    missing = required - keys
    extra = keys - allowed
    if missing:
        raise ValueError(f"{label} missing fields: {sorted(missing)}")
    if extra:
        raise ValueError(f"{label} has unexpected fields: {sorted(extra)}")


def _nonempty(value: Any, label: str) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{label} must be a non-empty exact string")
    return value


def validate_effect_envelope(
    envelope: dict[str, Any],
    *,
    contract: EffectAttentionContract,
) -> None:
    if type(envelope) is not dict:
        raise ValueError("effect envelope must be an object")
    _exact_keys(
        envelope,
        required=contract.required_fields,
        allowed=contract.allowed_fields,
        label="effect envelope",
    )
    if envelope.get("schema_version") != "DISCOVERY_EFFECT_ATTEMPT_V0":
        raise ValueError("unsupported effect-envelope version")

    for field in (
        "source_system",
        "source_operation_id",
        "source_state",
        "source_ref",
        "action_class",
    ):
        _nonempty(envelope.get(field), field)

    payload_digest = envelope.get("source_payload_sha256")
    if payload_digest is not None and (
        type(payload_digest) is not str or _SHA256.fullmatch(payload_digest) is None
    ):
        raise ValueError("source_payload_sha256 must be null or lowercase SHA-256")

    phase = envelope.get("normalized_phase")
    if phase not in contract.phases:
        raise ValueError("normalized_phase outside bound contract")
    retry = envelope.get("retry_disposition")
    if retry not in contract.retry_dispositions:
        raise ValueError("retry_disposition outside bound contract")

    target = envelope.get("target")
    if type(target) is not dict:
        raise ValueError("target must be an object")
    _exact_keys(
        target,
        required=contract.target_required,
        allowed=contract.target_allowed,
        label="target",
    )
    _nonempty(target.get("kind"), "target.kind")
    _nonempty(target.get("locator"), "target.locator")
    expected = target.get("expected_precondition")
    if expected is not None and type(expected) is not str:
        raise ValueError("target.expected_precondition must be string or null")

    receipts = envelope.get("receipts")
    if type(receipts) is not list:
        raise ValueError("receipts must be an array")
    for index, receipt in enumerate(receipts):
        if type(receipt) is not dict:
            raise ValueError(f"receipt {index} must be an object")
        _exact_keys(
            receipt,
            required=contract.receipt_required,
            allowed=contract.receipt_allowed,
            label=f"receipt {index}",
        )
        _nonempty(receipt.get("kind"), f"receipt {index}.kind")
        _nonempty(receipt.get("value"), f"receipt {index}.value")


def _key(envelope: dict[str, Any]) -> str:
    return f"{envelope['source_system']}:{envelope['source_operation_id']}"


def build_effect_attention_view(
    envelopes: Iterable[dict[str, Any]],
    *,
    contract: EffectAttentionContract,
) -> dict[str, Any]:
    """Build a read-only coordination attention view.

    Producers select the latest native envelope. This function does not infer
    source-native ordering and never returns an instruction to execute, retry,
    reconcile, restore, merge, deploy, or mutate any target.
    """
    rows = list(envelopes)
    seen: set[str] = set()
    attention_required: list[str] = []
    unresolved: list[str] = []
    verified_or_reconciled: list[str] = []
    terminal_failures: list[str] = []
    do_not_retry: list[str] = []

    phase_counts = {phase: 0 for phase in sorted(contract.phases)}
    retry_counts = {
        disposition: 0 for disposition in sorted(contract.retry_dispositions)
    }

    for envelope in rows:
        validate_effect_envelope(envelope, contract=contract)
        key = _key(envelope)
        if key in seen:
            raise ValueError(
                "coordination view requires one producer-selected latest envelope "
                f"per native operation: duplicate {key}"
            )
        seen.add(key)

        phase = envelope["normalized_phase"]
        retry = envelope["retry_disposition"]
        phase_counts[phase] += 1
        retry_counts[retry] += 1

        if phase in {"PRE_EFFECT", "POST_EFFECT_UNVERIFIED", "OUTCOME_UNKNOWN"}:
            unresolved.append(key)
        if phase in {"POST_EFFECT_VERIFIED", "RECONCILED"}:
            verified_or_reconciled.append(key)
        if phase == "TERMINAL_FAILURE":
            terminal_failures.append(key)
        if retry == "INSPECT_BEFORE_RETRY" or phase == "OUTCOME_UNKNOWN":
            attention_required.append(key)
        if retry == "DO_NOT_RETRY":
            do_not_retry.append(key)

    return {
        "schema": "VERA_COORDINATION_EFFECT_ATTENTION_V1",
        "total_latest_operations": len(rows),
        "phase_counts": phase_counts,
        "retry_counts": retry_counts,
        "attention_required": sorted(attention_required),
        "unresolved": sorted(unresolved),
        "verified_or_reconciled": sorted(verified_or_reconciled),
        "terminal_failures": sorted(terminal_failures),
        "do_not_retry": sorted(do_not_retry),
        "authority_ceiling": (
            "COORDINATION_OBSERVATION_ONLY_NO_EXECUTION_RETRY_CONTROL_OR_RUNTIME_AUTHORITY"
        ),
    }


__all__ = [
    "EffectAttentionContract",
    "build_effect_attention_view",
    "load_effect_attention_contract",
    "validate_effect_envelope",
]
