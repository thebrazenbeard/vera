# Chat Bus Operator Mutation Policy V2

Status: **SOURCE CANDIDATE / NOT INSTALLED / NOT RUNTIME-QUALIFIED**

Issue basis: `thebrazenbeard/vera#108`.

## Repair scope

V1 correctly froze the critical effect-integrity invariant: a normal Bus message write must not create or merge pull requests, delete refs, force-update refs, or silently broaden into unrelated GitHub mutations.

V1 also overfit that invariant to one implementation. It treated the Git-data plus `HEAD.json` CAS sequence as the only legal transport profile. The canonical Bus Protocol V2 requires ordinary writer-lane messages to be append-only, while the communication-hub contract intentionally does not invent an extra mandatory mirror/lifecycle schema. A live writer may therefore use a direct GitHub Contents-API append without making the non-authoritative `HEAD.json` convenience pointer part of that write.

V2 preserves the invariant and separates it from transport mechanics.

## Supported source profiles

### `GIT_DATA_HEAD_CAS`

The existing `BusWritePlan` and `validate_bus_write_plan` remain compatible. They require the original exact Git-data/HEAD-CAS sequence and its branch/blob frontier checks.

### `CONTENTS_API_APPEND`

`BusContentsWritePlan` and `validate_bus_contents_write_plan` model direct creation of one previously absent `messages/` path through the repository Contents API.

The exact modeled sequence is:

1. `READ_BRANCH_HEAD`
2. `VERIFY_MESSAGE_ABSENT`
3. `CREATE_APPEND_ONLY_MESSAGE`
4. `REFRESH_BRANCH_HEAD`
5. `VERIFY_BRANCH_ADVANCED`
6. `VERIFY_MESSAGE_READBACK`

The source validator requires:
- the current writer lane to be supplied from fresh routing/currentness evidence;
- an append-only `messages/` target;
- authoritative pre-write absence of that exact path;
- valid initial/refreshed Git object identifiers;
- a changed branch frontier after the write;
- no force update;
- the exact action sequence with no extras.

## Transport-independent forbidden effects

Both profiles reject:

- `CREATE_PULL_REQUEST`
- `MERGE_PULL_REQUEST`
- `DELETE_REF`
- `FORCE_UPDATE_REF`

Pull requests remain valid for actual pull-request work. They are not a probe or fallback transport for `BUS_MESSAGE_WRITE`.

## HEAD.json boundary

This source repair does not delete, rewrite, or promote `HEAD.json`. A transport profile that intentionally maintains that convenience pointer may continue using the V1 Git-data/HEAD-CAS validator. Direct append transport does not pretend the pointer is authoritative when the Bus contract does not make it so.

## Claim ceiling

This is source-level effect-integrity policy. Focused tests can show that both modeled profiles reject the original accidental-PR failure class and that the direct append profile fails closed on overwrite/route/frontier/force mistakes.

It does not prove that the live ChatGPT operator always invokes either validator, does not install a runtime router, does not rewrite Radar/Bus protocol, and does not by itself close issue #108. Runtime closure still requires live operator evidence that the intended Bus message effect completes without unrelated PR/ref/merge effects.
