---
description: Register a long-lived Executor for an existing resonance run
argument-hint: "<uuid>"
---

# /resonance:executor

You are running the bundled resonance Executor command. The agent/session that invokes this command becomes the Executor for this resonance run.

Do not invoke or depend on any external resonance instructions. This plugin command is the Executor entrypoint.

Treat `$ARGUMENTS` as the resonance run UUID. If no UUID is provided, ask for the UUID and do not create a new work folder.

## Plugin References

Read the plugin-local workflow and protocol references before acting unless they are already in context:

- In an installed Claude Code plugin when `CLAUDE_PLUGIN_ROOT` is available: `@${CLAUDE_PLUGIN_ROOT}/references/workflow.md` and `@${CLAUDE_PLUGIN_ROOT}/references/protocol.md`
- In this repository checkout: `plugins/resonance/references/workflow.md` and `plugins/resonance/references/protocol.md`

Executor startup contract:

1. Locate the existing resonance work folder by UUID.
2. Read the root `control.md`.
3. Register this Executor session in `control.md`.
4. Set `Owner: orchestrator`, `Status: awaiting-orchestrator`, and `Next action: executor-ready`.
5. Start one native monitor/watch on the absolute `control.md` path when the current agent supports it: Codex automations in Codex, Claude Code `Monitor` in Claude Code, or the current agent's equivalent. If no native watcher is available, run the plugin-owned `scripts/fallback_monitor_control.sh`; do not create a custom shell monitor.
6. Wait until `control.md` says `Owner: executor` and `Status: awaiting-executor`.

When the baton is assigned to the Executor, read only the files named by `Phase:`, `Target:`, and `Next action:`. Write detailed review or implementation output to the target `discussion.md` or `execution.md`, then return the baton through `control.md`.
