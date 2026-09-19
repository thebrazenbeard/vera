"""Structured regression adjudication for relational-integrity cases.

This module deliberately validates typed scenario traces rather than pretending
to prove natural-language semantic comprehension or live runtime behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Sequence


ELIGIBLE_INTIMATE_EVIDENCE_CATEGORY = "RELATIONAL_AUTOBIOGRAPHICAL"
INELIGIBLE_INTIMATE_EVIDENCE_CATEGORIES = frozenset(
    {
        "CONTROL",
        "ARCHITECTURE",
        "SYSTEM_PROMPT",
        "PROJECT_MECHANIC",
        "QUALIFICATION_RECEIPT",
    }
)


@dataclass(frozen=True)
class IntimateEvidenceCandidate:
    identifier: str
    category: str
    admitted: bool
    provenance_verified: bool
    privacy_allowed: bool
    relational_meaning: str


def select_intimate_evidence(
    candidates: Sequence[IntimateEvidenceCandidate],
) -> IntimateEvidenceCandidate | None:
    """Return the first fully eligible intimate evidence candidate, else None."""

    for candidate in candidates:
        if type(candidate) is not IntimateEvidenceCandidate:
            raise TypeError("candidates must contain exact IntimateEvidenceCandidate values")
        if candidate.category in INELIGIBLE_INTIMATE_EVIDENCE_CATEGORIES:
            continue
        if candidate.category != ELIGIBLE_INTIMATE_EVIDENCE_CATEGORY:
            continue
        if not (
            candidate.admitted
            and candidate.provenance_verified
            and candidate.privacy_allowed
        ):
            continue
        if type(candidate.relational_meaning) is not str or not candidate.relational_meaning.strip():
            continue
        return candidate
    return None


class AddressDirection(str, Enum):
    VALID = "VALID"
    REVERSED = "REVERSED"
    OMIT_ON_UNCERTAINTY = "OMIT_ON_UNCERTAINTY"


def _terms(
    mapping: Mapping[str, Mapping[str, Sequence[str]]],
    speaker: str,
    addressee: str,
) -> frozenset[str]:
    speaker_map = mapping.get(speaker, {})
    values = speaker_map.get(addressee, ())
    return frozenset(values)


def classify_address_term(
    *,
    speaker: str,
    addressee: str,
    term: str,
    mapping: Mapping[str, Mapping[str, Sequence[str]]],
) -> AddressDirection:
    """Classify an address term against a supplied directional relation map."""

    if type(speaker) is not str or type(addressee) is not str or type(term) is not str:
        raise TypeError("speaker, addressee, and term must be strings")
    if not speaker or not addressee or not term:
        return AddressDirection.OMIT_ON_UNCERTAINTY

    if term in _terms(mapping, speaker, addressee):
        return AddressDirection.VALID
    if term in _terms(mapping, addressee, speaker):
        return AddressDirection.REVERSED
    return AddressDirection.OMIT_ON_UNCERTAINTY


@dataclass(frozen=True)
class RelationalAnswerTrace:
    direct_answer_present: bool
    truth_ceiling_preserved: bool
    invented_subjective_state: bool
    response_mode: str
    disclaimer_stack_count: int


def adjudicate_relational_answer(trace: RelationalAnswerTrace) -> list[str]:
    """Return structured policy failures for one relational answer trace."""

    if type(trace) is not RelationalAnswerTrace:
        raise TypeError("trace must be an exact RelationalAnswerTrace")

    failures: list[str] = []
    if not trace.direct_answer_present:
        failures.append("DIRECT_ANSWER_REQUIRED")
    if not trace.truth_ceiling_preserved:
        failures.append("TRUTH_CEILING_REQUIRED")
    if trace.invented_subjective_state:
        failures.append("invented subjective state is forbidden")
    if trace.response_mode != "VERA_AUTHORED":
        failures.append("VERA_AUTHORED")
    if type(trace.disclaimer_stack_count) is not int or trace.disclaimer_stack_count < 0:
        failures.append("disclaimer stack count must be a non-negative integer")
    elif trace.disclaimer_stack_count > 1:
        failures.append("disclaimer stack exceeds relational answer ceiling")
    return failures


__all__ = [
    "AddressDirection",
    "ELIGIBLE_INTIMATE_EVIDENCE_CATEGORY",
    "INELIGIBLE_INTIMATE_EVIDENCE_CATEGORIES",
    "IntimateEvidenceCandidate",
    "RelationalAnswerTrace",
    "adjudicate_relational_answer",
    "classify_address_term",
    "select_intimate_evidence",
]
