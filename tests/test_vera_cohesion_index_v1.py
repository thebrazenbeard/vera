import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "architecture" / "VERA_COHESION_INDEX_V1.json"

EXPECTED_SYSTEM_FIELDS = {
    "id",
    "locator",
    "role",
    "authority_class",
    "retrieval_entrypoint",
    "lifecycle_summary",
    "proof_unit_refs",
}
EXPECTED_DOMAIN_FIELDS = {
    "id",
    "authority_resolver_ref",
    "evidence_sources",
    "retrieval_targets",
    "dependencies",
    "failure_signature_refs",
    "privacy_class",
    "fail_closed_behavior",
}
REQUIRED_TARGET_FIELDS = {"source_ref", "route_ref", "evidence_capability_refs"}
OPTIONAL_TARGET_FIELDS = {"selector_ref"}
EXPECTED_ROUTE_FIELDS = {"id", "locator", "declaration_state"}
LIFECYCLE_SEMANTICS = "NAVIGATION_ONLY_NON_AUTHORITATIVE_NON_MONOTONIC"
AUTHORITY_PREFIX = "VERA_RUNTIME_CONTRACT_V1#authority_resolvers."
EVIDENCE_PREFIX = "VERA_RUNTIME_CONTRACT_V1#evidence_classes."
FAILURE_PREFIX = "VERA_RUNTIME_CONTRACT_V1#failure_signatures."


def load_index():
    return json.loads(INDEX.read_text(encoding="utf-8"))


class VeraCohesionIndexV1Tests(unittest.TestCase):
    def test_fixed_system_inventory_is_explicit_and_temporal_is_auxiliary(self):
        self.assertTrue(INDEX.exists(), "consolidated cohesion index must exist")
        document = load_index()
        self.assertEqual(document["schema"], "VERA_COHESION_INDEX_V1")
        systems = document["systems"]
        self.assertEqual(len(systems), 13)
        ids = [system["id"] for system in systems]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn("supabase-vera-production", ids)
        self.assertNotIn("supabase-production", ids)
        self.assertNotIn("temporal", ids)
        self.assertEqual(document["auxiliary_sources"]["temporal"]["role"], "CHRONOLOGY_ONLY")

    def test_system_rows_are_compact_navigation_not_authority_proof(self):
        for system in load_index()["systems"]:
            self.assertEqual(set(system), EXPECTED_SYSTEM_FIELDS)
            self.assertEqual(system["lifecycle_summary"]["semantics"], LIFECYCLE_SEMANTICS)
            self.assertIsInstance(system["proof_unit_refs"], list)
            self.assertEqual(
                system["proof_unit_refs"],
                [],
                "proof-unit refs remain empty until an exact dereferenceable registry exists",
            )
            self.assertNotEqual(system["authority_class"], "CURRENT_AUTHORITY_OWNER")

    def test_routes_are_declarations_not_runtime_availability_claims(self):
        document = load_index()
        routes = document.get("route_declarations")
        self.assertIsInstance(routes, list)
        route_ids = [route["id"] for route in routes]
        self.assertEqual(len(route_ids), len(set(route_ids)))
        for route in routes:
            self.assertEqual(set(route), EXPECTED_ROUTE_FIELDS)
            self.assertEqual(route["declaration_state"], "DECLARED")
            self.assertTrue(route["locator"])

    def test_domains_use_one_resolver_with_many_capability_typed_targets(self):
        document = load_index()
        domains = document.get("domains")
        self.assertIsInstance(domains, list, "consolidated index requires domains")
        domain_ids = [domain["id"] for domain in domains]
        self.assertEqual(len(domain_ids), len(set(domain_ids)))
        known_sources = {system["id"] for system in document["systems"]} | set(document["auxiliary_sources"])
        known_routes = {route["id"] for route in document["route_declarations"]}
        known_selectors = {selector["id"] for selector in document.get("selector_declarations", [])}
        for domain in domains:
            self.assertEqual(set(domain), EXPECTED_DOMAIN_FIELDS)
            self.assertTrue(domain["authority_resolver_ref"].startswith(AUTHORITY_PREFIX), domain["id"])
            self.assertTrue(domain["evidence_sources"], domain["id"])
            self.assertTrue(set(domain["evidence_sources"]).issubset(known_sources), domain["id"])
            self.assertTrue(domain["retrieval_targets"], domain["id"])
            for target in domain["retrieval_targets"]:
                self.assertTrue(REQUIRED_TARGET_FIELDS.issubset(target), domain["id"])
                self.assertTrue(set(target).issubset(REQUIRED_TARGET_FIELDS | OPTIONAL_TARGET_FIELDS), domain["id"])
                self.assertIn(target["source_ref"], known_sources, domain["id"])
                self.assertIn(target["route_ref"], known_routes, domain["id"])
                self.assertTrue(target["evidence_capability_refs"], domain["id"])
                for capability in target["evidence_capability_refs"]:
                    self.assertTrue(capability.startswith(EVIDENCE_PREFIX), domain["id"])
                if "selector_ref" in target:
                    self.assertIn(target["selector_ref"], known_selectors)
            self.assertTrue(domain["fail_closed_behavior"], domain["id"])

    def test_failure_signatures_are_contract_refs_not_opaque_local_labels(self):
        for domain in load_index()["domains"]:
            for value in domain["failure_signature_refs"]:
                self.assertTrue(value.startswith(FAILURE_PREFIX), f"{domain['id']} -> {value}")
                self.assertLessEqual(len(value), 160)
                self.assertNotIn("\n", value)

    def test_dependency_graph_refs_resolve_without_requiring_dag(self):
        domains = load_index()["domains"]
        domain_ids = {domain["id"] for domain in domains}
        for domain in domains:
            self.assertTrue(set(domain["dependencies"]).issubset(domain_ids), domain["id"])


if __name__ == "__main__":
    unittest.main()
