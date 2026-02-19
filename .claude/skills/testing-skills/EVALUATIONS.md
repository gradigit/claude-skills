# Evaluations for testing-skills

## Scenario 1: Happy path — valid EVALUATIONS.md (should-trigger, functional)

**Given** a skill directory at ~/.claude/skills/handoff/ with a valid EVALUATIONS.md containing 3 Given/When/Then scenarios
**When** user says "test the handoff skill"
**Then**
- [ ] Skill activates (testing-skills, not auditing-skills or updating-skills)
- [ ] Reads the target skill's EVALUATIONS.md
- [ ] Classifies scenarios by tier (triggering, functional, performance)
- [ ] Runs at least one scenario
- [ ] Generates a diagnostic report with Summary table and per-scenario results
- [ ] Does NOT automatically modify the skill under test

## Scenario 2: Edge case — missing EVALUATIONS.md (should-trigger, functional)

**Given** a skill directory at ~/.claude/skills/my-skill/ with SKILL.md but no EVALUATIONS.md
**When** user says "run evaluations on my-skill"
**Then**
- [ ] Skill activates
- [ ] Reports "No EVALUATIONS.md found"
- [ ] Suggests creating EVALUATIONS.md using creating-skills spec
- [ ] Does NOT attempt to test without scenarios
- [ ] Does NOT create EVALUATIONS.md itself

## Scenario 3: Should-NOT-trigger — audit request

**Given** user wants to validate skill spec compliance
**When** user says "audit my skill for best practices"
**Then**
- [ ] testing-skills does NOT activate
- [ ] auditing-skills activates instead (spec compliance is auditing, not testing)

## Scenario 4: Should-NOT-trigger — create request

**Given** user wants to create a new skill
**When** user says "create a skill for formatting code"
**Then**
- [ ] testing-skills does NOT activate
- [ ] creating-skills activates instead

## Performance Comparison

### Baseline (without testing-skills)
Ask Claude "test my skill" without the skill loaded. Claude will likely read files and provide ad-hoc feedback without structured tiers, report format, or hybrid grading.

### With testing-skills
Structured three-tier evaluation, hybrid grading, diagnostic report template, and clear separation between testing and repair.

### Expected Delta
- Structured report vs freeform feedback
- Consistent tier classification vs ad-hoc checking
- Reproducible grading methodology vs subjective assessment
