# Resonance Plugin

Resonance exposes slash commands for a review-gated Orchestrator and Executor workflow. Roles are chosen at runtime: the agent/session that runs `/resonance:orchestrator` is the Orchestrator, and the agent/session that runs `/resonance:executor <uuid>` is the Executor.

## Commands

- `/resonance:orchestrator [change request]`: Start a resonance run, create the root `control.md` baton, and return the Executor command before substantive feature work.
- `/resonance:executor <uuid>`: Register a long-lived Executor session for the existing resonance run and monitor `control.md`.

The workflow is transpiled into plugin command files plus plugin-local references and scripts. No separate resonance install is required.

The plugin includes `scripts/fallback_monitor_control.sh` for fallback shell monitoring when native watchers are unavailable. Agents should run that plugin-owned script instead of creating custom monitor scripts.
