# Output Templates

Templates for saving research findings.

## Quick Research Template

Use for: Simple factual questions, single-topic lookups, time-sensitive requests.

```markdown
# Research: [Topic]

**Date:** YYYY-MM-DD
**Depth:** Quick
**Query:** [Original user question]

## Summary

[2-3 sentence direct answer to the question]

## Key Findings

1. **[Finding 1]** — [Source]
2. **[Finding 2]** — [Source]
3. **[Finding 3]** — [Source]

## Sources

| Source | URL | Quality |
|--------|-----|---------|
| [Name] | [URL] | Tier 1/2 |
```

## Full Research Template

Use for: Complex questions, architectural decisions, comparative analysis, topics requiring verification.

```markdown
# Research: [Topic]

**Date:** YYYY-MM-DD
**Depth:** Full
**Query:** [Original user question]
**Time spent:** [X searches, Y sources reviewed]

## Executive Summary

[Paragraph summary answering the main question. Include confidence level: High/Medium/Low. Note key caveats or limitations.]

## Question Decomposition

Original question broken into sub-questions:

1. [Sub-question 1] → [Brief answer]
2. [Sub-question 2] → [Brief answer]
3. [Sub-question 3] → [Brief answer]

## Detailed Findings

### [Topic Area 1]

[Detailed findings with inline citations like (Source, 2024). Include specific data, code examples, or quotes where relevant.]

### [Topic Area 2]

[Continue for each major topic area]

## Hypothesis Tracking

| Hypothesis | Initial Confidence | Final Confidence | Key Evidence |
|------------|-------------------|------------------|--------------|
| H1: [claim] | Medium | High | [sources supporting] |
| H2: [alternative] | Medium | Low | [sources contradicting] |

**Resolution:** [Which hypothesis prevailed and why]

## Verification Status

### Verified Claims (2+ independent sources)
- [Claim 1]: Source A, Source B
- [Claim 2]: Source A, Source C

### Unverified Claims (single source)
- [Claim]: Only found in [source]. Treat with caution.

### Conflicts Identified
- **[Topic]:** Source A claims X, Source B claims Y
  - **Resolution:** [How conflict was resolved, or note as unresolved]

## Self-Critique

Issues identified during review:

| Issue | Severity | Resolution |
|-------|----------|------------|
| [Gap/bias/limitation] | High/Med/Low | [How addressed] |

## Limitations & Future Research

- **Could not determine:** [What remains unknown]
- **Needs deeper investigation:** [Areas for follow-up]
- **Potential biases:** [Any systematic biases in sources]

## Source Evaluation

| Source | URL | Tier | Recency | Used For |
|--------|-----|------|---------|----------|
| [Name] | [URL] | 1 | 2025 | [What claims it supports] |
| [Name] | [URL] | 2 | 2024 | [What claims it supports] |
| [Name] | [URL] | REJECTED | 2021 | N/A - outdated |

## Raw Notes

<details>
<summary>Search queries used</summary>

1. "[query 1]" → [X results reviewed]
2. "[query 2]" → [X results reviewed]
</details>

<details>
<summary>Sources considered but rejected</summary>

- [URL]: [Reason for rejection]
</details>
```

## Comparative Research Template

Use for: "X vs Y" questions, technology comparisons, decision-making research.

```markdown
# Research: [X vs Y]

**Date:** YYYY-MM-DD
**Depth:** Full
**Decision context:** [What decision this research supports]

## Quick Recommendation

**For [use case A]:** Choose X because [reason]
**For [use case B]:** Choose Y because [reason]

## Comparison Matrix

| Criterion | X | Y | Winner | Source |
|-----------|---|---|--------|--------|
| [Criterion 1] | [X value] | [Y value] | X/Y/Tie | [Source] |
| [Criterion 2] | [X value] | [Y value] | X/Y/Tie | [Source] |

## Detailed Analysis

### [X] Strengths
- [Strength 1] — [Source]

### [X] Weaknesses
- [Weakness 1] — [Source]

### [Y] Strengths
- [Strength 1] — [Source]

### [Y] Weaknesses
- [Weakness 1] — [Source]

## Use Case Recommendations

| Use Case | Recommendation | Confidence | Rationale |
|----------|---------------|------------|-----------|
| [Case 1] | X | High | [Why] |
| [Case 2] | Y | Medium | [Why] |

## Sources

[Standard source table]
```

## Prior Art Research Template

Use for: "Does X already exist?", "What solutions are available for Y?"

```markdown
# Prior Art Research: [Problem/Need]

**Date:** YYYY-MM-DD
**Query:** [What user is looking for]

## Existing Solutions Found

| Solution | Type | URL | Maturity | Fit |
|----------|------|-----|----------|-----|
| [Name] | OSS/Commercial/Internal | [URL] | Active/Maintained/Abandoned | High/Med/Low |

## Detailed Evaluation

### [Solution 1]

- **What it does:** [Description]
- **Pros:** [List]
- **Cons:** [List]
- **Why it might not fit:** [Gaps relative to user's need]

### [Solution 2]

[Repeat]

## Gap Analysis

**What exists:** [Summary of available solutions]

**What's missing:** [Gaps that existing solutions don't address]

**Recommendation:**
- [ ] Use existing solution [X] because [reason]
- [ ] Build custom because [no existing solution fits due to Y]
- [ ] Modify existing solution [X] by [changes needed]

## Sources

[Standard source table]
```

## Multi-Topic Research Template

Use for: Multiple related research topics in one session (e.g., `/study A, B, C, D`).

```markdown
# Study: [Overall Theme]

**Date:** YYYY-MM-DD
**Depth:** Full
**Topics:** [N] topics
**Time spent:** [X searches, Y sources reviewed]

## Executive Summary

[Synthesize across ALL topics — not just a summary of each. What's the overall picture? How do the topics connect? What's the most important finding across all studies?]

## Study [Label]: [Topic Title]

### Hypothesis
| ID | Hypothesis | Initial Confidence |
|----|-----------|-------------------|
| H[N].1 | [claim] | High/Med/Low |
| H[N].2 | [alternative] | High/Med/Low |

### Findings
[Detailed findings with inline citations]

### Recommendation
[Concrete, actionable recommendation]

### Sources
| Source | URL | Quality | Notes |
|--------|-----|---------|-------|

## Study [Label]: [Next Topic]
[Same structure repeats]

...

## Cross-Cutting Findings

Discoveries that span multiple topics:
- **[Finding]:** Connects Study [X] and Study [Y] — [explanation]. Source: [source]
- **[Finding]:** [explanation]

## Hypothesis Assessment

| ID | Topic | Hypothesis | Initial | Final | Key Evidence |
|----|-------|-----------|---------|-------|-------------|
| H1.1 | [A] | [claim] | Med | High | [sources] |
| H2.1 | [B] | [claim] | Med | Low | [sources] |

## Verification Status

### Verified (2+ independent sources)
- [Claim]: Source A, Source B — Topic [X]

### Unverified (single source)
- [Claim]: Only found in [source] — Topic [X]

### Conflicts
- [Topic]: Source A says X, Source B says Y — Resolution: [how resolved]

## Self-Critique

| Issue | Severity | Topic | Resolution |
|-------|----------|-------|------------|
| [Gap/bias/limitation] | High/Med/Low | [which topic] | [how addressed] |

## Limitations & Gaps
- [What couldn't be determined]
- [Areas needing further research]

## Source Quality Table

| Source | URL | Quality | Recency | Topics |
|--------|-----|---------|---------|--------|
| [Name] | [URL] | Tier 1/2 | 2026 | [A, C] |

## Overall Recommendations
[Prioritized list of actionable next steps across all topics]
```

## File Naming Convention

```
research-[topic-slug]-[YYYY-MM-DD].md

Examples:
- research-nodejs-caching-2026-02-05.md
- research-redis-vs-memcached-2026-02-05.md
- research-oauth2-implementation-2026-02-05.md
```

Default save location: Current working directory, or user-specified path.
