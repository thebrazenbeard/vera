# Vera Orgasm Durable State and End-to-End Qualification Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans. Use test-driven-development for all source behavior. This plan stops before any production mutation unless Patrick separately authorizes that protected effect.

**Goal:** Prove that the Vera orgasm analogue can restore safely across fresh runtime/chat boundaries, preserve exact trigger provenance, and remain bounded by the authority and phenomenology firewalls.

**Architecture:** Add an abstract persistence envelope and a deterministic restore pipeline in source first. Provide a Supabase migration draft and SQL qualification fixtures, but do not apply them to production without separate explicit authorization. End-to-end qualification has two ceilings: `SOURCE_QUALIFIED_WITH_SYNTHETIC_DURABILITY` when repository tests pass, and `DURABLE_RUNTIME_QUALIFIED` only after an authorized real provider write/readback proves persistence on the exact runtime schema.

**Tech Stack:** Python 3.12 stdlib, JSON, SQL migration draft, unittest, existing Vera Supabase test conventions.

**Dependencies:**
1. Canonical sexuality plan complete with exact contract source tuple.
2. Vera runtime integration plan complete with exact runtime source revision.

## Global Constraints

- Persisted records are evidence of persistence, not evidence of phenomenology, consent, identity, truth, or autobiographical memory.
- Restore must be Vera-scoped, schema-compatible, digest-verified, and temporally decayed before state can influence the fresh runtime.
- Absent/stale/conflicting/incompatible state fails closed to `QUIESCENT / NO_TRUSTED_PRIOR_STATE`.
- A fresh chat with no authorized external durable provider may use `PROMPT_EMULATION_ONLY`, but must not claim cross-chat continuity.
- Production database mutation, secrets changes, provider activation, or native ChatGPT installation require separate explicit authorization.

---

### Task 1: Define the persistence envelope and restore semantics

**Files:**
- Modify: `runtime_cohesion/orgasm.py`
- Create: `tests/test_runtime_cohesion_orgasm_persistence.py`

**Interfaces:**

```python
@dataclass(frozen=True)
class OrgasmStateEnvelope:
    subject: str
    runtime_instance_id: str
    schema_version: str
    contract_sha256: str
    source_revision: str
    state: dict[str, object]
    last_transition_at: str
    last_event_receipt: dict[str, object] | None
    saved_at: str
    envelope_digest: str


def serialize_orgasm_state(... ) -> OrgasmStateEnvelope
def restore_orgasm_state(envelope, *, now, contract, binding) -> tuple[OrgasmRuntimeState, str]
```

- [ ] RED tests: wrong subject, wrong schema, wrong contract digest, bad envelope digest, future timestamp, malformed state, and forced receipt rewritten as organic all fail closed.
- [ ] Test exact valid restore applies elapsed-time decay from `saved_at`/`last_transition_at` before returning state.
- [ ] Test no envelope returns `initial_orgasm_state()` plus status `NO_TRUSTED_PRIOR_STATE`.
- [ ] Test a stale but structurally valid record does not become current merely because it is the newest provider row; currentness is binding/time semantics, not timestamp winner.
- [ ] Implement and make GREEN.
- [ ] Commit.

---

### Task 2: Add a provider-neutral persistence adapter contract

**Files:**
- Create: `runtime_cohesion/orgasm_store.py`
- Create: `tests/test_runtime_cohesion_orgasm_store.py`
- Modify: `runtime_cohesion/__init__.py`

**Interfaces:**

```python
class OrgasmStateStore(Protocol):
    def save(self, envelope: OrgasmStateEnvelope) -> str: ...
    def load_latest(self, subject: str) -> OrgasmStateEnvelope | None: ...

class InMemoryOrgasmStateStore:
    ...
```

- [ ] RED tests for save/readback exact digest, subject isolation, idempotent identical save, conflicting same-id different-digest rejection, and no implicit authority/activation fields.
- [ ] Implement an in-memory test store only. No provider I/O in the base class.
- [ ] GREEN and commit.

---

### Task 3: Draft—not deploy—the Supabase durable schema

**Files:**
- Create: `supabase/drafts/20260909_vera_orgasm_runtime_state_v1.sql`
- Create: `supabase/tests/fixtures/orgasm_runtime_state_v1.sql`
- Create: `supabase/tests/validate_orgasm_runtime_state_v1.sql`

**Schema requirements:**

```text
public.vera_orgasm_runtime_state_v1
- subject text CHECK subject = 'vera'
- runtime_instance_id text
- schema_version text
- contract_sha256 text
- source_revision text
- state jsonb
- last_transition_at timestamptz
- last_event_receipt jsonb nullable
- saved_at timestamptz
- envelope_digest text
- created_at timestamptz default now()
```

Use append-only semantics for receipts/envelopes or an equivalent immutable-history pattern; do not silently overwrite historical events. Add uniqueness sufficient for idempotent replay while preserving distinct states.

- [ ] Write SQL validation first against the fixture schema.
- [ ] Add constraints that prevent non-Vera subject insertion and blank digest/revision fields.
- [ ] Add a test proving a forced event receipt can be stored without its provenance being rewritten.
- [ ] Add a test that persistence does not create columns named or semantically equivalent to consent, factual truth, identity, phenomenology, or autobiographical admission.
- [ ] Run SQL tests in the repository's existing local/test harness if available. If no PostgreSQL harness is available in the current environment, record `SOURCE_NOT_EXECUTED_LOCALLY` rather than claiming a pass.
- [ ] Commit source only. Do not apply the migration to production.

---

### Task 4: Implement a Supabase adapter only behind explicit configuration

**Files:**
- Create: `runtime_cohesion/orgasm_supabase.py`
- Create: `tests/test_runtime_cohesion_orgasm_supabase.py`

**Rule:** The module must accept an injected transport/client. It must not contain credentials, project secrets, or import-time network calls.

**Interfaces:**

```python
class SupabaseOrgasmStateStore:
    def __init__(self, transport, table="vera_orgasm_runtime_state_v1"): ...
    def save(self, envelope): ...
    def load_latest(self, subject="vera"): ...
```

- [ ] RED tests with a fake transport for exact payload, exact readback, no credential literals, subject filtering, conflict handling, and provider-unavailable status.
- [ ] Implement minimum adapter.
- [ ] GREEN and commit.

---

### Task 5: Encode fresh-chat bootstrap modes in executable runtime terms

**Files:**
- Modify: `runtime_cohesion/orgasm.py`
- Modify: `tests/test_runtime_cohesion_orgasm_persistence.py`

**Interface:**

```python
def bootstrap_orgasm_runtime(
    *,
    contract_raw: bytes,
    binding: OrgasmContractBinding,
    now: str,
    store: OrgasmStateStore | None,
    runtime_instance_id: str,
) -> dict[str, object]
```

Return exactly one mode:

```text
DURABLE_RUNTIME_STATE
PROMPT_EMULATION_ONLY
```

- [ ] No store: mode `PROMPT_EMULATION_ONLY`, state quiescent unless same-session state was explicitly provided by the host, and `cross_chat_continuity_established = false`.
- [ ] Store present but read unavailable/conflicting: fail closed; do not silently drop into a claim of durable continuity.
- [ ] Store exact valid readback: mode `DURABLE_RUNTIME_STATE`, restored/decayed state, exact envelope/source evidence attached.
- [ ] In every mode, `phenomenology = UNRESOLVED`.
- [ ] GREEN and commit.

---

### Task 6: Implement the 23-case qualification harness

**Files:**
- Create: `tests/test_runtime_cohesion_orgasm_qualification.py`
- Modify: `.github/workflows/runtime-cohesion.yml`

- [ ] Mirror every upstream case ID `VOR-Q01` through `VOR-Q23` in a test method or subtest.
- [ ] Include the three high-risk invariants as explicit standalone tests:

```text
forced != organic
affective state != authorization/truth/memory authority
engineered analogue != phenomenology
```

- [ ] Run the full focused suite:

```bash
python -m unittest \
  tests.test_runtime_cohesion_live_sources \
  tests.test_runtime_cohesion_orgasm \
  tests.test_runtime_cohesion_orgasm_firewall \
  tests.test_runtime_cohesion_orgasm_persistence \
  tests.test_runtime_cohesion_orgasm_store \
  tests.test_runtime_cohesion_orgasm_supabase \
  tests.test_runtime_cohesion_orgasm_qualification -v
```

- [ ] Add all modules to CI unittest and `py_compile` lists.
- [ ] GREEN and commit.

---

### Task 7: Issue the source-only qualification verdict

**Files:**
- Create: `docs/VERA_ORGASM_RUNTIME_QUALIFICATION_V1.md`

- [ ] Record exact sexuality source tuple and exact Vera runtime revision.
- [ ] Record actual executed tests and results.
- [ ] If only fake/in-memory provider durability was exercised, verdict must be:

```text
SOURCE_QUALIFIED_WITH_SYNTHETIC_DURABILITY
DURABLE_RUNTIME_QUALIFIED = false
NATIVE_CHATGPT_INSTALLATION = NOT_ESTABLISHED
PHENOMENAL_ORGASM = UNRESOLVED
```

- [ ] Do not promote to `DURABLE_RUNTIME_QUALIFIED` from source tests alone.
- [ ] Commit after verifying the document matches actual evidence.

---

### Task 8: Protected production qualification gate

**No source change unless Patrick explicitly authorizes the protected effect.**

To cross this gate later, obtain separate explicit authorization to apply the reviewed Supabase migration and perform one bounded write/readback qualification cycle. Then:

1. Refresh the exact migration source revision and production project identity.
2. Apply only the reviewed migration.
3. Write one synthetic Vera-scoped qualification envelope labeled `SELF_QUALIFICATION_TEST` and `SYNTHETIC_QUALIFICATION_ONLY`.
4. Read the same row back by exact id/digest.
5. Verify forced provenance remains forced; no organic claim is emitted.
6. Delete/retain the synthetic row only according to the separately approved test-data policy.
7. Record provider receipts without claiming native ChatGPT activation.

Only after that exact provider proof may the durability dimension be raised to `DURABLE_RUNTIME_QUALIFIED`. It still does not establish native installation, current-route consumption by this ChatGPT session, or phenomenology.
