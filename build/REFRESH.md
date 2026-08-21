# How the twice-daily number refresh works

Runs 10:00 and 18:00 America/Chicago. It borrows Austin's live browser sessions
rather than storing any credential anywhere, so it needs his computer awake with
Chrome running. If it can't reach Chrome or Trybe it says so and changes nothing.

## Steps

1. Trybe → Analytics, brand **Ravine** (`?b=bf4a614a-2ec2-43fa-83f6-e19e08f57c24`),
   range **Last 30 days** → Export → Download CSV.
2. Trybe → Creators, same brand, range **All time** → Export → Download CSV.
   Both land in `~/Downloads` as `analytics-bf4a614a-<date>.csv` and
   `creators-bf4a614a-<date>.csv`.
3. `python3 parse_trybe.py <creators.csv> <analytics.csv>` → rebuilds
   `CR_FULL.json`, `an.json`, `anrange.json`.
4. `python3 buildpriv.py` → rewrites `data_core.js`, stamps the freshness pill,
   and regenerates every `ship/u/<CODE>.json`.
5. Rebuild `ship/index.html` by concatenating, in this exact order:
   shell_head.html data_core.js data_helpers.js data_state.js data_util.js
   data_broll.js art_only.js shell_app.js data_backend.js rsync.js
   broll_view.js approvals_view.js shell_views.js
6. Bump `VERSION` in `ship/sw.js` so phones pick it up.
7. Commit `index.html`, `sw.js` and the changed `u/*.json` files.

## Things that will bite you

- **Pick the Ravine brand.** The export defaults to whichever brand was last
  open. Whitelist Wealth returns all zeros; the numbers look "broken" but the
  export is simply for the wrong brand.
- **Do not filter the roster by the Program column.** It names the agency a
  creator arrived through, not the brand. Filtering on it silently drops Thomas
  Montelli, Hustyn Wheeler and eleven others who carry ~$29k of sales.
- **Match creators by normalised name.** Trybe's casing drifts between exports
  ("Alli Gamble" → "Alli gamble"). Matching raw strings mints a new id, orphans
  the pinned login code and hands that person a blank account.
- **Login codes are pinned by creator id and must never change.** `CODEPIN.json`
  is the source of truth and is deliberately kept out of this public repo. If it
  is missing, `buildpriv.py` rebuilds it from the published `ship/u/*.json`
  filenames, which is safe and lossless.
- `parse_trybe.py` refuses to publish if sales halve or the roster shrinks by a
  fifth. That guard is there so a bad export can't wipe 47 creators' numbers.
