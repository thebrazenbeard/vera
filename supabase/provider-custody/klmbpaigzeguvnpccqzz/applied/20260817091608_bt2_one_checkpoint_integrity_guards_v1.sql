do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conname='role_operational_checkpoints_payload_digest_ck'
      and conrelid='build_team_2.role_operational_checkpoints'::regclass
  ) then
    alter table build_team_2.role_operational_checkpoints
      add constraint role_operational_checkpoints_payload_digest_ck
      check (checkpoint_sha256 = encode(digest(convert_to(checkpoint_payload_text,'UTF8'),'sha256'),'hex'));
  end if;

  if not exists (
    select 1 from pg_constraint
    where conname='role_operational_checkpoints_payload_binding_ck'
      and conrelid='build_team_2.role_operational_checkpoints'::regclass
  ) then
    alter table build_team_2.role_operational_checkpoints
      add constraint role_operational_checkpoints_payload_binding_ck
      check (
        checkpoint_payload_text::jsonb ->> 'schema' = checkpoint_schema
        and checkpoint_payload_text::jsonb ->> 'role_key' = role_key
        and checkpoint_payload_text::jsonb #>> '{training_binding,version}' = training_package_version
        and checkpoint_payload_text::jsonb #>> '{training_binding,source_set_digest_sha256}' = training_source_set_digest_sha256
      );
  end if;
end $$;