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

import getpass

from werkzeug.security import generate_password_hash


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def main():
    username = input("Benutzername: ").strip()
    if not username:
        print("Fehler: Kein Benutzername angegeben.")
        return

    password = getpass.getpass(f"Passwort für '{username}': ")
    if not password:
        print("Fehler: Kein Passwort angegeben.")
        return

    hashed = hash_password(password)
    print("")
    print("Eintrag für secrets/users.yaml:")
    print("")
    print(f"  {username}:")
    print(f'    password_hash: "{hashed}"')
    print("    roles:")
    print("      - deine_rolle")


if __name__ == "__main__":
    main()
