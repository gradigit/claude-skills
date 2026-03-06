# Changelog

All notable changes to the forge-builder skill.

## [1.2.0] - 2026-03-04

### Changed
- Conflict Prevention section references structured FILE SCOPE format (own/read/deny)
- "Exclusive file ownership" language replaced with "FILE SCOPE declaration"

### Context
Aligns forge-builder with Tier 0 structured scope declarations from forge-orchestrator 1.3.0.

## [1.1.0] - 2026-03-03

### Changed
- Added GATE A and GATE B checkpoints to prevent skipping pre-build steps
- Added Step Completion Protocol section explaining gate enforcement
- Workflow checklist now shows per-step outputs and gate markers
- Step 1: added "MUST extract and output" language
- Step 2: marked MANDATORY with explicit "read the file" requirement and GATE A checkpoint
- Step 3: marked MANDATORY with "must have plan before writing code" requirement and GATE B checkpoint

### Context
Preventive hardening based on forge-research production eval. forge-research skipped 4 of 9 steps on first run — same pattern likely in forge-builder (skip Steps 1-3, jump to coding). Gates are prompt-level enforcement since skills have no runtime validation.

## [1.0.0] - 2026-03-03

### Added
- Initial release — autonomous building with self-review, self-improvement, and quality gates
- Entry point: orchestrated mode (skip auto-detect) and standalone mode (classify directive vs inquiry)
- 6-step workflow: parse, platform detect, plan, build phases, feature detection, final validation
- Build phase loop: implement, self-review, test, self-improvement scan, improve, quality gate
- Quality gate criteria: tests, lint, self-review, requirements match, no regressions
- Gate failure protocol: fix, re-gate (max 2 retries), escalate to user
- New feature detection with improvement vs new feature decision table
- SUGGESTIONS.md bidirectional format with status lifecycle
- Conflict prevention: exclusive file ownership, DEFERRED-CHANGES.md for out-of-scope changes
- Long-running session support: single-feature focus, git checkpointing, compaction resilience
- Reference files: suggestions-template.md, quality-gates.md, long-running.md

### Context
Layer 1 capability skill — usable standalone or orchestrated by forge-orchestrator. References Layer 0 practices (forge-claude-teams or forge-codex-multiagent) for platform-specific multi-agent patterns.
