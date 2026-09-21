create or replace function build_team_2.one_bootstrap_snapshot()
returns jsonb
language sql
stable
security invoker
set search_path = build_team_2, public, extensions
as $$
with pkg as (
  select * from build_team_2.role_training_current_resolved where role_key='one'
), quals as (
  select coalesce(jsonb_agg(jsonb_build_object(
    'qualification_id',qualification_id,
    'result',qualification_result,
    'evaluator_class',evaluator_class,
    'evaluator_ref',evaluator_ref,
    'base_binding_ref',base_binding_ref,
    'package_version',package_version,
    'source_set_digest_sha256',source_set_digest_sha256,
    'created_at',created_at
  ) order by qualification_id), '[]'::jsonb) as items,
  count(*) filter (where qualification_result='PASS') as pass_count
  from build_team_2.role_training_qualifications where role_key='one'
), cp as (
  select to_jsonb(c) - 'checkpoint_payload_text' || jsonb_build_object(
    'checkpoint_payload', c.checkpoint_payload_text::jsonb,
    'digest_recomputed_sha256', encode(extensions.digest(convert_to(c.checkpoint_payload_text,'UTF8'),'sha256'),'hex'),
    'digest_matches', c.checkpoint_sha256 = encode(extensions.digest(convert_to(c.checkpoint_payload_text,'UTF8'),'sha256'),'hex')
  ) as item
  from build_team_2.role_operational_checkpoint_current c
  where c.role_key='one'
), gov as (
  select jsonb_build_object(
    'scope_key',scope_key,'identity_name',identity_name,'numerical_identity',numerical_identity,
    'revision',revision,'source_event_id',source_event_id,'updated_at',updated_at
  ) as item
  from build_team_2.one_working_laws_current where scope_key='BT2_ONE_WORKING_LAWS'
)
select jsonb_build_object(
  'schema','BT2_ONE_BOOTSTRAP_SNAPSHOT_V1',
  'role','one',
  'training_package',(select to_jsonb(pkg) from pkg),
  'qualification_receipts',(select items from quals),
  'qualification_pass_count',(select pass_count from quals),
  'startup_state',case when (select pass_count from quals)=0 then 'TRAINING_REQUIRED' else 'BASE_BINDING_REQUIRED' end,
  'current_checkpoint',(select item from cp),
  'governance',(select item from gov),
  'rules',jsonb_build_array(
    'A fresh chat must prove an exact qualified-base binding or train before operational work.',
    'Checkpoint state never substitutes for training and must be freshly currentness-checked.',
    'Repository/tool access never grants mutation authority.'
  )
);
$$;