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
