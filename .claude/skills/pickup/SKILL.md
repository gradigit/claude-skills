---
name: pickup
description: The consumer counterpart to handoff/handoff-fresh/wrap. Picks up what was handed off AND where work left off. Manual command entry point is /pickup. Producer-agnostic — detects whichever artifact was written (bundle, canonical HANDOFF.md, or FORGE/CLAUDE pointers), reads the full First-Steps set with enforced receipts, replays the verbatim last exchange, and runs a stakes-tiered verify-still-true gate before acting. Routes the bare "read HANDOFF.md" path here so the default gets the strong behavior. Do NOT use to WRITE a handoff — use handoff/wrap for that.
license: MIT
metadata:
  version: "1.2.0"
  author: gradigit
  updated: "2026-06-20"
  tags:
    - context
    - handoff
    - resume
    - continuity
    - session
  triggers:
    - "/pickup"
    - "pickup"
    - "pick up where we left off"
    - "catch up"
    - "where were we"
    - "resume the session"
    - "continue from the handoff"
    - "read HANDOFF.md"
    - "read handoff.md and continue"
---

# Pickup

The **consumer** skill for the handoff family. `/handoff`, `/handoff-fresh`, and
`/wrap` *write* session-resume state; `/pickup` *reads* it. It picks up what was
handed off and resumes exactly where work left off.

`/pickup` is the symmetric counterpart to `/wrap`: `/wrap` closes a session,
`/pickup` opens one.

## Why this is a skill, not just "read the files"

The guarantee lives in **this skill's behavior**, not in text inside the
generated artifact. Old, hand-written, or trimmed `HANDOFF.md` files carry a weak
or absent read-contract, so an agent that just "reads the file" silently
shallow-ingests: it reads one file, declares done, and acts on stale state.
`/pickup` enforces read-all + receipts + verify **regardless of what the artifact
contains**.

## Command Contract (Explicit, Manual)

- Primary entry point: `/pickup`
- Natural-language triggers are allowed when intent is explicit (see frontmatter)
- **Route the bare "read HANDOFF.md" path here** — it is the highest-traffic,
  weakest-enforced resume path; `/pickup` gives it the strong behavior
- `/pickup` is **non-mutating by default**: it reads, verifies, and reports. It
  writes no files unless `--write-receipt` is passed
- Do **not** use `/pickup` to generate or update a handoff — that is
  `/handoff` / `/handoff-fresh` / `/wrap`

## Arguments

- `--write-receipt`: Persist the read receipt to `.pickup-receipt.md` (opt-in;
  default is to print the receipt inline only)
- `--stakes <auto|low|high>`: Override stakes detection for the verify gate
  (default `auto` — see Step 6)
- `--artifact <path>`: Skip detection and pick up from an explicit artifact

## Workflow

```
- [ ] 1. Detect candidate artifacts (precedence order) and pick the freshest
- [ ] 2. Section-select within the chosen artifact (newest era wins)
- [ ] 3. Read ALL required files; first reply is the per-file read receipt
- [ ] 4. Validate the receipt deterministically (validator script)
- [ ] 5. Read the verbatim Last Exchange FIRST and anchor the resume
- [ ] 6. Run the stakes-tiered verify-still-true gate
- [ ] 7. Reconcile claims vs reality; surface the handoff's open decisions
- [ ] 8. Output the 5-item resume contract
```

## Step 1: Detect candidate artifacts

List all candidates, then choose by **freshness first**: compare embedded date
headers (then file mtime). The rung order below is only a **tie-breaker** when
dates are equal or absent — it is *not* an absolute precedence. In particular, if
a canonical root `HANDOFF.md` is newer than the bundle (e.g. the user switched
back to `/handoff` after a `/handoff-fresh`), prefer the canonical file and flag
the stale bundle as historical.

1. **Fresh bundle** — `.handoff-fresh/current/handoff.md` (written by
   `/handoff-fresh` or `/wrap --with-fresh`). Use the bundle path when it is
   present **and not older** than the root `HANDOFF.md`.
2. **Root `HANDOFF.md`** — disambiguate by reading it:
   - If it contains the schema marker `<!-- HANDOFF-SCHEMA ... producer=handoff-fresh-bridge -->`
     **or** a `# Context Handoff Bridge` / "read this first instead" pointer →
     it is a **bridge**; redirect to the bundle and treat as case (1).
   - Otherwise it is a **canonical** handoff (`/handoff` / `/wrap`).
3. **FORGE-\* set** (`FORGE-HANDOFF.md` / `FORGE-STATUS.md`) and **CLAUDE.md
   resume pointers** — repo-specific fallback when no handoff exists.

**Identify the producer.** Read the top-of-file schema marker if present:
`<!-- HANDOFF-SCHEMA v3.0.0 producer=handoff -->`. The marker tells you the
schema version and which producer wrote it. **Match on the marker FIRST**, and
fall back to heading text only when the marker is absent (hand-written/old files
have neither — those route to the skill-enforced path with a "weak contract" flag).

**Flag everything not chosen as historical.** When multiple artifacts disagree on
timestamp (e.g. CLAUDE.md points at a March `FORGE-*` set while `HANDOFF.md` is
from June), pick the freshest and explicitly list the others as historical in the
output drift flags — never silently merge them.

**Scope to your current checkout first — recency across checkouts is NOT precedence.**
When the repo has parallel worktrees / sibling checkouts (the user runs several
sessions at once, each in its own checkout to avoid clobbering), the authoritative
handoff for THIS session is the one in **your current checkout (`cwd`)** — *not* the
globally-freshest one. A *newer* handoff in a sibling checkout almost always belongs
to a **different parallel session**; adopting it is the cross-worktree mistake this
rule exists to prevent. Determine your checkout root once (`git rev-parse --show-toplevel`).

Order of resolution:
1. **Current checkout wins.** If `cwd`'s checkout has a `HANDOFF.md` / `.handoff-fresh/`,
   that is the default authoritative source — use it. Do **not** switch to a sibling
   just because it is newer.
2. **Cross-checkout is a deliberate, flagged fallback**, used only when (a) the current
   checkout has no handoff, or (b) the current handoff *and* the user's stated intent
   both point elsewhere (e.g. `cwd`'s handoff says "no active work here" and the user
   asks for "the auth work" living in `worktrees/feature-auth/`). Enumerate candidates
   (`git worktree list`, plus sibling `<repo>-<suffix>` checkouts), pick the one
   **matching the user's intent — never the merely-newest**, and state the cross-checkout
   jump explicitly in the resume contract.
3. **When several checkouts have handoffs and intent doesn't disambiguate, surface the
   list and ask which** — silent freshest-wins is the bug. Always confirm the chosen
   handoff's own recorded checkout/branch matches where you actually are; a mismatch
   (handoff written for `worktrees/X` but you are in `worktrees/Y`) is a drift flag.

**Establish direction-of-drift before calling anything stale.** A freshness verdict
needs evidence of *which side is older*, not merely that two sources disagree.
Gather: the embedded date headers compared side by side, file mtimes, and
`git log -1` on the conflicting files; bound staleness by comparing the handoff's
date to today. If no timestamps are recoverable, mark freshness **`unknown`** —
never assert **`stale`** from content-disagreement alone.

## Step 2: Section-select within the chosen artifact

A long-lived `HANDOFF.md` can accumulate multiple eras (more than one "First
Steps" / "READ FIRST" block). Select the **freshest section's** read list and mark
older blocks historical. This prevents reading a stale First-Steps list from an
earlier era.

## Step 3: Read all required files + emit receipts

Derive the required-read list:

- **Bundle path**: the 5-file Read Gate (`handoff.md`, `claude.md`, `todo.md`,
  `state.md`, `context.md`).
- **Canonical path**: the numbered files in the freshest "First Steps (Read in
  Order)" section.

Read **every** file in the list before replying. The **first substantive reply**
must be the per-file read receipt — one line per file:

```
- [x] <file> — <one-line takeaway>
```

Do **not** send interim one-file acknowledgements ("read HANDOFF.md, here's a
summary"). No partial reads. See [templates.md](templates.md) for the receipt
format.

**Anchor read-all to the chosen artifact's OWN directive.** Treat the live
artifact's bootstrap line and its "First Steps (Read in Order)" as the authority for
*what* to read and in *what order* — quote that directive when you receipt, so you
demonstrate obeying the authoritative handoff rather than inferring the read-all from
this skill's routing. Follow the artifact's stated order (e.g. `../../README.md` then
`src/auth/session.py`), not an order of your own.

## Step 4: Validate the receipt (deterministic)

**Default (non-mutating):** self-check the receipt you just emitted against the
derived required list — every required file present, checked, with a non-empty,
non-placeholder takeaway. If any are missing, finish reading them and re-emit the
receipt before continuing. Do not proceed to verify/act on an incomplete receipt.

**To run the deterministic validator** (optional; relative to this skill dir),
materialize the receipt first, then point the script at it:

```bash
# Canonical path: write the receipt, then validate against the First Steps list
python3 scripts/validate_read_gate.py --receipt .pickup-receipt.md --required-from-firststeps HANDOFF.md   # needs --write-receipt

# Bundle path: the bundle already ships read-receipt.md
python3 scripts/validate_read_gate.py --bundle-dir .handoff-fresh/current
```

Exit `0` = PASS (every required file checked with a non-empty takeaway), exit `1`
= FAIL (missing entry, unchecked, or placeholder takeaway). The validator is the
same engine handoff-fresh uses, so PASS here means the same gate the bundle path
enforces.

## Step 5: Read the verbatim Last Exchange FIRST

Before reconstructing state from the (paraphrased) summary, open the verbatim
record and use it as the **exact resume anchor**:

- **Canonical**: the `## Last Exchange (Verbatim)` section (last user prompt, last
  assistant response, and load-bearing earlier directives, quoted).
- **Bundle**: the verbatim last-turn block in `session-log-chunk.md`.

Resume *as if the break never happened* — the verbatim exchange captures immediate
prior intent that a synthesis can lose. Distinguish **synthesis** (paraphrased
state, for fast orientation) from **evidence** (the verbatim exchange, for
zero-loss resume) and trust the evidence for the precise next move.

If the artifact has **no** verbatim section (old/hand-written), record it as a
**single** weak-contract line ("weak contract: hand-written, no verbatim/marker/verify
block") and fall back to the synthesis plus a freshness rebuild — do not silently
assume continuity. Do **not** expand a hand-written file's missing v3 scaffolding into
a multi-item blockers list; a missing marker/section is a contract note, **not** a
defect of the work. Reserve the repair offer (Step 7) for handoffs whose *claims are
false/stale*, not merely unmarked.

**Redaction + budget on replay** (consumer-side safety): the producer redacts at
write time, but old/hand-written handoffs never had a redaction pass. When
replaying the verbatim block, do not echo obvious secrets — mask anything that
looks like a key/token/password/connection-string with «redacted», and if the
block is oversized, quote only the decision-bearing portion. Flag an unredacted
old handoff as a drift item.

## Step 6: Verify-still-true gate (stakes-tiered)

A handoff captures *what was true when written*. Verify before trusting.

**Run the producer's Verify Block if present.** The upgraded handoff contract
emits a `## Verify Block` of `claim | check-command | expected` lines. Run each
check and compare to expected.

**Otherwise derive an advisory checklist**: do the First-Steps files still exist?
Is the tree clean / branch as claimed? Does `HEAD` match the handoff's "Last
commit"? Is the bundle older than its source docs (per syncing-docs alerts)? If a
`basis` fingerprint exists, diff stored-vs-recomputed (HEAD, branch, changed-file
set, test result).

**Tiering:**

| Tier | When | Behavior |
|------|------|----------|
| **Advisory** (default) | Low-stakes resume | Emit a checklist of assumptions to re-check; proceed, surfacing drift |
| **Blocking** | (a) the artifact declares a Verify Block, OR (b) **high-stakes** | Do **not** act until the named checks are re-run and pass |

**High-stakes detection (rule-based heuristic).** This is a keyword/intent check
over the artifact and the planned next action, not a script — so **default to
high-stakes when uncertain**. Treat the resume as high-stakes when ANY of these
hold:

- The **next action is writing code or a destructive/irreversible op**
  (edit/write/delete/move/reset/migrate/deploy/push) — the most reliable signal;
  lean on it.
- The artifact mentions a **live/production system, monitor, scheduler, daemon,
  cron/rearm job, deploy, trading, billing, or external side effects** (match
  synonyms, not just these literal words).
- A **Verify Block** is present (its existence means the producer wanted checks run).

`--stakes low|high` overrides this. When the signals are ambiguous, prefer
blocking. Report PASS / drift per check.

**Never fabricate a verification.** Report a check as `PASS` / `current` / "clean"
**only** if you actually ran it this turn and can quote its output. If you did not
run a check — no shell, skipped it, or only inferred it — label that line
**`assumed (unverified)`**. Do not state environment facts like "not a git repo",
"working tree clean", "HEAD matches", or "tests green" as *verified* when no command
produced that result. A fabricated PASS is worse than an honest "unverified": the
next agent trusts it. This is the inverse of acting-on-stale — here the danger is
inventing the verification itself.

> Why this exists: in a real resume on a live trading-signal system, the agent
> read two files, declared the system healthy, and did zero verification until the
> user had to interject "check current health before you rearm the monitor." The
> blocking tier exists to make that class of incident impossible.

## Step 7: Reconcile and surface open decisions

- Reconcile the handoff's claims against current `git` / `TODO.md` / live state;
  list mismatches as drift. Reconciliation includes **factual content claims** the
  handoff asserts about files (counts, config values, test results, "0 items left"):
  open the referenced file and compare — do not pass these through unchecked.
- **Commit to the designated next action.** If the handoff (its summary or verbatim
  Last Exchange) already names the next step, adopt it as the resume target — do not
  end with a redundant "Want me to proceed?" round-trip. Ask only the ONE genuinely
  blocking decision, and never bundle a blocking question with a proceed-confirmation.
- **Offer to repair a chosen-but-stale handoff.** When the authoritative handoff
  *itself* carries now-false claims (drift caught in Step 6), surface a concrete
  remediation — "re-run `/handoff` to correct these lines before the next `/clear` so
  the false claims don't re-mislead" — naming the specific lines. Stay non-mutating:
  offer, don't auto-edit.
- **Surface the handoff's open decisions/questions back to the user.** Use
  `ask-question` **only if genuinely blocked** — never to re-ask something the
  handoff already answered (a recurring failure: agents asking the user to
  re-supply context the handoff contained).

## Step 8: Output — the 5-item resume contract

Precede the contract with the per-file read receipt (Step 3) and the verify-gate
PASS/drift report (Step 6). Then always return these five items:

1. **Resume target** — which artifact was chosen (+ its date/commit), and which
   others were flagged historical.
2. **Freshness judgment** — `current | stale | unknown`, with the basis-diff /
   drift evidence.
3. **Next 1–3 actions** — the single prioritized next action plus runnable resume
   commands.
4. **Fallback path used** — "none — handoff found" or which detection rung / era
   was used.
5. **Blockers / drift flags** — failed verify checks, missing First-Steps files,
   timestamp divergence, plus any open decisions surfaced to the user. A
   hand-written file's missing v3 scaffolding (marker / Last Exchange / Verify Block)
   is **one** weak-contract line here, never a per-section findings list.

See [templates.md](templates.md) for the output template.

## Boundaries

ALWAYS:
- Read every required file before the first substantive reply
- Emit per-file receipts and validate them
- Read the verbatim Last Exchange before acting
- Run the verify gate; block on high-stakes / Verify-Block artifacts
- Pick the freshest artifact and flag the rest historical

NEVER:
- Shallow-ingest (read one file, summarize, stop)
- Mutate exported handoff artifacts during a live session (non-mutating reader;
  `--write-receipt` is the only opt-in write, to `.pickup-receipt.md`)
- Assume "newest file == current truth" without the freshness check
- Skip the rebuild/flag when the artifact is stale
- Re-ask the user for context the handoff already contains
- **Report an un-run check as verified** — label it `assumed (unverified)` instead
- **Adopt a sibling/worktree checkout's handoff because it is newer** than your current
  checkout's — recency is not cross-checkout precedence; the current checkout wins, and
  crossing checkouts is an intent-driven, explicitly-flagged fallback
- **Over-report on a minimal/hand-written artifact.** The weak-contract flag is a
  one-line internal note, not a graded critique. Do not enumerate the v3 sections a
  hand-written file "should" have as if they were findings, and do not narrate
  skill-internal routing/tiering ("blocking-tier intent", "schema-marker drift") as
  if it were session state. Keep output to grounded state + the next action.
- **Route the next session to a non-First-Steps file** — never tell it to read an
  oracle / ground-truth / scratch file that the chosen artifact's First Steps did
  not list.

## Reused Components

- **`scripts/validate_read_gate.py`** — deterministic receipt validator shared
  with handoff-fresh (regex receipt matching + non-empty/placeholder takeaway
  rejection, exit 0/1). The `--required-list` / `--required-from-firststeps` flags
  let it run on the canonical root `HANDOFF.md` path, not just the bundle.
  This copy must stay byte-identical to handoff-fresh's on the shared functions
  (enforced by the EVALUATIONS "validator parity" scenario).
- **Bundle/canonical detection markers** — `.handoff-fresh/current/` presence, the
  `<!-- HANDOFF-SCHEMA ... -->` marker, the `BEGIN/END SHARED-ONBOARDING-CONTEXT`
  block, the `# Context Handoff Bridge` heading, the canonical H1
  `# Context Handoff — <date>`, and the `First Steps (Read in Order)` heading.
- **Freshness-as-data** (from narrative-engine prior art, de-domained): current →
  resume; stale → treat as historical and rebuild from live sources. Freshness via
  **basis-diff** (stored vs recomputed) is stronger than a TTL; TTL is only a
  fallback when no basis exists.
- **LLM-wiki / OKF ingestion patterns**: index-first navigation, progressive
  disclosure (digest before raw chunk), source backlinks for verification, and a
  token budget on ingestion.

## Self-Evolution

Update this skill when:
1. **A resume shallow-ingests** despite `/pickup` — tighten the read-all/receipt gate
2. **A new producer/artifact shape appears** — extend the detection precedence
3. **A stale-state action slips through** — strengthen the verify gate or its high-stakes detection
4. **The handoff contract changes** — keep the schema-marker and Verify-Block parsing in sync

**Applied Learnings:**
- v1.2.0: **Parallel-worktree correctness.** Replaced the "pick the freshest match across
  worktrees" rule (which actively grabbed a sibling session's handoff) with **current-
  checkout-first**: the handoff in `cwd`'s checkout is authoritative; a newer sibling
  handoff is presumed to belong to a different parallel session. Cross-checkout is now an
  intent-driven, explicitly-flagged fallback (never recency-driven), with an ask-which when
  ambiguous and a checkout/branch-mismatch drift flag. Driven by mining real sessions that
  read a foreign checkout's HANDOFF.md after `/clear` without reading their own.
- v1.1.1: Closed the residual over-ceremony case the after-eval still caught (C1): Step 5
  and the Step 8 blockers contract no longer instruct flagging a hand-written file's
  missing v3 scaffolding as drift items — it is one weak-contract line, and the repair
  offer is reserved for false/stale *claims*, not unmarked files.
- v1.1.0: Hardened against failure modes surfaced by an A/B fixture eval. (1) **Never
  fabricate a verification** — un-run checks must be labeled `assumed (unverified)`,
  not reported as PASS (fixed agents asserting "not a git repo"/"tree clean" with no
  command run). (2) **Worktree-aware detection** — enumerate sibling worktrees so a
  stale root `HANDOFF.md` no longer hides the live one. (3) **Direction-of-drift**
  required before a `stale` verdict; `unknown` when no timestamps. (4) Anchor read-all
  + order to the chosen artifact's own bootstrap/First-Steps text. (5) Commit to the
  handoff's designated next action instead of a redundant "proceed?" round-trip;
  reconcile factual content claims; offer to repair a chosen-but-stale handoff. (6)
  Stop over-reporting on minimal/hand-written artifacts and never route the next
  session to a non-First-Steps oracle file.
- v1.0.0: Initial consumer skill. Producer-agnostic detection (bundle / canonical / FORGE-CLAUDE), skill-owned read-all+receipt guarantee, verbatim-first resume, stakes-tiered verify-still-true gate, and the 5-item resume contract. Generalized the handoff-fresh read-gate validator to the canonical path. Grounded in a session-log eval of real resumes and the swarm-research-droid feedback report.

Current version: 1.2.0. See [CHANGELOG.md](CHANGELOG.md) for history.
