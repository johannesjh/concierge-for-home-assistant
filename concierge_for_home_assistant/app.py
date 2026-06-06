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

"""Flask application factory."""

from __future__ import annotations

import logging
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, session, url_for

from .auth import init_auth
from .config import load_config
from .ha import (
    check_ha_health,
    get_ha_location_name,
    init_ha_client,
    load_ha_token,
    read_entity,
)

logger = logging.getLogger("cfh")


def _setup_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def create_app(config_path: str = "config.yaml") -> Flask:
    _setup_logging()

    config = load_config(config_path)

    # Load HA token
    ha_token = load_ha_token(config.ha_token_path)
    init_ha_client(config.ha_url, ha_token)

    app = Flask(__name__)
    app.secret_key = _load_secret("/app/secrets/flask_secret_key")

    # --- auth routes + hooks ---
    init_auth(app, config)

    # --- HTML page routes ---
    @app.route("/")
    def index():
        if "user" in session:
            return redirect(url_for("dashboard"))
        return redirect(url_for("login_page"))

    @app.route("/login")
    def login_page():
        return render_template("login.html")

    @app.route("/dashboard")
    def dashboard():
        username = session.get("user")
        if not username:
            return redirect(url_for("login_page"))

        user_config = config.users.get(username, {})
        roles = user_config.get("roles", [])

        view_ids = []
        seen = set()
        for role_name in roles:
            role = config.roles.get(role_name, {})
            for v in role.get("views", []):
                if v not in seen:
                    seen.add(v)
                    view_ids.append(v)

        views = []
        for vid in view_ids:
            view_cfg = config.views.get(vid, {})
            card_names = view_cfg.get("cards", [])
            cards = []
            for card_name in card_names:
                card_cfg = config.cards.get(card_name, {})
                cards.append({"name": card_name, **card_cfg})
            views.append(
                {
                    "id": vid,
                    "title": view_cfg.get("title", vid),
                    "cards": cards,
                }
            )

        title = get_ha_location_name(fallback=config.ha_title_fallback)
        return render_template("dashboard.html", user=username, views=views, title=title)

    # --- Card data endpoints (fetches live data from HA) ---
    @app.route("/health", methods=["GET"])
    def health():
        if check_ha_health():
            return jsonify(status="healthy")
        return jsonify(status="unhealthy"), 503

    @app.route("/api/card/<card_name>/data", methods=["GET"])
    def card_data(card_name: str):
        username = session.get("user")
        if not username:
            return jsonify(error="unauthorized"), 401

        # Check user has access to this card
        user_config = config.users.get(username, {})
        roles = user_config.get("roles", [])
        allowed = set()
        for role_name in roles:
            role = config.roles.get(role_name, {})
            for v in role.get("views", []):
                view_cfg = config.views.get(v, {})
                for c in view_cfg.get("cards", []):
                    allowed.add(c)

        if card_name not in allowed:
            return jsonify(error="forbidden"), 403

        card_cfg = config.cards.get(card_name, {})
        entity = card_cfg.get("entity", "")

        if not entity:
            return jsonify(value=None)

        state = read_entity(entity)
        if state is None:
            return jsonify(value=None, available=False)

        return jsonify(
            value=state.get("state"),
            attributes=state.get("attributes", {}),
            entity_id=state.get("entity_id"),
            available=True,
        )

    return app


def _load_secret(path: str) -> str:
    p = Path(path)
    if p.exists():
        return p.read_text(encoding="utf-8").strip()
    import os

    val = os.environ.get("FLASK_SECRET_KEY", "")
    if not val:
        raise RuntimeError(f"Secret not found at {path} and FLASK_SECRET_KEY not set")
    return val
