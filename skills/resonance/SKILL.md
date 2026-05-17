---
name: resonance
description: Coordinate large changes through a review-gated Orchestrator/Executor workflow where Codex is the Orchestrator and dispatches Claude Code CLI Executor sessions in the Codex Mac app terminal. Use when a feature, bug fix, refactor, migration, documentation change, design implementation, or release task is large enough to split into ordered tasks with strict brainstorm, plan, execution, review, and final-verification gates; also use for /resonance orchestrator, /resonance executor, requests to implement with resonance, and requests to launch Codex-terminal Claude Code Executor sessions for a resonance task.
---

# Resonance

Use resonance to coordinate a large change through durable markdown artifacts, Codex app terminal-launched Claude Code Executor sessions, and strict Orchestrator review gates.

Personal runtime mapping:

- Treat Codex as the Orchestrator.
- Treat Claude Code CLI as the Executor.
- Treat the Codex Mac app terminal as the terminal runtime.
- Have the Orchestrator dispatch each phase review or task execution as its own visible Claude Code CLI session in the Codex app terminal, record the returned terminal session handle when available, and monitor the session alongside the durable markdown channel.

## Core Rule

Never let an Executor move to another task until the Orchestrator approves the current task and explicitly assigns or dispatches the next task.

## Invocation Modes

Interpret these requests as Orchestrator mode. In Orchestrator mode, create the coordination files and dispatch terminal-based Claude Code Executor sessions; do not act as the Executor for implementation tasks unless the user explicitly asks for a local dry run.

```text
/resonance orchestrator
Let's implement <change> with resonance.
Use resonance for <change>.
```

Interpret these requests as Executor mode. Executor mode is meant to run inside a Claude Code CLI terminal session created by the Orchestrator.

```text
/resonance executor <uuid>
/resonance executor <uuid> task-N
/resonance executor <uuid> brainstorm
/resonance executor <uuid> plan
```

In Executor mode, locate the existing work folder by UUID before doing anything else. Do not create a new work folder for an unknown UUID.

## First Moves

1. Identify the repo or workspace root.
2. Ask where to store resonance coordination files unless the base folder is already documented in the repo or conversation.
3. Prefer `.resonance` or `docs/resonance` as base-folder options.
4. Generate a UUID and a change slug.
5. Create `<base-folder>/<change-slug>-<uuid>/`.
6. Create or update `<base-folder>/index.md`.
7. Use this skill's `scripts/init_work_package.py` when it helps scaffold the folder and starter files.

Example:

```bash
python /path/to/resonance/scripts/init_work_package.py \
  --base-folder .resonance \
  --change-name "Add saved searches" \
  --user-request "Build saved search support end to end"
```

## Orchestrator Workflow

1. Use Superpowers brainstorming when available to explore context, constraints, approaches, trade-offs, and acceptance criteria.
2. Write the draft design direction into `<work-folder>/brainstorm/context.md`.
3. Record the draft and review loop in `<work-folder>/brainstorm/discussion.md`.
4. Create a Codex phase monitor automation for the absolute brainstorm `discussion.md` path when automation tools are available.
5. Dispatch a Claude Code CLI Executor phase review in a Codex app terminal session with `/resonance executor <uuid> brainstorm`.
6. Let the Codex automation and Executor monitor exchange async turns through `discussion.md` until both agents mark `Alignment: aligned`.
7. Ask the user to approve the aligned brainstorm context before planning.
8. Use Superpowers writing-plans when available to create `<work-folder>/plan/context.md`.
9. Create a Codex phase monitor automation for the absolute plan `discussion.md` path when automation tools are available.
10. Dispatch a Claude Code CLI Executor plan review in a Codex app terminal session with `/resonance executor <uuid> plan`.
11. Let the Codex automation and Executor monitor exchange async turns through `discussion.md` until both agents mark `Alignment: aligned`.
12. Ask the user to approve the aligned plan context before implementation.
13. Create one `task-N/` folder per approved task, each with `context.md` and `execution.md`.
14. Self-review all task contexts for missing requirements, vague steps, overlapping write locks, missing verification, inconsistent names, and placeholders.
15. Before dispatching each ready task, create a Codex task monitor automation for that task's absolute `execution.md` path when automation tools are available.
16. Dispatch only ready tasks whose dependencies are approved and whose write locks do not overlap.
17. Review each task independently through its `execution.md`.
18. Run final verification only after every task is approved.

If a phase or task exceeds six review/response turns without alignment or approval, mark it `user-decision-needed` and ask the user to decide.

## Executor Workflow

1. Locate the work folder by UUID.
2. Read `plan/context.md`.
3. If reviewing a phase, read that phase's `context.md` and `discussion.md`, append an Executor review, create an Executor phase monitor for that absolute `discussion.md` path, and stop.
4. If implementing a task, claim exactly one ready task.
5. Read only `plan/context.md`, the selected task's `context.md`, the selected task's `execution.md`, and repo files required by that task.
6. Confirm the task status is `not-started` or `changes-requested`.
7. Confirm dependencies are approved and write locks do not conflict with active work.
8. Set the task status to `in-progress`.
9. Implement only the current task.
10. Record summary, files touched, commands run, deviations, and open questions in `execution.md`.
11. Set status to `awaiting-orchestrator-review`.
12. Create an Executor task monitor for that task's absolute `execution.md` path.
13. Stop until Orchestrator approval or changes requested.

Do not read sibling task folders unless the current task context explicitly names them as dependency inputs.

## Async Monitors

Every active phase or task needs a paired monitor loop when local automation and terminal tools are available. The phase channel is `<work-folder>/<phase>/discussion.md`; the task channel is `<work-folder>/task-N/execution.md`.

For Claude Code CLI v2.1.98 or later, the Executor must use Claude Code's built-in `Monitor` tool by default. Do not hand-write a shell monitor for normal runs. The `Monitor` tool creates and runs its own background watch script and feeds output lines back into the same Claude Code session. Use a shell monitor only as a documented fallback when `Monitor` is unavailable, disabled, or not allowed.

Orchestrator duties:

1. Before dispatching a brainstorm or plan Executor review, create a Codex phase monitor automation for the absolute `discussion.md` path.
2. The phase automation reads the phase `context.md`, responds only when a new `### Executor review - round N` is waiting, appends `### Orchestrator response - round N`, updates alignment or status, and does nothing when no Executor review is pending.
3. Before dispatching a task Executor session, create a Codex task monitor automation for the absolute `execution.md` path.
4. The task automation reads the plan, task `context.md`, and `execution.md`, responds only when `Status: awaiting-orchestrator-review` is present, appends `### Orchestrator review - round N`, updates `Status:` to `approved`, `changes-requested`, or `user-decision-needed`, and does nothing otherwise.
5. Stop or delete the Codex automation when the phase is `user-approved`, the task is `approved`, or the item is `user-decision-needed`.

Executor duties:

1. After appending a phase review to `discussion.md`, start a Claude Code `Monitor` that watches for a new `### Orchestrator response - round N` or terminal phase status.
2. If the Orchestrator response requests changes, resume the same Claude Code session to append the next Executor review round. If the phase becomes `user-approved` or `user-decision-needed`, stop and delete the monitor.
3. After setting a task to `Status: awaiting-orchestrator-review`, start a Claude Code `Monitor` that watches `execution.md` for the next Orchestrator review or status change.
4. If the Orchestrator writes `Status: changes-requested`, resume the same Claude Code session to fix only the findings for that task. If the task becomes `approved` or `user-decision-needed`, stop and delete the monitor.

Do not create separate monitor markdown files. The monitor's durable coordination surface is the phase `discussion.md` or task `execution.md`.

Use `<work-folder>/terminal/monitors/` only for fallback shell monitor artifacts when Claude Code `Monitor` is unavailable:

```text
fallback-monitor-<phase-or-task>.sh
fallback-monitor-<phase-or-task>.log
```

The monitor contract is required for real resonance runs. Skip it only for an explicitly local dry run, unavailable automation tools, unavailable Claude Code `Monitor` support, or a user-approved headless smoke test; record the skip or fallback reason in `<work-folder>/terminal/sessions.md`.

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

- Prefer one fresh Executor session per ready task.
- Prefer one isolated git worktree per active Executor session.
- Use a shared checkout only when active tasks have explicitly disjoint write locks and the repo tooling will not mutate shared files.
- Never dispatch two tasks with overlapping files, directories, generated artifacts, lockfiles, migration history, or shared package boundaries.
- Summarize dependency outputs in dependent task contexts instead of asking Executors to read earlier execution logs.

## Codex App Terminal Dispatch

Use the Codex Mac app terminal as the terminal runtime. Start visible Claude Code CLI Executor sessions from Codex app terminal sessions; do not use external terminal windows, tabs, or launch configurations for normal resonance runs.

Session protocol:

1. Create `<work-folder>/terminal/sessions.md` before the brainstorm Executor review.
2. Start one Codex app terminal session per phase review or task execution.
3. Record the returned terminal session handle when available, the repo/worktree path, the phase or task, the command shape, and the status source in `sessions.md`.
4. Use Codex app terminal output for live observation, but treat `discussion.md` and `execution.md` as the durable coordination records.
5. When a Claude Code `Monitor` wakes and more Executor work is required, resume the same terminal session if available; otherwise start a visible continuation session and record it.

Every dispatch command must:

1. Set the working directory to the repo root or assigned worktree.
2. Set the terminal title to `resonance:<short-uuid>:<phase-or-task>` when the terminal honors OSC title escapes.
3. Start a visible Claude Code CLI session with the matching `/resonance executor ...` prompt.
4. Pass the prompt directly to `claude "<query>"`.
5. Allow the Claude Code `Monitor` tool for async phase/task handoffs.
6. Avoid persistent prompt files. If a transient runner script or headless log is needed, keep it under `<work-folder>/terminal/`, delete it on exit, and record it in `sessions.md`.

Do not create `.done` sentinel files for visible Codex app terminal sessions. The terminal session is user-visible, and `discussion.md` or `execution.md` is the durable status record.

Use `claude "<query>"` as the default Codex app terminal invocation so the user can watch the Executor session. Use `claude -p` only for explicit headless smoke tests, CI-like checks, or when the user asks for non-interactive execution.

Codex app terminal command shape:

```bash
#!/usr/bin/env bash
set -euo pipefail

cd "<absolute-repo-or-worktree-path>"
printf '\033]0;%s\007' "resonance:<short-uuid>:<phase-or-task>"
mkdir -p "<work-folder>/terminal"

# Use `IFS= read -r -d '' … <<'EOF'` instead of `$(cat <<'EOF' … EOF)`.
# macOS ships bash 3.2, which has a parser bug where literal apostrophes
# inside a quoted heredoc nested in $(...) abort the script with
# "unexpected EOF while looking for matching `''". `read -d ''` avoids the
# wrapper. The trailing `|| true` is needed because `read -d ''` exits 1
# at real EOF and we run under `set -euo pipefail`.
IFS= read -r -d '' query <<'EOF' || true
/resonance executor <uuid> <phase-or-task>

<phase-or-task prompt with absolute context paths>
EOF

claude \
  --permission-mode acceptEdits \
  --allowedTools Read,Edit,Bash,Monitor \
  --append-system-prompt "You are Claude Code CLI running as the resonance Executor. Follow Executor mode exactly." \
  "$query"
```

Do not regress this to `query="$(cat <<'EOF' … EOF)"`. Any prompt body containing an apostrophe (e.g. `Claude Code's Monitor tool`) will fail under macOS's default bash 3.2.

If the app terminal launch path needs a runner script instead of an inline shell command, make the runner transient and self-deleting:

```bash
#!/usr/bin/env bash
set -euo pipefail

# Self-delete the runner on exit. The script holds the Executor prompt
# and absolute paths; we do not want it lingering in the user's repo
# working tree or getting committed by accident. The durable record is
# `discussion.md` / `execution.md` / `terminal/sessions.md`, not this file.
trap 'rm -f -- "<absolute-runner-script-path>"' EXIT

cd "<absolute-repo-or-worktree-path>"
printf '\033]0;%s\007' "resonance:<short-uuid>:<phase-or-task>"
mkdir -p "<work-folder>/terminal"

# Same heredoc rules as the visible command above.
IFS= read -r -d '' query <<'EOF' || true
/resonance executor <uuid> <phase-or-task>

<phase-or-task prompt with absolute context paths>
EOF

claude \
  --permission-mode acceptEdits \
  --allowedTools Read,Edit,Bash,Monitor \
  --append-system-prompt "You are Claude Code CLI running as the resonance Executor. Follow Executor mode exactly." \
  "$query"
```

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
/resonance executor <uuid> <phase-or-task>

<phase-or-task prompt with absolute context paths>
EOF

claude -p \
  --permission-mode acceptEdits \
  --allowedTools Read,Edit,Bash,Monitor \
  --append-system-prompt "You are Claude Code CLI running as the resonance Executor. Follow Executor mode exactly." \
  "$query" 2>&1 | tee "<absolute-log-path>"
```

## Reference

Read `references/protocol.md` when you need exact artifact schemas, status values, UUID lookup rules, automation prompts, phase discussion templates, task execution templates, or final dispatch/review prompt shapes.
