#!/usr/bin/env python3
"""Regression suite for okf_lint.py v1.1 — one assertion per reproduced panel finding."""
import json, os, shutil, subprocess, sys, tempfile

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
        json.dump({"wikiDir": wiki}, f)
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

# ── R2-26. hook case-insensitive containment (breaker r2 #4, macOS APFS)
d = mkrepo("caseins")
payload = json.dumps({"tool_input": {"file_path": os.path.join(d, "WIKI", "concepts", "good.md")}})
code, out = lint(d, "hook", stdin=payload)
logtxt = open(os.path.join(d, "wiki/log.md")).read()
check("case-different path still logged", "auto | session edits" in logtxt and "concepts/good.md" in logtxt, logtxt)

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
check("staged wiki deletion surfaces graph warning", "graph check" in out and "good.md" in out, "code=%s %s" % (code, out))

# ── R3-34. inline frontmatter comment now warns (codex-v2 #7)
d = mkrepo("inlinewarn")
w(d, "wiki/concepts/iw.md", "---\ntype: reference # comment here\ntitle: IW\ndescription: Inline comment warning regression for the parser transparency check.\n---\n# IW\nBody long enough to clear the thin threshold for this regression scenario as well.\n## Sources\n[S1] Local: y\n")
code, out = lint(d, "lint")
check("inline comment stripped -> warning", "inline '#' comment stripped" in out, out)

print("\n=== %d passed, %d failed ===" % (len(PASS), len(FAIL)))
sys.exit(1 if FAIL else 0)
