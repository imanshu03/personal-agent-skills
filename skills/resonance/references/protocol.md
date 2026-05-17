# Resonance Protocol Reference

Use this reference for exact artifact shapes, status values, and coordination prompts. Keep `SKILL.md` as the operational overview; load this file when creating or reviewing resonance artifacts.

## Table Of Contents

- Storage model
- UUID lookup
- Core artifacts
- Codex app terminal dispatch contract
- Async monitor contract
- Phase alignment
- Task status state machine
- Artifact templates
- Automation behavior
- Dispatch prompts
- Endgame

## Storage Model

Ask the user for the base folder before creating resonance work documents unless a base folder is already established. Suggested options:

- `.resonance`
- `docs/resonance`

Each change gets a folder named `<change-slug>-<uuid>` inside the base folder.

```text
<base-folder>/
  index.md
  <change-slug>-<uuid>/
    brainstorm/
      context.md
      discussion.md
    plan/
      context.md
      discussion.md
    task-1/
      context.md
      execution.md
    task-2/
      context.md
      execution.md
```

The work folder is the source of truth. The base index is only a lookup convenience.

## UUID Lookup

When invoked as `/resonance executor <uuid>`, locate the work folder before acting:

1. Search the repo's documented resonance base folder.
2. Search `.resonance` and `docs/resonance`.
3. Read discovered `<base-folder>/index.md` files and look for the UUID.
4. Search for a direct child folder ending with `-<uuid>`.
5. Search for `*/*-<uuid>/plan/context.md`, excluding dependency and build output folders.
6. If exactly one folder matches, use it.
7. If multiple folders match, ask the user which one to use.
8. If no folder matches, ask for the base folder or full work folder path.

Do not create a new work folder for an unknown UUID.

## Core Artifacts

Create these durable markdown files before implementation starts:

- `<base-folder>/index.md`: UUID, change name, work folder path, current state, active tasks.
- `<work-folder>/brainstorm/context.md`: approved design direction.
- `<work-folder>/brainstorm/discussion.md`: mutable brainstorm review log.
- `<work-folder>/plan/context.md`: approved implementation plan, task graph, write locks, final verification.
- `<work-folder>/plan/discussion.md`: mutable plan review log.
- `<work-folder>/task-N/context.md`: stable task-level instructions and review checklist.
- `<work-folder>/task-N/execution.md`: live task coordination, status, completion notes, review rounds.
- `<work-folder>/terminal/sessions.md`: Codex app terminal dispatch record, including session handles when available, fallback behavior, runner scripts, and visible session status.
- `<work-folder>/terminal/run-<phase-or-task>-executor.sh`: optional transient runner script for one Claude Code Executor session. The runner self-deletes on exit; treat it as ephemeral and do not commit it.
- `<work-folder>/terminal/monitors/fallback-monitor-<phase-or-task>.sh`: optional fallback only when the Claude Code `Monitor` tool is unavailable, disabled, or not allowed.
- `<work-folder>/terminal/monitors/fallback-monitor-<phase-or-task>.log`: fallback monitor output when a fallback script is required.
- `<work-folder>/terminal/logs/<phase-or-task>.log`: transient captured Executor output for explicit headless runs. Self-deletes on exit alongside the runner; tail it live during the run, do not commit it.

Do not create monitor-specific markdown artifacts. `discussion.md` and `execution.md` are the durable async transcript and state files for both Codex automation and Claude Code `Monitor`.
Do not create `.done` sentinel files for visible Codex app terminal sessions. The terminal session is user-visible, and `discussion.md` or `execution.md` is the durable status record.

## Codex App Terminal Dispatch Contract

Use the Codex Mac app terminal as the terminal runtime. Start one visible Claude Code Executor session per phase or task in the Codex app terminal, and record the app terminal session handle when one is available. Do not use external terminal windows, tabs, or launch configurations for normal resonance runs.

### Session Record

Before dispatching the brainstorm review, create `<work-folder>/terminal/sessions.md`:

```markdown
# Codex App Terminal Sessions

**Date:** YYYY-MM-DD
**UUID:** <uuid>
**Runtime:** Codex Mac app terminal
**Feature title:** resonance:<short-uuid>
**Repo/worktree:** <absolute-repo-or-worktree-path>
**Dispatch command template:** `claude "<query>"`
**Session handle source:** <Codex app terminal session id | unavailable reason>
**Fallback runner folder:** `<work-folder>/terminal`

## Dispatches

- brainstorm: session=<session-id | unavailable>, cwd=<repo-or-worktree>, command=<summary>, status source=<discussion.md>
```

If the Codex app returns a terminal session id or PTY handle, record it. If no handle is exposed, write `Session handle: unavailable` and rely on the durable markdown channel plus visible terminal output.

### Per-Session Command

For every phase review and task execution, launch a visible Codex app terminal session running `claude "<query>"` without `-p` so the user can watch the Claude Code session. Pass the query directly; do not write a separate prompt file. Use `-p` only for explicit headless smoke tests, CI-like checks, or when the user asks for non-interactive execution.

Run this command shape directly in the Codex app terminal:

```bash
set -euo pipefail

cd "<absolute-repo-or-worktree-path>"
printf '\033]0;%s\007' "resonance:<short-uuid>:<phase-or-task>"
mkdir -p "<work-folder>/terminal"

# Use `IFS= read -r -d '' ... <<'EOF'`, not `$(cat <<'EOF' ... EOF)`.
# macOS bash 3.2 has a parser bug where literal apostrophes inside a
# quoted heredoc nested in $(...) abort the script with "unexpected EOF
# while looking for matching `''". `read -d ''` reads until NUL (never
# present in the heredoc), so it always exits 1 at real EOF; the
# trailing `|| true` keeps `set -euo pipefail` from killing the script.
IFS= read -r -d '' query <<'EOF' || true
/resonance executor <uuid> <phase-or-task>

<phase-or-task prompt with absolute paths>
EOF

claude \
  --permission-mode acceptEdits \
  --allowedTools Read,Edit,Bash,Monitor \
  --append-system-prompt "You are Claude Code CLI running as the resonance Executor. Follow Executor mode exactly." \
  "$query"
```

Do not regress this template to `query="$(cat <<'EOF' ... EOF)"` - any prompt body containing an apostrophe (e.g. `Claude Code's Monitor tool`) will fail under macOS's default bash 3.2.

Use `--allowedTools Read,Write,Edit,Bash,Monitor` for task execution when the task context permits file creation. Keep phase reviews read/edit-only for discussion files, plus `Monitor` for async handoffs.

If the app terminal launch path needs a runner script instead of an inline command, keep the runner under `<work-folder>/terminal/` and treat it as transient. It contains the literal Executor prompt and absolute paths, so the script must self-delete on exit and must never be committed. The durable record is `discussion.md` / `execution.md` / `terminal/sessions.md`.

```bash
#!/usr/bin/env bash
set -euo pipefail

# Self-delete this runner on exit so the prompt and absolute paths do
# not linger in the user's repo or get committed. bash holds the script
# inode open until the process exits; the EXIT trap runs after `claude`
# returns (clean exit, non-zero exit, Ctrl-C, or `set -e` abort).
# The Orchestrator substitutes the literal absolute path here; do not
# use `$0`, which becomes relative when a user invokes the script as
# `bash run-task-N-executor.sh` from inside `terminal/`.
trap 'rm -f -- "<absolute-runner-script-path>"' EXIT

cd "<absolute-repo-or-worktree-path>"
printf '\033]0;%s\007' "resonance:<short-uuid>:<phase-or-task>"
mkdir -p "<work-folder>/terminal"

# Same heredoc rules as the visible command above.
IFS= read -r -d '' query <<'EOF' || true
/resonance executor <uuid> <phase-or-task>

<phase-or-task prompt with absolute paths>
EOF

claude \
  --permission-mode acceptEdits \
  --allowedTools Read,Edit,Bash,Monitor \
  --append-system-prompt "You are Claude Code CLI running as the resonance Executor. Follow Executor mode exactly." \
  "$query"
```

For explicit headless runs, build a complete runner that captures `tee` output to a transient log and deletes both the runner and the log on exit:

```bash
#!/usr/bin/env bash
set -euo pipefail

# Self-delete the runner AND the tee'd log on exit. The log captures
# the full Executor prompt and session output; tail it live during the
# run, but do not leave it on disk.
trap 'rm -f -- "<absolute-runner-script-path>" "<absolute-log-path>"' EXIT

cd "<absolute-repo-or-worktree-path>"
mkdir -p "<work-folder>/terminal/logs"

# Same heredoc rules as the visible runner above.
IFS= read -r -d '' query <<'EOF' || true
/resonance executor <uuid> <phase-or-task>

<phase-or-task prompt with absolute paths>
EOF

claude -p \
  --permission-mode acceptEdits \
  --allowedTools Read,Edit,Bash,Monitor \
  --append-system-prompt "You are Claude Code CLI running as the resonance Executor. Follow Executor mode exactly." \
  "$query" 2>&1 | tee "<absolute-log-path>"
```

## Async Monitor Contract

Every resonance phase or task uses paired monitors so Codex and Claude Code can coordinate through durable markdown instead of terminal scrollback. For Claude Code CLI v2.1.98 or later, use the built-in `Monitor` tool for Executor-side monitoring. The `Monitor` tool writes and runs its own background watch script and feeds output lines back into the same Claude Code session, so resonance should not create hand-written shell monitor scripts for normal runs.

`Monitor` must be present in `--allowedTools`. It follows the same permission rules as `Bash`; if it is unavailable, disabled by environment settings, or not allowed in the session, record the reason and use the fallback monitor path below.

There are two channels:

- Brainstorm and plan phases use `<work-folder>/<phase>/discussion.md`.
- Task execution uses `<work-folder>/task-N/execution.md`.

There are two monitor roles:

- The Orchestrator creates a Codex automation before dispatching a phase or task. It watches the absolute channel path and appends the next Orchestrator response or review only when Executor output is pending.
- The Executor starts a Claude Code `Monitor` after it writes its phase review or task completion. It watches the same channel path for the next Orchestrator response, review, or terminal status.

### Phase Monitor Loop

Use this loop for brainstorm and plan:

1. Orchestrator writes or updates `<phase>/context.md`.
2. Orchestrator appends `### Orchestrator draft - round N` to `<phase>/discussion.md`.
3. Orchestrator creates a Codex phase monitor automation for the absolute `discussion.md` path.
4. Orchestrator dispatches a visible Codex app terminal session running `claude "<query>"` with `/resonance executor <uuid> <phase>`.
5. Executor appends `### Executor review - round N` and starts a Claude Code `Monitor` for the same `discussion.md` file.
6. The Codex automation notices the pending Executor review, updates `<phase>/context.md` if needed, and appends `### Orchestrator response - round N`.
7. The Executor monitor notices the new Orchestrator response. If alignment is still pending, it resumes the same Claude Code session or launches a visible Codex app terminal continuation to append the next Executor review.
8. Both monitors stop when the phase status is `user-approved` or `user-decision-needed`.

The Codex phase automation must no-op if no new `### Executor review - round N` is waiting. The Executor phase monitor must no-op if it has already handled the latest `### Orchestrator response - round N`.

### Task Monitor Loop

Use this loop for every task:

1. Orchestrator creates `task-N/context.md` and `task-N/execution.md`.
2. Before dispatch, Orchestrator creates a Codex task monitor automation for the absolute `task-N/execution.md` path.
3. Orchestrator dispatches a visible Codex app terminal session running `claude "<query>"` with `/resonance executor <uuid> task-N`.
4. Executor implements only that task, records completion notes, and sets `Status: awaiting-orchestrator-review`.
5. Executor starts a Claude Code `Monitor` for the same `execution.md` file.
6. The Codex automation notices `Status: awaiting-orchestrator-review`, reviews the task, appends `### Orchestrator review - round N`, and sets `Status: approved`, `Status: changes-requested`, or `Status: user-decision-needed`.
7. The Executor monitor notices the Orchestrator review. If status is `changes-requested`, it resumes the same Claude Code session or launches a visible Codex app terminal continuation to fix only the findings for that task.
8. Both monitors stop when the task status is `approved` or `user-decision-needed`.

The Codex task automation must no-op unless the current task status is `awaiting-orchestrator-review`. The Executor task monitor must no-op if it has already handled the latest `### Orchestrator review - round N` or terminal status.

### Executor Monitor Setup

Use Claude Code's `Monitor` tool by default. Ask Claude Code to watch the absolute target file and emit a wake-up only when a relevant Orchestrator marker or terminal status appears:

- Phase target: `<work-folder>/<phase>/discussion.md`
- Phase wake-up: new `### Orchestrator response - round N`
- Phase terminal statuses: `user-approved`, `user-decision-needed`
- Task target: `<work-folder>/task-N/execution.md`
- Task wake-up: new `### Orchestrator review - round N` or `Status: changes-requested`
- Task terminal statuses: `Status: approved`, `Status: user-decision-needed`

Do not create `monitor-*.md` files. When the monitor wakes, the Executor contributes directly to the watched `discussion.md` or `execution.md` file. That file is the record.

Fallback shell scripts are allowed only when Claude Code `Monitor` is unavailable, disabled, or not allowed. If fallback is required, create `fallback-monitor-<phase-or-task>.sh` and `fallback-monitor-<phase-or-task>.log`, and record the fallback reason in `<work-folder>/terminal/sessions.md`. Do not make fallback scripts the default path.

### Codex Automation Prompts

Use absolute paths in Codex automations.

Phase automation prompt:

```text
Watch <work-folder>/<phase>/discussion.md for a pending Executor review. Read <work-folder>/<phase>/context.md and the discussion file. If no new Executor review is pending, do nothing. If review is pending, update context.md if needed, append ### Orchestrator response - round N, and set Alignment: pending or Alignment: aligned. Stop/delete this automation when the phase is user-approved or user-decision-needed.
```

Task automation prompt:

```text
Watch <work-folder>/task-N/execution.md for Status: awaiting-orchestrator-review. Read <work-folder>/plan/context.md, <work-folder>/task-N/context.md, and the execution file. If the task is not awaiting Orchestrator review, do nothing. If review is pending, inspect only files and commands allowed by task context, append ### Orchestrator review - round N, and set Status to approved, changes-requested, or user-decision-needed. Stop/delete this automation when the task is approved or user-decision-needed.
```

## Phase Alignment

Brainstorm and plan phases use the same loop:

1. Orchestrator writes or updates phase `context.md`.
2. Orchestrator appends `### Orchestrator draft - round N` to `discussion.md`.
3. Orchestrator creates a Codex phase monitor automation for the absolute phase `discussion.md` path.
4. Orchestrator dispatches `/resonance executor <uuid> <phase>`.
5. Executor reviews the phase context, appends `### Executor review - round N`, and starts a Claude Code `Monitor` for the same `discussion.md` file.
6. Codex automation responds in `### Orchestrator response - round N`.
7. Executor monitor resumes the Executor if another review round is needed.
8. Repeat until both agents write `Alignment: aligned`.
9. Ask the user to approve the aligned phase context.
10. Delete monitors/automations after user approval or `user-decision-needed`.

After more than six review/response turns without alignment, stop and ask the user to decide.

## Task Status State Machine

Use these exact task statuses:

```text
blocked
not-started
in-progress
awaiting-orchestrator-review
changes-requested
approved
user-decision-needed
```

Recommended happy path:

```text
blocked -> not-started -> in-progress -> awaiting-orchestrator-review -> approved
```

When changes are needed:

```text
awaiting-orchestrator-review -> changes-requested -> in-progress -> awaiting-orchestrator-review -> approved
```

When agents cannot converge:

```text
awaiting-orchestrator-review -> changes-requested -> awaiting-orchestrator-review -> user-decision-needed
```

Use `Status: not-started` for tasks without dependencies. Use `Status: blocked` for tasks waiting on dependencies.

## Brainstorm Context Template

```markdown
# <Change Name> Brainstorm Context

**Date:** YYYY-MM-DD
**UUID:** <uuid>
**Skill:** resonance
**Invocation namespace:** resonance
**Role model:** Orchestrator/Executor
**Base folder:** <base-folder>
**Work folder:** <work-folder>
**Phase status:** draft | in-review | aligned | user-approved

## User Request

<Original request and clarifying constraints.>

## Project Context

<Relevant repo docs, files, existing behavior, product constraints, and design constraints.>

## Explored Approaches

1. <Approach and trade-offs.>
2. <Approach and trade-offs.>
3. <Approach and trade-offs.>

## Approved Direction

<Design or architecture direction both agents aligned on.>

## Decisions

- <Decision and reason.>

## Out Of Scope

- <Explicitly excluded work.>

## Acceptance Criteria

- <Observable behavior or artifact.>

## Open Questions

- None | <Question requiring user decision.>
```

## Brainstorm Discussion Template

```markdown
# <Change Name> Brainstorm Discussion

**Date:** YYYY-MM-DD
**UUID:** <uuid>
**Context:** context.md
**Phase:** brainstorm
**Status:** draft | in-review | aligned | user-approved | user-decision-needed
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
- Alignment: pending | aligned

## User approval

- Status: pending | approved
- Notes:
```

## Plan Context Template

```markdown
# <Change Name> Plan Context

**Date:** YYYY-MM-DD
**UUID:** <uuid>
**Skill:** resonance
**Invocation namespace:** resonance
**Role model:** Orchestrator/Executor
**Base folder:** <base-folder>
**Work folder:** <work-folder>
**Brainstorm context:** ../brainstorm/context.md
**Brainstorm discussion:** ../brainstorm/discussion.md
**Phase status:** draft | in-review | aligned | user-approved

## Approved Design

<Concise summary from brainstorm/context.md.>

## Architecture

<Implementation approach and key boundaries.>

## Tasks

1. [Task 1 - Name](../task-1/context.md)
2. [Task 2 - Name](../task-2/context.md)

## Task Dependency Graph

- Task 1: no dependencies
- Task 2: depends on Task 1

## Parallel Execution Plan

- Wave 1: Task 1 can run immediately.
- Wave 2: Task 2 can start after Task 1 is approved.
- Use one Executor session per active task.
- Prefer one isolated worktree per active Executor session.

## Final Verification

<Commands and checks to run after every task is approved.>
```

## Plan Discussion Template

```markdown
# <Change Name> Plan Discussion

**Date:** YYYY-MM-DD
**UUID:** <uuid>
**Context:** context.md
**Brainstorm context:** ../brainstorm/context.md
**Phase:** plan
**Status:** draft | in-review | aligned | user-approved | user-decision-needed
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
- Alignment: pending | aligned

## User approval

- Status: pending | approved
- Notes:
```

## Task Context Template

```markdown
# Task N - <Task Name>

**Date:** YYYY-MM-DD
**UUID:** <uuid>
**Plan:** ../plan/context.md
**Execution:** execution.md
**Depends on:** none | task-1 | task-1, task-2
**Parallel group:** wave-1 | wave-2 | sequential
**Write locks:** `<path-or-directory>`, `<path-or-directory>`
**Recommended session:** fresh Executor session
**Recommended workspace:** isolated worktree preferred | shared checkout allowed

## Goal

<One or two sentences describing the task outcome.>

## Scope

<Exact boundaries for this task.>

## Dependency Inputs

<Approved prior task outputs this task relies on, summarized here. Use "None" for independent tasks.>

## Parallel Safety

- Can run in parallel with: `<task-N>`, `<task-N>`
- Must not run in parallel with: `<task-N>` because `<write-lock-or-domain-conflict>`
- Shared files or generated artifacts: `<paths-or-none>`

## Files

- Create: `<path>`
- Modify: `<path>`
- Test: `<path>`

## Steps

- [ ] Step 1 with exact action.
- [ ] Step 2 with exact action.

## Verification

- Run: `<command>`
- Expected: `<expected outcome>`

## Orchestrator Review Checklist

- Verify these exact requirements.
- Inspect these exact files.
- Run only these exact commands.

## Out Of Scope

- <Work that must not be done in this task.>
```

## Task Execution Template

```markdown
# Task N - <Task Name> Execution

**Date:** YYYY-MM-DD
**UUID:** <uuid>
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

Status: blocked
```

## Automation Behavior

Create a Codex monitor automation for each active phase or task before dispatch when automation tools are available. Use absolute file paths. The Executor must also create the matching local monitor after it writes its review or completion.

Recommended intervals:

- Brainstorm phase review: every 2 minutes.
- Plan phase review: every 2 minutes.
- Task review: every 4 minutes.

Automation names:

- `resonance-<short-uuid>-brainstorm-monitor`
- `resonance-<short-uuid>-plan-monitor`
- `resonance-<short-uuid>-task-1-monitor`

Automation behavior:

1. Read the target `discussion.md` or `execution.md` file.
2. For phases, respond only when a new `### Executor review - round N` is pending.
3. For tasks, respond only when `Status: awaiting-orchestrator-review` is present.
4. Read only the needed context files.
5. Append the Orchestrator response or review.
6. Update only the alignment/status fields owned by that phase or task.
7. Do nothing if there is no pending Executor output.
8. Stop or delete itself when the phase is `user-approved`, the task is `approved`, or the item is `user-decision-needed`.

Executor monitor behavior:

1. For phases, start Claude Code `Monitor` on `discussion.md` after appending `### Executor review - round N`.
2. For tasks, start Claude Code `Monitor` on `execution.md` after setting `Status: awaiting-orchestrator-review`.
3. Resume the same Claude Code session, or launch a visible Codex app terminal continuation, only when a new Orchestrator response or review requires more Executor work.
4. Do nothing if the latest Orchestrator marker was already handled.
5. Stop the `Monitor` when the phase is `user-approved`, the task is `approved`, or the item is `user-decision-needed`.
6. Use a fallback shell monitor only when the `Monitor` tool is unavailable, disabled, or not allowed; record the fallback reason.

## Executor Phase Review Prompt

```text
Run /resonance executor <uuid> <phase>. You are reviewing a resonance phase, not implementing product code.

Phase:
brainstorm | plan

Context:
<work-folder>/<phase>/context.md

Discussion:
<work-folder>/<phase>/discussion.md

Review the phase context for missing context, unstated assumptions, bias, contradictions, feasibility risks, and unclear acceptance criteria. Append Executor review - round N to discussion.md. If the phase is acceptable, write Alignment: aligned. If changes are needed, write clear findings and leave Alignment: pending. Do not edit product code. Start Claude Code's Monitor tool for the absolute discussion.md path so this same session wakes only on a new Orchestrator response or terminal status, then resumes this Executor flow if another review is needed. Do not create a separate monitor markdown file; discussion.md is the record. Use fallback-monitor-<phase>.sh only if Monitor is unavailable, disabled, or not allowed, and record the reason in <work-folder>/terminal/sessions.md. Keep the monitor running until the phase is user-approved or user-decision-needed, then stop it. If there have been more than six review/response turns without alignment, mark Status: user-decision-needed and ask the Orchestrator to escalate to the user.
```

## Executor Task Prompt

```text
Run /resonance executor <uuid>. You are implementing one task from resonance.

Plan:
<work-folder>/plan/context.md

Task context:
<work-folder>/task-N/context.md

Task execution:
<work-folder>/task-N/execution.md

If a task was not assigned explicitly, locate <work-folder> by UUID and claim the first ready task whose dependencies are approved and whose write locks do not conflict with an in-progress task. Implement only that task in this Executor session. Follow the task context exactly. Do not implement future tasks. Do not read sibling task folders unless the claimed task's context.md explicitly names them as dependencies. Record this session and workspace/worktree in execution.md, then set Status to in-progress. When complete, update execution.md with summary, files touched, commands run, deviations, and open questions. Set Status to awaiting-orchestrator-review. Start Claude Code's Monitor tool for the absolute execution.md path so this same session wakes only on a new Orchestrator review or terminal status. If Status is changes-requested, resume this Executor flow and fix only the Orchestrator findings for this task. Do not create a separate monitor markdown file; execution.md is the record. Use fallback-monitor-task-N.sh only if Monitor is unavailable, disabled, or not allowed, and record the reason in <work-folder>/terminal/sessions.md. Keep the monitor running until the task is approved or user-decision-needed, then stop it.
```

## Orchestrator Review Prompt

```text
Review Task N from resonance.

Plan:
<work-folder>/plan/context.md

Task context:
<work-folder>/task-N/context.md

Task execution:
<work-folder>/task-N/execution.md

Follow the Orchestrator Review Process in execution.md and the Orchestrator Review Checklist in context.md. Review only Task N. Confirm the actual diff stays inside Task N's declared write locks. Append a new Orchestrator review round directly above Task N's Status line in execution.md and update only Task N's Status to approved, changes-requested, or user-decision-needed.
```

## Parallel Dispatch Prompt

```text
Dispatch the next ready parallel wave for resonance.

Plan:
<work-folder>/plan/context.md

Task folders:
<work-folder>/task-*/

Read the plan, each task context.md, each task execution.md, and <work-folder>/terminal/sessions.md. Mark blocked tasks as not-started only when their dependencies are approved. Select ready tasks whose write locks do not overlap. For each selected task, create a Codex task monitor automation for the absolute task execution.md path at a 4-minute interval before launch. Dispatch one visible Codex app terminal session per selected task, using a transient runner under <work-folder>/terminal/ only when the terminal launch path cannot pass the prompt inline. The prompt must allow the Claude Code Monitor tool and require the Executor to start Monitor for task-N after it sets Status: awaiting-orchestrator-review. The Executor must write all responses to execution.md, not a separate monitor markdown file. Record each terminal session handle, continuation, runner fallback, and status source in sessions.md. Rename the terminal session to resonance:<short-uuid>:task-N when the terminal honors OSC title escapes, and run Claude Code CLI with /resonance executor <uuid> task-N. Do not dispatch tasks with overlapping write locks in the same wave. Summarize dispatched tasks, skipped tasks, and why each skipped task was not ready.
```

## Endgame

After all tasks are approved:

1. Run final verification from `<work-folder>/plan/context.md`.
2. Commit the implementation when the user requested commit ownership or the workflow requires it.
3. Push the branch when requested or expected by the repo workflow.
4. Open a PR to the target branch when requested or expected by the repo workflow.
5. Address PR review comments as focused follow-up commits.
6. Keep unrelated dirty files out of review-fix commits.
