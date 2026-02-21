# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.4.0] - 2026-02-21

### Added
- Mandatory HANDOFF bootstrap-read rule so "read HANDOFF.md" prompts auto-expand to full First Steps reading
- First-response contract in templates: no interim one-file summary; require per-file read receipt

### Changed
- Validation checklist now enforces presence of bootstrap-read rule in generated HANDOFF.md

## [2.3.0] - 2026-02-21

### Added
- AGENTS.md-aware prerequisite handling (create/minimize parity gaps when missing)
- Validation check for CLAUDE.md/AGENTS.md shared-context contradictions

### Changed
- HANDOFF first-step guidance now includes AGENTS.md alongside CLAUDE.md for cross-agent continuity

## [2.2.0] - 2026-02-21

### Added
- Explicit manual command contract centered on `/handoff` (no implicit/side-channel invocation)
- Clear routing rule: use `/handoff-fresh` for fork-safe, brand-new-agent onboarding bundles

### Changed
- Clarified `/handoff` scope as canonical single-file continuity (`HANDOFF.md`) while fresh multi-file bundles live in `handoff-fresh`

## [2.1.0] - 2026-02-07

### Added
- "Failed Approaches" section in HANDOFF.md template — documents what was tried and why it didn't work, preventing next session from repeating dead ends
- Quick Mode — lightweight handoff path for small tasks (bug fix, config change), skips Steps 2-4, uses minimal template
- Quick handoff template in templates.md
- "quick handoff" trigger in metadata
- Failed Approaches example in the concrete walkthrough (HS256→RS256, JWT→Redis)

## [2.0.0] - 2026-02-07

### Changed
- **BREAKING**: Renamed skill from `handing-off` to `handoff` (directory and name field)
- Fixed frontmatter to use proper YAML `---` delimiters (was `***` / `----------------`)
- Restructured workflow from 5 steps to 6 steps (added prerequisites and validation)
- Converted verbose prose to compact tables throughout (Step 1, Step 3, Step 4)
- Made example significantly more concrete with realistic project details, actual file paths, commit hashes, and step-by-step walkthrough
- Enriched Self-Evolution section with CHANGELOG reference and version-specific learnings

### Added
- Step 2: Handle Prerequisites — edge case handling table (no git, no CLAUDE.md, merge conflicts, no-commit preference, dirty submodules)
- Step 6: Validate and Confirm — verification checklist before outputting confirmation
- Common Pitfalls table with 7 pitfalls and prevention strategies
- Git operations reference table with explicit rules
- Extracted templates to `templates.md` for progressive disclosure (standard, confirmation, emergency)
- Metadata fields: author, updated, tags, triggers array
- Parallel execution directive in Step 1

## [1.0.0] - 2026-02-05

### Added
- Initial release
- Comprehensive handoff workflow: assess → commit → update docs → generate HANDOFF.md → confirm
- Branching instructions pattern — HANDOFF.md tells new sessions exactly what files to read
- Emergency handoff mode for interrupted sessions
- Integration with existing CLAUDE.md and TODO.md patterns
- First Steps section for single-command context restoration ("Read HANDOFF.md and continue")
- Reference files table for quick navigation
- Self-evolution section for continuous improvement
