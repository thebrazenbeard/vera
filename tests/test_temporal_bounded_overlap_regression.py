from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest

from protocol import temporal_enforcement as legacy
from protocol.temporal_role_precision import RoleTemporalPoint, elapsed_between


BASE = datetime(2026, 7, 30, 23, 40, tzinfo=timezone.utc)


def evidence(reference_id: str) -> legacy.ExternalEvidence:
    return legacy.ExternalEvidence(
        system=legacy.EvidenceSystem.SUPABASE,
        operation="temporal_read",
        confirmed=True,
        reference_id=reference_id,
        observed_at=BASE,
        subject_hash="0" * 64,
        immutable=True,
    )


def bounded_point(
    *,
    reference_id: str,
    representative: datetime,
    lower: datetime,
    upper: datetime,
) -> RoleTemporalPoint:
    return RoleTemporalPoint(
        source=evidence(reference_id),
        scope_instance_id="scope-overlap",
        event_time=representative,
        event_time_precision=legacy.TemporalPrecision.BOUNDED,
        event_time_lower_bound=lower,
        event_time_upper_bound=upper,
    )


class BoundedOverlapRegressionTests(unittest.TestCase):
    def test_reversed_representatives_with_nonnegative_support_remain_bounded(self):
        start = bounded_point(
            reference_id="start",
            representative=BASE + timedelta(minutes=10),
            lower=BASE,
            upper=BASE + timedelta(minutes=20),
        )
        end = bounded_point(
            reference_id="end",
            representative=BASE + timedelta(minutes=5),
            lower=BASE + timedelta(minutes=5),
            upper=BASE + timedelta(minutes=30),
        )

        result = elapsed_between(start, end)

        self.assertIs(result.status, legacy.ElapsedStatus.BOUNDED)
        self.assertEqual(result.lower_seconds, 0.0)
        self.assertEqual(result.best_seconds, 0.0)
        self.assertEqual(result.upper_seconds, 1800.0)

    def test_fully_reversed_supported_intervals_remain_conflicted(self):
        start = bounded_point(
            reference_id="start-fully-reversed",
            representative=BASE + timedelta(minutes=20),
            lower=BASE + timedelta(minutes=15),
            upper=BASE + timedelta(minutes=25),
        )
        end = bounded_point(
            reference_id="end-fully-reversed",
            representative=BASE + timedelta(minutes=5),
            lower=BASE,
            upper=BASE + timedelta(minutes=10),
        )

        result = elapsed_between(start, end)

        self.assertIs(result.status, legacy.ElapsedStatus.CONFLICTED)
        self.assertIsNone(result.best_seconds)


if __name__ == "__main__":
    unittest.main()
