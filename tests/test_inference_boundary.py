from __future__ import annotations

import importlib.util
import unittest

from runtime_cohesion import inference_boundary as ib


def require(testcase: unittest.TestCase, name: str):
    testcase.assertTrue(hasattr(ib, name), f"missing inference-boundary API: {name}")
    return getattr(ib, name)


class InferenceBoundaryBootstrapTests(unittest.TestCase):
    def test_inference_boundary_module_exists(self):
        self.assertIsNotNone(importlib.util.find_spec("runtime_cohesion.inference_boundary"))


class StateCompositionTests(unittest.TestCase):
    def component(self, **overrides):
        StateComponentRef = require(self, "StateComponentRef")
        canonical_digest = require(self, "canonical_digest")
        payload = overrides.pop("payload", {"activation": 0.4, "salience": ["cohesion"]})
        values = dict(
            component_id="affect:1",
            domain_id="affect",
            source_locator="runtime://affect/current",
            source_revision="rev-a",
            component_generation="2",
            content_digest=canonical_digest(payload),
            observed_at="2026-09-12T14:00:00Z",
            currentness_basis="LIVE_OBSERVATION",
            supersession_state="CURRENT_OBSERVATION",
            conflict_state="NONE",
            privacy_classification="PROJECT_PRIVATE",
            allowed_egress_scopes=frozenset({"PROJECT_PRIVATE_HOST", "LOCAL_PROCESS_ONLY"}),
            disclosure_source="policy://affect",
            disclosure_generation="1",
            requirement_class="OPTIONAL",
            payload=payload,
            payload_ref=None,
        )
        values.update(overrides)
        return StateComponentRef(**values)

    def test_inline_payload_digest_mismatch_fails(self):
        StateComponentRef = require(self, "StateComponentRef")
        with self.assertRaisesRegex(ValueError, "digest"):
            StateComponentRef(
                component_id="affect:1", domain_id="affect", source_locator="x",
                source_revision="r", component_generation="1", content_digest="0" * 64,
                observed_at="t", currentness_basis="live",
                supersession_state="CURRENT_OBSERVATION", conflict_state="NONE",
                privacy_classification="PROJECT_PRIVATE",
                allowed_egress_scopes=frozenset({"LOCAL_PROCESS_ONLY"}),
                disclosure_source="p", disclosure_generation="1",
                requirement_class="OPTIONAL", payload={"x": 1}, payload_ref=None,
            )

    def test_component_requires_exact_payload_or_pointer(self):
        StateComponentRef = require(self, "StateComponentRef")
        with self.assertRaisesRegex(ValueError, "payload"):
            StateComponentRef(
                component_id="x", domain_id="x", source_locator="x", source_revision="r",
                component_generation="1", content_digest="a" * 64, observed_at="t",
                currentness_basis="live", supersession_state="CURRENT_OBSERVATION",
                conflict_state="NONE", privacy_classification="PROJECT_PRIVATE",
                allowed_egress_scopes=frozenset({"LOCAL_PROCESS_ONLY"}),
                disclosure_source="p", disclosure_generation="1",
                requirement_class="OPTIONAL", payload=None, payload_ref=None,
            )

    def test_duplicate_component_ids_fail(self):
        compose_state = require(self, "compose_state")
        a = self.component()
        b = self.component(source_revision="rev-b")
        with self.assertRaisesRegex(ValueError, "duplicate"):
            compose_state(subject="vera", components=[a, b], omissions=[], policy_revision="r3")

    def test_noncurrent_or_conflicted_component_fails_composition(self):
        compose_state = require(self, "compose_state")
        with self.assertRaisesRegex(ValueError, "current"):
            compose_state(
                subject="vera",
                components=[self.component(supersession_state="SUPERSEDED")],
                omissions=[], policy_revision="r3",
            )
        with self.assertRaisesRegex(ValueError, "conflict"):
            compose_state(
                subject="vera",
                components=[self.component(conflict_state="CONFLICT")],
                omissions=[], policy_revision="r3",
            )

    def test_optional_omission_changes_composition_digest(self):
        OmissionRecord = require(self, "OmissionRecord")
        compose_state = require(self, "compose_state")
        component = self.component()
        base = compose_state(subject="vera", components=[component], omissions=[], policy_revision="r3")
        omitted = compose_state(
            subject="vera",
            components=[component],
            omissions=[OmissionRecord(
                component_id="memory:1", domain_id="memory_salience",
                reason="unavailable", observed_at="t", evidence_ref="probe://memory",
                requirement_class="OPTIONAL",
            )],
            policy_revision="r3",
        )
        self.assertNotEqual(base.composition_digest, omitted.composition_digest)

    def test_mandatory_omission_cannot_be_admitted(self):
        OmissionRecord = require(self, "OmissionRecord")
        compose_state = require(self, "compose_state")
        bind_admitted_state = require(self, "bind_admitted_state")
        composition = compose_state(
            subject="vera", components=[self.component()],
            omissions=[OmissionRecord(
                component_id="identity:1", domain_id="identity", reason="missing",
                observed_at="t", evidence_ref="probe://identity", requirement_class="OPTIONAL",
            )], policy_revision="r3",
        )
        with self.assertRaisesRegex(ValueError, "mandatory"):
            bind_admitted_state(
                composition,
                admission_receipt_digest="b" * 64,
                admitted_component_ids={"affect:1"},
                mandatory_component_ids={"identity:1"},
                target_egress_scope="LOCAL_PROCESS_ONLY",
                forbidden_domains={"truth", "authorization"},
                admission_currentness_basis="receipt://current",
                admission_epoch_or_lease="epoch-1",
                admitted_at="t",
            )

    def test_egress_is_explicit_set_membership_not_scope_ordering(self):
        compose_state = require(self, "compose_state")
        bind_admitted_state = require(self, "bind_admitted_state")
        composition = compose_state(subject="vera", components=[self.component()], omissions=[], policy_revision="r3")
        admitted = bind_admitted_state(
            composition,
            admission_receipt_digest="b" * 64,
            admitted_component_ids={"affect:1"}, mandatory_component_ids=set(),
            target_egress_scope="PROJECT_PRIVATE_HOST",
            forbidden_domains={"truth"}, admission_currentness_basis="receipt://current",
            admission_epoch_or_lease="epoch-1", admitted_at="t",
        )
        self.assertEqual(admitted.admitted_disclosure_scope, "PROJECT_PRIVATE_HOST")
        with self.assertRaisesRegex(ValueError, "egress"):
            bind_admitted_state(
                composition,
                admission_receipt_digest="b" * 64,
                admitted_component_ids={"affect:1"}, mandatory_component_ids=set(),
                target_egress_scope="APPROVED_EXTERNAL_PROVIDER",
                forbidden_domains={"truth"}, admission_currentness_basis="receipt://current",
                admission_epoch_or_lease="epoch-1", admitted_at="t",
            )


if __name__ == "__main__":
    unittest.main()
