// Builds the affiliate sales SQL from Social Snowball rows, inside the browser. No emails ever go in.
// rows: [{order_id, affiliate (name as Snowball shows it), code, placed_at (ISO), amount (number), refunded (bool)}]
function affSql(rows, at){
  const q=s=>s==null?'null':"'"+String(s).replace(/'/g,"''")+"'";
  const n=x=>{ const v=Math.round(Number(x)*100)/100; if(!isFinite(v)) throw new Error('bad amount '+x); return v.toFixed(2); };
  const vals=rows.map(r=>'('+[q(r.order_id),q(r.affiliate),q(r.code),q(new Date(r.placed_at).toISOString()),n(r.amount),r.refunded?'true':'false'].join(',')+')');
  return `-- Ravine Creator Games: Social Snowball affiliate sales, pulled ${at}. Paste into a NEW empty Supabase query tab and Run.
-- One row per order. A sale counts toward quest tiers unless it was refunded. Safe to run twice.
do $aff$
declare n int;
begin
  if to_regclass('app.affiliate_sales') is null then raise exception 'STOP: run p2_harder.sql first'; end if;
  drop table if exists _af;
  create temp table _af (order_id text primary key, affiliate text, code text, placed_at timestamptz, amount numeric, refunded boolean, cid uuid) on commit drop;
  insert into _af (order_id, affiliate, code, placed_at, amount, refunded) values
${vals.join(',\n')||"('none',null,null,now(),0,true)"};
  delete from _af where order_id = 'none';
  -- match the affiliate to a creator by name (display name or Trybe name), only when exactly one creator matches
  update _af a set cid = x.cid from (
    select a2.order_id, min(c.id::text)::uuid cid, count(distinct c.reward_identity) k from _af a2
      join app.creators c on c.active and app.on_roster(c.id) and lower(regexp_replace(trim(a2.affiliate), '\\s+', ' ', 'g')) in
           (lower(regexp_replace(trim(c.display_name), '\\s+', ' ', 'g')), lower(regexp_replace(trim(coalesce(c.trybe_name, '')), '\\s+', ' ', 'g')))
     group by a2.order_id) x where x.order_id = a.order_id and x.k = 1;
  insert into app.affiliate_sales (order_id, creator_id, affiliate_code, placed_at, amount, refunded, source, synced_at)
  select order_id, cid, code, placed_at, amount, refunded, 'snowball', now() from _af where cid is not null
  on conflict (order_id) do update set creator_id = excluded.creator_id, affiliate_code = excluded.affiliate_code, placed_at = excluded.placed_at,
    amount = excluded.amount, refunded = excluded.refunded, synced_at = excluded.synced_at;
  create table if not exists app.affiliate_unmatched (affiliate text primary key, orders int, synced_at timestamptz);
  alter table app.affiliate_unmatched enable row level security; revoke all on app.affiliate_unmatched from anon, authenticated;
  delete from app.affiliate_unmatched;
  insert into app.affiliate_unmatched select affiliate, count(*), now() from _af where cid is null group by affiliate;
end $aff$;
select 'Affiliate sales loaded' as result,
  (select count(*) from app.affiliate_sales) as orders_in_app,
  (select count(*) from app.affiliate_sales where refunded) as refunded,
  (select '$' || to_char(coalesce(sum(amount) filter (where not refunded), 0), 'FM999,999,990.00') from app.affiliate_sales where placed_at >= timestamptz '2026-11-16 06:00+00') as counting_nov_16_30,
  (select coalesce(string_agg(affiliate || ' (' || orders || ')', ', '), 'none') from app.affiliate_unmatched) as not_matched_to_a_creator;`;
}
if(typeof module!=='undefined') module.exports={affSql};
