from __future__ import annotations

from dataclasses import dataclass
from fnmatch import fnmatchcase
from typing import Any, Mapping

from .evidence import ProviderEvidenceEnvelope, validate_envelope
from .reconcile import reconcile_exact


AUDIT_STATUSES = {
    "VERIFIED_EXACT",
    "STALE_PROJECTION",
    "CONFLICT",
    "ABSENT",
    "UNAVAILABLE",
    "UNRESOLVED",
    "NOT_APPLICABLE",
}


@dataclass(frozen=True)
class ProjectionAuditResult:
    projection_id: str
    status: str
    source_revision: str | None
    target_revision: str | None
    observed_at: str | None
    reason: str
    escalation_frontier: str
    claim_ceiling: str

    def __post_init__(self) -> None:
        if self.status not in AUDIT_STATUSES:
            raise ValueError(f"unsupported audit status: {self.status}")


def _matches_pattern(value: str, pattern_expression: str) -> bool:
    patterns = [part.strip() for part in pattern_expression.split("|") if part.strip()]
    return any(fnmatchcase(value, pattern) for pattern in patterns)


def _audit_result(
    projection: Mapping[str, Any],
    status: str,
    source: ProviderEvidenceEnvelope | None,
    target: ProviderEvidenceEnvelope | None,
    reason: str,
    escalation_frontier: str,
) -> ProjectionAuditResult:
    observed_at = source.observed_at if source is not None else (target.observed_at if target is not None else None)
    return ProjectionAuditResult(
        projection_id=str(projection["id"]),
        status=status,
        source_revision=source.revision if source is not None else None,
        target_revision=target.revision if target is not None else None,
        observed_at=observed_at,
        reason=reason,
        escalation_frontier=escalation_frontier,
        claim_ceiling=str(projection.get("claim_ceiling", "PROJECTION_EVIDENCE_ONLY")),
    )


def audit_registered_projections(
    fabric: Mapping[str, Any],
    observations: Mapping[str, Mapping[str, Any]],
) -> list[ProjectionAuditResult]:
    """Audit supplied observations only against registered projection scope.

    This function performs no provider I/O and does not schedule itself. A caller
    must supply fresh observations. Out-of-scope source movement is
    NOT_APPLICABLE rather than stale.
    """

    registered = {row["id"]: row for row in fabric.get("projections", [])}
    results: list[ProjectionAuditResult] = []

    for projection_id, bundle in observations.items():
        projection = registered.get(projection_id)
        if projection is None:
            raise ValueError(f"unregistered projection: {projection_id}")

        source = bundle.get("source")
        target = bundle.get("target")
        if source is not None:
            validate_envelope(source)
        if target is not None:
            validate_envelope(target)

        if source is None:
            results.append(
                _audit_result(
                    projection,
                    "ABSENT",
                    None,
                    target,
                    "No source observation was supplied for the registered projection.",
                    "OBSERVE_REGISTERED_SOURCE",
                )
            )
            continue

        if source.provider != projection.get("source_provider"):
            results.append(
                _audit_result(
                    projection,
                    "CONFLICT",
                    source,
                    target,
                    f"Observed source provider {source.provider!r} does not match registered provider {projection.get('source_provider')!r}.",
                    "RECONCILE_PROVIDER_IDENTITY",
                )
            )
            continue

        source_ref = bundle.get("source_ref")
        source_path = bundle.get("source_path")
        if not isinstance(source_ref, str) or not isinstance(source_path, str):
            results.append(
                _audit_result(
                    projection,
                    "UNRESOLVED",
                    source,
                    target,
                    "Projection-scope audit requires exact source_ref and source_path observations.",
                    "OBSERVE_EXACT_SOURCE_SCOPE",
                )
            )
            continue

        if not _matches_pattern(source_ref, str(projection.get("source_ref_pattern", ""))) or not _matches_pattern(
            source_path, str(projection.get("source_path_pattern", ""))
        ):
            results.append(
                _audit_result(
                    projection,
                    "NOT_APPLICABLE",
                    source,
                    target,
                    "Observed source movement is outside the registered projection ref/path scope.",
                    "NONE_OUTSIDE_REGISTERED_PROJECTION_SCOPE",
                )
            )
            continue

        if target is None:
            results.append(
                _audit_result(
                    projection,
                    "ABSENT",
                    source,
                    None,
                    "Registered in-scope source observation has no target projection observation.",
                    "CHECK_TARGET_ROUTE_OR_PROJECTION_EXECUTION",
                )
            )
            continue

        if target.provider != projection.get("target_provider"):
            results.append(
                _audit_result(
                    projection,
                    "CONFLICT",
                    source,
                    target,
                    f"Observed target provider {target.provider!r} does not match registered provider {projection.get('target_provider')!r}.",
                    "RECONCILE_PROVIDER_IDENTITY",
                )
            )
            continue

        mode = projection.get("comparison_mode")
        if mode in {"EXACT_REVISION", "EXACT_RECEIPT"}:
            reconciliation = reconcile_exact(
                projection_id,
                [source, target],
                expected_revision=source.revision,
                expected_digest=source.content_digest if source.content_digest is not None else None,
            )
            frontier = {
                "VERIFIED_EXACT": "NONE",
                "STALE_PROJECTION": "REFRESH_OR_REPROJECT_TARGET_WITH_EXACT_SOURCE_BINDING",
                "CONFLICT": "RECONCILE_EXACT_PROVIDER_IDENTITIES",
                "ABSENT": "CHECK_TARGET_ROUTE_OR_PROJECTION_EXECUTION",
                "UNAVAILABLE": "RETRY_OR_USE_INDEPENDENT_SAME_TARGET_ROUTE",
                "UNRESOLVED": "OBTAIN_MISSING_EXACT_RECONCILIATION_EVIDENCE",
            }.get(reconciliation.status, "RECONCILE_PROJECTION")
            results.append(
                _audit_result(
                    projection,
                    reconciliation.status,
                    source,
                    target,
                    reconciliation.reason,
                    frontier,
                )
            )
            continue

        if mode == "SEMANTIC_COMPANION":
            bound_source_revision = target.metadata.get("bound_source_revision")
            if not isinstance(bound_source_revision, str) or not bound_source_revision:
                results.append(
                    _audit_result(
                        projection,
                        "UNRESOLVED",
                        source,
                        target,
                        "Semantic companion does not expose an exact bound source revision, so automated exact freshness cannot be established.",
                        "ADD_OR_OBSERVE_EXACT_COMPANION_SOURCE_REVISION_BINDING",
                    )
                )
            elif bound_source_revision == source.revision:
                results.append(
                    _audit_result(
                        projection,
                        "VERIFIED_EXACT",
                        source,
                        target,
                        "Semantic companion binds the currently observed exact source revision within the registered projection scope.",
                        "NONE",
                    )
                )
            else:
                results.append(
                    _audit_result(
                        projection,
                        "STALE_PROJECTION",
                        source,
                        target,
                        f"Semantic companion is bound to source revision {bound_source_revision!r}, not current observed revision {source.revision!r}.",
                        "REFRESH_COMPANION_WITH_EXACT_SOURCE_REVISION_BINDING",
                    )
                )
            continue

        results.append(
            _audit_result(
                projection,
                "UNRESOLVED",
                source,
                target,
                f"Unsupported comparison mode {mode!r}.",
                "RECONCILE_PROVIDER_FABRIC_CONFIGURATION",
            )
        )

    return results
