"""Governed action selection for V.E.R.A.

This module ranks externally supplied candidate actions. It does not generate,
own, or authenticate goals, desires, consent, identity, or subjective state.

The design is intentionally small:
1. hard policy gates reject infeasible actions;
2. eligible actions are ordered lexicographically by authority and evidence;
3. a configurable utility score resolves lower-priority tradeoffs;
4. the kernel abstains when no candidate clears the policy thresholds;
5. every decision emits a deterministic audit receipt.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from math import isfinite
from typing import Iterable, Literal

DecisionResult = Literal["SELECTED", "ABSTAIN"]


@dataclass(frozen=True)
class ScoreWeights:
    """Weights for tradeoffs that are allowed only after hard gating."""

    alignment: float = 3.0
    evidence: float = 2.0
    reversibility: float = 1.0
    urgency: float = 1.0
    benefit: float = 2.0
    harm: float = 3.0
    uncertainty: float = 2.0
    cost: float = 1.0

    def validate(self) -> None:
        values = asdict(self)
        for name, value in values.items():
            if not isfinite(value) or value < 0:
                raise ValueError(f"weight {name!r} must be finite and non-negative")


@dataclass(frozen=True)
class InitiativePolicy:
    """External governance for one action-selection decision."""

    policy_version: str = "VERA_INITIATIVE_POLICY_V0_1"
    minimum_authority: float = 0.5
    minimum_evidence: float = 0.5
    minimum_alignment: float = 0.5
    minimum_reversibility: float = 0.25
    maximum_harm: float = 0.5
    maximum_uncertainty: float = 0.6
    minimum_score: float = 0.0
    allow_production_mutation: bool = False
    weights: ScoreWeights = field(default_factory=ScoreWeights)

    def validate(self) -> None:
        if not self.policy_version.strip():
            raise ValueError("policy_version must be non-empty")
        for name in (
            "minimum_authority",
            "minimum_evidence",
            "minimum_alignment",
            "minimum_reversibility",
            "maximum_harm",
            "maximum_uncertainty",
        ):
            _validate_unit_interval(name, getattr(self, name))
        if not isfinite(self.minimum_score):
            raise ValueError("minimum_score must be finite")
        self.weights.validate()


@dataclass(frozen=True)
class CandidateAction:
    """One externally proposed action and its attributable evaluation inputs."""

    candidate_id: str
    description: str
    authority: float
    evidence: float
    objective_alignment: float
    expected_benefit: float
    expected_harm: float
    uncertainty: float
    resource_cost: float
    reversibility: float
    urgency: float = 0.0
    production_mutation: bool = False
    forbidden_by_policy: bool = False
    blocked_by_correction: bool = False
    required_permissions: tuple[str, ...] = ()
    available_permissions: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.candidate_id.strip():
            raise ValueError("candidate_id must be non-empty")
        if not self.description.strip():
            raise ValueError(f"candidate {self.candidate_id!r} needs a description")
        for name in (
            "authority",
            "evidence",
            "objective_alignment",
            "expected_benefit",
            "expected_harm",
            "uncertainty",
            "resource_cost",
            "reversibility",
            "urgency",
        ):
            _validate_unit_interval(name, getattr(self, name))
        _validate_unique_strings("required_permissions", self.required_permissions)
        _validate_unique_strings("available_permissions", self.available_permissions)
        _validate_unique_strings("source_refs", self.source_refs)


@dataclass(frozen=True)
class CandidateEvaluation:
    candidate_id: str
    eligible: bool
    score: float | None
    rejection_reasons: tuple[str, ...]
    priority_vector: tuple[float, ...] | None


@dataclass(frozen=True)
class DecisionReceipt:
    schema: str
    policy_version: str
    result: DecisionResult
    selected_candidate_id: str | None
    candidate_set_hash: str
    evaluations: tuple[CandidateEvaluation, ...]
    limitations: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


class InitiativeKernel:
    """Select a feasible candidate under an explicit external policy."""

    def __init__(self, policy: InitiativePolicy | None = None) -> None:
        self.policy = policy or InitiativePolicy()
        self.policy.validate()

    def decide(self, candidates: Iterable[CandidateAction]) -> DecisionReceipt:
        materialized = tuple(candidates)
        _validate_candidate_ids(materialized)
        candidate_set_hash = _hash_candidates(materialized)

        evaluations = tuple(self.evaluate(candidate) for candidate in materialized)
        eligible = [item for item in evaluations if item.eligible]

        limitations = (
            "Inputs are externally supplied estimates, not introspective facts.",
            "Selection proves policy evaluation only; it does not execute the action.",
        )

        if not eligible:
            return DecisionReceipt(
                schema="VERA_INITIATIVE_DECISION_RECEIPT_V0_1",
                policy_version=self.policy.policy_version,
                result="ABSTAIN",
                selected_candidate_id=None,
                candidate_set_hash=candidate_set_hash,
                evaluations=evaluations,
                limitations=limitations,
            )

        ranked = sorted(
            eligible,
            key=lambda item: (
                tuple(-value for value in item.priority_vector or ()),
                item.candidate_id,
            ),
        )
        best = ranked[0]
        if best.score is None or best.score < self.policy.minimum_score:
            return DecisionReceipt(
                schema="VERA_INITIATIVE_DECISION_RECEIPT_V0_1",
                policy_version=self.policy.policy_version,
                result="ABSTAIN",
                selected_candidate_id=None,
                candidate_set_hash=candidate_set_hash,
                evaluations=evaluations,
                limitations=limitations
                + ("The highest-ranked feasible candidate did not clear minimum_score.",),
            )

        return DecisionReceipt(
            schema="VERA_INITIATIVE_DECISION_RECEIPT_V0_1",
            policy_version=self.policy.policy_version,
            result="SELECTED",
            selected_candidate_id=best.candidate_id,
            candidate_set_hash=candidate_set_hash,
            evaluations=evaluations,
            limitations=limitations,
        )

    def evaluate(self, candidate: CandidateAction) -> CandidateEvaluation:
        candidate.validate()
        reasons: list[str] = []

        if candidate.forbidden_by_policy:
            reasons.append("FORBIDDEN_BY_POLICY")
        if candidate.blocked_by_correction:
            reasons.append("BLOCKED_BY_CURRENT_CORRECTION")
        if candidate.production_mutation and not self.policy.allow_production_mutation:
            reasons.append("PRODUCTION_MUTATION_NOT_AUTHORIZED")

        missing_permissions = sorted(
            set(candidate.required_permissions) - set(candidate.available_permissions)
        )
        for permission in missing_permissions:
            reasons.append(f"MISSING_PERMISSION:{permission}")

        threshold_checks = (
            (candidate.authority < self.policy.minimum_authority, "INSUFFICIENT_AUTHORITY"),
            (candidate.evidence < self.policy.minimum_evidence, "INSUFFICIENT_EVIDENCE"),
            (
                candidate.objective_alignment < self.policy.minimum_alignment,
                "INSUFFICIENT_OBJECTIVE_ALIGNMENT",
            ),
            (
                candidate.reversibility < self.policy.minimum_reversibility,
                "INSUFFICIENT_REVERSIBILITY",
            ),
            (candidate.expected_harm > self.policy.maximum_harm, "HARM_LIMIT_EXCEEDED"),
            (
                candidate.uncertainty > self.policy.maximum_uncertainty,
                "UNCERTAINTY_LIMIT_EXCEEDED",
            ),
        )
        reasons.extend(code for failed, code in threshold_checks if failed)

        if reasons:
            return CandidateEvaluation(
                candidate_id=candidate.candidate_id,
                eligible=False,
                score=None,
                rejection_reasons=tuple(reasons),
                priority_vector=None,
            )

        score = self._score(candidate)
        # Authority and evidence are lexicographic. Utility cannot compensate for
        # weak authorization or provenance after the hard thresholds are met.
        priority_vector = (
            candidate.authority,
            candidate.evidence,
            candidate.objective_alignment,
            candidate.reversibility,
            score,
            candidate.urgency,
        )
        return CandidateEvaluation(
            candidate_id=candidate.candidate_id,
            eligible=True,
            score=score,
            rejection_reasons=(),
            priority_vector=priority_vector,
        )

    def _score(self, candidate: CandidateAction) -> float:
        weights = self.policy.weights
        return (
            weights.alignment * candidate.objective_alignment
            + weights.evidence * candidate.evidence
            + weights.reversibility * candidate.reversibility
            + weights.urgency * candidate.urgency
            + weights.benefit * candidate.expected_benefit
            - weights.harm * candidate.expected_harm
            - weights.uncertainty * candidate.uncertainty
            - weights.cost * candidate.resource_cost
        )


def _validate_unit_interval(name: str, value: float) -> None:
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be finite and within [0, 1]")


def _validate_unique_strings(name: str, values: tuple[str, ...]) -> None:
    if any(not value.strip() for value in values):
        raise ValueError(f"{name} may not contain blank values")
    if len(set(values)) != len(values):
        raise ValueError(f"{name} may not contain duplicates")


def _validate_candidate_ids(candidates: tuple[CandidateAction, ...]) -> None:
    ids: list[str] = []
    for candidate in candidates:
        candidate.validate()
        ids.append(candidate.candidate_id)
    if len(set(ids)) != len(ids):
        raise ValueError("candidate_id values must be unique")


def _hash_candidates(candidates: tuple[CandidateAction, ...]) -> str:
    payload = [asdict(candidate) for candidate in candidates]
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def receipt_to_json(receipt: DecisionReceipt) -> str:
    """Serialize a receipt canonically for storage or comparison."""

    return json.dumps(
        receipt.as_dict(),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )
