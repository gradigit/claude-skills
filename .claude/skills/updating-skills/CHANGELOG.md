# Changelog

All notable changes to this skill are documented here.

## [2.0.0] - 2026-02-07

### Added
- **Evaluation-First Updates section** — decision table for when to update EVALUATIONS.md
- **Evaluations audit checks** — EVALUATIONS.md presence, scenario coverage, should-NOT-trigger validity
- Cross-reference to testing-skills for running evaluations
- Negative trigger in description ("Do NOT use when creating, auditing, or testing")
- `category: meta-tooling` in metadata
- EVALUATIONS.md in Reading Current State file list

### Changed
- **BREAKING**: Workflow expanded from 10 to 12 steps — added "Run current evaluations (baseline)" and "Update EVALUATIONS.md"
- Example updated to reflect 12-step workflow
- Spec references updated to creating-skills v4.0.0 and auditing-skills v2.0.0
- Self-evolution version updated to 2.0.0

## [1.0.0] - 2026-01-29

### Added
- Initial release
- 10-step update workflow (read → change → version → changelog → audit → push)
- Semver classification guide (major/minor/patch)
- Cross-file consistency checklist (version, step counts, references, hardcoded values)
- Common pitfalls table from real screening-github-cloud update sessions
- References to creating-skills and auditing-skills
