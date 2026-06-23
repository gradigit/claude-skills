---
name: forge-orchestrator
description: "Master orchestrator that sequences forge-research and forge-builder through milestone-gated cycles with adversarial review, testing, brainstorming, and compound learning. Designed for long-running autonomous sessions. Invoke with /forge [goal]. Do NOT use for single research questions (use forge-research) or simple builds (use forge-builder)."
license: MIT
metadata:
  version: "1.5.0"
  author: gradigit
  category: forge
  tags:
    - orchestrator
    - autonomous
    - forge
    - milestone
    - review
    - multi-agent
  triggers:
    - "forge"
    - "forge orchestrate"
    - "autonomous build"
    - "long-running build"
---

# Forge Orchestrator

Sequences research and building through milestone-gated cycles with review, improvement, and compound learning.

## Workflow Overview

```
- [ ] 1. Intake and orientation                → produces: milestones in TODO.md, CLAUDE.md updated
  ── GATE A: milestones defined + platform practices read ──
- [ ] 2. For each milestone:
      RESEARCH → PLANNING
        ── GATE B: reviewed plan exists before code changes ──
      → BUILD → REVIEW → SECOND-OPINION
        ── GATE C: review findings serialized before improvement ──
      → IMPROVEMENT → QUALITY GATE
        ── GATE D: gate passed before goal reconciliation ──
      → GOAL RECONCILIATION
        ── GATE E: all acceptance criteria have evidence before learning codification ──
      → COMPOUND
- [ ] 3. Finalization                          → produces: completion summary
```

**Loading model:** This ladder is your always-on phase pointer. Read each step's full
section (and its inline `> GATE` detail) when you *enter* that phase — you don't need
to hold the whole skill body in context between phases. Full-body re-reading every
turn drove ~40% of real runs to compact mid-run (worst: 142 compactions), which
corrupts state; lean on the ladder + the persisted FORGE-STATUS.md instead.

### Gate Protocol

The `── GATE … ──` markers in the ladder above are **hard STOP checkpoints**: every
phase must produce visible output before the next begins. To keep context lean, each
gate is defined **once, inline at its phase boundary** (the `> GATE X` blockquotes in
the steps below). The ladder is the always-on pointer; read a gate's full detail when
you reach its phase rather than holding the whole protocol in context.

**Why they exist:** the natural failure is shortcutting from BUILD straight to the
next milestone, skipping REVIEW (the primary quality mechanism), IMPROVEMENT, and
COMPOUND (learning codification) — each shortcut compounds across milestones.

**Defense against compaction:** GATE E (completion evidence) is **machine-enforced** by
`hooks/forge_completion_guard.py`, and the spawn/milestone circuit breaker by
`hooks/forge_spawn_breaker.py`, so they bind even if this prose is compacted away — the
deterministic `state: FINALIZED` ledger, not the in-context markers, is the source of
truth for "run complete."

---

## Step 1: Intake and Orientation

a. Read FORGE-HANDOFF.md if it exists (resumption). Follow the Bootstrap sequence in it
b. Read FORGE-STATUS.md, CLAUDE.md, TODO.md, FORGE-MEMORY.md, architect/ if they exist
c. If none exist: create CLAUDE.md and TODO.md from project scan
d. Platform detection:
   - Claude Code (Agent/TeamCreate tools present) → read forge-claude-teams SKILL.md
   - Codex CLI (spawn_agent/AGENTS.md present) → read forge-codex-multiagent SKILL.md
   - Fallback: assume Claude Code, log warning
e. Create HUMAN-INPUT.md, MISSION-CONTROL.md, FORGE-HANDOFF.md templates if missing (see [steering-templates.md](steering-templates.md) and [state-templates.md](state-templates.md))
f. Check HUMAN-INPUT.md and MISSION-CONTROL.md for pre-existing directives
g. Parse goal into milestones (see [milestone-template.md](milestone-template.md))
   - **First classify: directive vs inquiry** (prevents the milestone loop from
     running on a question and halting on a text-only turn — observed in 19% of
     completed Codex runs). **Inquiry** ("research X", "how should we…", "is X
     feasible", "compare…") → do NOT enter the build loop; run forge-research to
     completion, deliver findings, stop (build gates/COMPOUND do not apply).
     **Directive** ("build/add/fix/refactor X") → continue. Ambiguous → ask first.
   - Open-ended goals ("make this better"): scan codebase, identify top 5-10 improvements, present for user approval before proceeding
   - Concrete goals: structure into milestones directly
h. Write initial plan to TODO.md
i. Add forge sections to CLAUDE.md (see [claude-md-sections.md](claude-md-sections.md))
j. Add forge artifacts to .git/info/exclude: `FORGE-STATUS.md`, `FORGE-HANDOFF.md`, `FORGE-MEMORY.md`, `HUMAN-INPUT.md`, `MISSION-CONTROL.md`, `SUGGESTIONS.md`, `DEFERRED-CHANGES.md`, `architect/agent-contexts/`, `architect/review-findings/`, `.claude/forge-scopes.json`, `index.md`, `log.md`
k. Create `.claude/forge-scopes.json` with empty agents map: `{"agents": {}}`
l. Install the guard hooks + checkers (scope guard, completion guard, spawn breaker) into `.claude/hooks/` and register the PreToolUse entries in `.claude/settings.local.json` (see Guard Installation below). Initialize FORGE-STATUS.md counters `spawns: 0`, `milestones: 0`, `state: running`.

> **GATE A checkpoint**: Do not proceed to Step 2 unless you have (1) parsed the goal into milestones written to TODO.md, (2) read the platform practices guide, and (3) created all steering file templates. If any of these are missing, go back now.

---

## Step 2: Milestone Loop

**CHECK HUMAN-INPUT.md, MISSION-CONTROL.md, and SUGGESTIONS.md AT EVERY PHASE TRANSITION.**

### RESEARCH PHASE

- Launch forge-research for unknowns in the current milestone
- Research runs to completion before building starts
- Output: `architect/research/{topic}.md`
- Skip if milestone has no research needs

### PLANNING PHASE (complexity-adaptive)

Complexity tiers:
- **Simple** (single file, clear spec): skip detailed planning, inline approach notes
- **Standard**: concise approach with key decisions
- **Complex** (multi-file, unknowns, architectural): detailed plan with >=2 approaches + trade-offs

Steps:
1. Draft implementation plan for this milestone
2. Self-critique the plan
3. Spawn adversarial reviewer: "Find flaws in this plan"
4. Iterate until no CRITICAL/HIGH findings remain (max 3 iterations)
   - MEDIUM and LOW findings are acceptable — note for implementation awareness

> **GATE B checkpoint**: Do not proceed to BUILD unless you have a reviewed implementation plan. If the plan has not been self-critiqued AND adversarially reviewed (for standard/complex milestones), STOP — building without a reviewed plan is the #1 cause of rework across milestones.

### BUILD PHASE

- Launch forge-builder with the refined plan
- Builder executes with self-review and self-improvement loops
- Builder writes completion signal when done
- Orchestrator waits for completion before proceeding

### REVIEW PHASE (parallel fan-out, FRESH context)

**CRITICAL: All review agents run in FRESH context. They receive ONLY:**
1. The milestone spec/requirements
2. The git diff of changes
3. Relevant test results

They do NOT receive the builder's conversation history. Fresh-context review avoids confirmation bias (40-60% quality improvement per ASDLC research).

**Batch 1** (up to 4 parallel — critical reviews):
- Adversarial review: bugs, logic errors, security issues
- Feature-presence review: verify each acceptance criterion has corresponding code paths and tests
- Performance review: inefficiencies, bottlenecks
- Test review: coverage gaps, missing scenarios

**Batch 2** (after batch 1 — enhancement reviews):
- Documentation: update/create docs for changes made
- Brainstorm: improvements, optimizations

Orchestrator collects all findings and serializes to `architect/review-findings/{milestone}.md`.

### SECOND-OPINION PHASE (optional)

- Try other CLIs if available (Codex, Gemini, Claude). Send git diff + intent
- Skip unavailable CLIs gracefully. Note which were unavailable
- Common case: all unavailable → skip entirely, note in summary

> **GATE C checkpoint**: Do not proceed to IMPROVEMENT unless review findings are collected and serialized to `architect/review-findings/{milestone}.md`. If you have not fanned out review agents in fresh context, STOP — skipping fresh-context review eliminates 40-60% of quality improvement. The review fan-out is the orchestrator's primary quality mechanism.

### IMPROVEMENT PHASE

1. Consolidate all review findings
2. Classify each finding:
   - **Bug fix** → apply immediately
   - **Improvement** (existing functionality) → apply
   - **New feature** → write to SUGGESTIONS.md, do not implement
3. Launch forge-builder with consolidated fixes and improvements
4. Re-run quality gates after improvements

### QUALITY GATE

Pass criteria (ALL must hold):
- Tests pass
- All critical review findings addressed
- No regressions
- Diminishing returns check: did this cycle improve substantially over last?

Outcomes:
- **Pass** → proceed to GOAL RECONCILIATION GATE
- **Fail** → loop back to BUILD PHASE (max 2 retries per milestone)
- **Fail after 2 retries** → escalate to user with details

> **GATE D checkpoint**: Do not proceed to GOAL RECONCILIATION unless the quality gate has been explicitly evaluated and passed. If you are about to reconcile goals or move to the next milestone without a gate evaluation, STOP — ungated work codifies bad patterns that propagate to all future milestones.

### GOAL RECONCILIATION GATE

**Prevents false completion — the #1 cause of user trust erosion.**

Before codifying learnings, verify that what was built actually matches what was requested:

1. Extract acceptance criteria from the milestone spec in TODO.md
2. For each criterion, require:
   - **Code evidence**: file:line where the behavior is implemented
   - **Test evidence**: named test that validates the behavior
   - **Runtime evidence** (if applicable): screenshot, log output, or manual verification note
3. Check for "merged" items: if a todo was merged into another, verify the merged item's implementation covers the original acceptance criteria. **Merged ≠ Complete** — status stays `in_progress` until behavior ships
4. Check for pinned requests: if the user requested the same thing twice or more, it is **pinned critical** — cannot be closed without all three evidence types
5. Write reconciliation result to `architect/review-findings/{milestone}-goal-reconciliation.md` using the table format in [state-templates.md](state-templates.md) (one row per criterion: `Criterion | Code | Test | Status`).
6. **Run the completion guard** (mandatory, deterministic — this is what makes GATE E bind):
   ```bash
   python3 hooks/forge_completion_guard.py \
     architect/review-findings/{milestone}-goal-reconciliation.md --repo-root .
   ```
   Exit 0 is **required** to proceed. The guard fails the gate unless every
   criterion has a `Code` file:line that resolves and a `Test` that actually
   exists in source (it excludes the forge artifacts from its search, so naming a
   test is not enough). **On Codex this is the primary enforcement** — there is no
   PreToolUse hook, and running the guard is itself a tool call that keeps the turn
   alive. Escape hatch for a genuine parser edge case: `--override "<reason>"`
   (logged; justify in FORGE-MEMORY.md). This addresses the #1 observed failure:
   GATE E was prose-only and bypassed in ~88% of completed runs.

Outcomes:
- **Guard exits 0 (all criteria have resolvable evidence)** → proceed to COMPOUND
- **Guard exits 1 (any criterion lacks evidence)** → loop back to BUILD PHASE with the unmet criteria as the scope (max 1 retry)
- **Retry exhausted** → escalate to user: "These acceptance criteria have no implementation evidence: {list}"

> **GATE E checkpoint**: Do not proceed to COMPOUND unless every acceptance criterion has code + test evidence mapped in the goal reconciliation artifact. If you are about to codify learnings or move to the next milestone without verifying criteria, STOP — unverified completion is the #1 cause of user trust erosion and compounds across milestones.

### COMPOUND STEP

After gate passes, codify learnings:
1. Update CLAUDE.md with conventions/patterns discovered this milestone
2. Consolidate SUGGESTIONS.md (deduplicate, sort by confidence)
3. Check SUGGESTIONS.md for human feedback:
   - **Approved** → add as new milestones or append to upcoming milestone scope
   - **Rejected** → mark status `rejected`, skip
   - **Needs-revision** → incorporate comments, refine plan, mark `planned`
4. Update TODO.md with deferred items and next steps
5. Update FORGE-MEMORY.md with learnings (minimum-signal gate: "Will a future agent act better knowing this?")
6. Update FORGE-STATUS.md with current state
7. Update FORGE-HANDOFF.md (full checkpoint)
8. **EMIT the OKF layer** (makes the artifact tree self-describing + navigable —
   see [OKF Artifact Layer](#okf-artifact-layer)):
   - Stamp each root forge artifact: `python3 .claude/hooks/okf_bundle.py stamp <file> --type <forge-type>` (vocabulary in [state-templates.md](state-templates.md): forge-status / handoff / memory / suggestions / research / review-finding / milestone …). FORGE-MEMORY.md is the canonical OKF `log.md` (append-only, newest-first).
   - Regenerate the root index: `python3 .claude/hooks/okf_bundle.py index . --okf-version 0.1`, then enrich its body with the FORGE-HANDOFF Bootstrap read-order + grouped `architect/research/*` and `architect/review-findings/*` listings with one-line descriptions, and backlinks (research ↔ review-finding ↔ milestone).
   - Emission is single-writer (orchestrator only).
9. Git commit milestone output
10. **Transition to next milestone immediately**: Read the next milestone's scope
   from TODO.md right now. Do NOT produce a standalone summary between milestones
   — on Codex CLI, a text-only response (no tool calls) ends the turn and halts
   the orchestration. The summary is implicit in the state files you just updated.
   If this is the last milestone, proceed to Step 3.

---

## Step 3: Finalization

a. Run full test suite
b. Update CLAUDE.md with what was built
c. Update TODO.md with completion status
d. Consolidate SUGGESTIONS.md (deduplicate, reconcile, sort by confidence)
e. Generate summary: what was done, what was deferred, what needs human attention
f. Update FORGE-STATUS.md with final state and set the completion ledger line
   **`state: FINALIZED`** (the parseable source of truth for run-complete — distinct
   from a turn ending). On Claude, the completion-guard PreToolUse hook blocks this
   write unless GATE E evidence exists for the milestones; on Codex, confirm the
   final milestone's completion guard passed before writing it.
g. **OKF final pass**: regenerate the root index, then
   `python3 .claude/hooks/okf_bundle.py validate . --recursive` (every artifact
   carries `type`+`timestamp`, reserved files exempt) and
   `python3 .claude/hooks/okf_bundle.py freshness . --recursive` (flag any artifact
   stamped before the repo's current state — re-stamp or mark historical).
h. Cleanup: delete `architect/agent-contexts/` and `DEFERRED-CHANGES.md`. **Keep
   `architect/review-findings/{milestone}-goal-reconciliation.md`** as the durable
   completion-evidence ledger (do not delete the reconciliation artifacts).

---

## Milestone Structure

Each milestone has explicit per-step success criteria. Without them, agents frequently skip steps or declare premature completion.

Reference: [milestone-template.md](milestone-template.md)

---

## Parallelism Model

**Parallelized serial threads** — parallel THREADS each running sequential work internally.

| Pattern | Parallelism | Rationale |
|---------|------------|-----------|
| Independent milestones | Parallel threads (2-3 max) | Each thread owns its files |
| Phases within a milestone | Sequential within thread | Context accumulation, data deps |
| Build agents on related files | Sequential within thread | Cascading changes need prior ctx |
| Review/audit after build | Fan-out within thread (3 max) | Independent read-only reviewers |
| Research queries | Fan-out within thread (3-5 max) | Independent info gathering |
| Two threads modifying same file | **NEVER** | Redesign decomposition |
| Build and review simultaneously | **NEVER** | Review needs completed code |
| Multiple threads writing same output | **NEVER** | Orchestrator is single writer |

---

## Agent Spawning Protocol

**Before each spawn batch** (and before starting a new milestone): run the circuit
breaker and update the counter — this makes the documented limits behavioral
(5/98 observed runs blew past 50 spawns, max 118, with zero narration):
```bash
python3 hooks/forge_spawn_breaker.py FORGE-STATUS.md   # exit 1 = STOP, save state + ask user
```
On exit 0, proceed and increment `spawns` (and `milestones` at milestone start) in
FORGE-STATUS.md frontmatter; surface the running `spawns/50` count in the phase
transition write. On exit 1, do not spawn — save state, summarize, ask the user.

For every sub-agent:

1. Draft context handoff using the 7-tag XML template (see [sub-agent-template.md](sub-agent-template.md))
2. Declare FILE SCOPE: For build agents, add a structured FILE SCOPE block (own/read/deny) to `<boundaries>` and write the scope to `.claude/forge-scopes.json` keyed by the agent's worktree absolute path. Skip for read-only agents (research, review).
3. Validate: prompt under 4K tokens, end-state objective, parseable output-format
4. Write handoff to `architect/agent-contexts/{name}.md` for workers; inline for quick tasks
5. Model: inherit (no override, no downgrades)
6. Isolation: `"worktree"` for build agents; shared for research/review
7. Agent type: use the specific custom agent for each role:
   - **forge-build-worker** (`.claude/agents/forge-build-worker.md`): implementation work with file-scope ownership
   - **forge-research-worker** (`.claude/agents/forge-research-worker.md`): web research and codebase exploration (read-only)
   - **forge-adversarial-reviewer** (`.claude/agents/forge-adversarial-reviewer.md`): critical review with confidence gating
   - **forge-performance-auditor** (`.claude/agents/forge-performance-auditor.md`): metric-driven performance analysis
   - Review roles without a dedicated agent (**feature-presence, test, documentation, brainstorm**) → `general-purpose` (Claude) / `explorer` (Codex) with that role's contract from REVIEW PHASE inlined into the prompt (there is no separate brainstorm agent file — inline its contract)
   - Use `general-purpose` for thread coordinators or tasks that don't match a custom agent
8. Validate output on return (see Sub-Agent Output Quality Bar)

---

## Sub-Agent Output Quality Bar

| Dimension | Pass (2) | Marginal (1) | Fail (0) |
|-----------|----------|--------------|----------|
| Schema | Exact match | Minor deviations | Missing sections |
| Evidence | All cited | Some unsourced | No evidence |
| Scope | Within bounds | Minor creep | Significant OOS |
| Completeness | All addressed | Most addressed | Key missing |
| Actionability | Immediately usable | Needs interpretation | Needs rework |

Minimum: 8/10. Score 6-7: request corrections (1 retry). Below 6: re-spawn with revised prompt. Do not surface scores to user — internal quality control only.

---

## Compaction Survival

Reference: [compaction-protocol.md](compaction-protocol.md)

---

## Concurrent Invocation Protection

Check FORGE-STATUS.md on startup. If an active run exists:
- **Recent** (<1 hour): warn user — "A forge orchestration is in progress. Resume or start fresh?"
- **Stale** (>1 hour): warn user — "Found abandoned forge run from {timestamp}. Resume or start fresh?"
- **Resume**: read FORGE-STATUS.md, pick up from last phase transition
- **Fresh**: archive FORGE-STATUS.md to `FORGE-STATUS.{timestamp}.md`, start clean

---

## Human Steering

Three async communication channels (human writes at any time, agent reads at phase transitions):

| File | Direction | Purpose |
|------|-----------|---------|
| SUGGESTIONS.md | Bidirectional | Agent writes suggestions, human approves/rejects |
| HUMAN-INPUT.md | Human → Agent | New work items, brainstorming ideas |
| MISSION-CONTROL.md | Human → Agent | Steering directives, course corrections |

**Change detection**: At each phase transition:
1. Read the file
2. Compare hash against last-seen hash (stored in FORGE-STATUS.md)
3. If changed: parse `## New` / `## Active Directives` for unprocessed items
4. Process items, move to `## Processed` / `## Acknowledged`
5. Update hash in FORGE-STATUS.md

Templates: [steering-templates.md](steering-templates.md)

---

## Exit Conditions

| Condition | Threshold |
|-----------|-----------|
| Milestone gate pass | Per-milestone criteria |
| Diminishing returns | <10% new actionable findings |
| Quality gate retries | Max 2 per milestone |
| Plan review iterations | Max 3 per milestone |
| Research depth cycles | Max 3 per research campaign |
| User intervention | Save state immediately |
| Global circuit breaker | Max 10 milestones, max 50 agent spawns per run |

When a global limit is hit: save state, present summary, ask user to continue or stop.

---

## Merge Strategy

Worktree branches merge one at a time:
1. Dependency order first (if deps exist between agents)
2. Completion order for independent agents (first-to-finish merges first)
3. Merge conflict → **STOP**, present to user. Do not auto-resolve cross-agent conflicts

---

## Scope Registry

When spawning build agents with FILE SCOPE declarations, the orchestrator writes the scope to `.claude/forge-scopes.json`:

```json
{
  "agents": {
    "/absolute/path/to/.claude/worktrees/agent-name": {
      "name": "agent-name",
      "owns": ["src/auth/*", "src/middleware/auth.*"],
      "readonly": ["src/config/*"],
      "deny": ["src/routes/*"]
    }
  }
}
```

The forge-scope-guard PreToolUse hook reads this file to validate file edits against declared scope. The registry is keyed by worktree absolute path (the agent's cwd).

The orchestrator creates this file during Step 1 (Intake) and updates it each time a build agent is spawned. Read-only agents (research, review) are not added to the registry.

---

## Guard Installation

During Step 1 (Intake), the orchestrator installs the guard hooks + checkers:

1. Copy the guard scripts:
   ```bash
   mkdir -p .claude/hooks
   cp .claude/skills/forge-orchestrator/hooks/forge-scope-guard.sh .claude/hooks/
   cp .claude/skills/forge-orchestrator/hooks/forge-completion-guard.sh .claude/hooks/
   cp .claude/skills/forge-orchestrator/hooks/forge_completion_guard.py .claude/hooks/
   cp .claude/skills/forge-orchestrator/hooks/forge_spawn_breaker.py .claude/hooks/
   cp .claude/skills/handoff-fresh/scripts/okf_bundle.py .claude/hooks/   # OKF emitter (single source: handoff-fresh)
   chmod +x .claude/hooks/forge-*.sh .claude/hooks/forge_*.py .claude/hooks/okf_bundle.py
   ```

2. Create or update `.claude/settings.local.json` with the PreToolUse hook entries
   (merge, don't overwrite, if the file already exists):
   ```json
   {
     "hooks": {
       "PreToolUse": [
         { "matcher": "Edit|Write", "hooks": [ { "type": "command", "command": ".claude/hooks/forge-scope-guard.sh" } ] },
         { "matcher": "Write|Edit", "hooks": [ { "type": "command", "command": ".claude/hooks/forge-completion-guard.sh" } ] }
       ]
     }
   }
   ```

**Two guards, two postures:**

| Guard | Trigger | Posture | Cross-platform |
|-------|---------|---------|----------------|
| `forge-scope-guard.sh` | Edit/Write outside declared FILE SCOPE | **warn-only** (exit 0) | Claude hook only |
| `forge-completion-guard.sh` → `forge_completion_guard.py` | Write that marks a run/milestone complete (`state: FINALIZED`, milestone completed) without passing GATE E | **blocks** (exit 2) | Claude hook; Codex runs `forge_completion_guard.py` directly at GATE E |
| `forge_spawn_breaker.py` | before each spawn batch / new milestone | **STOP** (exit 1) at limit | run directly on both platforms |

The scope guard stays warn-only (the corpus shows the orchestrator does almost all
writes; blocking would mostly false-positive). The completion guard blocks because
false-completion was the dominant failure — but it has an escape hatch
(`FORGE_GATE_OVERRIDE=1`, logged) so a parser edge case cannot deadlock a
legitimately-complete run.

---

## OKF Artifact Layer

Forge emits a sprawling artifact tree (FORGE-STATUS/HANDOFF/MEMORY, SUGGESTIONS,
`architect/research/*`, `architect/review-findings/*`, milestone files). The
OKF-lite layer makes it self-describing, navigable, and deterministically
fresh — so a resuming agent (or `/pickup`) can orient in one read and tell
current state from historical. It adopts **conventions only** (markdown +
frontmatter); it does NOT depend on the upstream `okf` Python package.

Mechanics (emitter: `.claude/hooks/okf_bundle.py`, single-sourced from
handoff-fresh; pyyaml-only):

| Element | What | When |
|---------|------|------|
| Per-file frontmatter | `type` + ISO `timestamp` (+ forge type vocabulary) | COMPOUND `stamp` |
| `index.md` | bundle index: read-order + grouped, typed listing + backlinks; carries `okf_version: 0.1` | COMPOUND `index` (orchestrator enriches body) |
| `log.md` | append-only run history — **FORGE-MEMORY.md is the canonical log** (newest-first) | COMPOUND |
| recursive validate | every artifact carries `type`+`timestamp` (reserved `index.md`/`log.md` exempt) | FINALIZATION |
| freshness | flag artifacts stamped before the repo's current state (git HEAD, or mtime outside git) | FINALIZATION + builder intake |

Rules: emission is **single-writer** (orchestrator only); `index.md`/`log.md` are
git-excluded with the other forge artifacts; keep the emitter additive (do not fork
toward the heavy upstream package). The same emitter powers handoff-fresh, so any
change must keep handoff-fresh's `validate` green.

## Error Recovery

| Failure | Response |
|---------|----------|
| Agent crash | Spawn FRESH agent with same context + failure note |
| Quality gate fail | Fix → re-gate (max 2) → escalate to user |
| Merge conflict | Present to user, pause orchestration |
| Context overflow | Compaction survival protocol (see reference) |
| All second-opinion CLIs unavailable | Skip phase, note in summary |

Never retry a crashed agent — spawn fresh. Never `send_input` to a failed agent.

---

## Self-Evolution

Version 1.5.0. See CHANGELOG.md.
