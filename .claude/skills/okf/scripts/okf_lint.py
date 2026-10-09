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
  session-start      SessionStart hook: prints the pointer, records the session base HEAD.
  post-commit        Git post-commit: advances the anchor when the commit touched the wiki.
  post-rewrite       Git post-rewrite: follows the anchor through amend/rebase.
  install-hooks      Merge the hook fragment into .claude/settings.json or --target codex.
  claims [--n N] [--seed S]
                     Truth-audit sampler: N (default 12) sentences from leaf pages, weighted toward status
                     lines, exact numbers and code references (where production wikis went
                     wrong), as JSON with each sentence's cited sources. Read-only, deterministic
                     for a given seed (default: today's date).
  pre-commit         Git pre-commit gate: staged wiki pages must pass lint and every
                     index.md entry must point at a page in the commit (errors block,
                     exit 1); committing code without any wiki/log change prints a
                     loud warning but does NOT block. Bypass: --no-verify.

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

OKF_LINT_VERSION = "1.4.1"
CONTRACT_VERSION = 3          # templates/agents-contract.md marker; older blocks in AGENTS.md are refreshed by /okf
OKF_DIR = ".okf"
CONFIG_PATH = os.path.join(OKF_DIR, "config.json")
STATE_PATH = os.path.join(OKF_DIR, "last-update.json")
SESSION_HEAD_PATH = os.path.join(OKF_DIR, "session-head")   # per-clone, gitignored: HEAD when this session started
HOOK_SEEN_PATH = os.path.join(OKF_DIR, "hook-seen.json")      # per-clone, gitignored: wiki file states the hook already processed
WIKIDIR_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]*$")
V02_STATUS = ("draft", "stable", "deprecated")
LEGACY_STATUS = ("verified", "unverified", "draft")
OKF_HOOK_MARKERS = ("lint.py hook", "lint.py stop-gate", "lint.py session-start", "okf-py.sh", "OKF knowledge base active")
DEFAULT_VOCAB = ["reference", "concept", "decision", "method", "case-study",
                 "asset", "idea", "hypothesis", "evidence", "index"]
RESERVED = {"index.md", "log.md", "readme.md", "_plan.md",
            "hypotheses.md", "evidence-matrix.md"}
RAW_DIRS = ("raw",)
WIKI_CANDIDATES = ["wiki", "docs/llm-wiki", "docs/wiki", "llm-wiki", "openwiki"]
# paths whose change should NOT demand a wiki update (agent plumbing, not knowledge)
NON_KNOWLEDGE = ("AGENTS.md", "CLAUDE.md", "DECISIONS.md", ".gitignore", ".claude/", ".codex/", OKF_DIR + "/")  # agent plumbing, never knowledge

def git(*args, strip=True):
    # quotepath=false: report non-ASCII paths as real UTF-8, not octal escapes
    try:
        r = subprocess.run(["git", "-c", "core.quotepath=false", *args],
                           capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        return 124, ""  # distinguishable: the Stop gate fails CLOSED on a timeout
    except OSError:
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
        d = str(d).replace("\\", "/").rstrip("/")
        if os.path.isabs(d) or d.startswith("../") or not WIKIDIR_RE.match(d):
            return None  # also rejects names that would break shell interpolation in hooks
        return d if os.path.isdir(d) else None
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
    last_key = None
    for line in text[3:end].splitlines():
        m = re.match(r"^([A-Za-z_][\w-]*):\s*(.*)$", line)
        if not m:
            # indented continuation = a nested OKF v0.2 family (sources:, verified:, generated:)
            if last_key and line[:1] in (" ", "\t", "-") and line.strip() and fm.get(last_key, "") == "":
                fm[last_key] = "<nested>"
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
        last_key = key
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

def index_links(text):
    """(planned, link) for markdown links in an index file; a line that says 'planned' marks its entries as planned."""
    for line in strip_code(text).splitlines():
        for link in re.findall(r"\[[^\]]*\]\(\s*([^)\s]+)(?:\s+\"[^\"]*\")?\s*\)", line):
            yield "planned" in line.lower(), link


def missing_index_targets(index_rel, text, exists):
    """(planned, link) for entries in <wiki>/<index_rel> whose wiki page does not exist. `exists(target_rel)` decides
    existence, so the pre-commit gate can check the staged tree and lint the working tree."""
    base, out = os.path.dirname(index_rel), []
    for planned, link in index_links(text):
        if re.match(r"^[a-z]+://", link) or link.startswith("#") or link.startswith("/"):
            continue
        target = os.path.normpath(os.path.join(base, link.split("#")[0]))
        if target.startswith("..") or not target.endswith(".md"):
            continue
        if not exists(target):
            out.append((planned, link))
    return out


def dead_index_message(index_rel, link):
    # an ERROR, not a warning: an index entry tells every agent the page exists; in production a never-written
    # page stayed listed for two months under the old forward-link warning
    return ("%s: index entry links to '%s', which does not exist — an index entry tells agents the page is there. "
            "Write the page, remove the entry, or say 'planned' on that line" % (index_rel, link))


def dead_index_entries_on_disk(wiki):
    """(index_rel, link) for every non-planned index entry whose page is missing from the working tree."""
    out = []
    for root, dirs, files in os.walk(wiki):
        dirs[:] = [d for d in dirs if d not in RAW_DIRS and not d.startswith(".")]
        for f in files:
            if f.lower() != "index.md":
                continue
            rel = os.path.relpath(os.path.join(root, f), wiki)
            try:
                text = read_text(os.path.join(root, f))
            except OSError:
                continue
            for planned, link in missing_index_targets(rel, text, lambda t: os.path.isfile(os.path.join(wiki, t))):
                if not planned:
                    out.append((rel, link))
    return sorted(out)


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
        # raw/ captures are evidence, not knowledge: excluded so a 1 GB capture dir
        # neither slows the stamp nor churns the anchor on every capture
        dirs[:] = sorted(d for d in dirs if not (os.path.normpath(root) == os.path.normpath(wiki) and d in RAW_DIRS))
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

# Descriptions are the one field with a measured retrieval lift; the eval's rubric judge flagged generic
# openers in every skill version (23-44% of pages), so the first words must be the distinguishing terms.
GENERIC_OPENER = re.compile(r"^(how|why|when|what|where|which|this (?:page|doc|document|note)|page|overview|notes?|details?|"
                            r"information|describes?|explains?|covers?|documents?|summary|introduction)\b", re.I)


def description_issue(desc):
    """None, or a one-line reason the description defeats progressive disclosure."""
    d = (desc or "").strip()
    if not d or d == "<nested>":
        return None
    m = GENERIC_OPENER.match(d)
    if m:
        return "description opens with the generic word '%s' — lead with the distinguishing terms a query would use" % m.group(1)
    return None


def index_mismatches(wiki, dir_rel):
    """Leaf pages in <wiki>/<dir_rel> whose own description does not appear in that directory's index.md
    (the index must REUSE descriptions verbatim — the judge flagged paraphrased index entries in every version)."""
    d = os.path.join(wiki, dir_rel)
    idx = os.path.join(d, "index.md")
    if not os.path.isfile(idx):
        return []
    try:
        itext = read_text(idx)
    except OSError:
        return []
    out = []
    for f in sorted(os.listdir(d)):
        p = os.path.join(d, f)
        if not f.endswith(".md") or f.lower() in RESERVED or not os.path.isfile(p) or os.path.islink(p):
            continue
        try:
            desc = (parse_frontmatter(read_text(p)) or {}).get("description", "")
        except OSError:
            continue
        if desc and desc != "<nested>" and not is_placeholder(desc) and desc not in itext:
            out.append(os.path.normpath(os.path.join(dir_rel, f)))
    return out


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
        di = description_issue(fm.get("description"))
        if di:
            warnings.append("%s: %s" % (rel, di))
        # citation presence — the one checkable slice of evidence discipline
        if not (fm.get("source") or fm.get("sources") or fm.get("resource")) and "## Sources" not in text and (fm.get("status") or "") != "draft":
            warnings.append("%s: no 'source:'/'sources:' frontmatter and no '## Sources' section — every page cites its evidence" % rel)
        st = (fm.get("status") or "").lower()
        if st and st not in V02_STATUS and st not in LEGACY_STATUS:
            warnings.append("%s: status '%s' is neither OKF v0.2 (draft|stable|deprecated) nor legacy (verified|unverified|draft)" % (rel, st))
        sa = fm.get("stale_after") or ""
        if sa and sa != "<nested>":
            try:
                when = datetime.fromisoformat(sa.replace("Z", "+00:00"))
                if when.tzinfo is not None and datetime.now(timezone.utc) >= when:
                    warnings.append("%s: stale_after %s has passed — re-verify the page or mark it deprecated" % (rel, sa))
            except ValueError:
                warnings.append("%s: stale_after '%s' is not an ISO 8601 datetime with an offset" % (rel, sa))
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
        def is_junk(p):
            # OS/tooling droppings that SHOULD be gitignored — never knowledge loss
            b = os.path.basename(unquote_git_path(p).rstrip("/"))
            return b in (".DS_Store", "Thumbs.db", "desktop.ini", "__pycache__") or b.endswith(".pyc")
        ignored = [l[3:] for l in out.splitlines() if l.startswith("!!") and not is_junk(l[3:])]
        if ignored:
            errors.append("%d file(s) inside the wiki are gitignored (e.g. %s) — fix .gitignore with parent re-inclusion, not bare negation"
                          % (len(ignored), unquote_git_path(ignored[0])))
        untracked = [l for l in out.splitlines() if l.startswith("??") and not is_junk(l[3:])]
        if untracked:
            names = ", ".join(unquote_git_path(l[3:]) for l in untracked[:5])
            warnings.append("wiki has %d untracked path(s) (git '??'): %s%s — commit them or they will not survive `git clean`"
                            % (len(untracked), names, " …" if len(untracked) > 5 else ""))
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
        is_index = os.path.basename(rel).lower() == "index.md"
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
                elif not os.path.isfile(os.path.join(wiki, target)) and not is_index:
                    warnings.append("%s: forward/broken link '%s' (ok if the page is planned — write it or fix the path)" % (rel, link))
        if is_index:
            for planned, link in missing_index_targets(rel, text, lambda t: t in pages or os.path.isfile(os.path.join(wiki, t))):
                if planned:
                    warnings.append("%s: planned page '%s' not written yet" % (rel, link))
                else:
                    errors.append(dead_index_message(rel, link))

    # cited LOCAL evidence must be durable: an untracked or gitignored file cited by a page will not
    # survive `git clean` or a clone (production and eval finding: migrations left cited ADRs ignored)
    cited = {}
    for rel, (text, is_leaf) in pages.items():
        if not is_leaf:
            continue
        fm = parse_frontmatter(text) or {}
        cands = re.findall(r"^\[S\d+\]\s+Local:\s*([^\s]+)", text, re.M)
        for k in ("source", "resource"):
            v = fm.get(k) or ""
            if v and not re.match(r"^[a-z]+://", v) and "<" not in v:
                cands.append(v)
        for c in cands:
            c = c.strip().rstrip(".,;)")
            if c and not c.startswith("http") and os.path.exists(c):
                cited.setdefault(c, rel)
    for path, rel in sorted(cited.items()):
        if os.path.isdir(path):
            continue
        code_t, _ = git("ls-files", "--error-unmatch", "--", path)
        if code_t == 0:
            continue
        code_i, _ = git("check-ignore", "-q", "--", path)
        # an ERROR, not a warning: warnings were ignored every time in production and in the eval;
        # evidence that provably cannot survive a clone is a broken page
        errors.append("%s: cites local evidence '%s' that is %s — track it (`!%s` in .gitignore if a parent rule hides it), or copy it into %s/raw/ "
                      "(copying never modifies the source location, so it is allowed even where the source dir must not be touched); "
                      "do NOT drop the citation to silence this — it will not survive git clean or a clone"
                      % (rel, path, "gitignored" if code_i == 0 else "untracked", os.path.dirname(path) or path, wiki))
    for d in sorted(dirs_with_pages):
        for m in index_mismatches(wiki, d):
            warnings.append("%s: its index.md entry does not reuse the page's description verbatim — copy the description into the index line" % m)
    # premature structure: subdirectories before ~7 pages make navigation deeper without making it clearer
    leaf_count = sum(1 for _, (_, is_leaf) in pages.items() if is_leaf)
    if leaf_count < 7 and any(os.path.dirname(r) for r, (_, is_leaf) in pages.items() if is_leaf):
        warnings.append("%d leaf pages spread over subdirectories — keep a flat wiki until ~7 pages (reference.md §3)" % leaf_count)
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
    try:
        m = re.search(r"<!-- okf:contract v(\d+) -->", read_text("AGENTS.md"))
        if m and int(m.group(1)) < CONTRACT_VERSION:
            warnings.append("AGENTS.md carries okf contract v%s; the current template is v%d — run /okf to refresh it"
                            % (m.group(1), CONTRACT_VERSION))
    except OSError:
        pass

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

def _is_code(p, wiki):
    """A path whose change may demand a wiki update: outside the wiki and not agent plumbing."""
    return not p.startswith(wiki + "/") and not any(p == n.rstrip("/") or p.startswith(n) for n in NON_KNOWLEDGE)

def _touches_wiki(paths, wiki):
    """Any wiki path that is knowledge (raw/ captures are evidence and never satisfy a gate)."""
    return any(p.startswith(wiki + "/") and not any(p.startswith(wiki + "/" + r + "/") for r in RAW_DIRS) for p in paths)

def _commits_since(last):
    """[[sha, subject, certified_by_marker, [paths]]] for last..HEAD in one git call.
    A commit is certified when it touches the wiki, carries [no-impact] in its subject,
    or an `Okf-Impact: none` trailer."""
    code, out = git("log", "--name-only",
                    "--pretty=format:@@%H%x1f%s%x1f%(trailers:key=Okf-Impact,valueonly)",
                    "%s..HEAD" % last, strip=False)
    if code != 0:
        return None
    commits, cur = [], None
    for line in out.splitlines():
        if line.startswith("@@"):
            parts = line[2:].split("\x1f")
            sha = parts[0].strip()
            subj = parts[1] if len(parts) > 1 else ""
            trailer = parts[2].strip().lower() if len(parts) > 2 else ""
            cur = [sha, subj, ("[no-impact]" in subj.lower()) or trailer.startswith("none"), []]
            commits.append(cur)
        elif line.strip() and cur is not None:
            cur[3].append(line.strip())
    return commits

def _no_impact_today(wiki):
    """A no-impact entry dated today (local or UTC) in the working-tree log.md, in either the
    legacy `## [date] no-impact | why` form or the v0.2 `## date` + bulleted form."""
    try:
        text = read_text(os.path.join(wiki, "log.md"))
    except OSError:
        return False
    days = {date.today().isoformat(), datetime.now(timezone.utc).date().isoformat()}
    for m in re.finditer(r"^## \[?(\d{4}-\d{2}-\d{2})\]?[^\n]*$", text, re.M):
        if m.group(1) not in days:
            continue
        if "no-impact" in m.group(0).lower():
            return True
        if re.search(r"^\s*[-*].*no-impact", text[m.end():m.end() + 600], re.M | re.I):
            return True
    return False

def _git_path(rel):
    code, out = git("rev-parse", "--git-path", rel)
    return out if code == 0 and out else os.path.join(".git", rel)

# ---------------------------------------------------------------- hook (PostToolUse)

def run_hook():
    try:
        return _hook_inner()
    except Exception:
        return 0  # contract: the session hook NEVER crashes or blocks

def _patch_paths(patch_text):
    """File paths named by a Codex apply_patch payload."""
    out = []
    for m in re.finditer(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$", patch_text or "", re.M):
        out.append(m.group(1).strip())
    for m in re.finditer(r"^\*\*\* Move to: (.+)$", patch_text or "", re.M):
        out.append(m.group(1).strip())
    return out

def _hook_paths(payload):
    """Edited paths from a Claude Code (tool_input.file_path) or Codex (apply_patch) payload."""
    ti = payload.get("tool_input")
    if not isinstance(ti, dict):
        return []
    fp = ti.get("file_path")
    if isinstance(fp, str) and fp:
        return [fp]
    patch = ti.get("command") if isinstance(ti.get("command"), str) else ti.get("patch")
    if (payload.get("tool_name") or "") == "apply_patch" or (isinstance(patch, str) and "*** Begin Patch" in patch):
        return _patch_paths(patch if isinstance(patch, str) else "")
    return []

def _wiki_rel(fp, wiki):
    """Wiki-relative path of fp, or None. Case-blind containment is decided by a filesystem
    probe (samefile), never by sys.platform — WSL /mnt/c is case-insensitive under linux."""
    try:
        real_fp, real_wiki = os.path.realpath(fp), os.path.realpath(wiki)
        rel = os.path.relpath(real_fp, real_wiki)
    except (ValueError, OSError):
        return None
    if not rel.startswith(".."):
        return rel
    if real_fp.lower().startswith(real_wiki.lower() + os.sep):
        tail = real_fp[len(real_wiki) + 1:]
        try:
            if os.path.samefile(real_fp, os.path.join(real_wiki, tail)):
                return tail
        except OSError:
            return None
    return None

def _wiki_file_states(wiki):
    """{repo-relative path: "mtime_ns:size"} for every wiki page (a stat walk, raw/ excluded) plus untracked raw
    captures. A stat walk, not `git status`: an agent that edits and commits in ONE shell command leaves a clean
    tree by the time the hook runs (the eval's update runs did exactly that with `sed -i ... && git commit`)."""
    states = {}
    for root, dirs, files in os.walk(wiki):
        dirs[:] = [d for d in dirs if d not in RAW_DIRS and not d.startswith(".")]
        for f in files:
            if not f.endswith(".md"):
                continue
            p = os.path.join(root, f)
            try:
                st = os.stat(p)
            except OSError:
                continue
            states[p.replace(os.sep, "/")] = "%d:%d" % (st.st_mtime_ns, st.st_size)
    code, out = git("ls-files", "--others", "--exclude-standard", "--", *[os.path.join(wiki, r) for r in RAW_DIRS], strip=False)
    if code == 0:
        for p in [l.strip() for l in out.splitlines() if l.strip()]:
            try:
                st = os.stat(p)
            except OSError:
                continue
            states[p] = "%d:%d" % (st.st_mtime_ns, st.st_size)
    return states


def _load_seen():
    try:
        with open(HOOK_SEEN_PATH, encoding="utf-8") as f:
            d = json.load(f)
            return d if isinstance(d, dict) else {}
    except (OSError, ValueError):
        return {}


def _save_seen(states):
    try:
        os.makedirs(OKF_DIR, exist_ok=True)
        with open(HOOK_SEEN_PATH, "w", encoding="utf-8") as f:
            json.dump(states, f)
    except OSError:
        pass


def _changed_since_last_hook(wiki):
    """Wiki files written by ANY tool since the previous hook run. Agents write pages with shell heredocs as
    often as with Edit/Write (the eval's Sonnet 5.5 executor did so in every bootstrap and migration), and a
    hook keyed on file_path alone never saw those writes."""
    now = _wiki_file_states(wiki)
    if not os.path.isfile(HOOK_SEEN_PATH):
        # no baseline yet (hooks installed mid-session, or SessionStart did not run): record one silently —
        # treating every existing page as "just written" would auto-log and nudge the whole wiki at once
        _save_seen(now)
        return []
    seen = _load_seen()
    _save_seen(now)
    return [p for p, sig in sorted(now.items()) if seen.get(p) != sig]


def _hook_inner():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    if not isinstance(payload, dict):
        return 0
    paths = _hook_paths(payload)
    chdir_repo_root()
    cfg = load_config()
    wiki = find_wiki_dir(cfg)
    if not wiki:
        return 0
    # tool-agnostic: whatever wrote to the wiki (Edit, Write, apply_patch, a shell heredoc, a script),
    # process every wiki file whose state changed since the last hook run, plus any explicitly named path
    root = os.getcwd()
    paths = sorted(set(paths) | {os.path.join(root, p) for p in _changed_since_last_hook(wiki)})
    if not paths:
        return 0
    notes = []
    # auto-log only edits that are still UNCOMMITTED: they ride along with the agent's next commit. An edit the
    # agent already committed (edit + commit in one shell command) is recorded by git; logging it would leave
    # log.md dirty after the agent's last commit. Quality nudges still apply either way.
    code, st_out = git("status", "--porcelain", "--untracked-files=all", "--", wiki, strip=False)
    uncommitted = set(porcelain_paths(st_out)) if code == 0 else None
    for fp in paths:
        rel = _wiki_rel(fp, wiki)
        if rel is None:
            continue
        top = rel.split(os.sep, 1)[0]
        if top in RAW_DIRS:
            notes.append("okf: captured %s under %s/%s/ — `git add` it before finishing; untracked evidence does not survive `git clean`."
                         % (os.path.basename(fp), wiki, top))
            continue
        if os.path.basename(fp).lower() == "index.md":
            mism = index_mismatches(wiki, os.path.dirname(rel))
            if mism:
                notes.append("okf: %s does not reuse the description of %s verbatim — index entries must copy each page's description."
                             % (rel, ", ".join(mism[:4])))
            continue
        if not fp.endswith(".md") or os.path.basename(fp).lower() in RESERVED:
            continue
        try:
            fm = parse_frontmatter(read_text(fp))
            missing = [k for k in ("type", "title", "description") if not (fm or {}).get(k)]
            if fm is None or missing:
                notes.append("okf: %s is missing frontmatter %s — add before finishing." % (rel, "/".join(missing) if missing else "block"))
            di = description_issue((fm or {}).get("description"))
            if di:
                notes.append("okf: %s %s." % (rel, di))
        except OSError:
            pass
        repo_rel = (wiki + "/" + rel.replace(os.sep, "/"))
        if uncommitted is None or repo_rel in uncommitted:
            append_daily_log(wiki, rel)  # auto-log: uncommitted leaf wiki page edits only
    touched = [r for r in (_wiki_rel(fp, wiki) for fp in paths)
               if r is not None and os.path.basename(r).lower() != "log.md" and r.split(os.sep, 1)[0] not in RAW_DIRS]
    if touched:  # pages or indexes this session wrote; log.md is excluded because the auto-log itself writes it
        dead = dead_index_entries_on_disk(wiki)
        if dead:
            notes.append("okf: index entries for pages that do not exist: %s — write each page, remove the entry, or say "
                         "'planned' on its line (lint error; the pre-commit hook blocks wiki commits until fixed)."
                         % ", ".join("%s → %s" % (i, l) for i, l in dead[:4]))
    if notes:
        # plain stdout on exit 0 goes to the debug log only; additionalContext is the documented
        # channel that reaches the model (identical shape under Codex)
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": " ".join(notes)}}))
    return 0

def _lock(fh):
    try:
        import fcntl
        fcntl.flock(fh, fcntl.LOCK_EX)
    except ImportError:
        try:
            import msvcrt
            msvcrt.locking(fh.fileno(), msvcrt.LK_LOCK, 1)
        except (ImportError, OSError):
            pass

def append_daily_log(wiki, page_rel):
    """Idempotent auto entry: one '## [DATE] auto | session edits' block per day, inserted ABOVE
    the newest entry but BELOW any preamble prose under the title (inserting at the first
    non-blank line stranded that prose one entry deeper every day — production finding).
    Lock-guarded; preserves the file's newline style (CRLF logs are not rewritten wholesale)."""
    log_path = os.path.join(wiki, "log.md")
    lock_path = os.path.join(OKF_DIR, "log.lock") if os.path.isdir(OKF_DIR) else log_path + ".lock"
    lock = None
    try:
        lock = open(lock_path, "w")
        _lock(lock)
        today = date.today().isoformat()
        header = "## [%s] auto | session edits" % today
        bullet = "- %s" % page_rel
        raw = ""
        if os.path.isfile(log_path):
            with open(log_path, "rb") as f:
                raw = f.read().decode("utf-8-sig", errors="replace")
        nl = "\r\n" if "\r\n" in raw else "\n"
        lines = raw.replace("\r\n", "\n").splitlines()
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
            at = next((i for i, ln in enumerate(lines) if ln.startswith("## ")), None)
            if at is None:
                at = len(lines)
                while at > 0 and lines[at - 1] == "":
                    at -= 1
                lines[at:at] = ["", header, bullet]
            else:
                lines[at:at] = [header, bullet, ""]
        with open(log_path, "w", encoding="utf-8", newline="") as f:
            f.write(nl.join(lines) + nl)
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
    """Prints CURRENT only when provably nothing knowledge-relevant changed since the anchor: no
    UNCERTIFIED commit (code touched, wiki untouched, no no-impact marker) and no worktree change
    outside the wiki. Commits that already carried their wiki update are excluded, so the output is
    a short per-commit list, not hundreds of flat paths. Every git failure degrades to STALE."""
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
        print("NO-STATE: no recorded anchor in this clone — anchor to the last wiki-touching commit with "
              "`python3 .okf/lint.py state-update --from-last-wiki-commit`, then re-run noop-check and review what it lists")
        return 0
    code, _ = git("cat-file", "-e", last + "^{commit}")
    if code != 0:
        print("STALE: recorded gitHead %s no longer exists (rebase/gc?) — run a full update pass and re-stamp" % last[:8])
        return 0
    uncertified = []
    if last != head:
        commits = _commits_since(last)
        if commits is None:
            print("STALE: could not compute %s..HEAD — treat as needing review" % last[:8])
            return 0
        for sha, subj, marker, paths in commits:
            code_paths = [p for p in paths if _is_code(p, wiki)]
            if code_paths and not marker and not _touches_wiki(paths, wiki):
                uncertified.append((sha, subj, code_paths))
    code, out = git("status", "--porcelain", strip=False)
    if code != 0:
        print("STALE: git status failed — treat as needing review")
        return 0
    outside = sorted(c for c in set(porcelain_paths(out)) if _is_code(c, wiki))
    if not uncertified and not outside:
        print("CURRENT: no uncertified commit and no worktree change outside %s/ since %s — skip the update, wiki is current." % (wiki, last[:8]))
        return 0
    print("STALE: %d uncertified commit(s) and %d uncommitted path(s) outside %s/ since %s. Review PER COMMIT (commits that already touched the wiki are not listed):"
          % (len(uncertified), len(outside), wiki, last[:8]))
    for sha, subj, code_paths in uncertified[:20]:
        top = sorted({p.split("/", 1)[0] for p in code_paths})
        print("  commit %s %s — %d path(s): %s" % (sha[:8], subj[:60], len(code_paths), ", ".join(top[:6])))
    if len(uncertified) > 20:
        print("  ... +%d more commit(s)" % (len(uncertified) - 20))
    for c in outside[:20]:
        print("  changed: " + c)
    if len(outside) > 20:
        print("  ... +%d more" % (len(outside) - 20))
    print("  git log %s..HEAD --stat" % last)
    print("After updating: commit the wiki change (the post-commit hook advances the anchor), or if you reviewed the diff and it has no doc impact: python3 .okf/lint.py state-update --mark-reviewed")
    return 0

def run_state_update(mark_reviewed=False, auto=False, from_last_wiki=False):
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
    anchor = head
    if from_last_wiki:
        code, lastw = git("log", "-1", "--format=%H", "--", wiki)
        if code == 0 and re.fullmatch(r"[0-9a-f]{40}", lastw or ""):
            anchor = lastw
    new_sha = wiki_tree_sha(wiki)
    state = load_state()
    if state.get("wikiSha256") == new_sha and state.get("gitHead") == anchor:
        print("okf: nothing changed — state file NOT rewritten (churn guard)")
        return 0
    if state.get("wikiSha256") == new_sha and not (mark_reviewed or auto or from_last_wiki):
        print("okf: wiki content unchanged — NOT rewritten (churn guard). If you reviewed the diff and it has "
              "no doc impact, advance the anchor with: python3 .okf/lint.py state-update --mark-reviewed")
        return 0
    os.makedirs(OKF_DIR, exist_ok=True)
    cmd = "state-update" + (" --mark-reviewed" if mark_reviewed else "") + (" --auto" if auto else "") + (" --from-last-wiki-commit" if from_last_wiki else "")
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump({"updatedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                   "command": cmd, "gitHead": anchor, "wikiSha256": new_sha,
                   "lintVersion": OKF_LINT_VERSION}, f, indent=2)
        f.write("\n")
    print("okf: state updated (gitHead %s%s)" % (anchor[:8], ", reviewed-no-impact" if mark_reviewed else (", auto" if auto else "")))
    return 0

def run_post_commit():
    """Git post-commit: when the commit just made touched the wiki (not raw/), advance the per-clone
    anchor to it — the review anchor then follows normal work with no manual step."""
    root = chdir_repo_root()
    cfg = load_config()
    wiki = find_wiki_dir(cfg)
    if not root or not wiki or cfg.get("profile") == "lite":
        return 0
    code, out = git("diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD", strip=False)
    if code != 0:
        return 0
    if _touches_wiki([l.strip() for l in out.splitlines() if l.strip()], wiki):
        return run_state_update(auto=True)
    return 0

def run_post_rewrite():
    """Git post-rewrite (amend/rebase): stdin carries `old new` pairs; if the recorded anchor was
    rewritten, follow it instead of going STALE forever."""
    root = chdir_repo_root()
    if not root:
        return 0
    state = load_state()
    old_anchor = state.get("gitHead")
    if not old_anchor:
        return 0
    try:
        pairs = sys.stdin.read().splitlines()
    except (OSError, ValueError):
        return 0
    for line in pairs:
        parts = line.split()
        if len(parts) >= 2 and parts[0] == old_anchor and re.fullmatch(r"[0-9a-f]{40}", parts[1]):
            state["gitHead"] = parts[1]
            state["command"] = "post-rewrite"
            state["updatedAt"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
            with open(STATE_PATH, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
                f.write("\n")
            print("okf: anchor remapped %s -> %s" % (old_anchor[:8], parts[1][:8]))
            return 0
    return 0

def _version_tuple(v):
    return tuple(int(x) for x in re.findall(r"\d+", v or "")[:3])


def run_session_start():
    """SessionStart hook (Claude Code and Codex): prints the pointer (stdout reaches the model for
    this event) and records the session base HEAD so the Stop gate can see commits made during
    this session. Never rewrites the base on a compaction restart."""
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        payload = {}
    root = chdir_repo_root()
    cfg = load_config()
    wiki = find_wiki_dir(cfg)
    if not root or not wiki:
        return 0
    source = (payload.get("source") if isinstance(payload, dict) else None) or "startup"
    code, head = git("rev-parse", "HEAD")
    if source != "compact" and code == 0 and re.fullmatch(r"[0-9a-f]{40}", head or ""):
        try:
            os.makedirs(OKF_DIR, exist_ok=True)
            with open(SESSION_HEAD_PATH, "w", encoding="utf-8") as f:
                f.write(head + "\n")
        except OSError:
            pass
    _save_seen(_wiki_file_states(wiki))
    print("OKF knowledge base active: read %s/index.md first; follow relative links. Persist durable findings to %s/ as you work "
          "(single writer; subagents read-only). Obligations: AGENTS.md -> ## Knowledge base." % (wiki, wiki))
    if cfg.get("profile") != "lite":
        hp_code, hp = git("config", "core.hooksPath")
        pc = _git_path("hooks/pre-commit")
        try:
            pc_ok = os.path.isfile(pc) and ".okf" in read_text(pc)
        except OSError:
            pc_ok = False
        if (hp_code != 0 or not hp) and not pc_ok:
            print("okf: git hooks are not installed in this clone — run /okf (or: git config core.hooksPath .okf/githooks).")
    # an installed skill newer than this repo's copy: say so every session, or the upgrade never happens (eval: plain
    # `/okf` on a current wiki ran an update and left a two-versions-old .okf/ in place)
    newest = None
    for cand in ("~/.claude/skills/okf/scripts/okf_lint.py", "~/.codex/skills/okf/scripts/okf_lint.py"):
        try:
            m = re.search(r'OKF_LINT_VERSION = "([0-9.]+)"', read_text(os.path.expanduser(cand)))
        except OSError:
            continue
        if m and _version_tuple(m.group(1)) > _version_tuple(OKF_LINT_VERSION) and (not newest or _version_tuple(m.group(1)) > _version_tuple(newest)):
            newest = m.group(1)
    if newest:
        print("okf: this repo's .okf/ is okf %s; the installed okf skill is %s — run /okf to upgrade lint, hooks and contract."
              % (OKF_LINT_VERSION, newest))
    skill_copy = os.path.expanduser("~/.claude/skills/okf/scripts/okf_lint.py")
    try:
        if os.path.isfile(skill_copy):
            with open(__file__, "rb") as a, open(skill_copy, "rb") as b:
                mine, theirs = hashlib.sha256(a.read()).hexdigest(), hashlib.sha256(b.read()).hexdigest()
            if mine != theirs and ('OKF_LINT_VERSION = "%s"' % OKF_LINT_VERSION) in read_text(skill_copy):
                print("okf: this repo's .okf/lint.py differs from the installed skill copy at the same version — review it; "
                      "repo-controlled code runs on every edit, stop and commit.")
    except OSError:
        pass
    return 0

# ---------------------------------------------------------------- stop-gate / pre-commit

def run_stop_gate():
    """Stop hook (Claude Code and Codex): exit 2 + stderr reason blocks; exit 0 + '{}' allows (Codex
    requires JSON stdout on allow). Checks BOTH the uncommitted worktree AND the commits made since
    this session started (.okf/session-head from the SessionStart hook), so committing code no
    longer bypasses the gate. Escapes: a wiki page or log entry touched this session, a no-impact
    log line dated today, or an `Okf-Impact: none` commit trailer. raw/ captures never count."""
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        payload = {}
    if isinstance(payload, dict) and payload.get("stop_hook_active"):
        print("{}")
        return 0
    root = chdir_repo_root()
    cfg = load_config()
    wiki = find_wiki_dir(cfg)
    if not root or not wiki or cfg.get("profile") == "lite":
        print("{}")
        return 0
    code, out = git("status", "--porcelain", strip=False)
    if code == 124:
        sys.stderr.write("okf stop-gate: git timed out while checking the worktree — retry (the gate fails closed by design).\n")
        return 2
    if code != 0:
        print("{}")
        return 0
    paths = porcelain_paths(out)
    wiki_touched = _touches_wiki(paths, wiki)
    code_changed = [p for p in paths if _is_code(p, wiki)]
    base = None
    try:
        base = read_text(SESSION_HEAD_PATH).strip()
    except OSError:
        pass
    hcode, head = git("rev-parse", "HEAD")
    committed_code, committed_wiki, marker = [], False, False
    if base and re.fullmatch(r"[0-9a-f]{40}", base) and hcode == 0 and base != head:
        c2, _ = git("cat-file", "-e", base + "^{commit}")
        for sha, subj, mk, cpaths in ((_commits_since(base) if c2 == 0 else None) or []):
            if _touches_wiki(cpaths, wiki):
                committed_wiki = True
            if mk:
                marker = True
            committed_code += [p for p in cpaths if _is_code(p, wiki)]
    if (code_changed or committed_code) and not (wiki_touched or committed_wiki or marker or _no_impact_today(wiki)):
        example = (code_changed or committed_code)[0]
        sys.stderr.write(
            "okf stop-gate: %d uncommitted and %d committed non-wiki change(s) this session (e.g. %s) but no wiki page or log entry was touched. "
            "Update the affected %s/ page(s) and append to %s/log.md — or, if this work truly has no knowledge impact, append one line to "
            "%s/log.md dated today: '## [%s] no-impact | <what and why>'. See AGENTS.md -> Knowledge base.\n"
            % (len(code_changed), len(committed_code), example, wiki, wiki, wiki, date.today().isoformat()))
        return 2
    print("{}")
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
        code, raw_untracked = git("ls-files", "--others", "--exclude-standard", "--", *[os.path.join(wiki, r) for r in RAW_DIRS], strip=False)
        raw_untracked = [l for l in (raw_untracked or "").splitlines() if l.strip()]
        if code == 0 and raw_untracked:
            print("okf WARNING: %d untracked capture(s) under %s/raw while wiki pages are being committed (e.g. %s) — "
                  "`git add` the evidence the pages cite, or gitignore it deliberately." % (len(raw_untracked), wiki, raw_untracked[0]))
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
        # every index.md in the commit must point at pages in the commit (staged tree, not disk)
        code, ls_out = git("ls-files", "-z", "--", wiki, strip=False)
        in_commit = {x[len(wiki) + 1:] for x in (ls_out or "").split("\0") if x.startswith(wiki + "/")} if code == 0 else set()
        for rel in sorted(in_commit):
            if os.path.basename(rel).lower() != "index.md" or rel.split("/", 1)[0] in RAW_DIRS:
                continue
            code, blob = git("show", ":%s/%s" % (wiki, rel), strip=False)
            if code != 0:
                continue
            for planned, link in missing_index_targets(rel, blob, lambda t: t.replace(os.sep, "/") in in_commit):
                if not planned:
                    blocking.append(dead_index_message(rel, link))
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

def _is_okf_entry(entry):
    if not isinstance(entry, dict):
        return False
    return any(any(m in (h.get("command") or "") for m in OKF_HOOK_MARKERS)
               for h in (entry.get("hooks") or []) if isinstance(h, dict))

def run_install_hooks(fragment_path, target="claude"):
    """Deep-merge a {'hooks': {...}} fragment into .claude/settings.json (or .codex/hooks.json with
    --target codex) WITHOUT touching sibling keys. Idempotent; an older okf entry for the same event
    is REPLACED (template upgrade), foreign entries are kept; events listed in config
    `hooksDisabled` are never (re)installed; the write is atomic and the backup lives under .okf/."""
    root = chdir_repo_root()
    if not root:
        print("okf: not a git repository — run from the target repo")
        return 1
    if not fragment_path:
        print("okf: usage: install-hooks <fragment.json> [--target claude|codex]")
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
    disabled = set(load_config().get("hooksDisabled") or [])
    spath = os.path.join(".codex", "hooks.json") if target == "codex" else os.path.join(".claude", "settings.json")
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
        os.makedirs(OKF_DIR, exist_ok=True)
        with open(os.path.join(OKF_DIR, os.path.basename(spath) + ".bak"), "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
            f.write("\n")
    os.makedirs(os.path.dirname(spath), exist_ok=True)
    hooks = settings.setdefault("hooks", {})
    added = replaced = skipped = 0
    for event, entries in frag_hooks.items():
        if not isinstance(entries, list):
            continue
        existing = hooks.setdefault(event, [])
        if event in disabled:
            existing[:] = [e for e in existing if not _is_okf_entry(e)]
            skipped += 1
            if not existing:
                hooks.pop(event, None)
            continue
        for entry in entries:
            if entry in existing:
                continue
            olds = [e for e in existing if _is_okf_entry(e)]
            for e in olds:
                existing.remove(e)
            replaced += 1 if olds else 0
            existing.append(entry)
            added += 1
    tmp = spath + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")
    os.replace(tmp, spath)
    print("okf: merged %d new hook entr%s into %s (%d upgraded, %d event(s) disabled by config) — sibling settings untouched%s"
          % (added, "y" if added == 1 else "ies", spath, replaced, skipped,
             " (backup: %s)" % os.path.join(OKF_DIR, os.path.basename(spath) + ".bak") if had_existing else ""))
    return 0

# ---------------------------------------------------------------- main

# ---------------------------------------------------------------- claims (truth-audit sampler)
# Production audit (2026-10, 600 claims over 4 wikis): the wrong claims were almost all exact numbers and status lines,
# so the sampler weights those kinds; the agent then checks each sentence against the repo (SKILL.md §Audit).

CLAIM_WEIGHTS = {"status": 4, "number": 3, "code": 2, "other": 1}
STATUS_RE = re.compile(r"\b(blockers?|blocked|not supported|unsupported|refus\w*|out of scope|not yet|todo|pending|deprecated|"
                       r"disabled|workaround|work around|until|unmet|open (?:blocker|question|issue)|stays|planned|missing|"
                       r"broken|fails?|failing|not implemented|no longer)\b", re.I)
SKIP_SECTIONS = ("sources", "related", "references", "see also")


def _claim_kind(sentence):
    if STATUS_RE.search(sentence):
        return "status"
    bare = re.sub(r"\[\^?S?\d+\]|\b\d{4}-\d{2}-\d{2}\b|\bADR-\d+\b|`[^`]*`", " ", sentence)
    if re.search(r"\d", bare):
        return "number"
    if "`" in sentence:
        return "code"
    return "other"


def _page_sources(text, fm):
    src = {}
    for m in re.finditer(r"^\s*(?:[-*]\s+)?\[(S\d+)\]\s+(?:Local:\s*)?(.+)$", text, re.M):
        src[m.group(1)] = m.group(2).strip()
    for m in re.finditer(r"^\[\^([\w.-]+)\]:\s*(.+)$", text, re.M):     # OKF v0.2 footnotes
        src[m.group(1)] = m.group(2).strip()
    default = [v for k in ("source", "resource") for v in [(fm or {}).get(k)] if isinstance(v, str) and v and "<" not in v]
    # no per-sentence marker and no source field: the page's own Sources list is the best hint
    return src, default or list(src.values())[:3]


def claim_candidates(rel, text):
    """(line, sentence) units of a leaf page body: paragraphs and bullet items split into sentences; headings,
    code blocks, link-only lines and the Sources/Related sections are skipped."""
    fm = parse_frontmatter(text) if text.startswith("---") else {}
    src, default = _page_sources(text, fm if isinstance(fm, dict) else {})
    lines = text.splitlines()
    start = 0
    if text.startswith("---"):
        end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), 0)
        start = end + 1
    units, buf, buf_line, section, fence = [], [], None, "", False

    def flush():
        if buf:
            units.append((buf_line, " ".join(x.strip() for x in buf)))
        buf.clear()

    for i in range(start, len(lines)):
        line = lines[i]
        if line.lstrip().startswith("```"):
            fence = not fence
            flush()
            continue
        if fence:
            continue
        h = re.match(r"^#{1,6}\s+(.*)", line)
        if h:
            flush()
            section = h.group(1).strip().lower()
            continue
        if any(section.startswith(x) for x in SKIP_SECTIONS) or line.lstrip().startswith(("<!--", "|")):
            flush()
            continue
        if not line.strip():
            flush()
            continue
        if re.match(r"^\s*([-*+]|\d+\.)\s+", line):
            flush()
            line = re.sub(r"^\s*([-*+]|\d+\.)\s+", "", line)
        if not buf:
            buf_line = i + 1
        buf.append(line)
    flush()
    out = []
    for ln, para in units:
        for sent in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9`*\"(\[])", para):
            plain = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", sent)
            if len(re.findall(r"[A-Za-z0-9]+", plain)) < 6:
                continue
            ids = re.findall(r"\[\^?(S\d+)\]", sent) + re.findall(r"\[\^([\w.-]+)\]", sent)
            inline = [l for l in re.findall(r"\]\(([^)\s#]+)", sent) if not l.endswith(".md") or l.startswith("..")]
            inline += [t for t in re.findall(r"`([^`\s]+)`", sent) if "/" in t or re.search(r"\.(py|ts|js|mjs|json|toml|ya?ml|sh|sql|md)$", t)]
            cites = list(dict.fromkeys([src[k] for k in ids if k in src] + inline)) or default
            out.append({"id": "%s:%d" % (rel, ln), "page": rel, "line": ln, "kind": _claim_kind(sent), "text": sent.strip(),
                        "cites": cites})
    return out


def run_claims(args):
    import random
    def opt(name, default):
        if name in args and args.index(name) + 1 < len(args):
            try:
                return int(args[args.index(name) + 1])
            except ValueError:
                pass
        return default
    n = max(1, opt("--n", 12))
    seed = opt("--seed", date.today().toordinal())
    chdir_repo_root()
    wiki = find_wiki_dir(load_config())
    if not wiki:
        print(json.dumps({"error": "no wiki directory found"}))
        return 1
    cands = []
    for rel, is_leaf in iter_pages(wiki):
        if not is_leaf:
            continue
        try:
            cands += claim_candidates(rel, read_text(os.path.join(wiki, rel)))
        except OSError:
            continue
    cands.sort(key=lambda c: (c["page"], c["line"], c["text"]))
    for k, c in enumerate(cands):     # several sentences can share a paragraph's line
        c["id"] = "%s#%d" % (c["id"], sum(1 for d in cands[:k] if d["page"] == c["page"] and d["line"] == c["line"]) + 1)
    rng = random.Random(seed)
    # weighted sampling without replacement (key = u^(1/w)), at most ~2n/pages per page so one long page cannot fill it
    keyed = sorted(cands, key=lambda c: rng.random() ** (1.0 / CLAIM_WEIGHTS[c["kind"]]), reverse=True)
    n_pages = len({c["page"] for c in cands}) or 1
    cap = max(2, -(-2 * n // n_pages))
    picked, per_page = [], {}
    for c in keyed:
        if len(picked) >= n:
            break
        if per_page.get(c["page"], 0) < cap:
            picked.append(c)
            per_page[c["page"]] = per_page.get(c["page"], 0) + 1
    for c in keyed:   # pages ran out under the cap: fill from the rest
        if len(picked) >= n:
            break
        if c not in picked:
            picked.append(c)
    picked.sort(key=lambda c: (c["page"], c["line"]))
    kinds = {}
    for c in cands:
        kinds[c["kind"]] = kinds.get(c["kind"], 0) + 1
    # one sentence per line: still valid JSON, and a `| head` in the caller cannot silently drop half the sample
    head = json.dumps({"wiki": wiki, "seed": seed, "candidates": len(cands), "candidates_by_kind": kinds,
                       "sampled": len(picked)}, ensure_ascii=False)
    body = ",\n".join(" " + json.dumps(c, ensure_ascii=False) for c in picked)
    print(head[:-1] + ', "claims": [\n' + body + "\n]}")
    return 0


USAGE = """okf lint %s — usage: python3 .okf/lint.py <subcommand> [flags]
  lint [--quiet]                       structure guard (exit 1 on errors)
  noop-check                           CURRENT / STALE (per-commit) / NO-STATE
  state-update [--mark-reviewed|--auto|--from-last-wiki-commit]
  stop-gate                            Stop hook: exit 2 blocks, prints {} on allow
  hook                                 PostToolUse hook (Claude file_path or Codex apply_patch)
  session-start                        SessionStart hook: pointer + session base HEAD
  pre-commit | post-commit | post-rewrite   git hooks
  install-hooks <fragment.json> [--target claude|codex]
  claims [--n 12] [--seed S]           truth-audit sample (JSON); read-only
""" % OKF_LINT_VERSION

def main():
    args = sys.argv[1:]
    cmd = args[0] if args and not args[0].startswith("-") else ("lint" if not args else args[0])
    if cmd in ("-h", "--help", "help"):
        print(USAGE)
        return 0
    if cmd == "hook":
        return run_hook()
    if cmd == "session-start":
        return run_session_start()
    if cmd == "noop-check":
        return run_noop_check()
    if cmd == "state-update":
        return run_state_update(mark_reviewed="--mark-reviewed" in args, auto="--auto" in args,
                                from_last_wiki="--from-last-wiki-commit" in args)
    if cmd == "stop-gate":
        return run_stop_gate()
    if cmd == "pre-commit":
        return run_pre_commit()
    if cmd == "post-commit":
        return run_post_commit()
    if cmd == "post-rewrite":
        return run_post_rewrite()
    if cmd == "install-hooks":
        target = args[args.index("--target") + 1] if "--target" in args and args.index("--target") + 1 < len(args) else "claude"
        frag = next((a for a in args[1:] if not a.startswith("-") and a != target), None)
        return run_install_hooks(frag, target=target)
    if cmd == "claims":
        return run_claims(args)
    if cmd == "lint" or cmd.startswith("-"):
        return run_lint(quiet="--quiet" in args)
    print("okf: unknown subcommand %r\n%s" % (cmd, USAGE))
    return 2


if __name__ == "__main__":
    sys.exit(main())
