# Changelog

All notable changes to the forge-orchestrator skill.

## [1.4.0] - 2026-03-06

### Added
- GOAL RECONCILIATION GATE between QUALITY GATE and COMPOUND (GATE E)
- Acceptance criteria ↔ evidence mapping in milestone template (Code/Test fields filled by builder, verified at GATE E)
- Feature-presence reviewer in REVIEW PHASE Batch 1 (verifies acceptance criteria have corresponding code paths and tests)
- "Merged ≠ Complete" policy: merged todos stay `in_progress` until behavior ships
- Pinned request escalation: user repeats same request twice → pinned critical, cannot close without all evidence types
- Goal reconciliation artifact: `architect/review-findings/{milestone}-goal-reconciliation.md`

### Changed
- Workflow overview now shows GOAL RECONCILIATION step between QUALITY GATE and COMPOUND
- GATE D now gates GOAL RECONCILIATION (was COMPOUND)
- QUALITY GATE pass outcome now routes to GOAL RECONCILIATION GATE (was COMPOUND)
- REVIEW PHASE Batch 1 expanded from 3 to 4 parallel reviewers
- Milestone template Rules section updated with acceptance criteria requirements

### Context
Post-mortem from real forge run where a user goal (hybrid Typora mode) was marked complete but never implemented. Root cause: "merged into another todo" treated as done without verification. GATE E ensures every acceptance criterion has code + test evidence before a milestone can close. See `2026-03-05-orchestration-missed-goal-issue-report.md`.

## [1.3.0] - 2026-03-04

### Added
- Structured FILE SCOPE block (own/read/deny) in sub-agent template boundaries
- Scope Registry (`.claude/forge-scopes.json`) — maps worktree paths to file patterns for automated validation
- `hooks/forge-scope-guard.sh` — warn-only PreToolUse hook on Edit/Write (~60 lines bash)
- Scope Guard Installation section — orchestrator copies hook and configures settings during intake
- Agent Spawning Protocol step 2: declare FILE SCOPE and write to scope registry
- Intake steps k-l: create scope registry and install hook

### Changed
- Sub-agent template boundaries now include FILE SCOPE before ALWAYS/NEVER/ASK FIRST
- Milestone template "Files in scope" field uses structured own/read/deny format
- Agent Spawning Protocol renumbered to 8 steps (was 7)
- forge-build-worker agent boundaries updated to reference FILE SCOPE own patterns

### Context
Tier 0 (structured scope declarations) + Tier 1 (warn-only scope guard). Research: `architect/research/agent-mail-coordination.md` + `agent-mail-alternatives.md`. For 2-5 agents, structured decomposition beats locking. Tier 0 makes scope machine-parseable; Tier 1 adds lightweight monitoring. Agent identity derived from worktree cwd — no env var injection needed.

## [1.2.0] - 2026-03-04

### Changed
- Added COMPOUND step 9: "Transition to next milestone immediately" — explicit continuation directive to read TODO.md for next milestone scope after git commit, preventing Codex CLI turn-ending between milestones

### Context
On Codex CLI, the COMPOUND step writes 6+ state files then the model naturally produces a text summary, which ends the turn (no tool calls = turn over). Step 9 ensures the model reads the next milestone scope immediately after committing, keeping the turn alive. Research: `architect/research/codex-turn-lifecycle-fix.md`. General Turn Lifecycle guidance added in forge-codex-multiagent v1.1.0.

## [1.1.0] - 2026-03-03

### Changed
- Added annotated workflow overview with per-phase outputs and GATE markers (A-D)
- Added Step Completion Protocol section explaining why gates exist and what each enforces
- Added GATE A after Intake: milestones + practices + steering templates must exist
- Added GATE B after PLANNING: reviewed plan required before BUILD — "building without a reviewed plan is the #1 cause of rework"
- Added GATE C after REVIEW/SECOND-OPINION: findings must be serialized before IMPROVEMENT — "fresh-context review is the orchestrator's primary quality mechanism"
- Added GATE D after QUALITY GATE: gate must pass before COMPOUND — prevents codifying bad patterns

### Context
Preventive hardening based on forge-research production eval (C+ grade — skipped 4/9 steps). Same skip pattern likely in the orchestrator's milestone loop: jump from BUILD to next milestone, skipping REVIEW (40-60% quality loss), IMPROVEMENT, and COMPOUND (learning propagation). Gates are prompt-level enforcement since skills have no runtime validation.

## [1.0.0] - 2026-03-03

### Added
- Initial release — master orchestrator for milestone-gated autonomous development
- 3-step workflow: intake/orientation, milestone loop, finalization
- Milestone loop: RESEARCH → PLANNING → BUILD → REVIEW → SECOND-OPINION → IMPROVEMENT → QUALITY GATE → COMPOUND
- Complexity-adaptive planning: simple (inline), standard (concise), complex (multi-approach)
- Parallel fan-out review in fresh context: adversarial, performance, test, documentation, brainstorm
- Optional second-opinion phase via other CLIs (graceful degradation)
- Compound learning: CLAUDE.md updates, FORGE-MEMORY.md, SUGGESTIONS.md consolidation
- Human steering: HUMAN-INPUT.md, MISSION-CONTROL.md, SUGGESTIONS.md (bidirectional)
- Compaction survival protocol with CLAUDE.md anchor and continuous state persistence
- Concurrent invocation protection via FORGE-STATUS.md staleness check
- Parallelized serial threads model with file ownership boundaries
- Agent spawning protocol with 7-tag XML template and quality bar scoring
- Merge strategy: dependency order, then completion order, stop on conflict
- Exit conditions: milestone gates, diminishing returns, global circuit breaker
- Reference files: state-templates.md, steering-templates.md, milestone-template.md, claude-md-sections.md, compaction-protocol.md, sub-agent-template.md

### Context
Layer 2 orchestrator skill — sequences forge-research and forge-builder through milestone-gated cycles. References Layer 0 practices (forge-claude-teams or forge-codex-multiagent) and Layer 1 capabilities. Bundles 4 custom agent definitions in agents/ directory.
