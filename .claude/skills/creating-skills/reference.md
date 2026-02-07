# Creating Skills Reference

Detailed best practices and patterns from official Anthropic documentation.

## Contents

- Frontmatter specification (required + optional fields)
- Adaptive interview methodology
- Evaluation-first development
- Content guidelines
- Progressive disclosure patterns
- Model-specific authoring
- MCP tool integration
- Common patterns
- Advanced: executable scripts
- Complete checklist

---

## Frontmatter Specification

### Required Fields

| Field | Rules |
|-------|-------|
| `name` | 1-64 chars, lowercase alphanumeric + hyphens, no `--`, can't start/end with `-`, no XML tags, must match directory name |
| `description` | 1-1024 chars, third person, what + when, no XML tags |

### Optional Fields

| Field | Purpose | Constraints |
|-------|---------|-------------|
| `license` | License for published skills | MIT, Apache-2.0, etc. |
| `compatibility` | Environment requirements | 1-500 chars |
| `metadata` | Custom key-value pairs | Map of strings |
| `allowed-tools` | Pre-approved tools | Space-delimited list |

### Complete Example

```yaml
---
name: processing-pdfs
description: Extracts text and tables from PDF files, fills forms. Activates when user mentions PDFs, forms, or document extraction.
license: Apache-2.0
compatibility: Requires pypdf and pdfplumber packages
metadata:
  version: "1.0.0"
  author: your-org
  category: document-processing
allowed-tools: Read Grep Glob Bash(python:*)
---
```

### allowed-tools Syntax

```yaml
allowed-tools: Read Grep Glob                    # Simple tools
allowed-tools: Bash(python:*) Bash(npm:*)        # Bash with patterns
allowed-tools: mcp__github__create_issue         # MCP tools
```

---

## Adaptive Interview Methodology

### Why Interview?

Traditional skill creation asks users to write specs upfront. Problems:
- Users don't know what's possible
- Users forget edge cases
- Requirements are incomplete

**Solution:** Adaptive questioning that builds understanding incrementally.

### Interview Principles

1. **Start broad, narrow down** — Don't ask for specifics first
2. **Adapt based on answers** — Skip irrelevant questions
3. **Show options** — Users recognize better than recall
4. **Get concrete examples** — Abstract descriptions fail
5. **Identify guardrails** — What should NOT happen?

### AskUserQuestion Tool Format

```json
{
  "questions": [
    {
      "question": "The question text?",
      "header": "Short label",
      "options": [
        {"label": "Option 1", "description": "What this means"},
        {"label": "Option 2", "description": "What this means"}
      ],
      "multiSelect": false
    }
  ]
}
```

Rules:
- 1-4 questions per call
- 2-4 options per question
- Header max 12 chars
- Users can always select "Other" for custom input

### Adaptive Flow

```
Round 1: What type? → Determines subsequent questions
    ↓
Round 2: Dependencies + Freedom level → Based on type
    ↓
Round 3: Examples + Guardrails → Always needed
    ↓
Round 4: Model targets → If multi-model mentioned
```

---

## Evaluation-First Development

### The Anthropic Methodology

From official docs: "Build evaluations BEFORE writing extensive documentation."

**Process:**
1. Identify gaps — Run Claude on tasks without skill, document failures
2. Create evaluations — 3 scenarios testing these gaps
3. Establish baseline — Measure performance without skill
4. Write minimal instructions — Just enough to pass evaluations
5. Iterate — Execute, compare, refine

### Evaluation File Format

Save as `{skill-name}/EVALUATIONS.md`:

```markdown
# Evaluations for {skill-name}

## Scenario 1: Happy Path
**Input:** [typical use case]
**Skills:** [{skill-name}]
**Expected behavior:**
- [ ] Does X correctly
- [ ] Produces output Y
- [ ] Follows format Z

**Success criteria:** [how to verify]

## Scenario 2: Edge Case
**Input:** [unusual but valid]
**Expected behavior:**
- [ ] Handles gracefully
- [ ] Produces reasonable output

**Success criteria:** [verification]

## Scenario 3: Error/Boundary Case
**Input:** [invalid or tricky]
**Expected behavior:**
- [ ] Doesn't crash
- [ ] Provides helpful feedback

**Success criteria:** [verification]
```

### Testing Loop

```
1. Run evaluation scenario
2. Did it pass?
   YES → Move to next scenario
   NO  → Add minimal instructions to skill
3. Re-run failed scenario
4. Repeat until all pass
5. Run all scenarios together (regression)
```

---

## Content Guidelines

### Conciseness Principle

The context window is shared. Your skill competes with:
- System prompt
- Conversation history
- Other skills' metadata
- User's request

**Default assumption:** Claude is smart. Only add what it doesn't know.

**Challenge each piece:**
- "Does Claude need this explanation?"
- "Can I assume Claude knows this?"
- "Does this justify its token cost?"

### Good vs Bad

**Good (~50 tokens):**
```markdown
## Extract PDF text

Use pdfplumber:

import pdfplumber
with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```

**Bad (~150 tokens):**
```markdown
## Extract PDF text

PDF (Portable Document Format) files are a common file format that contains
text, images, and other content. To extract text from a PDF, you'll need to
use a library. There are many libraries available...
```

---

## Model-Specific Authoring

### Model Characteristics

| Model | Token Efficiency | Guidance Needed | Best For |
|-------|-----------------|-----------------|----------|
| **Opus** | Most efficient | Minimal | Complex reasoning, terser skills |
| **Sonnet** | Balanced | Moderate | Default target |
| **Haiku** | Least efficient | Most explicit | Fast tasks, needs detail |

### Authoring Strategy

**If targeting single model:**
- Haiku: Add step-by-step details, explicit examples
- Sonnet: Balanced guidance (default)
- Opus: Can be terser, trust reasoning

**If targeting multiple models:**
- Write for Sonnet
- Test with Haiku to ensure enough guidance
- Test with Opus to ensure not over-explaining

### Example: Same Skill, Different Detail Levels

**Haiku version:**
```markdown
## Step 1: Read the file
1. Use the Read tool
2. Pass the full absolute path
3. Check if content is empty

## Step 2: Parse the content
1. Split by newlines
2. For each line, extract the key and value
3. Store in a dictionary
```

**Opus version:**
```markdown
## Process
Read file → Parse key-value pairs → Return dict
```

---

## MCP Tool Integration

### Fully Qualified Names

Always use `ServerName:tool_name` format:

```markdown
Use the GitHub:create_issue tool to create issues.
Use the BigQuery:bigquery_schema tool to retrieve schemas.
Use the Slack:post_message tool to send messages.
```

**Why?** Multiple MCP servers may define similar tools. Without the prefix, Claude may fail to locate the correct tool.

### Documenting MCP Dependencies

In frontmatter:
```yaml
compatibility: Requires GitHub MCP server configured
```

In body:
```markdown
## Prerequisites

This skill requires the following MCP servers:
- `GitHub` — for repository operations
- `Linear` — for issue tracking
```

---

## Progressive Disclosure Patterns

### Pattern 1: High-Level Guide with References

```markdown
# PDF Processing

## Quick start
[code example]

## Advanced features
**Form filling**: See [FORMS.md](FORMS.md)
**API reference**: See [REFERENCE.md](REFERENCE.md)
```

### Pattern 2: Domain-Specific Organization

```
bigquery-skill/
├── SKILL.md (overview)
└── reference/
    ├── finance.md
    ├── sales.md
    └── product.md
```

### Pattern 3: Conditional Details

```markdown
## Creating documents
Use docx-js. See [DOCX-JS.md](DOCX-JS.md).

## Editing documents
**For tracked changes**: See [REDLINING.md](REDLINING.md)
```

### Important: One Level Deep

**Bad:** SKILL.md → advanced.md → details.md

**Good:** SKILL.md → advanced.md (direct info)

---

## Common Patterns

### Workflow Pattern

```markdown
## Workflow

Copy this checklist:

- [ ] Step 1: Analyze input
- [ ] Step 2: Process data
- [ ] Step 3: Validate output
- [ ] Step 4: Present results

**Step 1: Analyze input**
[Details]
```

### Feedback Loop Pattern

```markdown
1. Make changes
2. **Validate**: python scripts/validate.py
3. If fails → fix → validate again
4. Only proceed when validation passes
```

### Template Pattern

**Strict:**
```markdown
ALWAYS use this exact template:
[template]
```

**Flexible:**
```markdown
Sensible default, adapt as needed:
[template]
```

### Examples Pattern

```markdown
**Example 1:**
Input: Added authentication
Output: feat(auth): add JWT authentication

**Example 2:**
Input: Fixed date bug
Output: fix(reports): correct date formatting
```

---

## Advanced: Executable Scripts

### Solve, Don't Punt

```python
# Good — handles errors
def process_file(path):
    try:
        with open(path) as f:
            return f.read()
    except FileNotFoundError:
        print(f"Creating {path}")
        with open(path, 'w') as f:
            f.write('')
        return ''

# Bad — just fails
def process_file(path):
    return open(path).read()
```

### Document Constants

```python
# Good — justified
REQUEST_TIMEOUT = 30  # HTTP requests typically complete within 30s
MAX_RETRIES = 3       # Balances reliability vs speed

# Bad — magic numbers
TIMEOUT = 47
RETRIES = 5
```

---

## Complete Checklist

### Frontmatter
- [ ] `name`: lowercase, hyphens, max 64, matches directory
- [ ] `description`: third person, what + when, max 1024
- [ ] `metadata.version`: semver in quotes
- [ ] Optional fields only if needed

### Interview
- [ ] Asked skill type
- [ ] Asked dependencies
- [ ] Asked freedom level
- [ ] Got concrete example
- [ ] Identified guardrails
- [ ] Asked about model targets

### Evaluations
- [ ] 3 scenarios defined BEFORE writing skill
- [ ] Happy path scenario
- [ ] Edge case scenario
- [ ] Error/boundary scenario
- [ ] All scenarios pass

### Content
- [ ] Body under 500 lines
- [ ] Workflow checklist
- [ ] Concrete example
- [ ] Self-evolution section
- [ ] No over-explaining
- [ ] References one level deep

### Testing
- [ ] Tested with target model(s)
- [ ] If multi-model: tested with Haiku for guidance adequacy

---

## Sources

- [Anthropic Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Agent Skills Overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [Agent Skills Spec](https://agentskills.io/specification)
- [Claude Code Skills](https://code.claude.com/docs/en/skills)
