create or replace function bug_ops.report_bug_deprecated_initial_v1(
  p_operation_id uuid,p_intake_key text,p_title text,p_description text default '',p_severity text default 'MEDIUM',p_component text default null,p_reported_by text default null,p_assigned_role text default null,p_evidence jsonb default '{}'::jsonb
) returns table(out_bug_id uuid,out_event_id uuid,out_state_version bigint,out_routing_revision bigint,out_queue_name text,out_queue_msg_id bigint,idempotent_replay boolean)
language plpgsql set search_path='' as $$ begin raise exception 'BUG_OPS_DEPRECATED_API'; end $$;

create or replace function bug_ops.route_bug_deprecated_initial_v1(
  p_operation_id uuid,p_bug_id uuid,p_expected_state_version bigint,p_expected_routing_revision bigint,p_target_role text,p_actor text default null,p_reason text default null
) returns table(out_bug_id uuid,out_event_id uuid,out_state_version bigint,out_routing_revision bigint,out_queue_name text,out_queue_msg_id bigint,idempotent_replay boolean)
language plpgsql set search_path='' as $$ begin raise exception 'BUG_OPS_DEPRECATED_API'; end $$;

create or replace function bug_ops.update_bug_status_deprecated_initial_v1(
  p_operation_id uuid,p_bug_id uuid,p_expected_state_version bigint,p_status text,p_actor text default null,p_note text default null
) returns table(out_bug_id uuid,out_event_id uuid,out_state_version bigint,out_routing_revision bigint,idempotent_replay boolean)
language plpgsql set search_path='' as $$ begin raise exception 'BUG_OPS_DEPRECATED_API'; end $$;

create or replace function bug_ops.claim_work_deprecated_initial_v1(
  p_role text,p_visibility_seconds integer default 300,p_qty integer default 10
) returns table(msg_id bigint,read_ct integer,enqueued_at timestamptz,vt timestamptz,message jsonb,headers jsonb,bug_id uuid,state_version bigint,routing_revision bigint,target_role text)
language plpgsql set search_path='' as $$ begin raise exception 'BUG_OPS_DEPRECATED_API'; end $$;

create or replace function bug_ops.ack_work_deprecated_initial_v1(
  p_role text,p_msg_id bigint,p_handled_event_id uuid,p_note text default null
) returns uuid
language plpgsql set search_path='' as $$ begin raise exception 'BUG_OPS_DEPRECATED_API'; end $$;

create or replace function bug_ops.archive_dispatch_internal_deprecated_initial_v1(
  p_queue text,p_msg_id bigint,p_classification text,p_message jsonb,p_bug_id uuid,p_source_event_id uuid,p_handled_event_id uuid,p_note text
) returns uuid
language plpgsql set search_path='' as $$ begin raise exception 'BUG_OPS_DEPRECATED_API'; end $$;

create or replace function bug_ops.ack_work_pre_claim_generation_cas(
  p_role text,p_msg_id bigint,p_dispatch_id uuid,p_handled_event_id uuid,p_note text default null
) returns uuid
language plpgsql set search_path='' as $$ begin raise exception 'BUG_OPS_DEPRECATED_API'; end $$;

revoke execute on function bug_ops.report_bug_deprecated_initial_v1(uuid,text,text,text,text,text,text,text,jsonb) from postgres;
revoke execute on function bug_ops.route_bug_deprecated_initial_v1(uuid,uuid,bigint,bigint,text,text,text) from postgres;
revoke execute on function bug_ops.update_bug_status_deprecated_initial_v1(uuid,uuid,bigint,text,text,text) from postgres;
revoke execute on function bug_ops.claim_work_deprecated_initial_v1(text,integer,integer) from postgres;
revoke execute on function bug_ops.ack_work_deprecated_initial_v1(text,bigint,uuid,text) from postgres;
revoke execute on function bug_ops.archive_dispatch_internal_deprecated_initial_v1(text,bigint,text,jsonb,uuid,uuid,uuid,text) from postgres;
revoke execute on function bug_ops.ack_work_pre_claim_generation_cas(text,bigint,uuid,uuid,text) from postgres;