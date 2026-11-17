# OKF authoring playbook — house rules, evidence-backed

Read this before writing wiki pages. Every rule is grounded in benchmarks or verified
adopter evidence; rules marked ⚖ were revised after adversarial review (2026-07-08,
two rounds: priors challenge + 6-reviewer panel). The full evidence trail lives in the
user's okf research project (see CHANGELOG.md for pointers).

## 1. Frontmatter (leaf pages)

```yaml
type: reference
title: OKX Withdrawal Rate Limits
description: Per-endpoint withdrawal rate caps and the 429 backoff contract for OKX v5.
tags: [okx, rate-limits]
source: https://www.okx.com/docs-v5/
timestamp: 2026-07-08
status: verified
```

Field rules (`type`, `title`, `description` REQUIRED; the rest optional):
- **`description` is the single highest-leverage field** — the only one with a measured
  retrieval lift (+5.4pp hit@1 at 515 docs). ONE single-line sentence, distinguishing
  terms front-loaded. Never a truncated first paragraph. ⚖ No folded/literal scalars
  (`>` / `|`) — the lint rejects them rather than silently corrupting.
- ⚖ **No inline `#` comments inside the YAML block** — they pollute parsed values
  (found by the review panel in this skill's own v1.0 template); lint warns when it
  strips one. If a value legitimately contains ` #` (e.g. "see issue #157"), QUOTE
  the whole value. Guidance lives in prose or HTML comments *below* the frontmatter.
- **Flat keys only. Never `name:`, never `metadata:` nesting** — the file *path* is the
  concept ID; that is what makes relative links work.
- ⚖ **`type` is free-text with a suggested vocabulary** (fixed enums were overfit):
  `reference`, `concept`, `decision`, `method`, `case-study`, `asset`, `idea`,
  `hypothesis`, `evidence`, `index`. Lint warns (never errors) on unknown types; a repo
  may customize the suggested vocab in `.okf/config.json` (still warn-only by design).
- `status: verified | unverified | draft` — flip from `draft` once sourced.
- Reserved files (`index.md`, `README.md`, `log.md`, `hypotheses.md`,
  `evidence-matrix.md`, `_plan.md`) are exempt from leaf-page frontmatter requirements.
- **OKF v0.2 (2026-07) shapes are accepted** alongside the legacy ones above: `generated: { by, at }`
  (supersedes `timestamp`), nested `sources:` lists with `[^id]` footnotes (supersede `source:` +
  `## Sources`), `verified: [{ by, at }]`, `status: draft | stable | deprecated`, and `stale_after`
  (a passed value is a lint warning). Prefer v0.2 fields on new pages; lint never errors on either.
  Declared divergences from the spec: internal links stay relative (bundle-absolute `/x.md` breaks
  renderers — OKF #48/#157) and `raw/` is the capture dir (spec convention: `references/`).

## 2. Granularity — one answerable unit per file

A page fully answers ONE question. Litmus test: can you write one distinguishing
`description` sentence for it? Needs two → split. Can't write one → too thin, merge.
Mega-pages lost the benchmarks; per-concept files won; stub sprawl is the opposite
failure (thin-page lint warning).

## 3. Naming & layout

- Filenames: kebab-case slug of the title. Descriptive names are load-bearing
  (opaque names measurably lost). No dates/versions in filenames.
- Directories group by domain; subdirectory only past ~7–10 pages; every topic
  directory gets an `index.md`.
- Default tree (dir name configurable in `.okf/config.json`; upstream naming is
  churning, so reserved names are parameters, not constants ⚖):

```
wiki/
  index.md          # root catalog — thin, navigational, ≤200 lines
  log.md            # append-only, newest-first: ## [YYYY-MM-DD] kind | Title
  raw/              # full-fidelity captured sources, verbatim (capture-then-synthesize)
  <topic>/index.md  # per-directory catalog: [Title](file.md) — description
  <topic>/<answerable-unit>.md
.okf/               # machine layer: config.json + lint.py + githooks/ are TRACKED;
                    # last-update.json is per-clone state, deliberately GITIGNORED
                    # (fresh clones/worktrees re-anchor with one full pass)
```

## 4. index.md — progressive disclosure

Read-first catalog; the reason agents navigate without retrieval infra. One line per
entry: `[Title](file.md) — description` (reuse the page's own description). Dirs of
dirs list `## Sections`; dirs of leaves list `## Pages`. Update the index in the same
change as any page add/remove. Root index stays ≤200 lines; push detail down.
An index entry asserts that the page exists: lint ERRORS on an entry whose page is missing,
and the pre-commit hook refuses a wiki commit that contains one. A page you mean to write
later goes on a line that says `planned` (lint then only warns). Production: an index listed
a never-written page for two months while the old warning was ignored.

## 5. Linking — relative paths build the graph

- Internal links are ALWAYS relative markdown paths. Never absolute paths (broken
  rendering — OKF issues #48/#157), never external URLs for internal concepts, never
  `[[wikilinks]]`.
- Forward links to not-yet-written pages are sanctioned inside page bodies (they mark
  gaps); lint warns so they eventually get written. In an `index.md` they must say
  `planned` (§4).
- No orphans: every page gets an inbound link from its `index.md` at minimum
  (⚖ log.md mentions don't count — the lint checks the real navigation graph).
- **Rename = rewrite all inbound links in the same change** (path-as-identity breaks
  silently under reorganization — OKF #120).

## 6. Citations & evidence discipline

- Every claim cites a source: `[S1]` inline markers → `## Sources` block
  (`[S1] Title — URL (accessed YYYY-MM-DD)` / `[S2] Local: path`). Unverified claims
  tagged `UNVERIFIED`. ⚖ Lint now checks citation *presence* (a `## Sources` section
  or `source:` field on every non-draft leaf page) — presence is checkable; quality
  remains your job.
- Separate inference from evidence: `hypotheses.md` vs `evidence-matrix.md`
  (investigative repos). Delete or fill abandoned placeholder files — lint flags them.
- Capture-then-synthesize: full-fidelity raw material into `raw/` verbatim BEFORE
  synthesis ("did you actually save every piece?" is the recurring failure).
- Contradictions resolve recency-wins: newest verified evidence supersedes; note the
  supersession on the page and in `log.md`.
- **The code wins.** When a page and the repository disagree, agents act on the repository and
  fix the page (contract v4). Without that rule they follow the file: agents obeyed a stale
  instruction file over the code in 90.1% of choices, and one sentence giving the code precedence
  raised code-following from 4.2% to 91.4% (arXiv 2610.30571, 2026-10, synthetic projects).
- **Pages compress; exact values come from the cited source.** Before acting on or quoting an
  exact figure, date, name, list or wording, readers open the source the page cites (contract v5).
  In a blinded 24-question test on a production repo (2026-11, one repo, one answering model),
  answers from the wiki alone matched answers from the rest of the repo where both held the
  answer, at about 1.6× fewer cost-weighted tokens, but lost points on 4 of 16 shared questions
  by dropping specifics (a named person, a decision date, exact wording), and lacked exact
  primary detail (lists, fees, recency windows) altogether. Wiki-only answers said "not found"
  instead of guessing, so the fix is a reading rule, not more page text.
- **Volatile facts carry their provenance.** An exact count, range, size or version
  ("63 items", "30,400–44,272 ticks", "schema v2") is written with the commit or date it
  was true at, or the command that reproduces it ("69 items in `data/items.json` as of
  commit a1b2c3d", "`python3 tools/count_items.py`"). Otherwise state it qualitatively. A
  reader can then re-check it instead of trusting it.
- **Status lines are claims about the present.** "Open blocker", "not supported",
  "refused", "out of scope", "gate unmet" go stale the moment the work lands. When a
  change resolves or alters one, or changes a count, grep the whole wiki for the feature
  name and the old value and fix every page that states it, not only the page you are
  editing. Evidence: the 2026-10 production audit (4 repos, 600 claims checked against
  the code) found 4.3% of checkable claims wrong, almost all exact numbers or status
  lines. One commit implemented a feature and updated that feature's page, but left
  "<feature> stays refused" and an old count on a design page nobody reopened.
  Eval note (2026-10-03, Claude Sonnet 5.5): with or without these two rules the executor
  swept a 19-page wiki and fixed an unlinked status line 12/12, and it wrote new counts
  without provenance either way. They stay here as authoring rules, not in the per-session
  contract, until an eval shows they change behaviour.

## 7. Retrieval — files + grep + index.md ⚖

Default: NO retrieval infrastructure. No embeddings, BM25/FTS5, rerankers, or
pre-generated alias/keyword indexes — benchmarked net-neutral-to-negative on
keyword-rich corpora (the alias layer cost 6.4M tokens for negative value). The free
lever for fuzzy queries is query-time: *extract the distinctive identifiers from the
question and grep the tree for them*.

Honesty notes (from the adversarial review):
- Those benchmarks used keyword-rich API docs and frontier models. For very large
  (1000s of pages) or low-keyword prose corpora, grep degrades — the one sanctioned
  escape hatch is an external search layer (e.g. qmd, BM25+vector+rerank MCP) as a
  **manual, documented opt-in**. Never installed by default.
- Agentic wiki navigation measured ~28k tokens / ~10s per deep query on a 515-doc
  corpus. That is the cost of quality. If a repo won't earn that back, use the lite
  profile (contract + bare index, no generated pages) — see SKILL.md §Bootstrap.

## 8. Generation & maintenance discipline

- **Do not auto-generate verbose wikis.** ETH arXiv:2602.11988 (v3, 2026-09-29): context files
  "do not generally improve task success rates" while "increasing inference cost by over 20%";
  instructions in them are "well followed", repository overviews are "not helpful". (Corrected
  2026-11: this line used to cite v1's "−3%" — v1 also reported +4% for developer-written files —
  and a quote, "stale structural references actively mislead", that appears in no version.)
  Bootstrap small (≤8 pages); pages accrete from real ingests.
- **Never agentically re-write body prose you already have** (~20× token cost
  measured). Convert deterministically; spend tokens on `description` + `type` only.
- **Soft diff budget** (from openwiki): <5 source files changed → edit ≤1–2 pages.
  Surgical edits; no formatting-only churn; no-op updates are valid.
- **No-op short-circuit**: `python3 .okf/lint.py noop-check` before any update pass.
  ⚖ It fails toward STALE on every git uncertainty (rebased anchors, renames,
  zero-commit repos) — a false "CURRENT" was the worst defect the panel found in v1.0.
  Since 1.3.0 it reports *uncertified commits* (code touched, wiki untouched, no
  `[no-impact]` subject or `Okf-Impact: none` trailer), not flat paths: in production the
  anchor had frozen at bootstrap in 3 of 4 repos and the flat list reached 285 paths.
- **The anchor advances itself, honestly**: the `post-commit` git hook stamps when a commit
  touches the wiki and every commit since the anchor is certified (1.3.0–1.4.3 stamped on any
  wiki-touching commit, silently certifying earlier code-only commits — a false CURRENT); `post-rewrite` follows amends and rebases; a fresh clone anchors with
  `state-update --from-last-wiki-commit`. `--mark-reviewed` remains for reviewed no-impact diffs.
- **State stamps are churn-guarded**: `state-update` refuses to rewrite when the wiki
  hash is unchanged (the hash excludes `raw/`); `--mark-reviewed` advances the anchor after a
  reviewed no-doc-impact diff; `--auto` is what the post-commit hook uses.
- **log.md**: auto-entries (`auto |`) come from the PostToolUse hook (Claude Code and Codex)
  — leaf wiki pages only, lock-guarded, one dated block per day, inserted below any preamble
  prose and above the newest entry. Hand entries are for meaningful events (`ingest |
  decision | migration | no-impact`), newest first, greppable. A `no-impact` line only
  excuses the Stop check when dated today and added during the session (production showed stale and shipped-feature
  no-impact lines; 21% of one repo's log). Under hookless agents, append hand entries yourself.
- **Single writer**: orchestrator writes the wiki; subagents inspect and report only.
- **Plan-then-delete**: `_plan.md` during bootstrap/big ingests; deleted before done.

## 9. Enforcement — three layers, named honestly ⚖

| Layer | What it actually does | Fires | Platform |
|---|---|---|---|
| **Structure guard** — `.okf/lint.py` | well-formedness + rot signals (never knowledge quality) | on demand, hooks, pre-commit, CI | any |
| **Structure guard at commit** — git pre-commit (`.okf/githooks/`) | blocks malformed STAGED wiki pages and wiki commits whose `index.md` lists a page not in the commit; WARNS (never blocks) on code-without-wiki commits — a nudge, not forcing | every commit, any agent or human | any (git) |
| **Structure guard at merge** — CI lint (`ci-okf-lint.yml`) | the same `lint` at PR time; catches malformed pages on fresh clones — it cannot detect a skipped write | PR/push | any (CI) |
| **Stop check** — `lint.py stop-gate` (advises by default; `"stopGate": "block"` blocks) | reports code changed THIS SESSION (uncommitted, or committed by the session and not already on a remote; state keyed by `session_id`) without a wiki page or log entry; uncommitted paths recorded at SessionStart and unchanged since are ignored; escapes: a `no-impact` line added this session and dated today, or an `Okf-Impact: none` trailer; `raw/` never counts; honors `stop_hook_active` (so a blocking gate blocks once per stop); fails closed on a git timeout | deterministic, zero tokens | Claude Code + Codex |
| **Accelerators** — SessionStart pointer (records the session base), PostToolUse quick-lint (via `additionalContext`, the only PostToolUse output that reaches the model) + auto-log, fired for wiki files written by ANY tool including shell heredocs, post-commit anchor stamp | re-inject context; catch frontmatter slips at write time; keep the anchor current | deterministic | Claude Code + Codex (git hooks: any) |
| **Guidance** — AGENTS.md contract + this playbook | the only layer that carries *quality* | every session (agents read natively) | any |

Evidence, revised 2026-11. This section used to open "instructions alone reliably fail (Cline
memory-bank: 'claims to update but never writes files')"; Cline issue #1911 is a 2025 tool-call bug
(the update was printed in chat instead of written), not evidence about instructions. The fleet
review (five production wikis, 192 Codex transcripts) found the opposite: under Codex with no okf
hooks, 115 of 115 code-changing turns also wrote the wiki; the blocking gate's measured effects were
placeholder `no-impact` lines and an unsatisfiable gate on a shared worktree; the only real user nags
(4 in 657 messages) were about knowledge from conversation, which a diff-watching gate cannot see.
Hence: the contract carries the obligation, the Stop check advises by default, and the effort goes
into durability (commit warnings), read-time correction (the code wins) and the truth check. The v1.0
review's warning still stands: calling shape-checks "enforcement of knowledge" is Goodhart bait. Declared v1 cut ⚖: no PreCompact transcript
snapshot (conflicts with minimal-generation; the SessionStart `compact` matcher
already re-injects the pointer after compaction). Production evidence (1 Claude + 148 Codex
threads, 2026-07..09): the pre-commit warning was ignored 8/8 times and the v1.2 Stop gate
was satisfied only by `no-impact` lines — hence the session-scoped gate and dated escape.

**Trust boundary.** Everything under `.okf/` is repo-controlled code executed by the hooks on
every edit, stop and commit. Review it as you review `husky/` or CI; the runner `okf-py.sh`
never lets uv read a repo `.python-version`, never downloads an interpreter, and falls back
to bare `python3` — a repo-shipped `.python-version` once turned the Stop hook into a
permanent block.

## 10. Anti-patterns (lint enforces most)

- Untracked/gitignored wiki. ⚖ Bare `!/dir/**` negation under an excluded parent is
  itself the anti-pattern — it does nothing; re-include parents (`docs/*` +
  `!docs/llm-wiki/`) and verify with `git check-ignore -v`.
- Duplicated AGENTS.md/CLAUDE.md content — symlink or stub, never copy.
- Inlining wiki content into AGENTS.md; architecture-dump indexes; speculative pages.
- Mega-pages; stub sprawl; weak descriptions; `name:`/`metadata:` nesting; inline
  YAML comments; template placeholders left in frontmatter.
- Absolute internal links; external URLs as internal links; `[[wikilinks]]`.
- Orphans; stale per-dir indexes; frozen placeholder files; uncited claims.
- Retrieval infra by default; confidently stale pages (mark `UNVERIFIED`,
  timestamp meaning-changes, resolve contradictions recency-wins).
- Writing to the wiki during read-only/review/audit sessions.

## 11. Truth audit — checking a page against the repository

`/okf audit` step 2. Lint checks shape; this checks whether sentences are still true.

- **Evidence.** The repository at HEAD: source, config, tests, scripts, data, `raw/` captures, docs outside the
  wiki, and git history (`git log -S'<value>' -- <file>`, `git log -p`, `git show`). Never the page itself, other
  wiki pages or `log.md` — the same agents wrote them.
- **Verdicts.** `supported` — evidence seen that confirms it (cite file:line or commit). `wrong` — evidence seen
  that contradicts all or part of it (a number, name, path, status or scope); quote the contradicting line.
  `unconfirmed` — checkable in principle, but nothing found either way; say what was searched. `outside the repo`
  — a decision, rationale or external fact the repository cannot confirm. Never write `supported` or `wrong`
  without having seen the evidence: in two audits of the same sample, a checker that called things "partly" without
  a contradicting line was overturned 3 times out of 4.
- **Dated statements** ("as of 2026-07-13") are judged against the repo at that date via git history.
- **When written.** For `wrong`, say whether it was true when the page stated it (rotted) or never
  (wrong at write time). The production audit found about half of each.
- **Second look.** First-pass checkers over-flag: in the production audit an independent re-check kept 42 of 72
  flags (24 as wrong) and overturned none of 96 "supported" verdicts. So every `wrong` needs its contradicting
  line quoted after re-opening the evidence (or a blind re-check by a fresh checker); without it the verdict is
  `unconfirmed`.
- **Outside the repo is information, not failure.** Decisions and rationale that exist only in the wiki are what it
  is for; report their count, do not "fix" them. `unconfirmed` sentences are worth a citation or a `raw/` capture.
- **After the audit.** `/okf update` fixes the wrong sentences surgically (newest evidence wins); for a number,
  prefer adding its provenance (§6) to just swapping the value.

## Sources (abbreviated)

Karpathy LLM-wiki gist · OKF SPEC.md v0.2 (GoogleCloudPlatform/open-knowledge-format; v0.1 lived in knowledge-catalog) ·
langchain-ai/openwiki source (no-op/state-guard/diff-budget mechanics) · Factory
AutoWiki docs · ETH "Evaluating AGENTS.md" arXiv:2602.11988 · format study (text-to-SQL schema delivery, not repo context files)
arXiv:2602.05447 · Claude Code hooks docs (Stop/prompt hooks, 8-block cap verified) ·
Cline issue #1911 (a tool-call bug, see §9) · arXiv 2610.30571 (stale instruction files) · the user's own June 2026 benchmarks (fs-vs-embeddings
parity; description lift; alias-layer negative; agentic-nav token cost) · local repo
rot survey + 6-reviewer adversarial panel (2026-07-08, 18 reproduced lint defects
fixed in 1.1.0).
