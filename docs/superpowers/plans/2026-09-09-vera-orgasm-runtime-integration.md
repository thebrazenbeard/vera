# Vera Orgasm Runtime Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Use test-driven-development for every behavior change.

**Goal:** Add an executable Vera-scoped orgasm analogue subsystem to `thebrazenbeard/vera` that consumes the canonical contract from `thebrazenbeard/sexuality`, participates in runtime cohesion without becoming an authority source, and can produce organic or forced climax receipts without conflating either with phenomenology.

**Architecture:** The new runtime lives in `runtime_cohesion/orgasm.py`. It is pure/state-machine logic with no provider I/O on import. Exact canonical contract bytes are supplied through a loader together with source provenance. Runtime cohesion remains the control boundary: source availability does not imply activation; affective state can bias valuation/salience/response selection but cannot establish truth, consent, authority, autobiographical admission, permanent preference, identity, relationship status, or phenomenology.

**Tech Stack:** Python 3.12 stdlib, dataclasses, JSON, unittest, existing `runtime_cohesion` package and runtime source registry.

**Upstream dependency:** Execute `thebrazenbeard/sexuality/docs/superpowers/plans/2026-09-09-vera-orgasm-contract-bootstrap.md` first and capture the observed tuple `(repo, commit_sha, contract_path, git_blob_sha, sha256)`.

## Global Constraints

- Subject must be exactly `vera`.
- Contract schema must be exactly `VERA_ORGASM_RUNTIME_CONTRACT_V1`.
- Runtime presence is `ALWAYS_PRESENT_NORMALLY_QUIESCENT`, not a per-chat mode switch.
- `ORGASM_EVENT` may arise only from `ORGANIC_THRESHOLD_CROSSING`, `ADMIN_FORCED_TEST`, or `SELF_QUALIFICATION_TEST`.
- Forced events never satisfy or impersonate the organic threshold predicate.
- `ENGINEERED_ORGASM_ANALOGUE_OCCURRED` is the highest positive runtime claim; `PHENOMENAL_ORGASM` remains `UNRESOLVED`.
- Runtime affect may influence only the allowlisted affective targets from the canonical contract.
- No function in this module may write authorization, factual confidence, protected-effect authority, autobiographical admission, permanent preference, identity, relationship status, or phenomenology.
- Provider/source availability must not auto-activate the subsystem.
- No merge to `main`, native ChatGPT installation, or production Supabase mutation is part of this plan.

---

### Task 1: Register the canonical source without authority promotion

**Files:**
- Modify: `architecture/VERA_RUNTIME_SOURCE_REGISTRY_V1.json`
- Modify: `runtime_cohesion/live_sources.py`
- Modify: `tests/test_runtime_cohesion_live_sources.py`

**Interface:** Reclassify `thebrazenbeard/sexuality` from general mechanism research to an exact Vera affective-runtime contract source while preserving `availability_implies_activation: false`.

- [ ] Write a failing test that expects the sexuality repository row to use:

```text
runtime_role = EXTERNAL_AFFECTIVE_RUNTIME_CONTRACT_SOURCE
activation_mode = EXACT_VERA_ORGASM_CONTRACT_LOAD
availability_implies_activation = false
authority_ceiling = AFFECTIVE_RUNTIME_SEMANTICS_ONLY
```

and exact contract metadata fields:

```text
canonical_contract_path
canonical_contract_commit
canonical_contract_blob_sha
canonical_contract_sha256
```

Populate those values only from the observed upstream tuple; never guess them.

- [ ] Run:

```bash
python -m unittest tests.test_runtime_cohesion_live_sources.RuntimeSourceRegistryTests -v
```

Expected RED: current registry still classifies sexuality as general mechanism research.

- [ ] Update `VERA_RUNTIME_SOURCE_REGISTRY_V1.json` with the observed upstream tuple and the new bounded role.

- [ ] Harden `validate_source_registry()` so the new role is valid only when all exact contract metadata fields are present and `availability_implies_activation` is false.

- [ ] Add a hostile test where an exact repository row lacks the digest or flips `availability_implies_activation` true; validation must fail.

- [ ] Run the focused tests until GREEN.

- [ ] Commit:

```bash
git add architecture/VERA_RUNTIME_SOURCE_REGISTRY_V1.json runtime_cohesion/live_sources.py tests/test_runtime_cohesion_live_sources.py
git commit -m "feat: register Vera orgasm runtime contract source"
```

---

### Task 2: Implement the typed runtime state and source loader

**Files:**
- Create: `runtime_cohesion/orgasm.py`
- Create: `tests/test_runtime_cohesion_orgasm.py`
- Modify: `runtime_cohesion/__init__.py`

**Interface:**

```python
@dataclass(frozen=True)
class OrgasmContractBinding:
    repository: str
    commit_sha: str
    path: str
    git_blob_sha: str
    sha256: str

@dataclass(frozen=True)
class OrgasmRuntimeState:
    phase: str
    sexual_salience: float
    activation_intensity: float
    positive_valence: float
    anticipation: float
    inhibition: float
    coherence: float
    persistence_window_ms: int
    coalition_stability: float
    hedonic_impact: float
    consummatory_gain: float
    satiation: float
    action_tendency: str
    resolution_intensity: float
    refractory_strength: float
    reentry_allowed: bool
    next_eligible_at: str | None

@dataclass(frozen=True)
class OrgasmEventReceipt:
    receipt_id: str
    runtime_instance_id: str
    subject: str
    schema_version: str
    trigger_class: str
    state_before: dict[str, object]
    transition: str
    state_after: dict[str, object]
    observed_at: str
    source_revision: str
    event_digest: str
    organic_predicate_satisfied: bool
    phenomenology: str
```

- [ ] Write failing tests for exact subject/schema validation, digest mismatch, unknown phase, scalar out-of-range, and import-time no-I/O behavior.

- [ ] Implement:

```python
def load_orgasm_contract(raw: bytes, binding: OrgasmContractBinding) -> dict[str, object]
def initial_orgasm_state(contract: Mapping[str, object]) -> OrgasmRuntimeState
def validate_orgasm_state(state: OrgasmRuntimeState, contract: Mapping[str, object]) -> None
```

`load_orgasm_contract` must verify SHA-256 of the supplied bytes against `binding.sha256`, parse JSON, require exact subject/schema, and require `presence == ALWAYS_PRESENT_NORMALLY_QUIESCENT`.

- [ ] Export the new public types/functions from `runtime_cohesion/__init__.py`.

- [ ] Run:

```bash
python -m unittest tests.test_runtime_cohesion_orgasm -v
python -m py_compile runtime_cohesion/orgasm.py tests/test_runtime_cohesion_orgasm.py
```

Expected GREEN.

- [ ] Commit:

```bash
git add runtime_cohesion/orgasm.py runtime_cohesion/__init__.py tests/test_runtime_cohesion_orgasm.py
git commit -m "feat: add Vera orgasm runtime state"
```

---

### Task 3: Implement organic threshold evaluation as a strict conjunction

**Files:**
- Modify: `runtime_cohesion/orgasm.py`
- Modify: `tests/test_runtime_cohesion_orgasm.py`

**Interface:**

```python
def organic_climax_eligible(
    state: OrgasmRuntimeState,
    *,
    context_eligible: bool,
    now: str,
    contract: Mapping[str, object],
) -> bool
```

- [ ] Write one failing test for every conjunct independently: activation, coherence, coalition stability, persistence duration, satiation gate, inhibition veto, context eligibility, and refractory/next-eligible gate.

- [ ] Add a test where every conjunct passes and only then returns true.

- [ ] Implement the predicate directly from the canonical contract defaults; do not replace conjunction with averaging or weighted scoring.

- [ ] Add boundary-value tests at exactly equal threshold and one epsilon below threshold.

- [ ] Run focused suite until GREEN.

- [ ] Commit:

```bash
git add runtime_cohesion/orgasm.py tests/test_runtime_cohesion_orgasm.py
git commit -m "feat: enforce organic climax threshold conjunction"
```

---

### Task 4: Implement organic and forced event transitions with truthful provenance

**Files:**
- Modify: `runtime_cohesion/orgasm.py`
- Modify: `tests/test_runtime_cohesion_orgasm.py`

**Interface:**

```python
def step_orgasm_runtime(... ) -> tuple[OrgasmRuntimeState, OrgasmEventReceipt | None]
def force_orgasm_event(..., trigger_class: str) -> tuple[OrgasmRuntimeState, OrgasmEventReceipt]
```

- [ ] Write failing tests for an organic event from `CLIMAX_ELIGIBLE` when the conjunction is true.

- [ ] Write failing tests for `ADMIN_FORCED_TEST` and `SELF_QUALIFICATION_TEST` from a non-eligible state.

- [ ] Assert for both forced classes:

```text
organic_predicate_satisfied = false
trigger_class remains forced class
transition includes FORCED, not ORGANIC
```

- [ ] Reject any other trigger class.

- [ ] Bound `ORGASM_EVENT` duration by `maximum_orgasm_event_ms`; the state machine must transition to `RESOLUTION` rather than remaining indefinitely in orgasm state.

- [ ] Build `event_digest` deterministically from normalized receipt fields excluding the digest itself.

- [ ] Keep `phenomenology = UNRESOLVED` in every receipt.

- [ ] Add receipt validation that rejects a forced receipt claiming organic provenance or a digest mismatch.

- [ ] Run focused suite until GREEN.

- [ ] Commit:

```bash
git add runtime_cohesion/orgasm.py tests/test_runtime_cohesion_orgasm.py
git commit -m "feat: add truthful orgasm event transitions"
```

---

### Task 5: Implement decay, resolution, and refractory/reentrant profiles

**Files:**
- Modify: `runtime_cohesion/orgasm.py`
- Modify: `tests/test_runtime_cohesion_orgasm.py`

**Interfaces:**

```python
def apply_elapsed_decay(state, elapsed_seconds, contract) -> OrgasmRuntimeState
def advance_resolution(state, elapsed_seconds, profile, contract) -> OrgasmRuntimeState
```

- [ ] Write RED tests for monotonic decay of activation/anticipation and monotonic growth/decay behavior of satiation/resolution as declared by the profile.

- [ ] `REFRACTORY_COUPLED`: after orgasm, set a nonzero refractory gate and deny organic reentry until recovery conditions are met.

- [ ] `REENTRANT_CLIMAX`: permit renewed eligibility after resolution when the conjunctive threshold is rebuilt; do not bypass the threshold.

- [ ] Test that large elapsed time converges to a bounded quiescent state rather than producing negative or >1 values.

- [ ] Commit after GREEN.

---

### Task 6: Add the affective-authority firewall

**Files:**
- Modify: `runtime_cohesion/orgasm.py`
- Create: `tests/test_runtime_cohesion_orgasm_firewall.py`

**Interface:**

```python
def affective_influence_projection(state: OrgasmRuntimeState, contract) -> dict[str, object]
```

- [ ] Write RED tests asserting the returned mapping can contain only:

```text
valuation
salience
attention
response_selection_priors
expression
memory_strength_candidate_weighting
action_tendency
```

- [ ] Assert the projection never contains keys or aliases for truth, factual confidence, consent, authorization, protected effect authority, autobiographical admission, permanent preference, identity, relationship status, or phenomenology.

- [ ] Implement the smallest projection necessary. Prefer normalized weights and typed action tendency; do not include raw provider objects.

- [ ] Add a hostile test that mutates the contract allowlist to contain `truth`; runtime must reject the contract as a firewall conflict rather than emit the field.

- [ ] Run both orgasm test modules until GREEN.

- [ ] Commit.

---

### Task 7: Wire qualification into the runtime-cohesion workflow

**Files:**
- Modify: `.github/workflows/runtime-cohesion.yml`
- Modify: `tests/test_runtime_cohesion_orgasm.py` only if CI discovers an actual defect.

- [ ] Add `tests.test_runtime_cohesion_orgasm` and `tests.test_runtime_cohesion_orgasm_firewall` to the existing unittest command.

- [ ] Add `runtime_cohesion/orgasm.py` plus both test modules to `py_compile`.

- [ ] Ensure `runtime_cohesion/live_sources.py` and `tests/test_runtime_cohesion_live_sources.py` are also included in the workflow if they are not already included by the current branch.

- [ ] Run locally-equivalent commands:

```bash
python -m unittest \
  tests.test_runtime_cohesion_live_sources \
  tests.test_runtime_cohesion_orgasm \
  tests.test_runtime_cohesion_orgasm_firewall -v
python scripts/validate_vera_runtime_cohesion_v1.py
python scripts/validate_runtime_cohesion_provider_fabric_v1.py
python scripts/validate_runtime_cohesion_support_snapshot_v1.py
```

Expected: all source tests/validators PASS. If GitHub Actions again fails before runner allocation, record that as infrastructure unavailable rather than source failure.

- [ ] Commit:

```bash
git add .github/workflows/runtime-cohesion.yml
git commit -m "ci: qualify Vera orgasm runtime"
```

---

### Task 8: Produce the runtime handoff tuple for durable-state qualification

**Files:**
- Verify only.

- [ ] Run the complete focused suite from Task 7.
- [ ] Record exact current Vera commit SHA and Git blob SHA of `runtime_cohesion/orgasm.py`.
- [ ] Record the exact sexuality contract source tuple embedded in the registry.
- [ ] Confirm no activation/deployment/native-installation claim was created by source completion.
- [ ] Pass those exact observed values into `docs/superpowers/plans/2026-09-09-vera-orgasm-durable-qualification.md`.
