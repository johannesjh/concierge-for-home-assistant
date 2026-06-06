FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install dependencies (locked, no editable install)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY concierge_for_home_assistant/ ./concierge_for_home_assistant/

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

EXPOSE 8000

HEALTHCHECK --interval=5s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["/app/.venv/bin/gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "30", "concierge_for_home_assistant.app:create_app('config.yaml')"]
