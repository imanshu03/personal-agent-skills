---
name: fast-turtle
description: >-
  Single-model structured build orchestration — a gate-driven workflow that drives a
  large feature through enforced brainstorm → architecture → plan+dependency-DAG →
  gated milestone execution → review → final-verification gates, using dynamic
  parallel-agent workflows to fan out independent milestones in parallel and an
  independent review-subagent gate between every milestone. Agent-agnostic: works in
  any AI coding agent that can dispatch parallel subagents. Use this whenever the user
  wants to build, ship, refactor, or migrate something large enough to split into
  ordered tasks — a full app, an end-to-end feature across multiple packages/apps, a
  monorepo, a big migration or refactor — and wants it done with discipline rather
  than ad hoc. Trigger on "build this end to end", "ship the whole feature",
  "orchestrate this build", "use fast-turtle", "fast turtle", "structured build",
  "build this with review gates", "build the platform/app/service", "build this slow
  and steady", or any multi-milestone build where planning, review gates, and parallel
  execution matter. Prefer this over diving straight into code for anything beyond a
  few files. Does NOT require a second model — a single agent fills the planner,
  executor, and reviewer seats, but the reviewer is always a fresh subagent so work is
  never marked by the same context that produced it.
---

# Fast Turtle — single-model structured build orchestration

> Named for the trade-off it makes: deliberately paced (gated, reviewed, planned) yet
> fast in wall-clock because independent milestones fan out in parallel. Slow and
> careful where it counts; fast where it's safe.
>
> **Agent-agnostic.** This skill describes a *method*, not a specific tool. It needs
> only two capabilities from your AI agent: the ability to dispatch **parallel
> subagents** and (ideally) to run a **multi-stage workflow** over them. Where it
> names a primitive (a "dynamic workflow", a "pipeline"), map it to your agent's
> equivalent. The user decides which reasoning-effort levels to run at.

## What this is and why it exists

This skill reproduces the part of a structured, gate-driven workflow that actually
moves the needle on engineering quality, **without** any two-process baton machinery.
It was distilled from a controlled three-way benchmark of the same large build:

- **A** — a gate-driven workflow with a dedicated *second model* as Architect/Reviewer + an executor agent.
- **B** — a single agent, mirroring the full gate-driven phase sequence.
- **C** — a single agent, native, no structure.

**B won** (avg 7.50 vs C 7.44 vs A 7.28). The decisive findings this skill is built on:

1. **The structure won, not the second model.** B reached #1 with *none* of the
   two-process baton / monitor machinery — just the ordered phase artifacts plus
   self-review. The separate-model orchestrator (A) came **last** and uniquely
   shipped no real database. So: keep the gates, drop the second process.
2. **The structure's measurable wins were concentrated** in worker durability
   (crash-resume, AND/OR joins) and test depth (a real cross-service e2e) — i.e.
   in *what the plan-then-review loop forced you to think about*, not in raw output.
3. **The failure modes the gates must catch** were concrete: A shipped in-memory
   `Map`s where a real database was claimed; B's final report carried unbacked
   metrics; C left an untested DB path. So the review gate explicitly verifies
   *claims against code* and *persistence/tests are real, not stubbed*.

The other lesson: don't re-mark your own homework. A single agent plays planner,
executor, and reviewer here, but **the reviewer is always a fresh subagent** with no
memory of how the code was written — that independence is what a second model bought
in A, and you can get most of it for free by spawning a clean reviewer.

This skill **composes whatever phase-level skills your agent already has** (a
brainstorming skill, a planning skill, a code-review skill); where it has none, just
perform the phase directly. The parallel build phase runs on your agent's
**parallel-subagent / dynamic-workflow** capability. See
`references/orchestration-recipe.md` for a concrete workflow pattern and ledger templates.

## When to reach for it

Use it for anything large enough to have a dependency graph: a full app, a
feature spanning multiple packages/apps, a monorepo build, a sizeable migration
or refactor. For a one-or-two-file change, skip it — the ceremony costs more than
it returns. The honest ROI from the benchmark: the structured workflow beat the
unstructured one by only 0.06 points, so the value here is **consistency and
durability** (the gates fire every time, the plan forces failure-mode thinking),
not a magic quality jump.

## The gate sequence

Run these in order. Each gate composes a phase capability and **writes a numbered
ledger doc** before the next gate may begin — the ledger is what lets a long build
survive context limits/compaction without losing the thread (the `01..NN`
numbered-doc pattern). Never skip ahead; the point of a gate is that it blocks.

**Where the docs go — one folder per feature.** All of a build's ledger docs live in
its **own per-feature folder** so concurrent or sequential features never clash:
`docs/fast-turtle/<feature>/`, where `<feature>` is a kebab-case slug you choose at
gate 1 from the feature name (e.g. `docs/fast-turtle/short-link/`). Create that folder
at gate 1 before writing anything. In the table below, **`<base>` = `docs/fast-turtle/<feature>/`**.
Never write fast-turtle docs to a bare `docs/` — that's what causes cross-feature collisions.

> The "Capability" column lists what each gate does. If your agent ships a named skill
> for it, compose that skill; otherwise perform the phase directly.

| # | Gate | Capability to compose | Ledger doc written |
|---|------|-----------------------|--------------------|
| 1 | **Brainstorm / requirements** — surface intent, constraints, open questions | brainstorming / requirements elicitation | `<base>/01-requirements.md`, `<base>/02-brainstorming.md` |
| 2 | **Architecture** — system shape, package/app boundaries, contracts, the *seams that enable parallelism* | architecture (write directly; ground in research) | `<base>/03-architecture.md` |
| 3 | **Plan + dependency DAG** — milestones, critical path, disjoint file ownership per parallel task | planning | `<base>/04-planning.md` |
| 4 | **Architecture/plan review** — fresh subagent critiques the plan *before* code | independent review subagent | `<base>/05-architecture-review.md` |
| 5 | **Execute milestones** — spine first, then parallel fan-out | parallel subagent dispatch / dynamic workflow | per-milestone notes |
| 6 | **Review gate (per milestone)** — fresh subagent verifies each milestone before it's accepted | independent code review | review notes per milestone |
| 7 | **Final verification** — run the real toolchain; nothing is "done" on assertion | verification-before-completion | `<base>/NN-production-readiness.md` |
| 8 | **Honest final report** — accomplishments grounded in code, limitations named | (write directly) | `<base>/final-report.md` |

Create one todo per gate at the start so the sequence is visible and you can't
silently drop one. Get user sign-off after gates 1, 3, and 4 (the cheap-to-change
points) before committing effort to code.

## Execution phase: build the spine first, then fan out

This is the heart of the skill and where your agent's **parallel-subagent /
dynamic-workflow** capability does the work.

> **Runtime requirement — this gate needs parallel subagents.** The fan-out launches
> the independent milestones as parallel subagents (ideally orchestrated as a
> multi-stage workflow). If your agent *cannot* dispatch parallel subagents, you can
> still run the milestones **sequentially** through the same `implement → review → fix`
> gates — you keep the discipline and the independent review, you just lose the
> wall-clock parallelism. Don't silently collapse the milestones into one inline blob;
> that throws away the disjoint-ownership safety and the independent review gate that
> are the whole point of this phase.
>
> **Effort is the user's call.** This skill does not mandate any reasoning-effort
> level. If your agent supports tunable per-task effort and the user wants to spend it
> wisely, the judgment seats — the per-milestone **review** gate, the **integrate/verify**
> stage, the gate-4 plan review — are where extra effort pays off most, and mechanical
> seats (scaffolding, pure codegen) are where it's safe to economize. But that's an
> optimization the user controls, not a requirement of the method.

The winning structure from the benchmark:

1. **Build the critical-path core spine yourself, first, to a high bar.** In the
   benchmark everything gated on the core package (domain + contracts + engine),
   so it was built first and personally, not fanned out. Identify your spine from
   the dependency DAG in gate 3 and finish it before any fan-out.
2. **Fan out the independent milestones in parallel.** Once the spine's *interfaces*
   exist, every milestone that depends only on those interfaces (DB adapters, API,
   worker, SDK, UI/web, docs) runs **in parallel** with **disjoint file ownership** —
   no two agents write the same file, so there are no conflicts. Run each milestone
   through `implement → review → fix` independently (a *pipeline*), so a fast milestone
   isn't blocked waiting on the slowest sibling at a barrier.
3. **Gate every milestone behind an independent reviewer:** the review stage is a
   fresh subagent that verifies the milestone against its plan *and against the
   persistence/test/claims checklist below* before it's accepted.
4. **Integrate, verify live, and report** in a final barrier stage (this one *does*
   need all milestones present): run the real typecheck/test/build, boot the artifact
   if possible, then write the honest report.

The concrete workflow pattern (disjoint-ownership labels, the reviewer gate stage, and
isolated working copies for milestones that touch shared files) is in
**`references/orchestration-recipe.md`** — read it before writing the execution
workflow. Use isolated working copies (e.g. git worktrees) if parallel milestones must
touch overlapping files; prefer disjoint ownership so you don't need them.

## The review-gate checklist (what the fresh reviewer must verify)

These are the exact failure modes the benchmark caught. Every milestone reviewer,
and the final reviewer, must check — citing files, not vibes:

- **Persistence is real, not faked.** A claimed a database and shipped in-memory
  `Map`s with prose "migrations". If the plan says a real datastore, the reviewer
  confirms a real adapter + an executable migration runner exist and are exercised.
- **Tests are real and deep.** Count and classify them; confirm at least one
  genuine cross-service / e2e test, plus failure and edge-case tests — not just
  happy-path units. B's e2e was a measurable win; C's untested DB path was a loss.
- **Claims match code.** Before accepting any doc/report, the reviewer greps the
  code for each claim. B's report carried unbacked metrics; the gate exists to
  stop that. Label metrics honestly: Observed / Measured / Estimated / Self-reported.
- **No silent stubs.** TODOs, placeholder returns, dead tables, forked-copy files,
  and "in-memory only" rate-limit/cache that the docs imply is production — all
  must be surfaced as limitations, not hidden.
- **Verification before completion.** The toolchain actually ran and passed; paste
  the output. "Done" is never asserted, only demonstrated.

## The ledger (durable progress state)

The two-process variant used a baton file to coordinate two live sessions.
Single-agent, you don't need a baton — but you **do** need durable state so a
multi-hour build survives context limits/compaction. Keep two cheap things:

- **Numbered phase docs** under the per-feature folder `docs/fast-turtle/<feature>/`
  (gate table above) — the substantive record.
- **A `control.md`-lite status header** in that same feature folder
  (`docs/fast-turtle/<feature>/control.md`) — current gate, milestone statuses, next
  action, open questions. Template in `references/orchestration-recipe.md`.

Keeping every doc under `docs/fast-turtle/<feature>/` is what prevents two features
built in the same repo from overwriting each other's `04-planning.md` / `control.md`.

Update the status header at every gate transition. On resume, read it first to know
exactly where the build stopped.

## What this deliberately does NOT do

- **No second model required.** The benchmark showed the separate-model orchestrator
  finished last; the single agent acting as its own architect (B) shipped more. The
  independence that mattered is recovered via fresh reviewer subagents.
- **No baton / monitor / two-session protocol.** That machinery only exists to
  synchronize two live processes. Single-agent, it has no job.
- **No skipping the production backlog.** All three benchmark builds shipped mock
  auth, insecure default secrets, and in-memory rate-limit/cache. The final report
  must name this backlog honestly rather than imply deployability.

## Quick start

1. Confirm the build is big enough (has a dependency graph). If not, just code it.
2. Pick a kebab-case `<feature>` slug and create `docs/fast-turtle/<feature>/`; create
   one todo per gate (table above).
3. Walk gates 1–4, writing the numbered ledger docs into `docs/fast-turtle/<feature>/`
   and getting sign-off at 1, 3, 4.
4. Confirm your agent can dispatch parallel subagents; if not, plan to run the
   milestones sequentially through the same gates.
5. Build the spine yourself; then read `references/orchestration-recipe.md` and run
   the fan-out (pipeline: implement → review → fix). The user chooses effort levels.
6. Final-verify with the real toolchain; write the honest `final-report.md`.
