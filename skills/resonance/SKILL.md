---
name: resonance
description: Coordinate large changes through a review-gated Orchestrator/Executor workflow where Codex is the Orchestrator and must create or dispatch Claude Code CLI Executor sessions in Warp or another terminal. Use when a feature, bug fix, refactor, migration, documentation change, design implementation, or release task is large enough to split into ordered tasks with strict brainstorm, plan, execution, review, and final-verification gates; also use for /resonance orchestrator, /resonance executor, requests to implement with resonance, and requests to launch Warp-based Claude Code Executor sessions for a resonance task.
---

# Resonance

Use resonance to coordinate a large change through durable markdown artifacts, terminal-launched Claude Code Executor sessions, and strict Orchestrator review gates.

Personal runtime mapping:

- Treat Codex as the Orchestrator.
- Treat Claude Code CLI as the Executor.
- Treat Warp as the terminal runtime.
- Have the Orchestrator open one feature-level Warp window when possible, record its handle, and dispatch each phase review or task execution as its own Claude Code CLI session in a dedicated Warp tab for that feature.

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
4. Create a Codex review automation for the absolute brainstorm discussion path when automation tools are available.
5. Dispatch a Claude Code CLI Executor phase review in a terminal/Warp session with `/resonance executor <uuid> brainstorm`.
6. Iterate until both agents mark `Alignment: aligned`.
7. Ask the user to approve the aligned brainstorm context before planning.
8. Use Superpowers writing-plans when available to create `<work-folder>/plan/context.md`.
9. Dispatch a Claude Code CLI Executor plan review in a terminal/Warp session with `/resonance executor <uuid> plan`.
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

Use Warp's URI scheme or launch configurations. Do not paste commands into Warp with UI keystrokes unless the user explicitly approves that local fallback.

Public Warp URI commands:

```bash
open "warp://action/new_window?path=<absolute-repo-or-worktree-path>"
open "warp://action/new_tab?path=<absolute-repo-or-worktree-path>"
open "warp://launch/<launch-configuration-name-or-path>"
```

Feature-window protocol:

1. Open one Warp window for the feature before the brainstorm Executor review.
2. Try to capture a local feature window handle if the machine exposes one.
3. Record the handle and dispatch templates in `<work-folder>/warp/window.md`.
4. Open each phase/task in a separate tab in that feature window.
5. If no window handle can be captured or focused, record `Window handle: unavailable` and use Warp launch configurations as the fallback.

Window handle capture is environment-specific. On macOS, this may require Accessibility permission:

```bash
feature_window_id="$(
  osascript -e 'tell application "System Events" to tell process "Warp" to get id of front window' 2>/dev/null || true
)"
```

Do not assume Warp accepts `window_id` in URI parameters unless the local Warp command template explicitly supports it. Warp's public URI scheme supports new windows, new tabs, and launch configurations; deterministic same-window targeting requires a verified local focus/window command.

Every dispatch must create a runner script or launch configuration that:

1. Sets the working directory to the repo root or assigned worktree.
2. Renames the tab with `resonance:<short-uuid>:<phase-or-task>`.
3. Starts a visible Claude Code CLI session with the matching `/resonance executor ...` prompt.
4. Writes the prompt under `<work-folder>/warp/prompts/`.
5. Writes a sentinel such as `<work-folder>/warp/<phase-or-task>.done` when the Claude Code session exits.

Use `claude "<query>"` as the default Warp invocation so the user can watch the Executor session. Use `claude -p` only for explicit headless smoke tests, CI-like checks, or when the user asks for non-interactive execution.

Runner script shape:

```bash
#!/usr/bin/env bash
set -euo pipefail

cd "<absolute-repo-or-worktree-path>"
printf '\033]0;%s\007' "resonance:<short-uuid>:<phase-or-task>"
mkdir -p "<work-folder>/warp/logs"
mkdir -p "<work-folder>/warp/prompts"

prompt_file="<work-folder>/warp/prompts/<phase-or-task>.txt"
cat > "$prompt_file" <<'EOF'
/resonance executor <uuid> <phase-or-task>

<phase-or-task prompt with absolute context paths>
EOF

claude \
  --permission-mode acceptEdits \
  --allowedTools Read,Edit,Bash \
  --append-system-prompt "You are Claude Code CLI running as the resonance Executor. Follow Executor mode exactly." \
  "$(<"$prompt_file")"

touch "<work-folder>/warp/<phase-or-task>.done"
```

If a headless run is explicitly needed, use the same prompt file with:

```bash
claude -p \
  --permission-mode acceptEdits \
  --allowedTools Read,Edit,Bash \
  --append-system-prompt "You are Claude Code CLI running as the resonance Executor. Follow Executor mode exactly." \
  "$(<"$prompt_file")" 2>&1 | tee "<work-folder>/warp/logs/<phase-or-task>.log"
```

Launch configuration shape:

```text
---
name: resonance-<short-uuid>-<phase-or-task>
windows:
  - tabs:
      - title: resonance:<short-uuid>:<phase-or-task>
        layout:
          cwd: <absolute-repo-or-worktree-path>
          commands:
            - exec: bash <absolute-runner-script-path>
        color: blue
```

Place launch configs in `$HOME/.warp/launch_configurations/`, then launch with:

```bash
open "warp://launch/resonance-<short-uuid>-<phase-or-task>.yaml"
```

For same-window dispatch, first focus the recorded feature window using the local verified command if one exists, then launch the new tab/config. If focus fails, continue with the launch configuration fallback and record the fallback in `<work-folder>/warp/window.md`.

## Reference

Read `references/protocol.md` when you need exact artifact schemas, status values, UUID lookup rules, automation prompts, phase discussion templates, task execution templates, or final dispatch/review prompt shapes.
