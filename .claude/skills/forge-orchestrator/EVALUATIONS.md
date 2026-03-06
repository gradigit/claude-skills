# Evaluations for forge-orchestrator

## Scenario 1: Happy path — full orchestration with milestones (should-trigger, functional)

**Given** user invokes the orchestrator with a multi-step goal
**When** user says "forge build a REST API with auth, CRUD endpoints, and a test suite"
**Then**
- [ ] Skill activates and runs intake/orientation (Step 1)
- [ ] Platform detection runs and reads the correct Layer 0 practices guide
- [ ] Goal is parsed into structured milestones with per-step success criteria
- [ ] TODO.md and FORGE-STATUS.md are created
- [ ] CLAUDE.md gets Compact Instructions and Forge Pipeline State sections
- [ ] HUMAN-INPUT.md, MISSION-CONTROL.md, FORGE-HANDOFF.md templates are created
- [ ] Forge artifacts are added to .git/info/exclude
- [ ] For each milestone, the full loop executes: RESEARCH → PLANNING → BUILD → REVIEW → SECOND-OPINION → IMPROVEMENT → QUALITY GATE → COMPOUND
- [ ] Review agents run in fresh context (not builder's context)
- [ ] FORGE-STATUS.md is updated at every phase transition
- [ ] COMPOUND step updates CLAUDE.md, FORGE-MEMORY.md, and TODO.md
- [ ] Finalization runs: full test suite, summary generated, cleanup performed

## Scenario 2: Edge case — resumption after compaction (should-trigger, functional)

**Given** the orchestrator was running and auto-compaction occurred
**When** CLAUDE.md Forge Pipeline State section is re-read post-compaction
**Then**
- [ ] Agent re-reads FORGE-HANDOFF.md, FORGE-STATUS.md, TODO.md, FORGE-MEMORY.md
- [ ] Current milestone and phase are correctly identified from FORGE-STATUS.md
- [ ] Agent resumes from "What's In Progress" in FORGE-HANDOFF.md
- [ ] compaction_count is incremented in FORGE-HANDOFF.md Health section
- [ ] No work is duplicated — previously completed steps remain marked [x] in TODO.md
- [ ] Partially-completed phase is re-run from scratch (idempotent)

## Scenario 3: Edge case — human steering via MISSION-CONTROL.md (should-trigger, functional)

**Given** the orchestrator is running and the human writes a directive to MISSION-CONTROL.md
**When** human adds "PRIORITY: Focus on the auth module, defer dashboard" to Active Directives
**Then**
- [ ] At the next phase transition, orchestrator detects the file change via hash comparison
- [ ] The directive is parsed from the Active Directives section
- [ ] Milestones are reordered to prioritize auth
- [ ] The directive is moved to the Acknowledged section with timestamp and action taken
- [ ] FORGE-STATUS.md hash is updated to reflect the processed change
- [ ] Deferred work is noted in TODO.md and SUGGESTIONS.md

## Scenario 4: Should-NOT-trigger — simple research question or quick build

**Given** user has a straightforward task that does not need orchestration
**When** user says "research the best caching strategies for Redis" or "add a health check endpoint"
**Then**
- [ ] forge-orchestrator does NOT activate
- [ ] forge-research activates for research questions
- [ ] forge-builder activates for simple build tasks
- [ ] No milestone infrastructure is created (no FORGE-STATUS.md, no FORGE-HANDOFF.md)

## Scenario 5: Edge case — concurrent invocation protection (should-trigger, functional)

**Given** a forge orchestration is already in progress (FORGE-STATUS.md exists with active run)
**When** user invokes forge again
**Then**
- [ ] Orchestrator detects existing FORGE-STATUS.md on startup
- [ ] If recent (<1 hour): warns user and offers resume or fresh start
- [ ] If stale (>1 hour): warns user about abandoned run, offers resume or fresh start
- [ ] Resume path: picks up from last phase transition in FORGE-STATUS.md
- [ ] Fresh path: archives existing FORGE-STATUS.md with timestamp, starts clean

## Scenario 6: Performance — milestone throughput and agent budget (performance)

**Given** an orchestration with 3 milestones, each with research + build + review phases
**When** the full pipeline runs to completion
**Then**
- [ ] Total agent spawns stay under 50 (global circuit breaker)
- [ ] Total milestones stay under 10 (global circuit breaker)
- [ ] FORGE-STATUS.md updates occur at every phase transition
- [ ] FORGE-HANDOFF.md checkpoint writes stay under 3,000 output tokens total
- [ ] Review agents run in fresh context (no builder history leakage)
