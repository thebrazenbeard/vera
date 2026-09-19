import unittest

from runtime_cohesion.hostile_reviewer import (
    AUTHORITY_CEILING,
    DEFAULT_ATTACK_DIMENSIONS,
    HostileReviewerConfig,
    build_hostile_review_request,
    render_hostile_review_block,
    review_response,
)


class HostileReviewerFeatureTests(unittest.TestCase):
    def test_off_is_noop(self):
        config = HostileReviewerConfig(mode="OFF")
        request = build_hostile_review_request(
            config,
            user_request="Choose an architecture.",
            primary_answer="Use the smaller design.",
        )
        self.assertIsNone(request)

    def test_on_binds_exact_primary_answer(self):
        config = HostileReviewerConfig(mode="ON", max_objections=3)
        request = build_hostile_review_request(
            config,
            user_request="Choose an architecture.",
            primary_answer="Use the smaller design.",
        )
        self.assertIsNotNone(request)
        self.assertEqual(
            "39f4a7282811cbb451876b8a06073ec7ccc2ea8d48d693364539437002794fbd",
            request.subject_sha256,
        )
        self.assertEqual(3, request.max_objections)
        self.assertEqual(DEFAULT_ATTACK_DIMENSIONS, request.attack_dimensions)
        self.assertEqual(AUTHORITY_CEILING, request.authority_ceiling)

    def test_non_substantive_turn_does_not_run(self):
        request = build_hostile_review_request(
            HostileReviewerConfig(mode="ON"),
            user_request="Thanks",
            primary_answer="You're welcome.",
            substantive=False,
        )
        self.assertIsNone(request)

    def test_invalid_mode_fails_closed(self):
        with self.assertRaises(ValueError):
            HostileReviewerConfig(mode="AUTO")

    def test_instruction_preserves_authority_and_private_reasoning_boundaries(self):
        request = build_hostile_review_request(
            HostileReviewerConfig(mode="ON"),
            user_request="Should this be shared infrastructure?",
            primary_answer="Yes, extract it.",
        )
        text = request.reviewer_instruction.lower()
        self.assertIn("do not reveal private chain-of-thought", text)
        self.assertIn("grant authority", text)
        self.assertIn("alter tool effects", text)
        self.assertIn("promote source to runtime truth", text)

    def test_visible_blockquote_format(self):
        rendered = render_hostile_review_block(
            "The abstraction is premature.\nA second consumer has not been proven."
        )
        self.assertEqual(
            "> **HOSTILE REVIEWER:** The abstraction is premature.\n"
            "> A second consumer has not been proven.",
            rendered,
        )


    def test_pipeline_off_does_not_invoke_reviewer(self):
        calls = []
        result = review_response(
            HostileReviewerConfig(mode="OFF"),
            user_request="Choose an architecture.",
            primary_answer="Use the smaller design.",
            reviewer=lambda request: calls.append(request) or "should not run",
        )
        self.assertEqual([], calls)
        self.assertEqual("Use the smaller design.", result.primary_answer)
        self.assertIsNone(result.rendered_block)

    def test_pipeline_on_invokes_exact_bound_reviewer_once(self):
        seen = []
        def reviewer(request):
            seen.append(request)
            return "The abstraction may be premature."

        result = review_response(
            HostileReviewerConfig(mode="ON"),
            user_request="Choose an architecture.",
            primary_answer="Use the smaller design.",
            reviewer=reviewer,
        )
        self.assertEqual(1, len(seen))
        self.assertEqual(seen[0].subject_sha256, result.subject_sha256)
        self.assertEqual(
            "> **HOSTILE REVIEWER:** The abstraction may be premature.",
            result.rendered_block,
        )

    def test_package_exports_runtime_pipeline(self):
        import runtime_cohesion
        self.assertIs(runtime_cohesion.review_response, review_response)


if __name__ == "__main__":
    unittest.main()
