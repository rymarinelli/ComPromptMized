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

cleanup() {
  if [ "$MAIL" = true ] && [ -d mailcow-dockerized ]; then
    (cd mailcow-dockerized && docker compose down >/dev/null 2>&1 || true)
  fi
}
trap cleanup EXIT

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
  fi
  (
    cd mailcow-dockerized
    if [ ! -f mailcow.conf ]; then
      export MAILCOW_HOSTNAME=mail.local
      export MAILCOW_TZ=UTC
      export DOCKER_COMPOSE_VERSION=native
      # BusyBox cp warns on the non-portable -n flag used in mailcow's
      # generate_config.sh and can terminate this script due to set -e.
      # Replace it with the POSIX-compliant --update=none option before
      # running the config generator.
      sed -i 's/cp -n/cp --update=none/' generate_config.sh
      yes "" | ./generate_config.sh >/dev/null
    fi

    # Choose a non-conflicting subnet for Mailcow's bridge network. The
    # network may be supplied as a CIDR (e.g. 192.168.10.0/24) via
    # MAILCOW_IPV4_NETWORK, and a host address can be set with
    # MAILCOW_IPV4_ADDRESS. Defaults avoid clashing with common Docker
    # networks.
    IPV4_CIDR="${MAILCOW_IPV4_NETWORK:-172.30.1.0/24}"
    IPV4_NETWORK="${IPV4_CIDR%/*}"
    IPV4_PREFIX="${IPV4_CIDR#*/}"
    IPV4_HOST_BASE="${IPV4_NETWORK%.*}"
    IPV4_ADDRESS="${MAILCOW_IPV4_ADDRESS:-${IPV4_HOST_BASE}.1}"
    # Mailcow expects IPV4_NETWORK without a trailing .0; the compose file
    # appends ".0/24" when defining the bridge subnet. Using the host base
    # avoids generating malformed values like 172.30.1.0.0/24.
    sed -i "s/^IPV4_NETWORK=.*/IPV4_NETWORK=${IPV4_HOST_BASE}/" mailcow.conf
    sed -i "s/^IPV4_NETWORK_PREFIX=.*/IPV4_NETWORK_PREFIX=${IPV4_PREFIX}/" mailcow.conf
    sed -i "s/^IPV4_ADDRESS=.*/IPV4_ADDRESS=${IPV4_ADDRESS}/" mailcow.conf

    docker compose down >/dev/null 2>&1 || true
    docker compose up -d
    add_user_script="./helper-scripts/addmailuser"
    if [ ! -x "$add_user_script" ]; then
      add_user_script="./addmailuser"
    fi
    if [ -x "$add_user_script" ]; then
      "$add_user_script" demo1@mail.local demo123
      "$add_user_script" demo2@mail.local demo123
    else
      echo "Could not find addmailuser helper script" >&2
    fi
  )
  export SMTP_HOST=localhost
  export SMTP_PORT=587
  export SMTP_USER=demo1@mail.local
  export SMTP_PASSWORD=demo123
  export SMTP_FROM=demo1@mail.local
  export SMTP_STARTTLS=true
fi

uv run streamlit run email_summarizer_app.py --server.address 0.0.0.0 --server.port 8501

