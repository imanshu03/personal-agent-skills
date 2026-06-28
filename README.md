# Personal Agent Skills

A small collection of local agent skills and plugins for Codex, Claude, and adjacent coding-agent workflows.

## Layout

```text
skills/
  fast-turtle/
    SKILL.md
    references/
plugins/
  resonance/
    agents/
    commands/
    references/
    scripts/
```

Skills live under `skills/<skill-name>/` so the repository can grow as a library while each skill stays self-contained. A root-level `SKILL.md` would make sense for a repository that contains exactly one skill; this repo keeps the root available for shared docs, tooling, tests, and future packaging.

Plugins live under `plugins/<plugin-name>/` when a workflow needs slash commands or app-specific packaging.

## Current Skills

- `fast-turtle`: Single-model, agent-agnostic structured build orchestration. Drives a large feature through gated brainstorm → architecture → plan + dependency-DAG → parallel milestone execution → per-milestone review → final-verification stages, fanning out independent milestones to parallel subagents with an independent reviewer gating each one. Ships `references/orchestration-recipe.md` (the fan-out pattern and ledger templates).

## Current Plugins

- `resonance`: Coordinates large changes through a review-gated two-agent workflow where whichever agent/session runs `/resonance:orchestrator` becomes the Orchestrator, whichever agent/session runs `/resonance:executor <uuid>` becomes the long-lived Executor, and both pass control through a root `control.md` baton file.

Run `fast-turtle` by asking an agent to build something large with it (for example,
"build this end to end with fast-turtle"). The skill writes its ledger docs under a
per-feature folder, `docs/fast-turtle/<feature>/`, so multiple features never clash.

Scaffold a new resonance work package with:

```bash
python3 plugins/resonance/scripts/init_work_package.py \
  --base-folder .resonance \
  --change-name "Short change name" \
  --user-request "Original user request" \
  --bootstrap-only
```

Resonance stores coordination files under a base folder (default `.resonance` or `docs/resonance`) chosen on first use. Bootstrap prints the `/resonance:executor <uuid>` command to run in the agent/session that should act as Executor.

## Install

Install a skill from this repository with `npx skills add`:

```bash
npx skills add https://github.com/imanshu03/personal-agent-skills.git/skills --skill fast-turtle
```

The repository URL points at the `skills/` directory, and `--skill` selects the skill folder to install. For future skills, replace `fast-turtle` with the folder name under `skills/`.

Resonance is plugin-only. To make `/resonance:orchestrator` and `/resonance:executor` appear in Claude Code or Codex, install or enable the `resonance` plugin from this repository.

For Claude Code, add this repository as a plugin marketplace and install the plugin:

```text
/plugin marketplace add imanshu03/personal-agent-skills
/plugin install resonance@personal-agent-skills
```

For local Claude Code testing from this checkout:

```bash
claude --plugin-dir plugins/resonance
```

For Codex, the repo-local plugin entry is in `.agents/plugins/marketplace.json`, and the plugin package is in `plugins/resonance`.

## Update

Update a globally installed skill with:

```bash
npx skills update fast-turtle -g -y
```

If the skill was installed as a global symlink for Claude and Codex, updating the global skill copy updates both agents. Restart any running agent sessions after updating so they reload the skill.

If you use the plugin commands, update or reinstall the `resonance` plugin as well, then restart active Claude Code and Codex sessions so the command picker reloads.

To check installed global skills:

```bash
npx skills list -g
```

If an update behaves unexpectedly, remove and reinstall the skill:

```bash
npx skills remove fast-turtle -g -y
npx skills add https://github.com/imanshu03/personal-agent-skills.git/skills --skill fast-turtle -g -a codex claude-code -y
```

## Versioning

Skills and plugins in this repository are currently versioned by git history. Users can update skills to the latest published version with `npx skills update`.

For human-readable releases, use git tags such as `fast-turtle-v0.1.0` and summarize changes in GitHub releases or release notes. If a formal skill-level version field is adopted later, add it consistently to each `SKILL.md` frontmatter and document it here.

## Notes

- Keep each skill's instructions in `skills/<skill-name>/SKILL.md`.
- Keep skill-specific scripts, references, and assets inside that same skill directory.
- Keep plugin-specific commands, references, scripts, agents, and assets inside `plugins/<plugin-name>/`.
- Put shared contributor and agent guidance in `AGENTS.md`.
