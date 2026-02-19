# Changelog

## [2.0.0] - 2026-02-07

### Added
- **Evaluation Coverage section** in SKILL.md — checks EVALUATIONS.md presence, scenario count, format, should-NOT-trigger
- **Evaluations section** in checklist.md — EVALUATIONS.md present, Given/When/Then format, should-NOT-trigger
- **Description Activation checks** in checklist.md — negative triggers, trigger disambiguation
- Negative trigger to description ("Do NOT use when creating, updating, or testing")
- `category: meta-tooling` in metadata
- Anti-patterns: missing EVALUATIONS.md (Warning), no negative triggers (Warning)
- Cross-reference to testing-skills for deep validation

### Changed
- **BREAKING**: Scoring now factors EVALUATIONS.md presence — PASS requires it present
- NEEDS WORK now includes missing EVALUATIONS.md as trigger

## v1.0.0

Initial release with:
- Frontmatter validation (name, description, license, version)
- Content structure checks (workflow, examples, line count)
- Anti-pattern detection
- Severity levels (critical/warning/suggestion)
- Audit report format
