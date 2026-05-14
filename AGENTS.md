# Agent Instructions

This repository contains personal agent skills. Treat it as a skill library: root-level files are shared project documentation, and individual skills live under `skills/<skill-name>/`.

## Repository Layout

- `skills/agent-handover/SKILL.md`: Skill definition and workflow for transferring task context between agents.
- `README.md`: Human-facing overview of the repository.
- `AGENTS.md`: Canonical instructions for coding agents working in this repository.
- `CLAUDE.md`: Pointer to this file for Claude compatibility.

## Editing Guidelines

- Keep each skill self-contained under `skills/<skill-name>/`.
- Prefer adding skill-local materials beside the skill:
  - `skills/<skill-name>/scripts/`
  - `skills/<skill-name>/references/`
  - `skills/<skill-name>/assets/`
- Do not move a skill to the repository root unless the repository is intentionally being converted into a single-skill package.
- Update `README.md` when adding, renaming, or removing skills.
- Keep instructions concise and specific to this repository.

## Current Caveat

`skills/agent-handover/SKILL.md` currently references helper scripts under `skills/agent-handover/scripts/`. If those scripts are added later, keep the documented paths in sync.

