#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -d ".venv" ]; then
    VENV_DIR=".venv"
elif [ -d "venv" ]; then
    VENV_DIR="venv"
else
    echo "No virtual environment found (.venv or venv). Run install.sh first"
    exit 1
fi

. "$VENV_DIR/bin/activate"

exec extrapolator "$@" || { read -pr "Got error, press any key to close" x; }
