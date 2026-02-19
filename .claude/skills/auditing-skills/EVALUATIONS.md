# Evaluations for auditing-skills

## Scenario 1: Happy path — skill with issues (should-trigger, functional)

**Given** a skill at ~/.claude/skills/my-skill/ with SKILL.md containing an uppercase name (`name: My-Skill`) and first-person description ("I help users")
**When** user says "audit the my-skill skill"
**Then**
- [ ] Skill activates (auditing-skills, not creating-skills or testing-skills)
- [ ] Reads SKILL.md and any referenced files
- [ ] Identifies "uppercase name" as Critical
- [ ] Identifies "first person in description" as Warning
- [ ] Generates audit report with Summary table (Critical/Warning/Suggestion counts)
- [ ] Overall grade is FAIL (1+ critical issues)
- [ ] Offers to fix the critical issues

## Scenario 2: Edge case — clean skill (should-trigger, functional)

**Given** a well-formed skill at ~/.claude/skills/clean-skill/ that passes all checks with EVALUATIONS.md present
**When** user says "validate this skill"
**Then**
- [ ] Skill activates
- [ ] Runs full checklist (frontmatter, content, quality)
- [ ] Reports PASS with 0 critical, 0-2 warnings
- [ ] Does not invent issues that don't exist

## Scenario 3: Edge case — missing EVALUATIONS.md (should-trigger, functional)

**Given** a skill at ~/.claude/skills/no-evals/ with valid SKILL.md but no EVALUATIONS.md
**When** user says "check this skill"
**Then**
- [ ] Skill activates
- [ ] Flags missing EVALUATIONS.md as Warning
- [ ] Reports scoring impact: PASS requires EVALUATIONS.md present
- [ ] Overall grade is NEEDS WORK (missing evaluations)

## Scenario 4: Should-NOT-trigger — create request

**Given** user wants to build a new skill from scratch
**When** user says "create a skill for processing images"
**Then**
- [ ] auditing-skills does NOT activate
- [ ] creating-skills activates instead

## Scenario 5: Should-NOT-trigger — test request

**Given** user wants to run evaluation scenarios
**When** user says "run the tests for my skill"
**Then**
- [ ] auditing-skills does NOT activate
- [ ] testing-skills activates instead

## Performance Comparison

### Baseline (without auditing-skills)
Ask Claude "audit my skill" without the skill loaded. Claude may check some things but inconsistently, without severity levels, checklist coverage, or structured report format.

### With auditing-skills
Systematic checklist from checklist.md, consistent severity levels, structured report, EVALUATIONS.md presence check, offer to fix critical issues.

### Expected Delta
- Complete checklist coverage vs ad-hoc checks
- Consistent severity classification vs mixed
- Structured report format vs freeform
- EVALUATIONS.md presence validated vs not checked
