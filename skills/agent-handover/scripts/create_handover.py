#!/usr/bin/env python3
"""Create a structured handover file for another agent."""

from __future__ import annotations

import argparse
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import detect_invocation


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_PATH = ROOT / "assets" / "handover.template.md"


def run(args: list[str], cwd: Path) -> str:
    try:
        return subprocess.check_output(args, cwd=cwd, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def git_root(cwd: Path) -> Path:
    root = run(["git", "rev-parse", "--show-toplevel"], cwd)
    return Path(root) if root else cwd


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:80] or "agent-handover"


def table_rows(items: list[str], columns: int) -> str:
    if not items:
        return "| _None captured_ | " + " | ".join([""] * (columns - 1)) + " |"
    rows = []
    for item in items:
        cells = [f"`{item}`"] + [""] * (columns - 1)
        rows.append("| " + " | ".join(cells) + " |")
    return "\n".join(rows)


def output_dir(repo: Path) -> Path:
    handover_dir = repo / "docs" / "handover"
    if handover_dir.exists():
        return handover_dir
    return repo / ".agent-handover"


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an agent handover markdown file.")
    parser.add_argument("--task", required=True, help="Short task title.")
    parser.add_argument("--from-agent", choices=["auto", "codex", "claude"], default="auto")
    parser.add_argument("--to-agent", choices=["auto", "codex", "claude"], default="auto")
    parser.add_argument("--destination", choices=["auto", "app", "cli"], default="auto")
    parser.add_argument("--status", default="in progress")
    parser.add_argument("--user-goal", default="_Fill in the latest user goal._")
    parser.add_argument("--context-summary", default="_Fill in the conversation context the script cannot infer._")
    parser.add_argument("--last-action", default="_Fill in the last meaningful action._")
    parser.add_argument("--next-action", default="_Fill in the recommended next action._")
    parser.add_argument("--brand-area", default="_Not specified._")
    parser.add_argument("--audience", default="_Not specified._")
    parser.add_argument("--design-tone", default="_Not specified._")
    parser.add_argument("--source-docs", default="_Not captured._")
    parser.add_argument("--base-commit", default="")
    parser.add_argument("--cwd", default=".", help="Workspace directory.")
    args = parser.parse_args()

    detected_agent, detection_reason = detect_invocation.detect_source_agent()
    from_agent = detected_agent if args.from_agent == "auto" else args.from_agent
    if args.from_agent != "auto":
        detection_reason = f"explicit --from-agent {args.from_agent}; detection saw {detection_reason}"
    to_agent = args.to_agent
    if to_agent == "auto":
        to_agent = detect_invocation.target_for(from_agent)
    if not from_agent:
        from_agent = "_unknown_"
    if not to_agent:
        raise SystemExit(
            "Could not infer --to-agent. Pass --to-agent codex or --to-agent claude."
        )

    cwd = Path(args.cwd).resolve()
    repo = git_root(cwd)
    out = output_dir(repo)
    out.mkdir(parents=True, exist_ok=True)
    out_path = out / f"{slugify(args.task)}.md"

    branch = run(["git", "branch", "--show-current"], repo) or "_unknown_"
    head = run(["git", "rev-parse", "HEAD"], repo) or "_unknown_"
    status = run(["git", "status", "--short"], repo) or "_clean_"
    recent = run(["git", "log", "--oneline", "-8"], repo) or "_No commits captured._"
    changed = [line[3:] for line in status.splitlines() if len(line) > 3 and line != "_clean_"]
    diff_summary = run(["git", "diff", "--stat"], repo) or "_No unstaged diff summary captured._"
    base_commit = args.base_commit or "_unknown; fill if task start point is known_"

    replacements = {
        "TASK_TITLE": args.task,
        "FROM_AGENT": from_agent,
        "TO_AGENT": to_agent,
        "SOURCE_DETECTION": detection_reason,
        "DESTINATION": args.destination,
        "CREATED_AT": datetime.now(timezone.utc).isoformat(),
        "WORKSPACE": str(repo),
        "WORKTREE": str(repo),
        "BRANCH": branch,
        "BASE_COMMIT": base_commit,
        "HEAD_COMMIT": head,
        "USER_GOAL": args.user_goal,
        "STATUS": args.status,
        "LAST_ACTION": args.last_action,
        "NEXT_ACTION": args.next_action,
        "CONTEXT_SUMMARY": args.context_summary,
        "DECISIONS_TABLE": "| _Fill in_ | _Fill in_ | _Fill in_ |",
        "CONSTRAINTS": "- _Fill in repo, user, platform, and safety constraints._",
        "BRAND_AREA": args.brand_area,
        "AUDIENCE": args.audience,
        "DESIGN_TONE": args.design_tone,
        "SOURCE_DOCS": args.source_docs,
        "FILES_TABLE": table_rows(changed, 3),
        "GIT_STATUS": status,
        "RECENT_COMMITS": recent,
        "DIFF_SUMMARY": diff_summary,
        "COMMANDS_TABLE": "| _Fill in_ | _not captured_ | _Only list commands actually run._ |",
        "TESTS_RUN": "_Fill in._",
        "TYPECHECK_RUN": "_Fill in._",
        "LINT_RUN": "_Fill in._",
        "MANUAL_VERIFICATION": "_Fill in._",
        "REMAINING_RISK": "_Fill in._",
        "BLOCKERS": "- _Fill in, or write None._",
        "DO_NOT_LOSE": "- _Fill in subtle context._",
        "HANDOVER_PATH": str(out_path),
    }

    content = TEMPLATE_PATH.read_text()
    for key, value in replacements.items():
        content = content.replace("{{" + key + "}}", value)
    out_path.write_text(content)
    print(str(out_path))


if __name__ == "__main__":
    main()
