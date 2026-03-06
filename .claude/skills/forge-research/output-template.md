# Research Output Template

Templates for saving forge-research campaign findings.

## Standard Output

Use for: single-phase research, quick campaigns, standalone invocations.

```markdown
# Research: {topic}

## Summary
{2-3 sentence synthesis}

## Key Findings
1. {finding} — confidence: {high|medium|low} — sources: {list}
2. {finding} — confidence: {high|medium|low} — sources: {list}
3. {finding} — confidence: {high|medium|low} — sources: {list}

## Hypotheses
| Hypothesis | Status | Evidence |
|-----------|--------|----------|
| H1: {claim} | confirmed/refuted/uncertain | {evidence summary} |
| H2: {claim} | confirmed/refuted/uncertain | {evidence summary} |

## Questions Resolved
- [x] {question} — answer: {answer}
- [x] {question} — answer: {answer}

## Gaps and Limitations
- {what couldn't be determined and why}

## Sources
- {url or reference} — {what it provided}
- {url or reference} — {what it provided}
```

## Extended Output (for multi-phase research)

Use for: multi-phase campaigns, orchestrated research, deep topics with adversarial review.

```markdown
# Research: {topic}
Date: {YYYY-MM-DD}
Phase: {1|2|final}

## Executive Summary
{paragraph with confidence assessment — overall certainty level, key caveats, and scope of findings}

## Verified Claims (2+ sources)
- {claim}: Source A, Source B
- {claim}: Source A, Source C

## Unverified Claims
- {claim}: Only found in {source}. Needs verification.
- {claim}: Only found in {source}. Treat with caution.

## Conflicts
- {topic}: Source A says X, Source B says Y. Resolution: {analysis of which is correct and why}

## Hypotheses
| ID | Hypothesis | Initial | Final | Key Evidence |
|----|-----------|---------|-------|-------------|
| H1 | {claim} | pending | confirmed | {sources and reasoning} |
| H2 | {claim} | pending | refuted | {sources and reasoning} |

## Questions Resolved
- [x] {question} — answer: {answer}

## Questions Unresolvable
- {question} — reason: {why it couldn't be resolved with available sources}

## Adversarial Review Summary
| Issue | Severity | Resolution |
|-------|----------|------------|
| {gap or flaw found} | critical/major/minor | {how it was addressed in Phase 2} |

## Depth Cycles
| Cycle | Focus | New Findings | Diminishing Returns? |
|-------|-------|-------------|---------------------|
| Phase 1 (breadth) | {broad queries} | {count} | No |
| Phase 2 (depth 1) | {targeted gaps} | {count} | No/Yes |
| Phase 2 (depth 2) | {remaining gaps} | {count} | Yes — terminated |

## Sources
| Source | URL | Quality | Recency | Notes |
|--------|-----|---------|---------|-------|
| {name} | {url} | Tier 1/2 | {year} | {what it provided} |
| {name} | {url} | REJECTED | {year} | {reason for rejection} |
```

## File Naming Convention

```
architect/research/{topic-slug}.md

Examples:
- architect/research/rust-async-runtimes.md
- architect/research/oauth2-implementation-patterns.md
- architect/research/caching-strategies.md
```

If the file already exists, append under a timestamped header rather than overwriting:

```markdown
## Update — {YYYY-MM-DD}

{new findings appended below}
```
