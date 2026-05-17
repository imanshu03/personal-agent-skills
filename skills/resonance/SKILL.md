---
name: resonance
description: Coordinate large changes through a review-gated Orchestrator/Executor workflow where Codex is the Orchestrator, Claude Code CLI is a long-lived Executor, and both coordinate through a root control.md baton file. Use when a feature, bug fix, refactor, migration, documentation change, design implementation, or release task is large enough to split into ordered tasks with strict brainstorm, plan, execution, review, and final-verification gates; also use for /resonance:orchestrator, /resonance:executor, and requests to implement with resonance.
---

# Resonance

Use resonance to coordinate a large change through durable markdown artifacts, one root control baton file, a long-lived Claude Code Executor session, and strict Orchestrator review gates.

Personal runtime mapping:

- Treat Codex as the Orchestrator.
- Treat Claude Code CLI as the Executor.
- Treat `<work-folder>/control.md` as the only control-transfer surface.
- Have the user start one Claude Code CLI Executor with `/resonance:executor <uuid>` after Orchestrator bootstrap.
- Have Codex and Claude monitor `control.md`; put feature context, reviews, plans, and task completion notes in their phase/task files, not in `control.md`.

## Core Rule

Never let an Executor move to another task until the Orchestrator approves the current task and explicitly assigns the next task through `control.md`.

## Invocation Modes

Interpret these requests as Orchestrator mode. In Orchestrator mode, bootstrap the coordination files, return the Executor command to the user before creating feature context, and coordinate through `control.md`; do not act as the Executor for implementation tasks unless the user explicitly asks for a local dry run.

```text
/resonance:orchestrator
Let's implement <change> with resonance.
Use resonance for <change>.
```

Interpret these requests as Executor mode. Executor mode is meant to run inside a long-lived Claude Code CLI terminal session started by the user from the Orchestrator-provided command.

```text
/resonance:executor <uuid>
```

In Executor mode, locate the existing work folder by UUID, read `<work-folder>/control.md`, register the Executor session there, set `Owner: orchestrator`, `Status: awaiting-orchestrator`, and `Next action: executor-ready`, start a Claude Code `Monitor` on the absolute `control.md` path, and wait for `Owner: executor`. Do not create a new work folder for an unknown UUID.

## First Moves

1. Identify the repo or workspace root.
2. Ask where to store resonance coordination files unless the base folder is already documented in the repo or conversation.
3. Prefer `.resonance` or `docs/resonance` as base-folder options.
4. Generate a UUID and a change slug.
5. Create `<base-folder>/<change-slug>-<uuid>/`.
6. Create `<work-folder>/control.md`.
7. Create or update `<base-folder>/index.md`.
8. Return this command to the user before writing brainstorm, plan, or task context:

```text
Run this in Claude Code CLI:

/resonance:executor <uuid>
```

9. Use this skill's `scripts/init_work_package.py` when it helps scaffold the folder and starter files.

Example:

```bash
python /path/to/resonance/scripts/init_work_package.py \
  --base-folder .resonance \
  --change-name "Add saved searches" \
  --user-request "Build saved search support end to end" \
  --bootstrap-only
```

The script prints the work folder and `/resonance:executor <uuid>` command.

## Orchestrator Workflow

1. Bootstrap the work folder and `control.md`, then return `/resonance:executor <uuid>` to the user before substantive feature work.
2. Create one Codex automation for the absolute `control.md` path when automation tools are available.
3. Wait for the Executor to register its session and global `Monitor` in `control.md`, or proceed only if the user explicitly asks for an Orchestrator-only draft.
4. Use Superpowers brainstorming when available to explore context, constraints, approaches, trade-offs, and acceptance criteria.
5. Write the draft design direction into `<work-folder>/brainstorm/context.md`.
6. Record the draft in `<work-folder>/brainstorm/discussion.md`.
7. Update `control.md` with `Owner: executor`, `Status: awaiting-executor`, `Phase: brainstorm`, `Target: brainstorm/discussion.md`, and `Next action: review-brainstorm`.
8. Let the Executor monitor wake, review `brainstorm/context.md`, append its thoughts to `brainstorm/discussion.md`, then return the baton with `Owner: orchestrator` and `Status: awaiting-orchestrator`.
9. Repeat baton turns through `control.md` until both agents mark `Alignment: aligned` in `brainstorm/discussion.md`, then ask the user to approve the aligned brainstorm context.
10. Use Superpowers writing-plans when available to create `<work-folder>/plan/context.md`.
11. Hand off plan review through `control.md` with `Phase: plan`, `Target: plan/discussion.md`, and `Next action: review-plan`.
12. Let baton turns continue until both agents mark `Alignment: aligned` in `plan/discussion.md`, then ask the user to approve the aligned plan context.
13. Create one `task-N/` folder per approved task, each with `context.md` and `execution.md`.
14. Self-review all task contexts for missing requirements, vague steps, overlapping write locks, missing verification, inconsistent names, and placeholders.
15. Assign only ready tasks whose dependencies are approved and whose write locks do not overlap by updating `control.md` with `Owner: executor`, `Phase: task-N`, `Target: task-N/execution.md`, and `Next action: execute-task`.
16. Review each task independently through its `execution.md` after the Executor returns the baton with `Status: awaiting-orchestrator`.
17. Run final verification only after every task is approved.

If a phase or task exceeds six review/response turns without alignment or approval, mark it `user-decision-needed` and ask the user to decide.

## Executor Workflow

1. Locate the work folder by UUID.
2. Read `<work-folder>/control.md`.
3. Register the Executor session in `control.md` without adding feature context, then set `Owner: orchestrator`, `Status: awaiting-orchestrator`, and `Next action: executor-ready`.
4. Start one Claude Code `Monitor` on the absolute `control.md` path.
5. When `control.md` says `Owner: executor`, read only the target files named by `Target:` and the context files required for that `Next action:`.
6. If reviewing a phase, read that phase's `context.md` and `discussion.md`, append an Executor review to `discussion.md`, then update `control.md` with `Owner: orchestrator`, `Status: awaiting-orchestrator`, and a concise completion note.
7. If implementing a task, claim exactly the task named by `Phase: task-N`, confirm dependencies and write locks, implement only that task, record completion in `execution.md`, set task status to `awaiting-orchestrator-review`, then update `control.md` with `Owner: orchestrator`, `Status: awaiting-orchestrator`, and a concise completion note.
8. Stop until the global `control.md` monitor wakes the session again.

Do not read sibling task folders unless the current task context explicitly names them as dependency inputs.

## Control Baton And Monitors

Every resonance run uses one root baton file: `<work-folder>/control.md`. This file is only for control transfer. Do not store feature context, requirements, implementation details, review substance, or completion summaries longer than one concise status line in it.

For Claude Code CLI v2.1.98 or later, the Executor must use Claude Code's built-in `Monitor` tool on `control.md` by default. Do not hand-write a shell monitor for normal runs. The Codex Orchestrator should create one Codex automation for the same absolute `control.md` path when automation tools are available.

Orchestrator duties:

1. Create or update `control.md` whenever the baton changes.
2. Create one Codex automation that watches `control.md`, responds only when `Owner: orchestrator` and `Status: awaiting-orchestrator`, and no-ops otherwise.
3. Put detailed Orchestrator responses in `brainstorm/discussion.md`, `plan/discussion.md`, or `task-N/execution.md`.
4. Hand the baton to the Executor by setting `Owner: executor`, `Status: awaiting-executor`, `Phase: <phase-or-task>`, `Target: <relative-target-file>`, and `Next action: <action>`.
5. Hand the baton to the user by setting `Owner: user` and `Status: awaiting-user`.
6. Stop or delete the Codex automation when `Status: complete` or `Status: user-decision-needed`.

Executor duties:

1. Register its session in `control.md`, set `Owner: orchestrator`, `Status: awaiting-orchestrator`, and `Next action: executor-ready`, then start one Claude Code `Monitor` on the absolute `control.md` path.
2. Wake only when `Owner: executor` and `Status: awaiting-executor`.
3. Read `Phase:`, `Target:`, and `Next action:` to decide which phase/task files to inspect.
4. Write detailed Executor output to the target `discussion.md` or `execution.md` file.
5. Return the baton by setting `Owner: orchestrator`, `Status: awaiting-orchestrator`, `Updated by: executor`, and a concise event log entry.
6. Keep the global monitor running until `Status: complete` or `Status: user-decision-needed`.

Use `<work-folder>/terminal/monitors/` only for fallback shell monitor artifacts when Claude Code `Monitor` is unavailable:

```text
fallback-monitor-control.sh
fallback-monitor-control.log
```

The monitor contract is required for real resonance runs. Skip it only for an explicitly local dry run, unavailable automation tools, unavailable Claude Code `Monitor` support, or a user-approved headless smoke test; record the skip or fallback reason in `<work-folder>/control.md`.

## Review Rules

Review as a strict code reviewer, not as a second implementer.

For every task review:

1. Read the plan, task context, and task execution file.
2. Inspect only files in scope for the task.
3. Compare the actual diff to the Executor's files-touched list.
4. Confirm all writes stay inside declared write locks.
5. Run only commands allowed by the task context.
6. Append `### Orchestrator review - round N` to the task execution file.
7. Update only that task's `Status:` line.

Use this finding shape:

```markdown
1. Severity: blocker | high | medium | low | nit
   Where: file:line or process
   Finding: One or two sentences.
   Suggested fix: One or two sentences.
```

Use this approval shape:

```markdown
No findings. Approved.

Status: approved
```

## Parallelism

Plan work as a dependency graph, not only as a numbered list.

- Prefer one long-lived Executor session per resonance run.
- Prefer one isolated git worktree per active Executor session.
- Use a shared checkout only when active tasks have explicitly disjoint write locks and the repo tooling will not mutate shared files.
- Never assign two tasks with overlapping files, directories, generated artifacts, lockfiles, migration history, or shared package boundaries.
- Summarize dependency outputs in dependent task contexts instead of asking Executors to read earlier execution logs.

## Executor Startup

The Orchestrator does not spawn phase or task Executor terminals by default. After bootstrap, show the user:

```text
Run this in Claude Code CLI:

/resonance:executor <uuid>
```

The Executor command starts a long-lived session. That session monitors `control.md`, performs only the action currently assigned to `Owner: executor`, writes detailed work to the target file, and returns the baton through `control.md`.

If a headless run is explicitly needed, reuse the same `query` shape with a transient log:

```bash
#!/usr/bin/env bash
set -euo pipefail

# Self-delete the runner AND the tee'd log on exit. The log captures the
# full Executor prompt and session output; treat it as transient and do
# not leave it on disk.
trap 'rm -f -- "<absolute-runner-script-path>" "<absolute-log-path>"' EXIT

cd "<absolute-repo-or-worktree-path>"
mkdir -p "<work-folder>/terminal/logs"

IFS= read -r -d '' query <<'EOF' || true
/resonance:executor <uuid>
EOF

claude -p \
  --permission-mode acceptEdits \
  --allowedTools Read,Edit,Bash,Monitor \
  --append-system-prompt "You are Claude Code CLI running as the resonance Executor. Follow Executor mode exactly." \
  "$query" 2>&1 | tee "<absolute-log-path>"
```

## Reference

Read `references/protocol.md` when you need exact artifact schemas, status values, UUID lookup rules, automation prompts, phase discussion templates, task execution templates, or final handoff/review prompt shapes.
