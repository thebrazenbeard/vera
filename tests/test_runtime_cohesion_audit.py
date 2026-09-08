import json
from pathlib import Path
import unittest

from runtime_cohesion.audit import audit_registered_projections
from runtime_cohesion.evidence import ProviderEvidenceEnvelope, load_provider_fabric

ROOT = Path(__file__).resolve().parents[1]
FABRIC_PATH = ROOT / "architecture" / "VERA_PROVIDER_FABRIC_V1.json"
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "runtime_cohesion" / "provider-observations-v1.json"


def env(row):
    return ProviderEvidenceEnvelope(**row)


def simple(provider, revision, role):
    return ProviderEvidenceEnvelope(
        provider=provider,
        locator=f"{provider}:fixture",
        revision=revision,
        observed_at="2026-09-09T00:00:00Z",
        evidence_class="coordination_record" if provider in {"github", "supabase"} else "persisted_provider_record",
        referent="bus-message-projection",
        scope="PROJECTION_OBJECT",
        privacy_class="GOVERNED",
        currentness_basis="exact_readback",
        supersession_state="CURRENT_OBSERVATION",
        conflict_state="NONE",
        metadata={"projection_role": role},
    )


class RuntimeCohesionAuditTests(unittest.TestCase):
    def setUp(self):
        self.fabric = load_provider_fabric(FABRIC_PATH)
        self.fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_semanticatlas_registered_exact_projection_is_verified(self):
        rows = self.fixture["observations"]
        audit = audit_registered_projections(
            self.fabric,
            {
                "projection:semanticatlas-github-to-supabase": {
                    "source": env(rows["semanticatlas_github"]),
                    "target": env(rows["semanticatlas_supabase"]),
                    "source_ref": "refs/heads/research/cee-always-active-v0.2",
                    "source_path": "runtime-manifest/current.json",
                }
            },
        )
        result = audit[0]
        self.assertEqual(result.status, "VERIFIED_EXACT")

    def test_out_of_scope_project_bus_lane_is_not_stale(self):
        audit = audit_registered_projections(
            self.fabric,
            {
                "projection:chat-bus-github-to-supabase-radar": {
                    "source": simple("github", "new-project-head", "SOURCE"),
                    "target": None,
                    "source_ref": "refs/heads/project/vera-runtime-cohesion-v1",
                    "source_path": "projects/vera-runtime-cohesion/messages/x.md",
                }
            },
        )
        self.assertEqual(audit[0].status, "NOT_APPLICABLE")

    def test_in_scope_bus_projection_with_old_target_is_stale(self):
        audit = audit_registered_projections(
            self.fabric,
            {
                "projection:chat-bus-github-to-supabase-radar": {
                    "source": simple("github", "new-bus-head", "SOURCE"),
                    "target": simple("supabase", "old-bus-head", "TARGET"),
                    "source_ref": "refs/heads/bus/vera-v2",
                    "source_path": "messages/vera-v2-9999.md",
                }
            },
        )
        self.assertEqual(audit[0].status, "STALE_PROJECTION")

    def test_missing_in_scope_target_is_absent(self):
        audit = audit_registered_projections(
            self.fabric,
            {
                "projection:chat-bus-github-to-supabase-radar": {
                    "source": simple("github", "new-bus-head", "SOURCE"),
                    "target": None,
                    "source_ref": "refs/heads/bus/vera-v2",
                    "source_path": "messages/vera-v2-9999.md",
                }
            },
        )
        self.assertEqual(audit[0].status, "ABSENT")

    def test_unbound_legacy_drive_companion_is_unresolved_not_guessed_stale(self):
        rows = self.fixture["observations"]
        source = ProviderEvidenceEnvelope(
            provider="github",
            locator="github:thebrazenbeard/vera/architecture/VERA_COHESION_INDEX_V1.json",
            revision="current-cohesion-head",
            observed_at="2026-09-09T00:00:00Z",
            evidence_class="source_provenance",
            referent="vera-runtime-cohesion-readable-companion",
            scope="SOURCE_OBJECT",
            privacy_class="GOVERNED",
            currentness_basis="fresh_branch_readback",
            supersession_state="CURRENT_OBSERVATION",
            conflict_state="NONE",
            metadata={"projection_role": "SOURCE"},
        )
        audit = audit_registered_projections(
            self.fabric,
            {
                "projection:cohesion-github-to-drive-readable-companion": {
                    "source": source,
                    "target": env(rows["drive_cohesion_companion"]),
                    "source_ref": "refs/heads/work/vera-runtime-cohesion-v1-20260908",
                    "source_path": "architecture/VERA_COHESION_INDEX_V1.json",
                }
            },
        )
        self.assertEqual(audit[0].status, "UNRESOLVED")
        self.assertIn("source revision", audit[0].reason.lower())

    def test_semantic_companion_with_bound_old_source_is_stale(self):
        target = ProviderEvidenceEnvelope(
            provider="google_drive",
            locator="drive:companion",
            revision="modified:later",
            observed_at="2026-09-09T01:00:00Z",
            evidence_class="persisted_provider_record",
            referent="vera-runtime-cohesion-readable-companion",
            scope="SEMANTIC_COMPANION",
            privacy_class="GOVERNED",
            currentness_basis="source_revision_binding",
            supersession_state="CURRENT_OBSERVATION",
            conflict_state="NONE",
            metadata={"projection_role": "TARGET", "bound_source_revision": "old-source"},
        )
        source = ProviderEvidenceEnvelope(
            provider="github",
            locator="github:cohesion",
            revision="new-source",
            observed_at="2026-09-09T00:00:00Z",
            evidence_class="source_provenance",
            referent="vera-runtime-cohesion-readable-companion",
            scope="SOURCE_OBJECT",
            privacy_class="GOVERNED",
            currentness_basis="branch_readback",
            supersession_state="CURRENT_OBSERVATION",
            conflict_state="NONE",
            metadata={"projection_role": "SOURCE"},
        )
        audit = audit_registered_projections(
            self.fabric,
            {
                "projection:cohesion-github-to-drive-readable-companion": {
                    "source": source,
                    "target": target,
                    "source_ref": "refs/heads/work/vera-runtime-cohesion-v1-20260908",
                    "source_path": "architecture/VERA_RUNTIME_CONTRACT_V1.json",
                }
            },
        )
        self.assertEqual(audit[0].status, "STALE_PROJECTION")


if __name__ == "__main__":
    unittest.main()
