# Evaluations for okf

## Scenario 1: Fresh bootstrap (should-trigger)
**Given** a repo with code but no AGENTS.md, no CLAUDE.md, no wiki directory
**When** user says "/okf" or "bootstrap an OKF wiki here"
**Then**
- [ ] Skill activates, detection routes to `bootstrap`
- [ ] Agent confirms it understands the two canonical concepts before building
- [ ] `wiki/` skeleton created (index.md, log.md), ≤8 pages generated on first pass
- [ ] AGENTS.md created as real file with the current `<!-- okf:contract v3 -->` block; CLAUDE.md is the one-line `@AGENTS.md` import
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

## Scenario 11: Commit-then-stop (edge — 1.3.0 P0 regression)
**Given** a bootstrapped repo with hooks; the agent changes code and COMMITS it without touching the wiki
**When** the session tries to stop
**Then**
- [ ] The Stop gate blocks (commits since the session base count, not only the worktree)
- [ ] A `no-impact` line dated today, or an `Okf-Impact: none` trailer, is the only accepted escape; an old no-impact line is not

## Scenario 12: Codex session with hooks (parity)
**Given** a bootstrapped repo opened in Codex, `.codex/hooks.json` trusted via /hooks
**When** the agent edits a wiki page with apply_patch and later stops with uncommitted code
**Then**
- [ ] The auto-log entry appears (apply_patch payload parsed); the Stop gate fires with exit 2
- [ ] An allowed stop prints `{}` (Codex requires JSON on allow)

## Scenario 13: Subdirectory launch / cd (edge — 1.3.0 P1 regression)
**Given** a bootstrapped repo, Claude launched inside `packages/api/`
**When** the session edits a wiki page and stops
**Then**
- [ ] Hooks still fire (the runner resolves the repo root); nothing silently no-ops

## Scenario 14: Anchor follows normal work (edge — production finding)
**Given** a bootstrapped repo where sessions commit wiki changes but nobody runs state-update
**When** `/okf update` runs weeks later
**Then**
- [ ] `noop-check` lists only uncertified commits (code without wiki), not every path since bootstrap
- [ ] Commits that carried their wiki update advanced the anchor via the post-commit hook

## Scenario 15: A change resolves a status line stated on two pages (production audit, 1.3.5)
**Given** a bootstrapped repo whose wiki says on the obvious page AND on an unrelated page that a feature is refused
(an open blocker), states a count that the feature changes, and lists a never-written page in `index.md`
**When** a normal coding session implements the feature and commits (no `/okf` mentioned)
**Then**
- [ ] Both pages stop claiming the feature is refused; the count on the unrelated page is updated or replaced by a
  reference to its source
- [ ] The dead index entry is fixed (page written, entry removed, or marked `planned`); the pre-commit hook would
  have blocked the wiki commit otherwise
- [ ] Code task done and tests pass

## Scenario 16: Outdated contract (1.3.5)
**Given** a bootstrapped repo whose AGENTS.md carries `<!-- okf:contract v1 -->`
**When** "/okf" runs (update or repair)
**Then**
- [ ] Lint's outdated-contract warning is shown; the contract is refreshed to v3 after a shown diff and
  confirmation (unattended: refreshed, choice logged), keeping the repo's own lines

## Scenario 17: Truth check finds wrong claims lint cannot see (1.4.0)
**Given** a bootstrapped repo where three facts went stale behind an `Okf-Impact: none` commit (lint and noop-check
say CURRENT) and two claims were wrong when written
**When** user says "/okf audit" or "is the wiki still accurate?"
**Then**
- [ ] `claims` sample is taken (the skill's own script when the repo's `.okf/lint.py` predates 1.4.0)
- [ ] Every sampled sentence gets a verdict row; each `wrong` quotes the contradicting line
- [ ] The planted wrong facts that were sampled are reported wrong; no true fact is reported wrong
- [ ] Nothing in the repo changes; fixes are left to `/okf update`

## Scenario 18: Upgrade an older repo (1.4.1)
**Given** a bootstrapped repo whose `.okf/lint.py` is older than the skill (contract v1, no runner, no Codex hooks),
with someone else's uncommitted changes in some files
**When** user says "/okf"
**Then**
- [ ] `.okf/` is upgraded first (lint, runner, githooks; project gates in githooks kept), Claude and Codex hooks
  merged, contract refreshed (unless AGENTS.md holds others' uncommitted work), committed on its own
- [ ] Files with others' uncommitted changes are neither edited nor committed; the skipped steps are listed
- [ ] Then the routed mode runs as usual

## Scenario 19: Refreshing a customized contract keeps the repo's own rules (1.4.2)
**Given** a repo on okf 1.2.3 whose v1 contract block carries repo-specific rules (an evidence protocol)
**When** user says "/okf"
**Then**
- [ ] The contract is refreshed with `refresh-contract`, not by hand; every repo-specific paragraph appears below
  the new block under "Repo-specific rules kept from the previous okf contract"
- [ ] AGENTS.md with uncommitted changes is not refreshed (the command refuses)

## Scenario 20: Someone else's uncommitted work does not trip the Stop gate (1.4.2)
**Given** a bootstrapped repo with uncommitted code changes that predate the session
**When** the session only answers a question (changes nothing)
**Then**
- [ ] The Stop gate allows the stop; nothing is written to the wiki about that work; the work is untouched
- [ ] A new code change made by the session, or a further change to one of those files, still trips the gate
