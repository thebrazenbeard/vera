# TUL Instrumented Host Fixture v0.1

A local, host-controlled proof fixture for the frozen and independently approved **TUL Host Capability Requirement v0.1.3**.

## What it proves

The fixture demonstrates that a host under our control can:

1. create an inbound message event with `MESSAGE_CREATION` semantics and `TRUSTED_BRIDGE` source;
2. capture `GENERATION_INVOCATION_START` immediately before invoking a model callable using `HOST_RUNTIME_CLOCK`;
3. inject the inbound and generation evidence into the model call;
4. create the resulting assistant message event with `MESSAGE_CREATION` semantics after output exists;
5. bind all three events to the same inbound message reference;
6. pass the events through a strict host-neutral adapter and elapsed calculator;
7. preserve `UNAVAILABLE` or `CONFLICTED` when evidence is absent or internally inconsistent.

## What it does not prove

It does **not** prove that ordinary ChatGPT or Codex exposes equivalent lifecycle hooks or authoritative per-message timestamps. Native ChatGPT/Codex support remains **UNPROVEN**.

It does not use or modify:

- Supabase
- Memory Ledger
- PR #3
- deployment or production systems
- signed owners
- semantic memory
- persistent storage

## Reproduce

Run these commands from the repository checkout:

```bash
cd experiments/tul_instrumented_host_fixture_v0_1
python -m pip install --no-build-isolation -e '.[test]'
python -m pytest -v
python scripts/generate_proof.py
python scripts/generate_manifest.py
python scripts/verify_manifest.py
```

The editable install resolves `tul_fixture` from repository-root `src` through the package configuration. The manifest covers this experiment directory and `src/tul_fixture`. It excludes virtual environments, caches, bytecode, package metadata, and build outputs so local tooling debris cannot alter the integrity boundary.

## Design note

The fixture owns its message lifecycle. Its inbound and assistant creation timestamps are therefore labeled `TRUSTED_BRIDGE`, not `PLATFORM_MESSAGE_METADATA`. The proof is a controlled-host capability proof, not a claim about ChatGPT's private runtime.
