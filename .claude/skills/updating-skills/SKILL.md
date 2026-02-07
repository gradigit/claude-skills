---
name: updating-skills
description: Systematic workflow for modifying existing Agent Skills. Ensures spec compliance, version bumps, changelog updates, and audit pass after every change. Activates when user asks to "update skill", "modify skill", "evolve skill", "bump version", or mentions changing an existing skill.
license: MIT
metadata:
  version: "1.0.0"
  author: gradigit
  updated: "2026-01-29"
  tags:
    - skills
    - workflow
    - maintenance
  triggers:
    - "update skill"
    - "modify skill"
    - "evolve skill"
    - "bump version"
    - "change skill"
---

# Updating Skills

Systematic workflow for modifying existing Agent Skills while maintaining spec compliance.

## Why This Exists

When iterating on a skill across multiple conversations, the creating-skills spec and auditing-skills checklist can fall out of context. This skill ensures every update follows the same disciplined process.

## Workflow

Use TaskCreate to track progress:

- [ ] 1. Read current state (all skill files)
- [ ] 2. Understand requested changes
- [ ] 3. Classify version bump (major/minor/patch)
- [ ] 4. Make changes following spec
- [ ] 5. Bump version in frontmatter
- [ ] 6. Update CHANGELOG.md
- [ ] 7. Audit against checklist
- [ ] 8. Fix any audit issues
- [ ] 9. Present summary to user
- [ ] 10. Push if published (user confirms)

## Reading Current State

Before any changes, read **all** skill files:

```
skill-name/
├── SKILL.md       # Always read first
├── CHANGELOG.md   # Check current version
├── examples.md    # If exists
├── heuristics.md  # If exists
├── reference.md   # If exists
├── README.md      # If exists (published skills)
└── LICENSE         # If exists
```

Never propose changes to files you haven't read.

## Classifying Version Bump

Follow semver:

| Change Type | Bump | Example |
|-------------|------|---------|
| Breaking change (workflow restructure, removed feature) | **Major** X.0.0 | 4.0.0 → 5.0.0 |
| New feature, new section, new capability | **Minor** x.Y.0 | 4.2.0 → 4.3.0 |
| Bug fix, typo, version ref fix, wording tweak | **Patch** x.y.Z | 4.3.0 → 4.3.1 |

When in doubt, use **minor**.

## Making Changes

Follow creating-skills spec:

- **Third person** in description — "Processes files" not "I process files"
- **Body under 500 lines** — use progressive disclosure if larger
- **Concrete examples** — real input/output, not abstract
- **One-level references** — SKILL.md → ref.md, never ref.md → detail.md
- **No over-engineering** — only change what was requested

### Cross-File Consistency

When updating, check **all files** for consistency:

| Check | Where |
|-------|-------|
| Version string | Frontmatter, CHANGELOG.md, examples.md, README.md |
| Workflow step count | SKILL.md workflow section, any "X steps" references |
| Feature references | If adding/removing a feature, update all mentions |
| Repo/URL references | If changing URLs, check every file |

This is the most common source of audit failures.

## Updating CHANGELOG.md

Follow Keep a Changelog format:

```markdown
## [X.Y.Z] - YYYY-MM-DD

### Added
- New features

### Changed
- Modified behavior

### Fixed
- Bug fixes

### Removed
- Removed features
```

Rules:
- Newest version at top
- Date in ISO format
- Group changes by type
- Be specific — "Added deep dependency investigation" not "Updated skill"

## Auditing

Run the auditing-skills checklist. Key checks:

### Frontmatter
- [ ] `name`: lowercase, hyphens, matches directory
- [ ] `description`: third person, what + when, max 1024 chars
- [ ] `license`: present
- [ ] `metadata.version`: matches CHANGELOG.md latest entry

### Content
- [ ] Body under 500 lines
- [ ] Workflow checklist present
- [ ] Concrete example present
- [ ] Self-evolution section present
- [ ] References one level deep

### Cross-File (updating-specific)
- [ ] Version consistent across all files
- [ ] Step counts match across all references
- [ ] No stale references to removed features
- [ ] No hardcoded values that should be generic
- [ ] CHANGELOG.md entry matches actual changes

### Quality
- [ ] No over-explaining
- [ ] No Windows paths
- [ ] No first/second person in description
- [ ] Consistent terminology

Report format:

```markdown
## Audit Result

**Grade**: A / B / C
**Version**: X.Y.Z

| Status | Count |
|--------|-------|
| Critical | 0 |
| Warnings | 0 |
| Suggestions | 0 |

{Details if any issues found}
```

## Pushing (If Published)

Only for skills published to GitHub:

```bash
cd <skill-directory>
git add -A
git commit -m "v{X.Y.Z}: {one-line summary}"
git push
```

Local-only skills skip this step.

## Example

**Input:**
```
Update the screening-github-cloud skill to add Python support
```

**Process:**
1. Read all files: SKILL.md, CHANGELOG.md, examples.md, heuristics.md, README.md, LICENSE
2. Changes needed: Add Python screening patterns
3. Version bump: minor (new capability) → 4.4.0
4. Make changes in SKILL.md, heuristics.md, examples.md
5. Update frontmatter version to "4.4.0"
6. Add CHANGELOG.md entry for 4.4.0
7. Audit all files for consistency
8. Fix any stale version refs (examples.md commonly has old versions)
9. Present diff summary
10. Push to GitHub

## Common Pitfalls

| Pitfall | Prevention |
|---------|------------|
| Stale version in examples.md | Search all files for old version string |
| Step count mismatch | Grep for "X steps" across all files |
| Hardcoded values surviving a "make generic" change | Search for the old hardcoded string |
| Forgetting CHANGELOG.md | Always update before audit |
| Amending when should be new version | Each user-requested change set = new version |

## Self-Evolution

Update this skill when:
1. **On missed consistency issue**: Add to cross-file checklist
2. **On new pitfall**: Add to common pitfalls table
3. **On workflow improvement**: Refine steps based on real usage

Current version: 1.0.0. See [CHANGELOG.md](CHANGELOG.md) for history.

## References

- Creating skills spec: [~/.claude/skills/creating-skills/SKILL.md](../creating-skills/SKILL.md)
- Auditing checklist: [~/.claude/skills/auditing-skills/SKILL.md](../auditing-skills/SKILL.md)
