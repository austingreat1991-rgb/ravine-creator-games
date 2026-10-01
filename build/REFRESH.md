# Numbers refresh — how it works now (Sept 30, 2026)

The source files for index.html no longer exist anywhere; the live index.html IS
the template. Everything below edits it in place with counted, exact splices.

    # from the repo root, with the two Trybe exports for the Ravine brand
    python3 build/refresh.py creators-<date>.csv analytics-<date>.csv --month 2026-10 \
            --baseline ../pipeline/BASELINE-2026-10.json      # October runs: base = Sept 30 snapshot
    python3 build/patch_quests.py                             # no-op once applied (RAVINE-QUESTS-V2)

What refresh.py does
  1. reads the live roster (CR in index.html) and every u/<CODE>.json — that is
     where the pinned codes and the 1st-of-month baseline live
  2. parses the creators export (All time, Ravine) — duplicates of a name are a
     video account plus a static-image account; the one that submits videos is
     kept, the other is dropped from the roster and never enters the pool
  3. this-month = all-time minus the frozen baseline, per creator
  4. parses the analytics export (Last 30 days, by creative) for ad metrics
  5. pool = 60% sales / 40% approved videos, this month only, VIDEO accounts
  6. rewrites u/<CODE>.json for everyone on the roster, revokes files for
     anyone who left, mints a code for anyone new (NEW_CODES-<stamp>.json goes
     to ../pipeline, never the repo)
  7. splices CR / TOTALS / SYNC / POOL / POOL_END into index.html and bumps
     VERSION in sw.js

Guards: refuses a non-Ravine export, a non-All-time creators export, a roster
that shrank >20% (pass --allow-shrink when Austin really removed people), and
any login code appearing in index.html.

Monthly flip (1st of the month): run the previous day's exports with
--snapshot-baseline ../pipeline/BASELINE-<next-month>.json, then run the new
month with --baseline pointing at that file. POOLS in refresh.py holds the pool
amount per month (Oct 2026 = 25,000).

Deploy = commit index.html, sw.js, build/, and the changed u/*.json. Nothing in
../pipeline is ever committed.
