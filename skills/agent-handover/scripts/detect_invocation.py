#!/usr/bin/env python3
"""Detect which agent surface invoked the handover skill."""

from __future__ import annotations

import argparse
import json
import os
import subprocess


AGENTS = {"codex", "claude"}


def _run(args: list[str]) -> str:
    try:
        return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def _parent_commands(limit: int = 8) -> list[str]:
    commands: list[str] = []
    pid = os.getpid()
    for _ in range(limit):
        row = _run(["ps", "-o", "ppid=,comm=", "-p", str(pid)])
        if not row:
            break
        parts = row.strip().split(None, 1)
        if not parts:
            break
        try:
            pid = int(parts[0])
        except ValueError:
            break
        if len(parts) > 1:
            commands.append(os.path.basename(parts[1]).lower())
        if pid <= 1:
            break
    return commands


def detect_source_agent() -> tuple[str | None, str]:
    bundle_id = os.environ.get("__CFBundleIdentifier", "")
    if bundle_id == "com.openai.codex":
        return "codex", "__CFBundleIdentifier=com.openai.codex"
    if bundle_id == "com.anthropic.claude":
        return "claude", "__CFBundleIdentifier=com.anthropic.claude"

    if any(key.startswith("CODEX_") for key in os.environ):
        return "codex", "CODEX_* environment variable"
    if any(key.startswith(("CLAUDE_CODE", "CLAUDECODE")) for key in os.environ):
        return "claude", "CLAUDE_CODE* environment variable"

    for command in _parent_commands():
        if command in AGENTS:
            return command, f"parent process {command}"
        if "codex" in command:
            return "codex", f"parent process {command}"
        if "claude" in command:
            return "claude", f"parent process {command}"

    return None, "no Codex/Claude invocation signal detected"


def main() -> None:
    parser = argparse.ArgumentParser(description="Detect the agent that invoked the handover skill.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON.")
    args = parser.parse_args()

    source_agent, reason = detect_source_agent()
    payload = {
        "workedOnBy": source_agent,
        "reason": reason,
    }
    print(json.dumps(payload, indent=2 if args.pretty else None))


if __name__ == "__main__":
    main()
