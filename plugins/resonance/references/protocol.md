# Resonance Protocol Reference

Use this reference for exact artifact shapes, status values, and coordination prompts. Keep `workflow.md` as the operational overview; load this file when creating or reviewing resonance artifacts.

## Table Of Contents

- Storage model
- UUID lookup
- Core artifacts
- Executor startup contract
- Control baton monitor contract
- Phase alignment
- Task status state machine
- Artifact templates
- Automation behavior
- Control prompts
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
    control.md
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

When invoked as `/resonance:executor <uuid>`, locate the work folder before acting:

1. Search the repo's documented resonance base folder.
2. Search `.resonance` and `docs/resonance`.
3. Read discovered `<base-folder>/index.md` files and look for the UUID.
4. Search for a direct child folder ending with `-<uuid>`.
5. Search for `*/*-<uuid>/control.md` and `*/*-<uuid>/plan/context.md`, excluding dependency and build output folders.
6. If exactly one folder matches, use it.
7. If multiple folders match, ask the user which one to use.
8. If no folder matches, ask for the base folder or full work folder path.

Do not create a new work folder for an unknown UUID.

## Core Artifacts

Create these durable markdown files before implementation starts:

- `<base-folder>/index.md`: UUID, change name, work folder path, current state, active tasks.
- `<work-folder>/control.md`: root baton file for control transfer only. It stores owner, status, phase, target file, next action, monitor registration, and a short event log. It must not store feature context or detailed review content.
- `<work-folder>/brainstorm/context.md`: approved design direction.
- `<work-folder>/brainstorm/discussion.md`: mutable brainstorm review log.
- `<work-folder>/plan/context.md`: approved implementation plan, task graph, write locks, final verification.
- `<work-folder>/plan/discussion.md`: mutable plan review log.
- `<work-folder>/task-N/context.md`: stable task-level instructions and review checklist.
- `<work-folder>/task-N/execution.md`: live task coordination, status, completion notes, review rounds.
- `<work-folder>/terminal/run-executor.sh`: optional transient runner script for one long-lived Executor session. The runner self-deletes on exit; treat it as ephemeral and do not commit it.
- `plugins/resonance/scripts/fallback_monitor_control.sh`: plugin-owned fallback watcher script. Agents must run this script instead of creating an ad hoc shell monitor.
- `<work-folder>/terminal/monitors/fallback-monitor-control.log`: fallback watcher output when the plugin-owned fallback script is required.
- `<work-folder>/terminal/monitors/fallback-monitor-control.pid`: optional pid file written by the plugin-owned fallback script.
- `<work-folder>/terminal/logs/executor.log`: transient captured Executor output for explicit headless runs. Self-deletes on exit alongside the runner; tail it live during the run, do not commit it.

Do not create monitor-specific markdown artifacts. `control.md` is the durable async baton file; `discussion.md` and `execution.md` are the durable content records.
Do not create `.done` sentinel files for Executor sessions. `control.md`, `discussion.md`, and `execution.md` are the durable status records.

## Executor Startup Contract

The Orchestrator does not spawn phase or task Executor sessions by default. After creating the work folder and `control.md`, the Orchestrator must show the user this command before substantive feature work:

```text
Run this in the agent/session that will act as Executor:

/resonance:executor <uuid>
```

The user starts one long-lived Executor session in whichever supported agent should perform the Executor role. That Executor locates the work folder by UUID, registers itself in `control.md`, sets `Owner: orchestrator`, `Status: awaiting-orchestrator`, and `Next action: executor-ready`, starts the current agent's native monitor/watch on the absolute `control.md` path when available, and waits for `Owner: executor`.

### Control Record

Create `<work-folder>/control.md` during bootstrap:

```markdown
# Resonance Control

**Date:** YYYY-MM-DD
**UUID:** <uuid>
**Work folder:** <absolute-work-folder>
**Control purpose:** baton only; no feature context or review substance

## Baton

Owner: orchestrator
Status: executor-start-needed
Phase: bootstrap
Target: control.md
Next action: start-executor
Round: 0
Updated by: orchestrator
Updated at: YYYY-MM-DDTHH:MM:SSZ

## Executor

Session: unregistered
Watch: unregistered
Workspace/worktree: unset

## Event Log

- YYYY-MM-DDTHH:MM:SSZ orchestrator: bootstrap created; waiting for Executor to start `/resonance:executor <uuid>`.
```

Allowed `Owner:` values: `orchestrator`, `executor`, `user`, `none`.
Allowed `Status:` values: `bootstrapping`, `executor-start-needed`, `orchestrator-working`, `awaiting-executor`, `executor-working`, `awaiting-orchestrator`, `awaiting-user`, `complete`, `user-decision-needed`.
Allowed `Next action:` values include `start-executor`, `executor-ready`, `review-brainstorm`, `review-plan`, `execute-task`, `fix-task`, `review-task`, `approve-phase`, `final-verify`, `none`.

For explicit Claude Code headless runs, build a complete runner that captures `tee` output to a transient log and deletes both the runner and the log on exit. For other agents, adapt the runner to that agent's CLI while preserving the `/resonance:executor <uuid>` query and transient logging rules:

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
/resonance:executor <uuid>
EOF

claude -p \
  --permission-mode acceptEdits \
  --allowedTools Read,Edit,Bash,Monitor \
  --append-system-prompt "You are Claude Code CLI running as the resonance Executor. Follow Executor mode exactly." \
  "$query" 2>&1 | tee "<absolute-log-path>"
```

## Control Baton Monitor Contract

Every resonance phase or task is assigned through `<work-folder>/control.md`, so the Orchestrator and Executor coordinate through durable markdown instead of terminal scrollback. Use each role session's native monitor, automation, reminder, or follow-up mechanism for `control.md` when available. Examples include Claude Code's built-in `Monitor` tool and Codex app automations. Resonance should not create hand-written shell monitor scripts for normal runs when a native monitor is available.

If using Claude Code `Monitor`, it must be present in `--allowedTools` and follows the same permission rules as `Bash`. If the current agent has no native monitor, the native monitor is disabled by environment settings, or it is not allowed in the session, record the reason and use the fallback monitor path below.

There is one baton channel:

- Control transfer uses `<work-folder>/control.md`.

There are two monitor roles:

- The Orchestrator creates one native monitor/automation after bootstrap when available. It watches the absolute `control.md` path and acts only when the baton says `Owner: orchestrator` and `Status: awaiting-orchestrator`.
- The Executor sets `Next action: executor-ready` after registering itself, then starts one native monitor/watch when available. It watches the same `control.md` path and acts only when the baton says `Owner: executor` and `Status: awaiting-executor`.

Agent-specific monitor mapping:

- If the role session is Codex, use Codex app automations for the `control.md` watcher.
- If the role session is Claude Code, use Claude Code's `Monitor` tool for the `control.md` watcher.
- If the role session is another supported agent, use that agent's native automation, monitor, reminder, or follow-up mechanism.
- Use the plugin-owned fallback shell monitor only when the current role session has no usable native watch mechanism; record the fallback reason in `control.md`.

### Phase Monitor Loop

Use this loop for brainstorm and plan:

1. Orchestrator writes or updates `<phase>/context.md`.
2. Orchestrator appends `### Orchestrator draft - round N` to `<phase>/discussion.md`.
3. Orchestrator updates `control.md`: `Owner: executor`, `Status: awaiting-executor`, `Phase: <phase>`, `Target: <phase>/discussion.md`, `Next action: review-<phase>`.
4. Executor monitor notices the baton, reads `<phase>/context.md` and `<phase>/discussion.md`, and appends `### Executor review - round N` to the discussion.
5. Executor updates `control.md`: `Owner: orchestrator`, `Status: awaiting-orchestrator`, `Phase: <phase>`, `Target: <phase>/discussion.md`, `Next action: review-<phase>-response`.
6. The Orchestrator monitor/automation notices the baton, reads the phase context and discussion, updates `<phase>/context.md` if needed, and appends `### Orchestrator response - round N`.
7. If alignment is pending, Orchestrator hands the baton back to Executor through `control.md`. If aligned, Orchestrator sets `Owner: user`, `Status: awaiting-user`, and asks the user to approve the phase.
8. Both monitors keep watching `control.md` until the run is complete or `user-decision-needed`.

The Orchestrator monitor/automation must no-op unless `control.md` assigns ownership to the Orchestrator. The Executor monitor must no-op unless `control.md` assigns ownership to the Executor.

### Task Monitor Loop

Use this loop for every task:

1. Orchestrator creates `task-N/context.md` and `task-N/execution.md`.
2. Orchestrator updates `control.md`: `Owner: executor`, `Status: awaiting-executor`, `Phase: task-N`, `Target: task-N/execution.md`, `Next action: execute-task`.
3. Executor monitor notices the baton, implements only that task, records completion notes in `task-N/execution.md`, and sets the task status to `awaiting-orchestrator-review`.
4. Executor updates `control.md`: `Owner: orchestrator`, `Status: awaiting-orchestrator`, `Phase: task-N`, `Target: task-N/execution.md`, `Next action: review-task`.
5. The Orchestrator monitor/automation notices the baton, reviews the task, appends `### Orchestrator review - round N`, and sets task `Status:` to `approved`, `changes-requested`, or `user-decision-needed`.
6. If changes are requested, Orchestrator hands the baton back through `control.md` with `Next action: fix-task`; otherwise it assigns the next ready task or moves toward final verification.

The Orchestrator monitor/automation must no-op unless `control.md` assigns ownership to the Orchestrator. The Executor monitor must no-op unless `control.md` assigns ownership to the Executor.

### Executor Monitor Setup

Use the current Executor agent's native monitor/watch by default. Ask it to watch the absolute `control.md` path and emit a wake-up only when the baton assigns work to the Executor:

- Target: `<work-folder>/control.md`
- Wake-up: `Owner: executor` with `Status: awaiting-executor`
- Terminal statuses: `Status: complete`, `Status: user-decision-needed`

Do not create `monitor-*.md` files. When the monitor wakes, the Executor reads `Target:` from `control.md` and contributes directly to that target `discussion.md` or `execution.md` file. `control.md` is only the baton.

Fallback shell monitoring is allowed only when the current agent's native monitor/watch is unavailable, disabled, or not allowed. If fallback is required, run the plugin-owned `scripts/fallback_monitor_control.sh`; do not create a custom monitor script. Write its log and optional pid file under `<work-folder>/terminal/monitors/`, and record the fallback reason in `<work-folder>/control.md`. Do not make fallback shell monitoring the default path.

Example fallback invocation for an Executor watcher:

```bash
nohup bash /path/to/plugins/resonance/scripts/fallback_monitor_control.sh \
  --control "<absolute-work-folder>/control.md" \
  --owner executor \
  --status awaiting-executor \
  --interval 5 \
  --log "<absolute-work-folder>/terminal/monitors/fallback-monitor-control.log" \
  --pid-file "<absolute-work-folder>/terminal/monitors/fallback-monitor-control.pid" \
  >/dev/null 2>&1 &
```

Example fallback invocation for an Orchestrator watcher:

```bash
nohup bash /path/to/plugins/resonance/scripts/fallback_monitor_control.sh \
  --control "<absolute-work-folder>/control.md" \
  --owner orchestrator \
  --status awaiting-orchestrator \
  --interval 5 \
  --log "<absolute-work-folder>/terminal/monitors/fallback-monitor-control.log" \
  --pid-file "<absolute-work-folder>/terminal/monitors/fallback-monitor-control.pid" \
  >/dev/null 2>&1 &
```

### Orchestrator Automation Prompts

Use absolute paths in Orchestrator-side monitors, automations, reminders, or follow-ups.

Global control automation prompt:

```text
Watch <work-folder>/control.md for Owner: orchestrator and Status: awaiting-orchestrator. If the baton is not assigned to the Orchestrator, do nothing. If it is assigned, read only the target file named by Target plus the necessary context file for the current Phase. For brainstorm or plan, append the next Orchestrator response to the phase discussion and update the phase context if needed. For task-N, review only that task, append the next Orchestrator review to task-N/execution.md, and update only that task Status. Then update control.md with the next owner, status, phase, target, next action, updated-by, updated-at, and a concise event log entry. Stop/delete this automation when Status is complete or user-decision-needed.
```

## Phase Alignment

Brainstorm and plan phases use the same loop:

When creating the brainstorm context or plan context, use Superpowers if it is available in the current Orchestrator agent: use the Superpowers brainstorming command/workflow for brainstorm and the Superpowers writing-plans command/workflow for planning. If Superpowers is not available, use the current agent's best available brainstorming/planning command, skill, plugin, or a structured manual pass.

1. Orchestrator writes or updates phase `context.md`.
2. Orchestrator appends `### Orchestrator draft - round N` to `discussion.md`.
3. Orchestrator updates `control.md` to hand the baton to the Executor for the phase review.
4. Executor reviews the phase context and appends `### Executor review - round N` to `discussion.md`.
5. Executor updates `control.md` to return the baton to the Orchestrator.
6. The Orchestrator monitor/automation responds in `### Orchestrator response - round N`.
7. Orchestrator updates `control.md` again if another Executor review round is needed.
8. Repeat until both agents write `Alignment: aligned`.
9. Ask the user to approve the aligned phase context.
10. Keep the global watchers alive for the next phase unless the run is complete or `user-decision-needed`.

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

## Control Template

```markdown
# Resonance Control

**Date:** YYYY-MM-DD
**UUID:** <uuid>
**Work folder:** <absolute-work-folder>
**Control purpose:** baton only; no feature context or review substance

## Baton

Owner: orchestrator
Status: executor-start-needed
Phase: bootstrap
Target: control.md
Next action: start-executor
Round: 0
Updated by: orchestrator
Updated at: YYYY-MM-DDTHH:MM:SSZ

## Executor

Session: unregistered
Watch: unregistered
Workspace/worktree: unset

## Event Log

- YYYY-MM-DDTHH:MM:SSZ orchestrator: bootstrap created; waiting for Executor to start `/resonance:executor <uuid>`.
```

## Brainstorm Context Template

```markdown
# <Change Name> Brainstorm Context

**Date:** YYYY-MM-DD
**UUID:** <uuid>
**Plugin:** resonance
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
**Plugin:** resonance
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
- Use the long-lived Executor session for assigned tasks.
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
**Recommended session:** long-lived Executor session
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

Create one role-appropriate watcher for `<work-folder>/control.md` after bootstrap when the current agent supports it. Use an absolute file path. If the role session is Codex, use a Codex automation. If the role session is Claude Code, use Claude Code `Monitor`. The Executor creates its own role-appropriate watcher on the same `control.md` file after it registers itself.

Recommended intervals:

- Control baton monitor: every 2 minutes.

Automation names:

- `resonance-<short-uuid>-control-monitor`

Automation behavior:

1. Read `control.md`.
2. Respond only when `Owner: orchestrator` and `Status: awaiting-orchestrator`.
3. Use `Phase:`, `Target:`, and `Next action:` to choose the minimum context files.
4. For phases, append the Orchestrator response to the target discussion and update the phase context/alignment if needed.
5. For tasks, review only the target task execution file and update only that task's `Status:`.
6. Update `control.md` with the next owner/status/action and a concise event log entry.
7. Do nothing if the baton is assigned to the Executor, user, none, or already handled.
8. Stop or delete itself when `Status: complete` or `Status: user-decision-needed`.

Executor monitor behavior:

1. Register the Executor session in `control.md`.
2. Set `Owner: orchestrator`, `Status: awaiting-orchestrator`, and `Next action: executor-ready`.
3. Start the role-appropriate watcher on the absolute `control.md` path: Codex automation when running in Codex, Claude Code `Monitor` when running in Claude Code, or the current agent's equivalent.
4. Wake only when `Owner: executor` and `Status: awaiting-executor`.
5. Use `Phase:`, `Target:`, and `Next action:` to choose the minimum context files.
6. Write detailed output to the target discussion or execution file.
7. Return the baton by updating `control.md` to `Owner: orchestrator` and `Status: awaiting-orchestrator`.
8. Stop the watcher when `Status: complete` or `Status: user-decision-needed`.
9. Use the plugin-owned fallback shell monitor only when the current role session has no usable native watcher; record the fallback reason.

## Executor Phase Review Prompt

```text
Run /resonance:executor <uuid>. You are reviewing a resonance phase, not implementing product code.

Phase:
brainstorm | plan

Control:
<work-folder>/control.md

Context:
<work-folder>/<phase>/context.md

Discussion:
<work-folder>/<phase>/discussion.md

Act only if control.md says Owner: executor, Status: awaiting-executor, and Phase: <phase>. Review the phase context for missing context, unstated assumptions, bias, contradictions, feasibility risks, and unclear acceptance criteria. Append Executor review - round N to discussion.md. If the phase is acceptable, write Alignment: aligned. If changes are needed, write clear findings and leave Alignment: pending. Do not edit product code. Return the baton by updating control.md to Owner: orchestrator and Status: awaiting-orchestrator with Target: <phase>/discussion.md and a concise event log entry. Do not create a separate monitor markdown file; control.md is the baton and discussion.md is the record. Keep the global control watcher running until Status is complete or user-decision-needed. If there have been more than six review/response turns without alignment, set Status: user-decision-needed in control.md and ask the Orchestrator to escalate to the user.
```

## Executor Task Prompt

```text
Run /resonance:executor <uuid>. You are implementing one task from resonance.

Plan:
<work-folder>/plan/context.md

Task context:
<work-folder>/task-N/context.md

Task execution:
<work-folder>/task-N/execution.md

Act only if control.md says Owner: executor, Status: awaiting-executor, and Phase: task-N. Implement only that task in this Executor session. Follow the task context exactly. Do not implement future tasks. Do not read sibling task folders unless the claimed task's context.md explicitly names them as dependencies. Record this session and workspace/worktree in execution.md, then set Status to in-progress. When complete, update execution.md with summary, files touched, commands run, deviations, and open questions. Set Status to awaiting-orchestrator-review. Return the baton by updating control.md to Owner: orchestrator and Status: awaiting-orchestrator with Target: task-N/execution.md and Next action: review-task. If control.md later assigns this same task with Next action: fix-task, resume this Executor flow and fix only the Orchestrator findings for this task. Do not create a separate monitor markdown file; control.md is the baton and execution.md is the record. Keep the global control watcher running until Status is complete or user-decision-needed.
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

## Task Assignment Prompt

```text
Assign the next ready task for resonance.

Plan:
<work-folder>/plan/context.md

Task folders:
<work-folder>/task-*/

Read the plan, each task context.md, each task execution.md, and <work-folder>/control.md. Mark blocked tasks as not-started only when their dependencies are approved. Select ready tasks whose write locks do not overlap. Assign exactly one selected task at a time to the long-lived Executor by updating control.md with Owner: executor, Status: awaiting-executor, Phase: task-N, Target: task-N/execution.md, and Next action: execute-task. The Executor must write all responses to execution.md, not a separate monitor markdown file. Do not assign tasks with overlapping write locks in the same wave. Summarize the selected task, skipped tasks, and why each skipped task was not ready.
```

## Endgame

After all tasks are approved:

1. Run final verification from `<work-folder>/plan/context.md`.
2. Commit the implementation when the user requested commit ownership or the workflow requires it.
3. Push the branch when requested or expected by the repo workflow.
4. Open a PR to the target branch when requested or expected by the repo workflow.
5. Address PR review comments as focused follow-up commits.
6. Keep unrelated dirty files out of review-fix commits.
