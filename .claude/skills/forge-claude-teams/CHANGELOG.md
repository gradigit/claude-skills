# Changelog

All notable changes to the forge-claude-teams skill.

## [1.1.0] - 2026-03-04

### Changed
- File Ownership Enforcement uses structured FILE SCOPE format (own/read/deny) instead of freeform declarations
- Context Handoff Template `<scope>` tag updated to structured format with deny list
- Worktree Setup fallback boundaries example uses FILE SCOPE block
- Added note linking structured format to forge-orchestrator scope registry and forge-scope-guard hook

### Context
Part of Tier 0 (structured file scope declarations) for the forge pipeline. Machine-parseable scope format enables automated validation via forge-scope-guard PreToolUse hook (Tier 1). Research: `architect/research/agent-mail-alternatives.md`.

## [1.0.0] - 2026-03-03

### Added
- Initial release — Claude Code multi-agent practices guide
- Agent tool section: subagent types, model selection, context handoff template, parallelism model
- Teams section: lifecycle, task ownership, communication, idle handling, shutdown protocol
- Conflict prevention pyramid: read-only shared, build worktrees, never same-file
- Error recovery: fresh agent on failure, merge conflict protocol, quality gate retry
- Progress observability: FORGE-STATUS.md, progress narration, TODO.md updates

### Context
Layer 0 practices skill — reference document for forge-research, forge-builder, and forge-orchestrator. Auto-injected or explicitly read by Layer 1/2 skills for platform-specific multi-agent guidance.
