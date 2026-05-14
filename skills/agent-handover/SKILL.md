---
name: agent-handover
description: Create a durable handover document for moving the current coding task between Claude and Codex. Use when the user asks to hand over, switch, transfer, resume, continue in another agent, move context to Claude/Codex, or preserve decisions, git state, files touched, commands run, worktree, brand/product context, and next steps for another agent.
---

# Agent Handover

## Overview

Use this skill to package the active task into a concise, durable handover file. Do not open Claude, Codex, terminal apps, or desktop apps automatically. After writing the file, show the user the exact prompt to paste into whichever agent they choose.

## Workflow

1. Identify which agent worked on the task: `codex`, `claude`, or unknown. Use `scripts/detect_invocation.py` to infer this when the user did not specify it.
2. Choose where to store handover documents. If `.agent-handover.json` is missing, ask the user where to store them and offer `.agent-handover` as the default. Save the choice with `scripts/setup_handover.py`.
3. Capture task context using `scripts/create_handover.py`.
4. Add any conversation-only context the script cannot infer: user goal, latest instruction, decision reasons, brand/product details, blockers, and recommended next action.
5. Tell the user where the handover was written.
6. Show the exact prompt to paste into the other agent. Do not try to route or launch another agent.

## Capture Rules

- Do not dump the full raw conversation. Summarize what the receiving agent needs to reconstruct state and continue safely.
- Always include workspace, worktree, branch, base commit when known, current HEAD, git status, files touched, commands run, verification, blockers, and next action.
- Include why decisions were made, not only what changed.
- Preserve interaction preferences, including asking the receiving agent to use structured/generative question UI when its runtime supports it.
- Include unrelated dirty files as "do not touch" when visible.
- Respect the repo-local handover directory preference in `.agent-handover.json`. If no preference exists, ask the user and default to `.agent-handover`.
- If a matching task context exists, mention it in the handover and update its execution log only when the current agent actually completed that work.

Read `references/context-capture.md` when deciding what belongs in each handover section.

## Commands

Create a handover:

```bash
python3 skills/agent-handover/scripts/create_handover.py --task "Short task title"
```

Pass `--worked-on-by` when the detected source agent is wrong.

Configure handover storage:

```bash
python3 skills/agent-handover/scripts/setup_handover.py --dir .agent-handover
```

Use any directory path relative to the repository root. To show the current setting:

```bash
python3 skills/agent-handover/scripts/setup_handover.py --show
```

Detect the invoking agent:

```bash
python3 skills/agent-handover/scripts/detect_invocation.py --pretty
```
