from __future__ import annotations

from hashlib import sha256
import unittest

from runtime_cohesion.coherent_currentness_cut import (
    CoherentCurrentnessCut,
    CurrentnessRequirementProfile,
    CutDisposition,
    SurfaceReadback,
    SurfaceStatus,
    evaluate_currentness_cut,
)


def h(label: str) -> str:
    return sha256(label.encode("utf-8")).hexdigest()


def profile(
    *,
    required: tuple[str, ...] = ("BUS_TOPOLOGY",),
    optional: tuple[str, ...] = (),
    scope: str = "scope",
) -> CurrentnessRequirementProfile:
    return CurrentnessRequirementProfile(
        profile_id="profile-1",
        proposition_type="RECOVERY_CURRENTNESS",
        scope_digest=h(scope),
        requirements_source_id="VCP_CURRENT_OWNER",
        requirements_source_digest=h("requirements-source"),
        required_surfaces=required,
        optional_surfaces=optional,
    )


def surface(
    surface_id: str,
    *,
    status: SurfaceStatus = SurfaceStatus.COMPLETE,
    start: str = "A",
    end: str = "A",
) -> SurfaceReadback:
    return SurfaceReadback(
        surface_id=surface_id,
        status=status,
        start_frontier=start,
        end_frontier=end,
        readback_identity=f"readback:{surface_id}",
        result_digest=h(surface_id),
    )


class CoherentCurrentnessCutTests(unittest.TestCase):
    def make_cut(
        self,
        *surfaces: SurfaceReadback,
        requirement_profile: CurrentnessRequirementProfile | None = None,
        retry_count: int = 0,
        predecessor_cut_digest: str | None = None,
        live_input_scope_digest: str | None = None,
    ) -> CoherentCurrentnessCut:
        selected = requirement_profile or profile(
            required=tuple(sorted(item.surface_id for item in surfaces))
        )
        return CoherentCurrentnessCut(
            cut_id="cut-1",
            requirement_profile=selected,
            live_input_digest=h("live-input"),
            live_input_scope_digest=(
                selected.scope_digest
                if live_input_scope_digest is None
                else live_input_scope_digest
            ),
            restored_frontier_digest=h("restored"),
            retry_count=retry_count,
            predecessor_cut_digest=predecessor_cut_digest,
            surfaces=tuple(sorted(surfaces, key=lambda item: item.surface_id)),
        )

    def assert_non_promoting(self, decision) -> None:
        self.assertTrue(decision.live_input_controls)
        self.assertFalse(decision.authority_granted)
        self.assertFalse(decision.identity_established)
        self.assertFalse(decision.effect_authorized)

    def test_all_profile_required_surfaces_stable_is_current_only(self):
        requirement_profile = profile(
            required=("BUS_TOPOLOGY", "TARGET_FRONTIER", "VCP_CONTROL_OWNER")
        )
        decision = evaluate_currentness_cut(
            self.make_cut(
                surface("BUS_TOPOLOGY"),
                surface("TARGET_FRONTIER"),
                surface("VCP_CONTROL_OWNER"),
                requirement_profile=requirement_profile,
            )
        )
        self.assertEqual(CutDisposition.CURRENT, decision.disposition)
        self.assertEqual((), decision.affected_surfaces)
        self.assertEqual(
            requirement_profile.digest,
            decision.requirement_profile_digest,
        )
        self.assert_non_promoting(decision)

    def test_required_surface_movement_retries_once(self):
        requirement_profile = profile(
            required=("BUS_TOPOLOGY", "VCP_CONTROL_OWNER")
        )
        decision = evaluate_currentness_cut(
            self.make_cut(
                surface("BUS_TOPOLOGY"),
                surface("VCP_CONTROL_OWNER", start="A", end="B"),
                requirement_profile=requirement_profile,
            )
        )
        self.assertEqual(
            CutDisposition.RETRY_AFFECTED_SURFACES,
            decision.disposition,
        )
        self.assertEqual(("VCP_CONTROL_OWNER",), decision.affected_surfaces)
        self.assert_non_promoting(decision)

    def test_second_required_surface_movement_is_unstable_unknown(self):
        requirement_profile = profile(required=("BUS_TOPOLOGY",))
        decision = evaluate_currentness_cut(
            self.make_cut(
                surface("BUS_TOPOLOGY", start="B", end="C"),
                requirement_profile=requirement_profile,
                retry_count=1,
                predecessor_cut_digest=h("first-cut"),
            )
        )
        self.assertEqual(CutDisposition.UNSTABLE_UNKNOWN, decision.disposition)
        self.assertEqual(("BUS_TOPOLOGY",), decision.affected_surfaces)
        self.assert_non_promoting(decision)

    def test_partial_required_surface_blocks_currentness(self):
        requirement_profile = profile(
            required=("PRIVATE_RELATIONAL_READBACK", "VCP_CONTROL_OWNER")
        )
        decision = evaluate_currentness_cut(
            self.make_cut(
                surface(
                    "PRIVATE_RELATIONAL_READBACK",
                    status=SurfaceStatus.PARTIAL,
                ),
                surface("VCP_CONTROL_OWNER"),
                requirement_profile=requirement_profile,
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

    def test_optional_unavailable_surface_does_not_block_required_cut(self):
        requirement_profile = profile(
            required=("VCP_CONTROL_OWNER",),
            optional=("OPTIONAL_TELEMETRY",),
        )
        decision = evaluate_currentness_cut(
            self.make_cut(
                surface(
                    "OPTIONAL_TELEMETRY",
                    status=SurfaceStatus.UNAVAILABLE,
                ),
                surface("VCP_CONTROL_OWNER"),
                requirement_profile=requirement_profile,
            )
        )
        self.assertEqual(CutDisposition.CURRENT, decision.disposition)
        self.assert_non_promoting(decision)

    def test_readback_cannot_self_assert_requiredness(self):
        with self.assertRaises(TypeError):
            SurfaceReadback(
                surface_id="BUS_TOPOLOGY",
                required=False,  # type: ignore[call-arg]
                status=SurfaceStatus.COMPLETE,
                start_frontier="A",
                end_frontier="A",
                readback_identity="readback:BUS_TOPOLOGY",
                result_digest=h("BUS_TOPOLOGY"),
            )

    def test_missing_profile_required_surface_is_rejected(self):
        requirement_profile = profile(
            required=("BUS_TOPOLOGY", "VCP_CONTROL_OWNER")
        )
        with self.assertRaisesRegex(ValueError, "exactly match"):
            self.make_cut(
                surface("BUS_TOPOLOGY"),
                requirement_profile=requirement_profile,
            )

    def test_undeclared_extra_surface_is_rejected(self):
        requirement_profile = profile(required=("BUS_TOPOLOGY",))
        with self.assertRaisesRegex(ValueError, "exactly match"):
            self.make_cut(
                surface("BUS_TOPOLOGY"),
                surface("UNDECLARED"),
                requirement_profile=requirement_profile,
            )

    def test_renamed_required_surface_cannot_satisfy_profile(self):
        requirement_profile = profile(required=("BUS_TOPOLOGY",))
        with self.assertRaisesRegex(
            ValueError,
            "missing=.*BUS_TOPOLOGY.*extra=.*BUS_TOPOLOGY_ALIAS",
        ):
            self.make_cut(
                surface("BUS_TOPOLOGY_ALIAS"),
                requirement_profile=requirement_profile,
            )

    def test_required_optional_overlap_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "must not overlap"):
            profile(
                required=("BUS_TOPOLOGY",),
                optional=("BUS_TOPOLOGY",),
            )

    def test_profile_surface_inventory_must_be_canonical(self):
        with self.assertRaisesRegex(ValueError, "canonical"):
            profile(required=("VCP_CONTROL_OWNER", "BUS_TOPOLOGY"))

    def test_moving_surface_from_required_to_optional_moves_profile_digest(self):
        strict = profile(
            required=("BUS_TOPOLOGY", "VCP_CONTROL_OWNER"),
            optional=(),
        )
        weakened = profile(
            required=("BUS_TOPOLOGY",),
            optional=("VCP_CONTROL_OWNER",),
        )
        self.assertNotEqual(strict.digest, weakened.digest)

    def test_live_input_scope_must_match_profile_scope(self):
        requirement_profile = profile(required=("BUS_TOPOLOGY",))
        with self.assertRaisesRegex(ValueError, "must match requirement profile scope"):
            self.make_cut(
                surface("BUS_TOPOLOGY"),
                requirement_profile=requirement_profile,
                live_input_scope_digest=h("different-scope"),
            )

    def test_retry_cut_requires_predecessor_digest(self):
        requirement_profile = profile(required=("BUS_TOPOLOGY",))
        with self.assertRaisesRegex(ValueError, "requires predecessor_cut_digest"):
            self.make_cut(
                surface("BUS_TOPOLOGY"),
                requirement_profile=requirement_profile,
                retry_count=1,
            )

    def test_initial_cut_cannot_claim_predecessor_digest(self):
        requirement_profile = profile(required=("BUS_TOPOLOGY",))
        with self.assertRaisesRegex(ValueError, "cannot claim predecessor"):
            self.make_cut(
                surface("BUS_TOPOLOGY"),
                requirement_profile=requirement_profile,
                predecessor_cut_digest=h("not-allowed"),
            )

    def test_duplicate_readbacks_are_rejected(self):
        requirement_profile = profile(required=("BUS_TOPOLOGY",))
        with self.assertRaisesRegex(ValueError, "canonical, sorted, and unique"):
            CoherentCurrentnessCut(
                cut_id="cut-duplicate",
                requirement_profile=requirement_profile,
                live_input_digest=h("live-input"),
                live_input_scope_digest=requirement_profile.scope_digest,
                restored_frontier_digest=None,
                retry_count=0,
                predecessor_cut_digest=None,
                surfaces=(
                    surface("BUS_TOPOLOGY"),
                    surface("BUS_TOPOLOGY"),
                ),
            )

    def test_profile_source_binding_changes_profile_digest(self):
        first = profile(required=("BUS_TOPOLOGY",))
        second = CurrentnessRequirementProfile(
            profile_id=first.profile_id,
            proposition_type=first.proposition_type,
            scope_digest=first.scope_digest,
            requirements_source_id=first.requirements_source_id,
            requirements_source_digest=h("other-requirements-source"),
            required_surfaces=first.required_surfaces,
            optional_surfaces=first.optional_surfaces,
        )
        self.assertNotEqual(first.digest, second.digest)


if __name__ == "__main__":
    unittest.main()
