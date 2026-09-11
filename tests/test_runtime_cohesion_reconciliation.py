import unittest

from runtime_cohesion.evidence import ProviderEvidenceEnvelope
from runtime_cohesion.reconcile import reconcile_exact


def obs(
    provider,
    revision,
    observed_at,
    *,
    role=None,
    digest=None,
    evidence_class="persisted_provider_record",
    conflict_state="NONE",
):
    metadata = {}
    if role is not None:
        metadata["projection_role"] = role
    return ProviderEvidenceEnvelope(
        provider=provider,
        locator=f"{provider}:fixture",
        revision=revision,
        observed_at=observed_at,
        evidence_class=evidence_class,
        referent="fixture-subject",
        scope="PROVIDER_OBJECT",
        privacy_class="GOVERNED",
        currentness_basis="exact_readback",
        supersession_state="CURRENT_OBSERVATION",
        conflict_state=conflict_state,
        content_digest=digest,
        receipt_ref=None,
        metadata=metadata,
    )


class RuntimeCohesionReconciliationTests(unittest.TestCase):
    def test_exact_github_supabase_revision_match_is_verified_exact(self):
        revision = "e68803e2631cf0722fec9a4e7fc39f3ad6b43de4"
        result = reconcile_exact(
            "semanticatlas-snapshot",
            [
                obs("github", revision, "2026-09-08T22:00:00Z", role="SOURCE", evidence_class="source_provenance"),
                obs("supabase", revision, "2026-08-23T14:04:10Z", role="TARGET"),
            ],
            expected_revision=revision,
        )
        self.assertEqual(result.status, "VERIFIED_EXACT")
        self.assertIn("provider object", result.authoritative_claim_ceiling.lower())

    def test_older_target_revision_after_source_moved_is_stale_projection(self):
        result = reconcile_exact(
            "bus-radar-projection",
            [
                obs("github", "new-head", "2026-09-08T22:00:00Z", role="SOURCE", evidence_class="coordination_record"),
                obs("supabase", "old-head", "2026-09-09T00:00:00Z", role="TARGET", evidence_class="coordination_record"),
            ],
            expected_revision="new-head",
        )
        self.assertEqual(result.status, "STALE_PROJECTION")
        self.assertIn("old-head", result.reason)

    def test_newer_timestamp_never_overrides_wrong_revision(self):
        result = reconcile_exact(
            "newest-is-not-authority",
            [
                obs("github", "expected", "2026-09-08T20:00:00Z", role="SOURCE", evidence_class="source_provenance"),
                obs("supabase", "wrong", "2026-09-09T23:59:59Z", role="TARGET"),
            ],
            expected_revision="expected",
        )
        self.assertNotEqual(result.status, "VERIFIED_EXACT")
        self.assertEqual(result.status, "STALE_PROJECTION")

    def test_digest_mismatch_is_conflict_even_when_revision_matches(self):
        result = reconcile_exact(
            "digest-conflict",
            [
                obs("google_drive", "same", "2026-09-08T22:00:00Z", digest="sha256:a"),
                obs("supabase", "same", "2026-09-08T22:00:01Z", digest="sha256:b"),
            ],
            expected_revision="same",
        )
        self.assertEqual(result.status, "CONFLICT")

    def test_explicit_provider_conflict_fails_closed(self):
        result = reconcile_exact(
            "explicit-conflict",
            [obs("supabase", "same", "2026-09-08T22:00:00Z", conflict_state="CONFLICT")],
            expected_revision="same",
        )
        self.assertEqual(result.status, "CONFLICT")

    def test_no_observations_is_absent(self):
        result = reconcile_exact("missing", [], expected_revision="x")
        self.assertEqual(result.status, "ABSENT")

    def test_single_observation_without_expected_peer_is_unresolved(self):
        result = reconcile_exact(
            "one-sided",
            [obs("supabase", "x", "2026-09-08T22:00:00Z")],
        )
        self.assertEqual(result.status, "UNRESOLVED")

    def test_incompatible_exact_observations_without_projection_roles_conflict(self):
        result = reconcile_exact(
            "divergent",
            [
                obs("google_drive", "a", "2026-09-08T22:00:00Z"),
                obs("supabase", "b", "2026-09-08T22:00:01Z"),
            ],
        )
        self.assertEqual(result.status, "CONFLICT")

    def test_temporal_observation_cannot_resolve_revision_conflict(self):
        result = reconcile_exact(
            "temporal-does-not-decide",
            [
                obs("github", "a", "2026-09-08T22:00:00Z", evidence_class="source_provenance"),
                obs("supabase", "b", "2026-09-08T22:00:01Z"),
                obs("temporal", "event-123", "2026-09-08T22:00:02Z"),
            ],
        )
        self.assertEqual(result.status, "CONFLICT")


if __name__ == "__main__":
    unittest.main()
