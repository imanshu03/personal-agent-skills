# Personal Agent Skills

A small collection of local agent skills for Codex, Claude, and adjacent coding-agent workflows.

## Layout

```text
skills/
  agent-handover/
    SKILL.md
```

Skills live under `skills/<skill-name>/` so the repository can grow as a library while each skill stays self-contained. A root-level `SKILL.md` would make sense for a repository that contains exactly one skill; this repo keeps the root available for shared docs, tooling, tests, and future packaging.

## Current Skills

- `agent-handover`: Creates a durable handover package for moving an active coding task between Claude and Codex.

## Install

Install a skill from this repository with `npx skills add`:

```bash
npx skills add https://github.com/imanshu03/personal-agent-skills.git/skills --skill agent-handover
```

The repository URL points at the `skills/` directory, and `--skill` selects the skill folder to install. For future skills, replace `agent-handover` with the folder name under `skills/`.

## Update

Update a globally installed skill with:

```bash
npx skills update agent-handover -g -y
```

If the skill was installed as a global symlink for Claude and Codex, updating the global skill copy updates both agents. Restart any running agent sessions after updating so they reload the skill.

To check installed global skills:

```bash
npx skills list -g
```

If an update behaves unexpectedly, remove and reinstall the skill:

```bash
npx skills remove agent-handover -g -y
npx skills add https://github.com/imanshu03/personal-agent-skills.git/skills --skill agent-handover -g -a codex claude-code -y
```

## Versioning

Skills in this repository are currently versioned by git history. Users can update to the latest published version with `npx skills update`.

For human-readable releases, use git tags such as `agent-handover-v0.1.0` and summarize changes in GitHub releases or release notes. If a formal skill-level version field is adopted later, add it consistently to each `SKILL.md` frontmatter and document it here.

## Notes

- Keep each skill's instructions in `skills/<skill-name>/SKILL.md`.
- Keep skill-specific scripts, references, and assets inside that same skill directory.
- Put shared contributor and agent guidance in `AGENTS.md`.
