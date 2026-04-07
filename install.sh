#!/usr/bin/env bash
# Create a virtual environment named .venv or venv in the script's directory if neither exists,
# install/update the current project (pip install .).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON=python3

if [ -d ".venv" ]; then
    VENV_DIR=".venv"
elif [ -d "venv" ]; then
    VENV_DIR="venv"
else
    "$PYTHON" -m venv .venv
    VENV_DIR=".venv"
fi

. "$VENV_DIR/bin/activate"

# removes annoying notices about updating pip
"$PYTHON" -m pip install --disable-pip-version-check --upgrade pip setuptools wheel
"$PYTHON" -m pip install --disable-pip-version-check .
