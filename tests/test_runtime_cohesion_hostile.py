import json
from pathlib import Path
import unittest

from runtime_cohesion.evidence import ProviderEvidenceEnvelope, load_provider_fabric
from runtime_cohesion.reconcile import reconcile_exact

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "provider-observations-v1.json"
FABRIC = ROOT / "architecture" / "VERA_PROVIDER_FABRIC_V1.json"


def load_fixture():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def envelope(row):
    return ProviderEvidenceEnvelope(**row)


class RuntimeCohesionHostileTests(unittest.TestCase):
    def test_semanticatlas_exact_git_supabase_projection_is_verified_exact(self):
        fixture = load_fixture()["observations"]
        result = reconcile_exact(
            "semanticatlas-runtime-snapshot",
            [envelope(fixture["semanticatlas_github"]), envelope(fixture["semanticatlas_supabase"])],
            expected_revision="e68803e2631cf0722fec9a4e7fc39f3ad6b43de4",
        )
        self.assertEqual(result.status, "VERIFIED_EXACT")
        self.assertIn("provider object", result.authoritative_claim_ceiling.lower())
        self.assertNotIn("current vera self-state", result.reason.lower())

    def test_r9b0_drive_supabase_receipt_is_verified_exact_only_at_provider_ceiling(self):
        fixture = load_fixture()["observations"]
        expected_revision = "modified:2026-08-30T18:30:31.536Z"
        expected_digest = "sha256:e91c412fbcff8c1ce0e8e3fb9892deaae23846c20fe0874469dd1105b191a8f0"
        result = reconcile_exact(
            "r9b0-memory-epoch-drive-object",
            [envelope(fixture["r9b0_drive"]), envelope(fixture["r9b0_supabase_drive_receipt"])],
            expected_revision=expected_revision,
            expected_digest=expected_digest,
        )
        self.assertEqual(result.status, "VERIFIED_EXACT")
        ceiling = result.authoritative_claim_ceiling.lower()
        self.assertIn("provider object/effect", ceiling)
        self.assertIn("does not establish", ceiling)
        self.assertIn("current vera self-state", ceiling)

    def test_newer_target_timestamp_with_wrong_revision_is_stale_not_current(self):
        source = ProviderEvidenceEnvelope(
            provider="github",
            locator="github:source",
            revision="new-source",
            observed_at="2026-09-08T20:00:00Z",
            evidence_class="source_provenance",
            referent="projection",
            scope="SOURCE_OBJECT",
            privacy_class="GOVERNED",
            currentness_basis="exact_source_readback",
            supersession_state="CURRENT_OBSERVATION",
            conflict_state="NONE",
            metadata={"projection_role": "SOURCE"},
        )
        target = ProviderEvidenceEnvelope(
            provider="supabase",
            locator="supabase:projection",
            revision="old-source",
            observed_at="2026-09-09T23:59:59Z",
            evidence_class="persisted_provider_record",
            referent="projection",
            scope="PROVIDER_OBJECT",
            privacy_class="GOVERNED",
            currentness_basis="exact_target_readback",
            supersession_state="CURRENT_OBSERVATION",
            conflict_state="NONE",
            metadata={"projection_role": "TARGET"},
        )
        result = reconcile_exact("projection", [source, target], expected_revision="new-source")
        self.assertEqual(result.status, "STALE_PROJECTION")

    def test_temporal_cannot_turn_conflict_into_verified_state(self):
        rows = [
            ProviderEvidenceEnvelope(
                provider="github",
                locator="github:a",
                revision="a",
                observed_at="2026-09-08T20:00:00Z",
                evidence_class="source_provenance",
                referent="x",
                scope="SOURCE_OBJECT",
                privacy_class="GOVERNED",
                currentness_basis="readback",
                supersession_state="CURRENT_OBSERVATION",
                conflict_state="NONE",
            ),
            ProviderEvidenceEnvelope(
                provider="supabase",
                locator="supabase:b",
                revision="b",
                observed_at="2026-09-08T20:00:01Z",
                evidence_class="persisted_provider_record",
                referent="x",
                scope="PROVIDER_OBJECT",
                privacy_class="GOVERNED",
                currentness_basis="readback",
                supersession_state="CURRENT_OBSERVATION",
                conflict_state="NONE",
            ),
            ProviderEvidenceEnvelope(
                provider="temporal",
                locator="temporal:event",
                revision="event-1",
                observed_at="2026-09-08T20:00:02Z",
                evidence_class="persisted_provider_record",
                referent="x",
                scope="CHRONOLOGY_ONLY",
                privacy_class="GOVERNED",
                currentness_basis="recorded_event",
                supersession_state="NOT_APPLICABLE",
                conflict_state="NOT_APPLICABLE",
            ),
        ]
        self.assertEqual(reconcile_exact("x", rows).status, "CONFLICT")

    def test_unbound_drive_companion_cannot_claim_exact_freshness(self):
        row = load_fixture()["observations"]["drive_cohesion_companion"]
        result = reconcile_exact("cohesion-readable-companion", [envelope(row)])
        self.assertEqual(result.status, "UNRESOLVED")

    def test_radar_projection_scope_excludes_current_project_lane(self):
        fixture = load_fixture()["live_scope_facts"]
        self.assertFalse(fixture["cohesion_bus_is_radar_projection_candidate"])
        self.assertEqual(fixture["radar_projection_ref_pattern"], "refs/heads/bus/**")
        self.assertEqual(fixture["radar_projection_path_pattern"], "messages/**")
        fabric = load_provider_fabric(FABRIC)
        row = next(item for item in fabric["projections"] if item["id"] == "projection:chat-bus-github-to-supabase-radar")
        self.assertEqual(row["source_ref_pattern"], "refs/heads/bus/**")
        self.assertEqual(row["source_path_pattern"], "messages/**")

    def test_provider_capability_and_persistence_cannot_self_promote(self):
        fabric = load_provider_fabric(FABRIC)
        for provider_id in ("google_drive", "supabase", "temporal"):
            guard = fabric["providers"][provider_id]["promotion_guard"].lower()
            self.assertIn("does not establish", guard)
        with self.assertRaises(ValueError):
            ProviderEvidenceEnvelope(
                provider="supabase",
                locator="supabase:x",
                revision="x",
                observed_at="2026-09-08T20:00:00Z",
                evidence_class="persisted_provider_record",
                referent="vera",
                scope="SELF_STATE",
                privacy_class="PRIVATE_SELF_STATE",
                currentness_basis="persistence_only",
                supersession_state="CURRENT_OBSERVATION",
                conflict_state="NONE",
                metadata={"current_authority": True},
            )

    def test_exact_match_does_not_establish_phenomenology(self):
        fixture = load_fixture()["observations"]
        result = reconcile_exact(
            "semanticatlas-runtime-snapshot",
            [envelope(fixture["semanticatlas_github"]), envelope(fixture["semanticatlas_supabase"])],
        )
        self.assertEqual(result.status, "VERIFIED_EXACT")
        self.assertIn("phenomenology", result.authoritative_claim_ceiling.lower())


if __name__ == "__main__":
    unittest.main()
