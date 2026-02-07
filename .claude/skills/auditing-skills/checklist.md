# Audit Checklist

Complete validation criteria for Agent Skills.

## Contents

- Frontmatter validation
- Content structure
- Quality checks
- Scripts and code
- Anti-patterns

---

## Frontmatter Validation

### Required Fields

#### name
- [ ] Present and non-empty
- [ ] Max 64 characters
- [ ] Lowercase letters, numbers, hyphens only
- [ ] No leading/trailing hyphens
- [ ] No consecutive hyphens (`--`)
- [ ] No XML tags
- [ ] Matches parent directory name
- [ ] No reserved words ("anthropic", "claude")

#### description
- [ ] Present and non-empty
- [ ] Max 1024 characters
- [ ] Written in third person
- [ ] No XML tags
- [ ] Describes what skill does
- [ ] Describes when to use it (trigger keywords)

### Recommended Fields

#### license
- [ ] Present (MIT, Apache-2.0, etc.)

#### metadata.version
- [ ] Present
- [ ] Semver format in quotes (e.g., "1.0.0")
- [ ] Not at top level (use `metadata.version`)

### Optional Fields

#### compatibility
- [ ] If present, max 500 characters
- [ ] Describes environment requirements

#### allowed-tools
- [ ] If present, space-delimited list
- [ ] Valid tool format

---

## Content Structure

### Line Count
- [ ] SKILL.md body under 500 lines
- [ ] If over 300 lines, uses progressive disclosure

### Workflow Section
- [ ] Has workflow or steps section
- [ ] Uses checklist format (`- [ ]`)
- [ ] Steps are clear and sequential

### Examples
- [ ] Has at least one concrete example
- [ ] Shows input and expected output
- [ ] Not abstract ("do X") but specific

### Self-Evolution
- [ ] Has self-evolution section
- [ ] Describes when to update
- [ ] Version reference (inline or to CHANGELOG.md)

### Progressive Disclosure
- [ ] Large content split into separate files
- [ ] References are one level deep
- [ ] No chains: `SKILL.md → a.md → b.md`

### Reference Files (if present)
- [ ] Files >100 lines have table of contents
- [ ] Clear, descriptive filenames
- [ ] Forward slashes in paths (not backslash)

---

## Quality Checks

### Conciseness
- [ ] No unnecessary explanations
- [ ] Assumes Claude's baseline knowledge
- [ ] Each paragraph justifies its token cost

### Terminology
- [ ] Consistent terms throughout
- [ ] One word for one concept (not "field/box/element")

### Time Sensitivity
- [ ] No date-dependent instructions
- [ ] No "before/after [date]" logic
- [ ] Historical info in "old patterns" section if needed

### Person
- [ ] Description in third person
- [ ] Body can vary but should be consistent

---

## Scripts and Code (if present)

### Script Quality
- [ ] Scripts handle errors explicitly
- [ ] No "punt to Claude" error handling
- [ ] Constants are documented (no magic numbers)

### Dependencies
- [ ] Required packages listed
- [ ] Platform differences noted (claude.ai vs API)

### Execution vs Reading
- [ ] Clear whether to run or read scripts
- [ ] "Run X" vs "See X for algorithm"

### MCP Tools (if used)
- [ ] Fully qualified names: `ServerName:tool_name`
- [ ] Not just `tool_name`

---

## Anti-Patterns to Check

| Anti-Pattern | Severity |
|--------------|----------|
| `version` at top level instead of `metadata.version` | Critical |
| Name with uppercase letters | Critical |
| Name with underscores | Critical |
| Name doesn't match directory | Critical |
| XML tags in name or description | Critical |
| Missing `name` field | Critical |
| Missing `description` field | Critical |
| SKILL.md over 500 lines | Critical |
| First/second person in description | Warning |
| Vague description without triggers | Warning |
| No workflow section | Warning |
| No examples | Warning |
| Deeply nested references | Warning |
| Windows paths (`\`) | Warning |
| Too many options without default | Warning |
| Verbose explanations | Suggestion |
| Changelog inline instead of separate file | Suggestion |
| No self-evolution section | Suggestion |
| Reference file >100 lines without TOC | Suggestion |

---

## Scoring

**PASS**: 0 critical, 0-2 warnings
**NEEDS WORK**: 0 critical, 3+ warnings OR any suggestions
**FAIL**: 1+ critical issues

---

## Sources

- [Agent Skills Specification](https://agentskills.io/specification)
- [Agent Skills Overview](https://agentskills.io/what-are-skills)
- [Agent Skills Integration](https://agentskills.io/integrate-skills)
- [Anthropic Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Gemini CLI Skills](https://geminicli.com/docs/cli/skills/)
