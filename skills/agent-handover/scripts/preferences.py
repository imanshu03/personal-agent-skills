#!/usr/bin/env python3
"""Read and write agent-handover macOS preferences."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


PREF_PATH = Path.home() / "Library" / "Application Support" / "agent-handover" / "preferences.json"


def default_preferences() -> dict:
    return {"version": 1, "defaults": {}, "lastUsed": {}}


def load_preferences() -> dict:
    if not PREF_PATH.exists():
        return default_preferences()
    try:
        data = json.loads(PREF_PATH.read_text())
    except json.JSONDecodeError:
        return default_preferences()
    data.setdefault("version", 1)
    data.setdefault("defaults", {})
    data.setdefault("lastUsed", {})
    return data


def save_preferences(data: dict) -> None:
    PREF_PATH.parent.mkdir(parents=True, exist_ok=True)
    PREF_PATH.write_text(json.dumps(data, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage agent-handover preferences.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("get", help="Print preferences as JSON.")

    set_parser = subparsers.add_parser("set", help="Set a default route.")
    set_parser.add_argument("--agent", choices=["claude", "codex"], required=True)
    set_parser.add_argument("--surface", choices=["auto", "app", "cli"], required=True)
    set_parser.add_argument("--terminal", help="Preferred terminal app name for CLI routing.")

    args = parser.parse_args()
    data = load_preferences()

    if args.command == "get":
        print(json.dumps(data, indent=2))
        return

    data["defaults"][args.agent] = {"surface": args.surface}
    if args.terminal:
        data["defaults"][args.agent]["terminal"] = args.terminal
    save_preferences(data)
    print(str(PREF_PATH))


if __name__ == "__main__":
    main()
