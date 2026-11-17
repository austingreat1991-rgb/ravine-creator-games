-- Ravine Creator Games: Nov 16-30 cash tiers get harder (Austin, Nov 16)
-- 1. Every tier needs sales: Trybe sales plus Social Snowball affiliate sales (an affiliate sale counts unless it was refunded).
-- 2. Only approved videos that got ad spend count toward a tier.
-- 3. Nov 1-15 and October are not touched.
-- Paste into a NEW empty Supabase query tab and Run. Set v_test to false to save. With v_test true nothing is saved.
do $p2$
declare
  v_test boolean := false;
  v_def text; v_lang text; v_body text; i1 int; i2 int; n int; v_msg text;
begin
  if not exists (select 1 from app.reward_periods where period_key = '2026-11-P2') then raise exception 'STOP: Nov 16-30 half is missing'; end if;
  if to_regprocedure('app.concepts_in_period(uuid,text)') is null or to_regprocedure('app.sales_in_period(uuid,text)') is null then
    raise exception 'STOP: tier functions are missing'; end if;

  -- keep the old tier numbers so this can be undone
  create table if not exists app.milestones_backup_1116 as select * from app.milestones where period_key = '2026-11-P2';

  -- affiliate sales from Social Snowball (one row per order)
  create table if not exists app.affiliate_sales (
    order_id text primary key,
    creator_id uuid not null,
    affiliate_code text,
    placed_at timestamptz not null,
    amount numeric(12,2) not null,
    refunded boolean not null default false,
    source text not null default 'snowball',
    synced_at timestamptz not null default now());
  alter table app.affiliate_sales enable row level security;
  revoke all on app.affiliate_sales from anon, authenticated;

  create or replace function app.affiliate_cents_in_period(p_identity uuid, p_period text) returns bigint
    language sql stable security definer set search_path to 'app', 'public' as $f$
    select coalesce(round(sum(a.amount) * 100), 0)::bigint
      from app.affiliate_sales a join app.creators c on c.id = a.creator_id join app.reward_periods rp on rp.period_key = p_period
     where c.reward_identity = p_identity and not a.refunded and a.placed_at >= rp.starts_at and a.placed_at < rp.ends_at
  $f$;

  -- keep the current functions as _v1 (only the first time), so older halves keep their exact rules
  if to_regprocedure('app.concepts_in_period_v1(uuid,text)') is null then
    v_def := pg_get_functiondef('app.concepts_in_period(uuid,text)'::regprocedure);
    execute replace(v_def, 'FUNCTION app.concepts_in_period(', 'FUNCTION app.concepts_in_period_v1(');
  end if;
  if to_regprocedure('app.sales_in_period_v1(uuid,text)') is null then
    v_def := pg_get_functiondef('app.sales_in_period(uuid,text)'::regprocedure);
    execute replace(v_def, 'FUNCTION app.sales_in_period(', 'FUNCTION app.sales_in_period_v1(');
  end if;

  -- new videos rule from Nov 16-30 on: the video (or its revision) has ad spend in that half or that month
  select l.lanname into v_lang from pg_proc p join pg_language l on l.oid = p.prolang where p.oid = 'app.concepts_in_period(uuid,text)'::regprocedure;
  if v_lang <> 'sql' then raise exception 'STOP: concepts_in_period is %, expected sql', v_lang; end if;
  v_def := pg_get_functiondef('app.concepts_in_period(uuid,text)'::regprocedure);
  i1 := position('$function$' in v_def); i2 := length(v_def) - position(reverse('$function$') in reverse(v_def)) - 9;
  v_body := $b$
select case when p_period < '2026-11-P2' then app.concepts_in_period_v1(p_identity, p_period) else (
with base as (
  select ac.distinct_key, ac.funnel, cp.unclassified_counts, cp.key ck
    from app.approved_concepts ac
    join app.creators c on c.id = ac.creator_id
    join app.submissions s on s.id = ac.video_id
    join app.reward_periods rp on rp.period_key = p_period
    join app.campaigns cp on cp.key = rp.campaign_key
   where c.reward_identity = p_identity and s.parent_id is null and s.deleted_at is null
     and s.submitted_at >= rp.starts_at and s.submitted_at < rp.ends_at
     and ac.approved_at >= cp.starts_at and ac.approved_at < cp.ends_at
     and exists (select 1 from app.video_metrics vm
                  where vm.spend > 0 and vm.range_key in (rp.period_key, rp.campaign_key)
                    and (vm.submission_id = s.id or vm.submission_id in (select k.id from app.submissions k where k.parent_id = s.id and k.deleted_at is null))))
select ((select count(distinct distinct_key) from base where funnel in ('TOF','MOF') or (funnel is null and unclassified_counts))
      + (select count(distinct distinct_key) from base where funnel = 'BOF' and ck >= '2026-11') / 2)::int) end
$b$;
  execute substr(v_def, 1, i1 + 9) || v_body || substr(v_def, i2 + 1);

  -- new sales rule from Nov 16-30 on: Trybe sales plus affiliate sales
  select l.lanname into v_lang from pg_proc p join pg_language l on l.oid = p.prolang where p.oid = 'app.sales_in_period(uuid,text)'::regprocedure;
  if v_lang <> 'sql' then raise exception 'STOP: sales_in_period is %, expected sql', v_lang; end if;
  v_def := pg_get_functiondef('app.sales_in_period(uuid,text)'::regprocedure);
  i1 := position('$function$' in v_def); i2 := length(v_def) - position(reverse('$function$') in reverse(v_def)) - 9;
  v_body := $b$
select case when p_period < '2026-11-P2' then app.sales_in_period_v1(p_identity, p_period)
            else app.sales_in_period_v1(p_identity, p_period) + app.affiliate_cents_in_period(p_identity, p_period) end
$b$;
  execute substr(v_def, 1, i1 + 9) || v_body || substr(v_def, i2 + 1);

  -- sales needed for each Nov 16-30 tier (dollars x 100); XP and video counts stay the same
  update app.milestones m set sales_required_cents = x.cents
    from (values (0,'Builder',100000),(0,'Operator',250000),(0,'Elite',500000),
                 (1,'Builder',250000),(1,'Operator',500000),(1,'Elite',1000000),
                 (2,'Builder',500000),(2,'Operator',1000000),(2,'Elite',2000000),
                 (3,'Builder',750000),(3,'Operator',1500000),(3,'Elite',3000000),
                 (4,'Builder',1000000),(4,'Operator',2000000),(4,'Elite',4000000)) x(lv, nm, cents)
   where m.period_key = '2026-11-P2' and m.prestige_level = x.lv and m.name = x.nm;
  get diagnostics n = row_count;
  if n <> 15 then raise exception 'STOP: expected 15 Nov 16-30 tiers, updated %', n; end if;

  -- checks: older halves unchanged, new rules in place
  if exists (select 1 from app.reward_periods rp cross join (select distinct reward_identity rid from app.creators where reward_identity is not null) c
              where rp.period_key < '2026-11-P2'
                and (app.concepts_in_period(c.rid, rp.period_key) <> app.concepts_in_period_v1(c.rid, rp.period_key)
                  or app.sales_in_period(c.rid, rp.period_key) <> app.sales_in_period_v1(c.rid, rp.period_key))) then
    raise exception 'STOP: an older half changed'; end if;
  if exists (select 1 from app.milestones where period_key = '2026-11-P2' and published and coalesce(sales_required_cents, 0) = 0) then
    raise exception 'STOP: a Nov 16-30 tier has no sales requirement'; end if;

  select string_agg(format('P%s %s $%s', prestige_level, name, sales_required_cents / 100), ', ' order by prestige_level, sort_order) into v_msg
    from app.milestones where period_key = '2026-11-P2';
  if v_test then raise exception 'TEST OK, nothing saved. Nov 16-30 tiers: %', v_msg; end if;
end $p2$;

select 'Nov 16-30 tiers updated' as result,
  (select count(*) from app.milestones where period_key = '2026-11-P2' and sales_required_cents > 0) as tiers_with_sales_gate,
  (select count(*) from app.affiliate_sales) as affiliate_rows;
