---
name: resonance
description: Coordinate large changes through a review-gated two-agent workflow where Codex acts as Orchestrator and Claude Code CLI acts as Executor. Use when a feature, bug fix, refactor, migration, documentation change, design implementation, or release task is large enough to split into ordered tasks with strict brainstorm, plan, execution, review, and final-verification gates; also use for /resonance:orchestrator, /resonance:executor, and requests to implement work with resonance.
---

# Resonance

Use resonance to coordinate a large change through durable markdown artifacts, separate Executor sessions, and strict Orchestrator review gates.

Personal runtime mapping:

- Treat Codex as the Orchestrator.
- Treat Claude Code CLI as the Executor.
- Treat Warp as the terminal runtime.
- Run each phase review or task execution in its own Claude Code CLI session, opened from a dedicated Warp tab or window.

## Core Rule

Never let an Executor move to another task until the Orchestrator approves the current task and explicitly assigns or dispatches the next task.

## Invocation Modes

Interpret these requests as Orchestrator mode:

```text
/resonance:orchestrator
Let's implement <change> with resonance.
Use resonance for <change>.
```

Interpret these requests as Executor mode:

```text
/resonance:executor <uuid>
/resonance:executor <uuid> task-N
/resonance:executor <uuid> brainstorm
/resonance:executor <uuid> plan
```

In Executor mode, locate the existing work folder by UUID before doing anything else. Do not create a new work folder for an unknown UUID.

## First Moves

1. Identify the repo or workspace root.
2. Ask where to store resonance coordination files unless the base folder is already documented in the repo or conversation.
3. Prefer `.resonance` or `docs/resonance` as base-folder options.
4. Generate a UUID and a change slug.
5. Create `<base-folder>/<change-slug>-<uuid>/`.
6. Create or update `<base-folder>/index.md`.
7. Use `scripts/init_work_package.py` when it helps scaffold the folder and starter files.

Example:

```bash
python /Users/imanshurathore/.codex/skills/resonance/scripts/init_work_package.py \
  --base-folder .resonance \
  --change-name "Add saved searches" \
  --user-request "Build saved search support end to end"
```

## Orchestrator Workflow

1. Use Superpowers brainstorming when available to explore context, constraints, approaches, trade-offs, and acceptance criteria.
2. Write the draft design direction into `<work-folder>/brainstorm/context.md`.
3. Record the draft and review loop in `<work-folder>/brainstorm/discussion.md`.
4. Create a Codex review automation for the absolute brainstorm discussion path when automation tools are available.
5. Dispatch a Claude Code CLI Executor phase review in Warp with `/resonance:executor <uuid> brainstorm`.
6. Iterate until both agents mark `Alignment: aligned`.
7. Ask the user to approve the aligned brainstorm context before planning.
8. Use Superpowers writing-plans when available to create `<work-folder>/plan/context.md`.
9. Review the plan through `<work-folder>/plan/discussion.md` with `/resonance:executor <uuid> plan`.
10. Iterate until both agents mark `Alignment: aligned`.
11. Ask the user to approve the aligned plan context before implementation.
12. Create one `task-N/` folder per approved task, each with `context.md` and `execution.md`.
13. Self-review all task contexts for missing requirements, vague steps, overlapping write locks, missing verification, inconsistent names, and placeholders.
14. Dispatch only ready tasks whose dependencies are approved and whose write locks do not overlap.
15. Review each task independently through its `execution.md`.
16. Run final verification only after every task is approved.

If a phase or task exceeds six review/response turns without alignment or approval, mark it `user-decision-needed` and ask the user to decide.

## Executor Workflow

1. Locate the work folder by UUID.
2. Read `plan/context.md`.
3. If reviewing a phase, read that phase's `context.md` and `discussion.md`, append an Executor review, create a temporary monitor, and stop.
4. If implementing a task, claim exactly one ready task.
5. Read only `plan/context.md`, the selected task's `context.md`, the selected task's `execution.md`, and repo files required by that task.
6. Confirm the task status is `not-started` or `changes-requested`.
7. Confirm dependencies are approved and write locks do not conflict with active work.
8. Set the task status to `in-progress`.
9. Implement only the current task.
10. Record summary, files touched, commands run, deviations, and open questions in `execution.md`.
11. Set status to `awaiting-orchestrator-review`.
12. Create a temporary monitor for that task's absolute `execution.md` path.
13. Stop until Orchestrator approval or changes requested.

Do not read sibling task folders unless the current task context explicitly names them as dependency inputs.

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

## Warp Dispatch

Use the local Warp launch command if known. The command must:

1. Open Warp.
2. Set the working directory to the repo root or assigned worktree.
3. Rename the tab with `resonance:<short-uuid>:<phase-or-task>`.
4. Start Claude Code CLI with the matching `/resonance:executor ...` command.

Conceptual template:

```text
<open-warp-command> --cwd <absolute-repo-or-worktree-path> --title resonance:<short-uuid>:<phase-or-task> -- <claude-code-cli> "/resonance:executor <uuid> <phase-or-task>"
```

If tab renaming happens inside the shell, run:

```bash
printf '\033]0;%s\007' 'resonance:<short-uuid>:<phase-or-task>'
```

## Reference

Read `references/protocol.md` when you need exact artifact schemas, status values, UUID lookup rules, automation prompts, phase discussion templates, task execution templates, or final dispatch/review prompt shapes.
