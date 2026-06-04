#!/bin/bash
# Double-click this file to preview the website with the full pixelation effect.
# It starts a tiny local server and opens it in your browser.
# Keep the Terminal window open while viewing; close it to stop the server.

cd "$(dirname "$0")" || exit 1

# Pick the first free port so re-launching never clashes with an old server.
PORT=8000
for p in 8000 8001 8002 8080 8765; do
  if ! lsof -i :"$p" >/dev/null 2>&1; then
    PORT=$p
    break
  fi
done

URL="http://localhost:$PORT/index.html"

echo "=============================================="
echo "  Still Saying Good Morning — local preview"
echo "  Opening: $URL"
echo "  (Keep this window open. Close it to stop.)"
echo "=============================================="

# Open the browser a moment after the server boots.
( sleep 1; open "$URL" ) &

# Run the server in the foreground so this window stays alive.
python3 -m http.server "$PORT"
