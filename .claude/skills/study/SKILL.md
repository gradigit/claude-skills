---
name: study
description: Conducts structured research with source verification, hypothesis tracking, and quality filtering. Activates when user asks to "research", "find out", "look up", "investigate", "deep dive", "study", or wants information gathered from multiple sources. Invoke with /study [topic].
license: MIT
metadata:
  version: "1.2.0"
  author: gradigit
  tags:
    - research
    - web-search
    - analysis
  triggers:
    - "research"
    - "find out"
    - "look up"
    - "investigate"
    - "deep dive"
    - "study"
---

# Study

Conducts high-quality research using decomposition, breadth-first search, cross-verification, and self-critique.

## Workflow

```
- [ ] 1. Parse request and select depth (quick | full)
- [ ] 2. Decompose question (Self-Ask pattern)
- [ ] 3. Breadth-first search (broad → narrow)
- [ ] 4. Apply quality filters (reject low-quality sources)
- [ ] 5. Cross-verify claims (2+ sources required) [full only]
- [ ] 6. Track hypotheses and confidence [full only]
- [ ] 7. Self-critique findings [full only]
- [ ] 8. Save structured output
- [ ] 9. Present findings with sources
```

## Step 1: Parse Request

Detect depth from user input:
- **Quick**: User says "quick", "brief", "fast", or question is simple/factual
- **Full** (default): Complex topics, "deep", "thorough", "comprehensive", or ambiguous

Detect execution mode:
- **Direct**: Run research in the current conversation (default)
- **Delegated**: User also requests agent teams, subagents, or parallel execution. See [Delegation Mode](#delegation-mode) below.

Detect topic count and select execution strategy:
- **Single-topic**: One question or area to research. Run directly.
- **Multi-topic (2-3 topics)**: Run sequentially in one session. Sequential context helps cross-topic discovery and the speed cost is small.
- **Multi-topic (4+ topics)**: Run in **parallel subagents** — one per topic — then a synthesis pass. See [Multi-Topic Research](#multi-topic-research) below. User can override with "sequential" to force single-session.

Ask user to confirm depth if unclear:
> Quick or full research? Quick = 3-5 sources, core facts. Full = 10+ sources, hypothesis tracking, verification.

## Step 2: Decompose Question (Self-Ask)

Break complex questions into sub-questions before searching.

```
Main question: [user's question]

Follow-up needed: Yes
Sub-question 1: [foundational question]
Sub-question 2: [specific aspect]
Sub-question 3: [verification angle]
...
```

**Skip decomposition if**: Question is already atomic (single fact, simple lookup).

## Step 3: Breadth-First Search

Start broad, then narrow. Do NOT start with specific queries.

**Phase A: Landscape scan**
- 2-3 broad queries to map the territory
- Identify key players, terminology, categories
- Note what exists vs. what's missing

**Phase B: Targeted deep-dive**
- Narrow queries based on landscape findings
- Follow promising links 1-2 levels deep
- Read documentation sections, not just landing pages

**Parallel execution**: Run 3+ searches simultaneously when queries are independent.

## Step 4: Quality Filters

Apply strict filtering. See [quality-filters.md](quality-filters.md) for detailed criteria.

### Quick Reference

**ACCEPT**
- Official documentation (docs.X.com, readthedocs)
- Active GitHub repos with contributors
- Peer-reviewed research, conference papers
- High-vote Stack Overflow with recent activity
- Content < 2 years old (unless foundational)

**REJECT**
- AI-generated SEO spam (generic advice, no code, "In today's fast-paced world...")
- No concrete details or examples
- Outdated (>2 years, unless foundational)
- Contradicts official documentation
- Single-source claims with no verification
- "Top 10 best X" listicles

**For every source, record:**
| Source | URL | Quality | Recency | Notes |
|--------|-----|---------|---------|-------|

## Step 5: Cross-Verify Claims [Full Only]

**Rule: No claim without 2+ independent sources.**

For each factual claim:
1. Find it in source A
2. Verify it appears in source B (independent)
3. If only 1 source → flag as "unverified"
4. If sources conflict → document both positions

```markdown
### Verified Claims
- [Claim]: Source A, Source B

### Unverified Claims
- [Claim]: Only found in [source]. Needs verification.

### Conflicts
- [Topic]: Source A says X, Source B says Y. Analysis: [which is correct and why]
```

## Step 6: Track Hypotheses [Full Only]

Maintain competing hypotheses, not just one answer.

```markdown
## Hypothesis Tracking

| Hypothesis | Confidence | Supporting Evidence | Contradicting Evidence |
|------------|------------|---------------------|------------------------|
| H1: [claim] | High/Med/Low | [sources] | [sources] |
| H2: [alternative] | High/Med/Low | [sources] | [sources] |
```

Update confidence as evidence accumulates. Final answer should acknowledge uncertainty where it exists.

## Step 7: Self-Critique [Full Only]

Before finalizing, challenge your findings:

1. **Completeness**: Did I answer all sub-questions?
2. **Source quality**: Am I relying on weak sources for key claims?
3. **Bias**: Did I favor sources that confirm initial assumptions?
4. **Gaps**: What couldn't I verify? What's still unknown?
5. **Recency**: Is any critical info potentially outdated?

Document issues found and how they were addressed.

## Step 8: Save Output

Save findings to file. Default: `research-[topic]-[date].md`

Use the output template from [output-templates.md](output-templates.md).

### Quick Template
```markdown
# Research: [Topic]
Date: [YYYY-MM-DD]

## Summary
[2-3 sentence answer]

## Key Findings
1. [Finding with source]
2. [Finding with source]
3. [Finding with source]

## Sources
- [Title](URL) — [quality rating]
```

### Full Template
```markdown
# Research: [Topic]
Date: [YYYY-MM-DD]
Depth: Full

## Executive Summary
[Paragraph summary with confidence assessment]

## Sub-Questions Investigated
1. [Sub-question] → [Answer]
2. [Sub-question] → [Answer]

## Detailed Findings
### [Topic Area 1]
[Findings with inline citations]

### [Topic Area 2]
[Findings with inline citations]

## Hypothesis Assessment
[Final assessment of competing hypotheses]

## Verification Status
### Verified (2+ sources)
- [Claims]

### Unverified
- [Claims with single source]

### Conflicts Resolved
- [How conflicts were resolved]

## Limitations & Gaps
- [What couldn't be determined]
- [Areas needing further research]

## Sources
| Source | URL | Quality | Accessed |
|--------|-----|---------|----------|
```

## Step 9: Present Findings

Present to user with:
1. Direct answer to their question
2. Key supporting evidence
3. Confidence level (if full depth)
4. Link to saved file
5. Sources as clickable links

## Multi-Topic Research

When the user requests research on multiple topics in one invocation (e.g., `/study A, B, C, D`):

### Execution Strategy (auto-selected by topic count)

| Topics | Strategy | Rationale |
|--------|----------|-----------|
| 1 | Direct | No multi-topic overhead needed |
| 2-3 | Sequential | Cross-topic context is valuable, speed cost is small |
| 4-6 | Parallel subagents + synthesis | Fresh context per topic, 4-6x faster, synthesis captures cross-topic findings |
| 7+ | Parallel + suggest splitting | Too many for one study invocation. Suggest splitting into two `/study` calls |

User can override: "sequential" forces single-session, "parallel" forces subagents even for 2-3 topics.

### Sequential Mode (2-3 topics)

1. List all topics with short labels
2. Run Step 2 (Self-Ask decomposition) for **each topic independently**
3. Before searching, scan for overlap — topics may share sub-questions
4. During Step 3 (Breadth-First Search), watch for **cross-topic hits**: a source found for topic A may contain findings relevant to topic D
5. Track these cross-pollinations explicitly — they're often the most valuable findings

### Parallel Mode (4+ topics)

Spawn one subagent per topic, then run a synthesis pass.

```
Step 1: Decompose all topics (in main context)
  - Run Self-Ask for each topic
  - Identify any shared sub-questions
  - Build per-topic research briefs

Step 2: Spawn parallel subagents (one per topic)
  Each subagent receives:
  - The full study methodology (Steps 2-7)
  - Quality filter criteria (ACCEPT/REJECT list inlined)
  - Cross-verification and hypothesis tracking instructions
  - Its specific topic brief with research questions
  - Output path: research-[topic-label]-[date].md

Step 3: Wait for all subagents to complete

Step 4: Synthesis pass (in main context or one more subagent)
  - Read all per-topic output files
  - Produce Cross-Cutting Findings section
  - Build unified Hypothesis Assessment table
  - Write executive summary that synthesizes across topics
  - Merge into single multi-topic output file
```

#### Per-topic subagent prompt template

```
You are a research subagent studying one topic as part of a multi-topic study.

## Your Topic: [Label]
**Context:** [Why this matters]
**Research questions:**
- [Question 1]
- [Question 2]

## Methodology (follow these steps exactly)

### Decompose (Self-Ask)
Break your topic into sub-questions before searching.

### Breadth-First Search
Phase A: 2-3 broad queries to map the territory.
Phase B: Narrow queries based on landscape findings.

### Quality Filters
ACCEPT: Official docs, active GitHub repos, peer-reviewed research, high-vote SO (<2 years old)
REJECT: AI-generated SEO spam, no concrete details, outdated (>2 years unless foundational), single-source claims, listicles

### Cross-Verify [Full only]
No claim without 2+ independent sources. Document conflicts.

### Track Hypotheses [Full only]
| Hypothesis | Confidence | Supporting Evidence | Contradicting Evidence |

### Self-Critique
Before finalizing: completeness, source quality, bias, gaps, recency.

## Output
Save to: [path]/research-[topic-label]-[date].md

Use this structure:
## Topic: [Label]
### Hypothesis
### Findings
### Recommendation
### Sources
| Source | URL | Quality | Notes |
```

#### Why parallel + synthesis beats pure sequential

- **Fresh context per topic**: each subagent does its best work, not degraded work on topic 6
- **Speed**: N topics in ~1x time instead of ~Nx time
- **Token cost**: roughly the same — each subagent does the same searches; synthesis adds ~15-20K overhead
- **Cross-topic discovery**: the synthesis pass explicitly looks for connections, which is more reliable than hoping the sequential agent notices them mid-search

### Output

Use the multi-topic template from [output-templates.md](output-templates.md). Key additions:
- Each topic gets its own section (hypothesis, findings, recommendation, sources)
- Add a **Cross-Cutting Findings** section after individual topics for discoveries that span multiple studies
- The Hypothesis Assessment table includes all topics, with a topic column for filtering
- The executive summary synthesizes across topics, not just summarizes each one

## Delegation Mode

When the user requests both `/study` and agent teams (or subagents, parallel agents, etc.), the research should be **delegated to a teammate agent** rather than run in the main conversation.

### How delegation works

1. **This skill still loads into the lead's context first.** The lead needs the methodology to write a good delegation prompt.
2. The lead constructs a researcher agent prompt by combining:
   - The full methodology from this skill (Steps 1-9)
   - The quality filter criteria (inline — the agent can't read quality-filters.md)
   - Domain-specific context for each topic (why it matters, what the current state is, what specific questions to answer)
   - Team integration instructions (TaskList, claim task, TaskUpdate when done)
   - The output file path and template

### Delegation prompt structure

```
You are a researcher agent. Your job is to conduct structured research following this methodology.

## Methodology
[Embed Steps 1-9 from this skill]

## Quality Filters
[Embed the ACCEPT/REJECT criteria from Step 4 — the full list, not just "be skeptical"]

## Source Recording
For every source, record:
| Source | URL | Quality Tier | Recency | Notes |

## Cross-Verification
[Embed Step 5 rules: no claim without 2+ sources, conflict documentation]

## Hypothesis Tracking
[Embed Step 6 format]

## Self-Critique
[Embed Step 7 checklist: completeness, source quality, bias, gaps, recency]

## Topics to Research

### Topic 1: [Label]
**Context:** [Why this matters — what problem it addresses]
**Current state:** [What's known, what's assumed, what's broken]
**Research questions:**
- [Specific question 1]
- [Specific question 2]
- [Specific question 3]

### Topic 2: [Label]
[Same structure]

## Output
Save to: [file path]
Use the multi-topic full template.

## Team Integration
- Check TaskList and claim your task
- Use TaskUpdate to mark complete when done
```

### What the lead must add (not in this skill)

The skill provides the methodology. The lead must provide:
- **Domain context per topic**: why it matters, what the current state is
- **Specific research questions**: not just "study X" but "is X possible? how? what are the alternatives?"
- **Output path**: where to save the file
- **Team integration**: task claiming and completion

### Why delegation exists

Running 6+ full-depth research topics in the main conversation consumes enormous context. Delegating to a teammate agent:
- Keeps the lead's context clean for coordination
- Allows research to run in parallel with other work (fixes, curation)
- Produces a saved file that persists beyond the conversation

## Example

**Input:**
```
/research what's the best way to implement caching in a Node.js API
```

**Process:**
1. Depth: Full (architectural decision)
2. Decompose:
   - What caching strategies exist for Node.js?
   - What are the tradeoffs (Redis vs in-memory vs file)?
   - What do official docs recommend?
   - What are common pitfalls?
3. Search: "Node.js caching strategies 2025", "Redis vs in-memory Node", "Express caching best practices"
4. Filter: Accept Redis docs, Node.js docs, high-vote SO. Reject generic blog posts.
5. Verify: Redis performance claims cross-referenced with benchmarks
6. Hypotheses: H1: Redis for distributed, H2: node-cache for single-instance
7. Self-critique: Checked for recency, verified benchmark methodology
8. Save: research-nodejs-caching-2026-02-05.md

**Output:**
> For a Node.js API, the caching strategy depends on your deployment:
>
> **Single instance**: Use `node-cache` (in-memory) — simplest, no external dependency, ~0.1ms reads
>
> **Distributed/Multi-instance**: Use Redis — shared cache across instances, persistence options, ~1-2ms network overhead
>
> Key finding: Redis adds latency but prevents cache inconsistency across instances. The official Express.js docs recommend starting with in-memory and migrating to Redis when scaling.
>
> Confidence: High (verified across Redis docs, Node.js best practices, and Express documentation)
>
> Full report saved to research-nodejs-caching-2026-02-05.md
>
> Sources:
> - [Redis Documentation](https://redis.io/docs/)
> - [Express.js Best Practices](https://expressjs.com/en/advanced/best-practice-performance.html)
> - [node-cache npm](https://www.npmjs.com/package/node-cache)

## Self-Evolution

Update this skill when:
1. **On quality miss**: Low-quality source slipped through → tighten filters
2. **On verification failure**: Claim turned out wrong → strengthen cross-reference rules
3. **On user correction**: User provides better methodology → incorporate

**Applied Learnings:**
- v1.0.0: Initial version based on Anthropic research system patterns, Self-Ask decomposition, and triangulation methodology
- v1.1.0: Added multi-topic and delegation modes after /study was invoked alongside agent teams and the skill was skipped entirely — the methodology was replaced with an ad-hoc prompt that lacked Self-Ask decomposition, breadth-first search, quality filters, and self-critique
- v1.2.0: Added parallel subagent execution for 4+ topics with auto-selection by topic count — sequential for 2-3 topics (cross-topic context), parallel + synthesis for 4+ topics (speed + fresh context per topic)

Current version: 1.2.0. See [CHANGELOG.md](CHANGELOG.md) for history.

## References

For detailed quality criteria, see [quality-filters.md](quality-filters.md).
For output templates, see [output-templates.md](output-templates.md).
For research methodology background, see [research-findings.md](research-findings.md).
