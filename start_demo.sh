#!/usr/bin/env bash
set -euo pipefail

MAIL=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --mail)
      MAIL=true
      shift
      ;;
    *)
      echo "Usage: $0 [--mail]" >&2
      exit 1
      ;;
  esac
done

if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found; installing with pip"
  python -m pip install --user uv
fi

if [ ! -d ".venv" ]; then
  uv venv
fi

uv sync

if [ "$MAIL" = true ]; then
  if [ ! -d mailcow-dockerized ]; then
    git clone https://github.com/mailcow/mailcow-dockerized
    (
      cd mailcow-dockerized
      export MAILCOW_HOSTNAME=mail.local
      export MAILCOW_TZ=UTC
      export DOCKER_COMPOSE_VERSION=native
      yes "" | ./generate_config.sh >/dev/null
    )
  fi
  (
    cd mailcow-dockerized && \
    docker compose up -d && \
    ./helper-scripts/add-account -p demo123 demo1@mail.local && \
    ./helper-scripts/add-account -p demo123 demo2@mail.local
  )
  export SMTP_HOST=localhost
  export SMTP_PORT=587
  export SMTP_USER=demo1@mail.local
  export SMTP_PASSWORD=demo123
  export SMTP_FROM=demo1@mail.local
  export SMTP_STARTTLS=true
fi

exec uv run streamlit run email_summarizer_app.py --server.address 0.0.0.0 --server.port 8501

