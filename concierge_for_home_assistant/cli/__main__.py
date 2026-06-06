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

"""Concierge for Home Assistant – CLI entry point."""

import argparse
import sys

from concierge_for_home_assistant.cli.hash_password import main as hash_password_main
from concierge_for_home_assistant.cli.setup import main as setup_main


def main():
    parser = argparse.ArgumentParser(description="Concierge for Home Assistant")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser(
        "hash-password",
        help="Generate a password hash for secrets/users.yaml",
    )
    subparsers.add_parser(
        "setup",
        help="Interactive setup for configuration and secrets",
    )

    args = parser.parse_args()

    if args.command == "hash-password":
        hash_password_main()
    elif args.command == "setup":
        # Pass the stage argument from command line if needed, or handle via setup interactively
        # For compatibility with previous usage: python -m hg.cli.setup <stage>
        setup_main()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
