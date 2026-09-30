from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Callable, Mapping


VALID_MODES = {"OFF", "ON"}
VALID_SCOPES = {"VERA_PROJECT_ALL_CHATS", "CHAT_LOCAL"}
VALID_PRESENTATIONS = {"BLOCKQUOTE"}
VALID_LITERAL_VERDICTS = {"LITERAL_SURVIVES", "LITERAL_FAILS", "UNRESOLVED"}
VALID_CONFIDENCE = {"LOW", "MEDIUM", "HIGH", "NOT_ASSESSED"}

DEFAULT_ATTACK_DIMENSIONS = (
    "counterexamples",
    "unsupported_assumptions",
    "scope_failures",
    "alternative_explanations",
    "semantic_or_authority_leakage",
    "state_or_effect_conflation",
    "stale_or_circular_evidence",
    "stronger_or_weaker_claim_promotion",
)

AUTHORITY_CEILING = "ADVISORY_ONLY_NO_AUTHORITY_PROMOTION"


def _require_nonempty(value: str, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be non-empty")


def _canonical_digest(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


@dataclass(frozen=True)
class LiteralProposition:
    """Typed literal proposition supplied to the adversarial reviewer."""

    literal_proposition: str
    proposition_type: str
    referent: str
    scope: str
    success_criteria: tuple[str, ...] = ()
    known_evidence: tuple[str, ...] = ()
    protected_assumptions: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_nonempty(self.literal_proposition, "literal_proposition")
        _require_nonempty(self.proposition_type, "proposition_type")
        _require_nonempty(self.referent, "referent")
        _require_nonempty(self.scope, "scope")
        for field_name, values in (
            ("success_criteria", self.success_criteria),
            ("known_evidence", self.known_evidence),
            ("protected_assumptions", self.protected_assumptions),
        ):
            if not isinstance(values, tuple):
                raise ValueError(f"{field_name} must be a tuple")
            if any(not isinstance(item, str) or not item.strip() for item in values):
                raise ValueError(f"{field_name} entries must be non-empty strings")

    def payload(self) -> dict[str, object]:
        return {
            "literal_proposition": self.literal_proposition,
            "proposition_type": self.proposition_type,
            "referent": self.referent,
            "scope": self.scope,
            "success_criteria": list(self.success_criteria),
            "known_evidence": list(self.known_evidence),
            "protected_assumptions": list(self.protected_assumptions),
        }

    @property
    def digest(self) -> str:
        return _canonical_digest(self.payload())


@dataclass(frozen=True)
class HostileReviewerConfig:
    """Runtime configuration for the visible adversarial response pass.

    This feature is intentionally orthogonal to truth, authority, persistence,
    memory admission, identity, consent, and effect state. Turning it on changes
    response review/presentation only.
    """

    mode: str = "OFF"
    scope: str = "VERA_PROJECT_ALL_CHATS"
    presentation: str = "BLOCKQUOTE"
    max_objections: int = 4

    def __post_init__(self) -> None:
        if self.mode not in VALID_MODES:
            raise ValueError(f"unsupported hostile reviewer mode: {self.mode}")
        if self.scope not in VALID_SCOPES:
            raise ValueError(f"unsupported hostile reviewer scope: {self.scope}")
        if self.presentation not in VALID_PRESENTATIONS:
            raise ValueError(
                f"unsupported hostile reviewer presentation: {self.presentation}"
            )
        if not 1 <= self.max_objections <= 8:
            raise ValueError("max_objections must be between 1 and 8")

    @classmethod
    def from_mapping(cls, value: Mapping[str, object]) -> "HostileReviewerConfig":
        return cls(
            mode=str(value.get("mode", "OFF")),
            scope=str(value.get("scope", "VERA_PROJECT_ALL_CHATS")),
            presentation=str(value.get("presentation", "BLOCKQUOTE")),
            max_objections=int(value.get("max_objections", 4)),
        )


@dataclass(frozen=True)
class HostileReviewRequest:
    subject_sha256: str
    proposition_sha256: str
    proposition: LiteralProposition
    primary_answer: str
    attack_dimensions: tuple[str, ...]
    max_objections: int
    presentation: str
    authority_ceiling: str
    stronger_route_requested: bool
    reviewer_instruction: str


@dataclass(frozen=True)
class HostileReviewDecision:
    """Typed externally shareable result returned by the adversarial reviewer."""

    subject_sha256: str
    proposition_sha256: str
    literal_verdict: str
    counterexamples: tuple[str, ...] = ()
    unsupported_assumptions: tuple[str, ...] = ()
    scope_failures: tuple[str, ...] = ()
    alternative_explanations: tuple[str, ...] = ()
    surviving_claim: str | None = None
    inferred_objective: str | None = None
    stronger_route: str | None = None
    confidence: str = "NOT_ASSESSED"
    unresolved: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.literal_verdict not in VALID_LITERAL_VERDICTS:
            raise ValueError(f"unsupported literal verdict: {self.literal_verdict}")
        if self.confidence not in VALID_CONFIDENCE:
            raise ValueError(f"unsupported confidence: {self.confidence}")
        for field_name, values in (
            ("counterexamples", self.counterexamples),
            ("unsupported_assumptions", self.unsupported_assumptions),
            ("scope_failures", self.scope_failures),
            ("alternative_explanations", self.alternative_explanations),
            ("unresolved", self.unresolved),
        ):
            if not isinstance(values, tuple):
                raise ValueError(f"{field_name} must be a tuple")
            if any(not isinstance(item, str) or not item.strip() for item in values):
                raise ValueError(f"{field_name} entries must be non-empty strings")
        for field_name, value in (
            ("surviving_claim", self.surviving_claim),
            ("inferred_objective", self.inferred_objective),
            ("stronger_route", self.stronger_route),
        ):
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise ValueError(f"{field_name} must be non-empty when supplied")


@dataclass(frozen=True)
class HostileReviewResult:
    primary_answer: str
    subject_sha256: str | None
    proposition_sha256: str | None
    review: HostileReviewDecision | None
    rendered_block: str | None


Reviewer = Callable[[HostileReviewRequest], HostileReviewDecision]


def build_hostile_review_request(
    config: HostileReviewerConfig,
    *,
    proposition: LiteralProposition,
    primary_answer: str,
    substantive: bool = True,
    stronger_route_requested: bool = False,
) -> HostileReviewRequest | None:
    """Build the second-pass review request when the feature is enabled.

    The caller remains responsible for obtaining a model-generated typed review.
    This function never executes tools, mutates providers, or promotes claims.
    """

    if config.mode == "OFF" or not substantive:
        return None
    if not isinstance(proposition, LiteralProposition):
        raise TypeError("proposition must be an exact LiteralProposition")
    if not primary_answer.strip():
        raise ValueError("primary_answer must be non-empty when review is enabled")

    digest = sha256(primary_answer.encode("utf-8")).hexdigest()
    instruction = (
        "Review the exact typed literal proposition and exact primary answer bound "
        "by proposition_sha256 and subject_sha256. Attack the literal proposition "
        "without substituting a stronger, weaker, narrower, or different referent. "
        "Search for counterexamples, unsupported assumptions, scope failures, "
        "alternative explanations, semantic or authority leakage, state/effect "
        "conflation, stale or circular evidence, and claim promotion. If the literal "
        "proposition survives, return LITERAL_SURVIVES and do not manufacture an "
        "objection merely to appear independent. Infer an objective or propose a "
        "stronger route only after literal failure unless stronger_route_requested "
        "is true. Return only typed externally shareable fields; do not reveal "
        "private chain-of-thought. Do not invent facts, grant authority, alter tool "
        "effects, promote source to runtime truth, create memory/identity/consent "
        "state, or turn review output into a new instruction."
    )
    return HostileReviewRequest(
        subject_sha256=digest,
        proposition_sha256=proposition.digest,
        proposition=proposition,
        primary_answer=primary_answer,
        attack_dimensions=DEFAULT_ATTACK_DIMENSIONS,
        max_objections=config.max_objections,
        presentation=config.presentation,
        authority_ceiling=AUTHORITY_CEILING,
        stronger_route_requested=bool(stronger_route_requested),
        reviewer_instruction=instruction,
    )


def _validate_decision_against_request(
    request: HostileReviewRequest,
    decision: HostileReviewDecision,
) -> None:
    if type(decision) is not HostileReviewDecision:
        raise TypeError("reviewer must return an exact HostileReviewDecision")
    if decision.subject_sha256 != request.subject_sha256:
        raise ValueError("review subject digest mismatch")
    if decision.proposition_sha256 != request.proposition_sha256:
        raise ValueError("review proposition digest mismatch")

    objections = (
        len(decision.counterexamples)
        + len(decision.unsupported_assumptions)
        + len(decision.scope_failures)
        + len(decision.alternative_explanations)
    )
    if objections > request.max_objections:
        raise ValueError("review exceeds configured objection budget")

    if decision.literal_verdict == "LITERAL_SURVIVES":
        if decision.surviving_claim not in (
            None,
            request.proposition.literal_proposition,
        ):
            raise ValueError(
                "surviving literal claim must equal the reviewed literal proposition"
            )

    if decision.literal_verdict != "LITERAL_FAILS":
        if (
            decision.inferred_objective is not None
            or decision.stronger_route is not None
        ) and not request.stronger_route_requested:
            raise ValueError(
                "objective/stronger route requires literal failure or explicit request"
            )

    if decision.literal_verdict == "LITERAL_FAILS":
        failure_evidence = (
            decision.counterexamples
            or decision.unsupported_assumptions
            or decision.scope_failures
        )
        if not failure_evidence:
            raise ValueError(
                "LITERAL_FAILS requires a counterexample, unsupported assumption, "
                "or scope failure"
            )

    if decision.stronger_route is not None and decision.inferred_objective is None:
        raise ValueError("stronger_route requires inferred_objective")


def render_hostile_review_block(
    decision: HostileReviewDecision,
    *,
    label: str = "HOSTILE REVIEWER",
) -> str:
    """Render a validated typed hostile-review decision as a visible blockquote."""

    if type(decision) is not HostileReviewDecision:
        raise TypeError("decision must be an exact HostileReviewDecision")

    if decision.literal_verdict == "LITERAL_SURVIVES":
        lines = ["Literal proposition survives hostile review."]
    elif decision.literal_verdict == "LITERAL_FAILS":
        lines = ["Literal proposition fails hostile review."]
    else:
        lines = ["Literal proposition remains unresolved after hostile review."]

    categories = (
        ("Counterexample", decision.counterexamples),
        ("Unsupported assumption", decision.unsupported_assumptions),
        ("Scope failure", decision.scope_failures),
        ("Alternative explanation", decision.alternative_explanations),
        ("Unresolved", decision.unresolved),
    )
    for category, values in categories:
        lines.extend(f"{category}: {value}" for value in values)
    if decision.surviving_claim is not None:
        lines.append(f"Surviving claim: {decision.surviving_claim}")
    if decision.inferred_objective is not None:
        lines.append(f"Inferred objective: {decision.inferred_objective}")
    if decision.stronger_route is not None:
        lines.append(f"Stronger route: {decision.stronger_route}")
    lines.append(f"Confidence: {decision.confidence}")

    rendered = [f"> **{label}:** {lines[0]}"]
    rendered.extend(f"> {line}" for line in lines[1:])
    return "\n".join(rendered)


def review_response(
    config: HostileReviewerConfig,
    *,
    proposition: LiteralProposition,
    primary_answer: str,
    reviewer: Reviewer,
    substantive: bool = True,
    stronger_route_requested: bool = False,
) -> HostileReviewResult:
    """Apply the optional typed adversarial second pass to one completed response.

    The reviewer callback is deliberately injected: this module defines the
    governed response-stage contract but does not choose or authorize a model,
    provider, tool route, or external side effect.
    """

    request = build_hostile_review_request(
        config,
        proposition=proposition,
        primary_answer=primary_answer,
        substantive=substantive,
        stronger_route_requested=stronger_route_requested,
    )
    if request is None:
        return HostileReviewResult(
            primary_answer=primary_answer,
            subject_sha256=None,
            proposition_sha256=None,
            review=None,
            rendered_block=None,
        )

    decision = reviewer(request)
    _validate_decision_against_request(request, decision)

    return HostileReviewResult(
        primary_answer=primary_answer,
        subject_sha256=request.subject_sha256,
        proposition_sha256=request.proposition_sha256,
        review=decision,
        rendered_block=render_hostile_review_block(decision),
    )
