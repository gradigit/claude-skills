# Long-Running Build Sessions

Best practices for builds spanning multiple milestones or exceeding context limits. Based on Anthropic's "Effective Harnesses for Long-Running Agents" and cross-platform production data.

## Single-Feature Focus

Each build agent targets exactly one milestone or feature. Do not combine unrelated work in a single agent session.

**Why**: Context accumulation for one feature is productive — the agent builds up understanding of the problem space. Context accumulation across unrelated features is noise — it pollutes attention and degrades quality on all features.

**Rule**: If a build session discovers work outside its scope, write it to DEFERRED-CHANGES.md or SUGGESTIONS.md. Do not attempt it inline.

## Git-Based Checkpointing

Commit after each completed feature or milestone that passes its quality gate.

**Benefits**:
- Enables rollback if later phases introduce regressions
- Provides state recovery after crashes or context overflow
- Creates an audit trail of incremental progress

**Protocol**:
1. Phase passes quality gate
2. Stage changed files (`git add` specific files, not `-A`)
3. Commit with descriptive message referencing the milestone
4. Continue to next phase

**Rollback**: If a later phase fails its quality gate after 3 attempts, consider rolling back to the last checkpoint and re-approaching the phase differently.

## Compaction-Resilient State Persistence

Auto-compaction will happen during long sessions — the agent cannot prevent or invoke it. Design for graceful survival.

### State Files

| File | Purpose | Update Frequency |
|------|---------|-----------------|
| TODO.md | Task checklist with completion status | After each phase |
| FORGE-HANDOFF.md | Session-level context snapshot | Every 5 steps + at milestones |
| FORGE-STATUS.md | Orchestrator milestone/phase state | At phase transitions (orchestrator only) |
| CLAUDE.md | Project conventions + re-read instructions | At milestone completion |

### Persistence Rules

1. **Write state to disk continuously** — not just at milestones. If compaction occurs mid-phase, the most you should lose is one phase of context.
2. **CLAUDE.md is the anchor** — it survives compaction verbatim (re-read from disk, not summarized). Include a `## Forge Pipeline State` section with instructions to re-read state files.
3. **FORGE-HANDOFF.md supplements** what compaction summaries lose — session-level details like "what was I doing RIGHT NOW?" Keep it concise (~600 tokens).
4. **Partially-completed phases are re-run from scratch** — design phases to be idempotent. A phase that runs twice should produce the same result.

### Compaction Survival Protocol

After compaction:
1. CLAUDE.md is loaded (verbatim from disk)
2. `## Forge Pipeline State` instructs: re-read FORGE-HANDOFF.md, FORGE-STATUS.md, TODO.md
3. Agent reads state files, recovers session context
4. Agent resumes from the last completed phase transition
5. Agent increments `compaction_count` in FORGE-HANDOFF.md

### Compaction Count Thresholds

| Count | Behavior |
|-------|----------|
| 1-3 | Normal operation. Re-read state files, continue. |
| 4-5 | Delegate more aggressively to sub-agents. Keep orchestrator lean. |
| 5+ | Maximum sub-agent delegation. Note degradation risk in FORGE-STATUS.md. |

## Test-First Development

When test infrastructure exists, write or update tests before implementation.

**Benefits**:
- Tests serve as specification — they define what "done" means
- Tests serve as verification — they confirm the implementation works
- Red/Green TDD: write failing test, implement until it passes, refactor

**When to skip**: If the directive is about exploratory work, prototyping, or the project has no test infrastructure and the directive does not ask for it.

## Progress Narration

Before each significant action batch, emit a brief human-readable progress note:

```
-> About to implement the auth middleware. Files in scope: src/middleware/auth.ts,
  src/middleware/roles.ts. Expected: JWT validation + role-based access.
```

Never run silently for 5+ minutes. If a cycle produces no observable output, write a progress note explaining what is happening and why.

## Build Agent Lifecycle

```
1. Receive plan (from orchestrator or auto-generated)
2. Read practices guide (platform detection)
3. For each phase:
   a. Implement → self-review → test → improve → quality gate
   b. Commit on gate pass
   c. Update TODO.md
4. Final validation
5. Completion summary
```

If context begins degrading (repetitive outputs, forgotten constraints, contradictory statements), the build agent should:
1. Commit current progress
2. Write state to FORGE-HANDOFF.md
3. Signal completion of current scope
4. Let the orchestrator spawn a fresh agent for remaining work
