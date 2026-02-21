# Changelog

## [1.3.0] - 2026-02-21

### Changed
- Step 2 expanded from CLAUDE-only quality pass to instruction-doc quality flow (CLAUDE.md improvements + AGENTS.md parity mirror)
- Wrap summary now reports CLAUDE/AGENTS parity outcomes

## [1.2.0] - 2026-02-21

### Changed
- Updated `--with-fresh` behavior docs to target foldered handoff-fresh bundle path `.handoff-fresh/current/`

## [1.1.0] - 2026-02-21

### Added
- Explicit `/wrap` trigger in frontmatter
- Manual command contract (no implicit/side-channel invocation)
- `--with-fresh` flag to run `/handoff-fresh --no-sync` after standard wrap flow
- Optional fourth step for fresh-agent onboarding bundle generation

## [1.0.0] - 2026-02-07

### Added
- Initial version
- Chains syncing-docs → claude-md-improver → handoff
- `--no-handoff` flag for mid-session use
- `--quick` flag passed through to syncing-docs
- Compact wrap-complete summary
