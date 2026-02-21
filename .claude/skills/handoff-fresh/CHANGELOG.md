# Changelog

## [1.8.0] - 2026-02-21

### Changed
- Root `HANDOFF.md` bridge now explicitly treats "read HANDOFF.md" as bootstrap to switch into bundle handoff immediately
- Validation requirements now enforce bridge bootstrap wording presence

## [1.7.0] - 2026-02-21

### Added
- Token-budgeted session-log continuity artifacts: `session-log-digest.md` and `session-log-chunk.md`
- Configurable token budget arguments for log continuity payload
- High-signal selection rules (decisions, pivots, constraints, blockers) and low-signal exclusions

### Changed
- `handoff-everything.md` now includes session-log budget summary metadata

## [1.6.0] - 2026-02-21

### Added
- Mandatory `claude.md`/`agents.md` shared-context parity contract
- Required `SHARED-ONBOARDING-CONTEXT` marker block in both files
- Validation checks for byte-identical shared block content between both files

### Changed
- Root bridge guidance now explicitly requires full Read Gate before reply, no interim one-file summary, and preflight validator before Workspace Preparation

## [1.5.0] - 2026-02-21

### Added
- Bootstrap/autostart Read Gate rule for prompts that only request reading bundle `handoff.md`
- First-response contract requiring full Read Gate receipt before any interim summary

## [1.4.2] - 2026-02-21

### Changed
- Clarified `--validate-read-gate` as an agent-internal preflight step
- Updated guidance text to avoid implying users must run validator manually

## [1.4.1] - 2026-02-21

### Added
- Executable validator script at `scripts/validate_read_gate.py`
- Script-level PASS/FAIL output and exit codes for Read Gate preflight enforcement

## [1.4.0] - 2026-02-21

### Added
- Explicit `--validate-read-gate` preflight mode for `/handoff-fresh`
- Pass/fail validation rules for `read-receipt.md` checklist completion and non-empty takeaways
- Bundle handoff template instruction to run read-gate validator before coding

## [1.3.0] - 2026-02-21

### Added
- Mandatory Read Gate hard-stop section in bundle `handoff.md`
- Required read receipt checklist format with one-line takeaway per required file
- Required `read-receipt.md` artifact in fresh bundle
- Explicit “do not proceed if unread” rule before workspace prep/coding

## [1.2.0] - 2026-02-21

### Added
- Mandatory Question Gate guidance in bundle `handoff.md` workspace prep
- Explicit ask-question requirement when required information is missing or ambiguous
- Root `HANDOFF.md` bridge instruction to ask questions before coding if prep is blocked

## [1.1.0] - 2026-02-21

### Added
- Default bundle output directory `.handoff-fresh/current/` under project root
- Optional `--archive` mode to snapshot previous bundle into `.handoff-fresh/archive/<timestamp>/`
- Mandatory "Workspace Preparation" section in bundle `handoff.md`
- Root `HANDOFF.md` bridge note pointing fresh agents into bundle handoff path

### Changed
- Fresh-agent onboarding contract now prefers foldered bundles instead of writing all files directly in root

## [1.0.0] - 2026-02-21

### Added
- Initial release of `handoff-fresh`
- Explicit `/handoff-fresh` manual command contract
- Fork-safe onboarding bundle generation in project root
- Required file outputs: `claude.md`, `agents.md`, `todo.md`, `handoff.md`, `context.md`, `reports.md`, `artifacts.md`, `state.md`, `prior-plans.md`
- Mandatory `handoff-everything.md` full raw path/output artifact
- Reference-only safety rule for `prior-plans.md`
