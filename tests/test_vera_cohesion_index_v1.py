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
    "current_authority_rule_ref",
    "evidence_sources",
    "retrieval_route",
    "dependencies",
    "failure_signatures",
    "privacy_class",
    "fail_closed_behavior",
}
ROUTE_STATES = {"AVAILABLE", "UNAVAILABLE", "UNKNOWN", "CONFLICT"}
LIFECYCLE_SEMANTICS = "NAVIGATION_ONLY_NON_AUTHORITATIVE_NON_MONOTONIC"


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
        self.assertNotIn("temporal", ids)
        self.assertEqual(document["auxiliary_sources"]["temporal"]["role"], "CHRONOLOGY_ONLY")

    def test_system_rows_are_compact_navigation_not_authority_proof(self):
        for system in load_index()["systems"]:
            self.assertEqual(set(system), EXPECTED_SYSTEM_FIELDS)
            self.assertEqual(system["lifecycle_summary"]["semantics"], LIFECYCLE_SEMANTICS)
            self.assertIsInstance(system["proof_unit_refs"], list)
            self.assertNotEqual(system["authority_class"], "CURRENT_AUTHORITY_OWNER")

    def test_domains_have_typed_authority_rule_and_non_orphan_route(self):
        document = load_index()
        domains = document.get("domains")
        self.assertIsInstance(domains, list, "consolidated index requires domains")
        domain_ids = [domain["id"] for domain in domains]
        self.assertEqual(len(domain_ids), len(set(domain_ids)))
        known_sources = {system["id"] for system in document["systems"]} | set(document["auxiliary_sources"])
        for domain in domains:
            self.assertEqual(set(domain), EXPECTED_DOMAIN_FIELDS)
            self.assertTrue(
                domain["current_authority_rule_ref"].startswith("VERA_RUNTIME_CONTRACT_V1#authority_rules."),
                domain["id"],
            )
            self.assertTrue(domain["evidence_sources"], domain["id"])
            self.assertTrue(set(domain["evidence_sources"]).issubset(known_sources), domain["id"])
            route = domain["retrieval_route"]
            self.assertIn(route["state"], ROUTE_STATES)
            if route["state"] == "AVAILABLE":
                self.assertTrue(route.get("entrypoint"), domain["id"])
            else:
                self.assertFalse(route.get("entrypoint"), domain["id"])
                self.assertTrue(domain["fail_closed_behavior"], domain["id"])

    def test_dependencies_and_failure_signatures_are_pointer_sized_and_resolvable(self):
        document = load_index()
        domains = document.get("domains")
        self.assertIsInstance(domains, list, "consolidated index requires domains")
        domain_ids = {domain["id"] for domain in domains}
        auxiliary_ids = {f"aux:{key}" for key in document["auxiliary_sources"]}
        allowed = domain_ids | auxiliary_ids
        for domain in domains:
            for dependency in domain["dependencies"]:
                self.assertIn(dependency, allowed, f"{domain['id']} -> {dependency}")
            for value in domain["dependencies"] + domain["failure_signatures"]:
                self.assertIsInstance(value, str)
                self.assertLessEqual(len(value), 120)
                self.assertNotIn("\n", value)


if __name__ == "__main__":
    unittest.main()
