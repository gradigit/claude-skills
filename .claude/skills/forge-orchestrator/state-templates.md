# State File Templates

Templates for the three primary state files maintained by the forge orchestrator.

---

## FORGE-STATUS.md

```markdown
---
milestone: {N}
phase: {research|planning|build|review|second-opinion|improvement|gate|compound}
updated: {ISO timestamp}
spawns: {cumulative sub-agent/spawn_agent count this run}
milestones: {milestones STARTED this run}
state: {running|FINALIZED}
---
## Current State
Milestone {N} ({name}), Phase: {phase}. {N} of {total} tasks complete.
Spawns: {spawns}/50. Milestones: {milestones}/10.
Blocked on: {or "nothing"}.
Next action: {what to do next}.

## Milestones
- [x] Milestone 1: {name} — completed
- [ ] Milestone 2: {name} — in progress ({phase})
- [ ] Milestone 3: {name} — pending (blocked by M2)

## Active Agents
- {name}: {status} — {description}

## Human Steering Hashes
- HUMAN-INPUT.md: {hash}
- MISSION-CONTROL.md: {hash}
- SUGGESTIONS.md: {hash}

## Last Update: {timestamp}
```

**Write ownership**: Only the orchestrator (main thread) writes FORGE-STATUS.md. Sub-agents report status inline to the orchestrator.

**Update frequency**: Every phase transition within every milestone.

**Counters (circuit breaker)**: Increment `spawns` on every sub-agent spawn and
`milestones` when a new milestone starts. Before each spawn batch / new milestone,
run `python3 hooks/forge_spawn_breaker.py FORGE-STATUS.md` — exit 1 means STOP
(save state, summarize, ask the user). This makes the documented 50-spawn /
10-milestone breakers behavioral instead of advisory.

**Completion ledger**: `state` stays `running` until Finalization, which sets
`state: FINALIZED`. This single parseable line is the source of truth for
"run complete" — distinct from a turn ending. The completion guard (below) blocks
any write of `state: FINALIZED` (or a milestone marked completed) until GATE E
evidence exists.

---

## Goal-Reconciliation Artifact (GATE E)

Written to `architect/review-findings/{milestone}-goal-reconciliation.md` during
the GOAL RECONCILIATION GATE. Format the completion guard parses:

```markdown
# {Milestone} Goal Reconciliation

| Criterion | Code | Test | Status |
|-----------|------|------|--------|
| {acceptance criterion, verbatim from the milestone spec} | {file:line where implemented} | {named test that exists AND was run} | verified |
```

Rules the guard enforces (`hooks/forge_completion_guard.py`):
- Every acceptance criterion is a row; no placeholders (`-`, `TBD`, `{...}`).
- `Code` must resolve to a real `file:line` in the repo.
- `Test` must be a test that actually exists in source (not just named here — the
  guard excludes the forge artifacts from its search so writing the name is not enough).
- `Status` must be `verified` (the test was run and passed).

Run before COMPOUND/FINALIZATION: `python3 hooks/forge_completion_guard.py
architect/review-findings/{milestone}-goal-reconciliation.md --repo-root .` —
exit 0 is required to proceed. Escape hatch for genuine parser edge cases:
`--override "<reason>"` (logged loudly; justify in FORGE-MEMORY.md).

---

## FORGE-HANDOFF.md

```markdown
# Forge Handoff — {timestamp}

## Bootstrap
CLAUDE.md is already loaded (survives compaction). Re-read the mutable state files:
1. This file (session-level context snapshot)
2. FORGE-STATUS.md (milestone/phase state)
3. TODO.md (task checklist)
4. FORGE-MEMORY.md (cross-session learnings)

After reading, verify: current milestone matches FORGE-STATUS.md, current step matches TODO.md. If mismatch, trust FORGE-STATUS.md.

## Active Work
- **Milestone**: {N/total} — {name}
- **Step**: {N/total} — {name}
- **Status**: IN_PROGRESS | BLOCKED | COMPLETED
- **Working files**: {list}
- **Branch**: {current branch}

## What Was Just Completed
- [x] {step} (commit {hash})

## What's In Progress
{Current work description — specific enough to resume without guessing}

## Failed Approaches (This Session)
- Tried {X} → {why it failed}

## Blockers / Open Questions
- {or "None currently"}

## Key Context (Not in Other Files)
- {discoveries not yet in CLAUDE.md}

## Session Log Digest
{max ~500 tokens, high-signal decisions only}
{Priority: direction changes > rejected alternatives > constraints > debugging pivots}

## Health
- last_updated: {ISO timestamp}
- steps_since_last_checkpoint: {N}
- compaction_count: {N}
- stuck_indicator: {true|false}
- consecutive_failures: {N}
```

**Write ownership**: Only the orchestrator (main thread) writes FORGE-HANDOFF.md. Sub-agents report state inline.

**Update frequency**:

| Trigger | Write Type | Token Cost |
|---------|-----------|------------|
| Step completed | TODO.md mark `[x]` | ~20 tokens |
| Every 5 steps | Lightweight update (Active Work + In Progress) | ~200 tokens |
| Milestone completed | Full checkpoint (overwrite entire file) | ~600 tokens |
| Failed approach | Append to Failed Approaches section | ~100 tokens |
| Post-compaction recovery | Update compaction_count, verify state | ~100 tokens |

Total for a 4-milestone run: ~3,000 output tokens.

---

## FORGE-MEMORY.md

```markdown
# Forge Memory

Cross-session learnings. Minimum-signal gate: "Will a future agent act better knowing this?"
Keep under 3,000 tokens via aggressive deduplication.

## Architectural Decisions
- [{date}] {decision} — why: {rationale}. Alternatives rejected: {list}

## Failed Approaches
- [{date}] Tried {X} → failed because {Y}. Don't retry unless {condition}

## Patterns Learned
- [{date}] {pattern} — context: {when to apply}
```

**Deduplication rules**:
- Merge entries that describe the same decision or pattern
- Prefer the most recent entry when entries conflict
- Delete entries that are now captured in CLAUDE.md (promoted to project convention)

**Write frequency**: Updated during the COMPOUND step of each milestone.

FORGE-MEMORY.md doubles as the OKF `log.md` (append-only, newest-first). Stamp it
`--type forge-memory`.

---

## OKF Forge Type Vocabulary

When the COMPOUND step stamps artifacts (`okf_bundle.py stamp <file> --type <t>`),
use this controlled vocabulary so `index.md` can group and `freshness` can reason:

| Artifact | `type` |
|----------|--------|
| FORGE-STATUS.md | `forge-status` |
| FORGE-HANDOFF.md | `forge-handoff` |
| FORGE-MEMORY.md (= log.md) | `forge-memory` |
| SUGGESTIONS.md | `suggestions` |
| HUMAN-INPUT.md / MISSION-CONTROL.md | `steering` |
| architect/research/*.md | `research` |
| architect/review-findings/*.md | `review-finding` |
| milestone spec files | `milestone` |
| index.md | `index` (reserved) |

OKF requires only `type`; these are extension-friendly. `index.md` additionally
carries `okf_version: 0.1` (pin the Draft version).
