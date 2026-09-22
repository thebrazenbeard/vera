create or replace function bug_ops.report_bug(
  p_operation_id uuid,
  p_intake_key text,
  p_title text,
  p_description text default ''::text,
  p_severity text default 'MEDIUM'::text,
  p_component text default null::text,
  p_reported_by text default null::text,
  p_assigned_role text default null::text,
  p_evidence jsonb default '{}'::jsonb
)
returns table(
  out_bug_id uuid,
  out_event_id uuid,
  out_state_version bigint,
  out_dispatch_revision bigint,
  out_dispatch_id uuid,
  out_queue_msg_id bigint,
  idempotent_replay boolean
)
language plpgsql
set search_path to ''
as $function$
declare
  cfg bug_ops.system_config%rowtype;
  v_role text;
  v_payload jsonb;
  v_digest text;
  rcpt bug_ops.operation_receipts%rowtype;
  ev bug_ops.bug_events%rowtype;
  br bug_ops.bug_reports%rowtype;
  enq bug_ops.dispatch_events_v2%rowtype;
  v_bug uuid:=gen_random_uuid();
  v_event uuid:=gen_random_uuid();
  v_dispatch uuid:=gen_random_uuid();
  v_msg bigint;
  v_snapshot jsonb;
  v_pdigest text;
  v_result jsonb;
  v_result_digest text;
  v_sev text:=upper(btrim(p_severity));
  v_key text:=btrim(p_intake_key);
  v_title text:=btrim(p_title);
  inserted_id uuid;
  v_frozen jsonb;
begin
  perform pg_advisory_xact_lock(hashtextextended(p_operation_id::text,0));

  -- Historical replay is resolved before mutable current routing policy.
  select * into rcpt from bug_ops.operation_receipts r where r.operation_id=p_operation_id;
  if found then
    if rcpt.operation_kind<>'REPORT' then raise exception 'OPERATION_ID_REUSE_CONFLICT'; end if;
    select e.request_payload into v_frozen
      from bug_ops.bug_events e
      where e.event_id=rcpt.controlling_event_id and e.event_type='REPORTED';
    if v_frozen is null then raise exception 'OPERATION_RECEIPT_SOURCE_EVENT_MISSING'; end if;

    if coalesce(v_frozen->>'kind','') <> 'REPORT'
       or coalesce(v_frozen->>'intake_key','') <> coalesce(v_key,'')
       or coalesce(v_frozen->>'title','') <> coalesce(v_title,'')
       or coalesce(v_frozen->>'description','') <> coalesce(p_description,'')
       or coalesce(v_frozen->>'severity','') <> coalesce(v_sev,'')
       or coalesce(v_frozen->'component','null'::jsonb) <> coalesce(to_jsonb(p_component),'null'::jsonb)
       or coalesce(v_frozen->'reported_by','null'::jsonb) <> coalesce(to_jsonb(p_reported_by),'null'::jsonb)
       or coalesce(v_frozen->'evidence','{}'::jsonb) <> coalesce(p_evidence,'{}'::jsonb)
       or (p_assigned_role is not null and coalesce(v_frozen->>'assigned_role','') <> upper(btrim(p_assigned_role)))
    then
      raise exception 'OPERATION_ID_REUSE_CONFLICT';
    end if;

    return query select
      (rcpt.result_payload->>'bug_id')::uuid,
      (rcpt.result_payload->>'event_id')::uuid,
      (rcpt.result_payload->>'state_version')::bigint,
      (rcpt.result_payload->>'dispatch_revision')::bigint,
      (rcpt.result_payload->>'dispatch_id')::uuid,
      (rcpt.result_payload->>'queue_msg_id')::bigint,
      true;
    return;
  end if;

  select * into cfg from bug_ops.system_config where singleton=true;
  v_role:=coalesce(upper(nullif(btrim(p_assigned_role),'')),cfg.coordinator_role);
  if bug_ops.queue_for_role(v_role) is null then raise exception 'INVALID_TARGET_ROLE'; end if;
  if v_key is null or length(v_key)=0 then raise exception 'INVALID_INTAKE_KEY'; end if;
  if v_title is null or length(v_title)=0 then raise exception 'INVALID_TITLE'; end if;
  if v_sev not in ('LOW','MEDIUM','HIGH','CRITICAL') then raise exception 'INVALID_SEVERITY'; end if;
  if jsonb_typeof(coalesce(p_evidence,'{}'::jsonb))<>'object' then raise exception 'INVALID_EVIDENCE'; end if;

  v_payload:=jsonb_build_object(
    'kind','REPORT','home_project',cfg.project_key,'intake_key',v_key,'title',v_title,
    'description',coalesce(p_description,''),'severity',v_sev,'component',p_component,
    'reported_by',p_reported_by,'assigned_role',v_role,'evidence',coalesce(p_evidence,'{}'::jsonb)
  );
  v_digest:=bug_ops.sha256_jsonb(v_payload);

  insert into bug_ops.bug_reports(
    bug_id,home_project,intake_key,intake_digest,title,description,severity,status,component,
    reported_by,assigned_role,state_version,routing_revision,dispatch_revision,evidence
  ) values(
    v_bug,cfg.project_key,v_key,v_digest,v_title,coalesce(p_description,''),v_sev,'NEW',p_component,
    p_reported_by,v_role,1,1,1,coalesce(p_evidence,'{}'::jsonb)
  ) on conflict(intake_key) do nothing returning bug_id into inserted_id;

  if inserted_id is null then
    select * into br from bug_ops.bug_reports where intake_key=v_key;
    if br.intake_digest<>v_digest then raise exception 'INTAKE_KEY_REUSE_CONFLICT'; end if;
    select * into ev from bug_ops.bug_events e where e.bug_id=br.bug_id and e.event_type='REPORTED' order by e.state_version limit 1;
    if not found then raise exception 'INTAKE_CANONICAL_EVENT_MISSING'; end if;
    select * into enq from bug_ops.dispatch_events_v2 d where d.dispatch_id=ev.dispatch_id and d.event_type='ENQUEUED';
    v_result:=jsonb_build_object(
      'bug_id',br.bug_id,'event_id',ev.event_id,'state_version',ev.state_version,
      'dispatch_revision',ev.dispatch_revision,'dispatch_id',ev.dispatch_id,
      'queue_msg_id',case when enq.dispatch_event_id is null then null else enq.msg_id end
    );
    v_result_digest:=bug_ops.sha256_jsonb(v_result);
    insert into bug_ops.operation_receipts(operation_id,request_digest,operation_kind,bug_id,controlling_event_id,result_payload,result_digest)
    values(p_operation_id,v_digest,'REPORT',br.bug_id,ev.event_id,v_result,v_result_digest);
    return query select br.bug_id,ev.event_id,ev.state_version,ev.dispatch_revision,ev.dispatch_id,
      case when enq.dispatch_event_id is null then null::bigint else enq.msg_id end,true;
    return;
  end if;

  v_snapshot:=jsonb_build_object(
    'dispatch_id',v_dispatch,'bug_id',v_bug,'home_project',cfg.project_key,'event_id',v_event,
    'state_version',1,'dispatch_revision',1,'target_role',v_role,'action','BUG_REPORTED','operation_id',p_operation_id
  );
  v_pdigest:=bug_ops.sha256_jsonb(v_snapshot);
  insert into bug_ops.bug_events(
    event_id,bug_id,state_version,routing_revision,dispatch_revision,event_type,actor,operation_id,
    request_digest,request_payload,details,dispatch_id,dispatch_snapshot,dispatch_payload_digest
  ) values(
    v_event,v_bug,1,1,1,'REPORTED',p_reported_by,p_operation_id,v_digest,v_payload,
    jsonb_build_object('assigned_role',v_role),v_dispatch,v_snapshot,v_pdigest
  );
  select s into v_msg from pgmq.send('bug_dispatch',v_snapshot,0) s limit 1;
  insert into bug_ops.dispatch_events_v2(
    dispatch_id,queue_name,msg_id,event_type,bug_id,bug_event_id,target_role,payload_digest,observed_message
  ) values(v_dispatch,'bug_dispatch',v_msg,'ENQUEUED',v_bug,v_event,v_role,v_pdigest,v_snapshot);
  v_result:=jsonb_build_object(
    'bug_id',v_bug,'event_id',v_event,'state_version',1,'dispatch_revision',1,
    'dispatch_id',v_dispatch,'queue_msg_id',v_msg
  );
  v_result_digest:=bug_ops.sha256_jsonb(v_result);
  insert into bug_ops.operation_receipts(operation_id,request_digest,operation_kind,bug_id,controlling_event_id,result_payload,result_digest)
  values(p_operation_id,v_digest,'REPORT',v_bug,v_event,v_result,v_result_digest);
  return query select v_bug,v_event,1::bigint,1::bigint,v_dispatch,v_msg,false;
end
$function$;

create or replace function bug_ops.route_bug(
  p_operation_id uuid,
  p_bug_id uuid,
  p_expected_state_version bigint,
  p_expected_dispatch_revision bigint,
  p_target_role text,
  p_actor text default null::text,
  p_reason text default null::text
)
returns table(
  out_bug_id uuid,
  out_event_id uuid,
  out_state_version bigint,
  out_dispatch_revision bigint,
  out_dispatch_id uuid,
  out_queue_msg_id bigint,
  idempotent_replay boolean
)
language plpgsql
set search_path to ''
as $function$
declare
  br bug_ops.bug_reports%rowtype;
  rcpt bug_ops.operation_receipts%rowtype;
  v_role text:=upper(btrim(p_target_role));
  v_payload jsonb;
  v_digest text;
  v_event uuid:=gen_random_uuid();
  v_dispatch uuid:=gen_random_uuid();
  v_msg bigint;
  v_state bigint;
  v_dispatch_rev bigint;
  v_routing bigint;
  v_snapshot jsonb;
  v_pdigest text;
  v_result jsonb;
  v_result_digest text;
  v_frozen jsonb;
begin
  perform pg_advisory_xact_lock(hashtextextended(p_operation_id::text,0));

  -- Historical replay is resolved before mutable current routing policy.
  select * into rcpt from bug_ops.operation_receipts r where r.operation_id=p_operation_id;
  if found then
    if rcpt.operation_kind<>'ROUTE' then raise exception 'OPERATION_ID_REUSE_CONFLICT'; end if;
    select e.request_payload into v_frozen
      from bug_ops.bug_events e
      where e.event_id=rcpt.controlling_event_id and e.event_type='ROUTED';
    if v_frozen is null then raise exception 'OPERATION_RECEIPT_SOURCE_EVENT_MISSING'; end if;

    if coalesce(v_frozen->>'kind','') <> 'ROUTE'
       or coalesce((v_frozen->>'bug_id')::uuid,'00000000-0000-0000-0000-000000000000'::uuid) <> p_bug_id
       or coalesce((v_frozen->>'expected_state_version')::bigint,-1) <> p_expected_state_version
       or coalesce((v_frozen->>'expected_dispatch_revision')::bigint,-1) <> p_expected_dispatch_revision
       or coalesce(v_frozen->>'target_role','') <> v_role
       or coalesce(v_frozen->'actor','null'::jsonb) <> coalesce(to_jsonb(p_actor),'null'::jsonb)
       or coalesce(v_frozen->'reason','null'::jsonb) <> coalesce(to_jsonb(p_reason),'null'::jsonb)
    then
      raise exception 'OPERATION_ID_REUSE_CONFLICT';
    end if;

    return query select
      (rcpt.result_payload->>'bug_id')::uuid,
      (rcpt.result_payload->>'event_id')::uuid,
      (rcpt.result_payload->>'state_version')::bigint,
      (rcpt.result_payload->>'dispatch_revision')::bigint,
      (rcpt.result_payload->>'dispatch_id')::uuid,
      (rcpt.result_payload->>'queue_msg_id')::bigint,
      true;
    return;
  end if;

  if bug_ops.queue_for_role(v_role) is null then raise exception 'INVALID_TARGET_ROLE'; end if;
  v_payload:=jsonb_build_object(
    'kind','ROUTE','home_project','VERA','bug_id',p_bug_id,
    'expected_state_version',p_expected_state_version,'expected_dispatch_revision',p_expected_dispatch_revision,
    'target_role',v_role,'actor',p_actor,'reason',p_reason
  );
  v_digest:=bug_ops.sha256_jsonb(v_payload);

  select * into br from bug_ops.bug_reports b where b.bug_id=p_bug_id for update;
  if not found then raise exception 'BUG_NOT_FOUND'; end if;
  if br.state_version<>p_expected_state_version then raise exception 'STALE_STATE_VERSION expected %, actual %',p_expected_state_version,br.state_version; end if;
  if br.dispatch_revision<>p_expected_dispatch_revision then raise exception 'STALE_DISPATCH_REVISION expected %, actual %',p_expected_dispatch_revision,br.dispatch_revision; end if;
  if br.status='CLOSED' then raise exception 'BUG_CLOSED'; end if;

  v_state:=br.state_version+1;
  v_dispatch_rev:=br.dispatch_revision+1;
  v_routing:=br.routing_revision+1;
  v_snapshot:=jsonb_build_object(
    'dispatch_id',v_dispatch,'bug_id',p_bug_id,'home_project',br.home_project,'event_id',v_event,
    'state_version',v_state,'dispatch_revision',v_dispatch_rev,'target_role',v_role,
    'action','ROUTE','operation_id',p_operation_id
  );
  v_pdigest:=bug_ops.sha256_jsonb(v_snapshot);
  insert into bug_ops.bug_events(
    event_id,bug_id,state_version,routing_revision,dispatch_revision,event_type,actor,operation_id,
    request_digest,request_payload,details,dispatch_id,dispatch_snapshot,dispatch_payload_digest
  ) values(
    v_event,p_bug_id,v_state,v_routing,v_dispatch_rev,'ROUTED',p_actor,p_operation_id,v_digest,v_payload,
    jsonb_build_object('from_role',br.assigned_role,'to_role',v_role,'reason',p_reason),v_dispatch,v_snapshot,v_pdigest
  );
  select s into v_msg from pgmq.send('bug_dispatch',v_snapshot,0) s limit 1;
  insert into bug_ops.dispatch_events_v2(
    dispatch_id,queue_name,msg_id,event_type,bug_id,bug_event_id,target_role,payload_digest,observed_message
  ) values(v_dispatch,'bug_dispatch',v_msg,'ENQUEUED',p_bug_id,v_event,v_role,v_pdigest,v_snapshot);
  update bug_ops.bug_reports set assigned_role=v_role,state_version=v_state,routing_revision=v_routing,
    dispatch_revision=v_dispatch_rev,updated_at=clock_timestamp() where bug_id=p_bug_id;
  v_result:=jsonb_build_object(
    'bug_id',p_bug_id,'event_id',v_event,'state_version',v_state,'dispatch_revision',v_dispatch_rev,
    'dispatch_id',v_dispatch,'queue_msg_id',v_msg
  );
  v_result_digest:=bug_ops.sha256_jsonb(v_result);
  insert into bug_ops.operation_receipts(operation_id,request_digest,operation_kind,bug_id,controlling_event_id,result_payload,result_digest)
  values(p_operation_id,v_digest,'ROUTE',p_bug_id,v_event,v_result,v_result_digest);
  return query select p_bug_id,v_event,v_state,v_dispatch_rev,v_dispatch,v_msg,false;
end
$function$;