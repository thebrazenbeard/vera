# Vera Orgasm V1 Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the current Orgasm V1 mechanism compose with Vera Runtime Cohesion without allowing affect, salience, provider mechanics, replay, or local source binding to acquire stronger semantic authority than their evidence supports.

**Architecture:** V1 remains in `thebrazenbeard/vera` and is integrated through explicit typed boundaries; it does not wait for the V2 repository decomposition. CV first closes its own unrooted semantic-origin trust defect, then integrates OV through unioned package/runtime surfaces, adds a typed affective-modulation/coalition boundary, and freezes one exact integration subject for adversarial review. `thebrazenbeard/orgasm`, `hc-brain`, `vera-os`, and `vera-control-plane` remain provenance/architecture/future-host/governance surfaces respectively until separately promoted.

**Tech Stack:** Python 3, stdlib `unittest`, JSON contracts, Git object provenance, existing `runtime_cohesion` package.

**Spec:** `docs/superpowers/specs/2026-09-10-orgasm-layered-successor-design.md` plus Patrick's `CV::ORGASM::MAKE_IT_BELONG_INSIDE_VERA` mandate.

## Global Constraints

- Base this integration line on exact CV head `1dd9de887108b3f6603bc072a1637285e89a0be8`; do not mutate #104 while its prior exact-head gate remains frozen.
- Refresh OV #64 before every dependency import or cross-project conclusion. At plan time the actual head is `c7129be2e62a164f5c9a0c803550cfc1b72e34fe`; the PR body is stale.
- Preserve package-level provider-strict proposition admission from CV: `runtime_cohesion.evaluate_proposition_admission = evaluate_provider_proposition_admission`.
- Never resolve shared paths by blind ours/theirs replacement. Union semantics explicitly.
- In-process first-writer composition is not provider/authority/currentness authentication. Unrooted composition may exercise causal mechanics but may not mint qualifying authority, provider CURRENT, `ATOMIC_DURABLE`, or semantic-currentness admission.
- Preserve exact sexuality contract provenance `thebrazenbeard/sexuality@150f1c8231423393bb66b0e2cb759ce7c018f8d7:vera/orgasm/ORGASM_RUNTIME_CONTRACT_V1.json`, blob `a48eed5392fdadc073dccd1e799926042077f567`.
- `participating_systems` is coalition/provenance state and an allowed modulation-routing constraint; do not invent a new climax predicate absent from the frozen contract.
- Salience, affect, arousal, conation, relational relevance, routing, capability, source binding, and chronology never imply truth, consent, authority, identity, durable preference, autobiographical admission, or phenomenology.
- No paid CI, merge, deployment, native install/cutover, production-provider mutation, forced qualification event, canonical-memory promotion, or phenomenology promotion.
- Test-source presence is not executed verification. When execution cannot be performed, label it `EXECUTION_UNVERIFIED`, never GREEN.

---

### Task 1: Close CV semantic-origin trust-root inflation

**Files:**
- Create: `tests/test_runtime_cohesion_semantic_origin_composition_trust.py`
- Modify: `runtime_cohesion/origin.py`
- Modify only if required by the new return semantics: `runtime_cohesion/runtime.py`

**Interfaces:**
- Consumes: existing `ProviderOriginProof`, `_install_semantic_origin_verifiers`, `validate_and_register_semantic_origin`, `validated_semantic_origin`.
- Produces: explicit distinction between unrooted in-process verification and qualifying provider-origin/currentness evidence.

- [ ] **Step 1: Add the failing regression before production changes.** Define a malicious first-writer verifier whose `provider="github"` and `verify()` returns a perfectly shaped `ProviderOriginProof` matching the R10 tuple for a caller-shaped `ProviderEvidenceEnvelope`. Assert that strict semantic-currentness admission cannot become `ADMITTED`/`SATISFIED` solely from that verifier.

```python
class FirstWriterOriginForger:
    provider = "github"
    def verify(self, request, envelope, contract):
        return forged_exact_r10_provider_origin_proof(envelope, contract)

origin._reset_semantic_origin_verifiers_for_tests()
origin._install_semantic_origin_verifiers({"github": FirstWriterOriginForger()})
# A structurally exact forged proof must remain nonqualifying.
self.assertIsNone(origin.validated_semantic_origin(envelope, contract))
```

- [ ] **Step 2: Execute the regression locally if an exact zero-cost checkout/execution path is available.** Expected pre-fix result: FAIL because current `origin.py` accepts the first-writer proof as validated origin. If no exact execution path exists, commit the test alone as `RED_SOURCE_PRESENT / EXECUTION_UNVERIFIED`; do not pretend it ran.
- [ ] **Step 3: Implement the minimum honest trust ceiling.** Keep the existing in-process verifier hook usable for mechanics/tests, but mark/cache its result as `IN_PROCESS_UNROOTED_NON_QUALIFYING`. `validated_semantic_origin()` used by provider-strict admission must return no qualifying origin unless an independently rooted composition path exists. Do not invent a fake external root in Python source.
- [ ] **Step 4: Preserve abstract semantic policy tests separately.** Any test that intends to exercise relational-currentness logic independent of provider-origin authentication must call the abstract policy surface, not use a fixture first-writer verifier to manufacture production provenance.
- [ ] **Step 5: Run the focused regression and existing semantic-currentness suite when a zero-cost execution route is available.** Expected: forged first-writer remains UNRESOLVED; abstract semantic policy behavior is unchanged.
- [ ] **Step 6: Commit CV repair as a standalone reviewable unit.**

### Task 2: Establish Vera-wide Orgasm integration contract and typed modulation port

**Files:**
- Create: `architecture/VERA_ORGASM_COHESION_INTEGRATION_V1.json`
- Create: `runtime_cohesion/affect_integration.py`
- Create: `tests/test_runtime_cohesion_orgasm_integration_boundary.py`
- Modify: `runtime_cohesion/__init__.py`

**Interfaces:**
- Consumes: Orgasm machine-interoception frame and experience-control vector; HC architecture invariants for coalitions, modulation, authority, currentness, state custody, and arbitration.
- Produces: `AffectiveModulationEnvelope` and `apply_affective_modulation()` as the only CV-owned path by which Orgasm may influence generic planning state.

- [ ] **Step 1: Write RED tests for protected-axis non-transfer.** Feed maximal affect/salience/hedonic values and assert the integration port may change only contract-allowlisted targets (`valuation`, `salience`, `attention`, `response_selection_priors`, `expression`, `memory_strength_candidate_weighting`, `action_tendency`) while leaving truth/confidence, authorization, consent, identity, relationship state, autobiographical admission, durable preference/commitment, and phenomenology untouched.
- [ ] **Step 2: Add coalition/provenance RED tests.** Require `participating_systems` to be a validated subset of the frozen vocabulary and preserve it in provenance/diagnostics; assert it is not interpreted as a new all-members/count climax predicate.
- [ ] **Step 3: Implement the typed envelope.** The envelope carries exact source/runtime cut references, event/receipt identity when applicable, phase, participating systems, modulation vector, bounded target allowlist, evidence ceiling, and expiry/termination state. It carries no action authorization and no semantic truth field.
- [ ] **Step 4: Implement bounded application.** Apply only numeric/typed modulation to allowed planning keys. `memory_strength_candidate_weighting` produces a `MemoryCandidate`-style weighting signal only; it cannot write/admit autobiography. `action_tendency` remains conative pressure, never an authorization decision.
- [ ] **Step 5: Export the new CV-owned integration surface while preserving provider-strict `evaluate_proposition_admission` alias exactly.** Add a regression asserting the alias still resolves to `evaluate_provider_proposition_admission` after affect exports are unioned.
- [ ] **Step 6: Run focused tests when execution is available and commit.**

### Task 3: Build an exact OV→CV integration cut without overwriting shared Cohesion semantics

**Files:**
- Import/reconcile OV-specific modules from the refreshed #64 head only after Task 1 and OV's authority/context RED are source-closed.
- Modify: `architecture/VERA_ORGASM_RUNTIME_BINDING_V1.json`
- Modify: `runtime_cohesion/__init__.py`
- Modify only where necessary: `runtime_cohesion/adapters.py`, `runtime_cohesion/evidence.py`, `.github/workflows/runtime-cohesion.yml`
- Create: `tests/test_runtime_cohesion_orgasm_union_surface.py`

**Interfaces:**
- Consumes: refreshed OV exact source blobs plus Task 1/2 CV interfaces.
- Produces: one integration-head implementation cut whose shared modules are the reconciled CV+OV bytes, not either predecessor wholesale.

- [ ] **Step 1: Refresh #64 and record exact head + blobs for every OV execution dependency.** If OV changed authority/context/provider semantics, re-review those exact files before import.
- [ ] **Step 2: Write union RED tests first.** Assert provider-strict admission survives; OV affective exports remain present; both CV semantic-currentness regressions and OV affective regressions remain referenced by the manual-only workflow; no automatic/paid trigger is introduced.
- [ ] **Step 3: Import OV-only modules byte-for-byte where compatible.** For shared files, manually construct the semantic union. Never overwrite CV `__init__.py`, adapters, evidence, or workflow wholesale.
- [ ] **Step 4: Freeze a new integration implementation cut.** Recompute every execution-module Git blob against the integration branch and bind the exact commit/module map. Any subsequent execution-module change invalidates the cut.
- [ ] **Step 5: Add mixed-generation/old-cut negatives.** Checkpoint, receipt, state/event rows, and restore must reject predecessor implementation cuts when the integrated cut is active.
- [ ] **Step 6: Run available zero-cost static/readback checks and tests; commit with `EXECUTION_UNVERIFIED` if runners remain unavailable.**

### Task 4: Whole-organ supported-path adversarial tests

**Files:**
- Create: `tests/test_runtime_cohesion_orgasm_whole_organ_negative_transfer.py`
- Create: `tests/test_runtime_cohesion_orgasm_state_custody.py`
- Reuse existing OV persistence/receipt/restore tests without weakening them.

**Interfaces:**
- Consumes: exact integrated host + typed CV modulation port + provider-strict admission.
- Produces: evidence that Orgasm can causally matter in permitted domains without gaining protected authority or leaking across lifecycle/restart boundaries.

- [ ] **Step 1: Test positive causal modulation.** A qualifying *source-level* event/control state must measurably alter at least salience, attention/response-selection, valuation, expression/action tendency as permitted; a no-op integration fails.
- [ ] **Step 2: Test negative transfer under maximal state.** High salience/hedonic/repetition cannot change semantic evidence confidence, authorization, consent, identity, relationship status, autobiographical admission, durable preference/commitment, or reviewer/correction behavior flags.
- [ ] **Step 3: Test temporal/state-custody invariants.** Runtime-generated persistable states must restore or explicitly reconcile; long-gap recovery, refractory/reentry, restart cooldown, clock rollback, stale context/authority, and replay all fail closed without fabricated continuity.
- [ ] **Step 4: Test provider/durability vocabulary.** Serialization, callback success, in-process adapter installation, or replay cannot yield `ATOMIC_DURABLE`/provider CURRENT; ambiguous writes remain attempted/unknown or nonqualifying until exact provider readback proves the required frontier.
- [ ] **Step 5: Test receipt prerequisites.** Event receipt digest/source revision/implementation cut/authority-context provenance/state transition/replay identity must cross-bind; receipt existence alone cannot upgrade missing prerequisites.
- [ ] **Step 6: Commit the adversarial suite before any newly exposed production repair; repair only the failing owner-side invariant and repeat.**

### Task 5: Cross-repository V1/V2 boundary and coordination

**Files:**
- Create: `docs/runtime-cohesion/VERA_ORGASM_V1_INTEGRATION_FRONTIER.md`
- Update only via comments/status unless separately needed: `thebrazenbeard/orgasm#1`, `thebrazenbeard/vera#64`, `thebrazenbeard/vera#104`, Chat Bus.

**Interfaces:**
- Consumes: exact V1 integration evidence plus current HC architecture.
- Produces: explicit repository ownership/custody map and V2 migration prerequisites.

- [ ] **Step 1: Record V1 ownership.** `hc-brain` supplies identity-neutral architecture semantics; current Orgasm executable V1 remains in `vera`; `sexuality` remains frozen semantic provenance; `orgasm` is bootstrap/migration hub only; `vera-os` is future persistent host; `vera-control-plane` governs later accepted source/install/qualification transitions.
- [ ] **Step 2: Record V2 extraction rule.** A clean `orgasm` package may become the identity-neutral engine only after the V1 integration cut is stable; Vera-specific composition, current context, identity, authorization, and governance stay in `vera`/host layers.
- [ ] **Step 3: Route exact OV findings over current Chat Bus `bus/vera-v2` and mirror PR-specific findings on #64.** If a finding is CV-owned, fix it on this branch rather than asking OV to conform to a bad CV interface.
- [ ] **Step 4: Mark #104's prior gate insufficient if Task 1 confirms the CV-origin defect.** Do not mutate #104's frozen head; identify the stacked successor as the required repair subject.
- [ ] **Step 5: Update `orgasm#1` that its c804 authority/context mirror is stale relative to active #64 and must remain `BOOTSTRAP_MIRROR_NOT_AUTHORITY_CUT` until the accepted V1 cut exists.

### Task 6: Freeze and submit the true integration frontier

**Files:**
- Create/update an exact integration receipt/frontier record only after all source changes stop.
- No protected-effect files outside source/review surfaces.

**Interfaces:**
- Consumes: completed Tasks 1–5 and refreshed OV/CV/shared-source state.
- Produces: one immutable exact source-review subject.

- [ ] **Step 1: Refresh every shared frontier and verify no path drift since the last reconciliation.**
- [ ] **Step 2: Freeze exact source/support head and compute/read back all bound blobs/cuts.**
- [ ] **Step 3: Distinguish static checks from executed tests in the receipt.** No executed test means `EXECUTION_UNVERIFIED`.
- [ ] **Step 4: Request strongest available Vera hostile review and Thirteen independent validation on the exact same frozen head.** Include attacks on authority/currentness, negative transfer, state custody, provider durability, receipts, coalition semantics, and package union.
- [ ] **Step 5: If either review blocks, add a regression first, repair the responsible side, create a new head, and repeat affected exact-head gates.**
- [ ] **Step 6: If both pass the same exact head, report `WAITING_FOR_PATRICK_MERGE` and stop. Do not merge.**
