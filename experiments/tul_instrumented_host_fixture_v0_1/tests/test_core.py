from datetime import datetime, timedelta, timezone

import pytest

from tul_fixture.core import CalculatorPolicy, calculate_elapsed, validate_semantic_source
from tul_fixture.types import (
    ApproximationEvidence,
    ElapsedStatus,
    TemporalEndpoint,
    TimeSemantics,
    TimestampSource,
)


UTC = timezone.utc
T0 = datetime(2026, 7, 29, 12, 0, 0, tzinfo=UTC)


def endpoint(
    timestamp,
    semantics=TimeSemantics.MESSAGE_CREATION,
    source=TimestampSource.PLATFORM_MESSAGE_METADATA,
    *,
    domain="fixture-clock",
    uncertainty=0.0,
):
    return TemporalEndpoint(
        timestamp=timestamp,
        semantics=semantics,
        source=source,
        clock_domain=domain,
        resolution_seconds=0.001,
        uncertainty_seconds=uncertainty,
    )


def test_exact_elapsed_for_compatible_precise_endpoints():
    result = calculate_elapsed(endpoint(T0), endpoint(T0 + timedelta(seconds=2.5)))

    assert result.status is ElapsedStatus.EXACT
    assert result.value_seconds == pytest.approx(2.5)
    assert result.lower_bound_seconds is None
    assert result.upper_bound_seconds is None


def test_compatible_declared_clock_domains_are_accepted():
    policy = CalculatorPolicy(
        compatible_clock_domains=frozenset({("platform-clock", "host-clock")})
    )
    start = endpoint(T0, domain="platform-clock")
    end = endpoint(
        T0 + timedelta(seconds=1),
        TimeSemantics.GENERATION_INVOCATION_START,
        TimestampSource.HOST_RUNTIME_CLOCK,
        domain="host-clock",
    )

    result = calculate_elapsed(start, end, policy=policy)

    assert result.status is ElapsedStatus.EXACT
    assert result.value_seconds == pytest.approx(1.0)


def test_uncertainty_intervals_produce_nonnegative_bounds():
    start = endpoint(T0, uncertainty=0.2)
    end = endpoint(T0 + timedelta(seconds=1), uncertainty=0.3)

    result = calculate_elapsed(start, end)

    assert result.status is ElapsedStatus.BOUNDED
    assert result.lower_bound_seconds == pytest.approx(0.5)
    assert result.upper_bound_seconds == pytest.approx(1.5)


def test_overlapping_uncertainty_intervals_have_zero_lower_bound():
    start = endpoint(T0, uncertainty=1.0)
    end = endpoint(T0 + timedelta(seconds=0.5), uncertainty=1.0)

    result = calculate_elapsed(start, end)

    assert result.status is ElapsedStatus.BOUNDED
    assert result.lower_bound_seconds == 0.0
    assert result.upper_bound_seconds == pytest.approx(2.5)


def test_demonstrably_negative_order_is_conflicted():
    start = endpoint(T0, uncertainty=0.1)
    end = endpoint(T0 - timedelta(seconds=1), uncertainty=0.1)

    result = calculate_elapsed(start, end)

    assert result.status is ElapsedStatus.CONFLICTED
    assert "earlier than start" in result.reasons[0]


def test_unavailable_endpoint_remains_unavailable():
    missing = endpoint(
        None,
        TimeSemantics.UNKNOWN,
        TimestampSource.UNAVAILABLE,
        domain=None,
        uncertainty=None,
    )

    valid, reasons = validate_semantic_source(missing)
    result = calculate_elapsed(missing, endpoint(T0))

    assert valid is True
    assert reasons == ()
    assert result.status is ElapsedStatus.UNAVAILABLE


def test_turn_telemetry_cannot_masquerade_as_tul_endpoint():
    telemetry = endpoint(
        T0,
        TimeSemantics.TURN_START,
        TimestampSource.CODEX_TURN_METADATA,
    )

    valid, reasons = validate_semantic_source(telemetry)
    result = calculate_elapsed(telemetry, endpoint(T0 + timedelta(seconds=1)))

    assert valid is False
    assert any("not valid TUL comparison endpoints" in reason for reason in reasons)
    assert any("CODEX_TURN_METADATA" in reason for reason in reasons)
    assert result.status is ElapsedStatus.CONFLICTED


def test_message_creation_rejects_host_runtime_clock_source():
    invalid = endpoint(
        T0,
        TimeSemantics.MESSAGE_CREATION,
        TimestampSource.HOST_RUNTIME_CLOCK,
    )

    valid, reasons = validate_semantic_source(invalid)

    assert valid is False
    assert reasons == (
        "MESSAGE_CREATION requires PLATFORM_MESSAGE_METADATA or TRUSTED_BRIDGE",
    )


def test_documented_approximation_is_used_only_when_direct_calculation_is_unavailable():
    start = endpoint(T0, domain="platform-clock", uncertainty=None)
    end = endpoint(T0 + timedelta(seconds=3), domain="host-clock", uncertainty=None)
    approximation = ApproximationEvidence(
        estimated_elapsed_seconds=3.25,
        method="bounded host-observation estimate",
        error_model="plus or minus 0.5 seconds",
    )

    result = calculate_elapsed(start, end, approximation=approximation)

    assert result.status is ElapsedStatus.APPROXIMATE
    assert result.value_seconds == pytest.approx(3.25)
    assert any("bounded host-observation estimate" in reason for reason in result.reasons)


def test_undocumented_approximation_does_not_rescue_missing_evidence():
    start = endpoint(T0, domain="platform-clock", uncertainty=None)
    end = endpoint(T0 + timedelta(seconds=3), domain="host-clock", uncertainty=None)
    approximation = ApproximationEvidence(
        estimated_elapsed_seconds=3.0,
        method=" ",
        error_model="unknown",
    )

    result = calculate_elapsed(start, end, approximation=approximation)

    assert result.status is ElapsedStatus.UNAVAILABLE
    assert any("undocumented or invalid" in reason for reason in result.reasons)


def test_temporal_endpoint_rejects_naive_and_negative_metadata():
    with pytest.raises(ValueError, match="timezone-aware"):
        endpoint(datetime(2026, 7, 29, 12, 0, 0))

    with pytest.raises(ValueError, match="uncertainty_seconds must be non-negative"):
        endpoint(T0, uncertainty=-0.1)
