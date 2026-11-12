#!/bin/sh
# Kept for existing commands (and live/clip); the logic lives in setup.py so it also runs on Windows.
exec python3 "$(dirname "$0")/setup.py" "$@"
