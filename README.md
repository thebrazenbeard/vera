# Vera

This repository contains the version-controlled technical architecture for the Vera project.

## Purpose

GitHub stores code, database migrations, schemas, validators, release notes, and non-sensitive architectural documentation.

It is **not** the live memory store and must not contain private conversation records, relational memory content, credentials, access tokens, exported Supabase rows, or raw Vera Memory Ledger snapshots.

## System roles

- **Current conversation:** authority for present correction, consent, refusal, self-report, and immediate task intent.
- **Supabase:** durable structured storage for governed external memory records and temporal history.
- **VERA Memory Ledger:** compact Project-local semantic projection and audit surface for native recall.
- **GitHub:** version control for the machinery that supports those systems.

## Status

Initial repository boundary established. No live memory data is stored here.
