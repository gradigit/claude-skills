---
name: study
description: Conducts structured research with source verification, hypothesis tracking, and quality filtering. Activates when user asks to "research", "find out", "look up", "investigate", "deep dive", "study", or wants information gathered from multiple sources. Invoke with /study [topic].
license: MIT
metadata:
  version: "1.0.0"
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

Ask user to confirm if unclear:
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

Current version: 1.0.0. See [CHANGELOG.md](CHANGELOG.md) for history.

## References

For detailed quality criteria, see [quality-filters.md](quality-filters.md).
For output templates, see [output-templates.md](output-templates.md).
For research methodology background, see [research-findings.md](research-findings.md).
