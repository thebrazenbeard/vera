begin;

-- Pin trigger-function namespace resolution. Both functions are non-SECURITY
-- DEFINER, but a mutable caller search_path is still unnecessary ambiguity and
-- is flagged by the provider security advisor.

alter function build_team_2.reject_training_history_mutation()
  set search_path = pg_catalog, build_team_2;

alter function build_team_2.validate_checkpoint_qualification_binding()
  set search_path = pg_catalog, build_team_2;

commit;
