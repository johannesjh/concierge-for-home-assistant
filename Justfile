#!/usr/bin/env just
#
# Concierge for Home Assistant – Justfile
#
# Usage: just <command> [stage]
# stage: "dev" (default) oder "prod"

# Zeige alle Befehle (default)
default: help

# Zeige alle Befehle
help:
	just --list

# Einmaliges Secret-Setup: HA Token eingeben + Flask Secret generieren (+ HA URL bei prod)
setup stage="dev":
	python3 concierge_for_home_assistant/cli/setup.py config/{{stage}}

# Passwort-Hash für secrets/users.yaml generieren
hash-password:
	uv run python concierge_for_home_assistant/cli/hash_password.py

# Stack starten
up stage="dev":
	export UID=$(id -u) && export GID=$(id -g) && docker compose -f config/{{stage}}/docker-compose.yml up -d

# Concierge neu bauen und starten (nach Code- oder Config-Änderungen)
rebuild stage="dev":
	export UID=$(id -u) && export GID=$(id -g) && docker compose -f config/{{stage}}/docker-compose.yml up -d --build cfh

# Stack stoppen
down stage="dev":
	docker compose -f config/{{stage}}/docker-compose.yml down

# Logs beobachten
logs stage="dev":
	docker compose -f config/{{stage}}/docker-compose.yml logs -f

# Linting und Formatting
lint:
	uv run ruff check concierge_for_home_assistant/
	uv run ruff format concierge_for_home_assistant/
