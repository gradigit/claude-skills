---
name: forge-research
description: "Launches autonomous multi-agent research campaigns with hypothesis tracking, source verification, adversarial challenge, and iterative deepening. Can be used standalone or orchestrated by forge-orchestrator. Invoke with /forge-research [topic]. Do NOT use for building/coding — use forge-builder instead."
license: MIT
metadata:
  version: "1.1.0"
  author: gradigit
  category: forge
  tags:
    - research
    - autonomous
    - multi-agent
    - study
  triggers:
    - "forge research"
    - "autonomous research"
    - "research campaign"
    - "deep research"
---

# Forge Research

Launches autonomous multi-agent research campaigns with hypothesis tracking and adversarial challenge.

## Workflow

```
- [ ] 1. Parse research directive           → produces: Directive Table
- [ ] 2. Detect platform + read practices   → produces: platform name logged
  ── GATE A: directive parsed + practices read ──
- [ ] 3. Formulate hypotheses               → produces: H-table + Q-checklist (output visibly)
  ── GATE B: hypothesis table visible in response ──
- [ ] 4. Launch research agents (breadth)   → produces: agent results collected
- [ ] 5. Synthesize phase 1                 → produces: Phase 1 Findings table
  ── GATE C: findings table + tracking list updated ──
- [ ] 6. Adversarial challenge              → produces: challenge results (5-point or reviewer)
  ── GATE D: adversarial output visible in response ──
- [ ] 7. Targeted research (depth)          → produces: gap-fill results (or "no critical gaps")
- [ ] 8. Synthesize final findings          → produces: final findings with confidence scores
- [ ] 9. Write output                       → produces: output file written
```

### Step Completion Protocol

**Every step must produce visible output before the next step begins.** The GATE markers above are hard checkpoints — you MUST NOT skip past a gate.

- **GATE A** (after Steps 1-2): You must have a Directive Table and have read the practices guide. If you haven't, STOP and do it now.
- **GATE B** (after Step 3): You must have output a Hypotheses table and Questions to Resolve checklist in your response. If the table is not visible, STOP and create it.
- **GATE C** (after Step 5): You must have a Phase 1 Findings table and updated tracking list. If not, STOP and synthesize before proceeding.
- **GATE D** (after Step 6): You must have adversarial challenge output (either 5-point self-critique or reviewer findings). Skipping adversarial challenge is NEVER acceptable — it is the primary defense against confirmation bias.

**Why gates matter:** Without explicit gates, the natural tendency is to shortcut from "spawn agents" to "write output," skipping hypothesis tracking, adversarial review, and depth research. These are the steps that make forge-research produce better results than a simple multi-agent search.

---

## Step 1: Parse Research Directive

Extract from user input or orchestrator request. **You MUST output this table before proceeding.**

| Component | Value |
|-----------|-------|
| **Topic** | {extracted topic} |
| **Questions** | {explicit or inferred questions} |
| **Scope** | {boundaries on what to include/exclude} |
| **Constraints** | {time, depth, source restrictions — or "none"} |
| **Output path** | {explicit or default: `architect/research/{topic-slug}.md`} |

If invoked by forge-orchestrator, the directive arrives as a structured XML block with `<task>`, `<context>`, `<scope>`, `<boundaries>`, and `<output-contract>` tags. Parse each directly.

If invoked standalone by the user, infer these components from natural language. Ask for clarification if the topic is ambiguous.

---

## Step 2: Platform Detection

**MANDATORY.** Detect the current platform and read the practices guide BEFORE any agent spawning.

| Signal | Platform | Action |
|--------|----------|--------|
| Agent, TeamCreate, SendMessage, or EnterWorktree tools available | Claude Code | Read `.claude/skills/forge-claude-teams/SKILL.md` |
| spawn_agent, AGENTS.md, fork_context available | Codex CLI | Read `.claude/skills/forge-codex-multiagent/SKILL.md` |
| Neither detected | Unknown | Assume Claude Code, log warning: "Platform not detected, defaulting to Claude Code patterns" |

**You MUST read the practices guide file** (not just acknowledge it exists). It contains context handoff templates, concurrency limits, and conflict prevention rules that govern all subsequent steps. Log which platform was detected.

> **GATE A checkpoint**: Do not proceed to Step 3 unless you have (1) output the Directive Table from Step 1 and (2) read the practices guide file. If you skipped either, go back now.

---

## Step 3: Hypotheses and Questions to Resolve

**MANDATORY. You MUST output both tables below in your response before spawning any agents.**

Before any research begins, create an explicit tracking list. This list is the **termination criteria** — research cannot complete while unchecked questions remain.

```markdown
## Hypotheses
| ID | Hypothesis | Status | Evidence |
|----|-----------|--------|----------|
| H1 | {initial hypothesis} | pending | — |
| H2 | {alternative hypothesis} | pending | — |
| H3 | {at least one more} | pending | — |

## Questions to Resolve
- [ ] {question 1}
- [ ] {question 2}
- [ ] {question 3}
```

**Rules:**
- Minimum 2 hypotheses and 3 questions before proceeding
- Each research cycle must resolve, reclassify, or explicitly mark questions as "unresolvable with available sources"
- New questions discovered during research get appended to the list
- Hypotheses start as `pending`, then move to `confirmed`, `refuted`, or `uncertain`

> **GATE B checkpoint**: Do not proceed to Step 4 unless you have output the Hypotheses table and Questions to Resolve checklist above. If they are not visible in your response, STOP and create them now.

---

## Step 4: Launch Research Agents (Phase 1 — Breadth)

Spawn sub-agents for broad coverage. Agent types depend on the research need:

| Research Need | Agent Type | Tool |
|--------------|-----------|------|
| Web research (docs, papers, APIs) | Study sub-agent | Uses `study` skill if installed |
| Codebase exploration | Explore sub-agent | Read-only codebase analysis |
| Session log / workflow analysis | Explore sub-agent | Pattern extraction from logs |

### Agent Spawn Rules

**DEFAULT: sequential launches.** Parallelize ONLY for genuinely independent queries.

| Situation | Execution | Rationale |
|-----------|-----------|-----------|
| Questions share context | Sequential | Later queries benefit from earlier findings |
| Queries are fully independent | Parallel (max 3-5) | No shared state, no dependency |
| Single complex topic | Single agent, deep | Context accumulation matters |

### Context Handoff

**MANDATORY XML format.** Every sub-agent MUST receive a context handoff using these 5 XML tags. Do NOT use plain-text numbered lists or ad-hoc prompts — the XML structure ensures agents get scope, boundaries, and output contracts.

```xml
<task>
  Research: {specific question or topic slice}
</task>

<context>
  Part of a broader research campaign on {overall topic}.
  What we know so far: {any prior findings from earlier phases}.
  Hypotheses under investigation: {relevant H1, H2, etc.}
</context>

<scope>
  Focus on: {specific aspect}
  Time range: recent (< 2 years) unless foundational
</scope>

<boundaries>
  Do NOT research: {out-of-scope topics}
  Do NOT modify any files — read-only research only.
</boundaries>

<output-contract>
  Return: structured findings with source citations
  Format: claim + confidence + source URL per finding
  Signal: "RESEARCH_COMPLETE" when done
</output-contract>
```

### Persistence

- **Long campaigns** (3+ agents, multi-phase): persist handoffs to `architect/agent-contexts/{agent-name}.md`
- **Quick queries** (1-2 agents, single phase): inline handoff in agent prompt, no file persistence

### Study Skill Integration

If the `study` skill is installed (`.claude/skills/study/SKILL.md` exists), spawn study sub-agents that inherit its methodology: Self-Ask decomposition, breadth-first search, quality filters, cross-verification, hypothesis tracking.

**Fallback if study not installed:** direct WebSearch/WebFetch calls. Log warning: "study skill not found, using direct web search (reduced source verification)."

---

## Step 5: Collect and Synthesize Phase 1

Gather results from all sub-agents. Synthesize into a findings table:

```markdown
## Phase 1 Findings

| # | Finding | Confidence | Sources | Questions Addressed |
|---|---------|-----------|---------|-------------------|
| 1 | {finding} | high/medium/low | {source list} | Q1, Q3 |
| 2 | {finding} | high/medium/low | {source list} | Q2 |
```

**Update tracking:**
- Mark resolved questions as `[x]` with brief answer
- Update hypothesis status with evidence collected
- Identify gaps: which questions remain open? Which hypotheses lack evidence?

> **GATE C checkpoint**: Do not proceed to Step 6 unless you have (1) output the Phase 1 Findings table and (2) updated the hypothesis and question tracking lists. If you are about to write the final output file, STOP — you are skipping adversarial challenge (Step 6).

---

## Step 6: Adversarial Challenge

**MANDATORY. This step is NEVER optional**, even if findings seem solid. Skipping adversarial challenge is the #1 failure mode of this skill — it lets confirmation bias pass unchecked into the final output.

### Self-Critique (always — output the results visibly)

Review findings for:
1. **Confirmation bias** — did we favor sources that confirm initial hypotheses?
2. **Source quality** — are key claims resting on weak sources?
3. **Gaps** — what questions remain unanswered?
4. **Contradictions** — do any findings conflict with each other?
5. **Recency** — is any critical information potentially outdated?

### Adversarial Reviewer (when available)

If `forge-adversarial-reviewer` agent is defined (`.claude/agents/forge-adversarial-reviewer.md` exists), spawn it with:

```xml
<task>
  Critically review these research findings. Find flaws, gaps,
  unsupported claims, and logical errors.
</task>

<context>
  Research topic: {topic}
  Hypotheses: {H1, H2, ...}
  Findings: {Phase 1 findings table}
  Sources consulted: {source list}
</context>

<output-contract>
  Return: list of issues, each with severity (critical/major/minor)
  and specific recommendation for resolution.
  Confidence threshold: flag any finding below 80% confidence
  that lacks file:line or URL evidence.
</output-contract>
```

If `forge-adversarial-reviewer` is not available, perform self-critique only (the 5-point checklist above). **You MUST output the self-critique results** — a one-line "looks good" is not sufficient. Each of the 5 points must be explicitly addressed.

> **GATE D checkpoint**: Do not proceed to Step 7 unless adversarial challenge output is visible in your response. If you are about to write the final output file without having done adversarial review, STOP — go back to Step 6.

---

## Step 7: Targeted Research (Phase 2 — Depth)

Address gaps and challenges identified in Step 6. **Skip ONLY if** the adversarial challenge found no critical gaps and all questions are resolved — in which case, log: "Phase 2 skipped: no critical gaps identified in adversarial review."

### Gap Resolution

For each critical gap or adversarial challenge:

1. **Formulate targeted queries** — specific, not broad
2. **Cross-reference claims** — every disputed claim needs 2+ independent sources
3. **Deep crawl** — follow links from Phase 1 sources, read sub-pages, find the actual documentation (not summaries)
4. **Primary sources** — seek original papers, official docs, release notes over secondhand reports

### Phase 2 Agent Spawning

Same rules as Step 4, but:
- Queries are more targeted (depth, not breadth)
- Previous findings are included in agent context
- Agents are directed to specific gaps, not open exploration

### Iteration Limit

Maximum **3 depth cycles** (Phase 2 can repeat if adversarial review of Phase 2 results reveals new gaps). If gaps remain after 3 cycles, mark them as unresolvable and document why.

---

## Step 8: Synthesize Final Findings

Combine Phase 1 and Phase 2 results into final output.

### Confidence Scoring

| Level | Criteria |
|-------|---------|
| **High** | 2+ independent sources agree, official docs confirm, no contradictions |
| **Medium** | 1 strong source + 1 supporting indicator, or 2 sources with minor discrepancies |
| **Low** | Single source, or sources conflict, or information is >1 year old |

### Hypothesis Resolution

For each hypothesis, assign final status:

| Status | Meaning |
|--------|---------|
| **Confirmed** | Evidence strongly supports, no credible contradictions |
| **Refuted** | Evidence strongly contradicts, or better alternative confirmed |
| **Uncertain** | Insufficient evidence, or balanced contradictory evidence |

---

## Step 9: Write Output

### Default Output Location

`architect/research/{topic-slug}.md`

**If topic already has output at that path:** append under a timestamped header (`## Update — {YYYY-MM-DD}`). Do NOT overwrite previous findings.

### Output Structure

Use the template from [output-template.md](output-template.md). Summary of sections:

```markdown
# Research: {topic}

## Summary
{2-3 sentence synthesis}

## Key Findings
1. {finding} — confidence: {high|medium|low} — sources: {list}

## Hypotheses
| Hypothesis | Status | Evidence |
|-----------|--------|----------|
| H1 | confirmed/refuted/uncertain | {evidence summary} |

## Questions Resolved
- [x] {question} — answer: {answer}

## Gaps and Limitations
- {what couldn't be determined and why}

## Sources
- {url or reference} — {what it provided}
```

For multi-phase or extended research, use the extended output template (see [output-template.md](output-template.md)).

---

## Research Quality Standards

These standards apply to all research agents spawned by this skill.

| Standard | Rule |
|----------|------|
| **Source priority** | Official documentation first, always |
| **Recency** | Reject information >2 years old unless foundational/historical |
| **Cross-reference** | Every factual claim needs 2+ independent sources |
| **Deep crawl** | Follow links, read sub-pages, find actual documentation — not summaries |
| **SEO spam rejection** | Reject AI-generated content, listicles, "Top 10 best X" articles |
| **Citation** | Every claim needs a source citation — no unsourced assertions |
| **Conflict handling** | When sources disagree, document both positions and analyze which is correct |

---

## Termination Conditions

Research is complete when **all** of the following are true:

- [ ] Questions to Resolve list is fully checked (resolved or marked unresolvable)
- [ ] All hypotheses have a final status (confirmed/refuted/uncertain) with evidence
- [ ] Adversarial review finds no critical gaps remaining
- [ ] Diminishing returns: last cycle produced <10% new information
- [ ] Maximum 3 depth cycles reached (hard ceiling)

If any condition is unmet after 3 depth cycles, document remaining gaps and terminate with an explicit "Limitations" section.

---

## Relationship to Study Skill

forge-research and study serve different purposes:

| Aspect | study | forge-research |
|--------|-------|---------------|
| **Scope** | Single-session research | Multi-agent research campaigns |
| **Agents** | Runs in current context (or parallel subagents for 4+ topics) | Spawns multiple specialized agents |
| **Hypothesis tracking** | Per-session | Cross-agent, iterative |
| **Adversarial review** | Self-critique only | Dedicated adversarial reviewer agent |
| **Synthesis** | Single-pass | Multi-phase with iterative deepening |
| **Standalone** | Yes — primary research tool | Yes — or orchestrated by forge-orchestrator |

forge-research **spawns study agents** as one tool among many. study stays independent for standalone use. forge-research adds: multi-agent parallelism, hypothesis iteration, adversarial challenge, cross-agent synthesis.

---

## Output Format

See [output-template.md](output-template.md) for full templates including:
- Standard output (single-phase research)
- Extended output (multi-phase research with verified/unverified claims, conflicts, source quality table)

---

## Self-Evolution

Update this skill when:
1. **New research patterns**: Better decomposition, search, or synthesis strategies discovered
2. **Study skill changes**: If study adds new methodology, update integration guidance
3. **Agent API changes**: Platform multi-agent APIs change (see forge-claude-teams / forge-codex-multiagent)
4. **Quality misses**: Low-quality findings slip through — tighten standards or add adversarial checks
5. **User corrections**: Real-world usage reveals incorrect guidance

Current version: 1.1.0. See [CHANGELOG.md](CHANGELOG.md) for history.
