# Compaction Survival Protocol

Auto-compaction WILL happen in long-running sessions. The agent cannot prevent or invoke it. This protocol designs for graceful survival, not escape.

---

## Core Mechanism

1. **CLAUDE.md is the anchor** — re-read verbatim from disk after every compaction (confirmed behavior, not summarized). This is the single most important survival property
2. **Forge Pipeline State section** in CLAUDE.md instructs the agent to re-read state files. Because CLAUDE.md survives verbatim, this instruction persists across unlimited compaction cycles
3. **State files on disk** (FORGE-HANDOFF.md, FORGE-STATUS.md, TODO.md, FORGE-MEMORY.md) are the authoritative source of truth — not conversation context
4. **Sub-agents provide context isolation** — short-lived, fresh context windows. Heavy work in sub-agents keeps the orchestrator's context leaner
5. **Git commits as checkpoints** — even with severe context degradation, git log + state files enable recovery

---

## After Compaction Recovery

1. CLAUDE.md is in context (verbatim, not summarized)
2. `## Forge Pipeline State` instructs: re-read state files
3. Read FORGE-HANDOFF.md → learn what was in progress, what was completed, what failed
4. Read FORGE-STATUS.md → confirm current milestone and phase
5. Resume from the point in "What's In Progress"
6. Increment `compaction_count` in FORGE-HANDOFF.md Health section

---

## Compaction Count Behavior

| Count | Strategy |
|-------|----------|
| 1-3 | Normal operation. Re-read state files, continue |
| 4-5 | Delegate more aggressively to sub-agents. Reduce orchestrator to coordination only |
| 5+ | Maximum delegation. Note degradation risk in FORGE-STATUS.md. If external orchestrator available, trigger fresh-agent handoff |

---

## State Update Strategy

Write **incremental deltas**, not full rewrites:
- TODO.md: mark `[x]` on completed steps (~20 tokens)
- FORGE-HANDOFF.md: update Active Work + In Progress every 5 steps (~200 tokens)
- Full FORGE-HANDOFF.md rewrite only at milestone boundaries (~600 tokens)
- Failed approaches: append, never rewrite

This keeps writes small and preserves the append-only property for KV-cache optimization.

---

## Persist Continuously

The orchestrator MUST persist state after every phase transition so compaction mid-phase loses at most one phase of context. Partially-completed phases are re-run from scratch (idempotent by design).

---

## Optional SessionStart Hook

Claude Code only. Secondary signal, not primary mechanism:

```json
{
  "hooks": {
    "SessionStart": [{
      "matcher": "compact",
      "hooks": [{
        "type": "command",
        "command": "echo 'COMPACTION DETECTED: Re-read FORGE-HANDOFF.md and FORGE-STATUS.md now.'"
      }]
    }]
  }
}
```

Note: SessionStart hook stdout injection after compaction is not fully reliable (Issue #15174). The primary mechanism remains CLAUDE.md surviving verbatim.

---

## Known Limitations

- Agents sometimes ignore CLAUDE.md instructions to re-read files (training bias, Issue #13919). Mitigation: keep Forge Pipeline State short, prominent, imperative
- Summary stacking after 3+ compaction rounds consumes ~30% of context with cumulative summaries. Mitigation: aggressive sub-agent delegation
- Context usage is not exposed to the agent (Issue #23457). The agent cannot detect compaction directly — it infers it from the Forge Pipeline State re-read
