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
- Update `README.md` when adding, renaming, or removing skills, including the install command when the skill name changes.
- Keep instructions concise and specific to this repository.

## Install Convention

Document skills as installable from the repository's `skills/` directory:

```bash
npx skills add https://github.com/imanshu03/personal-agent-skills.git/skills --skill <skill-name>
```

Use the directory name under `skills/` as `<skill-name>`. For example:

```bash
npx skills add https://github.com/imanshu03/personal-agent-skills.git/skills --skill agent-handover
```
