# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.1.1] - 2026-06-20

### Fixed
- **Verify-honesty at the point of claim** (after-eval regression): note-sourced
  results (test counts, build/health) must be labeled `(per session notes — unverified)`
  in prose ("What Was Done" / "Current State"), not only inside the Verify Block — the
  producer-side counterpart to `/pickup`'s anti-fabrication rule.
- Verify Block commands must validate the *full* claim: `git branch --show-current` for
  branch-name claims (not `git rev-parse --short HEAD`); in-dir-unrunnable checks marked
  `unverifiable here`.

## [3.1.0] - 2026-06-20

### Added
- **Resume-artifact precedence & cleanup** (Step 5): when competing artifacts coexist
  (`FORGE-HANDOFF.*`, `FORGE-STATUS.*`, `MERGE-READINESS-*`, stale `.handoff-fresh/`,
  dated `HANDOFF-*` stubs), the generated `HANDOFF.md` emits an
  `> AUTHORITATIVE — supersedes: …` header naming the stale ones, and the confirmation
  recommends archiving them (no auto-delete).
- Validation checklist item + Common Pitfalls rows for precedence header and
  "never write a new dated stub" (write the one canonical `HANDOFF.md`).

### Why
Closes gap NEW-A (artifact sprawl / no precedence rule) and part of #6 (divergent
artifacts), both confirmed in the session-log audit and the P3 fixture eval where
neither pre-v3 nor v3 flagged or superseded the dead `FORGE-*` files.

## [3.0.0] - 2026-06-20

### Added
- Line-1 schema marker `<!-- HANDOFF-SCHEMA v3.0.0 producer=handoff -->` so the new `/pickup` consumer can detect schema/producer and distinguish skill-generated from hand-written handoffs
- Mandatory `## Last Exchange (Verbatim)` section — last user prompt + last assistant response (+ load-bearing earlier directives), quoted character-for-character as the resume anchor
- Step 0: capture the verbatim last exchange first, before any compaction can discard it (manual, no auto-hooks); compaction-boundary handling guidance
- Mandatory machine-runnable `## Verify Block` (`claim | check-command | expected`) that `/pickup` executes on resume
- Step 6 content-completeness assertions (verbatim exchange, verify block, what's-next, blockers, current state) and a full-overwrite finalize rule

### Changed
- Bootstrap Read Rule now points at `/pickup` as the preferred consumer; the embedded rule is a hint, not the enforcement mechanism (the guarantee lives in `/pickup`)
- Worked example updated to schema v3

### Breaking
- New mandatory sections + line-1 marker change the HANDOFF.md schema. Old/hand-written handoffs lack the marker; `/pickup` still consumes them but flags a weak contract. Re-run `/handoff` to regenerate at v3.

## [2.5.0] - 2026-02-22

### Added
- `--ignore-mode <local|shared|off>` argument for explicit handoff artifact ignore policy
- Default local ignore behavior to keep `HANDOFF.md` and `.handoff-fresh/` out of noisy untracked status

### Changed
- Validation checklist now requires ignore-entry presence when ignore mode is enabled

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
