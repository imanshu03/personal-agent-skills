---
description: Start a resonance Orchestrator run and return the Executor command first
argument-hint: "[change request]"
---

# /resonance:orchestrator

You are running the bundled resonance Orchestrator command.

Do not invoke or depend on any external resonance instructions. This plugin command is the Orchestrator entrypoint.

Treat `$ARGUMENTS` as the user's requested change. If no change request is provided and the conversation does not already define one, ask one concise question for the change request.

## Plugin References

Read the plugin-local workflow and protocol references before acting unless they are already in context:

- In an installed Claude Code plugin when `CLAUDE_PLUGIN_ROOT` is available: `@${CLAUDE_PLUGIN_ROOT}/references/workflow.md` and `@${CLAUDE_PLUGIN_ROOT}/references/protocol.md`
- In this repository checkout: `plugins/resonance/references/workflow.md` and `plugins/resonance/references/protocol.md`

Before doing any substantive feature work:

1. Identify the repo or workspace root.
2. Choose or ask for the resonance base folder, preferring `.resonance` or `docs/resonance`.
3. Generate a UUID and short change slug.
4. Create the work folder and root `control.md`, preferably with the plugin-local `scripts/init_work_package.py --bootstrap-only` when available.
5. Return this exact next-step shape to the user:

```text
Run this in the agent/session that will act as Executor:

/resonance:executor <uuid>
```

After the user starts the Executor, continue the resonance Orchestrator workflow through the root `control.md` baton file. Keep feature context in phase and task files, not in `control.md`.
