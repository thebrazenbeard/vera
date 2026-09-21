do $block$
declare
  v_voss_open integer;
  v_coord text;
  v_rev bigint;
  v_voss_active boolean;
  v_one_active boolean;
begin
  select coordinator_role, role_registry_revision into v_coord, v_rev
    from bug_ops.system_config where singleton=true for update;
  if v_coord <> 'VOSS' or v_rev <> 1 then
    raise exception 'BUG_OPS_CONFIG_PRECONDITION_FAILED coordinator %, revision %', v_coord, v_rev;
  end if;

  select active into v_voss_active from bug_ops.role_registry where role_key='VOSS';
  select active into v_one_active from bug_ops.role_registry where role_key='ONE';
  if coalesce(v_voss_active,false) is not true then
    raise exception 'VOSS_ROLE_PRECONDITION_FAILED';
  end if;
  if coalesce(v_one_active,false) is not true then
    raise exception 'ONE_ROLE_NOT_ACTIVE';
  end if;

  select count(*) into v_voss_open
    from bug_ops.bug_reports
    where assigned_role='VOSS' and status <> 'CLOSED';
  if v_voss_open <> 0 then
    raise exception 'VOSS_HAS_UNROUTED_OPEN_BUGS %', v_voss_open;
  end if;

  update bug_ops.system_config
     set coordinator_role='ONE', role_registry_revision=2
   where singleton=true;

  alter table bug_ops.role_registry disable trigger role_registry_immutable_v1;
  update bug_ops.role_registry
     set active = case when role_key='VOSS' then false else active end,
         registry_revision=2,
         updated_at=clock_timestamp();
  alter table bug_ops.role_registry enable trigger role_registry_immutable_v1;

  if exists(select 1 from bug_ops.role_registry where role_key='VOSS' and active) then
    raise exception 'VOSS_DEACTIVATION_FAILED';
  end if;
end
$block$;