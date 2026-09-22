import unittest

from runtime_cohesion.hostile_reviewer import (
    AUTHORITY_CEILING,
    DEFAULT_ATTACK_DIMENSIONS,
    HostileReviewDecision,
    HostileReviewerConfig,
    LiteralProposition,
    build_hostile_review_request,
    render_hostile_review_block,
    review_response,
)


def proposition(**overrides):
    values = {
        "literal_proposition": "Use the smaller design.",
        "proposition_type": "ARCHITECTURE_RECOMMENDATION",
        "referent": "candidate architecture A",
        "scope": "current source-only decision",
        "success_criteria": ("meets the stated requirements",),
        "known_evidence": ("candidate A has the smaller dependency surface",),
        "protected_assumptions": (),
    }
    values.update(overrides)
    return LiteralProposition(**values)


def surviving_decision(request, **overrides):
    values = {
        "subject_sha256": request.subject_sha256,
        "proposition_sha256": request.proposition_sha256,
        "literal_verdict": "LITERAL_SURVIVES",
        "surviving_claim": request.proposition.literal_proposition,
        "confidence": "HIGH",
    }
    values.update(overrides)
    return HostileReviewDecision(**values)


class HostileReviewerFeatureTests(unittest.TestCase):
    def test_off_is_noop(self):
        config = HostileReviewerConfig(mode="OFF")
        request = build_hostile_review_request(
            config,
            proposition=proposition(),
            primary_answer="Use the smaller design.",
        )
        self.assertIsNone(request)

    def test_on_binds_exact_primary_answer_and_typed_proposition(self):
        config = HostileReviewerConfig(mode="ON", max_objections=3)
        literal = proposition()
        request = build_hostile_review_request(
            config,
            proposition=literal,
            primary_answer="Use the smaller design.",
        )
        self.assertIsNotNone(request)
        self.assertEqual(
            "39f4a7282811cbb451876b8a06073ec7ccc2ea8d48d693364539437002794fbd",
            request.subject_sha256,
        )
        self.assertEqual(literal.digest, request.proposition_sha256)
        self.assertEqual(literal, request.proposition)
        self.assertEqual(3, request.max_objections)
        self.assertEqual(DEFAULT_ATTACK_DIMENSIONS, request.attack_dimensions)
        self.assertEqual(AUTHORITY_CEILING, request.authority_ceiling)

    def test_proposition_digest_changes_when_literal_semantics_change(self):
        base = proposition()
        changed_referent = proposition(referent="candidate architecture B")
        changed_type = proposition(proposition_type="USER_PREFERENCE")
        changed_scope = proposition(scope="all future architectures")
        self.assertNotEqual(base.digest, changed_referent.digest)
        self.assertNotEqual(base.digest, changed_type.digest)
        self.assertNotEqual(base.digest, changed_scope.digest)

    def test_non_substantive_turn_does_not_run(self):
        request = build_hostile_review_request(
            HostileReviewerConfig(mode="ON"),
            proposition=proposition(literal_proposition="Thanks"),
            primary_answer="You're welcome.",
            substantive=False,
        )
        self.assertIsNone(request)

    def test_invalid_mode_fails_closed(self):
        with self.assertRaises(ValueError):
            HostileReviewerConfig(mode="AUTO")

    def test_instruction_rejects_performative_opposition_and_preserves_boundaries(self):
        request = build_hostile_review_request(
            HostileReviewerConfig(mode="ON"),
            proposition=proposition(),
            primary_answer="Use the smaller design.",
        )
        text = request.reviewer_instruction.lower()
        self.assertIn("do not manufacture an objection", text)
        self.assertIn("literal proposition", text)
        self.assertIn("stronger route only after literal failure", text)
        self.assertIn("do not reveal private chain-of-thought", text)
        self.assertIn("grant authority", text)
        self.assertIn("alter tool effects", text)
        self.assertIn("promote source to runtime truth", text)

    def test_pipeline_literal_survives_with_zero_objections(self):
        seen = []

        def reviewer(request):
            seen.append(request)
            return surviving_decision(request)

        result = review_response(
            HostileReviewerConfig(mode="ON"),
            proposition=proposition(),
            primary_answer="Use the smaller design.",
            reviewer=reviewer,
        )
        self.assertEqual(1, len(seen))
        self.assertEqual("LITERAL_SURVIVES", result.review.literal_verdict)
        self.assertEqual((), result.review.counterexamples)
        self.assertIn("Literal proposition survives hostile review.", result.rendered_block)

    def test_pipeline_literal_failure_is_typed_and_rendered(self):
        def reviewer(request):
            return HostileReviewDecision(
                subject_sha256=request.subject_sha256,
                proposition_sha256=request.proposition_sha256,
                literal_verdict="LITERAL_FAILS",
                counterexamples=("A required dependency is missing.",),
                surviving_claim="A smaller design remains possible.",
                inferred_objective="Minimize dependency surface.",
                stronger_route="Use candidate C with the required dependency.",
                confidence="HIGH",
            )

        result = review_response(
            HostileReviewerConfig(mode="ON"),
            proposition=proposition(),
            primary_answer="Use the smaller design.",
            reviewer=reviewer,
        )
        self.assertEqual("LITERAL_FAILS", result.review.literal_verdict)
        self.assertIn("Counterexample: A required dependency is missing.", result.rendered_block)
        self.assertIn("Stronger route: Use candidate C", result.rendered_block)

    def test_proposition_substitution_digest_is_rejected(self):
        def reviewer(request):
            return HostileReviewDecision(
                subject_sha256=request.subject_sha256,
                proposition_sha256="0" * 64,
                literal_verdict="LITERAL_SURVIVES",
                confidence="HIGH",
            )

        with self.assertRaisesRegex(ValueError, "proposition digest mismatch"):
            review_response(
                HostileReviewerConfig(mode="ON"),
                proposition=proposition(),
                primary_answer="Use the smaller design.",
                reviewer=reviewer,
            )

    def test_primary_answer_substitution_digest_is_rejected(self):
        def reviewer(request):
            return HostileReviewDecision(
                subject_sha256="0" * 64,
                proposition_sha256=request.proposition_sha256,
                literal_verdict="LITERAL_SURVIVES",
                confidence="HIGH",
            )

        with self.assertRaisesRegex(ValueError, "subject digest mismatch"):
            review_response(
                HostileReviewerConfig(mode="ON"),
                proposition=proposition(),
                primary_answer="Use the smaller design.",
                reviewer=reviewer,
            )

    def test_surviving_claim_cannot_promote_or_substitute_literal_proposition(self):
        def reviewer(request):
            return surviving_decision(
                request,
                surviving_claim="Use this design for every future architecture.",
            )

        with self.assertRaisesRegex(ValueError, "surviving literal claim"):
            review_response(
                HostileReviewerConfig(mode="ON"),
                proposition=proposition(),
                primary_answer="Use the smaller design.",
                reviewer=reviewer,
            )

    def test_stronger_route_requires_literal_failure_or_explicit_request(self):
        def reviewer(request):
            return surviving_decision(
                request,
                inferred_objective="Minimize dependency surface.",
                stronger_route="Use candidate C.",
            )

        with self.assertRaisesRegex(ValueError, "requires literal failure or explicit request"):
            review_response(
                HostileReviewerConfig(mode="ON"),
                proposition=proposition(),
                primary_answer="Use the smaller design.",
                reviewer=reviewer,
            )

    def test_explicit_stronger_route_request_allows_route_after_literal_survival(self):
        def reviewer(request):
            return surviving_decision(
                request,
                inferred_objective="Minimize dependency surface.",
                stronger_route="Candidate C is even smaller.",
            )

        result = review_response(
            HostileReviewerConfig(mode="ON"),
            proposition=proposition(),
            primary_answer="Use the smaller design.",
            reviewer=reviewer,
            stronger_route_requested=True,
        )
        self.assertEqual("Candidate C is even smaller.", result.review.stronger_route)

    def test_literal_failure_requires_failure_evidence(self):
        def reviewer(request):
            return HostileReviewDecision(
                subject_sha256=request.subject_sha256,
                proposition_sha256=request.proposition_sha256,
                literal_verdict="LITERAL_FAILS",
                alternative_explanations=("Another design also exists.",),
                confidence="LOW",
            )

        with self.assertRaisesRegex(ValueError, "requires a counterexample"):
            review_response(
                HostileReviewerConfig(mode="ON"),
                proposition=proposition(),
                primary_answer="Use the smaller design.",
                reviewer=reviewer,
            )

    def test_stronger_route_requires_inferred_objective(self):
        def reviewer(request):
            return HostileReviewDecision(
                subject_sha256=request.subject_sha256,
                proposition_sha256=request.proposition_sha256,
                literal_verdict="LITERAL_FAILS",
                counterexamples=("A required dependency is missing.",),
                stronger_route="Use candidate C.",
                confidence="HIGH",
            )

        with self.assertRaisesRegex(ValueError, "requires inferred_objective"):
            review_response(
                HostileReviewerConfig(mode="ON"),
                proposition=proposition(),
                primary_answer="Use the smaller design.",
                reviewer=reviewer,
            )

    def test_objection_budget_is_enforced(self):
        def reviewer(request):
            return HostileReviewDecision(
                subject_sha256=request.subject_sha256,
                proposition_sha256=request.proposition_sha256,
                literal_verdict="UNRESOLVED",
                counterexamples=("one", "two"),
                unsupported_assumptions=("three", "four"),
                scope_failures=("five",),
                confidence="LOW",
            )

        with self.assertRaisesRegex(ValueError, "objection budget"):
            review_response(
                HostileReviewerConfig(mode="ON", max_objections=4),
                proposition=proposition(),
                primary_answer="Use the smaller design.",
                reviewer=reviewer,
            )

    def test_pipeline_off_does_not_invoke_reviewer(self):
        calls = []
        result = review_response(
            HostileReviewerConfig(mode="OFF"),
            proposition=proposition(),
            primary_answer="Use the smaller design.",
            reviewer=lambda request: calls.append(request),
        )
        self.assertEqual([], calls)
        self.assertEqual("Use the smaller design.", result.primary_answer)
        self.assertIsNone(result.review)
        self.assertIsNone(result.rendered_block)

    def test_reviewer_must_return_typed_decision(self):
        with self.assertRaisesRegex(TypeError, "HostileReviewDecision"):
            review_response(
                HostileReviewerConfig(mode="ON"),
                proposition=proposition(),
                primary_answer="Use the smaller design.",
                reviewer=lambda request: "opaque critique",
            )

    def test_visible_blockquote_is_derived_from_typed_result(self):
        literal = proposition()
        request = build_hostile_review_request(
            HostileReviewerConfig(mode="ON"),
            proposition=literal,
            primary_answer="Use the smaller design.",
        )
        decision = HostileReviewDecision(
            subject_sha256=request.subject_sha256,
            proposition_sha256=request.proposition_sha256,
            literal_verdict="LITERAL_FAILS",
            unsupported_assumptions=("A second consumer exists.",),
            confidence="MEDIUM",
        )
        rendered = render_hostile_review_block(decision)
        self.assertIn("> **HOSTILE REVIEWER:** Literal proposition fails hostile review.", rendered)
        self.assertIn("> Unsupported assumption: A second consumer exists.", rendered)

    def test_package_exports_typed_runtime_pipeline(self):
        import runtime_cohesion

        self.assertIs(runtime_cohesion.review_response, review_response)
        self.assertIs(runtime_cohesion.LiteralProposition, LiteralProposition)
        self.assertIs(runtime_cohesion.HostileReviewDecision, HostileReviewDecision)


if __name__ == "__main__":
    unittest.main()
