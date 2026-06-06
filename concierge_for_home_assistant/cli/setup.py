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

"""Interactive setup script: creates config.yaml (prod only) and writes secrets."""

import getpass
import pathlib
import re
import secrets
import sys


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m concierge_for_home_assistant setup <stage>")
        sys.exit(1)

    stage = sys.argv[1]
    template = pathlib.Path(stage) / "config.yaml.template"
    config = pathlib.Path(stage) / "config.yaml"
    secrets_dir = pathlib.Path(stage) / "secrets"

    # Bei prod: config.yaml aus Template erzeugen und HA URL abfragen
    if template.exists():
        url = input("Home Assistant URL (z.B. http://192.168.1.10:8123): ").strip()
        content = template.read_text(encoding="utf-8")
        content = re.sub(r'(  url:\s*)".*?"', f'  url: "{url}"', content, count=1)
        config.write_text(content, encoding="utf-8")
        print(f"config.yaml erstellt mit HA URL: {url}")

    # Secrets
    secrets_dir.mkdir(parents=True, exist_ok=True)
    token = getpass.getpass("HA Token: ")
    (secrets_dir / "ha_token").write_text(token.strip())
    print("HA Token gespeichert.")

    flask_secret = secrets.token_hex(32)
    (secrets_dir / "flask_secret_key").write_text(flask_secret)
    print("Flask Secret generiert und gespeichert.")


if __name__ == "__main__":
    main()
