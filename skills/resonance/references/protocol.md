# Resonance Protocol Reference

Use this reference for exact artifact shapes, status values, and coordination prompts. Keep `SKILL.md` as the operational overview; load this file when creating or reviewing resonance artifacts.

## Table Of Contents

- Storage model
- UUID lookup
- Core artifacts
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

When invoked as `/resonance:executor <uuid>`, locate the work folder before acting:

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

## Phase Alignment

Brainstorm and plan phases use the same loop:

1. Orchestrator writes or updates phase `context.md`.
2. Orchestrator appends `### Orchestrator draft - round N` to `discussion.md`.
3. Orchestrator dispatches `/resonance:executor <uuid> <phase>`.
4. Executor reviews the phase context and appends `### Executor review - round N`.
5. Executor creates a temporary monitor for the phase discussion file.
6. Codex review automation responds in `### Orchestrator response - round N`.
7. Repeat until both agents write `Alignment: aligned`.
8. Ask the user to approve the aligned phase context.
9. Delete monitors/automations after user approval or `user-decision-needed`.

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

Create a Codex review automation for each active phase or task when automation tools are available. Use absolute file paths.

Recommended intervals:

- Brainstorm phase review: every 2 minutes.
- Plan phase review: every 2 minutes.
- Task review: every 4 minutes.

Automation names:

- `resonance-<short-uuid>-brainstorm-review`
- `resonance-<short-uuid>-plan-review`
- `resonance-<short-uuid>-task-1-review`

Automation behavior:

1. Read the target discussion or execution file.
2. Check whether Executor output is waiting for Orchestrator review.
3. Read only the needed context files.
4. Append the Orchestrator review or response.
5. Update the status field.
6. Do nothing if there is no pending Executor output.
7. Stop or delete itself when the phase is `user-approved`, the task is `approved`, or the item is `user-decision-needed`.

## Executor Phase Review Prompt

```text
Run /resonance:executor <uuid> <phase>. You are reviewing a resonance phase, not implementing product code.

Phase:
brainstorm | plan

Context:
<work-folder>/<phase>/context.md

Discussion:
<work-folder>/<phase>/discussion.md

Review the phase context for missing context, unstated assumptions, bias, contradictions, feasibility risks, and unclear acceptance criteria. Append Executor review - round N to discussion.md. If the phase is acceptable, write Alignment: aligned. If changes are needed, write clear findings and leave Alignment: pending. Do not edit product code. Create a temporary monitor for the absolute discussion.md path so this Claude Code CLI session notices Codex response updates. Keep the monitor running until the phase is user-approved or user-decision-needed, then delete the monitor and stop. If there have been more than six review/response turns without alignment, mark Status: user-decision-needed and ask the Orchestrator to escalate to the user.
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

If a task was not assigned explicitly, locate <work-folder> by UUID and claim the first ready task whose dependencies are approved and whose write locks do not conflict with an in-progress task. Implement only that task in this Executor session. Follow the task context exactly. Do not implement future tasks. Do not read sibling task folders unless the claimed task's context.md explicitly names them as dependencies. Record this session and workspace/worktree in execution.md, then set Status to in-progress. When complete, update execution.md with summary, files touched, commands run, deviations, and open questions. Set Status to awaiting-orchestrator-review. Create a temporary monitor for the absolute execution.md path so this Claude Code CLI session notices Codex review updates. Keep the monitor running until the task is approved or user-decision-needed, then delete the monitor and stop.
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

Follow the Orchestrator Review Process in execution.md and the Orchestrator Review Checklist in context.md. Review only Task N. Confirm the actual diff stays inside Task N's declared write locks. Append a new Orchestrator review round directly above Task N's Status line in execution.md and update only Task N's Status to approved or changes-requested.
```

## Parallel Dispatch Prompt

```text
Dispatch the next ready parallel wave for resonance.

Plan:
<work-folder>/plan/context.md

Task folders:
<work-folder>/task-*/

Read the plan, each task context.md, and each task execution.md. Mark blocked tasks as not-started only when their dependencies are approved. Select ready tasks whose write locks do not overlap. For each selected task, create a Codex review automation for the absolute task execution.md path at a 4-minute interval, then open a separate Warp window/tab in the assigned repo/worktree, rename it to resonance:<short-uuid>:task-N, and run Claude Code CLI with /resonance:executor <uuid> task-N. Do not dispatch tasks with overlapping write locks in the same wave. Summarize dispatched tasks, skipped tasks, and why each skipped task was not ready.
```

## Endgame

After all tasks are approved:

1. Run final verification from `<work-folder>/plan/context.md`.
2. Commit the implementation when the user requested commit ownership or the workflow requires it.
3. Push the branch when requested or expected by the repo workflow.
4. Open a PR to the target branch when requested or expected by the repo workflow.
5. Address PR review comments as focused follow-up commits.
6. Keep unrelated dirty files out of review-fix commits.
