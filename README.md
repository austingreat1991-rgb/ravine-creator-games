# Ravine Creator Games — deploy guide

A single-page web app that installs to a phone home screen like a native app.
One URL works on iPhone, Android, Mac and PC.

## Files
- `index.html` — the whole app
- `manifest.webmanifest` — makes it installable
- `sw.js` — service worker: offline support + auto-update
- `icon-*.png`, `apple-touch-icon.png`, `favicon-*.png` — home screen icons
- `.nojekyll` — required for GitHub Pages
- `_headers` — cache rules (Netlify/Cloudflare; harmless on GitHub Pages)

## Deploy on GitHub Pages (free, HTTPS, ~5 minutes)

1. Create a free account at github.com if you don't have one.
2. New repository → name it `ravine-creator-games` → **Public** → Create.
3. On the repo page click **uploading an existing file**.
4. Drag in **every file from this folder** (including `.nojekyll`). Commit.
5. Settings → Pages → Source: **Deploy from a branch** → Branch: `main`, folder `/ (root)` → Save.
6. Wait ~60 seconds. Your URL:
   `https://<your-username>.github.io/ravine-creator-games/`

That link is what you send Chris and the creators.

## Custom domain (optional, makes it feel like a product)
You own tryravine.com, so point a subdomain at it:
1. In your DNS, add a CNAME: `creators` → `<your-username>.github.io`
2. Repo → Settings → Pages → Custom domain → `creators.tryravine.com` → Save
3. Tick **Enforce HTTPS**.

Creators then go to **creators.tryravine.com**.

## How creators install it
- **iPhone:** open the link in Safari → Share → Add to Home Screen
- **Android:** open in Chrome → an "Install" banner appears, or menu → Install app
- **Desktop:** an install icon appears in the address bar

After that it opens full screen with the Ravine icon. No app store, no download.

## Pushing updates
1. Ask Claude to make the change.
2. Claude gives you a new `index.html`.
3. Drag it into the repo (Add file → Upload files → commit) — it replaces the old one.
4. Bump `VERSION` in `sw.js` (e.g. `rcg-v1.0.1`) and upload that too.
5. Anyone with the app open gets a **"New version ready — Reload"** banner within 15 minutes,
   and anyone opening it fresh gets the new build immediately.

## Later: real app store presence
The same code wraps into a native shell with Capacitor when you want push
notifications or an App Store listing. Nothing here gets rewritten.

## Known limits until a backend is added
- Everyone signs in with the shared demo password `ravine`
- Creator numbers are a snapshot, refreshed when Claude re-pulls Trybe
- Breakdowns, thumbnails and posted reviews reset on reload (no database yet)

Fixing all three is the same job: a Supabase project + a nightly sync.
