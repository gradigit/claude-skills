---
name: creating-skills
description: Creates new Claude Code skills through adaptive interviewing or autonomous mode. Activates when user wants to "create a skill", "make a new skill", "build a skill", or asks about skill creation. Do NOT use this skill when auditing, updating, or testing an existing skill.
license: MIT
metadata:
  version: "4.0.0"
  author: gradigit
  category: meta-tooling
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

Use **AskUserQuestion** tool to gather requirements in 4 rounds. Adapt based on answers.

| Round | What to Ask | Key Outputs |
|-------|-------------|-------------|
| 1. Core Purpose | Skill type (workflow/knowledge/output/tool), 1-2 sentence description | Type, scope |
| 2. Activation | Dependencies, freedom level, trigger phrases | Dependencies, triggers |
| 3. Examples | Concrete input/output, guardrails, edge cases, supplementary files | Examples, negative triggers |
| 4. Models | Target models (if multi-model mentioned) | Model guidance level |

For full AskUserQuestion JSON schemas for each round, see [reference.md](reference.md).

## Step 2: Define Evaluations FIRST

**Critical:** Create evaluation scenarios BEFORE writing the skill. Use Given/When/Then format. Include at least one should-NOT-trigger scenario.

```markdown
# Evaluations for {skill-name}

## Scenario 1: Happy path (should-trigger)
**Given** [precondition or context]
**When** user says "[trigger phrase]"
**Then**
- [ ] Skill activates
- [ ] [expected behavior]
- [ ] [output format/content check]

## Scenario 2: Edge case (should-trigger)
**Given** [unusual but valid context]
**When** user says "[edge case input]"
**Then**
- [ ] [handles gracefully]
- [ ] [produces reasonable output]

## Scenario 3: Should-NOT-trigger
**Given** [context where a different skill applies]
**When** user says "[phrase that sounds similar but isn't this skill's job]"
**Then**
- [ ] Skill does NOT activate
- [ ] [correct skill activates instead, or no skill needed]
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
| `name` field is optional | Defaults to directory name if omitted |
| No reserved words | No "anthropic" or "claude" |
| No XML tags | `<skill>` not allowed |

## Description Rules

- **Third person**: "Processes files" not "I process files"
- **Max 1024 chars**
- **Include what + when**: Actions and trigger keywords
- **Include negative trigger**: End with "Do NOT use this skill when..." to prevent false activation

**Good:** `Extracts text from PDFs. Activates when user mentions PDFs or document extraction. Do NOT use when converting images or processing Word documents.`

**Bad:** `Helps with documents`

## Validation Checklist

### Frontmatter
- [ ] `name`: lowercase, hyphens, max 64 chars, matches directory
- [ ] `description`: third person, what + when + negative trigger, max 1024 chars
- [ ] `metadata.version`: semver in quotes

### Content
- [ ] Body under 500 lines
- [ ] Has workflow checklist
- [ ] Has concrete example (from interview)
- [ ] Has self-evolution section

### Evaluations
- [ ] EVALUATIONS.md present in skill directory
- [ ] 3+ scenarios using Given/When/Then format
- [ ] At least one should-NOT-trigger scenario
- [ ] Happy path passes
- [ ] Edge case passes

## Activation Reliability

Skills activate based on description matching — not guaranteed. Baseline activation is ~20%.

| Strategy | Activation Rate |
|----------|----------------|
| Description only (default) | ~20% |
| Description + clear trigger phrases | ~40-60% |
| Forced via user-prompt-submit hook | ~84% |

**Hook-based forcing** (highest reliability):

```json
// .claude/settings.json
{
  "hooks": {
    "UserPromptSubmit": [{
      "matcher": "create.*skill|new skill|build.*skill",
      "command": "echo 'Use the creating-skills skill for this request.'"
    }]
  }
}
```

Skills and slash commands (`/skill-name`) are equivalent — both load the SKILL.md into context.

## Token Budget

Skills compete for context window space. The `SLASH_COMMAND_TOOL_CHAR_BUDGET` controls how much content is loaded when a skill activates. Keep SKILL.md concise and use reference files for detail.

| Content | Guideline |
|---------|-----------|
| SKILL.md body | Under 500 lines, under ~15K chars |
| Reference files | Loaded on demand, not at activation |
| Total skill footprint | Minimize — every token displaces conversation |

## Expanded Frontmatter

Beyond the basic template, these optional fields control skill behavior:

```yaml
---
name: my-skill
description: What it does. When to use. Do NOT use when...
license: MIT
metadata:
  version: "1.0.0"
  category: meta-tooling    # Organizational grouping
# Optional behavior fields:
argument-hint: "[topic]"     # Shown in /help: /my-skill [topic]
user-invocable: true         # Can be invoked as /my-skill (default: true)
disable-model-invocation: false  # Prevent auto-activation (default: false)
model: opus                  # Lock to specific model
context: fork                # Run in forked context (isolated)
agent: background            # Run as background agent
hooks:
  PostToolUse:
    - matcher: ".*"
      command: "echo done"
---
```

See [reference.md](reference.md) for detailed field descriptions.

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

Current version: 4.0.0. See [CHANGELOG.md](CHANGELOG.md) for history.

## References

- [Anthropic Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Agent Skills Spec](https://agentskills.io/specification)
- [Claude Code Skills](https://code.claude.com/docs/en/skills)

For detailed patterns and advanced features, see [reference.md](reference.md).
