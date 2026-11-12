#!/bin/sh
# Kept for existing commands; the logic lives in fetch.py so it also runs on Windows.
exec python3 "$(dirname "$0")/fetch.py" "$@"
