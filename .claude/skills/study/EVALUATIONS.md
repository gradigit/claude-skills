# Evaluations for study

## Scenario 1: Happy path — research topic (should-trigger, functional)

**Given** user wants to learn about a technical topic
**When** user says "research the best caching strategies for Node.js APIs"
**Then**
- [ ] Skill activates
- [ ] Detects depth (full for architectural decision)
- [ ] Decomposes question into sub-questions
- [ ] Searches multiple sources (broad → narrow)
- [ ] Applies quality filters (rejects AI-generated SEO spam)
- [ ] Saves output to research-{topic}-{date}.md
- [ ] Presents findings with clickable source links

## Scenario 2: Edge case — quick lookup (should-trigger, functional)

**Given** user wants a simple factual answer
**When** user says "quick lookup: what's the default port for PostgreSQL"
**Then**
- [ ] Skill activates
- [ ] Detects quick depth (simple factual question)
- [ ] Skips decomposition (atomic question)
- [ ] Searches 3-5 sources
- [ ] Skips cross-verification, hypothesis tracking, self-critique (quick mode)
- [ ] Returns concise answer with sources

## Scenario 3: Should-NOT-trigger — explain code request

**Given** user wants to understand existing code in the project
**When** user says "explain how the auth middleware works"
**Then**
- [ ] study does NOT activate
- [ ] User gets code explanation from base Claude or explaining-code skill
