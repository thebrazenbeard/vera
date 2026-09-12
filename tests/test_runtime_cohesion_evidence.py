import json
from pathlib import Path
import unittest

from runtime_cohesion.evidence import ProviderEvidenceEnvelope, load_provider_fabric

ROOT = Path(__file__).resolve().parents[1]
FABRIC = ROOT / "architecture" / "VERA_PROVIDER_FABRIC_V1.json"


BASE = dict(
    provider="github",
    locator="github:thebrazenbeard/vera@deadbeef",
    revision="deadbeef",
    observed_at="2026-09-08T22:00:00Z",
    evidence_class="source_provenance",
    referent="vera-runtime-cohesion",
    scope="SOURCE_OBJECT",
    privacy_class="GOVERNED",
    currentness_basis="exact_ref_readback",
    supersession_state="CURRENT_OBSERVATION",
    conflict_state="NONE",
    content_digest=None,
    receipt_ref=None,
    metadata={},
)


class ProviderEvidenceTests(unittest.TestCase):
    def test_timezone_aware_observation_is_required(self):
        values = dict(BASE)
        values["observed_at"] = "2026-09-08T22:00:00"
        with self.assertRaises(ValueError):
            ProviderEvidenceEnvelope(**values)

    def test_required_identity_fields_are_non_empty(self):
        for field in ("provider", "locator", "revision", "evidence_class", "referent", "scope"):
            with self.subTest(field=field):
                values = dict(BASE)
                values[field] = ""
                with self.assertRaises(ValueError):
                    ProviderEvidenceEnvelope(**values)

    def test_conflict_and_supersession_states_are_bounded(self):
        values = dict(BASE)
        values["conflict_state"] = "NEWEST_WINS"
        with self.assertRaises(ValueError):
            ProviderEvidenceEnvelope(**values)
        values = dict(BASE)
        values["supersession_state"] = "WHATEVER_IS_NEWEST"
        with self.assertRaises(ValueError):
            ProviderEvidenceEnvelope(**values)

    def test_persistence_cannot_be_declared_semantic_authority(self):
        values = dict(BASE)
        values.update(
            provider="supabase",
            evidence_class="persisted_provider_record",
            metadata={"semantic_authority": True},
        )
        with self.assertRaises(ValueError):
            ProviderEvidenceEnvelope(**values)

    def test_provider_fabric_is_operational_not_normative(self):
        fabric = load_provider_fabric(FABRIC)
        self.assertEqual(fabric["schema"], "VERA_PROVIDER_FABRIC_V1")
        self.assertEqual(fabric["normative_status"], "NON_NORMATIVE_OPERATIONAL_SUPPORT")
        self.assertEqual(
            set(fabric["providers"]),
            {"github", "google_drive", "supabase", "temporal", "live_conversation"},
        )
        for provider in fabric["providers"].values():
            self.assertIn("promotion_guard", provider)
            self.assertTrue(provider["promotion_guard"])

    def test_projection_registry_has_exact_source_and_target_providers(self):
        fabric = load_provider_fabric(FABRIC)
        self.assertTrue(fabric["projections"])
        provider_ids = set(fabric["providers"])
        for row in fabric["projections"]:
            self.assertIn(row["source_provider"], provider_ids)
            self.assertIn(row["target_provider"], provider_ids)
            self.assertIn(row["comparison_mode"], {"EXACT_REVISION", "EXACT_RECEIPT", "SEMANTIC_COMPANION"})
            self.assertIn("claim_ceiling", row)
            self.assertTrue(row["claim_ceiling"])

    def test_fabric_never_uses_newest_wins(self):
        raw = FABRIC.read_text(encoding="utf-8").lower()
        self.assertNotIn('"newest_wins"', raw)
        self.assertNotIn('"newest wins"', raw)


if __name__ == "__main__":
    unittest.main()
