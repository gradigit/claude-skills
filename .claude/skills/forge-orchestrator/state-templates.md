# State File Templates

Templates for the three primary state files maintained by the forge orchestrator.

---

## FORGE-STATUS.md

```markdown
---
milestone: {N}
phase: {research|planning|build|review|second-opinion|improvement|gate|compound}
updated: {ISO timestamp}
---
## Current State
Milestone {N} ({name}), Phase: {phase}. {N} of {total} tasks complete.
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
