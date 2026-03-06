# Changelog

All notable changes to the forge-codex-multiagent skill.

## [1.1.0] - 2026-03-04

### Changed
- Added Section 9 "Turn Lifecycle" — documents Codex CLI's deterministic turn-ending mechanism (`needs_follow_up` only true on tool calls) and provides rules for continuous execution
- Revised Section 7 "Progress Narration" — progress notes must now be paired with tool calls; standalone text-only progress notes end Codex turns
- Added "Where This Matters Most" subsection identifying forge-orchestrator COMPOUND step, forge-builder phase transitions, and forge-research synthesis as key risk points

### Context
Codex CLI ends a turn when the model produces a text-only response (no tool calls). This is deterministic in `codex-rs/core/src/codex.rs` — `needs_follow_up` is only set to `true` when tool calls are present. The previous Progress Narration guidance (emit standalone text notes) directly triggered this mechanism. Research: `architect/research/codex-turn-lifecycle-fix.md`. GitHub issue: openai/codex#7900.

## [1.0.0] - 2026-03-03

### Added
- Initial release — Codex CLI multi-agent practices guide
- Core API section: spawn_agent, send_input, wait, close_agent, fork_context
- Batch processing: spawn_agents_on_csv, max_threads configuration
- Conflict prevention: file ownership scoping, fork_context for exploration, no worktree equivalent
- Session log analysis patterns: ownership scoping, short focused sessions, fan-out over pipeline
- Error recovery: close + fresh spawn, timeout handling
- Progress observability: TODO.md updates, FORGE-STATUS.md orchestrator guidance, progress narration
- Parallelism model: fan-out with independent tasks, comparison with Claude Code's parallelized serial threads
- Anti-patterns table: 10 common multi-agent mistakes with fixes
- Custom agent roles: Section 1b documenting `[agents.<name>]` config.toml syntax and forge role definitions

### Context
Layer 0 practices skill — parallel to forge-claude-teams for Codex CLI. Reference document for forge-research, forge-builder, and forge-orchestrator when running on Codex.
