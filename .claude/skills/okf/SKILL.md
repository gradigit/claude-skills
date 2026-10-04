---
name: okf
description: Bootstraps and maintains the agent knowledge base (OKF / Karpathy LLM-wiki) in a repo, and is the only correct way to change that wiki's structure: use it whenever the user asks to bootstrap, set up, create, migrate, repair, lint, audit or update a wiki or knowledge base for agents, asks whether the wiki is up to date or rotting, or mentions OKF, llm-wiki, the AGENTS.md contract or `.okf/`. Auto-detects repo state and routes to bootstrap (value-gated, full or lite), update, lint, audit, migrate or repair; installs the AGENTS.md contract, Claude Code and Codex hooks, git hooks, a git-tracking guard and a stdlib lint. Never hand-roll a knowledge base instead of using this skill. Do NOT use for ordinary documentation work (READMEs, docstrings, API docs) that does not involve the agent-maintained knowledge base.
argument-hint: "[bootstrap|update|lint|audit|migrate|repair]"
version: "1.4.0"
---

# OKF — bootstrap & maintain an agent knowledge base

Sets up and maintains a durable, agent-facing markdown wiki in the current repo: Karpathy's LLM-wiki pattern in Google's Open Knowledge Format. Works from Claude Code and Codex with the same files, contract and hooks; every mechanism is plain files + python3 stdlib + git. House authoring rules (evidence-backed, REQUIRED before writing pages): [reference.md](reference.md). Fetch the canonical sources only if genuinely unfamiliar: Karpathy gist `gist.github.com/karpathy/442a6bf555914893e9891c11519de94f`, OKF spec `github.com/GoogleCloudPlatform/open-knowledge-format/blob/main/SPEC.md` (v0.2; reference.md §1 summarizes what this skill accepts).

## Workflow

- [ ] 1. Detect repo state (§Detection) → route to a mode
- [ ] 2. Run that mode's flow (§Bootstrap / §Update / §Lint / §Audit / §Migrate / §Repair)
- [ ] 3. Verify: lint passes, wiki git-tracked, contract + CLAUDE.md delegation + hooks intact
- [ ] 4. Report visibly: show lint output, list pages touched, state what was skipped

An explicit argument overrides detection: `/okf bootstrap|update|lint|audit|migrate|repair`.

## Enforcement model — three layers, named honestly

1. **Structure guard** (`.okf/lint.py`): well-formedness and rot signals — frontmatter, links, index entries for missing pages, orphans, git-tracking, citation *presence*, passed `stale_after`. It cannot measure insight.
2. **Write-forcing and nudges** (deterministic, zero tokens). The **Stop gate** (Claude Code and Codex hooks) blocks ending a turn while code changed *this session* — uncommitted **or committed since the session started** — without a wiki page or log entry; the deliberate escapes are a `no-impact` log line dated today or an `Okf-Impact: none` commit trailer. `raw/` captures never satisfy it. The **git hooks** lint staged pages and refuse a wiki commit whose `index.md` lists a page that is not in it (errors block), warn on code-only commits, and advance the review anchor when a commit touches the wiki. **CI** re-runs the lint at merge. Reach, stated plainly: Claude and Codex hooks travel with the repo (`.claude/settings.json`, `.codex/hooks.json`) and load after the runtime's one-time trust step; git hooks and the review anchor are per-clone until `/okf` runs there; the SessionStart pointer says so when they are missing. Claude Code overrides a Stop hook after 8 consecutive blocks, so the gate is a strong nudge, not a guarantee. Under an agent with no hooks the contract alone carries the obligation.
3. **Guidance** (AGENTS.md contract + [reference.md](reference.md)): where quality lives — model judgment by design.

**Trust boundary.** `.okf/` (lint, runner, git hooks) is repo-controlled code that runs on every edit, stop and commit. Review it like `husky/` or CI config; on a clone you do not trust, run `python3 ~/.claude/skills/okf/scripts/okf_lint.py lint` instead. The SessionStart hook warns when the repo copy differs from the installed skill copy at the same version.

## Core invariants (non-negotiable)

1. **AGENTS.md is the real file; CLAUDE.md delegates to it.** Default: a one-line CLAUDE.md containing `@AGENTS.md` (Claude Code's documented import; works on Windows and in Cowork). A relative symlink is an opt-in for all-POSIX teams. Never duplicate content.
2. **Pointer, not inline.** AGENTS.md carries a short contract pointing into the wiki; it routes, it never summarizes (LLM-generated overviews are redundant with existing docs and cost tokens: ETH arXiv:2602.11988).
3. **Single writer.** The main agent is the sole writer of the wiki; subagents inspect and report only.
4. **Generate minimally; pages accrete.** First pass ≤8 pages; no architecture dumps.
5. **The wiki must be git-tracked** (the #1 observed rot cause). A bare `!/docs/llm-wiki/**` under a blanket `docs/` ignore does nothing; re-include parents: `docs/*` then `!docs/llm-wiki/`; verify with `git check-ignore -v <wiki>/index.md`.
6. **Copy-first migration.** Never move, delete or overwrite existing docs or agent files without a shown plan and explicit confirmation.
7. **Retrieval is files + grep + index.md.** No embeddings, BM25, rerankers or alias indexes by default (reference.md §7 has the one sanctioned opt-in and the honest cost note).
8. **Mechanize what can be mechanized; be honest about the rest.** Log appends, lint, gates and the anchor fire from hooks and scripts. Knowledge quality cannot be mechanized.

## Detection (run first, always)

Priority order, first match wins. Auto-detect the wiki dir among `wiki/`, `docs/llm-wiki/`, `docs/wiki/`, `llm-wiki/`, `openwiki/` (a dir with an `index.md`). Default for NEW bootstraps: `wiki/`. An existing healthy wiki dir always beats the default — never relocate a working wiki.

| # | State | Signals | Route |
|---|-------|---------|-------|
| 1 | Fully bootstrapped | AGENTS.md contains `<!-- okf:contract` AND CLAUDE.md delegates to it (symlink, `@AGENTS.md` import, or a file whose content is just `AGENTS.md`) AND `<wiki>/index.md` + `.okf/config.json` exist (config.json is the bootstrap-completed marker) | `update` (or `audit` if the user asked for status or whether the wiki is still accurate) |
| 2 | Partial / drifted | Wiki exists but contract, delegation, `.okf/`, or hooks missing; or CLAUDE.md and AGENTS.md are diverged regular files with real content | `repair` |
| 3 | Legacy / foreign wiki | `docs/llm-wiki/` without frontmatter, `openwiki/`, `droid-wiki/`, flat dated `research-*.md`, or ANY substantial pre-OKF knowledge dir (`architect/`, `research/`, `notes/`, dated reports) | `migrate` |
| 4 | Nothing | none of the above | `bootstrap` |

Always also check: `git rev-parse --show-toplevel` succeeds (no git → bootstrap must `git init` first) and the wiki path is tracked (`git check-ignore`, `git status --porcelain --ignored`). Namespace note: other tools also use `.okf/` (okf-skills' bundle dir) and `/okf`; if `.okf/` exists without `lint.py` + `config.json`, it is not ours — stop and ask.

## Bootstrap

1. **Value gate first.** Does this repo clear the wiki's cost bar? Knowledge-dense, investigative, or long-lived multi-session repos do; a small script repo may not — offer the **lite profile** (step L) or decline with reasons. Ask ≤3 questions total (value, capture depth, wiki dir if ambiguous). **Unattended runs:** self-arbitrate each question with the most reasonable assumption and record every choice in DECISIONS.md at the repo root (git-track it — an untracked root file pins noop-check to STALE). Attended runs record routing choices there too.
2. **Concept gate.** Confirm the two canonical concepts are understood ([reference.md](reference.md) §1 suffices offline).
3. **Survey** (read-only subagents allowed; single writer enforced): structural pass (README, manifests, entrypoints, CI), then semantic pass (domain, key flows, sources to ingest).
4. **Plan-then-delete.** Write `<wiki>/_plan.md` (page list → evidence → open questions); delete it before finishing. Mandatory for bootstraps and multi-file migrations; skippable for ≤3-file migrations with the skip logged in DECISIONS.md.
5. **Generate minimally** per invariant 4: root `index.md` (navigational, ≤200 lines; each entry copies the page's `description` **verbatim** and points at a page that exists — a planned page says `planned` on its line), a flat layout until ~7 pages, every `description` leading with its distinguishing terms (never "How/Why/When/This page…"), `log.md` (an event log, not a page catalog), and only the pages the survey justifies (≤8). Frontmatter per reference.md; no inline YAML comments. **Evidence durability:** newly fetched material goes verbatim under `<wiki>/raw/` and is `git add`ed; a cited pre-existing file that is UNTRACKED (and not ignored by policy) is copied — never moved — into `<wiki>/raw/` or tracked. Cited evidence must survive `git clean`.
6. **Wire the contract.** Create or append to AGENTS.md from [templates/agents-contract.md](templates/agents-contract.md) (`{WIKI}` replaced; preserve every non-OKF section, deduping prose the contract now covers). CLAUDE.md, four cases: absent → write the one-line `@AGENTS.md` import (or `ln -s AGENTS.md CLAUDE.md` if the user prefers symlinks); regular file with content → show it and SPLIT: instruction-shaped parts (how to work here) are absorbed into AGENTS.md; **knowledge-shaped parts (domain facts, findings) go to wiki pages, never into AGENTS.md** (invariant 2 outranks this step); then replace with the import (confirm first); already a symlink/import to AGENTS.md → done; symlink to anything else → show the target and do NOT retarget without explicit confirmation.
7. **Install enforcement.**
   - Copy `scripts/okf_lint.py` → `.okf/lint.py`, `templates/okf-py.sh` → `.okf/okf-py.sh`, and every file in `templates/githooks/` → `.okf/githooks/` (`chmod +x`). Write `.okf/config.json`: `{"wikiDir": "<wiki>", "profile": "full", "typeVocab": [...]}`.
   - **Git hooks (agent-agnostic, per clone).** Route by what exists, IN THIS ORDER; record the choice in DECISIONS.md:
     0. `git config --global|--system core.hooksPath` set → **never set a local core.hooksPath** (it would shadow the user's global hooks: secret scanners, git-lfs). If the global framework documents a per-repo chain point (e.g. `.git/hooks-local/`), install there a pre-commit that runs `sh .okf/okf-py.sh pre-commit` (and post-commit/post-rewrite likewise) and VERIFY it fires; no chain point → skip git hooks with a loud note and lean on CI.
     1. A LOCAL `core.hooksPath` is already set (e.g. `.githooks/`) → chain from that directory's hooks with confirmation; never overwrite.
     2. `.git/hooks/` has ANY native non-sample hook → install into `.git/hooks/pre-commit|post-commit|post-rewrite` directly (chaining into an existing file with confirmation); do NOT set core.hooksPath (it would orphan the other native hooks).
     3. husky/lefthook config present → chain into that framework or skip with a visible note.
     4. Clean → `git config core.hooksPath .okf/githooks`.
     Project gates belong in `.okf/githooks/pre-commit.local`; the template runs it first and survives re-copies.
   - **Claude hooks (scripted merge — never hand-edit settings.json):** render [templates/hooks-settings.json](templates/hooks-settings.json) to `.okf/hooks-fragment.json`, then `python3 .okf/lint.py install-hooks .okf/hooks-fragment.json`. It merges only `hooks.*`, is idempotent, upgrades older okf entries, honors `"hooksDisabled": ["Stop"]` in config (the way to turn the Stop gate off — never delete the block by hand), backs up under `.okf/`, and refuses invalid JSON.
   - **Codex hooks:** render [templates/hooks-codex.json](templates/hooks-codex.json) to `.okf/hooks-codex-fragment.json`, then `python3 .okf/lint.py install-hooks .okf/hooks-codex-fragment.json --target codex`. Tell the user: run `/hooks` once in Codex to trust the three entries; `codex exec` needs `--dangerously-bypass-hook-trust`.
   - **CI backstop:** copy [templates/ci-okf-lint.yml](templates/ci-okf-lint.yml) → `.github/workflows/okf-lint.yml` (or adapt). It matters MOST where git hooks could not be installed (routing 0/3).
   - Git-tracking guard per invariant 5.
8. **Lint, commit, stamp (this order).** Append the bootstrap entry to `log.md`; add `.okf/last-update.json`, `.okf/session-head`, `.okf/hook-seen.json`, `.okf/hooks-fragment.json`, `.okf/hooks-codex-fragment.json`, `.okf/log.lock`, `.okf/*.bak` to `.gitignore` (per-clone state, deliberately untracked); `python3 .okf/lint.py lint` and fix errors (the pre-commit hook would block them); `git add` wiki, AGENTS.md, CLAUDE.md, `.okf/`, `.claude/settings.json`, `.codex/hooks.json`, DECISIONS.md; make the bootstrap commit (the post-commit hook stamps the anchor; if hooks were skipped run `python3 .okf/lint.py state-update`); show the final lint output.

**L. Lite profile** (repos below the value bar): contract + CLAUDE.md delegation + git-tracking guard + `.okf/` (lint, runner, config **with `"profile": "lite"`**) + a bare `<wiki>/index.md` + `log.md`. No generated pages, no state machine, no CI, **no hooks** (say so). `/okf` upgrades lite→full on request.

## Update (the maintenance loop)

1. **No-op short-circuit:** `python3 .okf/lint.py noop-check`. `CURRENT` → report "wiki already current," stop. `STALE` lists **uncertified commits** (code touched, no wiki, no `[no-impact]`/`Okf-Impact: none` marker) and uncommitted paths — commits that already carried their wiki update are not listed. `NO-STATE` (fresh clone) → `state-update --from-last-wiki-commit`, then re-run. It fails toward STALE on any git uncertainty; trust it.
2. **Diff per commit:** `git log <anchor>..HEAD --stat` for the listed commits; `git diff --name-status HEAD` for the worktree.
3. **Docs-impact plan:** changed source → affected wiki page → edit → why; include any claim a truth audit (§Audit) reported wrong. No impact → no edit.
4. **Soft diff budget:** <5 source files changed → edit ≤1–2 pages; >3 pages needing edits demands re-justification. Budget by commit when the list is long. No-op updates are valid.
5. **Surgical edits:** replace the stale sentence; no formatting-only edits; bump the page `timestamp` (or `generated.at`) when meaning changes. **Sweep the whole wiki, not just the page you opened:** when a change resolves a status line ("open blocker", "not supported", "refused", "out of scope") or changes a count or value, `grep -rn '<feature>\|<old value>' <wiki>/` and fix every page that states it. In the 2026-10 production audit, status lines and counts on pages nobody reopened were most of the wrong claims ([reference.md](reference.md) §6).
6. **Rename safety:** renaming a page rewrites ALL inbound relative links in the same change.
7. **Contradictions:** newest verified evidence wins; note supersessions in the page and `log.md`; root index ≤200 lines.
8. **Close out:** update per-dir `index.md` if navigation changed; `python3 .okf/lint.py lint` (show output; an outdated-contract warning is fixed per §Repair step 2); commit the wiki changes — the post-commit hook advances the anchor. If you reviewed the diff and it truly had no doc impact: append a dated `no-impact` log line (or use the trailer) and `python3 .okf/lint.py state-update --mark-reviewed`.

**Ingest variant** (new source material): capture raw (and `git add` it) → synthesize into affected pages → cross-link → index if nav changed → log. Same budget discipline.

## Lint

`python3 .okf/lint.py lint` — deterministic, repo-local, stdlib-only; from a subdirectory use `python3 "$(git rev-parse --show-toplevel)/.okf/lint.py" lint`. Errors (exit 1): missing/malformed/placeholder frontmatter, multi-line scalars in required fields, absolute internal links, `index.md` entries for pages that do not exist (a line saying `planned` downgrades to a warning), gitignored wiki or wiki files, cited local evidence that is untracked or gitignored, non-git repo, missing root index. Warnings: unknown `type`, forward/broken links in pages, an AGENTS.md contract older than the template, orphans (log.md links don't count), missing per-dir index, thin pages, missing citations (`## Sources`, `source:` or v0.2 `sources:`), untracked files (named), passed `stale_after`, >200-line root index, duplicate descriptions, symlinked pages, descriptions opening with a generic word, index entries that do not reuse a page's description verbatim, subdirectories before ~7 pages. The write-time hook surfaces the description and index checks while you author, whichever tool wrote the page (Edit, Write, apply_patch or a shell command): fix them then. Fix errors now; triage warnings visibly. `--help` prints usage; `claims` is the truth-check sampler (§Audit).

## Audit (read-only)

Report, change nothing.

1. **Structure:** detection state, lint summary, `noop-check` result, page/dir counts, log.md recency, hook presence (`.claude/settings.json`, `.codex/hooks.json`, `git config core.hooksPath`, CI workflow), anchor age, git-tracking status. End with a prioritized repair list.
2. **Truth check** — whether the pages are still true, which lint cannot see. In a production audit, 4.3% of checkable claims were wrong, nearly all exact numbers or status lines.
   1. `python3 .okf/lint.py claims` samples 12 sentences (`--n` only if the user asks for more; `--seed` resamples), weighted toward status lines, numbers and code references, each with its cited sources. A repo whose `.okf/lint.py` predates 1.4.0 has no `claims`: run the skill's own `scripts/okf_lint.py claims` from the repo root instead (audit never upgrades `.okf/`).
   2. **Check every sampled sentence** against the repository per [reference.md](reference.md) §11 — the wiki is never evidence; code, config, tests, data, `raw/` captures and git history are. "Not checked" is not a verdict: the hard-to-check sentences are where wrong ones hide. Verdicts: **supported** (cite the confirming line) · **wrong** (all or part of it is contradicted: quote the contradicting line and say whether it went stale or was never true) · **unconfirmed** (checkable, but you found no evidence either way; say what you searched) · **outside the repo** (a decision, rationale or external fact the repo cannot confirm — expected, not a defect). In a large repo, split the sentences across read-only subagents (Claude Code: Agent tool; Codex: spawn_agent); they report and never edit (invariant 3).
   3. **Second look on every "wrong":** open the evidence again and quote the exact contradicting line (or have a fresh subagent, not told your verdict, re-check it). No quote, no "wrong" — it becomes unconfirmed. In the production audit a first pass's flags held up 42 of 72 times; its "supported" verdicts 96 of 96.
   4. Report one row per sampled sentence — `| page:line | claim | verdict | evidence (quoted for "wrong") | suggested fix |` — then the counts per verdict, stating that it is a sample. Fixes go through `/okf update` (Docs-impact plan), never through the audit.

## Repair (partial / drifted — confirmation-gated)

1. Run `audit` first and show the gap list. Confirm scope before changing anything.
2. **Reconcile AGENTS.md/CLAUDE.md drift:** show both; merge the union of non-duplicate content into AGENTS.md; a contract block whose marker version is OLDER than the template's (`<!-- okf:contract v1 -->` vs the template's v3; lint warns) is **outdated — show the diff and, with confirmation, refresh it to the template, carrying over lines the repo added**; a block at the current version whose text differs is a **customization — report it, do not refresh it**; then, with confirmation, replace CLAUDE.md with the delegation.
3. Add missing pieces in dependency order: `.okf/` (lint, runner, config, githooks) → git-tracking fix → git hooks → Claude and Codex hooks merge → missing `index.md`/`log.md` (thin, from existing pages only). Existing well-formed pages stay byte-identical.
4. Frontmatter backfill for existing pages: propose `type`/`title`/`description` per page as a shown plan; apply on confirmation.
5. Lint, commit, stamp; show output.

## Migrate (absorb existing docs — copy-first, confirmation-gated)

1. Inventory existing knowledge artifacts (legacy `docs/llm-wiki/`, `openwiki/`/`droid-wiki/` output, flat dated research files, ADRs).
2. Present a mapping plan: source file → target wiki page + `type` → synthesized or verbatim. **Nothing moves, is deleted, or overwritten until the user confirms** (unattended: copy-first, delete nothing, log the choice).
3. Copy content in with frontmatter; convert `[[wikilinks]]` to relative links; park full-fidelity originals under `<wiki>/raw/` when they are external or dated; keep an existing healthy wiki dir as the wiki dir. **Evidence durability check:** after any `.gitignore` fix, run `git check-ignore -v` on every file the pages cite (ADRs, docs, data); a cited file that is still ignored or untracked is re-included (`!docs/adr/`) or copied — never moved — into `<wiki>/raw/`. Lint warns on every cited local file that is not tracked.
4. Then run Bootstrap steps 6–8. Originals are archived or removed only on explicit confirmation.

## Codex parity

Identical files, contract and hooks. `.codex/hooks.json` carries the same SessionStart pointer, PostToolUse auto-log (parses `apply_patch`) and Stop gate; trust them once with `/hooks`. Invocation: the skill is installed at `~/.codex/skills/okf` as a copy — re-sync it after skill updates (`cp -r ~/.claude/skills/okf ~/.codex/skills/`); read this SKILL.md and follow it directly.

## Self-Evolution

Update when: (1) the user corrects a flow; (2) OKF spec moves past v0.2 or renames reserved files (config makes reserved names parameters); (3) lint changes — keep `scripts/okf_lint.py` and repo copies in sync (`lintVersion` is stamped in state files; re-copy on the next `/okf` run per repo); (4) a production repo patches `.okf/` locally — upstream it.

Current version: 1.4.0 — see [CHANGELOG.md](CHANGELOG.md) for the production evidence behind each change.
