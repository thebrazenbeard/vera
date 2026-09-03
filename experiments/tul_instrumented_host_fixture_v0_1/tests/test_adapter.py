from datetime import datetime, timedelta, timezone

import pytest

from tul_fixture.adapter import EvidenceValidationError, TulAdapter, endpoint_from_mapping
from tul_fixture.types import (
    AssistantMessageEvent,
    CapabilityClass,
    ElapsedStatus,
    GenerationEvent,
    InboundEvent,
    Speaker,
    TemporalEndpoint,
    TimeSemantics,
    TimestampSource,
)


UTC = timezone.utc
T0 = datetime(2026, 7, 29, 12, 0, 0, tzinfo=UTC)


def endpoint(timestamp, semantics, source, *, domain="fixture-clock", uncertainty=0.0):
    return TemporalEndpoint(
        timestamp=timestamp,
        semantics=semantics,
        source=source,
        clock_domain=domain,
        resolution_seconds=0.001,
        uncertainty_seconds=uncertainty,
    )


def lifecycle(*, generation_id="user-1", assistant_id="user-1"):
    inbound = InboundEvent(
        message_id="user-1",
        speaker=Speaker.USER,
        endpoint=endpoint(
            T0,
            TimeSemantics.MESSAGE_CREATION,
            TimestampSource.TRUSTED_BRIDGE,
        ),
    )
    generation = GenerationEvent(
        in_response_to_message_id=generation_id,
        endpoint=endpoint(
            T0 + timedelta(seconds=2),
            TimeSemantics.GENERATION_INVOCATION_START,
            TimestampSource.HOST_RUNTIME_CLOCK,
        ),
    )
    assistant = AssistantMessageEvent(
        message_id="assistant-1",
        speaker=Speaker.ASSISTANT,
        in_response_to_message_id=assistant_id,
        endpoint=endpoint(
            T0 + timedelta(seconds=5),
            TimeSemantics.MESSAGE_CREATION,
            TimestampSource.TRUSTED_BRIDGE,
        ),
    )
    return inbound, generation, assistant


def test_full_capability_requires_all_three_valid_endpoints():
    result = TulAdapter().evaluate(*lifecycle())

    assert result.capability is CapabilityClass.FULL
    assert result.causal_binding is ElapsedStatus.EXACT
    assert result.inbound_to_generation.status is ElapsedStatus.EXACT
    assert result.inbound_to_generation.value_seconds == 2.0
    assert result.inbound_to_assistant.status is ElapsedStatus.EXACT
    assert result.inbound_to_assistant.value_seconds == 5.0


def test_mismatched_causal_binding_is_conflicted_not_guessed():
    result = TulAdapter().evaluate(*lifecycle(generation_id="other-message"))

    assert result.capability is CapabilityClass.PARTIAL
    assert result.causal_binding is ElapsedStatus.CONFLICTED
    assert result.inbound_to_generation.status is ElapsedStatus.CONFLICTED
    assert "generation causal binding" in " ".join(result.reasons)


def test_unavailable_endpoints_remain_unavailable():
    unavailable = TemporalEndpoint(
        timestamp=None,
        semantics=TimeSemantics.UNKNOWN,
        source=TimestampSource.UNAVAILABLE,
        clock_domain=None,
        resolution_seconds=None,
        uncertainty_seconds=None,
    )
    inbound = InboundEvent("user-1", Speaker.USER, unavailable)
    generation = GenerationEvent("user-1", unavailable)
    assistant = AssistantMessageEvent("assistant-1", Speaker.ASSISTANT, "user-1", unavailable)

    result = TulAdapter().evaluate(inbound, generation, assistant)

    assert result.capability is CapabilityClass.UNAVAILABLE
    assert result.inbound_to_generation.status is ElapsedStatus.UNAVAILABLE
    assert result.inbound_to_assistant.status is ElapsedStatus.UNAVAILABLE


def test_turn_metadata_cannot_masquerade_as_message_creation():
    inbound, generation, assistant = lifecycle()
    bad_inbound = InboundEvent(
        message_id=inbound.message_id,
        speaker=inbound.speaker,
        endpoint=endpoint(
            T0,
            TimeSemantics.MESSAGE_CREATION,
            TimestampSource.CODEX_TURN_METADATA,
        ),
    )

    result = TulAdapter().evaluate(bad_inbound, generation, assistant)

    assert result.capability is CapabilityClass.PARTIAL
    assert result.causal_binding is ElapsedStatus.CONFLICTED
    assert any("CODEX_TURN_METADATA" in reason for reason in result.reasons)


def test_strict_validation_rejects_wrong_speaker():
    inbound, generation, assistant = lifecycle()
    bad_inbound = InboundEvent(inbound.message_id, Speaker.ASSISTANT, inbound.endpoint)

    with pytest.raises(EvidenceValidationError, match="inbound speaker"):
        TulAdapter().validate_strict(bad_inbound, generation, assistant)


def test_endpoint_mapping_rejects_semantic_payload_fields():
    mapping = {
        "timestamp": "2026-07-29T12:00:00Z",
        "time_semantics": "MESSAGE_CREATION",
        "timestamp_source": "TRUSTED_BRIDGE",
        "clock_domain": "fixture-clock",
        "resolution_seconds": 0.001,
        "uncertainty_seconds": 0.0,
        "message_text": "forbidden semantic content",
    }

    with pytest.raises(EvidenceValidationError, match="unsupported payload keys"):
        endpoint_from_mapping(mapping)
