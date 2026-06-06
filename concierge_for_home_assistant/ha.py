# Copyright (C) 2026 johannesjh
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Home Assistant REST API integration."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger("cfh.ha")


class HomeAssistantClient:
    """Thin wrapper around the Home Assistant REST API."""

    def __init__(self, url: str, token: str) -> None:
        self.url = url.rstrip("/")
        self.token = token
        self._session = requests.Session()
        self._session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
        )

    def read_entity(self, entity_id: str) -> dict[str, Any] | None:
        """GET /api/states/<entity_id>"""
        try:
            resp = self._session.get(f"{self.url}/api/states/{entity_id}", timeout=10)
            if resp.status_code == 404:
                logger.warning("Entity not found: %s", entity_id)
                return None
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.error("Failed to read entity %s: %s", entity_id, e)
            return None

    def get_config(self) -> dict:
        """GET /api/config"""
        try:
            resp = self._session.get(f"{self.url}/api/config", timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            logger.error("Failed to read HA config: %s", e)
            return {}

    def call_service(
        self,
        domain: str,
        service: str,
        service_data: dict[str, Any] | None = None,
    ) -> tuple[bool, str | None]:
        """POST /api/services/<domain>/<service>"""
        url = f"{self.url}/api/services/{domain}/{service}"
        payload = service_data or {}
        try:
            resp = self._session.post(url, json=payload, timeout=10)
            resp.raise_for_status()
            return True, None
        except requests.RequestException as e:
            msg = str(e)
            logger.error("HA service call %s/%s failed: %s", domain, service, e)
            return False, msg

    def check_health(self) -> bool:
        """GET /api/ -> check if API is running."""
        try:
            resp = self._session.get(f"{self.url}/api/", timeout=5)
            return resp.status_code == 200 and resp.json().get("message") == "API running."
        except requests.RequestException:
            return False


def call_ha_service(
    domain: str,
    service: str,
    service_data: dict[str, Any] | None = None,
) -> tuple[bool, str | None]:
    return get_ha_client().call_service(domain, service, service_data)


def init_ha_client(url: str, token: str) -> HomeAssistantClient:
    global _client
    _client = HomeAssistantClient(url, token)
    return _client


def get_ha_client() -> HomeAssistantClient:
    if _client is None:
        raise RuntimeError("HA client not initialized. Call init_ha_client() first.")
    return _client


def read_entity(entity_id: str) -> dict[str, Any] | None:
    return get_ha_client().read_entity(entity_id)


def get_ha_location_name(fallback: str = "Home Assistant Gateway") -> str:
    """Return the HA location_name, or fallback if unavailable."""
    cfg = get_ha_client().get_config()
    return cfg.get("location_name", fallback) or fallback


def check_ha_health() -> bool:
    return get_ha_client().check_health()


def load_ha_token(token_path: str) -> str:
    """Read HA token from a Docker secret file."""
    path = Path(token_path)
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    # Fallback: environment variable
    import os

    token = os.environ.get("HA_TOKEN", "")
    if not token:
        raise RuntimeError(f"HA token not found at {token_path} and HA_TOKEN env var is not set")
    return token
