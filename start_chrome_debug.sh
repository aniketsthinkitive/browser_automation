#!/usr/bin/env bash
# Start real Google Chrome with remote debugging enabled so Playwright can
# attach to it over CDP (see tests/test_form_fill.py).
#
# Chrome 136+ refuses --remote-debugging-port on your default profile, so we
# use a dedicated profile directory. Log in to SmartRecruiters once in this
# window - the profile keeps the session for future runs.

PORT=9222
PROFILE_DIR="$HOME/.chrome-debug-profile"

if curl -s "http://localhost:$PORT/json/version" > /dev/null 2>&1; then
    echo "Chrome is already listening on port $PORT - nothing to do."
    exit 0
fi

# setsid + nohup fully detach Chrome from this terminal so it keeps
# running after the script (or the terminal) exits.
setsid nohup google-chrome \
    --remote-debugging-port=$PORT \
    --user-data-dir="$PROFILE_DIR" \
    --no-first-run \
    --no-default-browser-check \
    > /dev/null 2>&1 &

# Wait until the CDP endpoint is actually up (max ~10s).
for _ in $(seq 1 20); do
    if curl -s "http://localhost:$PORT/json/version" > /dev/null 2>&1; then
        break
    fi
    sleep 0.5
done

if ! curl -s "http://localhost:$PORT/json/version" > /dev/null 2>&1; then
    echo "ERROR: Chrome did not start listening on port $PORT." >&2
    exit 1
fi

echo "Chrome started with debugging on http://localhost:$PORT"
echo "Profile: $PROFILE_DIR (log in once; the session is remembered)"
