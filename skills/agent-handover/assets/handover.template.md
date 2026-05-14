# Agent Handover: {{TASK_TITLE}}

## Handover Intent

- Worked on by: {{WORKED_ON_BY}}
- Source detection: {{SOURCE_DETECTION}}
- Created at: {{CREATED_AT}}
- Workspace: `{{WORKSPACE}}`
- Worktree: `{{WORKTREE}}`
- Branch: `{{BRANCH}}`
- Base commit: `{{BASE_COMMIT}}`
- Current HEAD: `{{HEAD_COMMIT}}`

## User Goal

{{USER_GOAL}}

## Current Status

- Status: {{STATUS}}
- Last meaningful action: {{LAST_ACTION}}
- Recommended next action: {{NEXT_ACTION}}

## Context Summary

{{CONTEXT_SUMMARY}}

## Decisions Made

| Decision | Reason | Alternatives Considered |
| --- | --- | --- |
{{DECISIONS_TABLE}}

## Important Constraints

{{CONSTRAINTS}}

## Brand / Product Context

- Brand or product area: {{BRAND_AREA}}
- Audience: {{AUDIENCE}}
- Design tone: {{DESIGN_TONE}}
- Source docs loaded: {{SOURCE_DOCS}}

## Files Touched

| File | Change Type | Notes |
| --- | --- | --- |
{{FILES_TABLE}}

## Git State

```bash
# branch
{{BRANCH}}

# status --short
{{GIT_STATUS}}

# recent commits
{{RECENT_COMMITS}}
```

## Diff Summary

{{DIFF_SUMMARY}}

## Commands Run

| Command | Result | Notes |
| --- | --- | --- |
{{COMMANDS_TABLE}}

## Verification

- Tests run: {{TESTS_RUN}}
- Typecheck run: {{TYPECHECK_RUN}}
- Lint run: {{LINT_RUN}}
- Manual verification: {{MANUAL_VERIFICATION}}
- Remaining risk: {{REMAINING_RISK}}

## Blockers / Open Questions

{{BLOCKERS}}

## Do Not Lose

{{DO_NOT_LOSE}}

## Interaction Preference

When clarification is needed, use the receiving surface's structured or generative question UI if it is available. For example, Codex app may expose structured choice prompts in planning contexts. If the runtime does not provide such UI, ask concise plain-text questions instead.
