# Context Capture

Use the handover to preserve decision-quality context, not raw transcript volume.

## Include

- Latest user request and any earlier constraints that still apply.
- Product, brand, audience, and design-system context the next agent would otherwise need to rediscover.
- Repo instructions loaded: root `AGENTS.md`, app `AGENTS.md`, architecture docs, personas, task files, design docs, or handover specs.
- Files read, files modified, files created, and files intentionally avoided.
- Git state: repository root, worktree path, branch, base commit if known, current HEAD, dirty status, relevant commits.
- Commands actually run, with pass/fail outcome. Do not list aspirational checks.
- Decision reasons and alternatives considered when they affect future implementation.
- Verification performed and residual risk.
- Next concrete action for the receiving agent.

## Exclude

- Long raw diffs unless the user explicitly asks.
- Full chat transcripts when a structured summary is enough.
- Unrelated commit history.
- Guesses about tests or commands that were not run.
- Secrets, API keys, tokens, private credentials, or local-only credentials.

## Commit Guidance

- `Base commit`: the commit before task work began, when known.
- `Current HEAD`: the repository's current `HEAD`.
- `Task commits`: include commits created for this task.
- `Relevant prior commits`: include only if they explain current behavior or constraints.
- `Do not include`: broad unrelated history that makes the receiving agent chase noise.

## Conversation-Only Fields

The scripts can infer git and file state, but the current agent must fill these when they matter:

- `User Goal`
- `Context Summary`
- `Decisions Made`
- `Brand / Product Context`
- `Commands Run`
- `Verification`
- `Do Not Lose`
- `Recommended next action`
