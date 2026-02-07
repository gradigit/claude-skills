# Changelog

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
