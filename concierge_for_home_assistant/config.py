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

"""Configuration loader – reads config.yaml at startup."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger("cfh.config")


class Config:
    """Immutable configuration loaded from config.yaml."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._data: dict[str, Any] = {}
        self._load()

    # ------------------------------------------------------------------
    # Public accessors
    # ------------------------------------------------------------------
    @property
    def users(self) -> dict[str, dict[str, Any]]:
        return self._data.get("users", {})

    @property
    def roles(self) -> dict[str, dict[str, Any]]:
        return self._data.get("roles", {})

    @property
    def views(self) -> dict[str, dict[str, Any]]:
        return self._data.get("views", {})

    @property
    def cards(self) -> dict[str, dict[str, Any]]:
        return self._data.get("cards", {})

    @property
    def ha_url(self) -> str:
        return self._data.get("home_assistant", {}).get("url", "http://homeassistant.local:8123")

    @property
    def ha_token_path(self) -> str:
        return self._data.get("home_assistant", {}).get("token_path", "/app/secrets/ha_token")

    @property
    def ha_title_fallback(self) -> str:
        return self._data.get("home_assistant", {}).get("title", "Home Assistant Gateway")

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------
    def _load(self) -> None:
        if not self._path.exists():
            raise FileNotFoundError(f"config.yaml not found at {self._path}")

        with open(self._path, encoding="utf-8") as f:
            self._data = yaml.safe_load(f) or {}

        # Load secrets/users.yaml if it exists
        users_path = self._path.parent / "secrets" / "users.yaml"
        if users_path.exists():
            with open(users_path, encoding="utf-8") as f:
                users_data = yaml.safe_load(f) or {}
                self._data["users"] = users_data.get("users", users_data)

        logger.info("Configuration loaded from %s", self._path)


def load_config(path: str | Path = "config.yaml") -> Config:
    return Config(path)
