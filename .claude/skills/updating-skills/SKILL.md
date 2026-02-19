---
name: updating-skills
description: Systematic workflow for modifying existing Agent Skills. Ensures spec compliance, version bumps, changelog updates, and audit pass after every change. Activates when user asks to "update skill", "modify skill", "evolve skill", "bump version", or mentions changing an existing skill. Do NOT use when creating, auditing, or testing skills.
license: MIT
metadata:
  version: "2.0.0"
  author: gradigit
  category: meta-tooling
  updated: "2026-02-07"
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
- [ ] 2. Run current evaluations (baseline)
- [ ] 3. Understand requested changes
- [ ] 4. Classify version bump (major/minor/patch)
- [ ] 5. Make changes following spec
- [ ] 6. Update EVALUATIONS.md (if behavior changed)
- [ ] 7. Bump version in frontmatter
- [ ] 8. Update CHANGELOG.md
- [ ] 9. Audit against checklist
- [ ] 10. Fix any audit issues
- [ ] 11. Present summary to user
- [ ] 12. Push if published (user confirms)

## Reading Current State

Before any changes, read **all** skill files:

```
skill-name/
├── SKILL.md        # Always read first
├── CHANGELOG.md    # Check current version
├── EVALUATIONS.md  # Check existing test scenarios
├── examples.md     # If exists
├── heuristics.md   # If exists
├── reference.md    # If exists
├── README.md       # If exists (published skills)
└── LICENSE          # If exists
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

## Evaluation-First Updates

Decide whether EVALUATIONS.md needs changes:

| Change Type | Update EVALUATIONS.md? | Example |
|-------------|----------------------|---------|
| New feature / capability | Yes — add scenario | Added Python support → add Python triggering + functional test |
| Changed behavior | Yes — update existing scenario | Modified output format → update expected output |
| Bug fix | Maybe — add edge case if gap exposed | Fix crash on empty input → add empty-input scenario |
| Wording / typo only | No | Fixed typo in description |

Run evaluations **before** changes (baseline) and **after** (regression check). Use [testing-skills](../testing-skills/SKILL.md) for execution.

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

### Evaluations
- [ ] EVALUATIONS.md present and up to date
- [ ] New/changed behavior has matching scenario
- [ ] should-NOT-trigger scenarios still valid

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
1. Read all files: SKILL.md, CHANGELOG.md, EVALUATIONS.md, examples.md, heuristics.md, README.md, LICENSE
2. Run current evaluations (baseline — all pass)
3. Changes needed: Add Python screening patterns
4. Version bump: minor (new capability) → 4.4.0
5. Make changes in SKILL.md, heuristics.md, examples.md
6. Update EVALUATIONS.md (add Python triggering + functional scenario)
7. Update frontmatter version to "4.4.0"
8. Add CHANGELOG.md entry for 4.4.0
9. Audit all files for consistency
10. Fix any stale version refs (examples.md commonly has old versions)
11. Present diff summary
12. Push to GitHub

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

Current version: 2.0.0. See [CHANGELOG.md](CHANGELOG.md) for history.

## References

- Creating skills spec (v4.0.0): [creating-skills](../creating-skills/SKILL.md)
- Auditing checklist (v2.0.0): [auditing-skills](../auditing-skills/SKILL.md)
- Testing evaluations: [testing-skills](../testing-skills/SKILL.md)
