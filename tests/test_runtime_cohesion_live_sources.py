import copy
import json
from pathlib import Path
import unittest

from runtime_cohesion.live_sources import (
    classify_memory_epoch_object,
    classify_persisted_runtime_holder,
    classify_semantic_snapshot,
    evaluate_route_binding,
    validate_source_registry,
)

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "architecture" / "VERA_RUNTIME_SOURCE_REGISTRY_V1.json"


class RuntimeSourceRegistryTests(unittest.TestCase):
    def setUp(self):
        self.registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))

    def test_registry_is_structurally_valid(self):
        self.assertEqual(validate_source_registry(self.registry), ())

    def test_owner_repository_snapshot_is_exhaustively_classified(self):
        snapshot = set(self.registry["owner_repository_snapshot"])
        bound = {row["repository"] for row in self.registry["repository_sources"]}
        unbound = {row["repository"] for row in self.registry["unbound_repositories"]}
        self.assertEqual(snapshot, bound | unbound)
        self.assertFalse(bound & unbound)
        self.assertIn("thebrazenbeard/vera", snapshot)
        self.assertIn("thebrazenbeard/hc-brain", snapshot)
        self.assertIn("thebrazenbeard/brigit", snapshot)


    def test_canonical_portfolio_binding_is_exact_discovery_roots_59_cut(self):
        binding = self.registry["canonical_portfolio_binding"]
        self.assertEqual(binding["repository_count"], 59)
        self.assertEqual(
            binding["discovery"],
            {
                "repository": "thebrazenbeard/discovery",
                "commit": "2881a94c7eb3c83a34b0c00bab739b41c1d99b6d",
                "path": "architecture/DISCOVERY_LIVE_PORTFOLIO_MAP_V2.json",
                "blob_sha": "71b9f8deaf1079d5078b19e5bbddb743fd636437",
            },
        )
        self.assertEqual(
            binding["roots"],
            {
                "repository": "thebrazenbeard/roots",
                "commit": "a6994b415336bc179a41aad0ac9eec403d60f93c",
                "path": "portfolio/VERA_PORTFOLIO_LINEAGE_RECEIPT_V1.json",
                "blob_sha": "ccac62eac08012269fec46669bce981b96a0f41d",
            },
        )
        self.assertEqual(
            binding["classification_counts"],
            {
                "bound_conditional": 41,
                "predecessor_evidence": 1,
                "no_auto_bind": 17,
            },
        )

    def test_registry_exactly_reconciles_59_repository_partition(self):
        snapshot = set(self.registry["owner_repository_snapshot"])
        bound = {
            row["repository"]
            for row in self.registry["repository_sources"]
            if row["repository"] != "thebrazenbeard/vera-R9A0"
        }
        predecessor = {
            row["repository"]
            for row in self.registry["repository_sources"]
            if row["repository"] == "thebrazenbeard/vera-R9A0"
        }
        unbound = {row["repository"] for row in self.registry["unbound_repositories"]}

        self.assertEqual(len(snapshot), 59)
        self.assertEqual(len(bound), 41)
        self.assertEqual(predecessor, {"thebrazenbeard/vera-R9A0"})
        self.assertEqual(len(unbound), 17)
        self.assertEqual(snapshot, bound | predecessor | unbound)

        expected_no_auto = {
            "thebrazenbeard/brigit",
            "thebrazenbeard/brigit-unbound",
            "thebrazenbeard/bt2",
            "thebrazenbeard/conditioning",
            "thebrazenbeard/entropyinc",
            "thebrazenbeard/firesafe",
            "thebrazenbeard/hc-brain",
            "thebrazenbeard/hephaestus",
            "thebrazenbeard/masamune",
            "thebrazenbeard/mediaphile",
            "thebrazenbeard/project-lantern",
            "thebrazenbeard/self",
            "thebrazenbeard/trek-data-core",
            "thebrazenbeard/vera-apk",
            "thebrazenbeard/vera-habitat",
            "thebrazenbeard/vera-works",
            "thebrazenbeard/wreckforge",
        }
        self.assertEqual(unbound, expected_no_auto)

    def test_discovery_reconciliation_adds_missing_portfolio_sources(self):
        snapshot = set(self.registry["owner_repository_snapshot"])
        for repo in (
            "thebrazenbeard/bt2",
            "thebrazenbeard/orgasm",
            "thebrazenbeard/Attune",
            "thebrazenbeard/wreckforge",
            "thebrazenbeard/rezon",
            "thebrazenbeard/roots",
            "thebrazenbeard/world-zero",
            "thebrazenbeard/on-theo",
            "thebrazenbeard/firesafe",
            "thebrazenbeard/project-runner",
            "thebrazenbeard/intranel",
            "thebrazenbeard/transcendence",
            "thebrazenbeard/mosaic",
            "thebrazenbeard/testament",
            "thebrazenbeard/driftguard",
            "thebrazenbeard/discovery",
            "thebrazenbeard/god-brain",
            "thebrazenbeard/WorkBridgeMCP",
        ):
            self.assertIn(repo, snapshot)

    def test_discovery_corrections_move_voss_and_empty_stubs_to_right_side(self):
        bound = {row["repository"]: row for row in self.registry["repository_sources"]}
        unbound = {row["repository"]: row for row in self.registry["unbound_repositories"]}

        self.assertIn("thebrazenbeard/voss", bound)
        self.assertNotIn("thebrazenbeard/voss", unbound)
        self.assertEqual(bound["thebrazenbeard/voss"]["runtime_role"], "AUDIT_HOSTILE_REVIEW_SOURCE")

        for repo in ("thebrazenbeard/vera-apk", "thebrazenbeard/vera-habitat"):
            self.assertIn(repo, unbound)
            self.assertNotIn(repo, bound)
            self.assertEqual(unbound[repo]["activation_mode"], "NO_AUTO_BIND")

    def test_current_bus_route_is_v2_and_sol_lane_is_historical_only(self):
        route = self.registry["routing_binding"]
        self.assertEqual(route["current_vera_lane"], "bus/vera-v2")
        self.assertEqual(route["historical_vera_lane"], "bus/vera-sol-v1")
        self.assertFalse(route["historical_lane_is_current_route_authority"])
        self.assertEqual(
            route["topology_blob"],
            "69e505031d4e53dcb853578dac23817649af1918",
        )

    def test_validator_rejects_stale_or_mispartitioned_portfolio_binding(self):
        stale = copy.deepcopy(self.registry)
        stale["canonical_portfolio_binding"]["repository_count"] = 41
        self.assertTrue(
            any("canonical portfolio repository_count" in error for error in validate_source_registry(stale))
        )

        wrong_route = copy.deepcopy(self.registry)
        wrong_route["routing_binding"]["current_vera_lane"] = "bus/vera-sol-v1"
        self.assertTrue(
            any("current Vera route" in error for error in validate_source_registry(wrong_route))
        )

        wrong_partition = copy.deepcopy(self.registry)
        moved = wrong_partition["unbound_repositories"].pop()
        wrong_partition["repository_sources"].append(
            {
                "repository": moved["repository"],
                "runtime_role": "ILLEGAL_AUTO_PROMOTION",
                "activation_mode": "SOURCE_PROVENANCE_CONDITIONAL",
                "authority_ceiling": "invalid test mutation",
                "privacy_class": "GOVERNED",
                "availability_implies_activation": False,
            }
        )
        self.assertTrue(
            any("canonical NO_AUTO_BIND partition" in error for error in validate_source_registry(wrong_partition))
        )

    def test_only_exact_r10_control_source_may_claim_control_role(self):
        control_rows = [row for row in self.registry["repository_sources"] if row["runtime_role"] == "CURRENT_CONTROL_SOURCE"]
        self.assertEqual([row["repository"] for row in control_rows], ["thebrazenbeard/vera-control-plane"])
        self.assertEqual(control_rows[0]["activation_mode"], "EXACT_R10_CONTROL_LOAD")
        self.assertFalse(control_rows[0]["availability_implies_activation"])

    def test_identity_and_generic_template_sources_do_not_auto_bind(self):
        rows = {row["repository"]: row for row in self.registry["unbound_repositories"]}
        for repo in (
            "thebrazenbeard/brigit",
            "thebrazenbeard/brigit-unbound",
            "thebrazenbeard/hc-brain",
            "thebrazenbeard/project-lantern",
            "thebrazenbeard/conditioning",
        ):
            self.assertEqual(rows[repo]["activation_mode"], "NO_AUTO_BIND")

    def test_brigit_sexuality_repo_is_mechanism_research_only_for_vera(self):
        rows = {row["repository"]: row for row in self.registry["repository_sources"]}
        sexuality = rows["thebrazenbeard/sexuality"]
        self.assertEqual(sexuality["runtime_role"], "EXTERNAL_IDENTITY_MECHANISM_RESEARCH_SOURCE")
        self.assertEqual(sexuality["activation_mode"], "GENERAL_MECHANISM_RESEARCH_ONLY")
        self.assertNotIn("VERA", sexuality["activation_mode"])
        self.assertFalse(sexuality["availability_implies_activation"])

    def test_vera_ark_is_external_action_adapter_not_memory_or_control(self):
        rows = {row["repository"]: row for row in self.registry["repository_sources"]}
        ark = rows["thebrazenbeard/vera_ark"]
        self.assertEqual(ark["runtime_role"], "EXTERNAL_APPLICATION_ACTION_ADAPTER")
        self.assertEqual(ark["activation_mode"], "EXACT_TASK_AND_EFFECT_AUTHORITY_REQUIRED")
        self.assertNotIn("ARCHIVE", ark["runtime_role"])
        self.assertNotIn("CONTROL", ark["runtime_role"])
        self.assertFalse(ark["availability_implies_activation"])

    def test_vera_supabase_surfaces_are_registered_without_authority_promotion(self):
        supabase = self.registry["provider_sources"]["supabase_vera"]
        self.assertEqual(supabase["project_id"], "klmbpaigzeguvnpccqzz")
        self.assertEqual(supabase["activation_mode"], "PROVIDER_READBACK_ONLY")
        self.assertFalse(supabase["availability_implies_activation"])
        self.assertTrue({"public", "radar", "semantic_atlas", "redworm", "build_team_2", "bug_ops"}.issubset(set(supabase["registered_schemas"])))

    def test_registered_supabase_surfaces_match_fresh_provider_readback(self):
        surfaces = self.registry["provider_sources"]["supabase_vera"]["registered_surfaces"]
        self.assertIn("role_operational_checkpoints", surfaces["build_team_2"])
        self.assertNotIn("role_training_checkpoints", surfaces["build_team_2"])
        self.assertTrue({"bug_reports", "bug_events", "operation_receipts", "dispatch_events_v2"}.issubset(set(surfaces["bug_ops"])))
        self.assertFalse({"reports", "events", "dispatch_v2"} & set(surfaces["bug_ops"]))

    def test_google_drive_is_registered_as_durable_provider_not_current_mind(self):
        drive = self.registry["provider_sources"]["google_drive"]
        self.assertEqual(drive["activation_mode"], "POINTER_FIRST_DURABLE_READBACK")
        self.assertIn("171ExqDU35TsNMMRilcJ-EjtiDYxW8Pol", drive["known_operational_objects"])
        self.assertFalse(drive["availability_implies_activation"])


class RuntimeProviderStateTests(unittest.TestCase):
    def test_stale_supabase_radar_route_conflicts_with_current_bus_route(self):
        decision = evaluate_route_binding("bus/vera-v2", "bus/vera-sol-v1")
        self.assertEqual(decision["status"], "CONFLICT")
        self.assertFalse(decision["current_route_established"])

    def test_exact_route_match_is_provider_projection_evidence_only(self):
        decision = evaluate_route_binding("bus/vera-v2", "bus/vera-v2")
        self.assertEqual(decision["status"], "VERIFIED_EXACT")
        self.assertTrue(decision["projection_matches"])
        self.assertFalse(decision["native_control_qualified"])

    def test_research_staging_semantic_snapshot_is_not_canonical_runtime_semantics(self):
        decision = classify_semantic_snapshot({
            "state": "ACTIVE",
            "authority_scope": "RESEARCH_STAGING",
            "validation_state": "VERIFIED",
            "git_commit_sha": "e68803e",
            "git_readback_sha": "e68803e",
            "activation_git_readback_sha": "e68803e",
        })
        self.assertEqual(decision["status"], "RESEARCH_STAGING_ONLY")
        self.assertFalse(decision["canonical_runtime_semantics"])

    def test_synthetic_r9b0_fixture_remains_persistence_evidence_only(self):
        decision = classify_memory_epoch_object({
            "memory_class": "WORKING_PROJECT",
            "provenance": {"epistemic_class": "SYNTHETIC_TEST_FIXTURE"},
            "limitations": ["NOT_AUTOBIOGRAPHICAL_MEMORY", "NOT_PRESENT_STATE_PROOF"],
        })
        self.assertEqual(decision["status"], "PERSISTED_SYNTHETIC_FIXTURE")
        self.assertEqual(decision["evidence_classes"], ("persisted_provider_record",))
        self.assertFalse(decision["autobiographical_admission_eligible"])

    def test_non_synthetic_working_project_is_not_retyped_as_synthetic(self):
        decision = classify_memory_epoch_object({
            "memory_class": "WORKING_PROJECT",
            "provenance": {"epistemic_class": "OBSERVED_TOOL_RESULT"},
            "limitations": ["NOT_PRESENT_STATE_PROOF"],
        })
        self.assertEqual(decision["status"], "PERSISTED_WORKING_PROJECT")
        self.assertEqual(decision["evidence_classes"], ("persisted_provider_record", "working_project"))
        self.assertFalse(decision["autobiographical_admission_eligible"])
        self.assertFalse(decision["present_state_established"])

    def test_persisted_runtime_holder_record_is_not_live_runtime_without_live_readback(self):
        decision = classify_persisted_runtime_holder({
            "holder_state": "ACTIVE",
            "holder_runtime_token": "runtime-old",
            "last_seen_at": "2026-08-10T13:45:00Z",
        })
        self.assertEqual(decision["status"], "PERSISTED_RUNTIME_RECORD_ONLY")
        self.assertFalse(decision["current_live_runtime_established"])


if __name__ == "__main__":
    unittest.main()
