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

## Open items
1. Commit `official-ravine-logo.png` (sha256 101d8066...07dbd0) at the repo root so the wordmark is self-hosted.
2. The five mockup PNGs were not available to this build; layouts follow the written spec.
3. Proposed frames, titles, season patches, Rising Creators / Most Improved / Creative of the Week, guided paths and the eight draft quests are not built: each needs a server-side entitlement or selection record first.
4. Admin Contest & imports still shows some November column headers over the October payload.
5. BOF wording on Rewards is unchanged pending the policy decision.
