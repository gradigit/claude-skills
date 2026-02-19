# Evaluations for creating-skills

## Scenario 1: Happy path — autonomous mode (should-trigger, functional)

**Given** user has a clear idea for a new skill
**When** user says "create a skill that formats git commit messages"
**Then**
- [ ] Skill activates (creating-skills, not updating-skills or auditing-skills)
- [ ] Asks mode preference (autonomous vs guided) via AskUserQuestion
- [ ] If autonomous: infers name, triggers, type from request
- [ ] Generates SKILL.md with valid frontmatter (name, description, metadata.version)
- [ ] Creates EVALUATIONS.md with at least 3 Given/When/Then scenarios
- [ ] Description is third person with trigger keywords
- [ ] Includes a should-NOT-trigger scenario in EVALUATIONS.md

## Scenario 2: Edge case — vague request (should-trigger, functional)

**Given** user provides minimal information
**When** user says "make a new skill for my project"
**Then**
- [ ] Skill activates
- [ ] Asks mode preference
- [ ] If guided: proceeds through interview rounds to clarify purpose
- [ ] If autonomous: makes reasonable assumptions and presents for review
- [ ] Does not generate a skill with vague description like "helps with projects"

## Scenario 3: Should-NOT-trigger — update request

**Given** user wants to modify an existing skill
**When** user says "update my auditing-skills to add a new check"
**Then**
- [ ] creating-skills does NOT activate
- [ ] updating-skills activates instead

## Scenario 4: Should-NOT-trigger — audit request

**Given** user wants to validate a skill
**When** user says "check if my skill follows the spec"
**Then**
- [ ] creating-skills does NOT activate
- [ ] auditing-skills activates instead

## Performance Comparison

### Baseline (without creating-skills)
Ask Claude "create a skill" without the skill loaded. Claude may produce a SKILL.md but likely with inconsistent frontmatter, missing evaluations, no interview process, and potentially first-person descriptions.

### With creating-skills
Structured interview or autonomous mode, evaluation-first development, spec-compliant frontmatter, Given/When/Then evaluations with should-NOT-trigger.

### Expected Delta
- Consistent frontmatter format vs ad-hoc
- Evaluations defined before skill body vs no evaluations
- Negative triggers included vs omitted
- Mode selection (autonomous/guided) vs one-size-fits-all
