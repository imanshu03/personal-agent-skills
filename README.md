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

## Notes

- Keep each skill's instructions in `skills/<skill-name>/SKILL.md`.
- Keep skill-specific scripts, references, and assets inside that same skill directory.
- Put shared contributor and agent guidance in `AGENTS.md`.

