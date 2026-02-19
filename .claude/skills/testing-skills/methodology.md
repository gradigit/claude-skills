# Testing Methodology

Detailed testing protocols for Agent Skills evaluation.

## Contents

- CLI invocation patterns
- Isolated execution with context: fork
- Session continuation for multi-turn tests
- Agent-as-a-Judge protocol
- Hybrid grading decision table
- Three-tier methodology background

---

## CLI Invocation Patterns

### Single-Turn Test

```bash
# Basic invocation
claude -p "Create a skill for formatting git commits" --output-format json

# With specific model
claude -p "Test prompt" --model sonnet --output-format json

# With JSON schema validation
claude -p "Test prompt" --output-format json --json-schema '{"type":"object"}'
```

### Checking Skill Activation

After running a prompt, check the response for indicators that the skill was loaded:
- The response follows the skill's workflow
- Skill-specific terminology or patterns appear
- Tools listed in `allowed-tools` are used

### Output Capture

```bash
# Capture to file for analysis
claude -p "Test prompt" --output-format json > /tmp/test-output.json
```

---

## Isolated Execution

Use `context: fork` when testing skills that modify files to avoid side effects:

```bash
# The skill's frontmatter should include:
# context: fork
```

For ad-hoc isolation, run tests in a temporary directory:

```bash
# Create isolated test environment
mkdir -p /tmp/skill-test && cd /tmp/skill-test
git init
# Run test
claude -p "Test prompt"
# Clean up
rm -rf /tmp/skill-test
```

---

## Session Continuation

For multi-turn tests (e.g., guided interview skills):

1. Start a session with the first prompt
2. Continue with follow-up prompts in the same session
3. Verify state carries across turns

Multi-turn testing is manual — `claude -p` is single-turn only. For multi-turn, interact directly and observe.

---

## Agent-as-a-Judge Protocol

### When to Use

Use Agent-as-a-Judge for criteria that cannot be verified deterministically:

| Criterion | Method |
|-----------|--------|
| "Output is well-structured" | Agent-as-a-Judge |
| "Description is specific, not vague" | Agent-as-a-Judge |
| "Appropriate tools selected" | Agent-as-a-Judge |
| "File contains valid YAML" | Code check |
| "Exactly 3 files created" | Code check |

### Evaluation Prompt Template

```
You are evaluating the output of an Agent Skill. Grade each criterion as PASS or FAIL.

## Skill Under Test
{skill-name} v{version}

## Test Scenario
{scenario description}

## Skill Output
{captured output}

## Criteria
{list of criteria from EVALUATIONS.md Then block}

For each criterion, respond:
- **Criterion**: {text}
- **Grade**: PASS or FAIL
- **Reason**: {one sentence justification}
```

### Reliability

Agent-as-a-Judge shows 0.3% disagreement rate with human evaluators (vs 31% for raw LLM-as-Judge without structured rubrics). The key differentiator is the structured rubric — always provide specific criteria, never ask for open-ended quality assessment.

---

## Hybrid Grading Decision Table

For each criterion in a Then block, choose the grading method:

| Pattern | Method | Example |
|---------|--------|---------|
| File exists / created | Code: `ls` or `test -f` | "Creates HANDOFF.md" |
| Output contains text | Code: grep | "Includes summary section" |
| Count of items | Code: count | "Lists exactly 3 scenarios" |
| YAML/JSON valid | Code: parse | "Frontmatter is valid YAML" |
| Format follows template | Hybrid | Code for structure, Agent for content |
| Content quality | Agent | "Description is specific and actionable" |
| Behavioral | Agent | "Asks clarifying question before proceeding" |
| Negative | Agent or Code | "Does NOT modify any files" |

---

## Three-Tier Methodology

### Tier 1: Triggering Tests

**Purpose**: Verify the skill activates when it should and stays silent when it shouldn't.

**Why this matters**: Skills compete for activation based on description matching. Without triggering tests, a skill might silently fail to activate or incorrectly fire on unrelated prompts.

**What to test**:
- Exact trigger phrases from the description
- Paraphrased triggers (natural language variations)
- Phrases that sound similar but belong to a different skill (should-NOT-trigger)

### Tier 2: Functional Tests

**Purpose**: Verify the skill produces correct, complete output for various inputs.

**Standard scenarios**:
- Happy path: typical, expected usage
- Edge case: unusual but valid input
- Error/boundary: invalid input or missing prerequisites

### Tier 3: Performance Tests

**Purpose**: Verify the skill adds value beyond what baseline Claude provides.

**When to include**: Only for skills where the delta is measurable and meaningful. Most skills skip this tier.

**Method**: Run the same task with and without the skill, compare on defined metrics.

---

## Sources

- [Anthropic Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Agent Skills Spec](https://agentskills.io/specification)
