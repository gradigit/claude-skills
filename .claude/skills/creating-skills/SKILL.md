---
name: creating-skills
description: Creates new Claude Code skills through adaptive interviewing or autonomous mode. Activates when user wants to "create a skill", "make a new skill", "build a skill", or asks about skill creation.
license: MIT
metadata:
  version: "3.1.0"
  author: gradigit
  tags:
    - skills
    - meta
    - creation
  triggers:
    - "create a skill"
    - "make a new skill"
    - "build a skill"
    - "new skill"
---

# Creating Skills

Creates well-structured skills through adaptive interviewing or autonomous generation.

## Workflow

```
- [ ] 1. Ask mode preference (guided vs autonomous)
- [ ] 2. If guided: Interview user (adaptive questions)
     If autonomous: Infer requirements from request
- [ ] 3. Define evaluation scenarios (3 test cases)
- [ ] 4. Generate minimal SKILL.md
- [ ] 5. Validate against checklist
- [ ] 6. Create at ~/.claude/skills/{name}/SKILL.md
- [ ] 7. Test and iterate (if guided mode)
```

## Step 1: Mode Selection

**Always ask this first** using AskUserQuestion:

```json
{
  "questions": [
    {
      "question": "How should I create this skill?",
      "header": "Mode",
      "options": [
        {"label": "Autonomous (Recommended)", "description": "I'll infer everything and create it — no questions asked"},
        {"label": "Guided interview", "description": "Walk me through requirements step by step"}
      ],
      "multiSelect": false
    }
  ]
}
```

### Autonomous Mode

If user selects **Autonomous**:
1. Parse the user's request for: purpose, triggers, examples, complexity
2. Make reasonable assumptions — prefer simplicity
3. Generate skill immediately without further questions
4. Present the complete skill for review
5. User can request changes after seeing the result

**Best for:**
- Simple skills with clear purpose
- User already provided a detailed prompt
- User wants quick iteration (create → tweak → done)

### Guided Mode

If user selects **Guided interview**:
1. Proceed to Step 2 (Adaptive Interview)
2. Ask questions in rounds
3. More thorough but requires back-and-forth

**Best for:**
- Complex workflows
- User is unsure what they want
- Skill needs precise guardrails

---

## Step 2a: Autonomous Inference

When in autonomous mode, extract from user's request:

| Element | How to Infer |
|---------|--------------|
| **Name** | Gerund form of main action (e.g., "format commits" → `formatting-commits`) |
| **Triggers** | Key verbs/nouns in request |
| **Type** | Workflow if multi-step, Knowledge if reference-heavy, Output if formatting |
| **Freedom** | High unless user specifies exact steps |
| **Complexity** | Simple unless request implies reference files |

**If ambiguous:** Make the simpler choice. User can refine after seeing output.

Proceed directly to Step 3 (Evaluations) then Step 4 (Generate).

---

## Step 2b: Guided Interview (Adaptive)

Use **AskUserQuestion** tool to gather requirements. Ask in rounds — adapt based on answers.

### Round 1: Core Purpose (Guided Only)

Use AskUserQuestion with these questions:

```json
{
  "questions": [
    {
      "question": "What type of skill do you want to create?",
      "header": "Skill type",
      "options": [
        {"label": "Workflow automation", "description": "Multi-step process with checklist"},
        {"label": "Knowledge/reference", "description": "Domain expertise, guidelines, standards"},
        {"label": "Output formatting", "description": "Templates, structured outputs"},
        {"label": "Tool integration", "description": "MCP servers, scripts, APIs"}
      ],
      "multiSelect": false
    }
  ]
}
```

Then ask open-ended: "Describe what this skill should do in 1-2 sentences."

### Round 2: Activation & Dependencies (Guided Only)

Adapt based on Round 1 answers:

```json
{
  "questions": [
    {
      "question": "What external dependencies does this skill need?",
      "header": "Dependencies",
      "options": [
        {"label": "None", "description": "Self-contained, no packages or tools"},
        {"label": "Python packages", "description": "Needs pip packages"},
        {"label": "MCP servers", "description": "Needs MCP tool access"},
        {"label": "Shell commands", "description": "Runs CLI tools"}
      ],
      "multiSelect": true
    },
    {
      "question": "How much freedom should Claude have when executing?",
      "header": "Freedom level",
      "options": [
        {"label": "High", "description": "Multiple valid approaches, Claude decides"},
        {"label": "Medium", "description": "Preferred pattern with flexibility"},
        {"label": "Low", "description": "Exact steps required, fragile operations"}
      ],
      "multiSelect": false
    }
  ]
}
```

Ask: "List 3-5 trigger phrases that should activate this skill."

### Round 3: Examples & Guardrails (Guided Only)

```json
{
  "questions": [
    {
      "question": "Will this skill need supplementary files?",
      "header": "Complexity",
      "options": [
        {"label": "Simple", "description": "Just SKILL.md, under 300 lines"},
        {"label": "With examples", "description": "Needs examples.md"},
        {"label": "With reference docs", "description": "Needs reference.md"},
        {"label": "With scripts", "description": "Needs executable code"}
      ],
      "multiSelect": true
    }
  ]
}
```

Ask:
1. "Show me a concrete example: input and expected output."
2. "What should this skill NOT do? Any guardrails?"
3. "Any edge cases to handle specially?"

### Round 4: Model Testing (Guided Only, if multi-model)

```json
{
  "questions": [
    {
      "question": "Which models will use this skill?",
      "header": "Models",
      "options": [
        {"label": "All models", "description": "Haiku, Sonnet, and Opus"},
        {"label": "Sonnet only", "description": "Balanced guidance level"},
        {"label": "Opus only", "description": "Can be terser"},
        {"label": "Haiku only", "description": "Needs more explicit guidance"}
      ],
      "multiSelect": false
    }
  ]
}
```

## Step 2: Define Evaluations FIRST

**Critical:** Create 3 evaluation scenarios BEFORE writing the skill.

```markdown
## Evaluation Scenarios

### Scenario 1: Happy path
- **Input**: [typical use case from interview]
- **Expected behavior**: [what Claude should do]
- **Success criteria**: [how to verify]

### Scenario 2: Edge case
- **Input**: [unusual but valid input]
- **Expected behavior**: [correct handling]
- **Success criteria**: [verification method]

### Scenario 3: Boundary/error case
- **Input**: [invalid or tricky input]
- **Expected behavior**: [graceful handling]
- **Success criteria**: [verification method]
```

Save to `{skill-name}/EVALUATIONS.md` for future testing.

## Step 3: Generate Minimal SKILL.md

Write just enough to pass evaluations. Start minimal, add only when tests fail.

### Frontmatter Template

```yaml
---
name: {lowercase-hyphens-only}
description: {Third person. What it does + when to use it. Max 1024 chars.}
metadata:
  version: "1.0.0"
---
```

**Optional fields** (add only if needed):

```yaml
license: MIT                              # If publishing
compatibility: Requires pdfplumber        # If has dependencies
allowed-tools: Read Grep Bash(python:*)   # If pre-approving tools
```

### Body Template

```markdown
# {Skill Name}

{One-line description}

## Workflow

- [ ] 1. First step
- [ ] 2. Second step
- [ ] 3. Third step

## Core Logic

{Main rules — keep minimal}

## Example

**Input:**
{from interview}

**Output:**
{from interview}

## Self-Evolution

Update when:
1. User corrects output → update rules
2. New pattern discovered → add to skill

Current version: 1.0.0
```

## Naming Conventions

| Rule | Example |
|------|---------|
| Lowercase + hyphens | `pdf-processing` not `PDF_Processing` |
| Max 64 chars | Keep short |
| Gerund form preferred | `creating-skills` not `skill-creator` |
| Match directory name | `name: foo` → directory `foo/` |
| No reserved words | No "anthropic" or "claude" |
| No XML tags | `<skill>` not allowed |

## Description Rules

- **Third person**: "Processes files" not "I process files"
- **Max 1024 chars**
- **Include what + when**: Actions and trigger keywords

**Good:** `Extracts text from PDFs. Activates when user mentions PDFs or document extraction.`

**Bad:** `Helps with documents`

## Validation Checklist

### Frontmatter
- [ ] `name`: lowercase, hyphens, max 64 chars, matches directory
- [ ] `description`: third person, what + when, max 1024 chars
- [ ] `metadata.version`: semver in quotes

### Content
- [ ] Body under 500 lines
- [ ] Has workflow checklist
- [ ] Has concrete example (from interview)
- [ ] Has self-evolution section

### Evaluations
- [ ] 3 scenarios defined
- [ ] Happy path passes
- [ ] Edge case passes
- [ ] Error case handled gracefully

## Model-Specific Guidance

| Model | Authoring Consideration |
|-------|------------------------|
| **Haiku** | Add more explicit guidance, step-by-step details |
| **Sonnet** | Balanced — default target |
| **Opus** | Can be terser, avoid over-explaining |

If targeting multiple models, write for Sonnet and test with Haiku to ensure enough guidance.

## MCP Tool References

For skills using MCP tools, use fully qualified names:

```markdown
Use the GitHub:create_issue tool to create issues.
Use the BigQuery:bigquery_schema tool to retrieve schemas.
```

Format: `ServerName:tool_name`

## Anti-Patterns

| Anti-Pattern | Why |
|--------------|-----|
| First/second person in description | Breaks discovery |
| Vague trigger keywords | Skill won't activate |
| Over-explaining | Wastes tokens |
| Nested references | Claude may partially read |
| Too many options | Confuses agent |
| Writing before evaluations | May build wrong thing |

## Progressive Disclosure

**When to use:** SKILL.md exceeds ~300 lines or has detailed reference material.

```
skill-name/
├── SKILL.md        # Core (loaded when triggered)
├── EVALUATIONS.md  # Test scenarios
├── examples.md     # Additional examples (on demand)
├── reference.md    # Detailed docs (on demand)
└── scripts/        # Executable code (run, not loaded)
```

## Self-Evolution

Update this skill when:
1. **On correction**: User corrects generated skill → update template
2. **On spec change**: Official docs change → update to match
3. **On interview improvement**: Better questions discovered → refine rounds

Current version: 3.1.0. See [CHANGELOG.md](CHANGELOG.md) for history.

## References

- [Anthropic Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Agent Skills Spec](https://agentskills.io/specification)
- [Claude Code Skills](https://code.claude.com/docs/en/skills)

For detailed patterns and advanced features, see [reference.md](reference.md).
