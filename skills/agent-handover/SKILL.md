---
name: agent-handover
description: Create a durable handover package that transfers the current coding task between Claude and Codex. Use when the user asks to hand over, switch, transfer, resume, continue in another agent, move context to Claude/Codex, open a CLI/app session for the other agent, or preserve decisions, git state, files touched, commands run, worktree, brand/product context, and next steps for a receiving agent.
---

# Agent Handover

## Overview

Use this skill to package the active task into a concise, durable handover file and optionally open the receiving agent on macOS. Prefer reliable CLI handoff; use app handoff only when a supported app route exists.

## Workflow

1. Identify the source and target agents: `codex` or `claude`.
2. Capture task context using `scripts/create_handover.py`.
3. Add any conversation-only context the script cannot infer: user goal, latest instruction, decision reasons, brand/product details, blockers, and recommended next action.
4. Detect available target surfaces with `scripts/detect_targets.py` when the user wants the receiving agent opened.
5. Route with `scripts/launch_agent.py` when a CLI/app target is available. If routing is uncertain, print the handover path and receiving-agent prompt instead of guessing.
6. Tell the user where the handover was written and what route was used.

## Capture Rules

- Do not dump the full raw conversation. Summarize what the receiving agent needs to reconstruct state and continue safely.
- Always include workspace, worktree, branch, base commit when known, current HEAD, git status, files touched, commands run, verification, blockers, and next action.
- Include why decisions were made, not only what changed.
- Include unrelated dirty files as "do not touch" when visible.
- Respect repo-specific handover conventions. In this repo, write to `docs/handover/<slug>.md` when available; otherwise use `.agent-handover/<slug>.md`.
- If a matching task context exists, mention it in the handover and update its execution log only when the current agent actually completed that work.

Read `references/context-capture.md` when deciding what belongs in each handover section.

## Routing Rules

For macOS routing, read `references/mac-routing.md`.

- `auto`: use saved preference first; otherwise prefer CLI because it can receive a file path/prompt reliably.
- `cli`: launch the target CLI in the preferred terminal when detected.
- `app`: open the app only when detected. Do not claim full context injection unless the app exposes a supported route.
- If no reliable route exists, create the handover file and provide the exact prompt to paste into the receiving agent.

Store preferences in `~/Library/Application Support/agent-handover/preferences.json`. Use `scripts/preferences.py` to read or write them.

## Commands

Create a handover:

```bash
python3 skills/agent-handover/scripts/create_handover.py --to-agent claude --task "Short task title"
```

Detect local targets:

```bash
python3 skills/agent-handover/scripts/detect_targets.py
```

Launch a receiving CLI:

```bash
python3 skills/agent-handover/scripts/launch_agent.py --to-agent claude --handover docs/handover/my-task.md --surface cli
```

Show or save preferences:

```bash
python3 skills/agent-handover/scripts/preferences.py get
python3 skills/agent-handover/scripts/preferences.py set --agent claude --surface cli --terminal Ghostty
```
