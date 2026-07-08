#!/usr/bin/env python3
"""okf lint — structure guard + maintenance helpers for an OKF/LLM-wiki bundle.

Copied into each repo as .okf/lint.py at bootstrap so enforcement survives without
the skill installed (hooks, git hooks, CI, collaborators). Stdlib only; needs git.

Subcommands (all resolve the repo root via `git rev-parse --show-toplevel`, so they
work from any subdirectory):
  lint [--quiet]     Structure lint. Exit 1 on errors, 0 on ok/warnings.
  hook               Claude Code PostToolUse fast path (hook JSON on stdin): quick-
                     lints an edited wiki page + idempotent daily log append.
                     ALWAYS exits 0, never crashes the session.
  noop-check         Update-mode short-circuit: CURRENT only when it can PROVE no
                     path outside the wiki changed since the recorded gitHead.
                     Any git uncertainty degrades to STALE, never to CURRENT.
  state-update [--mark-reviewed]
                     Records {updatedAt, gitHead, wikiSha256}. Refuses to rewrite
                     when wiki content is unchanged (churn guard) UNLESS
                     --mark-reviewed, which advances gitHead after a reviewed
                     no-doc-impact pass.
  stop-gate          Claude Code Stop command-hook: blocks (exit 2, reason on
                     stderr) when uncommitted changes touch code but no wiki page
                     or log entry was touched. Honors stop_hook_active.
  pre-commit         Git pre-commit gate: staged wiki pages must pass lint (errors
                     block, exit 1); committing code without any wiki/log change
                     prints a loud warning but does NOT block. Bypass: --no-verify.

Config: .okf/config.json  {"wikiDir": "wiki", "typeVocab": [...]}
State:  .okf/last-update.json
"""
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime, timezone

OKF_LINT_VERSION = "1.2.0"
OKF_DIR = ".okf"
CONFIG_PATH = os.path.join(OKF_DIR, "config.json")
STATE_PATH = os.path.join(OKF_DIR, "last-update.json")
DEFAULT_VOCAB = ["reference", "concept", "decision", "method", "case-study",
                 "asset", "idea", "hypothesis", "evidence", "index"]
RESERVED = {"index.md", "log.md", "readme.md", "_plan.md",
            "hypotheses.md", "evidence-matrix.md"}
RAW_DIRS = ("raw",)
WIKI_CANDIDATES = ["wiki", "docs/llm-wiki", "docs/wiki", "llm-wiki", "openwiki"]
# paths whose change should NOT demand a wiki update (agent plumbing, not knowledge)
NON_KNOWLEDGE = ("AGENTS.md", "CLAUDE.md", ".gitignore", ".claude/", OKF_DIR + "/")

def git(*args, strip=True):
    # quotepath=false: report non-ASCII paths as real UTF-8, not octal escapes
    try:
        r = subprocess.run(["git", "-c", "core.quotepath=false", *args],
                           capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""
    return r.returncode, (r.stdout.strip() if strip else r.stdout)

def repo_root():
    code, out = git("rev-parse", "--show-toplevel")
    return out if code == 0 and out else None

def chdir_repo_root():
    root = repo_root()
    if root:
        try:
            os.chdir(root)
        except OSError:
            return None
    return root

def load_config():
    try:
        with open(CONFIG_PATH, encoding="utf-8-sig") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}

def find_wiki_dir(cfg):
    d = cfg.get("wikiDir")
    if d:
        # configured dir is authoritative: no silent fallback to candidates
        # (a stale config must fail loudly, not lint some other wiki)
        if os.path.isabs(d) or d.replace("\\", "/").startswith("../"):
            return None
        return d.rstrip("/") if os.path.isdir(d) else None
    for c in WIKI_CANDIDATES:
        if os.path.isfile(os.path.join(c, "index.md")) or os.path.isfile(os.path.join(c, "INDEX.md")):
            return c
    return None

def read_text(path):
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        return f.read()

def unquote_git_path(p):
    p = p.strip()
    if len(p) >= 2 and p[0] == '"' and p[-1] == '"':
        p = p[1:-1]
    return p

def porcelain_paths(out):
    """Parse `git status --porcelain` WITHOUT corrupting the 2-char status column.
    Handles renames (both sides count as changed paths)."""
    paths = []
    for line in out.splitlines():
        if len(line) < 4:
            continue
        path_part = line[3:]
        if " -> " in path_part:
            old, new = path_part.split(" -> ", 1)
            paths.append(unquote_git_path(old))
            paths.append(unquote_git_path(new))
        else:
            paths.append(unquote_git_path(path_part))
    return paths

def parse_frontmatter(text):
    """Minimal flat-YAML frontmatter parser. Returns dict (possibly with
    __malformed__ / __folded__ diagnostics) or None if no frontmatter."""
    if text.startswith("﻿"):
        text = text.lstrip("﻿")
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return {"__malformed__": "unterminated frontmatter (missing closing ---)"}
    fm = {}
    for line in text[3:end].splitlines():
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if val[:1] in ('"', "'"):
            q = val[0]
            close = val.find(q, 1)
            val = val[1:close] if close > 0 else val.strip(q)
        else:
            stripped = val.split(" #")[0].rstrip()  # strip inline comment
            if stripped != val:
                fm.setdefault("__inline_comment__", []).append(key)
            val = stripped
        if val in (">", "|", ">-", "|-", ">+", "|+"):
            fm.setdefault("__folded__", []).append(key)
            val = ""
        fm[key] = val
    return fm

def frontmatter_body_split(text):
    if text.startswith("﻿"):
        text = text.lstrip("﻿")
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:]
    return text

def strip_code(text):
    """Remove fenced blocks (line-anchored ``` toggling) and inline code spans."""
    kept, in_fence = [], False
    for line in text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            kept.append(line)
    return re.sub(r"`[^`\n]*`", "", "\n".join(kept))

def extract_links(text):
    """Markdown link targets, tolerating optional \"title\" suffixes."""
    return re.findall(r"\[[^\]]*\]\(\s*([^)\s]+)(?:\s+\"[^\"]*\")?\s*\)", strip_code(text))

def iter_pages(wiki, notes=None):
    """Yield (relpath, is_leaf) for regular .md files. Symlinks are skipped (noted)."""
    for root, dirs, files in os.walk(wiki):
        dirs[:] = [d for d in dirs if d not in RAW_DIRS and not d.startswith(".")]
        for f in sorted(files):
            if not f.endswith(".md"):
                continue
            p = os.path.join(root, f)
            rel = os.path.relpath(p, wiki)
            if os.path.islink(p):
                if notes is not None:
                    notes.append("%s: symlinked page skipped (lint checks the target only)" % rel)
                continue
            yield rel, os.path.basename(f).lower() not in RESERVED

def wiki_tree_sha(wiki):
    h = hashlib.sha256()
    for root, dirs, files in os.walk(wiki):
        dirs.sort()
        for f in sorted(files):
            p = os.path.join(root, f)
            try:
                with open(p, "rb") as fh:
                    data = fh.read()
            except OSError:
                continue
            # length-prefixed framing: (path, content) boundaries can't collide
            h.update(("%s\x00%d\x00" % (os.path.relpath(p, wiki), len(data))).encode())
            h.update(data)
    return h.hexdigest()

def is_placeholder(val):
    return bool(re.match(r"^<.*>$", val or ""))

def lint_page(text, rel, vocab):
    """Page-level checks on CONTENT (source-agnostic: disk file or git index blob).
    Returns (errors, warnings, fm)."""
    errors, warnings = [], []
    fm = parse_frontmatter(text)
    if fm is None:
        errors.append("%s: missing YAML frontmatter (type/title/description required)" % rel)
    elif "__malformed__" in fm:
        errors.append("%s: %s" % (rel, fm["__malformed__"]))
    else:
        for k in fm.get("__folded__", []):
            if k in ("type", "title", "description"):
                errors.append("%s: '%s' uses a multi-line scalar (>/|) — unsupported; write a single-line value" % (rel, k))
        for req in ("type", "title", "description"):
            v = fm.get(req, "")
            if not v:
                if req not in fm.get("__folded__", []):
                    errors.append("%s: missing required frontmatter field '%s'" % (rel, req))
            elif is_placeholder(v):
                errors.append("%s: '%s' still contains a template placeholder (%s)" % (rel, req, v))
        t = (fm.get("type") or "").lower()
        if t and t not in vocab:
            warnings.append("%s: type '%s' not in suggested vocab (%s) — fine if intentional" % (rel, t, ", ".join(sorted(vocab))))
        for k in fm.get("__inline_comment__", []):
            warnings.append("%s: inline '#' comment stripped from frontmatter '%s' — banned by the playbook; remove it (or quote the value if the '#' is real content)" % (rel, k))
        if fm.get("name") is not None:
            warnings.append("%s: uses a 'name:' field — the file path is the concept ID; drop it" % rel)
        # citation presence — the one checkable slice of evidence discipline
        if not (fm.get("source") or fm.get("resource")) and "## Sources" not in text and (fm.get("status") or "") != "draft":
            warnings.append("%s: no 'source:' frontmatter and no '## Sources' section — every page cites its evidence" % rel)
    body = frontmatter_body_split(text)
    if len(body.strip()) < 120:
        warnings.append("%s: thin/placeholder page (<120 chars body) — flesh out or merge (placeholder rot)" % rel)
    for link in extract_links(text):
        if link.startswith("/"):
            errors.append("%s: absolute link '%s' — use relative paths (absolute links break rendering)" % (rel, link))
    return errors, warnings, fm

def git_guard_errors(root, wiki):
    """Git persistence checks (the #1 observed rot cause). Returns (errors, warnings)."""
    errors, warnings = [], []
    if not root:
        errors.append("not a git repository — the wiki's persistence promise requires git (run `git init` and commit the wiki)")
        return errors, warnings
    code, _ = git("check-ignore", "-q", wiki)
    if code == 0:
        errors.append(("wiki dir '%s' is IGNORED by .gitignore — persistence is broken. NOTE: a bare '!/%s/**' "
                       "does NOT work when a parent dir is excluded; re-include parents instead, e.g. for a "
                       "blanket 'docs/' rule use two lines: 'docs/*' then '!docs/llm-wiki/'.") % (wiki, wiki))
    else:
        # tracked wikis dodge check-ignore, but a blanket parent rule still
        # silently ignores every FUTURE file — probe with a plain, ordinary
        # page name (dunder-style probes false-positived on `__*` conventions)
        code, vout = git("check-ignore", "-v", os.path.join(wiki, "okf-new-page-probe.md"))
        if code == 0:
            pat = vout.split("\t")[0].strip() if "\t" in vout else vout.strip()
            errors.append(("existing wiki files are tracked, but a NEW page like '%s/okf-new-page-probe.md' "
                           "would be gitignored (matched by %s) — fix .gitignore with parent re-inclusion "
                           "('docs/*' + '!%s/') before adding pages.") % (wiki, pat or "an ignore rule", wiki))
    code, out = git("status", "--porcelain", "--ignored", "--", wiki, strip=False)
    if code == 0:
        ignored = [l[3:] for l in out.splitlines() if l.startswith("!!")]
        if ignored:
            errors.append("%d file(s) inside the wiki are gitignored (e.g. %s) — fix .gitignore with parent re-inclusion, not bare negation"
                          % (len(ignored), unquote_git_path(ignored[0])))
        untracked = [l for l in out.splitlines() if l.startswith("??")]
        if untracked:
            warnings.append("wiki has %d untracked file(s) (git '??') — commit them or they will not survive" % len(untracked))
    return errors, warnings

# ---------------------------------------------------------------- lint

def run_lint(quiet=False):
    root = chdir_repo_root()
    cfg = load_config()
    wiki = find_wiki_dir(cfg)
    errors, warnings = [], []
    if not wiki:
        if cfg.get("wikiDir"):
            print("okf-lint: configured wikiDir '%s' (.okf/config.json) does not exist or is invalid — fix the config; NOT falling back to other directories." % cfg.get("wikiDir"))
        else:
            print("okf-lint: no wiki directory found (looked for: %s)%s. Run /okf bootstrap, or run from inside the repo."
                  % (", ".join(WIKI_CANDIDATES), "" if root else " — and this is not a git repository"))
        return 1
    vocab = set(v.lower() for v in cfg.get("typeVocab", DEFAULT_VOCAB))

    g_err, g_warn = git_guard_errors(root, wiki)
    errors += g_err
    warnings += g_warn

    pages, descriptions, inbound = {}, {}, {}
    dirs_with_pages = set()
    for rel, is_leaf in iter_pages(wiki, notes=warnings):
        try:
            pages[rel] = (read_text(os.path.join(wiki, rel)), is_leaf)
        except OSError:
            warnings.append("%s: unreadable (broken symlink or permissions) — skipped" % rel)
            continue
        dirs_with_pages.add(os.path.dirname(rel))

    for rel, (text, is_leaf) in pages.items():
        if is_leaf:
            p_err, p_warn, fm = lint_page(text, rel, vocab)
            errors += p_err
            warnings += p_warn
            d = (fm or {}).get("description", "") if isinstance(fm, dict) else ""
            if d and not is_placeholder(d):
                if d.lower() in descriptions:
                    warnings.append("%s: description duplicates %s" % (rel, descriptions[d.lower()]))
                descriptions[d.lower()] = rel
        base = os.path.dirname(rel)
        from_log = os.path.basename(rel).lower() == "log.md"
        for link in extract_links(text):
            if re.match(r"^[a-z]+://", link) or link.startswith("#"):
                continue
            if link.startswith("/"):
                if not is_leaf:  # leaf pages already got this error from lint_page
                    errors.append("%s: absolute link '%s' — use relative paths (absolute links break rendering)" % (rel, link))
                continue
            target = os.path.normpath(os.path.join(base, link.split("#")[0]))
            if target.startswith(".."):
                continue  # points outside the wiki — repo-relative reference, not a concept link
            if target.endswith(".md"):
                if target in pages:
                    if not from_log:  # log.md mentions don't make a page non-orphan
                        inbound.setdefault(target, set()).add(rel)
                elif not os.path.isfile(os.path.join(wiki, target)):
                    warnings.append("%s: forward/broken link '%s' (ok if the page is planned — write it or fix the path)" % (rel, link))

    for d in sorted(dirs_with_pages):
        if d == "":
            continue
        if not any(os.path.isfile(os.path.join(wiki, d, n)) for n in ("index.md", "INDEX.md", "README.md")):
            warnings.append("%s/: no index.md — every topic directory needs a navigational index" % d)

    for rel, (_, is_leaf) in pages.items():
        if is_leaf and rel not in inbound:
            warnings.append("%s: orphan page (no inbound links) — link it from its index.md at minimum" % rel)

    root_index = next((n for n in ("index.md", "INDEX.md") if os.path.isfile(os.path.join(wiki, n))), None)
    if not root_index:
        errors.append("missing root %s/index.md" % wiki)
    else:
        n_lines = len(read_text(os.path.join(wiki, root_index)).splitlines())
        if n_lines > 200:
            warnings.append("%s/%s: %d lines — exceeds the ~200-line navigational budget" % (wiki, root_index, n_lines))
    if not os.path.isfile(os.path.join(wiki, "log.md")):
        warnings.append("missing %s/log.md (append-only changelog)" % wiki)

    for e in errors:
        print("ERROR   " + e)
    shown = warnings[:10] if quiet else warnings
    for w in shown:
        print("warning " + w)
    if quiet and len(warnings) > 10:
        print("warning (+%d more — run 'python3 .okf/lint.py lint' for all)" % (len(warnings) - 10))
    print("okf-lint %s: %d error(s), %d warning(s) across %d page(s) in %s/"
          % (OKF_LINT_VERSION, len(errors), len(warnings), len(pages), wiki))
    return 1 if errors else 0

# ---------------------------------------------------------------- hook (PostToolUse)

def run_hook():
    try:
        return _hook_inner()
    except Exception:
        return 0  # contract: the session hook NEVER crashes or blocks

def _hook_inner():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(payload, dict):
        return 0
    ti = payload.get("tool_input")
    fp = ti.get("file_path") if isinstance(ti, dict) else None
    if not isinstance(fp, str) or not fp:
        return 0
    chdir_repo_root()
    cfg = load_config()
    wiki = find_wiki_dir(cfg)
    if not wiki:
        return 0
    try:
        # realpath on BOTH sides: hook payloads may carry logical paths while getcwd
        # is physical (macOS /var -> /private/var, symlinked project dirs)
        real_fp, real_wiki = os.path.realpath(fp), os.path.realpath(wiki)
        rel = os.path.relpath(real_fp, real_wiki)
        if rel.startswith("..") and sys.platform in ("darwin", "win32"):
            # default-case-insensitive filesystems: WIKI/page.md == wiki/page.md
            if real_fp.lower().startswith(real_wiki.lower() + os.sep):
                rel = real_fp[len(real_wiki) + 1:]
    except ValueError:
        return 0
    if rel.startswith(".."):
        return 0
    is_md = fp.endswith(".md")
    in_raw = rel.split(os.sep, 1)[0] in RAW_DIRS
    reserved = os.path.basename(fp).lower() in RESERVED
    if is_md and not in_raw and not reserved:
        try:
            fm = parse_frontmatter(read_text(fp))
            missing = [k for k in ("type", "title", "description") if not (fm or {}).get(k)]
            if fm is None or missing:
                print("okf: %s is missing frontmatter %s — add before finishing."
                      % (rel, "/".join(missing) if missing else "block"))
        except OSError:
            pass
        append_daily_log(wiki, rel)  # auto-log: leaf wiki pages only
    return 0

def append_daily_log(wiki, page_rel):
    """Idempotent auto entry: one '## [DATE] auto | session edits' block per day.
    Guarded by an exclusive lock so parallel sessions can't drop bullets."""
    log_path = os.path.join(wiki, "log.md")
    lock_path = os.path.join(OKF_DIR, "log.lock") if os.path.isdir(OKF_DIR) else log_path + ".lock"
    lock = None
    try:
        lock = open(lock_path, "w")
        try:
            import fcntl
            fcntl.flock(lock, fcntl.LOCK_EX)
        except ImportError:
            pass
        today = date.today().isoformat()
        header = "## [%s] auto | session edits" % today
        bullet = "- %s" % page_rel
        lines = read_text(log_path).splitlines() if os.path.isfile(log_path) else []
        if not lines or not lines[0].startswith("#"):
            lines = ["# log", ""] + lines
        if header in lines:
            i = lines.index(header) + 1
            while i < len(lines) and (lines[i].startswith("- ") or lines[i] == ""):
                if lines[i] == bullet:
                    return
                i += 1
            lines.insert(lines.index(header) + 1, bullet)
        else:
            at = 1
            while at < len(lines) and lines[at] == "":
                at += 1
            lines[at:at] = [header, bullet, ""]
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    except OSError:
        pass
    finally:
        if lock:
            lock.close()

# ---------------------------------------------------------------- noop-check / state

def load_state():
    try:
        with open(STATE_PATH, encoding="utf-8-sig") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}

def run_noop_check():
    """Prints CURRENT only when provably nothing outside the wiki changed.
    Every git failure or uncertainty degrades to STALE/NO-STATE, never CURRENT."""
    root = chdir_repo_root()
    cfg = load_config()
    wiki = find_wiki_dir(cfg)
    if not root or not wiki:
        print("NO-STATE: %s — run /okf bootstrap" % ("no wiki directory found" if root else "not a git repository"))
        return 0
    if cfg.get("profile") == "lite":
        print("LITE: this repo uses the lite profile (no state machine, no generated pages) — nothing to noop-check. Upgrade with /okf bootstrap (full) if the repo has outgrown lite.")
        return 0
    code, head = git("rev-parse", "HEAD")
    if code != 0 or not re.fullmatch(r"[0-9a-f]{40}", head or ""):
        print("NO-STATE: repository has no commits yet — commit, then stamp state")
        return 0
    last = load_state().get("gitHead")
    if not last or not re.fullmatch(r"[0-9a-f]{40}", last):
        print("NO-STATE: no valid recorded gitHead — full update pass needed, then `state-update`")
        return 0
    code, _ = git("cat-file", "-e", last + "^{commit}")
    if code != 0:
        print("STALE: recorded gitHead %s no longer exists (rebase/gc?) — run a full update pass and re-stamp" % last[:8])
        return 0
    changed = set()
    if last != head:
        code, out = git("log", "--name-only", "--pretty=format:", "%s..HEAD" % last, strip=False)
        if code != 0:
            print("STALE: could not compute %s..HEAD — treat as needing review" % last[:8])
            return 0
        changed |= {l.strip() for l in out.splitlines() if l.strip()}
    code, out = git("status", "--porcelain", strip=False)
    if code != 0:
        print("STALE: git status failed — treat as needing review")
        return 0
    changed |= set(porcelain_paths(out))
    # same knowledge-relevance classification as stop-gate/pre-commit: agent
    # plumbing (AGENTS.md/CLAUDE.md/.gitignore/.claude/.okf) never demands a wiki pass
    outside = sorted(c for c in changed
                     if not c.startswith(wiki + "/") and not any(
                         c == n.rstrip("/") or c.startswith(n) for n in NON_KNOWLEDGE))
    if not outside:
        print("CURRENT: no repository changes outside %s/ since %s — skip the update, wiki is current." % (wiki, last[:8]))
        return 0
    print("STALE: %d path(s) changed since %s. Build a docs-impact plan from:" % (len(outside), last[:8]))
    print("  git log %s..HEAD --name-status" % last)
    print("  git diff --name-status HEAD && git status --short")
    for c in outside[:40]:
        print("  changed: " + c)
    if len(outside) > 40:
        print("  ... +%d more" % (len(outside) - 40))
    print("After updating (or confirming no doc impact): python3 .okf/lint.py state-update%s"
          % ("" if None else " [--mark-reviewed]"))
    return 0

def run_state_update(mark_reviewed=False):
    root = chdir_repo_root()
    cfg = load_config()
    wiki = find_wiki_dir(cfg)
    if not root or not wiki:
        print("okf: %s — nothing to record" % ("no wiki dir" if root else "not a git repository"))
        return 1
    code, head = git("rev-parse", "HEAD")
    if code != 0 or not re.fullmatch(r"[0-9a-f]{40}", head or ""):
        print("okf: repository has no commits yet — make the initial commit before stamping state")
        return 1
    new_sha = wiki_tree_sha(wiki)
    state = load_state()
    if state.get("wikiSha256") == new_sha and state.get("gitHead") == head:
        print("okf: nothing changed — state file NOT rewritten (churn guard)")
        return 0
    if state.get("wikiSha256") == new_sha and not mark_reviewed:
        print("okf: wiki content unchanged — NOT rewritten (churn guard). If you reviewed the diff and it has "
              "no doc impact, advance the anchor with: python3 .okf/lint.py state-update --mark-reviewed")
        return 0
    os.makedirs(OKF_DIR, exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump({"updatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                   "command": "state-update" + (" --mark-reviewed" if mark_reviewed else ""),
                   "gitHead": head, "wikiSha256": new_sha,
                   "lintVersion": OKF_LINT_VERSION}, f, indent=2)
        f.write("\n")
    print("okf: state updated (gitHead %s%s)" % (head[:8], ", reviewed-no-impact" if mark_reviewed else ""))
    return 0

# ---------------------------------------------------------------- stop-gate / pre-commit

def run_stop_gate():
    """Stop command-hook: exit 2 + stderr reason blocks the stop; exit 0 allows it."""
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        payload = {}
    if isinstance(payload, dict) and payload.get("stop_hook_active"):
        return 0
    root = chdir_repo_root()
    cfg = load_config()
    wiki = find_wiki_dir(cfg)
    if not root or not wiki:
        return 0
    code, out = git("status", "--porcelain", strip=False)
    if code != 0:
        return 0
    paths = porcelain_paths(out)
    wiki_touched = any(p.startswith(wiki + "/") for p in paths)
    code_changed = [p for p in paths
                    if not p.startswith(wiki + "/") and not any(
                        p == n.rstrip("/") or p.startswith(n) for n in NON_KNOWLEDGE)]
    if code_changed and not wiki_touched:
        sys.stderr.write(
            "okf stop-gate: %d uncommitted non-wiki change(s) (e.g. %s) but no wiki page or log entry was touched. "
            "Update the affected %s/ page(s) and append to %s/log.md — or, if this change truly has no knowledge "
            "impact, append one line to %s/log.md: '## [%s] no-impact | <what and why>'. See AGENTS.md → Knowledge base.\n"
            % (len(code_changed), code_changed[0], wiki, wiki, wiki, date.today().isoformat()))
        return 2
    return 0

def run_pre_commit():
    """Git pre-commit: validates the STAGED index blobs (`git show :path`), not the
    working tree — continued edits after `git add` can't slip broken content past
    the gate. Page-level errors on staged wiki pages + git-persistence errors BLOCK
    (exit 1); code-only commits with no wiki/log change get a loud warning (exit 0)."""
    root = chdir_repo_root()
    cfg = load_config()
    wiki = find_wiki_dir(cfg)
    if not root or not wiki:
        return 0
    code, out = git("diff", "--cached", "--name-status", "-M", strip=False)
    if code != 0:
        return 0
    staged, wiki_structure_change = [], False
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) < 2 or not parts[0].strip():
            continue
        status, paths = parts[0][:1], [unquote_git_path(p) for p in parts[1:]]
        staged.extend(paths)
        # deletes/renames of wiki pages can break links/orphans that per-blob
        # linting cannot see — trigger a full-graph pass for those
        if status in ("D", "R") and any(p.startswith(wiki + "/") for p in paths):
            wiki_structure_change = True
    if not staged:
        return 0
    staged_wiki = [p for p in staged if p.startswith(wiki + "/")]
    # the git-persistence guard runs on EVERY commit — a gitignored/untracked wiki
    # must never pass silently just because this commit didn't stage wiki files
    guard_err, _ = git_guard_errors(root, wiki)
    if guard_err and not staged_wiki:
        for e in guard_err:
            print("okf WARNING (not blocking this code-only commit): " + e)
        print("okf WARNING: the wiki's git persistence is broken — fix now (`python3 .okf/lint.py lint` / `/okf repair`).")
    if staged_wiki:
        vocab = set(v.lower() for v in cfg.get("typeVocab", DEFAULT_VOCAB))
        blocking = list(guard_err)
        for p in staged_wiki:
            rel = p[len(wiki) + 1:]
            if (not p.endswith(".md") or os.path.basename(p).lower() in RESERVED
                    or rel.split("/", 1)[0] in RAW_DIRS):
                continue
            code, blob = git("show", ":%s" % p, strip=False)
            if code != 0:
                continue  # deleted/renamed-away in the index
            p_err, _, _ = lint_page(blob, rel, vocab)
            blocking += p_err
        if wiki_structure_change:
            # full-graph pass (disk approximates the post-commit tree for D/R):
            # catches links broken by the deletion/rename and new orphans
            import io
            buf, old = io.StringIO(), sys.stdout
            sys.stdout = buf
            try:
                graph_rc = run_lint(quiet=True)
            finally:
                sys.stdout = old
            if graph_rc != 0:
                blocking.append("staged wiki deletion/rename breaks the graph — full lint errors follow:")
                blocking += ["  " + l for l in buf.getvalue().splitlines() if l.startswith("ERROR")]
            else:
                for l in buf.getvalue().splitlines():
                    if "broken link" in l or "orphan" in l:
                        print("okf WARNING (deletion/rename graph check): " + l)
        if blocking:
            for e in blocking:
                print("ERROR   " + e)
            print("okf pre-commit: %d error(s) in STAGED content (checked as staged, not as on disk) — "
                  "fix and re-add, or bypass once with `git commit --no-verify`" % len(blocking))
            return 1
    staged_code = [p for p in staged
                   if not p.startswith(wiki + "/") and not any(
                       p == n.rstrip("/") or p.startswith(n) for n in NON_KNOWLEDGE)]
    if staged_code and not staged_wiki:
        print("okf WARNING: committing %d non-wiki change(s) with no wiki/log update — if this changes what the "
              "wiki asserts, update it in this commit (AGENTS.md → Knowledge base). Not blocking." % len(staged_code))
    return 0

# ---------------------------------------------------------------- install-hooks

def run_install_hooks(fragment_path):
    """Deep-merge a {'hooks': {...}} fragment into .claude/settings.json WITHOUT
    touching sibling keys (permissions, env, model...). Idempotent: entries already
    present are not duplicated. Backs up an existing settings.json first."""
    root = chdir_repo_root()
    if not root:
        print("okf: not a git repository — run from the target repo")
        return 1
    if not fragment_path:
        print("okf: usage: install-hooks <fragment.json>")
        return 1
    try:
        with open(fragment_path, encoding="utf-8-sig") as f:
            frag = json.load(f)
    except (OSError, ValueError) as e:
        print("okf: cannot read hooks fragment %s (%s)" % (fragment_path, e))
        return 1
    frag_hooks = frag.get("hooks") if isinstance(frag, dict) else None
    if not isinstance(frag_hooks, dict):
        print("okf: fragment has no top-level 'hooks' object")
        return 1
    spath = os.path.join(".claude", "settings.json")
    settings, had_existing = {}, os.path.isfile(spath)
    if had_existing:
        try:
            with open(spath, encoding="utf-8-sig") as f:
                settings = json.load(f)
        except ValueError:
            print("okf: existing %s is NOT valid JSON — refusing to touch it; fix it first" % spath)
            return 1
        if not isinstance(settings, dict):
            print("okf: existing %s is not a JSON object — refusing to touch it" % spath)
            return 1
        with open(spath + ".bak", "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
            f.write("\n")
    os.makedirs(".claude", exist_ok=True)
    hooks = settings.setdefault("hooks", {})
    added = 0
    for event, entries in frag_hooks.items():
        if not isinstance(entries, list):
            continue
        existing = hooks.setdefault(event, [])
        for entry in entries:
            if entry not in existing:
                existing.append(entry)
                added += 1
    with open(spath, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")
    print("okf: merged %d new hook entr%s into %s%s — sibling settings untouched"
          % (added, "y" if added == 1 else "ies", spath,
             " (backup: %s.bak)" % spath if had_existing else ""))
    return 0

# ---------------------------------------------------------------- main

def main():
    args = sys.argv[1:]
    cmd = args[0] if args and not args[0].startswith("-") else "lint"
    if cmd == "hook":
        return run_hook()
    if cmd == "noop-check":
        return run_noop_check()
    if cmd == "state-update":
        return run_state_update(mark_reviewed="--mark-reviewed" in args)
    if cmd == "stop-gate":
        return run_stop_gate()
    if cmd == "pre-commit":
        return run_pre_commit()
    if cmd == "install-hooks":
        return run_install_hooks(args[1] if len(args) > 1 else None)
    return run_lint(quiet="--quiet" in args)

if __name__ == "__main__":
    sys.exit(main())
