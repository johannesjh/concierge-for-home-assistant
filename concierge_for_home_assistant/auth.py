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

"""Authentication – login, logout, session management."""

from __future__ import annotations

import logging
import os
import secrets

from flask import Flask, jsonify, redirect, request, send_from_directory, session, url_for
from werkzeug.security import check_password_hash

from .config import Config
from .ha import call_ha_service

logger = logging.getLogger("cfh.auth")

_INSECURE_COOKIE = os.environ.get("CFH_INSECURE_COOKIE", "").lower() in ("1", "true", "yes")


def init_auth(app: Flask, config: Config) -> None:
    """Register auth-related hooks and routes."""

    @app.before_request
    def require_login():
        if request.path == "/health":
            return None
        if request.path.startswith("/static/"):
            return None
        if request.path == "/service-worker.js":
            return None
        if request.path in ("/login", "/api/login"):
            return None

        user = session.get("user")
        if not user:
            if request.path.startswith("/api/"):
                return jsonify_error("unauthorized", 401)
            return redirect(url_for("login_page"))

    @app.before_request
    def validate_csrf():
        if request.path == "/api/login":
            return
        if request.method in ("POST", "PUT", "DELETE", "PATCH"):
            csrf_token = request.headers.get("X-CSRF-Token")
            session_token = session.get("csrf_token")
            if not session_token or csrf_token != session_token:
                logger.warning(
                    "CSRF validation failed: header=%s session=%s", csrf_token, session_token
                )
                return jsonify_error("CSRF validation failed", 400)

    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SECURE"] = not _INSECURE_COOKIE
    app.config["SESSION_COOKIE_SAMESITE"] = "Strict"
    app.config["SESSION_REFRESH_EACH_REQUEST"] = True

    if _INSECURE_COOKIE:
        logger.warning("CFH_INSECURE_COOKIE is set – SESSION_COOKIE_SECURE disabled. Dev only!")

    # CSRF token lives in the session
    @app.before_request
    def load_csrf_token():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_hex(32)

    @app.route("/service-worker.js")
    def service_worker():
        static_dir = os.path.join(os.path.dirname(__file__), "static")
        return send_from_directory(
            static_dir, "service-worker.js", mimetype="application/javascript"
        )

    @app.route("/api/login", methods=["POST"])
    def login():
        body = request.get_json(silent=True)
        if body is None:
            # Fallback: form-urlencoded (z.B. wenn JS nicht geladen wurde)
            body = request.form.to_dict()
        username = body.get("username", "").strip()
        password = body.get("password", "")

        if not username or not password:
            return jsonify_error("missing credentials", 400)

        user_config = config.users.get(username)
        if not user_config:
            logger.warning("Login attempt for unknown user: %s", username)
            return jsonify_error("invalid credentials", 401)

        stored_hash = user_config.get("password_hash", "")
        if not check_password_hash(stored_hash, password):
            logger.warning("Failed login for user: %s", username)
            return jsonify_error("invalid credentials", 401)

        session["user"] = username
        logger.info("User logged in: %s", username)
        return {"ok": True, "user": username}

    @app.route("/api/logout", methods=["POST"])
    def logout():
        username = session.get("user")
        session.clear()
        if username:
            logger.info("User logged out: %s", username)
        return {"ok": True}

    @app.route("/api/me", methods=["GET"])
    def me():
        username = session.get("user")
        if not username:
            return jsonify_error("unauthorized", 401)

        user_config = config.users.get(username, {})
        roles = user_config.get("roles", [])

        # Resolve views from roles
        view_ids = set()
        for role_name in roles:
            role = config.roles.get(role_name, {})
            for v in role.get("views", []):
                view_ids.add(v)

        return {
            "user": username,
            "roles": roles,
            "views": sorted(view_ids),
        }

    @app.route("/api/views", methods=["GET"])
    def list_views():
        username = session.get("user")
        if not username:
            return jsonify_error("unauthorized", 401)

        user_config = config.users.get(username, {})
        roles = user_config.get("roles", [])

        view_ids = set()
        for role_name in roles:
            role = config.roles.get(role_name, {})
            for v in role.get("views", []):
                view_ids.add(v)

        result = []
        for vid in sorted(view_ids):
            view_cfg = config.views.get(vid, {})
            result.append(
                {
                    "id": vid,
                    "title": view_cfg.get("title", vid),
                }
            )
        return {"views": result}

    @app.route("/api/views/<view_id>", methods=["GET"])
    def get_view(view_id: str):
        username = session.get("user")
        if not username:
            return jsonify_error("unauthorized", 401)

        # Check user has access to this view
        user_config = config.users.get(username, {})
        roles = user_config.get("roles", [])
        allowed = set()
        for role_name in roles:
            role = config.roles.get(role_name, {})
            for v in role.get("views", []):
                allowed.add(v)

        if view_id not in allowed:
            return jsonify_error("forbidden", 403)

        view_cfg = config.views.get(view_id, {})
        card_defs = []
        for card_name in view_cfg.get("cards", []):
            card_cfg = config.cards.get(card_name, {})
            card_defs.append({"name": card_name, **card_cfg})

        return {
            "id": view_id,
            "title": view_cfg.get("title", view_id),
            "cards": card_defs,
        }

    @app.route("/api/actions/<action_name>", methods=["POST"])
    def execute_action(action_name: str):
        username = session.get("user")
        if not username:
            return jsonify_error("unauthorized", 401)

        # Verify the action card is in any view the user has access to
        user_config = config.users.get(username, {})
        roles = user_config.get("roles", [])
        allowed_cards = set()
        for role_name in roles:
            role = config.roles.get(role_name, {})
            for v in role.get("views", []):
                view_cfg = config.views.get(v, {})
                for c in view_cfg.get("cards", []):
                    allowed_cards.add(c)

        if action_name not in allowed_cards:
            log_audit(username, action_name, "forbidden", "card not allowed")
            return jsonify_error("forbidden", 403)

        card_cfg = config.cards.get(action_name, {})
        card_type = card_cfg.get("type")
        if card_type not in ("action", "toggle"):
            log_audit(
                username, action_name, "error", f"card is of type {card_type}, not action or toggle"
            )
            return jsonify_error("not an action or toggle card", 400)

        if card_type == "action":
            service_domain = card_cfg.get("service", {}).get("domain", "")
            service_service = card_cfg.get("service", {}).get("service", "")
            service_data = card_cfg.get("data", {})
        else:  # toggle card
            entity = card_cfg.get("entity", "")
            if not entity:
                log_audit(username, action_name, "error", "toggle card has no entity")
                return jsonify_error("toggle card has no entity", 400)
            service_domain = "homeassistant"
            service_service = "toggle"
            service_data = {"entity_id": entity}

        ok, error = call_ha_service(service_domain, service_service, service_data)

        if ok:
            called = f"called {service_domain}.{service_service}"
            log_audit(username, action_name, "success", called)
            return {"ok": True}
        else:
            log_audit(username, action_name, "error", error or "unknown")
            return jsonify_error(error or "HA call failed", 502)


def jsonify_error(message: str, status: int):
    return jsonify(error=message), status


def log_audit(user: str, action: str, result: str, detail: str = ""):
    logger = logging.getLogger("cfh.audit")
    extra = f"user={user} action={action} result={result}"
    if detail:
        extra += f" detail={detail}"
    logger.info(extra)
