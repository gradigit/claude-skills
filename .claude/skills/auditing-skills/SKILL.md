---
name: auditing-skills
description: Audits Agent Skills for spec compliance and best practices. Activates when user asks to "audit skill", "check skill", "validate skill", or mentions skill optimization.
license: MIT
metadata:
  version: "1.0.0"
  author: gradigit
  tags:
    - skills
    - meta
    - audit
    - validation
  triggers:
    - "audit skill"
    - "check skill"
    - "validate skill"
    - "skill audit"
---

# Auditing Skills

Validates skills against Agent Skills specifications and best practices.

## Workflow

```
- [ ] 1. Identify target skill (path or name)
- [ ] 2. Read SKILL.md and any referenced files
- [ ] 3. Run validation checks (see checklist.md)
- [ ] 4. Generate audit report
- [ ] 5. Offer to fix critical issues
```

## Quick Audit

For a fast check, validate these critical items:

### Frontmatter (Required)
| Field | Rule |
|-------|------|
| `name` | Lowercase, hyphens only, max 64 chars, matches directory name, no XML tags |
| `description` | Non-empty, max 1024 chars, third person, includes what + when, no XML tags |

### Frontmatter (Recommended)
| Field | Rule |
|-------|------|
| `license` | Present (MIT, Apache-2.0, etc.) |
| `metadata.version` | Semver string in quotes |

### Content
| Check | Rule |
|-------|------|
| Line count | SKILL.md body under 500 lines |
| Workflow | Has checklist of steps |
| Example | Has concrete input/output |
| References | One level deep (no chains) |

## Audit Report Format

Generate report in this structure:

```markdown
# Skill Audit: {skill-name}

**Path**: {path}
**Version**: {version or "not specified"}

## Summary

| Status | Count |
|--------|-------|
| Critical | X |
| Warnings | Y |
| Suggestions | Z |

**Overall**: PASS / NEEDS WORK / FAIL

## Critical Issues

{Issues that violate the spec - must fix}

## Warnings

{Best practice violations - should fix}

## Suggestions

{Optimizations - nice to have}
```

## Severity Levels

**Critical** (spec violations):
- Missing required frontmatter fields
- Invalid name format (uppercase, underscores, XML tags)
- Name doesn't match directory
- SKILL.md over 500 lines without progressive disclosure

**Warning** (best practice violations):
- Missing license or version
- No workflow checklist
- No concrete examples
- First/second person in description
- Deeply nested references (>1 level)
- Windows-style paths

**Suggestion** (optimizations):
- Verbose explanations (Claude already knows X)
- Changelog in SKILL.md instead of separate file
- Reference files >100 lines without TOC
- Missing self-evolution section

## Common Issues

| Issue | Fix |
|-------|-----|
| `name: My-Skill` | Use lowercase: `my-skill` |
| `name: my_skill` | Use hyphens: `my-skill` |
| Description: "I help you..." | Use third person: "Helps users..." |
| Description: "Does stuff" | Add specifics: what + when to trigger |
| SKILL.md 600 lines | Split into reference files |
| `ref.md → detail.md → info.md` | Flatten to one level |

## Example

**Input**: Audit ~/.claude/skills/my-skill

**Output**:
```markdown
# Skill Audit: my-skill

**Path**: ~/.claude/skills/my-skill
**Version**: 1.0.0

## Summary

| Status | Count |
|--------|-------|
| Critical | 0 |
| Warnings | 2 |
| Suggestions | 1 |

**Overall**: NEEDS WORK

## Warnings

1. **No workflow checklist** - Add a workflow section with steps
2. **First person in description** - Change "I process files" to "Processes files"

## Suggestions

1. **Changelog in SKILL.md** - Move to separate CHANGELOG.md for token efficiency
```

## Self-Evolution

Update this skill when:
1. **On spec change**: Agent Skills spec updates → update checklist
2. **On new anti-pattern**: Discover common issue → add to checks

Current version: 1.0.0. See [CHANGELOG.md](CHANGELOG.md) for history.

## References

For complete validation criteria, see [checklist.md](checklist.md).
