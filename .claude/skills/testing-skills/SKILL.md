---
name: testing-skills
description: Tests Agent Skills using three-tier evaluation (triggering, functional, performance). Reads EVALUATIONS.md, runs scenarios via CLI, and produces diagnostic reports. Activates when user asks to "test skill", "run evaluations", "evaluate skill", or mentions skill testing. Do NOT use when creating, updating, or auditing skills.
license: MIT
metadata:
  version: "1.0.0"
  author: gradigit
  category: meta-tooling
  tags:
    - skills
    - meta
    - testing
    - evaluation
  triggers:
    - "test skill"
    - "run evaluations"
    - "evaluate skill"
    - "test evaluations"
---

# Testing Skills

Tests Agent Skills using three-tier evaluation: triggering, functional, and performance. Reads EVALUATIONS.md, runs scenarios, and produces diagnostic reports.

## Workflow

```
- [ ] 1. Identify target skill and read EVALUATIONS.md
- [ ] 2. Classify tests by tier (triggering / functional / performance)
- [ ] 3. Run triggering tests
- [ ] 4. Run functional tests
- [ ] 5. Run performance tests (if defined)
- [ ] 6. Grade results (hybrid: code-based + Agent-as-a-Judge)
- [ ] 7. Generate diagnostic report
- [ ] 8. Present findings (diagnostic only — no auto-repair)
```

## Step 1: Read EVALUATIONS.md

Locate and read the target skill's EVALUATIONS.md:

```
~/.claude/skills/{skill-name}/EVALUATIONS.md
```

If EVALUATIONS.md is missing:
- Report "No EVALUATIONS.md found — cannot test"
- Suggest creating one using creating-skills spec (Given/When/Then format)
- Stop — do not proceed without evaluation scenarios

## Step 2: Classify Tests

Each scenario in EVALUATIONS.md maps to a tier:

| Tier | Purpose | Identifies |
|------|---------|-----------|
| **Triggering** | Does the skill activate on the right prompts? | should-trigger + should-NOT-trigger scenarios |
| **Functional** | Does the skill produce correct output? | Happy path, edge case, error handling |
| **Performance** | Does the skill outperform baseline Claude? | Quality delta vs no-skill baseline |

Classify by scenario tags or naming convention:
- `should-trigger` / `should-NOT-trigger` → Triggering
- `happy path` / `edge case` / `error` → Functional
- `baseline comparison` / `performance` → Performance

## Step 3: Run Triggering Tests

For each triggering scenario:

1. Invoke Claude with the test prompt via CLI:
   ```bash
   claude -p "test prompt here" --output-format json
   ```
2. Check whether the target skill was loaded into context
3. For should-trigger: verify skill activated
4. For should-NOT-trigger: verify skill did NOT activate

### Interpreting Results

| Scenario Type | Skill Activated | Result |
|--------------|----------------|--------|
| should-trigger | Yes | PASS |
| should-trigger | No | FAIL — skill not activating on expected trigger |
| should-NOT-trigger | No | PASS |
| should-NOT-trigger | Yes | FAIL — false positive activation |

## Step 4: Run Functional Tests

For each functional scenario:

1. Run the skill on the test input
2. Check each criterion in the **Then** block
3. Use the appropriate grading method per criterion (see Step 6)

### CLI Invocation

```bash
# Single-turn test
claude -p "test prompt" --output-format json

# Multi-turn test (session continuation)
claude -p "first message" --output-format json
# Then continue in the same session
```

Use `context: fork` for isolated execution when testing skills that modify files.

## Step 5: Run Performance Tests

**Only if defined in EVALUATIONS.md.** Most skills skip this tier.

1. Run the task WITHOUT the skill (baseline)
2. Run the task WITH the skill
3. Compare outputs on defined criteria
4. Record the delta

## Step 6: Grade Results

Use hybrid grading — deterministic checks where possible, Agent-as-a-Judge for quality.

| Criterion Type | Grading Method |
|---------------|---------------|
| File exists at path | Code check |
| Output contains required string | Code check |
| Frontmatter has field X | Code check (parse YAML) |
| Output follows template | Code for structure, Agent for content |
| Quality of generated content | Agent-as-a-Judge |
| Correct tool selection | Agent-as-a-Judge |

### Agent-as-a-Judge Protocol

When using Agent-as-a-Judge:

1. Feed the skill's output to a separate evaluation prompt
2. Provide the rubric from EVALUATIONS.md as context
3. Ask for pass/fail per criterion with brief justification
4. Record the judge's assessment

See [methodology.md](methodology.md) for detailed grading protocol.

## Step 7: Generate Report

```markdown
# Test Report: {skill-name}

**Date**: {YYYY-MM-DD}
**Version**: {skill version}
**Scenarios**: {total} ({pass} passed, {fail} failed, {skip} skipped)

## Summary

| Tier | Pass | Fail | Skip |
|------|------|------|------|
| Triggering | X | Y | Z |
| Functional | X | Y | Z |
| Performance | X | Y | Z |

## Results

### Triggering
| Scenario | Type | Result | Notes |
|----------|------|--------|-------|
| {name} | should-trigger | PASS/FAIL | {details} |

### Functional
| Scenario | Result | Criteria Met | Notes |
|----------|--------|-------------|-------|
| {name} | PASS/FAIL | 3/4 | {details} |

### Performance (if applicable)
| Metric | Baseline | With Skill | Delta |
|--------|----------|-----------|-------|
| {metric} | {score} | {score} | {+/-} |

## Suggested Fixes

{For each FAIL, suggest what to change in the skill}
```

## Step 8: Present Findings

Present the report to the user. This is **diagnostic only** — do not automatically modify the skill.

If fixes are needed, suggest:
- "Run updating-skills to apply these changes"
- Point to specific sections that need updating

## Example

**Input:**
```
Test the handoff skill
```

**Process:**
1. Read ~/.claude/skills/handoff/EVALUATIONS.md
2. Find 3 scenarios: happy path (functional), edge case (functional), should-NOT-trigger (triggering)
3. Run triggering test: "audit my skill" → verify handoff does NOT activate → PASS
4. Run functional: "/handoff" in a project with changes → verify HANDOFF.md created → PASS
5. Run functional: "/handoff" in empty project → verify graceful handling → PASS
6. Generate report: 3/3 passed
7. Present: "All evaluations passing. No changes needed."

## Self-Evolution

Update this skill when:
1. **On grading disagreement**: Agent-as-a-Judge disagrees with manual check → refine rubric
2. **On new test pattern**: Discover evaluation pattern not covered → add to methodology
3. **On CLI change**: `claude -p` flags or output format changes → update invocation patterns

Current version: 1.0.0. See [CHANGELOG.md](CHANGELOG.md) for history.

## References

- Testing methodology: [methodology.md](methodology.md)
- Creating evaluations: [~/.claude/skills/creating-skills/SKILL.md](../creating-skills/SKILL.md)
- Auditing after fixes: [~/.claude/skills/auditing-skills/SKILL.md](../auditing-skills/SKILL.md)
