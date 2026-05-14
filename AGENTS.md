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

## Update Convention

Document globally installed skills as updatable with:

```bash
npx skills update <skill-name> -g -y
```

For example:

```bash
npx skills update agent-handover -g -y
```

If users installed global symlinks for Claude and Codex, explain that updating the global skill copy updates both agent installs. Remind users to restart active agent sessions after updating.

When troubleshooting update issues, recommend a clean reinstall:

```bash
npx skills remove <skill-name> -g -y
npx skills add https://github.com/imanshu03/personal-agent-skills.git/skills --skill <skill-name> -g -a codex claude-code -y
```

## Versioning Guidance

This repository currently uses git history as the source of truth for skill updates. The `npx skills update` command is the user-facing update mechanism.

For human-visible releases, prefer git tags named per skill, such as `agent-handover-v0.1.0`, and summarize changes in GitHub releases or release notes. Do not add an ad hoc `version` field to one skill unless the repo is adopting a consistent skill-level version convention for all skills.
