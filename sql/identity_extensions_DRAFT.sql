-- Creator Games identity extensions. DRAFT. Not run anywhere. Do not paste into production until the earning rules marked UNRESOLVED are decided.
-- Adds frames, titles, season patches, guided quest paths and recognition picks. Cosmetic only. No XP, cash, rank or payout changes.
-- Everything is seeded with active = false, so app.my_identity returns nothing to creators until an item is switched on.

create table if not exists app.cosmetic_catalog (
  key text primary key,
  kind text not null check (kind in ('frame','title','season_patch')),
  label text not null,
  how text not null,
  rule jsonb not null default '{}'::jsonb,
  active boolean not null default false,
  sort_order int not null default 100
);
create table if not exists app.creator_cosmetics (
  creator_id uuid not null,
  cosmetic_key text not null references app.cosmetic_catalog(key),
  earned_at timestamptz not null default now(),
  source text not null,
  primary key (creator_id, cosmetic_key)
);
create table if not exists app.creator_loadout (
  creator_id uuid primary key,
  frame_key text references app.cosmetic_catalog(key),
  title_key text references app.cosmetic_catalog(key),
  updated_at timestamptz not null default now()
);
create table if not exists app.quest_paths (
  key text primary key,
  label text not null,
  blurb text,
  unlocks_cosmetic text references app.cosmetic_catalog(key),
  active boolean not null default false,
  sort_order int not null default 100
);
create table if not exists app.quest_path_steps (
  path_key text not null references app.quest_paths(key),
  step_no int not null,
  label text not null,
  icon text not null default 'star',
  quest_keys text[] not null,
  primary key (path_key, step_no)
);
create table if not exists app.recognition (
  id bigint generated always as identity primary key,
  period_key text not null,
  kind text not null check (kind in ('rising','most_improved','creative_of_week')),
  creator_id uuid not null,
  submission_id text,
  note text,
  selected_by uuid not null,
  created_at timestamptz not null default now()
);
alter table app.cosmetic_catalog enable row level security;
alter table app.creator_cosmetics enable row level security;
alter table app.creator_loadout enable row level security;
alter table app.quest_paths enable row level security;
alter table app.quest_path_steps enable row level security;
alter table app.recognition enable row level security;

create or replace function app.current_creator() returns uuid language sql stable security definer set search_path = app, public as $f$
  select d.creator_id from app.creator_devices d where d.auth_user_id = auth.uid() and d.revoked_at is null limit 1
$f$;

-- Read: active catalog with this creator ownership, loadout, active paths (step completion is worked out in the app from approved quest entries), and recognition picks.
create or replace function app.my_identity() returns jsonb language plpgsql stable security definer set search_path = app, public as $f$
declare me uuid := app.current_creator(); out jsonb;
begin
  if me is null then return null; end if;
  select jsonb_build_object(
    'cosmetics', coalesce((select jsonb_agg(jsonb_build_object('key', c.key, 'kind', c.kind, 'label', c.label, 'how', c.how, 'owned', o.creator_id is not null, 'earned_at', o.earned_at) order by c.sort_order, c.key)
       from app.cosmetic_catalog c left join app.creator_cosmetics o on o.cosmetic_key = c.key and o.creator_id = me where c.active), '[]'::jsonb),
    'loadout', coalesce((select jsonb_build_object('frame', l.frame_key, 'title', l.title_key) from app.creator_loadout l where l.creator_id = me), jsonb_build_object('frame', null, 'title', null)),
    'paths', coalesce((select jsonb_agg(jsonb_build_object('key', p.key, 'label', p.label, 'blurb', p.blurb, 'unlocks', p.unlocks_cosmetic,
         'steps', (select jsonb_agg(jsonb_build_object('label', s.label, 'icon', s.icon, 'quest_keys', to_jsonb(s.quest_keys)) order by s.step_no) from app.quest_path_steps s where s.path_key = p.key)) order by p.sort_order, p.key)
       from app.quest_paths p where p.active), '[]'::jsonb),
    'recognition', coalesce((select jsonb_agg(jsonb_build_object('kind', r.kind, 'period', r.period_key, 'name', cr.display_name, 'me', r.creator_id = me, 'note', r.note) order by r.created_at desc)
       from app.recognition r join app.creators cr on cr.id = r.creator_id where r.created_at > now() - interval '45 days'), '[]'::jsonb)
  ) into out;
  return out;
end $f$;

-- Write: equip a frame or title the creator owns. Passing null clears the slot. Nothing else changes.
create or replace function app.set_loadout(p_frame text, p_title text) returns jsonb language plpgsql security definer set search_path = app, public as $f$
declare me uuid := app.current_creator();
begin
  if me is null then return jsonb_build_object('ok', false, 'why', 'not signed in'); end if;
  if p_frame is not null and not exists (select 1 from app.creator_cosmetics o join app.cosmetic_catalog c on c.key = o.cosmetic_key where o.creator_id = me and o.cosmetic_key = p_frame and c.kind = 'frame' and c.active) then
    return jsonb_build_object('ok', false, 'why', 'frame is locked'); end if;
  if p_title is not null and not exists (select 1 from app.creator_cosmetics o join app.cosmetic_catalog c on c.key = o.cosmetic_key where o.creator_id = me and o.cosmetic_key = p_title and c.kind = 'title' and c.active) then
    return jsonb_build_object('ok', false, 'why', 'title is locked'); end if;
  insert into app.creator_loadout (creator_id, frame_key, title_key) values (me, p_frame, p_title)
    on conflict (creator_id) do update set frame_key = excluded.frame_key, title_key = excluded.title_key, updated_at = now();
  return jsonb_build_object('ok', true, 'frame', p_frame, 'title', p_title);
end $f$;

-- Admin only: grant a cosmetic, record a recognition pick.
create or replace function app.admin_grant_cosmetic(p_creator uuid, p_key text, p_source text) returns jsonb language plpgsql security definer set search_path = app, public as $f$
begin
  if not app.is_admin() then return jsonb_build_object('ok', false, 'why', 'admin only'); end if;
  insert into app.creator_cosmetics (creator_id, cosmetic_key, source) values (p_creator, p_key, coalesce(p_source, 'admin')) on conflict do nothing;
  return jsonb_build_object('ok', true);
end $f$;
create or replace function app.admin_recognize(p_period text, p_kind text, p_creator uuid, p_submission text, p_note text) returns jsonb language plpgsql security definer set search_path = app, public as $f$
begin
  if not app.is_admin() then return jsonb_build_object('ok', false, 'why', 'admin only'); end if;
  insert into app.recognition (period_key, kind, creator_id, submission_id, note, selected_by) values (p_period, p_kind, p_creator, p_submission, p_note, auth.uid());
  return jsonb_build_object('ok', true);
end $f$;
grant execute on function app.my_identity() to anon, authenticated;
grant execute on function app.set_loadout(text, text) to anon, authenticated;
grant execute on function app.admin_grant_cosmetic(uuid, text, text) to anon, authenticated;
grant execute on function app.admin_recognize(text, text, uuid, text, text) to anon, authenticated;

-- Seeds. All inactive. UNRESOLVED marks a rule Austin has to decide before switching the row on.
insert into app.cosmetic_catalog (key, kind, label, how, rule, sort_order) values
  ('frame_night_ops', 'frame', 'Night Ops Frame', 'Finish the Hook Builder path', '{"UNRESOLVED": "Granted when the Hook Builder path is complete, or hand-granted by Austin?"}', 10),
  ('frame_ravine_edge', 'frame', 'Ravine Edge', 'Everyone starts with it', '{"UNRESOLVED": "Should every creator own a base frame by default?"}', 5),
  ('title_hook_builder', 'title', 'Hook Builder', 'Finish the Hook Builder path', '{"UNRESOLVED": "Same trigger as the frame, or separate?"}', 20),
  ('title_feedback_pro', 'title', 'Feedback Pro', 'Finish the Feedback Loop path', '{"UNRESOLVED": "Trigger"}', 21),
  ('patch_2026_11', 'season_patch', 'November 2026 Contender', 'Compete in the November season', '{"UNRESOLVED": "What counts as competing: one approved November video, one sale, or being ranked at close?"}', 30)
on conflict (key) do nothing;
insert into app.quest_paths (key, label, blurb, unlocks_cosmetic, sort_order) values
  ('hook_builder', 'Hook Builder', 'Five steps to stronger openings.', 'frame_night_ops', 10),
  ('feedback_loop', 'Feedback Loop', 'Get notes, apply them, improve the video.', 'title_feedback_pro', 20)
on conflict (key) do nothing;
insert into app.quest_path_steps (path_key, step_no, label, icon, quest_keys) values
  ('hook_builder', 1, 'Study', 'book', array['oct_recreate','oct_review3']),
  ('hook_builder', 2, 'Write', 'wrench', array['oct_concepts5','oct_newangle3']),
  ('hook_builder', 3, 'Film', 'camera', array['oct_hooks3']),
  ('hook_builder', 4, 'Test', 'target', array['oct_improve','oct_weakspot']),
  ('hook_builder', 5, 'Debrief', 'check', array['oct_feedback']),
  ('feedback_loop', 1, 'Get reviewed', 'people', array['oct_review3']),
  ('feedback_loop', 2, 'Apply it', 'wrench', array['oct_feedback']),
  ('feedback_loop', 3, 'Improve', 'star', array['oct_improve','oct_weakspot'])
on conflict do nothing;
