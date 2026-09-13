#!/bin/zsh
# Starts StudyMate locally and opens the working app in your default browser.
set -e
cd "$(dirname "$0")"

if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv
  .venv/bin/python -m pip install -r requirements.txt
fi

open http://127.0.0.1:8000
exec .venv/bin/python -m uvicorn main:app
