# Creator Games redesign (branch `redesign-nov`)

Base: `main` at f45836d (rollback reference; the live app at the site root is unchanged by this branch).
Preview: `next/index.html` is this branch's app built one folder down by `build/make-preview.sh`. It talks to the same backend as the live app.
QA: `build/qa-shot.js` serves the repo in fixture mode with `build/fixtures.js` (synthetic accounts, no network, nothing saved).

## What changed
- Tokens: charcoal/olive/sandstone palette (`--rg-*`), 12px cards, 44px controls, dark ink on orange buttons.
- Shell: official Ravine wordmark (`official-ravine-logo.png`, falls back to the same file on tryravine.com until it is committed), full 18-destination menu in its own scroll area, account block pinned, mobile bar and All pages sheet restyled.
- Home: "Your daily briefing" (next action with reviewer note, creator card, period-labelled metrics, active mission, next unlock). Every earlier Home module is still on the page below it.
- Quests: `#/quests?f=needs_changes|in_progress|submitted|available` now filters to that state (Home links used it but Quests ignored it). "Not approved" entries are listed apart from "Completed".
- Armory: loadout + closest unlock, collection grid. Tapping a camo opens Inspect; Equip is a separate button and only for owned camos.
- Rewards: Rewards / Trophy Room switch (`#/rewards?v=trophies`). Trophy Room shows the existing badge records. No claim rail was added; November stays no-claim.
- Leaderboard: top 3 as player cards; stacks on phones.

## Not changed
Routes, aliases, RPC names, permissions, XP/cash/prestige rules, payout flow, camo keys, storage keys, service worker logic.

## v2 (visual correction against the five approved mockups)
Mockups and the official logo were viewed at full size. `official-ravine-logo.png` is now committed at the repo root (sha256 101d806671e2ff87026313a369da5537776612e5662b7d89f9e9e4192407dbd0); nothing loads from tryravine.com.
- Shell: top season bar (season, XP half, reset clock, account), uppercase display headings, wordmark sidebar with all 18 destinations.
- Home (01): media + sandstone next-move hero, camo creator card with crest, four-metric strip, active mission filmstrip, next-unlock nameplate, team goal banner, recent achievement.
- Quests (02): skill coverage patch strip (real per-type approvals this half), state tabs with counts and search, row mission cards, sandstone read-only brief beside the board at 1280px and up. The working brief with the evidence form is still the drawer.
- Leaderboard (03): three photo player cards, sandstone Your race strip with real neighbours, aligned standings table with worded movement.
- Armory (04): loadout banner, four real slots (camo, name color, prestige, collection), sandstone closest-unlock panel, filterable collection of all nine camos.
- Trophy Room (05): sandstone This half panel, creator legacy card, lit shelf of the nine existing badges with stitched patch art, real no-claim reward status.

Intentional differences from the mockups
- Official wordmark instead of the mountain mark; full 18-item menu instead of five, so the sidebar is taller and 248px wide.
- Real Ravine photos (`ph/angle-*.jpg`, quest art, creator thumbnails) instead of backpacks and generated faces.
- Dark ink on orange buttons (5.58:1) instead of white.
- Hook Builder path, Night Ops Frame, Frame and Emblem slots, Field Kit and Alpine names, Rising creators, Most improved, Creator spotlight, Personal best, November contender and the claim rail are not built: none has a data source. Their places are filled by real equivalents (skill coverage, closest camo, prestige and collection slots, reward status).
- No landscape photography exists in the repo beyond the angle photos, so banners reuse those.

## Open items
3. Proposed frames, titles, season patches, Rising Creators / Most Improved / Creative of the Week, guided paths and the eight draft quests are not built: each needs a server-side entitlement or selection record first.
4. Admin Contest & imports still shows some November column headers over the October payload.
5. BOF wording on Rewards is unchanged pending the policy decision.


## v3 approved branch fixes
- Original textured embroidered patch material is local in art/embroidered-patch-base.svg. It embeds the exact generated transparent PNG, so it has no external image dependency and is not a replacement brand logo.
- Existing symbols use raised metallic overlays and explicit gold/silver/bronze variants. Legacy Home badge strip/detail emoji are replaced too. Badge conditions, category mappings, ownership and payouts are unchanged.
- Historical admin contest headers now say GMV (Oct videos) and Approved Oct videos. Queries, snapshots and freeze behavior are unchanged.
- Isolated checks pass: node build/check-patch-artwork.cjs (four inline JS blocks, 12 state/tone cases, accessibility/paint IDs, embedded transparent asset/fallback, unchanged badge eligibility pinned to9ced3a1) and node build/check-admin-contest-labels.cjs (four campaign/finalization fixtures).
- Browser visual comparison and interaction QA remain unverified for this patch. Finish full-size comparisons and the prior missing keyboard/zoom/draft-submit tests before calling the whole redesign complete.
- New frames, titles, season patches, guided paths, draft quests and recognition still require implementation with real records. BOF wording needs authoritative existing-rule verification. Do not introduce new payouts or live data mutations to complete visual QA.
- No main-branch or live preview deployment is part of these fixes. Pull current redesign-nov before continuing in Claude.


## v4 (Nov 14, evening): remaining build, checks and speed
Built on c327383. `main` is unchanged (f45836d). The live-data `next/` preview was removed from the branch.

New, shown only when the database has them (it does not yet)
- Frames, titles, season patches, guided paths, recognition picks. Schema and functions: `sql/identity_extensions_DRAFT.sql` (tested on a throwaway local Postgres only; every seed row is inactive). The app reads `app.my_identity`; when it is missing the app asks once per session and shows the existing skill coverage strip, closest camo and prestige/collection slots instead.
- Quest drafts mapped to existing quests in `sql/QUEST-DRAFTS.md`. Three are new and need XP and limits.

Unresolved earning rules (nothing is switched on until these are decided)
1. Night Ops Frame and the Hook Builder title: granted automatically when the path completes, or hand-granted?
2. Ravine Edge base frame: does everyone own it?
3. November season patch: what counts as competing (one approved video, one sale, or ranked at close)?
4. Rising creators, Most improved, Creative of the week: picked by Austin through `app.admin_recognize`. No automatic formula was built.
5. XP and limits for B-roll With a Job, One Variable Test and Creator Debrief.
6. Sales wording on Rewards still says "not marked BOF". Video wording now says BOF videos count as half.

Other changes
- Closing a drawer returns keyboard focus to what opened it.
- Patch artwork file cut from 3.86 MB to 60 KB (same approved image, 380 px, palette PNG). Service worker now caches SVG.
- Home loads armory, leaderboard and identity in parallel with the rest.
- Angle Library toolbar wraps instead of overflowing between 600 and 1279 px.

Checks (all isolated, test data only)
- `node build/check-patch-artwork.cjs`, `node build/check-admin-contest-labels.cjs`: pass.
- `node build/qa-flows.js`: 37 checks pass (draft, autosave failure and retry, validation, single submit, inspect vs equip, roles, admin J/K/A/C shortcuts, keyboard focus, 200% zoom on all 18 destinations, short window, sales privacy, no claim action, local logo).
- `node build/qa-shot.js`: every destination at 1440, 1024, 768 and 390 wide, no sideways scroll, no script errors.
- `node build/qa-perf.js`: phone Home first visit about 400 KB (live 235 KB), desktop 400 KB (live 656 KB); page HTML 184 KB gzipped (live 159 KB); every screen renders in under 0.15 s on a 4x-slowed CPU; no layout shift.

Isolated preview: `preview.html` (built by `build/make-preview.sh`). Test accounts only, no backend calls, no service worker. Delete it or leave it out when merging to `main`.

Not verified: real-account data on the new layouts, real phones, screen readers, and the SQL against the production schema.
