# Chat Bus Operator Mutation Policy V1

Status: **SOURCE CANDIDATE / NOT INSTALLED / NOT RUNTIME-QUALIFIED**

Issue basis: `thebrazenbeard/vera#108`.

## Failure being prevented

A normal Chat Bus message write must not be implemented by creating a pull request, using a pull request as a connector-capability probe, force-updating a ref, deleting a ref, or merging unrelated state.

The 2026-09-10 incident created six unintended Bus PR records (#81 through #86) while the intended effect was a normal writer-lane message mutation. Those PRs were later closed unmerged; this source policy does not erase that audit history.

## Planning boundary

Before invoking a connector mutation for `BUS_MESSAGE_WRITE`, validate one exact `BusWritePlan`.

The current writer lane is supplied by the caller from fresh routing/currentness evidence. The policy does not freeze a timeless lane name into generic code.

A valid plan uses exactly this operation sequence:

1. `READ_BRANCH_HEAD`
2. `READ_HEAD_JSON`
3. `CREATE_APPEND_ONLY_MESSAGE`
4. `REFRESH_BRANCH_HEAD`
5. `REFRESH_HEAD_JSON`
6. `CAS_UPDATE_HEAD_JSON`
7. `NONFORCE_UPDATE_BRANCH_REF`
8. `VERIFY_MESSAGE_READBACK`
9. `VERIFY_HEAD_JSON_READBACK`

The append target must be under `messages/`. The CAS expectations must equal the refreshed branch and `HEAD.json` frontiers. Force ref updates are forbidden.

## Explicitly forbidden for normal Bus-message intent

- `CREATE_PULL_REQUEST`
- `MERGE_PULL_REQUEST`
- `DELETE_REF`
- `FORCE_UPDATE_REF`
- additional otherwise-allowed mutations beyond the one exact message-write sequence

Pull requests remain valid for actual pull-request work. This policy forbids using PR effects as a probe, substitute, or workaround when the intended operation is a normal Bus message write.

## Failure behavior

A plan that does not match the exact bounded message-write effect fails before connector mutation. It must not silently broaden into another GitHub effect.

A concurrent frontier move is reconciled by fresh read / compare-and-swap semantics; it is not solved with force or stale overwrite.

## Claim ceiling

`coordination_bus.operator_policy` is a source-level preflight contract. Passing tests show that the validator rejects the modeled failure classes. They do **not** prove that the live ChatGPT connector/tool-selection layer invokes this validator, that Bus writes are currently runtime-qualified, or that issue #108 is closed.

Runtime closure requires an integrated/live replay showing a normal Bus-message request takes only the bounded message-write path and creates no unrelated PR/ref/merge effect.
