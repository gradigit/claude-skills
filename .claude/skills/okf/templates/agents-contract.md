<!-- okf:contract v3 -->
## Knowledge base (OKF / LLM-wiki)

This repo keeps a durable, agent-facing knowledge base under `{WIKI}/`. It survives compaction and
session resets: read it first, write to it as you work. It routes; it does not summarize the code.

**Read first.** Start at `{WIKI}/index.md`; follow relative links. Prefer the wiki over re-deriving
knowledge from raw sources or chat history.

**Write as you go (during authorized work).**
- A durable fact, decision, or hypothesis a future agent should not rediscover goes to the right
  `{WIKI}/` page in the same unit of work — never only into chat, and never into your private
  auto-memory (that is for your own preferences; repo knowledge belongs here, shared and tracked).
- Read-only, review, or audit sessions do NOT write to the wiki; they report.
- Capture full-fidelity source material under `{WIKI}/raw/` and `git add` it; keep synthesis on
  the topic pages. Untracked captures do not survive `git clean` and never satisfy the gates.
- Keep inference separate from evidence (`hypotheses.md` vs `evidence-matrix.md` in investigative
  repos). Cite every claim (local path, URL, or thread ref); mark uncertain claims `UNVERIFIED`.

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

**Maintenance goes through the skill.** To update, lint, audit, repair or migrate this knowledge base,
run `/okf` (the okf skill) instead of editing its structure by hand — it knows the review anchor,
the lint and the hooks. Never build a second knowledge base beside this one.

**What is mechanized, honestly.** Under Claude Code and Codex, hooks in `.claude/settings.json` /
`.codex/hooks.json` print this pointer, auto-log page edits, and block stopping while code changed
this session (uncommitted OR committed) with no wiki or log entry. The git hooks lint staged pages and
index entries (errors block), warn on code-only commits, and advance the review anchor when a commit
touches the wiki; CI re-runs the same lint. None of these judge knowledge quality — that is your job. Under an
agent without hooks: append log entries yourself and run `python3 .okf/lint.py lint` before
finishing. `.okf/` is repo-controlled code that runs on every edit, stop, and commit — review it as
you would `husky/` or CI config.
<!-- /okf:contract v3 -->
