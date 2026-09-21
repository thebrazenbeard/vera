from __future__ import annotations

from hashlib import sha256
import unittest

from runtime_cohesion.coherent_currentness_cut import (
    CoherentCurrentnessCut,
    CurrentnessRequirementProfile,
    CutDisposition,
    SurfaceReadback,
    SurfaceReadbackContract,
    SurfaceStatus,
    evaluate_currentness_cut,
)


def h(label: str) -> str:
    return sha256(label.encode("utf-8")).hexdigest()


def contract(
    surface_id: str,
    *,
    identity: str | None = None,
    seed: str = "v1",
) -> SurfaceReadbackContract:
    return SurfaceReadbackContract(
        surface_id=surface_id,
        readback_identity=identity or f"readback:{surface_id}",
        contract_id=f"contract:{surface_id}:{seed}",
        contract_digest=h(f"contract:{surface_id}:{seed}"),
    )


def profile(
    *,
    required: tuple[str, ...] = ("BUS_TOPOLOGY",),
    optional: tuple[str, ...] = (),
    scope: str = "scope",
    contract_seed: str = "v1",
) -> CurrentnessRequirementProfile:
    declared = tuple(sorted(required + optional))
    return CurrentnessRequirementProfile(
        profile_id="profile-1",
        proposition_type="RECOVERY_CURRENTNESS",
        scope_digest=h(scope),
        requirements_source_id="VCP_CURRENT_OWNER",
        requirements_source_digest=h("requirements-source"),
        required_surfaces=required,
        optional_surfaces=optional,
        readback_contracts=tuple(
            contract(surface_id, seed=contract_seed) for surface_id in declared
        ),
    )


def surface(
    surface_id: str,
    *,
    status: SurfaceStatus = SurfaceStatus.COMPLETE,
    start: str = "A",
    end: str = "A",
    identity: str | None = None,
    start_result: str | None = None,
    end_result: str | None = None,
) -> SurfaceReadback:
    start_digest = start_result or h(f"result:{surface_id}:{start}")
    end_digest = end_result or (
        start_digest if start == end else h(f"result:{surface_id}:{end}")
    )
    return SurfaceReadback(
        surface_id=surface_id,
        status=status,
        start_frontier=start,
        end_frontier=end,
        readback_identity=identity or f"readback:{surface_id}",
        start_result_digest=start_digest,
        end_result_digest=end_digest,
    )


class CoherentCurrentnessCutTests(unittest.TestCase):
    def make_cut(
        self,
        *surfaces: SurfaceReadback,
        requirement_profile: CurrentnessRequirementProfile | None = None,
        retry_count: int = 0,
        predecessor_cut: CoherentCurrentnessCut | None = None,
        live_input_scope_digest: str | None = None,
        cut_family_id: str = "family-1",
    ) -> CoherentCurrentnessCut:
        selected = requirement_profile or profile(
            required=tuple(sorted(item.surface_id for item in surfaces))
        )
        return CoherentCurrentnessCut(
            cut_id="cut-1" if retry_count == 0 else "cut-2",
            cut_family_id=cut_family_id,
            requirement_profile=selected,
            live_input_digest=h("live-input"),
            live_input_scope_digest=(
                selected.scope_digest
                if live_input_scope_digest is None
                else live_input_scope_digest
            ),
            restored_frontier_digest=h("restored"),
            retry_count=retry_count,
            predecessor_cut=predecessor_cut,
            surfaces=tuple(sorted(surfaces, key=lambda item: item.surface_id)),
        )

    def predecessor(
        self,
        requirement_profile: CurrentnessRequirementProfile,
        *,
        family: str = "family-1",
        scope: str | None = None,
        moved_surface: str = "BUS_TOPOLOGY",
        stable: bool = False,
    ) -> CoherentCurrentnessCut:
        selected = requirement_profile
        if scope is not None:
            selected = profile(
                required=requirement_profile.required_surfaces,
                optional=requirement_profile.optional_surfaces,
                scope=scope,
            )
        end = "A" if stable else "B"
        return self.make_cut(
            *(
                surface(
                    surface_id,
                    start="A",
                    end=(end if surface_id == moved_surface else "A"),
                )
                for surface_id in selected.declared_surface_ids
            ),
            requirement_profile=selected,
            retry_count=0,
            cut_family_id=family,
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
                predecessor_cut=self.predecessor(requirement_profile),
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
                start_result_digest=h("a"),
                end_result_digest=h("a"),
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

    def test_retry_cut_requires_actual_predecessor_cut(self):
        requirement_profile = profile(required=("BUS_TOPOLOGY",))
        with self.assertRaisesRegex(ValueError, "requires exact predecessor CoherentCurrentnessCut"):
            self.make_cut(
                surface("BUS_TOPOLOGY"),
                requirement_profile=requirement_profile,
                retry_count=1,
            )

    def test_initial_cut_cannot_claim_predecessor_cut(self):
        requirement_profile = profile(required=("BUS_TOPOLOGY",))
        with self.assertRaisesRegex(ValueError, "cannot claim predecessor_cut"):
            self.make_cut(
                surface("BUS_TOPOLOGY"),
                requirement_profile=requirement_profile,
                predecessor_cut=self.predecessor(requirement_profile),
            )

    def test_duplicate_readbacks_are_rejected(self):
        requirement_profile = profile(required=("BUS_TOPOLOGY",))
        with self.assertRaisesRegex(ValueError, "canonical, sorted, and unique"):
            CoherentCurrentnessCut(
                cut_id="cut-duplicate",
                cut_family_id="family-1",
                requirement_profile=requirement_profile,
                live_input_digest=h("live-input"),
                live_input_scope_digest=requirement_profile.scope_digest,
                restored_frontier_digest=None,
                retry_count=0,
                predecessor_cut=None,
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
            readback_contracts=first.readback_contracts,
        )
        self.assertNotEqual(first.digest, second.digest)


    def test_equal_frontier_with_result_movement_is_not_current(self):
        requirement_profile = profile(required=("BUS_TOPOLOGY",))
        decision = evaluate_currentness_cut(
            self.make_cut(
                surface(
                    "BUS_TOPOLOGY",
                    start="A",
                    end="A",
                    start_result=h("snapshot-a"),
                    end_result=h("snapshot-b"),
                ),
                requirement_profile=requirement_profile,
            )
        )
        self.assertEqual(
            CutDisposition.RETRY_AFFECTED_SURFACES,
            decision.disposition,
        )
        self.assertEqual(("BUS_TOPOLOGY",), decision.affected_surfaces)

    def test_mismatched_readback_identity_is_rejected(self):
        requirement_profile = profile(required=("BUS_TOPOLOGY",))
        with self.assertRaisesRegex(ValueError, "readback_identity"):
            self.make_cut(
                surface("BUS_TOPOLOGY", identity="readback:OTHER_PROVIDER"),
                requirement_profile=requirement_profile,
            )

    def test_readback_contract_movement_changes_profile_digest(self):
        first = profile(required=("BUS_TOPOLOGY",), contract_seed="v1")
        second = profile(required=("BUS_TOPOLOGY",), contract_seed="v2")
        self.assertNotEqual(first.digest, second.digest)

    def test_stable_typed_retry_can_be_current(self):
        requirement_profile = profile(required=("BUS_TOPOLOGY",))
        decision = evaluate_currentness_cut(
            self.make_cut(
                surface("BUS_TOPOLOGY", start="B", end="B"),
                requirement_profile=requirement_profile,
                retry_count=1,
                predecessor_cut=self.predecessor(requirement_profile),
            )
        )
        self.assertEqual(CutDisposition.CURRENT, decision.disposition)
        self.assert_non_promoting(decision)

    def test_retry_rejects_unrelated_cut_family(self):
        requirement_profile = profile(required=("BUS_TOPOLOGY",))
        with self.assertRaisesRegex(ValueError, "cut_family_id"):
            self.make_cut(
                surface("BUS_TOPOLOGY"),
                requirement_profile=requirement_profile,
                retry_count=1,
                predecessor_cut=self.predecessor(
                    requirement_profile, family="unrelated-family"
                ),
            )

    def test_retry_rejects_unrelated_profile_digest(self):
        requirement_profile = profile(required=("BUS_TOPOLOGY",))
        other_profile = profile(required=("BUS_TOPOLOGY",), contract_seed="other")
        with self.assertRaisesRegex(ValueError, "requirement_profile digest"):
            self.make_cut(
                surface("BUS_TOPOLOGY"),
                requirement_profile=requirement_profile,
                retry_count=1,
                predecessor_cut=self.predecessor(other_profile),
            )

    def test_retry_rejects_unrelated_scope(self):
        requirement_profile = profile(required=("BUS_TOPOLOGY",))
        other_profile = profile(required=("BUS_TOPOLOGY",), scope="other-scope")
        with self.assertRaisesRegex(ValueError, "requirement_profile digest|scope_digest"):
            self.make_cut(
                surface("BUS_TOPOLOGY"),
                requirement_profile=requirement_profile,
                retry_count=1,
                predecessor_cut=self.predecessor(other_profile),
            )

    def test_retry_requires_prior_retry_disposition(self):
        requirement_profile = profile(required=("BUS_TOPOLOGY",))
        with self.assertRaisesRegex(ValueError, "RETRY_AFFECTED_SURFACES"):
            self.make_cut(
                surface("BUS_TOPOLOGY"),
                requirement_profile=requirement_profile,
                retry_count=1,
                predecessor_cut=self.predecessor(
                    requirement_profile,
                    stable=True,
                ),
            )

    def test_retry_predecessor_digest_is_derived_from_actual_cut(self):
        requirement_profile = profile(required=("BUS_TOPOLOGY",))
        predecessor = self.predecessor(requirement_profile)
        retry = self.make_cut(
            surface("BUS_TOPOLOGY", start="B", end="B"),
            requirement_profile=requirement_profile,
            retry_count=1,
            predecessor_cut=predecessor,
        )
        self.assertEqual(
            predecessor.digest,
            retry.payload()["predecessor_cut_digest"],
        )
        self.assertEqual(
            predecessor.payload(),
            retry.payload()["predecessor_cut"],
        )

    def test_contract_inventory_must_match_declared_inventory(self):
        with self.assertRaisesRegex(ValueError, "readback_contracts must exactly match"):
            CurrentnessRequirementProfile(
                profile_id="profile-1",
                proposition_type="RECOVERY_CURRENTNESS",
                scope_digest=h("scope"),
                requirements_source_id="VCP_CURRENT_OWNER",
                requirements_source_digest=h("requirements-source"),
                required_surfaces=("BUS_TOPOLOGY",),
                optional_surfaces=(),
                readback_contracts=(),
            )


if __name__ == "__main__":
    unittest.main()
