#!/bin/sh
# Builds next/index.html: the same app served one folder down, so it can sit beside the live app without replacing it.
set -e; cd "$(dirname "$0")/.."; mkdir -p next
sed -E "s#(['\"(\`=])\./#\1../#g; s#window.APP_MODE=\"live\";#window.APP_MODE=\"live\";window.PREVIEW=1;#; s#<head>#<head><meta name=\"robots\" content=\"noindex\"><script src=\"./preview-shim.js\"></script>#" index.html > next/index.html
grep -c '\.\./' next/index.html
