# Changelog

## [4.0.0] - 2026-02-07

### Added
- **Negative trigger guidance**: Description must include "Do NOT use this skill when..." pattern
- **Activation Reliability section**: ~20% baseline, hooks for 84%+, skills/commands equivalence
- **Token Budget section**: SLASH_COMMAND_TOOL_CHAR_BUDGET guidance, context window competition
- **Expanded frontmatter template**: argument-hint, user-invocable, disable-model-invocation, model, context, agent, hooks
- **`name` field note**: Explicitly documented as optional (defaults to directory name)
- `category` field in metadata
- Agent-as-a-Judge evaluation methodology in reference.md (0.3% disagreement rate)
- Success criteria framework table in reference.md (quantitative + qualitative)
- Advanced frontmatter fields reference table in reference.md
- Nested directory discovery for monorepos in reference.md

### Changed
- **BREAKING**: Evaluation format changed from Input/Expected/Criteria to **Given/When/Then**
- **BREAKING**: should-NOT-trigger scenario now required in evaluations
- Validation checklist updated: EVALUATIONS.md presence required, 3+ scenarios, should-NOT-trigger
- Interview JSON examples moved from SKILL.md to reference.md (line budget recovery)
- Interview section condensed to summary table with reference.md link

## [3.1.0] - 2026-02-05

### Added
- **Mode selection** as first step: Autonomous vs Guided interview
  - Autonomous mode: Claude infers everything from request, no questions asked
  - Guided mode: Full 4-round interview process
- **Autonomous inference table**: How to extract name, triggers, type, freedom, complexity from user request
- Best-for guidance for each mode

### Changed
- Workflow restructured: Mode selection is now Step 1
- Interview rounds marked as "(Guided Only)"
- Description updated to reflect dual-mode capability

## [3.0.0] - 2026-02-05

### Added
- **Adaptive interview workflow** using AskUserQuestion tool
  - 4-round interview process with JSON schemas
  - Adapts questions based on previous answers
  - Gathers skill type, dependencies, freedom level, examples, guardrails
- **Evaluation-first methodology** (Anthropic's recommended approach)
  - Define 3 test scenarios BEFORE writing skill
  - EVALUATIONS.md template for future testing
  - Testing loop: run → fail → add minimal instructions → repeat
- **Model-specific authoring guidance**
  - Detailed table for Haiku/Sonnet/Opus differences
  - Strategy for multi-model targeting
  - Example showing same skill at different detail levels
- **MCP tool references** in main SKILL.md
  - `ServerName:tool_name` format
  - Integration with compatibility field
- **Optional frontmatter fields** properly documented
  - `license` (for published skills)
  - `compatibility` (environment requirements)
  - `allowed-tools` (pre-approved tools with syntax)

### Changed
- Workflow restructured: 7 steps (was 5)
- `license` downgraded from implied-required to optional
- Frontmatter template simplified (optional fields shown separately)
- Anti-patterns updated: added "Writing before evaluations"
- Self-evolution section updated with new trigger

### Removed
- `license` from required frontmatter template
- Redundant validation checklist items (consolidated)

## [2.1.0] - 2026-01-15

### Added
- XML tag restrictions for name/description fields
- Directory name matching requirement
- MCP tool references section (`ServerName:tool_name` format)
- Visual analysis pattern for image-based inputs
- `assets/` directory to progressive disclosure structure
- "too many options" anti-pattern
- TOC requirement for reference files >100 lines

### Changed
- Renamed `skill-creator` → `creating-skills` (gerund convention)

## [2.0.0] - 2025-12-01

### Added
- `license` field
- Progressive disclosure patterns
- Degrees of freedom guidance
- Anti-patterns section
- Self-evolution pattern

### Changed
- Moved `version` to `metadata.version`

## [1.0.0] - 2025-10-15

Initial version with basic template.
