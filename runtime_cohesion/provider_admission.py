from __future__ import annotations

from typing import Iterable, Mapping

from .evidence import ProviderEvidenceEnvelope
from .runtime import AdmissionDecision, evaluate_proposition_admission as evaluate_abstract_proposition_admission


def evaluate_provider_proposition_admission(
    domain_id: str,
    proposition_or_effect_class: str,
    referent_scope: str,
    observations: Iterable[ProviderEvidenceEnvelope],
    contract: Mapping[str, object],
) -> AdmissionDecision:
    """Provider-backed admission boundary.

    The abstract runtime evaluator intentionally supports lightweight policy-test
    evidence objects. Provider-backed callers must not use that convenience path:
    every observation here must retain the full ProviderEvidenceEnvelope binding,
    currentness, conflict, and proposition/referent metadata.
    """
    materialized = tuple(observations)
    if not all(isinstance(item, ProviderEvidenceEnvelope) for item in materialized):
        raise TypeError(
            "provider-backed proposition admission requires ProviderEvidenceEnvelope observations"
        )
    return evaluate_abstract_proposition_admission(
        domain_id,
        proposition_or_effect_class,
        referent_scope,
        materialized,
        contract,
    )
