# Personal Agent Skills

A small collection of local agent skills for Codex, Claude, and adjacent coding-agent workflows.

## Layout

```text
skills/
  fast-turtle/
    SKILL.md
    references/
```

Skills live under `skills/<skill-name>/` so the repository can grow as a library while each skill stays self-contained. A root-level `SKILL.md` would make sense for a repository that contains exactly one skill; this repo keeps the root available for shared docs, tooling, tests, and future packaging.

Plugins (when a workflow needs slash commands or app-specific packaging) would live under `plugins/<plugin-name>/` and register in the marketplace files at `.claude-plugin/marketplace.json` (Claude Code) and `.agents/plugins/marketplace.json` (Codex). There are currently no plugins; those manifests carry an empty `plugins` list as scaffolding.

## Current Skills

- `fast-turtle`: Single-model, agent-agnostic structured build orchestration. Drives a large feature through gated brainstorm → architecture → plan + dependency-DAG → parallel milestone execution → per-milestone review → final-verification stages, fanning out independent milestones to parallel subagents with an independent reviewer gating each one. Ships `references/orchestration-recipe.md` (the fan-out pattern and ledger templates).

Run `fast-turtle` by asking an agent to build something large with it (for example,
"build this end to end with fast-turtle"). The skill writes its ledger docs under a
per-feature folder, `docs/fast-turtle/<feature>/`, so multiple features never clash.

## Install

Install a skill from this repository with `npx skills add`:

```bash
npx skills add https://github.com/imanshu03/personal-agent-skills.git/skills --skill fast-turtle
```

The repository URL points at the `skills/` directory, and `--skill` selects the skill folder to install. For future skills, replace `fast-turtle` with the folder name under `skills/`.

## Update

Update a globally installed skill with:

```bash
npx skills update fast-turtle -g -y
```

If the skill was installed as a global symlink for Claude and Codex, updating the global skill copy updates both agents. Restart any running agent sessions after updating so they reload the skill.

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

Skills in this repository are currently versioned by git history. Users can update skills to the latest published version with `npx skills update`.

For human-readable releases, use git tags such as `fast-turtle-v0.1.0` and summarize changes in GitHub releases or release notes. If a formal skill-level version field is adopted later, add it consistently to each `SKILL.md` frontmatter and document it here.

## Notes

- Keep each skill's instructions in `skills/<skill-name>/SKILL.md`.
- Keep skill-specific scripts, references, and assets inside that same skill directory.
- If a plugin is added later, keep its commands, references, scripts, agents, and assets inside `plugins/<plugin-name>/` and register it in the marketplace files.
- Put shared contributor and agent guidance in `AGENTS.md`.
