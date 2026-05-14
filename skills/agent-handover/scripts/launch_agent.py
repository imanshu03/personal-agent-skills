#!/usr/bin/env python3
"""Launch a receiving agent from a handover file on macOS."""

from __future__ import annotations

import argparse
import json
import shlex
import subprocess
from pathlib import Path

import detect_targets
import preferences


def run(args: list[str]) -> int:
    return subprocess.call(args)


def osascript(script: str) -> int:
    return run(["osascript", "-e", script])


def command_for(agent: str, handover: Path) -> str:
    prompt = (
        "Continue the task from this handover file: "
        f"{handover}. Start by reading it, checking git state, and proceeding from the recommended next action. "
        "Do not revert user changes."
    )
    return f"{shlex.quote(agent)} {shlex.quote(prompt)}"


def launch_terminal(terminal: str, command: str) -> int:
    if terminal == "Terminal":
        return osascript(f'tell application "Terminal" to do script {json.dumps(command)}\ntell application "Terminal" to activate')
    if terminal == "iTerm":
        script = (
            'tell application "iTerm"\n'
            "  create window with default profile\n"
            f"  tell current session of current window to write text {json.dumps(command)}\n"
            "  activate\n"
            "end tell"
        )
        return osascript(script)
    return run(["open", "-a", terminal, "--args", "-e", command])


def choose_route(agent: str, requested_surface: str, requested_terminal: str | None) -> tuple[str, str | None]:
    prefs = preferences.load_preferences()
    agent_pref = prefs.get("defaults", {}).get(agent, {})
    surface = requested_surface
    if surface == "auto":
        surface = agent_pref.get("surface", "cli")
    terminal = requested_terminal or agent_pref.get("terminal") or "Terminal"
    return surface, terminal


def terminal_is_available(targets: dict, terminal: str) -> bool:
    return bool(targets.get("terminals", {}).get(terminal))


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch a target agent for a handover.")
    parser.add_argument("--to-agent", choices=["claude", "codex"], required=True)
    parser.add_argument("--handover", required=True)
    parser.add_argument("--surface", choices=["auto", "app", "cli"], default="auto")
    parser.add_argument("--terminal", help="Terminal app name for CLI routing.")
    args = parser.parse_args()

    handover = Path(args.handover).resolve()
    targets = detect_targets.detect()
    surface, terminal = choose_route(args.to_agent, args.surface, args.terminal)
    agent_info = targets["agents"][args.to_agent]

    if surface == "cli":
        if not agent_info.get("cli"):
            raise SystemExit(f"{args.to_agent} CLI was not detected.")
        command = command_for(args.to_agent, handover)
        chosen_terminal = terminal or "Terminal"
        if not terminal_is_available(targets, chosen_terminal):
            chosen_terminal = "Terminal"
        code = launch_terminal(chosen_terminal, command)
        if code == 0:
            prefs = preferences.load_preferences()
            prefs["lastUsed"] = {
                "targetAgent": args.to_agent,
                "surface": "cli",
                "terminal": chosen_terminal,
            }
            preferences.save_preferences(prefs)
        raise SystemExit(code)

    apps = agent_info.get("apps", [])
    if surface == "app" and apps:
        code = run(["open", "-a", apps[0]])
        print(f"Opened {apps[0]}. Paste the receiving prompt from {handover}.")
        raise SystemExit(code)

    print(f"No reliable {surface} route found. Handover file: {handover}")
    print(command_for(args.to_agent, handover))


if __name__ == "__main__":
    main()
