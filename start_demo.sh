#!/usr/bin/env bash
set -euo pipefail

# Ensure uv is installed
if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found; installing with pip"
  python -m pip install --user uv
fi

# Create virtual environment if missing
if [ ! -d ".venv" ]; then
  uv venv
fi

# Install dependencies
uv sync

# Launch the Streamlit app
exec uv run streamlit run email_summarizer_app.py --server.address 0.0.0.0 --server.port 8501
