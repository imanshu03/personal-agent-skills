#!/usr/bin/env python3
"""Detect local Claude/Codex handover targets on macOS."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path


APP_BUNDLE_IDS = {
    "claude": ["com.anthropic.claude"],
    "codex": ["com.openai.chatgpt", "com.openai.codex"],
}

TERMINALS = ["Terminal", "iTerm", "iTerm2", "Ghostty", "WezTerm", "Warp", "Alacritty", "kitty"]
APP_ROOTS = [
    Path("/Applications"),
    Path("/System/Applications"),
    Path("/System/Applications/Utilities"),
    Path.home() / "Applications",
]


def run(args: list[str]) -> str:
    try:
        return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def find_apps(bundle_ids: list[str], names: list[str]) -> list[str]:
    paths: list[str] = []
    for bundle_id in bundle_ids:
        result = run(["mdfind", f'kMDItemCFBundleIdentifier == "{bundle_id}"'])
        paths.extend([line for line in result.splitlines() if line.endswith(".app")])

    for root in APP_ROOTS:
        for name in names:
            candidate = root / f"{name}.app"
            if candidate.exists():
                paths.append(str(candidate))

    return sorted(set(paths))


def detect() -> dict:
    return {
        "agents": {
            "claude": {
                "cli": shutil.which("claude"),
                "apps": find_apps(APP_BUNDLE_IDS["claude"], ["Claude"]),
            },
            "codex": {
                "cli": shutil.which("codex"),
                "apps": find_apps(APP_BUNDLE_IDS["codex"], ["Codex", "ChatGPT"]),
            },
        },
        "terminals": {name: find_apps([], [name]) for name in TERMINALS},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Detect handover targets.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON.")
    args = parser.parse_args()
    print(json.dumps(detect(), indent=2 if args.pretty else None))


if __name__ == "__main__":
    main()
