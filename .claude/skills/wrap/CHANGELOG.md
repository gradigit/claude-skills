# Changelog

## [1.5.0] - 2026-06-20

### Added
- "Choosing the artifact shape" guidance (Step 4): when to use `--with-fresh` (the
  bundle) vs the default single canonical `HANDOFF.md`, so the shape is a deliberate
  choice rather than an accident of which flag was typed.
- Final summary now states the artifact shape produced and that `/pickup` consumes it;
  a coexisting older bundle is explicitly marked historical.

### Why
Closes gap NEW-B (producer shape depends on which command ran) surfaced by the session
audit and the P2 fixture probe.

## [1.4.0] - 2026-06-20

### Added
- Step 0: capture the verbatim last exchange first, before sync (so a compaction during the later steps cannot lose it)
- Documented the wrap↔pickup producer→consumer contract pair (`/wrap` closes a session, `/pickup` opens the next)

### Changed
- Step 3 now notes the handoff v3.0.0 mandatory `## Last Exchange (Verbatim)` + `## Verify Block` + schema marker that make the handoff consumable by `/pickup`

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
