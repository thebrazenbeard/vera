from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping


RETRIEVABLE_ROUTE_STATES = {"CURRENTLY_OBSERVED_REACHABLE", "RESULT"}
BUDGET_OK = "WITHIN_BUDGET"
BUDGET_EXHAUSTED = "UNRESOLVED_RETRIEVAL_BUDGET_EXHAUSTED"


@dataclass(frozen=True)
class RetrievalPlan:
    domain_id: str
    targets: tuple[dict[str, Any], ...]
    visited_domains: tuple[str, ...]
    unresolved: tuple[str, ...]
    budget_state: str
    reason: str
    privacy_classes: tuple[str, ...]


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


def build_retrieval_plan(
    domain_id: str,
    index: Mapping[str, Any],
    contract: Mapping[str, Any],
    observed_route_states: Mapping[str, str],
    privacy_allowlist: set[str] | frozenset[str],
) -> RetrievalPlan:
    """Build the smallest bounded retrieval plan from already-observed route state.

    The function performs no provider I/O. A route enters the executable target
    set only after the caller supplies a fresh observed state of
    CURRENTLY_OBSERVED_REACHABLE or RESULT for that exact route.
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
            route_state = observed_route_states.get(route_ref)
            if route_state not in RETRIEVABLE_ROUTE_STATES:
                unresolved.append(
                    f"ROUTE_NOT_CURRENTLY_OBSERVED_REACHABLE:{current_id}:{route_ref}:{route_state or 'UNOBSERVED'}"
                )
                continue
            key = (target.get("source_ref"), route_ref, target.get("selector_ref"))
            if key in target_keys:
                continue
            target_keys.add(key)
            targets.append(
                {
                    "domain_id": current_id,
                    "source_ref": target.get("source_ref"),
                    "route_ref": route_ref,
                    "selector_ref": target.get("selector_ref"),
                    "evidence_capability_refs": tuple(target.get("evidence_capability_refs", [])),
                    "observed_route_state": route_state,
                    "privacy_class": privacy_class,
                }
            )

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
