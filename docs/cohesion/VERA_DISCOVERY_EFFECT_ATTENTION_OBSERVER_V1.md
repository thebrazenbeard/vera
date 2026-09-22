# Vera Discovery Effect Attention Observer V1

Status: **SOURCE EXPERIMENT / READ-ONLY COORDINATION VIEW / NOT RUNTIME ACTIVATED**

This experiment is stacked on Vera PR #136, whose current source registry already
classifies Discovery as a non-authoritative portfolio meta-source.

The observer exists to answer one bounded coordination question:

> Which producer-selected latest effect records require human/coordinator attention?

It does **not** answer what Vera should execute next.

## Exact contract

The vendored schema is byte-identical to Discovery's experimental V0 contract:

- Discovery PR #12 head:
  `bf0fc4fb96e27a65da8d26293c29ebeeffc10b64`
- source path:
  `schemas/effect_attempt_envelope_v0.schema.json`
- Git blob:
  `b5d85ba31a33ad7192fd4a08934628a72e593312`

The schema is vendored only so Vera's source experiment can validate exact
envelope structure without a runtime dependency on Discovery.

The repository also pins the vendored schema path with:

`architecture/discovery/effect_attempt_envelope_v0.schema.json -text`

in `.gitattributes`. This deliberately disables Git text/EOL conversion for that
one JSON artifact so Windows and Linux working-tree bytes remain the committed Git
blob bytes. The loader therefore keeps its literal exact-byte contract rather than
silently normalizing CRLF/LF differences.

## Independent observer

`runtime_cohesion/effect_attention.py` is not exported through
`runtime_cohesion.__init__` and is not called by Cohesion execution,
inference, provider admission, affect, SD1, or control code.

It treats `source_state` as opaque.

Its only cross-source semantics are those already normalized by V0:

- `normalized_phase`
- `retry_disposition`

The output is an observational attention report containing unresolved,
attention-required, verified/reconciled, terminal-failure, and do-not-retry
groupings.

No grouping is an instruction.

## Why this is an independent second observer

Discovery's first observer asks for a generic portfolio summary.

Vera's observer asks a different operational question: which already-normalized
records deserve coordinator attention while preserving producer-native authority.

The implementation is independently written and does not import Discovery's
observer.

Tests require the same path to accept the three currently qualified producers
and an unknown future producer without registration or source-specific branches.

## Claim ceiling

A PASS can establish a second independent downstream consumer of the neutral
contract.

It cannot establish:

- runtime activation;
- Vera self-state;
- control authority;
- retry authority;
- target authority;
- net maintenance savings;
- `PROVEN_REUSABLE`;
- justification for a shared runtime library.
