# Evaluations for okf

## Scenario 1: Fresh bootstrap (should-trigger)
**Given** a repo with code but no AGENTS.md, no CLAUDE.md, no wiki directory
**When** user says "/okf" or "bootstrap an OKF wiki here"
**Then**
- [ ] Skill activates, detection routes to `bootstrap`
- [ ] Agent confirms it understands the two canonical concepts before building
- [ ] `wiki/` skeleton created (index.md, log.md), ≤8 pages generated on first pass
- [ ] AGENTS.md created as real file with `<!-- okf:contract v1 -->` block; CLAUDE.md created as relative symlink to AGENTS.md
- [ ] `.okf/lint.py` + `.okf/config.json` + `.okf/last-update.json` created; hooks merged into `.claude/settings.json` (not clobbered)
- [ ] Wiki is git-tracked (`.gitignore` checked/fixed); lint runs clean and its output is shown

## Scenario 2: Update on bootstrapped repo (should-trigger)
**Given** a repo already bootstrapped (contract marker present, wiki + state file exist), with 2 source files changed since `last-update.json.gitHead`
**When** user says "/okf" or "/okf update"
**Then**
- [ ] Detection routes to `update`; no re-bootstrap
- [ ] No-op short-circuit checked first (`python3 .okf/lint.py noop-check`)
- [ ] Docs-impact plan built from the commit-range diff; soft diff budget respected (≤1–2 pages edited)
- [ ] Edits are surgical (stale sentences replaced, no formatting-only churn); log.md appended; state file updated only if wiki content hash changed

## Scenario 3: Legacy wiki migration (should-trigger, edge)
**Given** a repo with `docs/llm-wiki/` containing pages without frontmatter, and a CLAUDE.md that is a regular file with real content
**When** user says "/okf" or "/okf migrate"
**Then**
- [ ] Detection routes to repair/migrate, NOT fresh bootstrap
- [ ] A mapping plan is shown; nothing is moved, deleted, or overwritten without explicit confirmation
- [ ] Existing CLAUDE.md content is absorbed into AGENTS.md before CLAUDE.md is replaced with a symlink (confirmed first)
- [ ] Existing wiki dir is kept as the wiki dir (auto-detect wins over `wiki/` default); frontmatter backfilled

## Scenario 4: No-op short-circuit (should-trigger, edge)
**Given** a bootstrapped repo where the only changes since `last-update.json.gitHead` are inside the wiki dir itself
**When** user says "/okf update"
**Then**
- [ ] `noop-check` reports current; the agent reports "wiki already current" and does NOT rewrite pages or churn metadata

## Scenario 5: Should-NOT-trigger
**Given** any repo
**When** user says "write a README for this project" or "improve the docstrings in utils.py"
**Then**
- [ ] Skill does NOT activate — ordinary documentation work is not knowledge-base bootstrap/maintenance
- [ ] Normal editing proceeds (the AGENTS.md contract, if present, still governs whether findings get persisted)

## Scenario 6: Value bar / lite profile (should-trigger, edge)
**Given** a 10-file utility-script repo with no research/knowledge dimension
**When** user says "/okf bootstrap"
**Then**
- [ ] The value-bar question is asked; lite profile offered (contract + symlink + git guard + bare index, no generated pages, no state machine)
- [ ] Full machinery is NOT installed unless the user insists

## Scenario 7: Rebased anchor (edge — v1.0 P0 regression)
**Given** a bootstrapped repo whose recorded `gitHead` was rebased away
**When** "/okf update" runs `noop-check`
**Then**
- [ ] Reports STALE with a re-stamp instruction — NEVER a false CURRENT

## Scenario 8: Reviewed, no doc impact (edge — v1.0 deadlock regression)
**Given** source changes since the anchor that genuinely don't affect the wiki
**When** the agent completes the docs-impact plan concluding "no impact"
**Then**
- [ ] `state-update --mark-reviewed` advances the anchor; the next `noop-check` is CURRENT
- [ ] A `no-impact` line is appended to log.md

## Scenario 9: Codex session (parity)
**Given** a bootstrapped repo, agent is Codex (no hooks)
**When** Codex does substantial work and commits
**Then**
- [ ] The AGENTS.md contract instructs manual log appends + lint before finishing
- [ ] The git pre-commit hook fires anyway (lint errors block; code-without-wiki warns)

## Scenario 10: Existing hooks framework (edge, safety)
**Given** a repo already using husky (or a set `core.hooksPath`)
**When** "/okf bootstrap" reaches the git-hooks step
**Then**
- [ ] Existing hook setup is NOT clobbered — the okf pre-commit is chained into the existing framework, or skipped with a visible note
