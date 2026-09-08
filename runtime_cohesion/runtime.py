from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping


RETRIEVABLE_ROUTE_STATES = {"CURRENTLY_OBSERVED_REACHABLE", "RESULT"}
BUDGET_OK = "WITHIN_BUDGET"
BUDGET_EXHAUSTED = "UNRESOLVED_RETRIEVAL_BUDGET_EXHAUSTED"
ADMISSION_STATUSES = {"ADMITTED", "UNRESOLVED", "CONFLICT"}


@dataclass(frozen=True)
class RetrievalPlan:
    domain_id: str
    candidate_targets: tuple[dict[str, Any], ...]
    targets: tuple[dict[str, Any], ...]
    visited_domains: tuple[str, ...]
    unresolved: tuple[str, ...]
    budget_state: str
    reason: str
    privacy_classes: tuple[str, ...]


@dataclass(frozen=True)
class AdmissionDecision:
    status: str
    dispatch_id: str | None
    resolver_ref: str | None
    required_evidence_classes: tuple[str, ...]
    observed_evidence_classes: tuple[str, ...]
    reason: str

    def __post_init__(self) -> None:
        if self.status not in ADMISSION_STATUSES:
            raise ValueError(f"unsupported admission status: {self.status}")


def _rows_by_id(rows: Iterable[Mapping[str, Any]], kind: str) -> dict[str, Mapping[str, Any]]:
    result: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        row_id = row.get("id")
        if not isinstance(row_id, str) or not row_id:
            raise ValueError(f"{kind} row missing id")
        if row_id in result:
            raise ValueError(f"duplicate {kind} id: {row_id}")
        result[row_id] = row
    return result


def _validate_selector_narrowing(
    target: Mapping[str, Any],
    selectors: Mapping[str, Mapping[str, Any]],
) -> None:
    selector_ref = target.get("selector_ref")
    if selector_ref is None:
        return
    selector = selectors.get(selector_ref)
    if selector is None:
        raise ValueError(f"unknown selector: {selector_ref}")
    if selector.get("source_ref") != target.get("source_ref"):
        raise ValueError(f"selector/source mismatch: {selector_ref}")
    narrowed = selector.get("evidence_capability_refs")
    if narrowed is None:
        return
    parent = set(target.get("evidence_capability_refs", []))
    narrowed_set = set(narrowed)
    if not narrowed_set.issubset(parent):
        raise ValueError(f"selector broadens parent evidence capabilities: {selector_ref}")


def evaluate_proposition_admission(
    domain_id: str,
    proposition_or_effect_class: str,
    referent_scope: str,
    observations: Iterable[Any],
    contract: Mapping[str, Any],
) -> AdmissionDecision:
    """Fail closed unless B dispatch admits decisive evidence for the proposition.

    Transport, readability, and even exact cross-provider reconciliation are not
    proposition authority. Dispatch is selected before terminal resolver
    acceptance. Exact-domain rows outrank wildcard rows at equal precedence; an
    equal-precedence/equal-specificity overlap that points to different resolvers
    is a conflict rather than an arbitrary winner.

    Current B rows encode actor-sensitive direct-self-report requirements in
    `conflict_disposition`; an explicit future `required_evidence_classes` list on
    a dispatch row takes precedence over that compatibility rule.
    """

    dispatch_rows = contract.get("resolver_dispatch", [])
    candidates: list[Mapping[str, Any]] = []
    for row in dispatch_rows:
        if not isinstance(row, Mapping):
            continue
        if row.get("domain_scope") not in {"*", domain_id}:
            continue
        if row.get("proposition_or_effect_class") != proposition_or_effect_class:
            continue
        if row.get("referent_scope") != referent_scope:
            continue
        candidates.append(row)

    observed = tuple(sorted({
        evidence_class
        for item in observations
        if isinstance((evidence_class := getattr(item, "evidence_class", None)), str) and evidence_class
    }))

    if not candidates:
        return AdmissionDecision(
            status="UNRESOLVED",
            dispatch_id=None,
            resolver_ref=None,
            required_evidence_classes=(),
            observed_evidence_classes=observed,
            reason="No resolver_dispatch row matches the exact domain/proposition/referent tuple.",
        )

    def rank(row: Mapping[str, Any]) -> tuple[int, int]:
        precedence = row.get("precedence")
        if not isinstance(precedence, int):
            precedence = -1
        specificity = 1 if row.get("domain_scope") == domain_id else 0
        return precedence, specificity

    best_rank = max(rank(row) for row in candidates)
    best = [row for row in candidates if rank(row) == best_rank]
    best_resolvers = {row.get("resolver_ref") for row in best}
    if len(best_resolvers) != 1:
        return AdmissionDecision(
            status="CONFLICT",
            dispatch_id=None,
            resolver_ref=None,
            required_evidence_classes=(),
            observed_evidence_classes=observed,
            reason="Equal-precedence/equal-specificity dispatch rows select different terminal resolvers.",
        )

    selected = sorted(best, key=lambda row: str(row.get("id", "")))[0]
    dispatch_id = selected.get("id")
    resolver_ref = selected.get("resolver_ref")
    resolvers = contract.get("authority_resolvers", {})
    resolver = resolvers.get(resolver_ref) if isinstance(resolvers, Mapping) else None
    if not isinstance(dispatch_id, str) or not dispatch_id or not isinstance(resolver_ref, str) or not isinstance(resolver, Mapping):
        return AdmissionDecision(
            status="UNRESOLVED",
            dispatch_id=dispatch_id if isinstance(dispatch_id, str) else None,
            resolver_ref=resolver_ref if isinstance(resolver_ref, str) else None,
            required_evidence_classes=(),
            observed_evidence_classes=observed,
            reason="Selected dispatch does not resolve to a valid terminal authority resolver.",
        )

    accepted = {
        value for value in resolver.get("accepted_evidence_classes", [])
        if isinstance(value, str) and value
    }
    explicit_required = selected.get("required_evidence_classes")
    if isinstance(explicit_required, list) and explicit_required:
        required = {value for value in explicit_required if isinstance(value, str) and value}
    elif "DIRECT_SELF_REPORT_REQUIRED" in str(selected.get("conflict_disposition", "")).upper():
        required = {"vera_current_self_report"}
    else:
        required = set(accepted)

    if not required:
        return AdmissionDecision(
            status="UNRESOLVED",
            dispatch_id=dispatch_id,
            resolver_ref=resolver_ref,
            required_evidence_classes=(),
            observed_evidence_classes=observed,
            reason="Selected dispatch/resolver exposes no decisive evidence class.",
        )
    if not required.issubset(accepted):
        return AdmissionDecision(
            status="CONFLICT",
            dispatch_id=dispatch_id,
            resolver_ref=resolver_ref,
            required_evidence_classes=tuple(sorted(required)),
            observed_evidence_classes=observed,
            reason="Dispatch decisive-evidence requirement exceeds its terminal resolver acceptance set.",
        )

    observed_set = set(observed)
    if observed_set.intersection(required):
        return AdmissionDecision(
            status="ADMITTED",
            dispatch_id=dispatch_id,
            resolver_ref=resolver_ref,
            required_evidence_classes=tuple(sorted(required)),
            observed_evidence_classes=observed,
            reason="Observed evidence includes a decisive class required by the selected non-bypassable dispatch.",
        )

    return AdmissionDecision(
        status="UNRESOLVED",
        dispatch_id=dispatch_id,
        resolver_ref=resolver_ref,
        required_evidence_classes=tuple(sorted(required)),
        observed_evidence_classes=observed,
        reason="Readable/reconciled evidence is insufficient to decide this proposition under the selected dispatch.",
    )


def build_retrieval_plan(
    domain_id: str,
    index: Mapping[str, Any],
    contract: Mapping[str, Any],
    observed_route_states: Mapping[str, str],
    privacy_allowlist: set[str] | frozenset[str],
) -> RetrievalPlan:
    """Build the smallest bounded retrieval plan from supplied route observations.

    The function performs no provider I/O. `candidate_targets` are the targets
    that survive domain/dependency/privacy/budget/selector checks and are safe to
    probe. `targets` are the subset whose exact routes have fresh supplied state
    CURRENTLY_OBSERVED_REACHABLE or RESULT.
    """

    domains = _rows_by_id(index.get("domains", []), "domain")
    selectors = _rows_by_id(index.get("selector_declarations", []), "selector")
    if domain_id not in domains:
        raise ValueError(f"unknown domain: {domain_id}")

    policy = contract.get("active_context_policy", {})
    budget = policy.get("uncertainty_probe_budget", {})
    max_depth = int(budget.get("max_dependency_depth", 0))
    max_domains = int(budget.get("max_total_new_domains", 0))
    if max_depth < 0 or max_domains < 1:
        raise ValueError("invalid active-context retrieval budget")

    visited: list[str] = []
    visited_set: set[str] = set()
    candidate_targets: list[dict[str, Any]] = []
    candidate_keys: set[tuple[Any, ...]] = set()
    targets: list[dict[str, Any]] = []
    target_keys: set[tuple[Any, ...]] = set()
    unresolved: list[str] = []
    privacy_seen: set[str] = set()
    budget_state = BUDGET_OK

    queue: list[tuple[str, int]] = [(domain_id, 0)]
    while queue:
        current_id, depth = queue.pop(0)
        if current_id in visited_set:
            continue
        if depth > max_depth or len(visited_set) >= max_domains:
            budget_state = BUDGET_EXHAUSTED
            unresolved.append(f"BUDGET_EXHAUSTED:{current_id}")
            continue

        current = domains.get(current_id)
        if current is None:
            unresolved.append(f"UNKNOWN_DEPENDENCY:{current_id}")
            continue

        visited_set.add(current_id)
        visited.append(current_id)
        privacy_class = current.get("privacy_class")
        if not isinstance(privacy_class, str) or not privacy_class:
            unresolved.append(f"MISSING_PRIVACY_CLASS:{current_id}")
            continue
        privacy_seen.add(privacy_class)

        if privacy_class not in privacy_allowlist and "*" not in privacy_allowlist:
            unresolved.append(f"PRIVACY_NOT_ELIGIBLE:{current_id}:{privacy_class}")
            continue

        for target in current.get("retrieval_targets", []):
            _validate_selector_narrowing(target, selectors)
            route_ref = target.get("route_ref")
            if not isinstance(route_ref, str) or not route_ref:
                unresolved.append(f"MISSING_ROUTE_REF:{current_id}")
                continue
            key = (target.get("source_ref"), route_ref, target.get("selector_ref"))
            candidate = {
                "domain_id": current_id,
                "source_ref": target.get("source_ref"),
                "route_ref": route_ref,
                "selector_ref": target.get("selector_ref"),
                "evidence_capability_refs": tuple(target.get("evidence_capability_refs", [])),
                "privacy_class": privacy_class,
            }
            if key not in candidate_keys:
                candidate_keys.add(key)
                candidate_targets.append(candidate)

            route_state = observed_route_states.get(route_ref)
            if route_state not in RETRIEVABLE_ROUTE_STATES:
                unresolved.append(
                    f"ROUTE_NOT_CURRENTLY_OBSERVED_REACHABLE:{current_id}:{route_ref}:{route_state or 'UNOBSERVED'}"
                )
                continue
            if key in target_keys:
                continue
            target_keys.add(key)
            targets.append({**candidate, "observed_route_state": route_state})

        for dependency in current.get("dependencies", []):
            if dependency in visited_set:
                continue
            if depth + 1 > max_depth or len(visited_set) + len(queue) >= max_domains:
                budget_state = BUDGET_EXHAUSTED
                unresolved.append(f"BUDGET_EXHAUSTED:{dependency}")
                continue
            queue.append((dependency, depth + 1))

    if budget_state == BUDGET_EXHAUSTED:
        reason = "Retrieval expansion exhausted the configured ACTIVE_CONTEXT_SET budget and remains unresolved."
    elif unresolved:
        reason = "Retrieval plan is bounded with explicit unresolved route/privacy/dependency state."
    else:
        reason = "Retrieval plan is within budget and every selected target has fresh supplied reachability/result evidence."

    return RetrievalPlan(
        domain_id=domain_id,
        candidate_targets=tuple(candidate_targets),
        targets=tuple(targets),
        visited_domains=tuple(visited),
        unresolved=tuple(unresolved),
        budget_state=budget_state,
        reason=reason,
        privacy_classes=tuple(sorted(privacy_seen)),
    )


def build_operational_checkpoint(
    plan: RetrievalPlan,
    reconciliation_results: Iterable[Any],
) -> dict[str, Any]:
    """Create a pointer-first resumable operational checkpoint.

    Reconciliation payloads are deliberately not copied. Only compact subject,
    status, and reason pointers are retained.
    """

    target_refs = [
        {
            "domain_id": target["domain_id"],
            "source_ref": target["source_ref"],
            "route_ref": target["route_ref"],
            "selector_ref": target["selector_ref"],
            "observed_route_state": target["observed_route_state"],
        }
        for target in plan.targets
    ]
    reconciliation_refs = [
        {
            "subject_key": getattr(result, "subject_key", None),
            "status": getattr(result, "status", None),
            "reason": getattr(result, "reason", None),
        }
        for result in reconciliation_results
    ]
    return {
        "referent": plan.domain_id,
        "scope": "DURABLE_OPERATIONAL_STATE",
        "provenance": "VERA_RUNTIME_COHESION_V1",
        "purpose": "RUNTIME_COHESION_RESUMABLE_OPERATION",
        "sensitivity_or_privacy_class": list(plan.privacy_classes),
        "minimum_necessary_payload_or_pointer": {
            "domain_id": plan.domain_id,
            "target_refs": target_refs,
            "reconciliation_refs": reconciliation_refs,
            "unresolved": list(plan.unresolved),
            "budget_state": plan.budget_state,
        },
        "destination_eligibility": "REQUIRES_ELIGIBLE_DURABLE_PROVIDER",
        "retention_or_expiry": "UNTIL_TASK_RESOLVED_EXPIRED_OR_SUPERSEDED",
        "supersession_semantics": "EXPLICIT_SUCCESSOR_OR_EXPIRY_REQUIRED; NEWEST_TIMESTAMP_DOES_NOT_SUPERSEDE",
        "non_promotion_flag": True,
    }
