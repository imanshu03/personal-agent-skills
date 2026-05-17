#!/usr/bin/env python3
"""Create a resonance work package scaffold."""

from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
import uuid
from pathlib import Path


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    return slug or "resonance-work"


def write_once(path: Path, content: str) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def append_index(index_path: Path, row: str, header: str) -> None:
    if not index_path.exists():
        index_path.write_text(header + row, encoding="utf-8")
        return

    existing = index_path.read_text(encoding="utf-8")
    row_uuid = row.split("|")[1].strip()
    if row_uuid in existing:
        return
    with index_path.open("a", encoding="utf-8") as handle:
        if existing and not existing.endswith("\n"):
            handle.write("\n")
        handle.write(row)


def brainstorm_context(change: str, request: str, today: str, work_uuid: str, base: str, work: str) -> str:
    return f"""# {change} Brainstorm Context

**Date:** {today}
**UUID:** {work_uuid}
**Skill:** resonance
**Invocation namespace:** resonance
**Role model:** Orchestrator/Executor
**Base folder:** {base}
**Work folder:** {work}
**Phase status:** draft

## User Request

{request}

## Project Context

Record relevant repo docs, files, existing behavior, product constraints, and design constraints.

## Explored Approaches

1. Record approach and trade-offs.
2. Record approach and trade-offs.
3. Record approach and trade-offs.

## Approved Direction

Record the direction both agents align on.

## Decisions

- Record decisions and reasons.

## Out Of Scope

- Record explicitly excluded work.

## Acceptance Criteria

- Record observable behavior or artifacts.

## Open Questions

- None
"""


def brainstorm_discussion(change: str, today: str, work_uuid: str) -> str:
    return f"""# {change} Brainstorm Discussion

**Date:** {today}
**UUID:** {work_uuid}
**Context:** context.md
**Phase:** brainstorm
**Status:** draft
**Turns:** 0

## Orchestrator draft - round 1

- Summary:
- Key decisions:
- Risks or assumptions:

## Executor review - round 1

- Findings:
- Missing context:
- Bias or assumption checks:
- Recommendation:

## Orchestrator response - round 1

- Changes made:
- Accepted feedback:
- Rejected feedback with reason:
- Alignment: pending

## User approval

- Status: pending
- Notes:
"""


def plan_context(change: str, today: str, work_uuid: str, base: str, work: str, task_count: int) -> str:
    tasks = "\n".join(
        f"{index}. [Task {index} - Name](../task-{index}/context.md)"
        for index in range(1, task_count + 1)
    ) or "Add approved tasks after plan review."
    graph = "\n".join(f"- Task {index}: define dependencies" for index in range(1, task_count + 1)) or "- Define task dependencies."
    return f"""# {change} Plan Context

**Date:** {today}
**UUID:** {work_uuid}
**Skill:** resonance
**Invocation namespace:** resonance
**Role model:** Orchestrator/Executor
**Base folder:** {base}
**Work folder:** {work}
**Brainstorm context:** ../brainstorm/context.md
**Brainstorm discussion:** ../brainstorm/discussion.md
**Phase status:** draft

## Approved Design

Summarize the approved brainstorm context.

## Architecture

Record implementation approach and boundaries.

## Tasks

{tasks}

## Task Dependency Graph

{graph}

## Parallel Execution Plan

- Define execution waves and write-lock constraints.
- Use one Executor session per active task.
- Prefer one isolated worktree per active Executor session.

## Final Verification

Record commands and checks to run after every task is approved.
"""


def plan_discussion(change: str, today: str, work_uuid: str) -> str:
    return f"""# {change} Plan Discussion

**Date:** {today}
**UUID:** {work_uuid}
**Context:** context.md
**Brainstorm context:** ../brainstorm/context.md
**Phase:** plan
**Status:** draft
**Turns:** 0

## Orchestrator draft - round 1

- Summary:
- Task decomposition:
- Parallelism plan:
- Risks or assumptions:

## Executor review - round 1

- Findings:
- Missing task context:
- Dependency or write-lock concerns:
- Feasibility concerns:
- Recommendation:

## Orchestrator response - round 1

- Changes made:
- Accepted feedback:
- Rejected feedback with reason:
- Alignment: pending

## User approval

- Status: pending
- Notes:
"""


def task_context(index: int, today: str, work_uuid: str) -> str:
    return f"""# Task {index} - Name

**Date:** {today}
**UUID:** {work_uuid}
**Plan:** ../plan/context.md
**Execution:** execution.md
**Depends on:** none
**Parallel group:** wave-1
**Write locks:** unset
**Recommended session:** fresh Executor session
**Recommended workspace:** isolated worktree preferred

## Goal

Describe the task outcome.

## Scope

Define exact boundaries for this task.

## Dependency Inputs

None

## Parallel Safety

- Can run in parallel with: none
- Must not run in parallel with: none
- Shared files or generated artifacts: none

## Files

- Create: none
- Modify: none
- Test: none

## Steps

- [ ] Define exact action.

## Verification

- Run: define command
- Expected: define expected outcome

## Orchestrator Review Checklist

- Verify exact requirements.
- Inspect exact files.
- Run only allowed commands.

## Out Of Scope

- Define excluded work.
"""


def task_execution(index: int, today: str, work_uuid: str, status: str) -> str:
    return f"""# Task {index} - Name Execution

**Date:** {today}
**UUID:** {work_uuid}
**Plan:** ../plan/context.md
**Context:** context.md
**Executor session:** unset
**Workspace/worktree:** unset

## Orchestrator Review Process

- Review only this task.
- Read `../plan/context.md`.
- Read `context.md`.
- Read the Executor's latest completion notes in `execution.md`.
- Inspect only the files in scope for this task.
- Run only commands allowed by `context.md`.
- Append a new `### Orchestrator review - round N` section directly above the `### Status` heading or `Status:` line.
- Update only this task's `Status:` to `approved`, `changes-requested`, or `user-decision-needed`.
- Do not edit other task execution files.
- Do not review future tasks early.

## Executor claim

- Claimed by: unset
- Claimed at: unset
- Workspace/worktree: unset

## Executor completion - round 1

- Summary:
- Files touched:
- Commands run:
- Deviations from context:
- Open questions:

## Orchestrator review - round 1

Orchestrator appends findings or approval here.

### Status

Status: {status}
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a resonance work package scaffold.")
    parser.add_argument("--base-folder", required=True, help="Base coordination folder, such as .resonance")
    parser.add_argument("--change-name", required=True, help="Human-readable change name")
    parser.add_argument("--user-request", default="", help="Original user request")
    parser.add_argument("--uuid", default="", help="Existing UUID to use instead of generating one")
    parser.add_argument("--tasks", type=int, default=0, help="Number of task folders to scaffold")
    parser.add_argument("--repo-root", default=".", help="Repository root for resolving relative paths")
    parser.add_argument("--include-plan", action="store_true", help="Create plan files before tasks are known")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.tasks < 0:
        print("--tasks must be zero or greater", file=sys.stderr)
        return 2

    repo_root = Path(args.repo_root).resolve()
    base_folder = Path(args.base_folder)
    if not base_folder.is_absolute():
        base_folder = repo_root / base_folder
    base_folder.mkdir(parents=True, exist_ok=True)

    work_uuid = args.uuid or str(uuid.uuid4())
    change_slug = slugify(args.change_name)
    work_folder = base_folder / f"{change_slug}-{work_uuid}"
    work_folder.mkdir(parents=True, exist_ok=False)

    today = dt.date.today().isoformat()
    request = args.user_request or "Record the original user request."
    relative_base = str(base_folder.relative_to(repo_root)) if base_folder.is_relative_to(repo_root) else str(base_folder)
    relative_work = str(work_folder.relative_to(repo_root)) if work_folder.is_relative_to(repo_root) else str(work_folder)

    index_header = "# Resonance Work Index\n\n| UUID | Change | Work folder | State | Active tasks |\n| --- | --- | --- | --- | --- |\n"
    index_row = f"| {work_uuid} | {args.change_name} | `{relative_work}` | brainstorm-draft | none |\n"
    append_index(base_folder / "index.md", index_row, index_header)

    write_once(
        work_folder / "brainstorm" / "context.md",
        brainstorm_context(args.change_name, request, today, work_uuid, relative_base, relative_work),
    )
    write_once(work_folder / "brainstorm" / "discussion.md", brainstorm_discussion(args.change_name, today, work_uuid))

    if args.include_plan or args.tasks:
        write_once(work_folder / "plan" / "context.md", plan_context(args.change_name, today, work_uuid, relative_base, relative_work, args.tasks))
        write_once(work_folder / "plan" / "discussion.md", plan_discussion(args.change_name, today, work_uuid))

    for index in range(1, args.tasks + 1):
        task_dir = work_folder / f"task-{index}"
        write_once(task_dir / "context.md", task_context(index, today, work_uuid))
        status = "not-started" if index == 1 else "blocked"
        write_once(task_dir / "execution.md", task_execution(index, today, work_uuid, status))

    print(work_folder)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
