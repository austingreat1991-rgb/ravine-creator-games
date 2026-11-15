#!/bin/sh
# Builds preview.html: the same app in fixture mode with build/fixtures.js. Synthetic accounts only, no backend calls, no service worker, nothing saved.
set -e; cd "$(dirname "$0")/.."
sed -e 's#window.APP_MODE="live";#window.APP_MODE="fixture";window.NO_SW=1;#' -e 's#<head>#<head><meta name="robots" content="noindex">#' -e 's#<script>/\* Ravine Creator Games · October build · core#<script src="./build/fixtures.js"></script><script>/* Ravine Creator Games · October build · core#' index.html > preview.html
grep -c 'APP_MODE="fixture"' preview.html; grep -c 'build/fixtures.js' preview.html
