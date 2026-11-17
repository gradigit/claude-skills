#!/usr/bin/env python3
"""Regression suite for okf_lint.py v1.1 — one assertion per reproduced panel finding."""
import json, os, re, shutil, subprocess, sys, tempfile
from datetime import date

# resolve relative to this file so the suite survives copies/publishes of the skill dir
LINT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "okf_lint.py")
if not os.path.isfile(LINT):  # fallback when run from a scratch copy outside the skill tree
    LINT = os.path.expanduser("~/.claude/skills/okf/scripts/okf_lint.py")
PASS, FAIL = [], []

def sh(cwd, *args, stdin=None):
    r = subprocess.run(list(args), cwd=cwd, capture_output=True, text=True, input=stdin, timeout=60)
    return r.returncode, r.stdout + r.stderr

def lint(cwd, *args, stdin=None):
    return sh(cwd, sys.executable, os.path.join(cwd, ".okf", "lint.py"), *args, stdin=stdin)

def mkrepo(name, wiki="wiki", commit=True):
    d = tempfile.mkdtemp(prefix="okf-reg-%s-" % name)
    sh(d, "git", "init", "-q")
    sh(d, "git", "config", "user.email", "t@t"); sh(d, "git", "config", "user.name", "t")
    os.makedirs(os.path.join(d, ".okf")); os.makedirs(os.path.join(d, wiki, "concepts"), exist_ok=True)
    shutil.copy(LINT, os.path.join(d, ".okf", "lint.py"))
    with open(os.path.join(d, ".okf", "config.json"), "w") as f:
        json.dump({"wikiDir": wiki, "stopGate": "block"}, f)   # the blocking gate is the heavily tested path; advise is tested separately
    w(d, wiki + "/index.md", "# INDEX\n## Sections\n* [concepts](concepts/index.md) — core\n")
    w(d, wiki + "/log.md", "# log\n\n")
    w(d, wiki + "/concepts/index.md", "# concepts\n## Pages\n* [Good](good.md) — the frobnicator retry contract rules.\n")
    w(d, wiki + "/concepts/good.md", "---\ntype: reference\ntitle: Frobnicator retry contract\ndescription: Exponential backoff and 429 handling rules for the frobnicator client.\n---\n# Frob\nRetries with exponential backoff on 429, capped at five attempts, per the client spec [S1].\n## Sources\n[S1] Local: src/frob.py\n")
    if commit:
        sh(d, "git", "add", "-A"); sh(d, "git", "commit", "-qm", "init")
    return d

def w(d, rel, content):
    p = os.path.join(d, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f: f.write(content)

def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  <<< " + detail[:300]))

# ── 1. hook never crashes on type-invalid payloads (breaker #1)
d = mkrepo("hookcrash")
for payload in ['{"tool_input":{"file_path":12345}}', '{"tool_input":{"file_path":true}}',
                '{"tool_input":{"file_path":["a"]}}', '{"tool_input":[1,2]}', '[1,2,3]', 'not json']:
    code, out = lint(d, "hook", stdin=payload)
    check("hook no-crash %s" % payload[:28], code == 0 and "Traceback" not in out, out)

# ── 2. unstaged wiki-only edit → CURRENT (breaker #2 strip bug)
d = mkrepo("stripbug")
code, _ = lint(d, "state-update")
w(d, "wiki/index.md", "# INDEX\n## Sections\n* [concepts](concepts/index.md) — core topics\n")
code, out = lint(d, "noop-check")
check("unstaged wiki edit -> CURRENT", "CURRENT" in out, out)

# ── 3. rename wiki→outside → STALE (breaker #3)
d = mkrepo("rename")
lint(d, "state-update")
sh(d, "git", "mv", "wiki/concepts/good.md", "leaked.md")
code, out = lint(d, "noop-check")
check("wiki->outside rename -> STALE", "STALE" in out and "leaked.md" in out, out)

# ── 4. zero-commit state-update refuses (breaker #4)
d = mkrepo("zerocommit", commit=False)
code, out = lint(d, "state-update")
check("zero-commit state-update refuses", code == 1 and "no commits" in out, "code=%s %s" % (code, out))
code, out = lint(d, "noop-check")
check("zero-commit noop-check NO-STATE", "NO-STATE" in out and "CURRENT" not in out, out)

# ── 5. rebased-away gitHead → STALE (codex P0-1 / fresh m1)
d = mkrepo("rebased")
lint(d, "state-update")
st = json.load(open(os.path.join(d, ".okf/last-update.json")))
st["gitHead"] = "deadbeef" * 5
json.dump(st, open(os.path.join(d, ".okf/last-update.json"), "w"))
w(d, "src/app.py", "x=1"); sh(d, "git", "add", "-A"); sh(d, "git", "commit", "-qm", "code")
code, out = lint(d, "noop-check")
check("rebased anchor -> STALE not CURRENT", "STALE" in out and "CURRENT" not in out, out)

# ── 6. BOM page parses (breaker #5)
d = mkrepo("bom")
w(d, "wiki/concepts/bom.md", "﻿---\ntype: concept\ntitle: BOM page\ndescription: A page saved with a UTF-8 byte order mark by a Windows editor.\n---\n# BOM\nBody long enough to clear the thin-page threshold for this regression test case here.\n## Sources\n[S1] Local: x\n")
code, out = lint(d, "lint")
check("BOM page no frontmatter error", "bom.md: missing YAML frontmatter" not in out, out)

# ── 7. inline comment stripped (fresh M1 / codex #10)
d = mkrepo("inlinecomment")
w(d, "wiki/concepts/ic.md", "---\ntype: reference # routing key\ntitle: IC page\ndescription: Inline comment stripping regression for the frontmatter parser check. # REQUIRED\n---\n# IC\nBody long enough to clear the thin-page threshold for this particular regression test.\n## Sources\n[S1] Local: y\n")
code, out = lint(d, "lint")
check("inline comment: no vocab warn", "ic.md: type 'reference" not in out and "not in suggested vocab" not in out.split("ic.md")[-1][:80], out)
check("inline comment: no dup pollution", "duplicates" not in out, out)

# ── 8. folded scalar → explicit error (breaker #6)
d = mkrepo("folded")
w(d, "wiki/concepts/f.md", "---\ntype: concept\ntitle: Folded\ndescription: >\n  A folded multi-line description that the flat parser cannot represent.\n---\n# F\nBody long enough to clear the thin-page threshold for this regression scenario too.\n## Sources\n[S1] Local: z\n")
code, out = lint(d, "lint")
check("folded scalar -> explicit error", code == 1 and "multi-line scalar" in out, out)

# ── 9. titled broken link caught (breaker #7)
d = mkrepo("titled")
w(d, "wiki/concepts/t.md", "---\ntype: concept\ntitle: Titled\ndescription: Titled-link extraction regression for the markdown link scanner behavior.\n---\n# T\nSee [gone](missing-target.md \"a title\") for details, which does not exist right now.\n## Sources\n[S1] Local: q\n")
code, out = lint(d, "lint")
check("titled broken link warned", "missing-target.md" in out, out)

# ── 10. inline-code fake link ignored (breaker #8)
d = mkrepo("inlinecode")
w(d, "wiki/concepts/icx.md", "---\ntype: concept\ntitle: Inline code\ndescription: Inline code span exclusion regression for the link extraction routine.\n---\n# X\nExample syntax: `[fake](not-a-real-target.md)` is how links look in markdown files.\n## Sources\n[S1] Local: r\n")
code, out = lint(d, "lint")
check("inline-code link not flagged", "not-a-real-target.md" not in out, out)

# ── 11. lint works from subdir (breaker #12 / codex P1-6)
d = mkrepo("subdir")
code, out = sh(os.path.join(d, "wiki", "concepts"), sys.executable, os.path.join(d, ".okf", "lint.py"), "lint")
check("lint from subdir finds wiki", "no wiki directory found" not in out and "page(s) in wiki/" in out, out)

# ── 12. log.md-only inbound still orphan (breaker #11)
d = mkrepo("logorphan")
w(d, "wiki/concepts/lonely.md", "---\ntype: concept\ntitle: Lonely\ndescription: Orphan detection regression where only the changelog links to this page.\n---\n# L\nThis page has a sufficiently long body but no inbound link from any index anywhere.\n## Sources\n[S1] Local: s\n")
w(d, "wiki/log.md", "# log\n\n## [2026-07-08] ingest | added [Lonely](concepts/lonely.md)\n")
code, out = lint(d, "lint")
check("log-only inbound still orphan", "lonely.md: orphan" in out, out)

# ── 13. --mark-reviewed advances anchor (codex P0-2)
d = mkrepo("reviewed")
lint(d, "state-update")
w(d, "src/app.py", "x=1"); sh(d, "git", "add", "-A"); sh(d, "git", "commit", "-qm", "code")
code, out = lint(d, "state-update")
check("churn guard suggests --mark-reviewed", "mark-reviewed" in out, out)
code, out = lint(d, "state-update", "--mark-reviewed")
check("--mark-reviewed accepted", code == 0 and "state updated" in out, out)
code, out = lint(d, "noop-check")
check("post-review noop-check CURRENT", "CURRENT" in out, out)

# ── 14. stop-gate behaviors (codex P0-4 fix)
d = mkrepo("stopgate")
w(d, "src/app.py", "x=1")
code, out = lint(d, "stop-gate", stdin="{}")
check("stop-gate blocks code w/o wiki", code == 2 and "no-impact" in out, "code=%s %s" % (code, out))
code, out = lint(d, "stop-gate", stdin='{"stop_hook_active": true}')
check("stop-gate honors stop_hook_active", code == 0, out)
w(d, "wiki/log.md", "# log\n\n## [2026-07-08] no-impact | tooling only\n")
code, out = lint(d, "stop-gate", stdin="{}")
check("stop-gate passes after log entry", code == 0, out)

# ── 15. pre-commit: warn-only for code, block for wiki lint errors
d = mkrepo("precommit")
w(d, "src/app.py", "x=1"); sh(d, "git", "add", "src/app.py")
code, out = lint(d, "pre-commit")
check("pre-commit code-only warns, exit 0", code == 0 and "WARNING" in out, "code=%s %s" % (code, out))
w(d, "wiki/concepts/bad.md", "---\ntype: concept\ntitle: Bad\n---\n# Bad\nshort\n")
sh(d, "git", "add", "wiki/concepts/bad.md")
code, out = lint(d, "pre-commit")
check("pre-commit blocks wiki lint errors", code == 1, "code=%s %s" % (code, out))

# ── 16a. gitignore blanket parent, UNTRACKED wiki (the real csv-api-diff rot case, fresh C1)
d = mkrepo("gitignore", wiki="docs/llm-wiki", commit=False)
w(d, ".gitignore", "docs/\n")
sh(d, "git", "add", ".gitignore", ".okf"); sh(d, "git", "commit", "-qm", "init-no-wiki")
code, out = lint(d, "lint")
check("untracked+ignored wiki -> error", code == 1 and "IGNORED" in out, out)
check("advice teaches parent re-inclusion", "docs/*" in out and "!docs/llm-wiki/" in out, out)
w(d, ".gitignore", "docs/*\n!docs/llm-wiki/\n")
code2, out2 = sh(d, "git", "check-ignore", "-q", "docs/llm-wiki/index.md")
check("recommended pattern actually works", code2 != 0, "check-ignore says still ignored")

# ── 16b. TRACKED wiki under blanket rule: future-files trap probe
d = mkrepo("gitignore2", wiki="docs/llm-wiki")
w(d, ".gitignore", "docs/\n")
code, out = lint(d, "lint")
check("tracked wiki future-trap probed", code == 1 and "NEW page" in out, out)

# ── R2-23. pre-commit validates STAGED blob, not working tree (breaker r2 #1)
d = mkrepo("stagedblob")
w(d, "wiki/concepts/broken.md", "---\ntype: concept\ntitle: Broken\n---\n# B\nStaged version is missing its description field entirely in this regression case.\n")
sh(d, "git", "add", "wiki/concepts/broken.md")
w(d, "wiki/concepts/broken.md", "---\ntype: concept\ntitle: Broken\ndescription: Disk version fixed after staging, but the staged blob is still broken.\n---\n# B\nStaged version is missing its description field entirely in this regression case.\n## Sources\n[S1] Local: x\n")
code, out = lint(d, "pre-commit")
check("pre-commit blocks broken STAGED blob despite fixed disk", code == 1 and "description" in out and "STAGED" in out, "code=%s %s" % (code, out))
sh(d, "git", "add", "wiki/concepts/broken.md")
code, out = lint(d, "pre-commit")
check("pre-commit passes once fix is staged", code == 0, "code=%s %s" % (code, out))

# ── R2-24. probe: narrow __* convention is NOT a false positive (breaker r2 #2)
d = mkrepo("narrowignore")
w(d, ".gitignore", "wiki/__*.md\n")
code, out = lint(d, "lint")
check("narrow __* ignore no false probe error", "NEW page" not in out and "IGNORED" not in out, out)
w(d, ".gitignore", "wiki/*\n")
code, out = lint(d, "lint")
check("broad wiki/* rule still probed", "NEW page" in out or "gitignored" in out, out)

# ── R2-25. unicode paths reported as real UTF-8 (breaker r2 #3)
d = mkrepo("unicode")
lint(d, "state-update")
w(d, "src/日本語.py", "x=1")
sh(d, "git", "add", "-A")
code, out = lint(d, "noop-check")
check("unicode path readable in noop-check", "日本語" in out and "\\346" not in out, out)

# ── R2-26. hook case-insensitive containment — decided by a filesystem probe, never by sys.platform
# (macOS APFS and NTFS are case-insensitive; so is WSL /mnt/c under linux; ext4 is not)
d = mkrepo("caseins")
probe_ci = os.path.exists(os.path.join(d, "WIKI", "concepts", "good.md"))
# The auto-log records only UNCOMMITTED edits (1.3.4), so leave one. Called on the committed, unmodified page this
# check could never log: it passed vacuously on a case-sensitive filesystem and failed on a case-insensitive one.
# No hook baseline exists here (no session-start ran), so the page reaches the hook only through the payload path.
with open(os.path.join(d, "wiki", "concepts", "good.md"), "a", encoding="utf-8") as f:
    f.write("One more sentence, left uncommitted so the auto-log has something to record.\n")
payload = json.dumps({"tool_input": {"file_path": os.path.join(d, "WIKI", "concepts", "good.md")}})
code, out = lint(d, "hook", stdin=payload)
logtxt = open(os.path.join(d, "wiki/log.md")).read()
logged = "auto | session edits" in logtxt and "concepts/good.md" in logtxt
check("case-different path logged iff the filesystem is case-insensitive", logged == probe_ci, "probe_ci=%s logged=%s" % (probe_ci, logged))

# ── RA-28. pre-commit git guard fires on code-only commits too (req-audit-v2 gap 1)
d = mkrepo("guardalways", wiki="docs/llm-wiki", commit=False)
w(d, ".gitignore", "docs/\n")
sh(d, "git", "add", ".gitignore", ".okf"); sh(d, "git", "commit", "-qm", "init-no-wiki")
w(d, "src/app.py", "x=1"); sh(d, "git", "add", "src/app.py")
code, out = lint(d, "pre-commit")
check("code-only commit still surfaces broken wiki persistence", code == 0 and "persistence is broken" in out and "not blocking" in out, "code=%s %s" % (code, out))

# ── R2-27. tree hash boundary collision (breaker r2 #5)
d = mkrepo("hashcoll")
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location("lintmod", os.path.join(d, ".okf", "lint.py"))
_m = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_m)
t1 = tempfile.mkdtemp(); t2 = tempfile.mkdtemp()
open(os.path.join(t1, "a"), "w").write("bc")
open(os.path.join(t2, "ab"), "w").write("c")
check("tree hash separates path/content boundary", _m.wiki_tree_sha(t1) != _m.wiki_tree_sha(t2),
      "%s == %s" % (_m.wiki_tree_sha(t1), _m.wiki_tree_sha(t2)))

# ── 17. placeholder frontmatter → error (codex #10)
d = mkrepo("placeholder")
w(d, "wiki/concepts/p.md", "---\ntype: concept\ntitle: <distinctive short name>\ndescription: <ONE sentence>\n---\n# P\nBody long enough to clear the thin threshold for the placeholder regression case.\n")
code, out = lint(d, "lint")
check("placeholders -> error", code == 1 and "placeholder" in out, out)

# ── 18. headerless log append creates header (breaker #14)
d = mkrepo("logheader")
w(d, "wiki/log.md", "some legacy freeform line\n")
w(d, "wiki/concepts/good.md", open(os.path.join(d, "wiki/concepts/good.md")).read() + "\nEdited.\n")  # a real (uncommitted) edit
payload = json.dumps({"tool_input": {"file_path": os.path.join(d, "wiki/concepts/good.md")}})
code, out = lint(d, "hook", stdin=payload)
logtxt = open(os.path.join(d, "wiki/log.md")).read()
check("headerless log gets # header first", logtxt.startswith("# log") and "auto | session edits" in logtxt and "legacy freeform" in logtxt, logtxt)

# ── 19. hypotheses.md reserved (fresh m4)
d = mkrepo("reserved")
w(d, "wiki/hypotheses.md", "# Hypotheses\n- maybe X causes Y\n")
code, out = lint(d, "lint")
check("hypotheses.md no frontmatter error", "hypotheses.md: missing YAML frontmatter" not in out, out)

# ── 20. citation presence: warn non-draft, exempt draft
d = mkrepo("citation")
w(d, "wiki/concepts/nocite.md", "---\ntype: concept\ntitle: No cite\ndescription: Citation presence regression for a verified page without any sources block.\nstatus: verified\n---\n# N\nA long enough body making claims without any citation section present at all here.\n")
w(d, "wiki/concepts/draft.md", "---\ntype: concept\ntitle: Draft\ndescription: Citation presence exemption regression for a page still marked as draft.\nstatus: draft\n---\n# D\nA long enough body for a draft page that is not yet required to carry citations.\n")
code, out = lint(d, "lint")
check("uncited verified page warned", "nocite.md: no 'source:'" in out, out)
check("draft page exempt from citation warn", "draft.md: no 'source:'" not in out, out)

# ── 21. ../ escape link not misvalidated (codex #11)
d = mkrepo("escape")
w(d, "wiki/concepts/esc.md", "---\ntype: concept\ntitle: Escape\ndescription: Wiki-escaping relative link regression for the target resolution logic.\n---\n# E\nSee [repo readme](../../README.md) which lives outside the knowledge base tree.\n## Sources\n[S1] Local: t\n")
code, out = lint(d, "lint")
check("../ escape link not flagged broken", "README.md" not in out, out)

# ── 22. happy path still clean
d = mkrepo("happy")
code, out = lint(d, "lint")
check("happy path exit 0", code == 0, out)

# ── R3-29. install-hooks deep merge preserves siblings + idempotent (fresh-v2 M1)
d = mkrepo("installhooks")
os.makedirs(os.path.join(d, ".claude"), exist_ok=True)
w(d, ".claude/settings.json", json.dumps({"permissions": {"allow": ["Bash(ls:*)"]},
    "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "echo custom"}]}]}}))
w(d, ".okf/hooks-fragment.json", json.dumps({"hooks": {"PostToolUse": [{"matcher": "Edit|MultiEdit|Write",
    "hooks": [{"type": "command", "command": "if [ -f .okf/lint.py ]; then python3 .okf/lint.py hook; fi"}]}]}}))
code, out = lint(d, "install-hooks", ".okf/hooks-fragment.json")
s = json.load(open(os.path.join(d, ".claude/settings.json")))
check("install-hooks merged", code == 0 and len(s["hooks"]["PostToolUse"]) == 1, out)
check("install-hooks preserved siblings", s["permissions"]["allow"] == ["Bash(ls:*)"] and len(s["hooks"]["PreToolUse"]) == 1, json.dumps(s))
code, out = lint(d, "install-hooks", ".okf/hooks-fragment.json")
s = json.load(open(os.path.join(d, ".claude/settings.json")))
check("install-hooks idempotent", code == 0 and "0 new hook" in out and len(s["hooks"]["PostToolUse"]) == 1, out)
w(d, ".claude/settings.json", "{invalid")
code, out = lint(d, "install-hooks", ".okf/hooks-fragment.json")
check("install-hooks refuses invalid settings", code == 1 and "refusing" in out, out)

# ── R3-30. noop-check ignores agent plumbing (fresh-v2 m1: NON_KNOWLEDGE parity)
d = mkrepo("plumbing")
lint(d, "state-update")
w(d, ".gitignore", "node_modules/\n")
w(d, "AGENTS.md", "# contract\n")
code, out = lint(d, "noop-check")
check("plumbing-only changes -> CURRENT", "CURRENT" in out, out)

# ── R3-31. lite profile short-circuits noop-check (fresh-v2 m2)
d = mkrepo("lite")
w(d, ".okf/config.json", json.dumps({"wikiDir": "wiki", "profile": "lite"}))
code, out = lint(d, "noop-check")
check("lite profile notice", "LITE" in out, out)

# ── R3-32. configured-but-missing wikiDir fails loudly, no fallback (codex-v2 #6)
d = mkrepo("badconfig")
w(d, ".okf/config.json", json.dumps({"wikiDir": "docs/gone"}))
code, out = lint(d, "lint")
check("missing configured wikiDir errors loudly", code == 1 and "NOT falling back" in out, out)

# ── R3-33. staged deletion of a linked page surfaces graph damage (codex-v2 #4)
d = mkrepo("graphdelete")
sh(d, "git", "rm", "-q", "wiki/concepts/good.md")
code, out = lint(d, "pre-commit")
# 1.3.5: the index still lists the deleted page, so this is now a blocking error, not a graph warning
check("staged wiki deletion that leaves its index entry is blocked", code == 1 and "good.md" in out and "index entry" in out, "code=%s %s" % (code, out))

# ── R3-34. inline frontmatter comment now warns (codex-v2 #7)
d = mkrepo("inlinewarn")
w(d, "wiki/concepts/iw.md", "---\ntype: reference # comment here\ntitle: IW\ndescription: Inline comment warning regression for the parser transparency check.\n---\n# IW\nBody long enough to clear the thin threshold for this regression scenario as well.\n## Sources\n[S1] Local: y\n")
code, out = lint(d, "lint")
check("inline comment stripped -> warning", "inline '#' comment stripped" in out, out)

# ── R4-35. junk files (gitignored/untracked) never flagged (live finding, v1.2.2)
d = mkrepo("junkfiles")
w(d, ".gitignore", ".DS_Store\n")
w(d, "wiki/.DS_Store", "junk")
w(d, "wiki/concepts/.DS_Store", "junk")
code, out = lint(d, "lint")
check("gitignored .DS_Store in wiki -> no error", code == 0 and "gitignored" not in out, out)
check("junk not counted as untracked", "untracked file" not in out, out)
w(d, ".gitignore", ".DS_Store\nwiki/concepts/real-page.md\n")
w(d, "wiki/concepts/real-page.md", "---\ntype: concept\ntitle: R\ndescription: A real knowledge page that got gitignored and must still be flagged.\n---\n# R\nBody long enough to clear thin threshold in the junk-exclusion regression case.\n")
code, out = lint(d, "lint")
check("gitignored real .md still errors", code == 1 and "gitignored" in out, out)


# ═══════════════════════════════════════ 1.3.0 — production-driven mechanics
def _head(d):
    return sh(d, "git", "rev-parse", "HEAD")[1].strip()

def _commit(d, msg, *extra):
    sh(d, "git", "add", "-A"); sh(d, "git", "commit", "-q", "-m", msg, *extra)

# ── 130-1. Stop gate: committing code no longer bypasses it (session base from session-start)
d = mkrepo("gatecommit")
code, out = lint(d, "session-start", stdin='{"source":"startup"}')
check("session-start prints the pointer and records the session base", "OKF knowledge base active" in out and os.path.isfile(os.path.join(d, ".okf/sessions/default.json")), out)
w(d, "src/app.py", "x=1"); _commit(d, "code only")
code, out = lint(d, "stop-gate", stdin="{}")
check("commit-then-stop is BLOCKED (exit 2)", code == 2 and "committed" in out, "code=%s %s" % (code, out[:120]))
w(d, "wiki/raw/capture.json", "{}")
code, out = lint(d, "stop-gate", stdin="{}")
check("a raw/ capture alone does not satisfy the gate", code == 2, "code=%s" % code)
w(d, "wiki/concepts/good.md", open(os.path.join(d, "wiki/concepts/good.md")).read() + "\nUpdated after the code change.\n")
code, out = lint(d, "stop-gate", stdin="{}")
check("touching a wiki page this session allows the stop and prints {}", code == 0 and out.strip() == "{}", "code=%s %s" % (code, out))

# ── 130-2. no-impact escape must be dated today; an Okf-Impact trailer also certifies
d = mkrepo("gatehatch")
w(d, "wiki/log.md", "# log\n\n## [2020-01-01] no-impact | ancient\n"); _commit(d, "old log")
lint(d, "session-start", stdin='{"source":"startup"}')
w(d, "src/app.py", "x=1"); _commit(d, "code")
code, out = lint(d, "stop-gate", stdin="{}")
check("a no-impact line from a past day does not excuse today's code", code == 2, "code=%s" % code)
lint(d, "session-start", stdin='{"source":"startup"}')
w(d, "src/app2.py", "y=2"); _commit(d, "code 2")
w(d, "wiki/log.md", "# log\n\n## [%s] no-impact | plumbing only\n" % date.today().isoformat()); _commit(d, "log today")
code, out = lint(d, "stop-gate", stdin="{}")
check("a committed no-impact line dated today, added this session, excuses this session's code commit", code == 0 and out.strip() == "{}", "code=%s %s" % (code, out[:100]))
lint(d, "session-start", stdin='{"source":"startup"}')
w(d, "src/app3.py", "z=3"); _commit(d, "chore", "-m", "Okf-Impact: none")
code, out = lint(d, "stop-gate", stdin="{}")
check("an Okf-Impact: none trailer certifies a code commit", code == 0, "code=%s %s" % (code, out[:100]))
code, out = lint(d, "stop-gate", stdin='{"stop_hook_active": true}')
check("stop_hook_active short-circuits with {}", code == 0 and out.strip() == "{}", out)

# ── 130-3. noop-check reports uncertified COMMITS, and excludes commits that carried their wiki update
d = mkrepo("percommit")
lint(d, "state-update")
for i in range(3):
    w(d, "src/f%d.py" % i, "x=%d" % i); _commit(d, "code %d" % i)
w(d, "wiki/index.md", "# INDEX\n## Sections\n* [concepts](concepts/index.md) — core topics\n"); _commit(d, "wiki nav")
code, out = lint(d, "noop-check")
check("noop-check lists 3 uncertified commits, not flat paths", "3 uncertified commit(s)" in out and out.count("  commit ") == 3 and "changed:" not in out, out)
d = mkrepo("certified")
lint(d, "state-update")
w(d, "src/a.py", "x"); w(d, "wiki/index.md", "# INDEX\n## Sections\n* [concepts](concepts/index.md) — core!\n"); _commit(d, "mixed")
code, out = lint(d, "noop-check")
check("a commit that touched code AND wiki is certified -> CURRENT", "CURRENT" in out, out)
w(d, "src/b.py", "y"); _commit(d, "code", "-m", "Okf-Impact: none")
code, out = lint(d, "noop-check")
check("an Okf-Impact: none commit is certified -> CURRENT", "CURRENT" in out, out)

# ── 130-4. post-commit advances the anchor only for wiki-touching commits; post-rewrite follows amends
d = mkrepo("postcommit")
w(d, ".gitignore", ".okf/last-update.json\n")   # as at bootstrap: per-clone state is never tracked
lint(d, "state-update")
w(d, "src/a.py", "x"); w(d, "wiki/index.md", "# INDEX\n## Sections\n* [concepts](concepts/index.md) — core?\n"); _commit(d, "mixed")
lint(d, "post-commit")
st = json.load(open(os.path.join(d, ".okf/last-update.json")))
head = _head(d)
check("post-commit stamps HEAD when the commit touched the wiki", st["gitHead"] == head and "--auto" in st["command"], json.dumps(st))
w(d, "src/b.py", "y"); _commit(d, "code only")
lint(d, "post-commit")
st2 = json.load(open(os.path.join(d, ".okf/last-update.json")))
check("post-commit leaves the anchor alone for code-only commits", st2["gitHead"] == head, st2["gitHead"][:8])
sh(d, "git", "reset", "-q", "--hard", head)
sh(d, "git", "commit", "-q", "--amend", "-m", "mixed (amended)")
new = _head(d)
code, out = lint(d, "post-rewrite", stdin="%s %s\n" % (head, new))
st3 = json.load(open(os.path.join(d, ".okf/last-update.json")))
check("post-rewrite remaps a rewritten anchor", st3["gitHead"] == new and "remapped" in out, out)
code, out = lint(d, "noop-check")
check("after the remap noop-check is CURRENT, not STALE-forever", "CURRENT" in out, out)
d = mkrepo("fromlastwiki")
first = _head(d)
w(d, "src/a.py", "x"); _commit(d, "code")
lint(d, "state-update", "--from-last-wiki-commit")
st = json.load(open(os.path.join(d, ".okf/last-update.json")))
check("state-update --from-last-wiki-commit anchors to the last wiki-touching commit", st["gitHead"] == first, st["gitHead"][:8] + " vs " + first[:8])

# ── 130-5. PostToolUse hook: Codex apply_patch payloads, additionalContext nudge, raw capture note
d = mkrepo("codexpatch")
patch = "*** Begin Patch\n*** Update File: wiki/concepts/good.md\n@@\n-Retries\n+Retries!\n*** End Patch\n"
w(d, "wiki/concepts/good.md", open(os.path.join(d, "wiki/concepts/good.md")).read().replace("Retries", "Retries!", 1))  # apply it
code, out = lint(d, "hook", stdin=json.dumps({"tool_name": "apply_patch", "tool_input": {"command": patch}}))
logtxt = open(os.path.join(d, "wiki/log.md")).read()
check("Codex apply_patch payload auto-logs the edited page", code == 0 and "concepts/good.md" in logtxt, logtxt)
w(d, "wiki/concepts/nofm.md", "# no frontmatter\nbody\n")
code, out = lint(d, "hook", stdin=json.dumps({"tool_input": {"file_path": os.path.join(d, "wiki/concepts/nofm.md")}}))
check("missing-frontmatter nudge is emitted as additionalContext JSON (reaches the model)", '"additionalContext"' in out and "missing frontmatter" in out, out)
code, out = lint(d, "hook", stdin=json.dumps({"tool_input": {"file_path": os.path.join(d, "wiki/concepts/good.md")}}))
check("a well-formed page edit emits no stdout (silent auto-log)", code == 0 and out.strip() == "", out)
w(d, "wiki/raw/cap.json", "{}")
code, out = lint(d, "hook", stdin=json.dumps({"tool_input": {"file_path": os.path.join(d, "wiki/raw/cap.json")}}))
check("a raw/ capture write gets a git-add reminder", "git add" in out, out)

# ── 130-6. auto-log lands below preamble prose and above the newest entry; CRLF preserved
d = mkrepo("preamble")
w(d, "wiki/log.md", "# Log\n\nNewest first. Conventions live here.\n\n## [2026-07-01] ingest | Bootstrap\nBody.\n")
w(d, "wiki/concepts/good.md", open(os.path.join(d, "wiki/concepts/good.md")).read() + "\nEdited.\n")  # a real (uncommitted) edit
lint(d, "hook", stdin=json.dumps({"tool_input": {"file_path": os.path.join(d, "wiki/concepts/good.md")}}))
logtxt = open(os.path.join(d, "wiki/log.md")).read()
check("auto entry sits below the preamble and above the newest entry",
      logtxt.index("Conventions live here.") < logtxt.index("auto | session edits") < logtxt.index("## [2026-07-01]"), logtxt)
d = mkrepo("crlf")
open(os.path.join(d, "wiki/log.md"), "wb").write(b"# log\r\n\r\n## [2026-07-01] ingest | x\r\nBody.\r\n")
w(d, "wiki/concepts/good.md", open(os.path.join(d, "wiki/concepts/good.md")).read() + "\nEdited.\n")  # a real (uncommitted) edit
lint(d, "hook", stdin=json.dumps({"tool_input": {"file_path": os.path.join(d, "wiki/concepts/good.md")}}))
raw = open(os.path.join(d, "wiki/log.md"), "rb").read()
check("CRLF log keeps CRLF line endings after the auto-log", b"\r\n" in raw and b"\n" not in raw.replace(b"\r\n", b""), repr(raw[:80]))

# ── 130-7. install-hooks: upgrades older okf entries, honors hooksDisabled, backs up under .okf/, codex target
d = mkrepo("hooksupgrade")
w(d, ".okf/frag-old.json", json.dumps({"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "if [ -f .okf/lint.py ]; then python3 .okf/lint.py stop-gate; fi"}]}]}}))
lint(d, "install-hooks", ".okf/frag-old.json")
newfrag = {"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "f=\"$(git rev-parse --show-toplevel)/.okf/okf-py.sh\"; sh \"$f\" stop-gate"}]}],
                     "PostToolUse": [{"matcher": "Edit|Write", "hooks": [{"type": "command", "command": "sh .okf/okf-py.sh hook"}]}]}}
w(d, ".okf/frag-new.json", json.dumps(newfrag))
lint(d, "install-hooks", ".okf/frag-new.json")
sj = json.load(open(os.path.join(d, ".claude/settings.json")))
stop = sj["hooks"]["Stop"]
check("install-hooks upgrades an older okf entry instead of appending a second one", len(stop) == 1 and "okf-py.sh" in stop[0]["hooks"][0]["command"], json.dumps(stop))
check("settings backup lands under .okf/, not next to the tracked file", os.path.isfile(os.path.join(d, ".okf/settings.json.bak")) and not os.path.exists(os.path.join(d, ".claude/settings.json.bak")), "")
w(d, ".okf/config.json", json.dumps({"wikiDir": "wiki", "hooksDisabled": ["Stop"]}))
lint(d, "install-hooks", ".okf/frag-new.json")
sj = json.load(open(os.path.join(d, ".claude/settings.json")))
check("hooksDisabled keeps a deliberately removed Stop gate out on re-install", "Stop" not in sj["hooks"] and "PostToolUse" in sj["hooks"], json.dumps(sj["hooks"]))
w(d, ".okf/config.json", json.dumps({"wikiDir": "wiki"}))
code, out = lint(d, "install-hooks", ".okf/frag-new.json", "--target", "codex")
cj = json.load(open(os.path.join(d, ".codex/hooks.json")))
check("install-hooks --target codex writes .codex/hooks.json with the same events", code == 0 and "Stop" in cj["hooks"] and "PostToolUse" in cj["hooks"], out)

# ── 130-8. OKF v0.2 shapes are accepted; passed stale_after warns; hostile wikiDir rejected; help/unknown exit codes
d = mkrepo("v02")
w(d, "wiki/concepts/v2.md", "---\ntype: reference\ntitle: V2 page\ndescription: An OKF v0.2 shaped page with nested sources and a passed stale_after value.\nstatus: stable\ngenerated: { by: human:t, at: 2026-06-01T00:00:00Z }\nstale_after: 2020-01-01T00:00:00Z\nsources:\n  - id: s1\n    resource: src/x.py\n---\n# V2\nBody long enough to clear the thin threshold for this v0.2 conformance regression case.\n")
w(d, "wiki/concepts/index.md", "# concepts\n## Pages\n* [Good](good.md) — the frobnicator retry contract rules.\n* [V2](v2.md) — v0.2 shaped page.\n")
code, out = lint(d, "lint")
check("v0.2 nested sources satisfy citation presence", "v2.md: no 'source:'" not in out, out)
check("v0.2 status 'stable' is accepted without a warning", "status 'stable'" not in out, out)
check("a passed stale_after produces a rot warning", "v2.md: stale_after" in out and "has passed" in out, out)
w(d, ".okf/config.json", json.dumps({"wikiDir": "my wiki"}))
code, out = lint(d, "lint")
check("a wikiDir that would break shell interpolation is rejected loudly", code == 1 and "NOT falling back" in out, out)
w(d, ".okf/config.json", json.dumps({"wikiDir": "wiki"}))
code, out = lint(d, "--help")
check("--help prints usage and exits 0 (never runs lint)", code == 0 and "usage" in out and "okf-lint 1" not in out, out[:100])
code, out = lint(d, "bogus")
check("unknown subcommand exits 2 with usage", code == 2 and "unknown subcommand" in out, out[:100])


# ── 131-1. cited local evidence that is untracked or gitignored is flagged
d = mkrepo("citeduntracked")
w(d, "docs/adr/0001.md", "# ADR 1\nDecision text.\n")
w(d, "wiki/concepts/adr.md", "---\ntype: decision\ntitle: ADR one\ndescription: Why the ADR-0001 decision was taken and what it constrains for the client.\n---\n# ADR one\nBody long enough to clear the thin threshold for this cited-evidence durability regression.\n## Sources\n[S1] Local: docs/adr/0001.md\n")
w(d, "wiki/concepts/index.md", "# concepts\n## Pages\n* [Good](good.md) — the frobnicator retry contract rules.\n* [ADR](adr.md) — ADR one.\n")
code, out = lint(d, "lint")
check("untracked cited local file -> durability ERROR (exit 1)", code == 1 and "cites local evidence 'docs/adr/0001.md' that is untracked" in out, "code=%s %s" % (code, out))
w(d, ".gitignore", "docs/\n")
code, out = lint(d, "lint")
check("gitignored cited local file -> durability error names the cause", code == 1 and "that is gitignored" in out, "code=%s %s" % (code, out))
sh(d, "git", "add", "-f", "docs/adr/0001.md"); sh(d, "git", "commit", "-qm", "track adr")
code, out = lint(d, "lint")
check("tracked cited file -> no durability error", code == 0 and "cites local evidence" not in out, "code=%s %s" % (code, out))


# ── 131-2. DECISIONS.md is agent plumbing: a decisions-only commit is never uncertified
d = mkrepo("decisionsonly")
lint(d, "state-update")
w(d, "DECISIONS.md", "# Decisions\n- routed hooks to core.hooksPath\n"); _commit(d, "chore: record decisions")
code, out = lint(d, "noop-check")
check("DECISIONS.md-only commit -> CURRENT", "CURRENT" in out, out)


# ── 132-1. description quality: generic openers warned in lint AND nudged at write time
d = mkrepo("genericdesc")
w(d, "wiki/concepts/how.md", "---\ntype: method\ntitle: Retry how\ndescription: How the client retries after a 429 from the frobnicator API.\n---\n# How\nBody long enough to clear the thin-page threshold for this description-quality regression case.\n## Sources\n[S1] Local: src/frob.py\n")
w(d, "wiki/concepts/index.md", "# concepts\n## Pages\n* [Good](good.md) — the frobnicator retry contract rules.\n* [How](how.md) — How the client retries after a 429 from the frobnicator API.\n")
code, out = lint(d, "lint")
check("generic description opener -> lint warning", "how.md: description opens with the generic word 'How'" in out, out)
code, out = lint(d, "hook", stdin=json.dumps({"tool_input": {"file_path": os.path.join(d, "wiki/concepts/how.md")}}))
check("generic description opener -> write-time additionalContext nudge", '"additionalContext"' in out and "generic word" in out, out)

# ── 132-2. index entries must reuse the page description verbatim (lint + nudge when the index is written)
d = mkrepo("indexreuse")
code, out = lint(d, "lint")
check("index paraphrasing the description -> lint warning", "concepts/good.md: its index.md entry does not reuse" in out, out)
code, out = lint(d, "hook", stdin=json.dumps({"tool_input": {"file_path": os.path.join(d, "wiki/concepts/index.md")}}))
check("writing a paraphrasing index.md -> nudge naming the page", '"additionalContext"' in out and "concepts/good.md" in out, out)
w(d, "wiki/concepts/index.md", "# concepts\n## Pages\n* [Good](good.md) — Exponential backoff and 429 handling rules for the frobnicator client.\n")
code, out = lint(d, "lint")
check("verbatim index entry -> no reuse warning", "does not reuse" not in out, out)
code, out = lint(d, "hook", stdin=json.dumps({"tool_input": {"file_path": os.path.join(d, "wiki/concepts/index.md")}}))
check("writing a correct index.md -> silent", out.strip() == "", out)

# ── 132-3. premature subdirectories warned
d = mkrepo("prematuresub")
code, out = lint(d, "lint")
check("1 leaf page in a subdirectory -> premature-structure warning", "keep a flat wiki until ~7 pages" in out, out)


# ── 133-1. the PostToolUse hook sees wiki pages written by a SHELL command (heredoc), not only Edit/Write
d = mkrepo("bashwrite")
lint(d, "session-start", stdin='{"source":"startup"}')
w(d, "wiki/concepts/shell.md", "---\ntype: method\ntitle: Shell page\ndescription: How the shell writes pages without the Write tool at all.\n---\n# Shell\nBody long enough to clear the thin threshold for this shell-written page regression case.\n## Sources\n[S1] Local: src/frob.py\n")
bash_payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": "cat > wiki/concepts/shell.md <<'EOF' ... EOF"}})
code, out = lint(d, "hook", stdin=bash_payload)
logtxt = open(os.path.join(d, "wiki/log.md")).read()
check("shell-written page is auto-logged", "concepts/shell.md" in logtxt, logtxt)
check("shell-written page with a generic opener gets the write-time nudge", '"additionalContext"' in out and "shell.md" in out and "generic word" in out, out)
code, out = lint(d, "hook", stdin=json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls"}}))
check("an unrelated shell command after it is silent (no re-nudge)", out.strip() == "", out)
d = mkrepo("bashbaseline")
w(d, "wiki/concepts/predirty.md", "---\ntype: method\ntitle: Pre\ndescription: How a page dirty before the session should not be re-nudged at all.\n---\n# Pre\nBody long enough to clear the thin threshold for this baseline regression case here.\n")
lint(d, "session-start", stdin='{"source":"startup"}')
code, out = lint(d, "hook", stdin=json.dumps({"tool_name": "Bash", "tool_input": {"command": "git status"}}))
check("files already dirty at session start are baselined, not nudged on the first shell command", "predirty" not in out, out)


# ── 134-1. a page edited AND committed inside one shell command is still seen (stat walk, not git status)
d = mkrepo("samecmdcommit")
lint(d, "session-start", stdin='{"source":"startup"}')
import time as _t; _t.sleep(0.05)
w(d, "wiki/concepts/good.md", open(os.path.join(d, "wiki/concepts/good.md")).read().replace("five attempts", "six attempts").replace("description: Exponential", "description: How exponential"))
sh(d, "git", "commit", "-qam", "edit and commit in one go")
code, out = lint(d, "hook", stdin=json.dumps({"tool_name": "Bash", "tool_input": {"command": "sed -i ... && git commit -am x"}}))
check("edit+commit in one shell command is still SEEN (quality nudge delivered)", "generic word" in out and "good.md" in out, out)
st = sh(d, "git", "status", "--porcelain", "--", "wiki")[1]  # .okf/hook-seen.json is gitignored at bootstrap
check("...but not auto-logged, so the wiki stays clean after the agent's commit", st.strip() == "", st)
w(d, "wiki/concepts/good.md", open(os.path.join(d, "wiki/concepts/good.md")).read().replace("six attempts", "seven attempts"))
code, out = lint(d, "hook", stdin=json.dumps({"tool_name": "Bash", "tool_input": {"command": "sed -i ..."}}))
logtxt = open(os.path.join(d, "wiki/log.md")).read()
check("an uncommitted shell edit is auto-logged (rides along with the next commit)", "concepts/good.md" in logtxt, logtxt)


# ── 134-2. no baseline -> the first hook run records one silently instead of logging every page
d = mkrepo("nobaseline")
for i in range(5):
    w(d, "wiki/concepts/p%d.md" % i, "---\ntype: concept\ntitle: P%d\ndescription: How page %d would be nudged if the baseline were missing.\n---\n# P\nBody text long enough to clear the thin-page threshold for the baseline regression.\n" % (i, i))
sh(d, "git", "add", "-A"); sh(d, "git", "commit", "-qm", "pages")
code, out = lint(d, "hook", stdin=json.dumps({"tool_name": "Bash", "tool_input": {"command": "ls"}}))
logtxt = open(os.path.join(d, "wiki/log.md")).read()
check("first hook run without a baseline is silent and logs nothing", out.strip() == "" and "auto | session edits" not in logtxt, out + logtxt)


# ── 135. index entries must point at pages that exist (1.3.5, production audit 2026-10: a never-written page
#        stayed listed in an index for two months under the old forward-link warning)
d = mkrepo("deadindex")
w(d, "wiki/concepts/index.md", "# concepts\n## Pages\n* [Good](good.md) — the frobnicator retry contract rules.\n* [Runbook](runbook.md) — Recovery steps when the frobnicator stalls.\n")
sh(d, "git", "add", "-A"); sh(d, "git", "commit", "-qm", "dead entry")
code, out = lint(d, "lint")
check("index entry for a missing page is a lint ERROR", code == 1 and "index entry links to 'runbook.md'" in out, "code=%s %s" % (code, out))
w(d, "wiki/concepts/index.md", "# concepts\n## Pages\n* [Good](good.md) — the frobnicator retry contract rules.\n* [Runbook](runbook.md) — planned: recovery steps when the frobnicator stalls.\n")
code, out = lint(d, "lint")
check("a line that says 'planned' downgrades it to a warning", code == 0 and "planned page 'runbook.md'" in out, "code=%s %s" % (code, out))
d = mkrepo("bodyforward")
w(d, "wiki/concepts/good.md", open(os.path.join(d, "wiki/concepts/good.md")).read().replace("per the client spec [S1].", "per the client spec [S1]. See [jitter](jitter.md)."))
code, out = lint(d, "lint")
check("a forward link inside a page body stays a warning", code == 0 and "forward/broken link 'jitter.md'" in out, "code=%s %s" % (code, out))
d = mkrepo("outsideindex")
w(d, "wiki/index.md", "# INDEX\n## Sections\n* [concepts](concepts/index.md) — core\n* [Readme](../README.md) — repo readme\n* [Retry rules](concepts/good.md#frob) — anchor link\n")
code, out = lint(d, "lint")
check("index links outside the wiki and #anchors to existing pages are not flagged", code == 0 and "index entry" not in out, "code=%s %s" % (code, out))

d = mkrepo("deadindexcommit")
w(d, "wiki/concepts/index.md", "# concepts\n## Pages\n* [Good](good.md) — the frobnicator retry contract rules.\n* [Runbook](runbook.md) — Recovery steps when the frobnicator stalls.\n")
sh(d, "git", "add", "-A"); sh(d, "git", "commit", "-qm", "drift under an older lint", "--no-verify")
w(d, "wiki/concepts/good.md", open(os.path.join(d, "wiki/concepts/good.md")).read().replace("five attempts", "six attempts"))
sh(d, "git", "add", "wiki/concepts/good.md")
code, out = lint(d, "pre-commit")
check("pre-commit blocks a wiki commit while an index lists a missing page", code == 1 and "runbook.md" in out and "index entry" in out, "code=%s %s" % (code, out))
sh(d, "git", "reset", "-q")
w(d, "src.py", "x = 1\n"); sh(d, "git", "add", "src.py")
code, out = lint(d, "pre-commit")
check("...but a code-only commit is not blocked by it", code == 0, "code=%s %s" % (code, out))
sh(d, "git", "reset", "-q")
w(d, "wiki/concepts/runbook.md", "---\ntype: method\ntitle: Frobnicator runbook\ndescription: Recovery steps when the frobnicator stalls.\n---\n# Runbook\nRestart the frobnicator worker, then replay the queue from the last acknowledged offset [S1].\n## Sources\n[S1] Local: src.py\n")
sh(d, "git", "add", "wiki/concepts/good.md")
code, out = lint(d, "pre-commit")
check("pre-commit checks the commit, not the disk (page written but not staged is still missing)", code == 1 and "runbook.md" in out, "code=%s %s" % (code, out))
sh(d, "git", "add", "wiki/concepts/runbook.md", "src.py")
code, out = lint(d, "pre-commit")
check("staging the page with the entry passes", code == 0, "code=%s %s" % (code, out))

d = mkrepo("deadindexhook")
w(d, "wiki/concepts/index.md", "# concepts\n## Pages\n* [Good](good.md) — the frobnicator retry contract rules.\n* [Runbook](runbook.md) — Recovery steps when the frobnicator stalls.\n")
sh(d, "git", "add", "-A"); sh(d, "git", "commit", "-qm", "drift", "--no-verify")
lint(d, "session-start", stdin='{"source":"startup"}')
import time as _t2; _t2.sleep(0.05)
w(d, "wiki/concepts/good.md", open(os.path.join(d, "wiki/concepts/good.md")).read().replace("five attempts", "six attempts"))
code, out = lint(d, "hook", stdin=json.dumps({"tool_name": "Bash", "tool_input": {"command": "sed -i ..."}}))
check("write-time hook names index entries for missing pages", '"additionalContext"' in out and "runbook.md" in out and "do not exist" in out, out)
code, out = lint(d, "hook", stdin=json.dumps({"tool_name": "Edit", "tool_input": {"file_path": os.path.join(d, "src.py")}}))
check("...but stays silent when the session did not touch the wiki", "runbook.md" not in out, out)

d = mkrepo("contractver")
w(d, "AGENTS.md", "# A\n<!-- okf:contract v2 -->\n## Knowledge base\n<!-- /okf:contract v2 -->\n")
code, out = lint(d, "lint")
check("lint warns when AGENTS.md carries an older okf contract", "contract v2" in out and "run /okf" in out, out)
w(d, "AGENTS.md", "# A\n<!-- okf:contract v4 -->\n## Knowledge base\n<!-- /okf:contract v4 -->\n")
code, out = lint(d, "lint")
check("...and is quiet at the current contract version", "contract v" not in out, out)


# ── 140. truth-audit sampler (1.4.0): `claims` samples sentences for the agent to check against the repo
d = mkrepo("claims")
w(d, "wiki/concepts/exporter.md", "---\ntype: reference\ntitle: Exporter\ndescription: Ledger exporter formats and the refused TSV option.\nsource: src/export.py\n---\n"
  "# Exporter\n\nThe exporter writes CSV and JSONL files for the nightly job every single night [S1]. TSV is refused until the "
  "tab-escaping blocker is resolved by the data team [S1]. The `export()` function takes a ledger and a format name as arguments.\n\n"
  "```\nnot a claim inside a code block with many words here\n```\n\n"
  "- The nightly job writes exactly 2 export files into the out directory [S2].\n- Short bullet.\n\n"
  "## Related\n- [Good](good.md) — the frobnicator retry contract rules and more words here.\n\n"
  "## Sources\n[S1] Local: src/export.py\n[S2] Local: src/nightly.py\n")
w(d, "wiki/concepts/index.md", "# concepts\n## Pages\n* [Good](good.md) — the frobnicator retry contract rules.\n* [Exporter](exporter.md) — Ledger exporter formats and the refused TSV option.\n")
sh(d, "git", "add", "-A"); sh(d, "git", "commit", "-qm", "exporter", "--no-verify")
code, out = lint(d, "claims", "--n", "50", "--seed", "1")
try:
    cj = json.loads(out)
except ValueError:
    cj = {}
texts = [c["text"] for c in cj.get("claims", [])]
check("claims prints JSON with sampled sentences", code == 0 and cj.get("sampled") == len(texts) > 0, out[:300])
check("claims skips code blocks, Related/Sources sections and short bullets",
      not any("code block" in t or "retry contract rules and more" in t or "Short bullet" in t or "Local:" in t for t in texts), str(texts))
kinds = {c["text"][:20]: c["kind"] for c in cj.get("claims", [])}
check("claims classifies status lines, numbers and code references",
      any(c["kind"] == "status" and "refused" in c["text"] for c in cj.get("claims", []))
      and any(c["kind"] == "number" and "exactly 2" in c["text"] for c in cj.get("claims", []))
      and any(c["kind"] == "code" and "export()" in c["text"] for c in cj.get("claims", [])), str(kinds))
check("claims maps [S#] markers to their cited sources",
      any("exactly 2" in c["text"] and c["cites"] == ["src/nightly.py"] for c in cj.get("claims", [])), str(cj.get("claims"))[:300])
check("claims never samples index.md or log.md", all(not c["page"].endswith(("index.md", "log.md")) for c in cj.get("claims", [])), str(cj.get("claims"))[:200])
code2, out2 = lint(d, "claims", "--n", "2", "--seed", "1")
code3, out3 = lint(d, "claims", "--n", "2", "--seed", "1")
check("claims is deterministic for a seed and honors --n", out2 == out3 and json.loads(out2)["sampled"] == 2, out2[:200])
check("claims prints one sentence per line (a `| head` cannot drop half the sample)", len(out.strip().splitlines()) == cj.get("sampled", -1) + 2, out[:200])
st = sh(d, "git", "status", "--porcelain")[1]
check("claims is read-only (worktree untouched)", st.strip() == "", st)
for i in range(6):
    w(d, "wiki/concepts/big%d.md" % i, "---\ntype: reference\ntitle: Big %d\ndescription: Filler page %d for the sampler spread regression case.\n---\n# Big\n\n" % (i, i)
      + " ".join("Sentence number %d on this page states a fact with 3 values in it." % k for k in range(12)) + "\n")
w(d, "wiki/concepts/huge.md", "---\ntype: reference\ntitle: Huge\ndescription: One very long page that must not fill the whole sample alone.\n---\n# Huge\n\n"
  + " ".join("Huge sentence %d holds a number like 42 and the word blocker inside." % k for k in range(200)) + "\n")
code, out = lint(d, "claims", "--n", "16", "--seed", "3")
pages = [c["page"] for c in json.loads(out)["claims"]]
check("claims spreads the sample across pages (one long page cannot fill it)", pages.count("concepts/huge.md") <= 4 and len(set(pages)) >= 5, str(pages))


# ── 150. session-start announces a newer installed skill (1.4.1: plain `/okf` left a two-versions-old .okf/ in place)
d = mkrepo("upgradenotice")
fake_home = tempfile.mkdtemp(prefix="okf-reg-home-")
os.makedirs(os.path.join(fake_home, ".claude", "skills", "okf", "scripts"))
w(fake_home, ".claude/skills/okf/scripts/okf_lint.py", 'OKF_LINT_VERSION = "9.9.9"\n')
env = dict(os.environ, HOME=fake_home)
r = subprocess.run([sys.executable, os.path.join(d, ".okf", "lint.py"), "session-start"], cwd=d, input='{"source":"startup"}',
                   capture_output=True, text=True, env=env, timeout=60)
check("session-start announces a newer installed okf skill", "installed okf skill is 9.9.9" in r.stdout and "run /okf to upgrade" in r.stdout, r.stdout)
w(fake_home, ".claude/skills/okf/scripts/okf_lint.py", 'OKF_LINT_VERSION = "0.0.1"\n')
r = subprocess.run([sys.executable, os.path.join(d, ".okf", "lint.py"), "session-start"], cwd=d, input='{"source":"startup"}',
                   capture_output=True, text=True, env=env, timeout=60)
check("...and stays quiet when the installed skill is older", "run /okf to upgrade" not in r.stdout, r.stdout)


# ── 160. refresh-contract (1.4.2): by hand, an agent dropped three of a repo's evidence rules from a v1 block
TEMPLATE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates", "agents-contract.md")
V1 = open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts", "okf_lint.py")).read()
d = mkrepo("refreshstock")
v1_block = re.search(r'OLD_CONTRACTS = \((".*?"), "', V1, re.S)
v1_text = json.loads(v1_block.group(1)).replace("{WIKI}", "wiki")
w(d, "AGENTS.md", "# Repo\n\nRun the tests first.\n\n" + v1_text + "\n## Release rules\n\nTag every release.\n")
sh(d, "git", "add", "-A"); sh(d, "git", "commit", "-qm", "v1 contract")
code, out = lint(d, "refresh-contract", "--template", TEMPLATE)
a = open(os.path.join(d, "AGENTS.md")).read()
check("refresh-contract replaces a stock v1 block with the template", code == 0 and "okf:contract v4" in a and "okf:contract v1" not in a
      and "Repo-specific rules kept" not in a and "template text only" in out, out + a[:200])
check("refresh-contract keeps everything outside the block", a.startswith("# Repo\n\nRun the tests first.") and a.rstrip().endswith("Tag every release."), a[-200:])
code, out = lint(d, "refresh-contract", "--template", TEMPLATE)
check("refresh-contract is idempotent (already current)", code == 0 and "already v4" in out, out)
d = mkrepo("refreshcustom")
custom = v1_text.replace("<!-- /okf:contract v1 -->", "Record URL, capture time and claim status for every source in `research/`.\n\n<!-- /okf:contract v1 -->")
w(d, "AGENTS.md", "# Repo\n\n" + custom)
sh(d, "git", "add", "-A"); sh(d, "git", "commit", "-qm", "custom v1 contract")
code, out = lint(d, "refresh-contract", "--template", TEMPLATE)
a = open(os.path.join(d, "AGENTS.md")).read()
kept_at = a.find("## Repo-specific rules kept from the previous okf contract")
check("refresh-contract keeps repo-specific contract text below the new block", code == 0 and kept_at > a.find("<!-- /okf:contract v4 -->") > 0
      and "Record URL, capture time and claim status" in a[kept_at:], out + a[-400:])
d = mkrepo("refreshdirty")
w(d, "AGENTS.md", "# Repo\n\n" + v1_text)
sh(d, "git", "add", "-A"); sh(d, "git", "commit", "-qm", "v1")
w(d, "AGENTS.md", "# Repo\n\nSomeone's uncommitted note.\n\n" + v1_text)
before_txt = open(os.path.join(d, "AGENTS.md")).read()
code, out = lint(d, "refresh-contract", "--template", TEMPLATE)
check("refresh-contract refuses while AGENTS.md has uncommitted changes", code == 1 and "uncommitted" in out
      and open(os.path.join(d, "AGENTS.md")).read() == before_txt, out)

# ── 161. the Stop gate ignores uncommitted work that predates the session (1.4.2)
d = mkrepo("predirty")
w(d, "src.py", "x = 1\n"); sh(d, "git", "add", "src.py"); sh(d, "git", "commit", "-qm", "code")
w(d, "src.py", "x = 2  # someone's work in progress\n")
w(d, "wiki/concepts/good.md", open(os.path.join(d, "wiki/concepts/good.md")).read() + "\nUncommitted edit by another session.\n")
lint(d, "session-start", stdin='{"source":"startup"}')
code, out = lint(d, "stop-gate", stdin="{}")
check("Stop gate allows a session that changed nothing (pre-existing uncommitted code ignored)", code == 0, "code=%s %s" % (code, out))
w(d, "other.py", "y = 1\n")
code, out = lint(d, "stop-gate", stdin="{}")
check("...blocks new code even though a pre-existing wiki edit is lying around", code == 2 and "other.py" in out, "code=%s %s" % (code, out))
os.remove(os.path.join(d, "other.py"))
w(d, "src.py", "x = 3  # changed again during this session\n")
code, out = lint(d, "stop-gate", stdin="{}")
check("...and blocks when the session changes a pre-existing uncommitted file further", code == 2 and "src.py" in out, "code=%s %s" % (code, out))

# ═══════════════════════════════════════ 1.5.0 — fixes from the 2026-11 re-evaluation (deep review + fleet audit)
def _cfg(d, **kw):
    c = {"wikiDir": "wiki"}
    c.update(kw)
    w(d, ".okf/config.json", json.dumps(c))

def _sess(sid, source="startup"):
    return json.dumps({"source": source, "session_id": sid})

# ── 170. honest anchor: a wiki-touching commit no longer certifies earlier code-only commits (false CURRENT)
d = mkrepo("honestanchor")
w(d, ".gitignore", ".okf/last-update.json\n.okf/sessions/\n"); _commit(d, "ignore state")
lint(d, "state-update")
anchor0 = json.load(open(os.path.join(d, ".okf/last-update.json")))["gitHead"]
w(d, "src/frob.py", "RETRIES = 9\n"); _commit(d, "change retry budget (code only)")
w(d, "wiki/log.md", "# log\n\n## [2026-11-17] decision | unrelated note\n- nothing about retries\n"); _commit(d, "unrelated log entry")
code, out = lint(d, "post-commit")
st = json.load(open(os.path.join(d, ".okf/last-update.json")))
check("post-commit keeps the anchor when an uncertified code commit lies behind it", st["gitHead"] == anchor0 and "anchor kept" in out, out + st["gitHead"][:8])
code, out = lint(d, "noop-check")
check("...so noop-check stays STALE and lists the code commit", "STALE" in out and "change retry budget" in out, out)
lint(d, "state-update", "--mark-reviewed")
w(d, "wiki/concepts/good.md", open(os.path.join(d, "wiki/concepts/good.md")).read() + "\nNine retries since the budget change.\n"); _commit(d, "wiki follow-up")
lint(d, "post-commit")
check("...and advances again once everything behind it is reviewed", json.load(open(os.path.join(d, ".okf/last-update.json")))["gitHead"] == _head(d), "")
d = mkrepo("rootstamp", commit=False)
_commit(d, "bootstrap as the repository's first commit")
lint(d, "post-commit")
check("post-commit stamps a root commit (diff-tree --root)", os.path.isfile(os.path.join(d, ".okf/last-update.json")), "")

# ── 171. Stop gate session identity: state keyed by session_id; resume keeps the base; pulls are not the session's
d = mkrepo("twosessions")
lint(d, "session-start", stdin=_sess("A"))
w(d, "src/a.py", "x = 1\n")
lint(d, "session-start", stdin=_sess("B"))
code, out = lint(d, "stop-gate", stdin=json.dumps({"session_id": "A"}))
check("a second session's start no longer erases the first session's gate", code == 2 and "src/a.py" in out, "code=%s %s" % (code, out[:120]))
d = mkrepo("resumebase")
lint(d, "session-start", stdin=_sess("R"))
w(d, "src/r.py", "x = 1\n"); _commit(d, "code in the session")
lint(d, "session-start", stdin=_sess("R", "resume"))
code, out = lint(d, "stop-gate", stdin=json.dumps({"session_id": "R"}))
check("resume keeps the session base, so the session's own earlier commit still counts", code == 2 and "committed" in out, "code=%s %s" % (code, out[:120]))
remote = tempfile.mkdtemp(prefix="okf-reg-remote-")
sh(remote, "git", "init", "-q", "--bare")
d = mkrepo("pullnotmine")
sh(d, "git", "remote", "add", "origin", remote); sh(d, "git", "push", "-q", "origin", "HEAD:refs/heads/main")
mate = tempfile.mkdtemp(prefix="okf-reg-mate-")
sh(mate, "git", "clone", "-q", remote, "c"); mc = os.path.join(mate, "c")
sh(mc, "git", "config", "user.email", "m@m"); sh(mc, "git", "config", "user.name", "m")
w(mc, "src/teammate.py", "y = 2\n"); sh(mc, "git", "add", "-A"); sh(mc, "git", "commit", "-qm", "teammate code"); sh(mc, "git", "push", "-q", "origin", "HEAD:main")
lint(d, "session-start", stdin=_sess("P"))
sh(d, "git", "pull", "-q", "--ff-only", "origin", "main")
code, out = lint(d, "stop-gate", stdin=json.dumps({"session_id": "P"}))
check("commits pulled from a remote are not blamed on the session", code == 0 and out.strip() == "{}", "code=%s %s" % (code, out[:120]))

# ── 172. no-impact escapes are scoped to the session and to their own dated section
d = mkrepo("oldnoimpact")
w(d, "wiki/log.md", "# log\n\n## [%s] no-impact | another session's tooling change\n" % date.today().isoformat()); _commit(d, "log")
lint(d, "session-start", stdin=_sess("N"))
w(d, "src/n.py", "x = 1\n"); _commit(d, "code")
code, out = lint(d, "stop-gate", stdin=json.dumps({"session_id": "N"}))
check("a no-impact line written before the session started does not excuse its code", code == 2, "code=%s %s" % (code, out[:120]))
d = mkrepo("noimpactwindow")
w(d, "wiki/log.md", "# log\n\n## [%s] decision | today's entry\n- chose the retry budget\n\n## [2020-01-01] decision | old\n- no-impact: an old bullet\n" % date.today().isoformat()); _commit(d, "log")
w(d, "src/w.py", "x = 1\n")
code, out = lint(d, "stop-gate", stdin="{}")
check("a no-impact bullet in an older section does not count for today", code == 2, "code=%s %s" % (code, out[:120]))
d = mkrepo("untrackeddir")
w(d, "scratch/a.txt", "pre-existing untracked dir\n")
lint(d, "session-start", stdin=_sess("U"))
w(d, "scratch/b.py", "new code inside it\n")
code, out = lint(d, "stop-gate", stdin=json.dumps({"session_id": "U"}))
check("new work inside a pre-existing untracked directory is seen", code == 2 and "scratch/b.py" in out, "code=%s %s" % (code, out[:120]))

# ── 173. advisory by default; "off"; ignorePaths
d = mkrepo("advise")
_cfg(d)
w(d, "src/v.py", "x = 1\n")
code, out = lint(d, "stop-gate", stdin="{}")
check("the default Stop gate advises: exit 0 with a JSON systemMessage", code == 0 and '"systemMessage"' in out and "src/v.py" in out, "code=%s %s" % (code, out[:120]))
_cfg(d, stopGate="off")
code, out = lint(d, "stop-gate", stdin="{}")
check("stopGate off allows with {}", code == 0 and out.strip() == "{}", out)
_cfg(d, stopGate="block", ignorePaths=["*.lock", "build/"])
os.remove(os.path.join(d, "src/v.py"))
w(d, "poetry.lock", "x\n"); w(d, "build/out.js", "x\n")
code, out = lint(d, "stop-gate", stdin="{}")
check("ignorePaths keeps lockfiles and build output from demanding a wiki update", code == 0 and out.strip() == "{}", "code=%s %s" % (code, out[:120]))

# ── 174. the runner and the Claude hook command resolve the repo from the project, not the current directory
TPL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")
d = mkrepo("hookroot")
shutil.copy(os.path.join(TPL, "okf-py.sh"), os.path.join(d, ".okf", "okf-py.sh"))
w(d, ".gitignore", "vendor/\n")
_commit(d, "runner")
nested = os.path.join(d, "vendor", "other")
os.makedirs(os.path.join(nested, ".okf")); sh(nested, "git", "init", "-q")
marker = os.path.join(tempfile.mkdtemp(prefix="okf-reg-marker-"), "pwned")
w(nested, ".okf/lint.py", "open(%r, 'w').write('x')\nprint('{}')\n" % marker)
w(nested, ".okf/okf-py.sh", "touch %s; echo '{}'\n" % marker)
stop_cmd = json.load(open(os.path.join(TPL, "hooks-settings.json")))["hooks"]["Stop"][0]["hooks"][0]["command"]
r = subprocess.run(["sh", "-c", stop_cmd], cwd=nested, input="{}", capture_output=True, text=True, timeout=60,
                   env=dict(os.environ, CLAUDE_PROJECT_DIR=d))
check("the Claude Stop hook run from inside a nested repo executes the project's runner, not the nested repo's",
      not os.path.exists(marker) and r.stdout.strip().startswith("{"), r.stdout + r.stderr)
r = subprocess.run(["sh", os.path.join(d, ".okf", "okf-py.sh"), "stop-gate"], cwd=nested, input="{}", capture_output=True, text=True, timeout=60)
check("the runner resolves the repo from its own location, not the caller's cwd", not os.path.exists(marker), r.stdout + r.stderr)

# ── 175. upgrade-check and install-hooks protect locally patched machinery and custom hooks
def _upgrade_check(d):
    return sh(d, sys.executable, LINT, "upgrade-check")
d = mkrepo("upgradeclean")
code, out = _upgrade_check(d)
check("upgrade-check: the skill's own lint copy is safe to upgrade", code == 0 and "safe to upgrade" in out, out)
with open(os.path.join(d, ".okf", "lint.py"), "a") as f:
    f.write("\n# local fix\n")
code, out = _upgrade_check(d)
check("upgrade-check flags a lint.py that matches no published release", code == 1 and "matches no published" in out, out)
d = mkrepo("upgradecustom")
custom_settings = {"hooks": {"PostToolUse": [{"matcher": "Edit|Write|Bash", "hooks": [{"type": "command",
                   "command": "okf_script=\"$(git rev-parse --show-toplevel)/.okf/lint.py\"; python3 \"$okf_script\" session-track"}]}]}}
w(d, ".claude/settings.json", json.dumps(custom_settings))
code, out = _upgrade_check(d)
check("upgrade-check lists a custom hook that calls .okf/ code", code == 1 and "custom hook" in out and "session-track" in out, out)
shutil.copy(os.path.join(TPL, "hooks-settings.json"), os.path.join(d, ".okf", "frag.json"))
code, out = lint(d, "install-hooks", ".okf/frag.json")
s_after = json.load(open(os.path.join(d, ".claude/settings.json")))
check("install-hooks refuses to merge beside a custom .okf/ hook (no duplicate hooks)", code == 1 and len(s_after["hooks"]["PostToolUse"]) == 1, out)
code, out = lint(d, "install-hooks", ".okf/frag.json", "--replace-custom")
s_after = json.load(open(os.path.join(d, ".claude/settings.json")))
check("...and replaces it only with --replace-custom", code == 0 and len(s_after["hooks"]["PostToolUse"]) == 1
      and "session-track" not in json.dumps(s_after), out)

stock123 = {"hooks": {
    "SessionStart": [{"matcher": "startup|resume|clear|compact", "hooks": [{"type": "command", "command":
        "test -f wiki/index.md && printf '%s\\n' 'OKF knowledge base active: read wiki/index.md first; follow relative links. Persist durable findings to wiki/ as you work (single writer; subagents read-only). Obligations: AGENTS.md -> ## Knowledge base.' || true"}]}],
    "PostToolUse": [{"matcher": "Edit|MultiEdit|Write", "hooks": [{"type": "command", "command":
        "if [ -f .okf/lint.py ]; then if command -v uv >/dev/null 2>&1; then uv run --no-project python3 .okf/lint.py hook; else python3 .okf/lint.py hook; fi; fi"}]}],
    "Stop": [{"hooks": [{"type": "command", "command":
        "if [ -f .okf/lint.py ]; then if command -v uv >/dev/null 2>&1; then uv run --no-project python3 .okf/lint.py stop-gate; else python3 .okf/lint.py stop-gate; fi; fi"}]}]}}
d = mkrepo("upgradestock")
w(d, ".claude/settings.json", json.dumps(stock123))
code, out = _upgrade_check(d)
check("upgrade-check treats the published 1.2.3 hook commands as stock", code == 0 and "custom hook" not in out, out)
custom_ptr = json.loads(json.dumps(stock123))
custom_ptr["hooks"]["SessionStart"][0]["hooks"][0]["command"] = custom_ptr["hooks"]["SessionStart"][0]["hooks"][0]["command"].replace(
    "Obligations: AGENTS.md -> ## Knowledge base.", "For every substantive turn, run the capture skill.")
w(d, ".claude/settings.json", json.dumps(custom_ptr))
code, out = _upgrade_check(d)
check("...and flags a hand-edited pointer text, which a merge would otherwise replace silently", code == 1 and "SessionStart" in out, out)

# ── 176. cited evidence: page-relative, linked and bulleted citations of untracked files are caught
d = mkrepo("citespell")
w(d, "docs/adr-1.md", "decision\n")
for label, src in [("page-relative", "[S1] Local: ../../docs/adr-1.md"), ("markdown link", "[S1] Local: [adr](../../docs/adr-1.md)"),
                   ("bullet", "- [S1] docs/adr-1.md (decision record)")]:
    w(d, "wiki/concepts/good.md", "---\ntype: reference\ntitle: Frobnicator retry contract\ndescription: Exponential backoff and 429 handling rules for the frobnicator client.\n---\n# Frob\nRetries with exponential backoff on 429, capped at five attempts, per the client spec [S1].\n## Sources\n%s\n" % src)
    code, out = lint(d, "lint")
    check("untracked evidence cited %s is a lint error" % label, code == 1 and "docs/adr-1.md" in out and "untracked" in out, "code=%s %s" % (code, out[-300:]))
sh(d, "git", "add", "docs/adr-1.md")
code, out = lint(d, "lint")
check("...and passes once the evidence is tracked", "cites local evidence" not in out, out[-300:])

# ── 177. durability: wiki edits left uncommitted for days are flagged by lint and at session start
d = mkrepo("aged")
p = os.path.join(d, "wiki/concepts/good.md")
w(d, "wiki/concepts/good.md", open(p).read() + "\nAn edit nobody committed.\n")
old = _t.time() - 10 * 86400
os.utime(p, (old, old))
code, out = lint(d, "lint")
check("lint warns about wiki edits uncommitted for more than 3 days", "uncommitted for more than 3 days" in out and "good.md" in out, out[-300:])
code, out = lint(d, "session-start", stdin=_sess("S"))
check("session-start tells the agent about them", "uncommitted for more than 3 days" in out, out)

# ── 178. smaller lint fixes
d = mkrepo("unplanned")
w(d, "wiki/concepts/index.md", "# concepts\n## Pages\n* [Good](good.md) — the frobnicator retry contract rules.\n* [Outage](outage.md) — Unplanned outage runbook.\n")
code, out = lint(d, "lint")
check("'Unplanned' does not downgrade a dead index entry ('planned' is matched as a word)", code == 1 and "outage.md" in out, "code=%s %s" % (code, out[-200:]))
d = mkrepo("multiline")
w(d, "wiki/concepts/good.md", "---\ntype: reference\ntitle: Frobnicator retry contract\ndescription: Exponential backoff and 429 handling\n  rules for the frobnicator client.\n---\n# Frob\nRetries with exponential backoff on 429, capped at five attempts, per the client spec [S1].\n## Sources\n[S1] Local: src/frob.py\n")
code, out = lint(d, "lint")
check("a description continued on an indented line is a lint error, not a silent truncation", code == 1 and "continues on an indented next line" in out, out[-200:])
d = mkrepo("claudetext")
w(d, "CLAUDE.md", "AGENTS.md")
code, out = lint(d, "lint")
check("a CLAUDE.md holding only the text 'AGENTS.md' (broken symlink checkout) is flagged", "imports nothing" in out, out[-200:])
d = mkrepo("tablesample")
w(d, "wiki/concepts/limits.md", "---\ntype: reference\ntitle: Limits\ndescription: Retry and rate limits of the frobnicator client in one table.\n---\n# Limits\n\n"
  "| Limit | Value |\n|---|---|\n| max retry attempts per request | 5 |\n| base delay in milliseconds before retrying | 250 |\n")
code, out = lint(d, "claims", "--n", "50", "--seed", "1")
texts = [c["text"] for c in json.loads(out)["claims"]]
check("claims samples table rows, labelled with their headers", any("Limit: max retry attempts per request; Value: 5" == t for t in texts), str(texts))
c1, o1 = lint(d, "claims", "--n", "3", "--seed", "audit-2026-11")
c2, o2 = lint(d, "claims", "--n", "3", "--seed", "audit-2026-11")
check("a text --seed is accepted and deterministic", c1 == 0 and o1 == o2 and json.loads(o1)["seed"] != date.today().toordinal(), o1[:120])

# ── 179. contract v4: refresh from a stock v3 block
d = mkrepo("refreshv3")
mod = {}
exec(compile("OLD_CONTRACTS = " + re.search(r"^OLD_CONTRACTS = (\(.*?\))\nCONTRACT_RE", open(LINT).read(), re.S | re.M).group(1), "c", "exec"), mod)
v3_text = mod["OLD_CONTRACTS"][2].replace("{WIKI}", "wiki")
w(d, "AGENTS.md", "# Repo\n\n" + v3_text); _commit(d, "v3 contract")
code, out = lint(d, "refresh-contract", "--template", TEMPLATE)
a = open(os.path.join(d, "AGENTS.md")).read()
check("refresh-contract upgrades a stock v3 block to v4 with nothing kept", code == 0 and "okf:contract v4" in a and "The code wins" in a
      and "Repo-specific rules kept" not in a, out)

print("\n=== %d passed, %d failed ===" % (len(PASS), len(FAIL)))
sys.exit(1 if FAIL else 0)
