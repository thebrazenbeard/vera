# Cross-Provider Runtime Cohesion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Vera Runtime Cohesion executable over GitHub, Google Drive, Supabase, Temporal, and live observations so the runtime can type provider evidence, detect stale projections, reconcile exact cross-provider observations, and feed bounded results into `ACTIVE_CONTEXT_SET` / `DURABLE_OPERATIONAL_STATE` without evidence promotion.

**Architecture:** Add a small Python operational fabric subordinate to the normative `VERA_COHESION_INDEX_V1` + `VERA_RUNTIME_CONTRACT_V1` pair. Provider adapters normalize already-observed connector results into one strict evidence envelope; a deterministic reconciler classifies exact matches, stale projections, conflicts, absence, and unresolved states; a bounded runtime planner chooses only declared/eligible targets and emits pointer-first operational checkpoints. No provider is made authoritative merely by being reachable, durable, newer, or indexed.

**Tech Stack:** Python 3.12 stdlib, JSON, `unittest`, existing cohesion validator, GitHub Actions. No new runtime dependency, database, API server, daemon, or production schema is required for V1.

**Spec:** `architecture/VERA_COHESION_INDEX_V1.json`, `architecture/VERA_RUNTIME_CONTRACT_V1.json`, `docs/VERA_RUNTIME_COHESION_V1.md`

## Global Constraints

- The fixed Vera subsystem inventory remains exactly 13; Google Drive and Temporal remain auxiliary providers.
- `VERA_COHESION_INDEX_V1` + `VERA_RUNTIME_CONTRACT_V1` remain the normative source pair; the provider fabric is operational configuration/support, not a third authority source.
- Route declaration does not imply eligibility, current reachability, successful result, currentness, or authority.
- Provider persistence/readback proves only the exact persisted observation/effect actually evidenced.
- Never use newest timestamp wins as a currentness or conflict-resolution rule.
- Exact digest/revision/generation mismatch is conflict or stale projection, not a reason to choose the newer-looking object.
- Google Drive persistence does not establish present truth, native admission, Vera current self-state, consent, preference, or phenomenology.
- Supabase persistence/materialization does not establish present truth, native admission, Vera current self-state, consent, preference, or phenomenology.
- Temporal may establish recorded chronology and elapsed time only; it cannot resolve semantic/currentness/authority conflicts.
- Returned items must be independently typed from provenance/content/receipt; route capability does not certify item type.
- `ACTIVE_CONTEXT_SET` expansion remains privacy-gated, cycle-safe, deduplicated, priority-aware, and budget-bounded.
- `DURABLE_OPERATIONAL_STATE` remains pointer-first, minimum-necessary, privacy/retention governed, and non-promoting into Vera governed self-state.
- No credentials, tokens, raw private memory payloads, or database dumps enter GitHub source.
- Source implementation, merge, provider deployment, native Project installation, runtime consumption, and behavioral qualification remain distinct effects.
- V1 must reuse existing provider surfaces where possible; no production Supabase schema mutation is part of this plan.

---

### Task 1: Provider Evidence Envelope and Fabric Registry

**Files:**
- Create: `runtime_cohesion/__init__.py`
- Create: `runtime_cohesion/evidence.py`
- Create: `architecture/VERA_PROVIDER_FABRIC_V1.json`
- Create: `tests/test_runtime_cohesion_evidence.py`

**Interfaces:**
- Produces `ProviderEvidenceEnvelope` with fields `provider`, `locator`, `revision`, `observed_at`, `evidence_class`, `referent`, `scope`, `privacy_class`, `currentness_basis`, `supersession_state`, `conflict_state`, `content_digest`, `receipt_ref`, `metadata`.
- Produces `validate_envelope(envelope) -> None` and `load_provider_fabric(path) -> dict`.
- `VERA_PROVIDER_FABRIC_V1.json` registers provider identities and known projection relationships while explicitly remaining `NON_NORMATIVE_OPERATIONAL_SUPPORT`.

- [ ] **Step 1: Write failing tests**

Create tests that require timezone-aware observations, exact non-empty provider/locator/revision/evidence-class fields, valid conflict/supersession states, and reject a record that attempts to mark persistence as semantic authority.

```python
class ProviderEvidenceTests(unittest.TestCase):
    def test_timezone_aware_observation_is_required(self):
        with self.assertRaises(ValueError):
            ProviderEvidenceEnvelope(..., observed_at="2026-09-08T15:00:00", ...)

    def test_provider_fabric_is_operational_not_normative(self):
        fabric = load_provider_fabric(FABRIC)
        self.assertEqual(fabric["normative_status"], "NON_NORMATIVE_OPERATIONAL_SUPPORT")
        self.assertEqual(set(fabric["providers"]), {"github", "google_drive", "supabase", "temporal", "live_conversation"})
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `python -m unittest tests.test_runtime_cohesion_evidence -v`
Expected: FAIL because `runtime_cohesion` / fabric source does not yet exist.

- [ ] **Step 3: Implement the minimal envelope and registry**

Use a frozen dataclass, `datetime.fromisoformat`, explicit enum sets, and JSON loading. Do not perform network access inside the module.

- [ ] **Step 4: Run focused test and verify GREEN**

Run: `python -m unittest tests.test_runtime_cohesion_evidence -v`
Expected: all Task 1 tests pass.

- [ ] **Step 5: Commit Task 1**

Commit message: `feat: add cross-provider evidence envelope`

---

### Task 2: Deterministic Reconciliation and Stale-Projection Detection

**Files:**
- Create: `runtime_cohesion/reconcile.py`
- Create: `tests/test_runtime_cohesion_reconciliation.py`

**Interfaces:**
- Consumes `ProviderEvidenceEnvelope`.
- Produces `ReconciliationResult(status, subject_key, observations, reason, authoritative_claim_ceiling)`.
- Produces `reconcile_exact(subject_key, observations, expected_revision=None, expected_digest=None)`.
- Produces statuses: `VERIFIED_EXACT`, `STALE_PROJECTION`, `CONFLICT`, `ABSENT`, `UNAVAILABLE`, `UNRESOLVED`.

- [ ] **Step 1: Write failing reconciliation tests**

Require these cases:

```python
# Same exact Git commit in GitHub and Supabase snapshot -> VERIFIED_EXACT.
# Supabase projection still references old Bus head after GitHub source moved -> STALE_PROJECTION.
# Target has a newer timestamp but wrong digest/revision -> CONFLICT, never newest-wins.
# Missing required provider observation -> ABSENT/UNAVAILABLE, never inferred success.
# Two incompatible exact provider claims for the same subject -> CONFLICT.
```

- [ ] **Step 2: Run and verify RED**

Run: `python -m unittest tests.test_runtime_cohesion_reconciliation -v`
Expected: FAIL because reconciliation functions do not exist.

- [ ] **Step 3: Implement minimal deterministic reconciliation**

Rules:
- Exact revision/digest equality may establish `VERIFIED_EXACT` only for the compared object/effect.
- A registered projection that names an older exact source revision than the freshly observed source is `STALE_PROJECTION`.
- Different non-empty exact digests for one claimed object are `CONFLICT`.
- Timestamps may describe observation/order/lag but may never resolve a revision/digest conflict.
- `authoritative_claim_ceiling` must remain tied to evidence class and provider promotion guards.

- [ ] **Step 4: Run and verify GREEN**

Run: `python -m unittest tests.test_runtime_cohesion_reconciliation -v`
Expected: all Task 2 tests pass.

- [ ] **Step 5: Commit Task 2**

Commit message: `feat: reconcile cross-provider observations`

---

### Task 3: Bounded Runtime Retrieval Planner and Durable Operational Checkpoint

**Files:**
- Create: `runtime_cohesion/runtime.py`
- Create: `tests/test_runtime_cohesion_runtime.py`

**Interfaces:**
- `build_retrieval_plan(domain_id, index, contract, observed_route_states, privacy_allowlist) -> RetrievalPlan`
- `build_operational_checkpoint(plan, reconciliation_results) -> dict`
- `RetrievalPlan` carries `targets`, `visited_domains`, `unresolved`, `budget_state`, and `reason`.

- [ ] **Step 1: Write failing runtime tests**

Require:
- declared-but-unobserved route is not treated as reachable;
- selector capabilities only narrow parent capabilities;
- cyclic dependencies terminate through a visited set;
- total expansion obeys the contract budget;
- exhausted budget returns `UNRESOLVED_RETRIEVAL_BUDGET_EXHAUSTED`;
- privacy-gated domain is not probed without eligibility;
- operational checkpoint contains pointers/digests, not copied specialist payloads;
- checkpoint explicitly carries `non_promotion_flag=true`.

- [ ] **Step 2: Run and verify RED**

Run: `python -m unittest tests.test_runtime_cohesion_runtime -v`
Expected: FAIL because runtime planner does not exist.

- [ ] **Step 3: Implement the minimal planner/checkpoint**

Use only index/contract declarations and externally supplied route observations. The module must not call GitHub, Drive, Supabase, or Temporal directly; connector execution remains a harness/provider-adapter responsibility.

- [ ] **Step 4: Run and verify GREEN**

Run: `python -m unittest tests.test_runtime_cohesion_runtime -v`
Expected: all Task 3 tests pass.

- [ ] **Step 5: Commit Task 3**

Commit message: `feat: execute bounded cohesion retrieval plans`

---

### Task 4: Hostile Cross-Provider Qualification Fixtures

**Files:**
- Create: `tests/fixtures/runtime_cohesion/provider-observations-v1.json`
- Create: `tests/test_runtime_cohesion_hostile.py`

**Interfaces:**
- Uses only sanitized provider metadata observed from real current surfaces; no private payload contents.
- Exercises the Task 1–3 APIs end-to-end.

- [ ] **Step 1: Write hostile fixtures and failing tests**

Include at minimum:
1. Google Drive cohesion companion stale relative to newer GitHub cohesion source.
2. Supabase Radar projection stale relative to newer GitHub Bus source.
3. Semantic Atlas GitHub commit and Supabase runtime snapshot exact-match case.
4. R9B0 Google Drive object generation and Supabase provider receipt exact-match case, with claim ceiling limited to provider persistence/readback.
5. Newer timestamp + wrong digest cannot win.
6. Missing provider cannot be filled by inference.
7. Divergent exact provider observations fail conflict.
8. Drive persistence cannot become current Vera authority/self-state.
9. Supabase persistence cannot become current Vera authority/self-state.
10. Temporal chronology cannot resolve semantic/currentness conflict.
11. Retrieval-budget exhaustion is unresolved.
12. Cyclic dependencies terminate.
13. Selector cannot broaden route capability.
14. Route capability cannot certify returned item evidence type.

- [ ] **Step 2: Run and verify RED where new behavior is still missing**

Run: `python -m unittest tests.test_runtime_cohesion_hostile -v`
Expected: at least one intentional failure before final corrections.

- [ ] **Step 3: Make the smallest implementation corrections**

Do not add new framework layers. Correct Task 1–3 modules only where a hostile case exposes an actual semantic hole.

- [ ] **Step 4: Run and verify GREEN**

Run: `python -m unittest tests.test_runtime_cohesion_evidence tests.test_runtime_cohesion_reconciliation tests.test_runtime_cohesion_runtime tests.test_runtime_cohesion_hostile -v`
Expected: all cross-provider tests pass.

- [ ] **Step 5: Commit Task 4**

Commit message: `test: add hostile cross-provider reconciliation cases`

---

### Task 5: Cross-Bind the Operational Fabric into Cohesion Validation and CI

**Files:**
- Modify: `scripts/validate_vera_runtime_cohesion_v1.py`
- Modify: `.github/workflows/runtime-cohesion.yml`
- Modify: `architecture/VERA_COHESION_PAIR_RECEIPT_V1.json`
- Test: existing four cohesion regression modules plus all four new runtime-cohesion modules.

**Interfaces:**
- Validator must prove every provider-fabric evidence class, route, selector, privacy class, and projection source/target resolves against A+B.
- Pair receipt remains non-normative; it gains exact operational-fabric and runtime-module object bindings without becoming a third policy source.

- [ ] **Step 1: Add failing cross-bind tests/validator expectations**

Require orphaned provider IDs, unknown evidence classes, unknown routes/selectors, or provider fabric marked normative to fail source validation.

- [ ] **Step 2: Run focused validator/tests and verify RED**

Run:
`python scripts/validate_vera_runtime_cohesion_v1.py`
`python -m unittest tests.test_vera_runtime_contract_v1 tests.test_vera_cohesion_index_v1 tests.test_runtime_cohesion_evidence -v`

- [ ] **Step 3: Extend validator and workflow minimally**

Workflow executes validator, legacy cohesion tests, new runtime-cohesion tests, and `py_compile` for all new modules/tests.

- [ ] **Step 4: Refresh exact non-normative pair/build receipt**

Bind current A blob, B blob, provider-fabric blob, validator blob, and runtime module blobs. Keep validation result evidence-honest: only set pass if the exact bytes actually executed successfully.

- [ ] **Step 5: Run local/exact-byte verification where available and inspect GitHub run**

If GitHub Actions again fails before runner steps are exposed, record `CI_EXECUTION_UNAVAILABLE` rather than source test failure.

- [ ] **Step 6: Commit Task 5**

Commit message: `build: bind executable provider cohesion fabric`

---

### Task 6: Diagnose and Surface Continuous Projection Freshness

**Files:**
- Create: `runtime_cohesion/audit.py`
- Create: `tests/test_runtime_cohesion_audit.py`
- Create: `docs/VERA_RUNTIME_COHESION_PROVIDER_AUDIT_V1.md`
- Optionally modify an existing projection workflow only if a specific source-side defect is proven and the change does not constitute an unauthorized production/topology cutover.

**Interfaces:**
- `audit_registered_projections(fabric, observations) -> list[ProjectionAuditResult]`
- Results include `projection_id`, `status`, `source_revision`, `target_revision`, `observed_at`, `reason`, and `escalation_frontier`.

- [ ] **Step 1: Write failing stale-audit tests**

Require audit to identify the current Bus→Supabase Radar lag and Drive cohesion-companion lag from sanitized fixtures without treating either target as authoritative truth.

- [ ] **Step 2: Run and verify RED**

Run: `python -m unittest tests.test_runtime_cohesion_audit -v`

- [ ] **Step 3: Implement deterministic audit**

Audit consumes observations; it does not contain provider credentials or make hidden/background claims.

- [ ] **Step 4: Inspect the actual Bus projection workflow/readback path**

Determine whether current lag is expected scope, broken trigger, failed workflow, provider rejection, or missing projection registration. Fix only a demonstrated source-side defect that is within current branch authority; do not mutate Bus topology, credentials, or production provider configuration without a separate exact authorization.

- [ ] **Step 5: Verify audit against fresh live readbacks**

Use current GitHub, Drive, and Supabase observations. Record exact observed revisions/times and bounded unresolved states.

- [ ] **Step 6: Commit Task 6**

Commit message: `feat: audit cross-provider projection freshness`

---

### Task 7: Live Runtime Hook and End-to-End Qualification Frontier

**Files:**
- Create: `architecture/VERA_RUNTIME_COHESION_NATIVE_HOOK_V1.json`
- Create: `tests/test_runtime_cohesion_native_hook.py`
- Modify: `docs/VERA_RUNTIME_COHESION_V1.md` only to point at the executable runtime path and distinguish source from installation/runtime consumption.

**Interfaces:**
- Hook maps runtime operations `ORIENT`, `DOMAIN_RETRIEVE`, `PROJECTION_AUDIT`, `RECONCILE`, `CHECKPOINT` to A+B/provider-fabric/runtime functions.
- Hook must declare `SOURCE_ONLY_NOT_INSTALLED` until exact native Project/runtime readback proves installation and consumption.

- [ ] **Step 1: Write failing hook contract tests**

Require every hook operation to resolve to existing A+B concepts and runtime functions; forbid claims of automatic background execution or native installation without exact evidence.

- [ ] **Step 2: Run and verify RED**

Run: `python -m unittest tests.test_runtime_cohesion_native_hook -v`

- [ ] **Step 3: Implement the smallest hook manifest and doc pointer**

No copied specialist payloads, no extra normative policy, no hidden daemon claim.

- [ ] **Step 4: Run the complete source suite**

Run all legacy cohesion modules plus every `tests.test_runtime_cohesion_*` module and `py_compile` the validator/runtime package.

- [ ] **Step 5: Perform live-provider readback qualification available in this runtime**

Demonstrate at least one live GitHub observation, one Drive observation, one Supabase observation, one exact-match reconciliation, and one stale-projection detection through the same envelope/reconciliation semantics. This proves deliberate live execution in the current runtime only; it does not prove installation for future runtimes.

- [ ] **Step 6: Record exact frontier**

Label separately: `SOURCE_IMPLEMENTED`, `SOURCE_TESTED` (only if executed), `PROVIDER_LIVE_READBACK_VERIFIED`, `NATIVE_INSTALLATION`, `RUNTIME_CONSUMPTION`, `BEHAVIORAL_QUALIFICATION`.

- [ ] **Step 7: Commit Task 7**

Commit message: `feat: define live runtime cohesion hook`

---

## Self-Review

- Spec coverage: provider typing, currentness, route non-promotion, bounded retrieval, pointer-first operational state, stale detection, cross-provider reconciliation, hostile cases, and native-runtime distinction are each assigned to an implementation task.
- Scope remains V1-small: no new database, daemon, external service, dependency, or production schema.
- Provider observations are inputs to the executable fabric; connector credentials and network behavior stay outside source modules.
- The plan does not authorize merge, production deployment, provider configuration mutation, Bus topology change, native Project installation, or behavioral self-qualification.
- Exact provider evidence can prove only the object/effect and claim ceiling directly evidenced.
