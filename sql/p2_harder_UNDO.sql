-- Undo the Nov 16-30 harder tiers: puts back the old functions and the old tier numbers. Affiliate sales rows stay but stop counting.
do $undo$
declare v_def text;
begin
  if to_regprocedure('app.concepts_in_period_v1(uuid,text)') is null then raise exception 'STOP: nothing to undo'; end if;
  v_def := pg_get_functiondef('app.concepts_in_period_v1(uuid,text)'::regprocedure);
  execute replace(v_def, 'FUNCTION app.concepts_in_period_v1(', 'FUNCTION app.concepts_in_period(');
  v_def := pg_get_functiondef('app.sales_in_period_v1(uuid,text)'::regprocedure);
  execute replace(v_def, 'FUNCTION app.sales_in_period_v1(', 'FUNCTION app.sales_in_period(');
  update app.milestones m set sales_required_cents = b.sales_required_cents from app.milestones_backup_1116 b where b.id = m.id;
end $undo$;
select 'Nov 16-30 tiers back to the old rules' as result;
