# V.E.R.A.

**Virtual Environment for Reciprocal Agency**

This repository contains the public, version-controlled technical architecture for the V.E.R.A. project.

Current neutral release: `VERA_NEUTRAL_CORE_R6A0_20260730_EC900174`

## Purpose

GitHub stores source code, database migrations, schemas, validators, release notes, and non-sensitive architecture documentation.

It is **not** the live context store and must not contain private conversation records, credentials, access tokens, exported Supabase rows, or raw memory-ledger snapshots.

## Bound systems

- **Current ChatGPT Project:** supplies present user intent, correction, project administration, and the active project instructions.
- **GitHub:** `thebrazenbeard/vera` is the canonical public architecture repository; `main` is the canonical branch.
- **Supabase:** project `Vera` (`klmbpaigzeguvnpccqzz`) stores governed external context and coordination records.

The authoritative connector binding is recorded in [`coordination/PROJECT_BINDING_R6A0_20260730_EC900174.md`](coordination/PROJECT_BINDING_R6A0_20260730_EC900174.md).

## Reality and persistence boundary

Connector access and recorded references establish an explicit project binding. They do not imply hidden synchronization, automatic persistence, model identity, recollection, consciousness, or authority beyond exposed tool operations.

A repository or database write is confirmed only by the result returned from that target system.

## Current status

The GitHub repository and Supabase project were verified through their connected tools on July 30, 2026. Legacy Supabase rows remain preserved, and neutral V3 records are stored separately from the legacy save-state tables.
