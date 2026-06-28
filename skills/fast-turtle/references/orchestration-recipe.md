# Orchestration recipe — parallel fan-out + ledger templates

Read this before writing the execution-phase fan-out (gate 5–6). It gives you a
concrete spine-then-fan-out pattern plus the two ledger templates. Adapt names to the
actual project; the *shape* is what won the benchmark.

**Agent-agnostic note.** The code block below is expressed in one representative
multi-stage-workflow API (`agent()` dispatches a subagent; `pipeline()` runs each item
through stages independently; `parallel()` is a barrier that waits for all). These are
*primitives*, not a specific product — map them to whatever your AI agent offers:

- `agent(prompt, opts)` → "dispatch a subagent with this prompt".
- `pipeline(items, stageA, stageB, …)` → "run each item through these stages
  independently, no barrier between stages" (a fast item can reach stage B while a slow
  one is still in stage A).
- `parallel(thunks)` → "run these concurrently and wait for all" (a barrier).
- If your agent has no workflow layer at all, run the same stages **sequentially** per
  milestone — you keep the gates and the independent review, you just lose parallelism.

## Table of contents
1. The execution model (spine → parallel fan-out → integrate)
2. Fan-out workflow pattern (pipeline: implement → review → fix)
3. Disjoint file-ownership table (how to avoid merge conflicts)
4. The reviewer subagent prompt (the gate)
5. Ledger template A — `control.md`-lite status header
6. Ledger template B — numbered phase docs

---

## 1. The execution model

```
spine (built by you, first, to a high bar)
  │   e.g. packages/core: domain + contracts + engine + validation
  ▼
parallel fan-out (subagents in parallel, disjoint file ownership)
  ├─ db       (packages/db)     ─┐
  ├─ api      (apps/api)         │  each milestone independently flows:
  ├─ worker   (apps/worker)      ├─  implement → independent review → fix
  ├─ sdk      (packages/sdk)     │  (pipeline, NOT a barrier — no waiting on siblings)
  ├─ ui+web   (packages/ui,web)  │
  └─ docs     (docs/fast-turtle/<feature>/*) ─┘
  ▼
integrate + verify-live + honest report (final barrier stage)
```

Why a `pipeline` and not a barrier: a barrier would make every fast milestone wait
for the slowest (the worker is usually the long pole). A pipeline lets `db` finish
and get reviewed while `worker` is still being implemented. Use a barrier only for
the final integrate/verify stage, which genuinely needs all milestones present.

The spine is built **before** the fan-out, by you, because everything gates on it
and its contracts must be stable before fan-out (in the benchmark, the core spine
was the entire critical path).

---

## 2. Fan-out workflow pattern

Run this after the spine is built and committed. It pipelines each milestone through
implement → review → fix, then integrates. **Effort levels are the user's choice** —
if your agent supports tunable per-task effort, the judgment seats (review, integrate)
are where extra effort pays off and mechanical seats are where it's safe to economize,
but nothing here mandates a level.

```javascript
// Representative workflow API — map agent()/pipeline()/parallel() to your agent's primitives.
const ROOT = '/abs/path/to/repo'
const FEATURE = 'short-link'                 // kebab-case slug for THIS feature; pick at gate 1
const DOCS = `docs/fast-turtle/${FEATURE}`   // every ledger + design doc for this feature lives here — one folder per feature, no cross-feature clashes
// Derived from gate-3 dependency DAG. `owns` = the ONLY paths this agent may write.
const MILESTONES = [
  { key: 'db',    owns: 'packages/db/**',                 needs: 'core contracts' },
  { key: 'api',   owns: 'apps/api/**',                    needs: 'core contracts' },
  { key: 'worker',owns: 'apps/worker/**',                 needs: 'core engine' },
  { key: 'sdk',   owns: 'packages/sdk/**',                needs: 'core DTOs' },
  { key: 'webui', owns: 'packages/ui/**, apps/web/**',    needs: 'core DTOs, sdk shape' },
  { key: 'docs',  owns: `${DOCS}/**`,                     needs: 'all of the above' },
]

const REVIEW_SCHEMA = {
  type: 'object', additionalProperties: false,
  required: ['milestone', 'accepted', 'blockers', 'evidence'],
  properties: {
    milestone: { type: 'string' },
    accepted:  { type: 'boolean' },
    blockers:  { type: 'array', items: { type: 'string' } },   // must be empty to accept
    evidence:  { type: 'string' },                              // file refs proving the checks
  },
}

const results = await pipeline(
  MILESTONES,
  // Stage 1 — implement. Writes ONLY under `owns`.
  m => agent(
    `Implement milestone "${m.key}" of the build in ${ROOT}.\n` +
    `You may WRITE ONLY under: ${m.owns}. Read the spine contracts read-only.\n` +
    `Follow ${DOCS}/04-planning.md for this milestone's scope. Write real code — no stubs, ` +
    `no in-memory fakes where the plan calls for real persistence. Include unit + failure + ` +
    `edge-case tests. Run this package's typecheck+test before returning. Report what you built with file refs.`,
    { label: `impl:${m.key}` }
  ),
  // Stage 2 — independent review gate (fresh subagent, see §4).
  (impl, m) => agent(reviewerPrompt(ROOT, m, impl), { label: `review:${m.key}`, schema: REVIEW_SCHEMA }),
  // Stage 3 — fix any blockers, then re-confirm.
  (review, m) => review.accepted ? review : agent(
    `Milestone "${m.key}" was REJECTED by review. Blockers:\n- ${review.blockers.join('\n- ')}\n` +
    `Fix every blocker (write only under ${m.owns}), re-run typecheck+test, and report the fixes with file refs.`,
    { label: `fix:${m.key}` }
  )
)

// Barrier is correct here: integration needs ALL milestones present.
const integration = await agent(
  `All milestones are implemented and reviewed in ${ROOT}. Run the FULL workspace toolchain ` +
  `(install, typecheck, test, build) and paste real output. Boot the built artifact if feasible and ` +
  `confirm a real end-to-end path works. Then write ${DOCS}/final-report.md: accomplishments grounded in ` +
  `code with file refs, metrics labeled Observed/Measured/Estimated/Self-reported, and the honest ` +
  `production backlog (auth, secrets, distributed state) named — do not imply deployability.`,
  { label: 'integrate+report' }
)

return { results, integration }
```

Notes:
- If two milestones genuinely must touch a shared file, give those subagents an
  **isolated working copy** (e.g. a git worktree) and merge after — but prefer
  disjoint ownership so you never need to.
- Keep the spine OUT of the fan-out. It's already built; the fan-out consumes it.

---

## 3. Disjoint file-ownership table

Put this in `docs/fast-turtle/<feature>/04-planning.md`. The rule that eliminates
merge conflicts: **no two parallel agents write the same file.** Apps depend on the
spine's *interfaces* (dependency injection), not on each other's concretes — that
decoupling is what makes the fan-out safe.

| Milestone | Writes ONLY under | Reads (read-only) |
|-----------|-------------------|-------------------|
| db        | `packages/db/**`  | core contracts |
| api       | `apps/api/**`     | core contracts |
| worker    | `apps/worker/**`  | core engine |
| sdk       | `packages/sdk/**` | core DTOs |
| ui+web    | `packages/ui/**`, `apps/web/**` | core DTOs, sdk shape |
| docs      | `docs/fast-turtle/<feature>/**` | everything |

---

## 4. The reviewer subagent prompt (the gate)

The reviewer is a **fresh subagent** — it did not write the code, so it can't rubber-stamp
its own choices. Build its prompt from the SKILL.md review checklist:

```javascript
function reviewerPrompt(root, m, impl) {
  return `You are an independent reviewer. You did NOT write this code. Verify milestone "${m.key}" ` +
  `in ${root} against ${DOCS}/04-planning.md, citing files for every judgment. Set accepted=false if ANY check fails:\n` +
  `1. Persistence is REAL where the plan says so — a real adapter + executable migrations, not in-memory Maps or prose.\n` +
  `2. Tests exist and are deep — unit + failure + edge-case, and (for cross-cutting milestones) a real integration/e2e path.\n` +
  `3. Every claim the implementer made is backed by code you can see — grep for it.\n` +
  `4. No silent stubs: surface TODOs, placeholder returns, dead code, forked-copy files.\n` +
  `5. The package's own typecheck+test actually pass.\n` +
  `List concrete blockers (empty array = accept). Implementer's self-report:\n${impl}`
}
```

---

## 5. Ledger template A — `control.md`-lite status header

Write to `docs/fast-turtle/<feature>/control.md` (same per-feature folder as the phase
docs). Single-agent: this is **status only**, not a baton. Update it at every gate
transition so a resumed session knows exactly where it stopped.

```markdown
# Build Status — <feature name>

Updated: <ISO timestamp>
Current gate: <1 brainstorm | 2 architecture | 3 plan | 4 plan-review | 5 execute | 6 review | 7 verify | 8 report>
Next action: <one line>

## Milestones
| Milestone | Status (todo/impl/review/accepted) | Notes |
|-----------|-----------------------------------|-------|
| core (spine) | accepted | built first, to a high bar |
| db        | impl   | |
| api       | todo   | |
| ...       |        | |

## Open questions
- <question awaiting user / decision>

## Sign-offs
- Gate 1 brainstorm: <approved? when>
- Gate 3 plan: <approved? when>
- Gate 4 plan-review: <approved? when>
```

---

## 6. Ledger template B — numbered phase docs

The substantive record (the winning `01..NN` structure). All under the per-feature
folder `docs/fast-turtle/<feature>/`. One file per gate; later milestones append
their own notes. A real winning sequence was:

```
docs/fast-turtle/<feature>/
  01-requirements.md          07-api.md
  02-brainstorming.md         08-security-review.md
  03-architecture.md          09-performance-review.md
  04-planning.md              10-rollout.md
  05-architecture-review.md   11-production-readiness.md
  06-testing-strategy.md      final-report.md
  control.md
```

Each doc states its gate/role at the top, records decisions with rationale, and
ends with what the next gate needs. The plan doc (`04`) must contain the milestone
table, the dependency DAG, the critical path, and the disjoint-ownership table —
those four are what make the fan-out safe and parallel.
