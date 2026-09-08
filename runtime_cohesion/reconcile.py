from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .evidence import ProviderEvidenceEnvelope, validate_envelope


STATUSES = {
    "VERIFIED_EXACT",
    "STALE_PROJECTION",
    "CONFLICT",
    "ABSENT",
    "UNAVAILABLE",
    "UNRESOLVED",
}


@dataclass(frozen=True)
class ReconciliationResult:
    status: str
    subject_key: str
    observations: tuple[ProviderEvidenceEnvelope, ...]
    reason: str
    authoritative_claim_ceiling: str

    def __post_init__(self) -> None:
        if self.status not in STATUSES:
            raise ValueError(f"unsupported reconciliation status: {self.status}")
        if not self.subject_key:
            raise ValueError("subject_key must be non-empty")


def _claim_ceiling(observations: tuple[ProviderEvidenceEnvelope, ...]) -> str:
    classes = {item.evidence_class for item in observations}
    if "persisted_provider_record" in classes:
        return (
            "Exact provider object/effect evidence only; persistence/readback does not "
            "establish present truth, current Vera self-state, consent, authority, "
            "native admission, runtime consumption, or phenomenology."
        )
    if "coordination_record" in classes:
        return (
            "Coordination/projection record evidence only; delivery or projection does "
            "not establish identity, memory incorporation, native route qualification, "
            "or task acceptance."
        )
    if "source_provenance" in classes or "control_source" in classes:
        return (
            "Exact source/provenance object evidence only; source availability does not "
            "establish installation, runtime consumption, or behavioral qualification."
        )
    return "Typed evidence only at the independently established evidence class and exact referent/scope."


def _result(
    status: str,
    subject_key: str,
    observations: tuple[ProviderEvidenceEnvelope, ...],
    reason: str,
) -> ReconciliationResult:
    return ReconciliationResult(
        status=status,
        subject_key=subject_key,
        observations=observations,
        reason=reason,
        authoritative_claim_ceiling=_claim_ceiling(observations),
    )


def reconcile_exact(
    subject_key: str,
    observations: Iterable[ProviderEvidenceEnvelope],
    *,
    expected_revision: str | None = None,
    expected_digest: str | None = None,
) -> ReconciliationResult:
    """Reconcile exact provider observations without using recency as authority.

    `expected_revision` / `expected_digest` are externally established comparison
    anchors for the exact subject. They do not gain authority from this function.
    A SOURCE observation matching the anchor plus an older/different TARGET revision
    is classified as a stale projection. Other incompatible exact claims conflict.
    """

    if not isinstance(subject_key, str) or not subject_key.strip():
        raise ValueError("subject_key must be non-empty")
    subject_key = subject_key.strip()
    items = tuple(observations)
    if not items:
        return _result("ABSENT", subject_key, items, "No provider observations were supplied.")

    for item in items:
        validate_envelope(item)

    if all(item.metadata.get("availability") == "UNAVAILABLE" for item in items):
        return _result("UNAVAILABLE", subject_key, items, "All supplied provider routes are unavailable.")

    if any(item.conflict_state in {"CONFLICT", "MISMATCH"} for item in items):
        return _result("CONFLICT", subject_key, items, "An observation carries an explicit exact-object conflict/mismatch state.")
    if any(item.conflict_state == "UNKNOWN" for item in items):
        return _result("UNRESOLVED", subject_key, items, "At least one observation has unresolved conflict state.")

    digests = {item.content_digest for item in items if item.content_digest is not None}
    if expected_digest is not None:
        wrong_digests = sorted(d for d in digests if d != expected_digest)
        if wrong_digests:
            return _result(
                "CONFLICT",
                subject_key,
                items,
                f"Exact content digest conflicts with expected digest: {wrong_digests!r}.",
            )
    elif len(digests) > 1:
        return _result(
            "CONFLICT",
            subject_key,
            items,
            f"Provider observations expose incompatible exact content digests: {sorted(digests)!r}.",
        )

    revisions = {item.revision for item in items}
    if expected_revision is not None:
        mismatched = [item for item in items if item.revision != expected_revision]
        if not mismatched:
            return _result(
                "VERIFIED_EXACT",
                subject_key,
                items,
                f"All supplied exact revisions match expected revision {expected_revision!r}.",
            )

        matching = [item for item in items if item.revision == expected_revision]
        mismatched_targets = [
            item for item in mismatched if item.metadata.get("projection_role") == "TARGET"
        ]
        if matching and len(mismatched_targets) == len(mismatched):
            stale = sorted({item.revision for item in mismatched_targets})
            return _result(
                "STALE_PROJECTION",
                subject_key,
                items,
                f"Target projection revision(s) {stale!r} do not match current source revision {expected_revision!r}.",
            )
        return _result(
            "CONFLICT",
            subject_key,
            items,
            f"Exact revisions conflict with expected revision {expected_revision!r}: {sorted(revisions)!r}.",
        )

    if len(items) == 1:
        return _result(
            "UNRESOLVED",
            subject_key,
            items,
            "A one-sided provider observation has no exact peer/anchor for cross-provider reconciliation.",
        )

    if len(revisions) == 1:
        revision = next(iter(revisions))
        return _result(
            "VERIFIED_EXACT",
            subject_key,
            items,
            f"All supplied provider observations agree on exact revision {revision!r}.",
        )

    return _result(
        "CONFLICT",
        subject_key,
        items,
        f"Provider observations expose incompatible exact revisions: {sorted(revisions)!r}; observation timestamps do not resolve the conflict.",
    )
