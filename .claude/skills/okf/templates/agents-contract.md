<!-- okf:contract v4 -->
## Knowledge base (OKF / LLM-wiki)

This repo keeps a durable, agent-facing knowledge base under `{WIKI}/`. It survives compaction and
session resets: read it first, write to it as you work. It routes; it does not summarize the code.

**Read first.** Start at `{WIKI}/index.md`; follow relative links. Prefer the wiki over re-deriving
knowledge from raw sources or chat history.

**The code wins.** When a page and the code, config or data disagree, act on what the repository
shows, then fix the page in the same unit of work. A page is a claim about the repo, not an order.

**Write as you go (during authorized work).**
- A durable fact, decision, or hypothesis a future agent should not rediscover goes to the right
  `{WIKI}/` page in the same unit of work — including knowledge that arrives in conversation or in
  documents the user supplies, not only knowledge from code changes. Never only into chat, and never
  into your private auto-memory (that is for your own preferences; repo knowledge belongs here).
- Read-only, review, or audit sessions do NOT write to the wiki; they report.
- Capture full-fidelity source material under `{WIKI}/raw/`; keep synthesis on the topic pages.
- Keep inference separate from evidence (`hypotheses.md` vs `evidence-matrix.md` in investigative
  repos). Cite every claim (local path, URL, or thread ref); mark uncertain claims `UNVERIFIED`.

**Commit it.** Commit wiki edits and the captures they cite with the work they describe. An
uncommitted page or capture is not durable: it does not survive `git clean`, a fresh clone, or another
machine. Never commit someone else's uncommitted work; tell the user about it instead.

**Authoring rules.** One answerable unit per file · kebab-case filenames · flat YAML frontmatter with
`type`, `title`, `description` (one distinguishing single-line sentence) · a per-directory `index.md`
updated whenever a page is added or removed, listing only pages that exist (a later page says `planned`) ·
relative links only · rewrite inbound links on rename ·
retrieval is files + grep + index.md — no embeddings, BM25, rerankers, or alias indexes here.

**Single writer.** The main agent is the sole writer of `{WIKI}/`. Subagents inspect and report only.

**Ship = update.** A change that invalidates a wiki page updates that page in the same commit; if a
change truly has no knowledge impact, say so with `## [YYYY-MM-DD] no-impact | <why>` in
`{WIKI}/log.md` dated today, or an `Okf-Impact: none` commit trailer. `{WIKI}/log.md` is the event
log (newest first, `## [YYYY-MM-DD] kind | Title`).

**Maintenance.** To update, lint, audit, repair or migrate this knowledge base's structure, run `/okf`
if you have the okf skill — it knows the review anchor, the lint and the hooks. Without it, follow
the rules above and run `sh .okf/okf-py.sh lint` before finishing. Never build a second knowledge base.

**What is mechanized, honestly.** Where hooks are installed (Claude Code `.claude/settings.json`, Codex
`.codex/hooks.json`), they print this pointer, auto-log page edits, and at the end of a turn report
code changed this session (uncommitted or committed) with no wiki or log entry — a notice by default,
a block where the repo opts in. The git hooks lint staged pages and index entries (errors block), warn
on code-only commits, and advance the review anchor only when no unreviewed code commit lies behind
it; CI re-runs the lint. None of these judge knowledge quality — that is your job. Without hooks (an
agent that has none, or a lite repo): append log entries yourself and run the lint before finishing.
`.okf/` is repo-controlled code that runs on every edit, stop, and commit — review it as you would
`husky/` or CI config.
<!-- /okf:contract v4 -->
