#!/usr/bin/env python3
"""Launch a receiving agent from a handover file on macOS."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path

import detect_targets
import detect_invocation
import preferences


APP_NAMES = {
    "claude": "Claude.app",
    "codex": "Codex.app",
}


def run(args: list[str]) -> int:
    return subprocess.call(args)


def osascript(script: str) -> int:
    return run(["osascript", "-e", script])


def command_for(agent: str, handover: Path) -> str:
    prompt = (
        "Continue the task from this handover file: "
        f"{handover}. Start by reading it, checking git state, and proceeding from the recommended next action. "
        "Do not revert user changes. When you need clarification, prefer structured/generative question UI if your runtime supports it; otherwise ask concise plain-text questions."
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


def choose_route(agent: str, requested_surface: str, requested_terminal: str | None) -> tuple[str, str | None, bool]:
    prefs = preferences.load_preferences()
    agent_pref = prefs.get("defaults", {}).get(agent, {})
    surface = requested_surface
    if surface == "auto":
        surface = agent_pref.get("surface", "cli")
    preferred_terminal = requested_terminal or agent_pref.get("terminal")
    terminal = preferred_terminal or "Terminal"
    return surface, terminal, preferred_terminal is None


def terminal_is_available(targets: dict, terminal: str) -> bool:
    return bool(targets.get("terminals", {}).get(terminal))


def available_terminals(targets: dict) -> list[str]:
    return [name for name, paths in targets.get("terminals", {}).items() if paths]


def choose_app(agent: str, apps: list[str]) -> str | None:
    preferred_name = APP_NAMES[agent]
    for app in apps:
        if Path(app).name == preferred_name:
            return app
    return apps[0] if apps else None


def agent_from_handover(handover: Path) -> str | None:
    try:
        content = handover.read_text()
    except OSError:
        return None
    match = re.search(r"^- To agent:\s*(codex|claude)\s*$", content, re.MULTILINE)
    return match.group(1) if match else None


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch a target agent for a handover.")
    parser.add_argument("--to-agent", choices=["auto", "claude", "codex"], default="auto")
    parser.add_argument("--handover", required=True)
    parser.add_argument("--surface", choices=["auto", "app", "cli"], default="auto")
    parser.add_argument("--terminal", help="Terminal app name for CLI routing.")
    args = parser.parse_args()

    handover = Path(args.handover).resolve()
    to_agent = args.to_agent
    if to_agent == "auto":
        to_agent = agent_from_handover(handover)
    if to_agent == "auto" or not to_agent:
        source_agent, _reason = detect_invocation.detect_source_agent()
        to_agent = detect_invocation.target_for(source_agent)
    if not to_agent:
        raise SystemExit(
            "Could not infer --to-agent. Pass --to-agent codex or --to-agent claude."
        )

    targets = detect_targets.detect()
    surface, terminal, terminal_was_defaulted = choose_route(to_agent, args.surface, args.terminal)
    agent_info = targets["agents"][to_agent]

    if surface == "cli":
        if not agent_info.get("cli"):
            raise SystemExit(f"{to_agent} CLI was not detected.")
        command = command_for(to_agent, handover)
        chosen_terminal = terminal or "Terminal"
        if not terminal_is_available(targets, chosen_terminal):
            print(
                f"Preferred terminal {chosen_terminal!r} was not detected; falling back to Terminal.",
                file=sys.stderr,
            )
            chosen_terminal = "Terminal"
        elif terminal_was_defaulted:
            detected = ", ".join(available_terminals(targets)) or "none detected"
            print(
                "No saved terminal preference was found; using Terminal. "
                f"Detected terminals: {detected}. "
                f"Save a default with: python3 skills/agent-handover/scripts/preferences.py set --agent {to_agent} --surface cli --terminal <TerminalName>",
                file=sys.stderr,
            )
        code = launch_terminal(chosen_terminal, command)
        if code == 0:
            prefs = preferences.load_preferences()
            prefs["lastUsed"] = {
                "targetAgent": to_agent,
                "surface": "cli",
                "terminal": chosen_terminal,
            }
            preferences.save_preferences(prefs)
        raise SystemExit(code)

    apps = agent_info.get("apps", [])
    app = choose_app(to_agent, apps)
    if surface == "app" and app:
        code = run(["open", app])
        print(f"Opened {app}. App routing cannot inject the handover automatically.")
        print("Paste this prompt into the receiving agent:")
        print(command_for(to_agent, handover))
        raise SystemExit(code)

    print(f"No reliable {surface} route found. Handover file: {handover}")
    print(command_for(to_agent, handover))


if __name__ == "__main__":
    main()
