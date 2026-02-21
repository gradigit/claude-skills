# Changelog

## [2.6.0] - 2026-02-21

### Added
- AGENTS.md as an owned doc target for drift fixing and session-learning sync
- CLAUDE.md/AGENTS.md shared-context contradiction checks in cross-file consistency step

### Changed
- Change-to-doc mapping now updates both CLAUDE.md and AGENTS.md for shared project command/context drift

## [2.5.0] - 2026-02-21

### Added
- Watched-file checks for handoff-fresh continuity artifacts: `.handoff-fresh/current/session-log-digest.md` and `.handoff-fresh/current/session-log-chunk.md`

## [2.4.0] - 2026-02-21

### Added
- Cross-file contradiction detection for `.handoff-fresh/current/claude.md` vs `.handoff-fresh/current/agents.md` shared-context parity drift

## [2.3.0] - 2026-02-21

### Added
- Added `.handoff-fresh/current/read-receipt.md` to watched-file checks for handoff-fresh bundle consistency

## [2.2.0] - 2026-02-21

### Changed
- Updated handoff-fresh bundle integration to foldered layout at `.handoff-fresh/current/`
- Updated watched-file validation and staleness checks to use foldered bundle paths
- Updated summary output examples to report bundle directory path

## [2.1.0] - 2026-02-21

### Added
- Explicit `/sync-docs` trigger in command contract language
- `--refresh-fresh-bundle` flag to regenerate handoff-fresh onboarding bundle after sync via `/handoff-fresh --no-sync`
- Watched-file checks for handoff-fresh bundle outputs: `claude.md`, `agents.md`, `todo.md`, `handoff.md`, `context.md`, `reports.md`, `artifacts.md`, `state.md`, `prior-plans.md`, `handoff-everything.md`
- Staleness alert for fresh bundle artifacts when source docs/state are newer

## [2.0.0] - 2026-02-07

### Added
- Session learnings capture (merged from revise-claude-md): reflects on session, proposes CLAUDE.md additions with approval
- Cross-file consistency checking for watched files (TODO.md, HANDOFF.md, architect/*.md)
- Code element reference tracking: extracts backtick identifiers and file paths, cross-references against codebase
- Staleness alerts for files owned by other skills (e.g., "HANDOFF.md is 23 commits old")
- Cross-file contradiction detection (phase mismatches, deleted file references)
- `--quick` mode: drift fix only, skips session learnings and cross-file checks
- File ownership model: owned (can edit) vs watched (read-only, flag only)
- Cumulative git history detection via manifest `last_synced` timestamp
- Expanded change-to-doc mapping: Docker files, barrel files, Go/Rust configs

### Changed
- Identity shift: from "documentation syncer" to "project state drift detector"
- Git change detection now uses `git log --since` for cumulative changes instead of single-commit comparison
- Auto-discovery expanded to include watched state files (TODO.md, HANDOFF.md, architect/*.md)
- Summary output restructured into sections: Drift Fixed, Session Learnings, Cross-File Issues, Flagged for Review

### Removed
- Template creation for missing docs (scaffolding ≠ syncing) — templates.md deleted
- "Creating Missing Docs" section and related workflow

## [1.0.0] - 2026-01-29

### Added
- Initial version
- Git diff detection for identifying code changes
- Timestamp fallback for non-git projects
- Auto-discovery of documentation files (CLAUDE.md, README.md, ARCHITECTURE.md, docs/)
- Hybrid manifest support (auto-discover + .doc-manifest.yaml override)
- Fix obvious staleness: broken paths, stale commands, missing key files
- Flag ambiguous staleness: deleted code, major refactors, semantic changes
- Create missing standard docs from templates (CLAUDE.md, README.md, ARCHITECTURE.md)
- --dry-run mode for previewing changes without applying
- Hybrid execution: scan in-context, edit via Task agent
- Medium-detail summary output (file + section changes)
- Integration with managing-doc-manifest skill
