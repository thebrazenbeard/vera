from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Mapping


VALID_MODES = {"OFF", "ON"}
VALID_SCOPES = {"VERA_PROJECT_ALL_CHATS", "CHAT_LOCAL"}
VALID_PRESENTATIONS = {"BLOCKQUOTE"}

DEFAULT_ATTACK_DIMENSIONS = (
    "hidden_assumptions",
    "evidence_gaps",
    "semantic_or_authority_leakage",
    "blast_radius_and_single_points_of_failure",
    "rollback_or_recovery_weakness",
    "false_equivalence_or_overgeneralization",
    "simpler_alternative",
)

AUTHORITY_CEILING = "ADVISORY_ONLY_NO_AUTHORITY_PROMOTION"


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
    user_request: str
    primary_answer: str
    attack_dimensions: tuple[str, ...]
    max_objections: int
    presentation: str
    authority_ceiling: str
    reviewer_instruction: str


def build_hostile_review_request(
    config: HostileReviewerConfig,
    *,
    user_request: str,
    primary_answer: str,
    substantive: bool = True,
) -> HostileReviewRequest | None:
    """Build the second-pass review request when the feature is enabled.

    The caller remains responsible for obtaining a model-generated critique.
    This function never executes tools, mutates providers, or promotes claims.
    """

    if config.mode == "OFF" or not substantive:
        return None
    if not user_request.strip():
        raise ValueError("user_request must be non-empty when review is enabled")
    if not primary_answer.strip():
        raise ValueError("primary_answer must be non-empty when review is enabled")

    digest = sha256(primary_answer.encode("utf-8")).hexdigest()
    instruction = (
        "Review the exact primary answer identified by subject_sha256. "
        "Act as an adversarial Countervoice whose job is to find the strongest "
        "material objections, not to agree with the primary answer. Attack hidden "
        "assumptions, evidence gaps, semantic or authority leakage, blast radius, "
        "rollback weakness, false equivalence, overgeneralization, and simpler "
        "alternatives where relevant. Return only concise externally shareable "
        "objections; do not reveal private chain-of-thought. Do not invent facts, "
        "change the user's request, grant authority, alter tool effects, promote "
        "source to runtime truth, or turn critique into a new instruction."
    )
    return HostileReviewRequest(
        subject_sha256=digest,
        user_request=user_request,
        primary_answer=primary_answer,
        attack_dimensions=DEFAULT_ATTACK_DIMENSIONS,
        max_objections=config.max_objections,
        presentation=config.presentation,
        authority_ceiling=AUTHORITY_CEILING,
        reviewer_instruction=instruction,
    )


def render_hostile_review_block(
    critique: str,
    *,
    label: str = "HOSTILE REVIEWER",
) -> str:
    """Render an already-generated critique as the visible review block."""

    body = critique.strip()
    if not body:
        raise ValueError("critique must be non-empty")
    lines = body.splitlines()
    rendered = [f"> **{label}:** {lines[0]}"]
    rendered.extend(f"> {line}" if line else ">" for line in lines[1:])
    return "\n".join(rendered)
