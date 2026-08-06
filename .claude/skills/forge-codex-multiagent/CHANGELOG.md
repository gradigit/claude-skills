# Changelog

All notable changes to the forge-codex-multiagent skill.

## [1.2.0] - 2026-06-21

### Added
- §1c "Codex Role Selection — prompt-templates": forge-* roles can't be spawned by name on Codex (#15250, 0/98 runs), so map each to a built-in `agent_type` (explorer/worker) with its quality bar inlined; mandate programmatic 7-tag injection.
- §6 "Rate-Limit (429) Resilience": 429 was the #1 real failure (1072×, ~46% blind re-spawns) — backoff+jitter, spawns-per-minute budget, pause-and-drain, task-signature dedup cache; a 429 is transient (not counted to retries).

### Fixed
- `wait()` → `wait_agent()` (real binary tool) in body, decision table, and quick-ref; Recovery Protocol example uses `agent_type=`/`message=`.

## [1.1.1] - 2026-06-20

### Fixed
- Corrected `forge-build-worker` sandbox value in the agent-roles table from the invalid `full-access` to `danger-full-access` (current Codex rejects `full-access` at load time; valid values are `read-only` / `workspace-write` / `danger-full-access`)
- Corrected the `spawn_agent` example and quick-reference to the actual tool parameters (`agent_type`, `message`, `model`, `fork_context`) — earlier drafts showed `name=`/`instructions=`, which the tool does not accept (verified against the 0.140.x binary and session-log calls)
- Removed a broken evidence pointer to `architect/research/codex-turn-lifecycle-fix.md` (that path was untracked from the public repo)

### Changed
- Section 1b now documents per-file `~/.codex/agents/*.toml` as the primary custom-role mechanism and demotes inline `[agents.<name>]` config.toml to legacy/alternate, with the known config-loading caveats (openai/codex#14579, #15250)
- Added a known-limitation note that `spawn_agent` may not select per-file custom roles by name in tool-backed sessions (session logs show only built-in `agent_type` values were used)
- Reframed `max_threads` 3/7 as forge recommendations rather than Codex limits (Codex's own default is 6 with no hard cap); reconciled the inconsistent example/default values

### Context
Triggered by an audit of the user's Codex sessions (CLI moved 0.128 → 0.137 → 0.140) and a ground-truth check against the live 0.140.x binary. The core multi-agent API (`spawn_agent`, `fork_context`, `send_input`, `wait_agent`, `close_agent`, `spawn_agents_on_csv`) is intact; this release corrects config/doc drift only.

## [1.1.0] - 2026-03-04

### Changed
- Added Section 9 "Turn Lifecycle" — documents Codex CLI's deterministic turn-ending mechanism (`needs_follow_up` only true on tool calls) and provides rules for continuous execution
- Revised Section 7 "Progress Narration" — progress notes must now be paired with tool calls; standalone text-only progress notes end Codex turns
- Added "Where This Matters Most" subsection identifying forge-orchestrator COMPOUND step, forge-builder phase transitions, and forge-research synthesis as key risk points

### Context
Codex CLI ends a turn when the model produces a text-only response (no tool calls). This is deterministic in `codex-rs/core/src/codex.rs` — `needs_follow_up` is only set to `true` when tool calls are present. The previous Progress Narration guidance (emit standalone text notes) directly triggered this mechanism. GitHub issue: openai/codex#7900.

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
