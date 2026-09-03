import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from tul_fixture.fixture import ClockReading, InstrumentedHostFixture, SequenceClock
from tul_fixture.types import CapabilityClass, ElapsedStatus, TimeSemantics, TimestampSource


UTC = timezone.utc
T0 = datetime(2026, 7, 29, 12, 0, 0, tzinfo=UTC)


def reading(offset_seconds, *, domain="fixture-clock", resolution=0.001, uncertainty=0.0):
    return ClockReading(
        timestamp=T0 + timedelta(seconds=offset_seconds),
        clock_domain=domain,
        resolution_seconds=resolution,
        uncertainty_seconds=uncertainty,
    )


def fixture(*offsets):
    return InstrumentedHostFixture(clock=SequenceClock(reading(offset) for offset in offsets))


def test_sync_run_captures_ordered_full_lifecycle():
    host = fixture(0, 2, 5)

    execution = host.run("hello", lambda user_text, context: "reply")

    assert execution.model_output == "reply"
    assert execution.evaluation.capability is CapabilityClass.FULL
    assert execution.evaluation.causal_binding is ElapsedStatus.EXACT
    assert execution.evaluation.inbound_to_generation.value_seconds == 2.0
    assert execution.evaluation.inbound_to_assistant.value_seconds == 5.0
    assert execution.generation.in_response_to_message_id == execution.inbound.message_id
    assert execution.assistant.in_response_to_message_id == execution.inbound.message_id


def test_model_receives_only_user_text_and_structured_temporal_context():
    captured = {}

    def model_call(user_text, context):
        captured["user_text"] = user_text
        captured["context"] = context
        return "ok"

    execution = fixture(0, 1, 2).run("semantic input", model_call)

    assert captured["user_text"] == "semantic input"
    assert set(captured["context"]) == {"inbound", "reply_generation"}
    assert captured["context"]["inbound"]["message_id"] == execution.inbound.message_id
    assert "semantic input" not in repr(captured["context"])


def test_fixture_assigns_declared_semantics_and_sources():
    execution = fixture(0, 1, 2).run("hello", lambda *_: "reply")

    assert execution.inbound.endpoint.semantics is TimeSemantics.MESSAGE_CREATION
    assert execution.inbound.endpoint.source is TimestampSource.TRUSTED_BRIDGE
    assert execution.generation.endpoint.semantics is TimeSemantics.GENERATION_INVOCATION_START
    assert execution.generation.endpoint.source is TimestampSource.HOST_RUNTIME_CLOCK
    assert execution.assistant.endpoint.semantics is TimeSemantics.MESSAGE_CREATION
    assert execution.assistant.endpoint.source is TimestampSource.TRUSTED_BRIDGE


def test_async_model_call_is_awaited_before_assistant_capture():
    observed = []

    async def model_call(user_text, context):
        observed.append((user_text, context["inbound"]["message_id"]))
        await asyncio.sleep(0)
        return "async reply"

    execution = asyncio.run(fixture(0, 1, 3).run_async("hello", model_call))

    assert execution.model_output == "async reply"
    assert observed == [("hello", execution.inbound.message_id)]
    assert execution.assistant.endpoint.timestamp == T0 + timedelta(seconds=3)


def test_non_string_model_output_is_rejected_before_assistant_capture():
    host = fixture(0, 1)

    with pytest.raises(TypeError, match="model_call must return str"):
        host.run("hello", lambda *_: {"not": "text"})


def test_sequence_clock_exhaustion_is_explicit():
    host = fixture(0, 1)

    with pytest.raises(RuntimeError, match="SequenceClock exhausted"):
        host.run("hello", lambda *_: "reply")


def test_proof_dict_excludes_model_output_and_semantic_payload():
    execution = fixture(0, 1, 2).run("secret user text", lambda *_: "secret model text")

    proof = execution.to_proof_dict()

    assert set(proof) == {"inbound", "generation", "assistant", "evaluation", "semantic_payload_included"}
    assert proof["semantic_payload_included"] is False
    assert "secret user text" not in repr(proof)
    assert "secret model text" not in repr(proof)


def test_sync_run_rejects_use_inside_running_event_loop():
    host = fixture(0, 1, 2)

    async def invoke_sync_run():
        with pytest.raises(RuntimeError, match="use run_async"):
            host.run("hello", lambda *_: "reply")

    asyncio.run(invoke_sync_run())
