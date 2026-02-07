# Quality Filters

Detailed criteria for evaluating source quality during research.

## Source Quality Tiers

### Tier 1: ACCEPT (High Quality)

**Official Documentation**
- Project/framework official docs (docs.X.com, X.readthedocs.io)
- API references from the source
- RFC/specification documents
- Official GitHub READMEs with active maintenance

**Academic & Professional**
- Peer-reviewed papers
- Conference proceedings (ACL, NeurIPS, ICML, etc.)
- Published technical reports from research labs
- Whitepapers from established companies

**Community (Verified)**
- Stack Overflow answers with:
  - 50+ upvotes AND
  - Activity within last 2 years AND
  - Accepted answer or multiple confirming answers
- GitHub issues/discussions with maintainer responses
- Well-maintained GitHub repos (recent commits, multiple contributors, stars > 100)

**Recency**
- Content published within last 2 years
- Exception: Foundational concepts (algorithms, protocols) can be older

### Tier 2: ACCEPT WITH CAUTION (Medium Quality)

Use these sources but cross-reference with Tier 1:

- Engineering blogs from reputable companies (but verify claims)
- Tutorial sites with working code examples
- Wikipedia (good for overview, not implementation details)
- Stack Overflow answers 2-5 years old but highly upvoted
- Medium/Dev.to posts from verified domain experts (check author credentials)
- YouTube tutorials from established educators (verify against docs)

**Caution flags:**
- No code examples → lower confidence
- Single author with no credentials → verify elsewhere
- Promotional tone → check for bias

### Tier 3: REJECT (Low Quality)

**AI-Generated SEO Spam**

Red flags:
- "In today's fast-paced world..."
- "Let's dive in..."
- "In conclusion, [restates obvious point]"
- Generic advice that applies to anything ("always write clean code")
- No specific code examples, versions, or concrete details
- Keyword-dense headings with thin content underneath
- Lists of vague benefits without implementation guidance
- Perfect grammar but no substance

**Outdated Content**
- >2 years old for fast-moving tech (JS frameworks, cloud services, AI/ML)
- >5 years old for stable tech (unless foundational)
- Mentions deprecated APIs/libraries without noting deprecation

**Unverifiable**
- Forum posts with no upvotes or verification
- Anonymous sources with no credentials
- Claims without citations
- Single-source claims that can't be cross-referenced

**Promotional/Biased**
- Vendor content promoting their product over alternatives
- Affiliate-heavy "best X" listicles
- Content that contradicts official documentation
- Reviews/comparisons with obvious bias

**Structural Red Flags**
- Paywalled content you can't fully read
- Content that just restates obvious things
- "Top 10 best X" without depth
- Excessive ads interrupting content
- Clickbait titles that don't match content

## Verification Checklist

For each source, verify:

| Check | Question |
|-------|----------|
| Authority | Who wrote this? What are their credentials? |
| Recency | When was this published/updated? |
| Citations | Does it cite sources? Can I verify them? |
| Specificity | Does it have concrete examples, code, data? |
| Consistency | Does it align with official docs? |
| Independence | Is this independent from other sources I'm using? |

## Cross-Reference Rules

**Claims requiring 2+ sources:**
- Performance benchmarks
- Security recommendations
- Best practice assertions
- "X is better than Y" comparisons
- Statistics and numbers

**Single source acceptable for:**
- Official documentation of a specific API
- Direct quotes from project maintainers
- Self-evident facts (e.g., "Python is interpreted")

## Recording Source Quality

For every source used, record:

```markdown
| Source | URL | Tier | Recency | Cross-Ref | Notes |
|--------|-----|------|---------|-----------|-------|
| Redis Docs | redis.io/docs | 1 | 2025 | N/A (official) | Primary source |
| SO Answer | stackoverflow.com/... | 1 | 2024, 150 votes | Matches Redis docs | Performance claim |
| Blog Post | example.com/... | 3-REJECT | 2021 | Contradicts docs | Outdated Redis 5 info |
```

## Quick Decision Tree

```
Is it official documentation?
  → YES: Accept (Tier 1)
  → NO: Continue

Is it peer-reviewed or from established institution?
  → YES: Accept (Tier 1)
  → NO: Continue

Does it have concrete examples/code?
  → NO: Likely reject
  → YES: Continue

Is it less than 2 years old?
  → NO: Reject unless foundational
  → YES: Continue

Can you verify the author's credentials?
  → NO: Treat as Tier 2, cross-reference
  → YES: Continue

Does it align with official docs?
  → NO: Reject
  → YES: Accept (Tier 1 or 2 based on source type)
```
