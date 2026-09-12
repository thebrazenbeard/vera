from __future__ import annotations

import unittest

from runtime_cohesion import inference_boundary as ib


class InferenceBoundaryReviewRepairTests(unittest.TestCase):
    def component(self, component_id: str, *, requirement_class: str = "OPTIONAL"):
        payload = {"activation": 0.4, "component": component_id}
        return ib.StateComponentRef(
            component_id=component_id,
            domain_id="affect",
            source_locator=f"runtime://{component_id}",
            source_revision="rev-a",
            component_generation="1",
            content_digest=ib.canonical_digest(payload),
            observed_at="2026-09-12T15:30:00Z",
            currentness_basis="LIVE_OBSERVATION",
            supersession_state="CURRENT_OBSERVATION",
            conflict_state="NONE",
            privacy_classification="PROJECT_PRIVATE",
            allowed_egress_scopes=frozenset({"PROJECT_PRIVATE_HOST"}),
            disclosure_source="policy://affect",
            disclosure_generation="1",
            requirement_class=requirement_class,
            payload=payload,
            payload_ref=None,
        )

    def composition(self):
        return ib.compose_state(
            subject="vera",
            components=[
                self.component("a", requirement_class="MANDATORY"),
                self.component("b", requirement_class="OPTIONAL"),
            ],
            omissions=[],
            policy_revision="r3-review-repair",
            composed_at="t0",
        )

    def admit(self, admitted_ids):
        return ib.bind_admitted_state(
            self.composition(),
            admission_receipt_digest="b" * 64,
            admitted_component_ids=set(admitted_ids),
            mandatory_component_ids=set(),
            target_egress_scope="PROJECT_PRIVATE_HOST",
            forbidden_domains={"truth", "authorization", "phenomenology"},
            admission_currentness_basis="receipt://current",
            admission_epoch_or_lease="epoch-1",
            admitted_at="t1",
        )

    def capability(self, admitted):
        return ib.bind_capability(
            admitted,
            host_identity="reference-host",
            host_revision="host-r1",
            host_generation="host-g1",
            target_provider_or_host="reference-host",
            target_egress_scope="PROJECT_PRIVATE_HOST",
            model_identity="model-x",
            model_revision="m1",
            adapter_identity="cohesion",
            adapter_revision="r3-review-repair",
            requested_backend="TEXT_CONTEXT_V1",
            supported_projection_backends={"TEXT_CONTEXT_V1"},
            backend_constraints={"max_chars": 4096},
            bound_at="t2",
        )

    def test_source_declared_mandatory_component_cannot_be_downgraded_by_caller(self):
        with self.assertRaisesRegex(ValueError, "mandatory"):
            self.admit({"b"})

    def test_capability_is_bound_to_exact_admission_result_not_only_composition(self):
        admitted_a = self.admit({"a"})
        capability_a = self.capability(admitted_a)
        admitted_ab = self.admit({"a", "b"})

        self.assertEqual(admitted_a.composition_digest, admitted_ab.composition_digest)
        self.assertNotEqual(admitted_a.admitted_state_digest, admitted_ab.admitted_state_digest)

        with self.assertRaisesRegex(ValueError, "admitted-state"):
            ib.project_text_context(admitted_ab, capability_a)

    def test_reservation_rechecks_exact_admission_digest(self):
        admitted_a = self.admit({"a"})
        capability_a = self.capability(admitted_a)
        projection_a = ib.project_text_context(admitted_a, capability_a)
        admitted_ab = self.admit({"a", "b"})
        frontier = ib.InvocationFrontier(host_generation="host-g1", durable=False)

        with self.assertRaisesRegex(ValueError, "admitted-state"):
            frontier.reserve(
                generation_id="g1",
                admitted=admitted_ab,
                capability=capability_a,
                projection=projection_a,
                request_material_digest=ib.canonical_digest({"projection": projection_a.projection_material}),
                currentness_mode="ATOMIC_START_SNAPSHOT",
                revalidate=lambda: True,
                reserved_at="t3",
            )


if __name__ == "__main__":
    unittest.main()
