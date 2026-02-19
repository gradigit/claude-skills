# Evaluations for updating-skills

## Scenario 1: Happy path — add feature to existing skill (should-trigger, functional)

**Given** a skill at ~/.claude/skills/my-skill/ with SKILL.md (v1.0.0) and CHANGELOG.md
**When** user says "update my-skill to add Python support"
**Then**
- [ ] Skill activates (updating-skills, not creating-skills)
- [ ] Reads all skill files before proposing changes
- [ ] Classifies as minor version bump (new capability)
- [ ] Makes changes following creating-skills spec (third person, under 500 lines)
- [ ] Bumps frontmatter version to 1.1.0
- [ ] Adds CHANGELOG.md entry with date and Added section
- [ ] Runs audit checks after changes
- [ ] Checks cross-file consistency (version string matches everywhere)

## Scenario 2: Edge case — breaking change (should-trigger, functional)

**Given** a skill at ~/.claude/skills/my-skill/ with v2.3.0 and user requests workflow restructure
**When** user says "modify this skill to completely restructure the workflow"
**Then**
- [ ] Skill activates
- [ ] Classifies as major version bump (breaking change)
- [ ] Bumps to 3.0.0 (not 2.4.0)
- [ ] CHANGELOG entry includes "Changed" or "Removed" section
- [ ] Verifies step count references match across all files

## Scenario 3: Edge case — typo fix (should-trigger, functional)

**Given** a skill with a typo in the description
**When** user says "fix the typo in my skill's description"
**Then**
- [ ] Skill activates
- [ ] Classifies as patch version bump
- [ ] Updates only the affected text
- [ ] Does NOT over-engineer or refactor surrounding code

## Scenario 4: Should-NOT-trigger — create request

**Given** user wants to build a brand new skill
**When** user says "create a new skill for linting markdown"
**Then**
- [ ] updating-skills does NOT activate
- [ ] creating-skills activates instead

## Scenario 5: Should-NOT-trigger — test request

**Given** user wants to test skill evaluations
**When** user says "evaluate my skill's test scenarios"
**Then**
- [ ] updating-skills does NOT activate
- [ ] testing-skills activates instead

## Performance Comparison

### Baseline (without updating-skills)
Ask Claude "update my skill" without the skill loaded. Claude may edit SKILL.md but often forgets CHANGELOG.md, doesn't bump versions consistently, misses cross-file consistency, and doesn't run audits.

### With updating-skills
10-step workflow with mandatory version bump, CHANGELOG update, cross-file consistency check, and audit pass.

### Expected Delta
- CHANGELOG always updated vs often forgotten
- Version bump correctly classified vs arbitrary
- Cross-file consistency checked vs missed
- Post-change audit vs no validation
