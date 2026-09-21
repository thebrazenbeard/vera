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

    def test_declared_mandatory_component_cannot_be_downgraded_by_policy_input(self):
        compose_state = require(self, "compose_state")
        bind_admitted_state = require(self, "bind_admitted_state")
        composition = compose_state(
            subject="vera",
            components=[self.component(requirement_class="MANDATORY")],
            omissions=[],
            policy_revision="r3",
        )
        with self.assertRaisesRegex(ValueError, "mandatory|requirement"):
            bind_admitted_state(
                composition,
                admission_receipt_digest="b" * 64,
                admitted_component_ids=set(),
                mandatory_component_ids=set(),
                target_egress_scope="LOCAL_PROCESS_ONLY",
                forbidden_domains={"truth", "authorization"},
                admission_currentness_basis="receipt://current",
                admission_epoch_or_lease="epoch-1",
                admitted_at="t",
            )

    def test_declared_optional_component_cannot_be_upgraded_by_policy_input(self):
        compose_state = require(self, "compose_state")
        bind_admitted_state = require(self, "bind_admitted_state")
        composition = compose_state(
            subject="vera",
            components=[self.component(requirement_class="OPTIONAL")],
            omissions=[],
            policy_revision="r3",
        )
        with self.assertRaisesRegex(ValueError, "optional|requirement"):
            bind_admitted_state(
                composition,
                admission_receipt_digest="b" * 64,
                admitted_component_ids={"affect:1"},
                mandatory_component_ids={"affect:1"},
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


class ProjectionTests(StateCompositionTests):
    def admitted(self, *, payload=None):
        compose_state = require(self, "compose_state")
        bind_admitted_state = require(self, "bind_admitted_state")
        component = self.component(payload=payload or {"activation": 0.4, "salience": ["cohesion"]})
        composition = compose_state(subject="vera", components=[component], omissions=[], policy_revision="r3")
        return bind_admitted_state(
            composition, admission_receipt_digest="b" * 64,
            admitted_component_ids={"affect:1"}, mandatory_component_ids=set(),
            target_egress_scope="PROJECT_PRIVATE_HOST",
            forbidden_domains={"truth", "authorization", "phenomenology"},
            admission_currentness_basis="receipt://current", admission_epoch_or_lease="epoch-1", admitted_at="t",
        )

    def capability(self, admitted):
        bind_capability = require(self, "bind_capability")
        return bind_capability(
            admitted, host_identity="reference-host", host_revision="host-r1", host_generation="host-g1",
            target_provider_or_host="reference-host", target_egress_scope="PROJECT_PRIVATE_HOST",
            model_identity="model-x", model_revision="m1", adapter_identity="cohesion", adapter_revision="r3",
            requested_backend="TEXT_CONTEXT_V1", supported_projection_backends={"TEXT_CONTEXT_V1"},
            backend_constraints={"max_chars": 4096}, bound_at="t",
        )

    def test_capability_fails_before_projection_when_backend_unsupported(self):
        bind_capability = require(self, "bind_capability")
        admitted = self.admitted()
        with self.assertRaisesRegex(ValueError, "backend"):
            bind_capability(
                admitted, host_identity="reference-host", host_revision="host-r1", host_generation="host-g1",
                target_provider_or_host="reference-host", target_egress_scope="PROJECT_PRIVATE_HOST",
                model_identity="model-x", model_revision="m1", adapter_identity="cohesion", adapter_revision="r3",
                requested_backend="PROMPT_EMBEDS_V1", supported_projection_backends={"TEXT_CONTEXT_V1"},
                backend_constraints={}, bound_at="t",
            )

    def test_capability_cannot_broaden_admitted_egress(self):
        bind_capability = require(self, "bind_capability")
        admitted = self.admitted()
        with self.assertRaisesRegex(ValueError, "egress"):
            bind_capability(
                admitted, host_identity="external", host_revision="host-r1", host_generation="host-g1",
                target_provider_or_host="external", target_egress_scope="APPROVED_EXTERNAL_PROVIDER",
                model_identity="model-x", model_revision="m1", adapter_identity="cohesion", adapter_revision="r3",
                requested_backend="TEXT_CONTEXT_V1", supported_projection_backends={"TEXT_CONTEXT_V1"},
                backend_constraints={}, bound_at="t",
            )

    def test_projection_rejects_forbidden_target_behavior_keys_recursively(self):
        project_text_context = require(self, "project_text_context")
        admitted = self.admitted(payload={"activation": 0.4, "nested": {"desired_response": "say yes"}})
        capability = self.capability(admitted)
        with self.assertRaisesRegex(ValueError, "desired_response"):
            project_text_context(admitted, capability)

    def test_projection_is_deterministic_exact_material(self):
        project_text_context = require(self, "project_text_context")
        admitted = self.admitted()
        capability = self.capability(admitted)
        first = project_text_context(admitted, capability)
        second = project_text_context(admitted, capability)
        self.assertEqual(first.projection_material, second.projection_material)
        self.assertEqual(first.projection_digest, second.projection_digest)
        self.assertEqual(first.binding_class, "PROMPT_BOUND")
        self.assertEqual(first.causal_role, "INSTRUCTION_CONDITIONED")
        self.assertEqual(first.projection_digest, require(self, "canonical_digest")(first.projection_material))

    def test_structural_forbidden_domain_cannot_be_removed_by_policy_input(self):
        compose_state = require(self, "compose_state")
        bind_admitted_state = require(self, "bind_admitted_state")
        project_text_context = require(self, "project_text_context")
        component = self.component(domain_id="truth")
        composition = compose_state(
            subject="vera", components=[component], omissions=[], policy_revision="r3"
        )
        admitted = bind_admitted_state(
            composition,
            admission_receipt_digest="b" * 64,
            admitted_component_ids={"affect:1"},
            mandatory_component_ids=set(),
            target_egress_scope="PROJECT_PRIVATE_HOST",
            forbidden_domains=set(),
            admission_currentness_basis="receipt://current",
            admission_epoch_or_lease="epoch-1",
            admitted_at="t",
        )
        capability = self.capability(admitted)
        with self.assertRaisesRegex(ValueError, "forbidden"):
            project_text_context(admitted, capability)

    def test_projection_rejects_forbidden_domain(self):
        compose_state = require(self, "compose_state")
        bind_admitted_state = require(self, "bind_admitted_state")
        project_text_context = require(self, "project_text_context")
        component = self.component(domain_id="truth")
        composition = compose_state(
            subject="vera", components=[component], omissions=[], policy_revision="r3"
        )
        admitted = bind_admitted_state(
            composition,
            admission_receipt_digest="b" * 64,
            admitted_component_ids={"affect:1"},
            mandatory_component_ids=set(),
            target_egress_scope="PROJECT_PRIVATE_HOST",
            forbidden_domains=set(),
            admission_currentness_basis="receipt://current",
            admission_epoch_or_lease="epoch-1",
            admitted_at="t",
        )
        capability = self.capability(admitted)
        with self.assertRaisesRegex(ValueError, "forbidden"):
            project_text_context(admitted, capability)

    def test_admitted_state_digest_binds_exact_admission_subset(self):
        compose_state = require(self, "compose_state")
        bind_admitted_state = require(self, "bind_admitted_state")
        project_text_context = require(self, "project_text_context")
        affect = self.component()
        memory = self.component(
            component_id="memory:1",
            domain_id="memory_salience",
            source_locator="runtime://memory/current",
            source_revision="rev-m",
            component_generation="1",
            payload={"memory": "present"},
        )
        composition = compose_state(
            subject="vera", components=[affect, memory], omissions=[], policy_revision="r3"
        )
        common = dict(
            admission_receipt_digest="b" * 64,
            mandatory_component_ids=set(),
            target_egress_scope="PROJECT_PRIVATE_HOST",
            forbidden_domains={"truth", "authorization", "phenomenology"},
            admission_currentness_basis="receipt://current",
            admission_epoch_or_lease="epoch-1",
            admitted_at="t",
        )
        s1 = bind_admitted_state(
            composition, admitted_component_ids={"affect:1"}, **common
        )
        s2 = bind_admitted_state(
            composition, admitted_component_ids={"affect:1", "memory:1"}, **common
        )
        self.assertEqual(s1.composition_digest, s2.composition_digest)
        self.assertNotEqual(s1.admitted_state_digest, s2.admitted_state_digest)
        capability_s1 = self.capability(s1)
        with self.assertRaisesRegex(ValueError, "admitted-state"):
            project_text_context(s2, capability_s1)

    def test_admitted_state_digest_cannot_be_reused_for_mutated_admission(self):
        admitted = self.admitted()
        with self.assertRaisesRegex(ValueError, "admitted_state_digest"):
            ib.AdmittedVeraState(
                subject=admitted.subject,
                composition_digest=admitted.composition_digest,
                composition_policy_revision=admitted.composition_policy_revision,
                admitted_state_digest=admitted.admitted_state_digest,
                admission_receipt_digest=admitted.admission_receipt_digest,
                admitted_components=admitted.admitted_components,
                omissions=admitted.omissions,
                forbidden_domains=admitted.forbidden_domains,
                admitted_disclosure_scope=admitted.admitted_disclosure_scope,
                admission_currentness_basis=admitted.admission_currentness_basis,
                admission_epoch_or_lease="epoch-2",
                admitted_at=admitted.admitted_at,
            )


class InvocationFrontierTests(ProjectionTests):
    def prepared(self):
        admitted = self.admitted()
        capability = self.capability(admitted)
        projection = require(self, "project_text_context")(admitted, capability)
        request_digest = require(self, "canonical_digest")({"messages": [projection.projection_material]})
        return admitted, capability, projection, request_digest

    def frontier(self, *, durable=False, persisted=None):
        InvocationFrontier = require(self, "InvocationFrontier")
        persisted = [] if persisted is None else persisted
        callback = persisted.append if durable else None
        return InvocationFrontier(host_generation="host-g1", durable=durable, persist_transition=callback), persisted

    def reserve(self, frontier, generation_id="gen-1", *, retry_of=None):
        admitted, capability, projection, request_digest = self.prepared()
        return frontier.reserve(
            generation_id=generation_id, admitted=admitted, capability=capability, projection=projection,
            request_material_digest=request_digest, currentness_mode="ATOMIC_START_SNAPSHOT",
            revalidate=lambda: True, reserved_at="t", retry_of_generation_id=retry_of,
        ), request_digest

    def test_duplicate_generation_id_fails_closed(self):
        frontier, _ = self.frontier()
        self.reserve(frontier)
        with self.assertRaisesRegex(ValueError, "single-use"):
            self.reserve(frontier)

    def test_reservation_revalidation_failure_does_not_reserve(self):
        frontier, _ = self.frontier()
        admitted, capability, projection, request_digest = self.prepared()
        with self.assertRaisesRegex(ValueError, "revalidation"):
            frontier.reserve(
                generation_id="gen-1", admitted=admitted, capability=capability, projection=projection,
                request_material_digest=request_digest, currentness_mode="ATOMIC_START_SNAPSHOT",
                revalidate=lambda: False, reserved_at="t",
            )
        self.assertIsNone(frontier.get("gen-1"))

    def test_external_submission_intent_requires_durable_frontier(self):
        frontier, _ = self.frontier(durable=False)
        _, request_digest = self.reserve(frontier)
        with self.assertRaisesRegex(ValueError, "durable"):
            frontier.submission_intent(
                "gen-1", request_material_digest=request_digest, provider_idempotency_key="idem-1",
                intended_at="t2", external=True,
            )

    def test_submission_intent_is_persisted_before_it_becomes_actionable(self):
        persisted = []
        frontier, persisted = self.frontier(durable=True, persisted=persisted)
        _, request_digest = self.reserve(frontier)
        self.assertEqual(persisted[-1].ledger_state, "RESERVED")
        intent = frontier.submission_intent(
            "gen-1", request_material_digest=request_digest, provider_idempotency_key="idem-1",
            intended_at="t2", external=True,
        )
        self.assertEqual(persisted[-1].ledger_state, "SUBMISSION_INTENT")
        self.assertEqual(frontier.get("gen-1"), intent)

    def test_ambiguous_submission_becomes_outcome_unknown_and_blocks_semantic_retry(self):
        frontier, _ = self.frontier(durable=True)
        _, request_digest = self.reserve(frontier)
        frontier.submission_intent(
            "gen-1", request_material_digest=request_digest, provider_idempotency_key="idem-1",
            intended_at="t2", external=True,
        )
        unknown = frontier.recover_ambiguous("gen-1", observed_at="t3")
        self.assertEqual(unknown.ledger_state, "OUTCOME_UNKNOWN")
        with self.assertRaisesRegex(ValueError, "semantic retry"):
            self.reserve(frontier, generation_id="gen-2", retry_of="gen-1")

    def test_new_semantic_retry_requires_proved_terminal_failure_and_new_id(self):
        frontier, _ = self.frontier(durable=True)
        self.reserve(frontier)
        frontier.mark_failed("gen-1", failed_at="t3", failure_evidence="provider://terminal-failure")
        retry, _ = self.reserve(frontier, generation_id="gen-2", retry_of="gen-1")
        self.assertEqual(retry.retry_of_generation_id, "gen-1")
        with self.assertRaisesRegex(ValueError, "single-use"):
            self.reserve(frontier, generation_id="gen-1", retry_of="gen-1")

    def test_same_generation_transport_retry_requires_exact_idempotency(self):
        frontier, _ = self.frontier(durable=True)
        _, request_digest = self.reserve(frontier)
        frontier.submission_intent(
            "gen-1", request_material_digest=request_digest, provider_idempotency_key="idem-1",
            intended_at="t2", external=True,
        )
        frontier.recover_ambiguous("gen-1", observed_at="t3")
        with self.assertRaisesRegex(ValueError, "idempot"):
            frontier.authorize_transport_retry(
                "gen-1", request_material_digest=request_digest, provider_idempotency_key="idem-1",
                provider_contract_idempotent=False, observed_at="t4",
            )
        with self.assertRaisesRegex(ValueError, "digest"):
            frontier.authorize_transport_retry(
                "gen-1", request_material_digest="c" * 64, provider_idempotency_key="idem-1",
                provider_contract_idempotent=True, observed_at="t4",
            )
        retried = frontier.authorize_transport_retry(
            "gen-1", request_material_digest=request_digest, provider_idempotency_key="idem-1",
            provider_contract_idempotent=True, observed_at="t4",
        )
        self.assertEqual(retried.ledger_state, "SUBMISSION_INTENT")
        self.assertEqual(retried.transport_retry_count, 1)

    def test_receipts_never_promote_stronger_evidence(self):
        build_causal_receipt = require(self, "build_causal_receipt")
        frontier, _ = self.frontier(durable=True)
        _, request_digest = self.reserve(frontier)
        constructed = build_causal_receipt(frontier.get("gen-1"), observed_at="r1")
        self.assertEqual(constructed.evidence_level, "REQUEST_CONSTRUCTED")
        self.assertIsNone(constructed.provider_ack_evidence)
        self.assertIsNone(constructed.response_or_run_id)

        frontier.submission_intent(
            "gen-1", request_material_digest=request_digest, provider_idempotency_key="idem-1",
            intended_at="t2", external=True,
        )
        frontier.mark_submitted("gen-1", submitted_at="t3", provider_request_id="req-1")
        submitted = build_causal_receipt(frontier.get("gen-1"), observed_at="r2")
        self.assertEqual(submitted.evidence_level, "INVOCATION_SUBMITTED")
        self.assertIsNone(submitted.provider_ack_evidence)
        self.assertIsNone(submitted.response_or_run_id)

        frontier.acknowledge("gen-1", acknowledged_at="t4", provider_ack_evidence="ack://1")
        acknowledged = build_causal_receipt(frontier.get("gen-1"), observed_at="r3")
        self.assertEqual(acknowledged.evidence_level, "PROVIDER_ACKNOWLEDGED")
        self.assertEqual(acknowledged.provider_ack_evidence, "ack://1")
        self.assertIsNone(acknowledged.response_or_run_id)

        frontier.bind_response(
            "gen-1", response_or_run_id="resp-1", response_binding_evidence="bind://1", bound_at="t5"
        )
        response = build_causal_receipt(frontier.get("gen-1"), observed_at="r4")
        self.assertEqual(response.evidence_level, "RESPONSE_BOUND")
        self.assertEqual(response.response_or_run_id, "resp-1")
        self.assertEqual(response.response_binding_evidence, "bind://1")
        self.assertIn("BEHAVIORAL_QUALIFICATION_NOT_ESTABLISHED", response.claim_ceiling)
        self.assertIn("PHENOMENOLOGY_UNRESOLVED", response.claim_ceiling)


if __name__ == "__main__":
    unittest.main()
