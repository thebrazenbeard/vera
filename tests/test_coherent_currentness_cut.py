from __future__ import annotations

from hashlib import sha256
import unittest

from runtime_cohesion.coherent_currentness_cut import (
    CoherentCurrentnessCut,
    CutDisposition,
    SurfaceReadback,
    SurfaceStatus,
    evaluate_currentness_cut,
)


def h(label: str) -> str:
    return sha256(label.encode("utf-8")).hexdigest()


def surface(
    surface_id: str,
    *,
    required: bool = True,
    status: SurfaceStatus = SurfaceStatus.COMPLETE,
    start: str = "A",
    end: str = "A",
) -> SurfaceReadback:
    return SurfaceReadback(
        surface_id=surface_id,
        required=required,
        status=status,
        start_frontier=start,
        end_frontier=end,
        readback_identity=f"readback:{surface_id}",
        result_digest=h(surface_id),
    )


class CoherentCurrentnessCutTests(unittest.TestCase):
    def make_cut(self, *surfaces: SurfaceReadback, retry_count: int = 0):
        return CoherentCurrentnessCut(
            cut_id="cut-1",
            live_input_digest=h("live-input"),
            restored_frontier_digest=h("restored"),
            retry_count=retry_count,
            surfaces=tuple(surfaces),
        )

    def assert_non_promoting(self, decision) -> None:
        self.assertTrue(decision.live_input_controls)
        self.assertFalse(decision.authority_granted)
        self.assertFalse(decision.identity_established)
        self.assertFalse(decision.effect_authorized)

    def test_all_required_surfaces_stable_is_current_only(self):
        decision = evaluate_currentness_cut(
            self.make_cut(
                surface("VCP_CONTROL_OWNER"),
                surface("BUS_TOPOLOGY"),
                surface("TARGET_FRONTIER"),
            )
        )
        self.assertEqual(CutDisposition.CURRENT, decision.disposition)
        self.assertEqual((), decision.affected_surfaces)
        self.assert_non_promoting(decision)

    def test_required_surface_movement_retries_once(self):
        decision = evaluate_currentness_cut(
            self.make_cut(
                surface("VCP_CONTROL_OWNER", start="A", end="B"),
                surface("BUS_TOPOLOGY"),
            )
        )
        self.assertEqual(
            CutDisposition.RETRY_AFFECTED_SURFACES,
            decision.disposition,
        )
        self.assertEqual(("VCP_CONTROL_OWNER",), decision.affected_surfaces)
        self.assert_non_promoting(decision)

    def test_second_required_surface_movement_is_unstable_unknown(self):
        decision = evaluate_currentness_cut(
            self.make_cut(
                surface("BUS_TOPOLOGY", start="B", end="C"),
                retry_count=1,
            )
        )
        self.assertEqual(CutDisposition.UNSTABLE_UNKNOWN, decision.disposition)
        self.assertEqual(("BUS_TOPOLOGY",), decision.affected_surfaces)
        self.assert_non_promoting(decision)

    def test_partial_required_surface_blocks_currentness(self):
        decision = evaluate_currentness_cut(
            self.make_cut(
                surface(
                    "PRIVATE_RELATIONAL_READBACK",
                    status=SurfaceStatus.PARTIAL,
                ),
                surface("VCP_CONTROL_OWNER"),
            )
        )
        self.assertEqual(
            CutDisposition.BLOCKED_REQUIRED_SURFACE,
            decision.disposition,
        )
        self.assertEqual(
            ("PRIVATE_RELATIONAL_READBACK",),
            decision.affected_surfaces,
        )
        self.assert_non_promoting(decision)

    def test_unavailable_required_surface_blocks_even_if_others_are_stable(self):
        decision = evaluate_currentness_cut(
            self.make_cut(
                surface("VCP_CONTROL_OWNER"),
                surface(
                    "PROVIDER_CURRENTNESS",
                    status=SurfaceStatus.UNAVAILABLE,
                ),
            )
        )
        self.assertEqual(
            CutDisposition.BLOCKED_REQUIRED_SURFACE,
            decision.disposition,
        )
        self.assert_non_promoting(decision)

    def test_optional_surface_movement_does_not_promote_or_block_required_cut(self):
        decision = evaluate_currentness_cut(
            self.make_cut(
                surface("VCP_CONTROL_OWNER"),
                surface(
                    "OPTIONAL_TELEMETRY",
                    required=False,
                    start="A",
                    end="B",
                ),
            )
        )
        self.assertEqual(CutDisposition.CURRENT, decision.disposition)
        self.assert_non_promoting(decision)

    def test_optional_complete_surface_cannot_rescue_missing_required_surface(self):
        decision = evaluate_currentness_cut(
            self.make_cut(
                surface(
                    "BUS_TOPOLOGY",
                    status=SurfaceStatus.UNAVAILABLE,
                ),
                surface("OPTIONAL_TELEMETRY", required=False),
            )
        )
        self.assertEqual(
            CutDisposition.BLOCKED_REQUIRED_SURFACE,
            decision.disposition,
        )
        self.assertEqual(("BUS_TOPOLOGY",), decision.affected_surfaces)
        self.assert_non_promoting(decision)

    def test_surface_ids_must_be_unique(self):
        with self.assertRaisesRegex(ValueError, "unique"):
            self.make_cut(surface("BUS_TOPOLOGY"), surface("BUS_TOPOLOGY"))

    def test_retry_count_is_bounded(self):
        with self.assertRaisesRegex(ValueError, "0 or 1"):
            self.make_cut(surface("BUS_TOPOLOGY"), retry_count=2)

    def test_digest_changes_when_required_frontier_changes(self):
        a = self.make_cut(surface("BUS_TOPOLOGY", start="A", end="A"))
        b = self.make_cut(surface("BUS_TOPOLOGY", start="A", end="B"))
        self.assertNotEqual(a.digest, b.digest)


if __name__ == "__main__":
    unittest.main()
