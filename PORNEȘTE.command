#!/bin/zsh
cd "$(dirname "$0")"
PY="/Users/sergiu/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"
if [ -f "$PY" ]; then
  "$PY" server.py
else
  python3 server.py
fi
