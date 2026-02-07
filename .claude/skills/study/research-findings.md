# Research Findings: Optimal Research Prompting for LLM Agents

Research conducted: 2026-02-05

## Sources Consulted

### High Quality (Official/Academic)
| Source | URL | Quality | Key Contribution |
|--------|-----|---------|------------------|
| Anthropic: Building Effective Agents | https://www.anthropic.com/engineering/building-effective-agents | Accepted | Orchestrator-workers pattern, ACI design |
| Anthropic: Multi-Agent Research System | https://www.anthropic.com/engineering/multi-agent-research-system | Accepted | 8 prompting principles, search strategy |
| Anthropic: Context Engineering | https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents | Accepted | Altitude calibration, progressive disclosure |
| Claude 4 Best Practices | https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-4-best-practices | Accepted | Research prompting, parallel tools |
| LearnPrompting: DecomP | https://learnprompting.org/docs/advanced/decomposition/decomp | Accepted | Task decomposition methodology |
| LearnPrompting: Self-Ask | https://learnprompting.org/docs/advanced/few_shot/self_ask | Accepted | Follow-up question generation |
| Scribbr: Triangulation | https://www.scribbr.com/methodology/triangulation/ | Accepted | Source verification methodology |

### Medium Quality (Cross-Referenced)
- Chain-of-Verification methodology (ACL 2024)
- Hallucination prevention research (multiple academic sources)
- Iterative query refinement (NAACL 2024)

## Key Findings

### 1. Architecture: Orchestrator-Workers Pattern

Anthropic's production research system uses:
- **Lead agent** (Claude Opus): Plans research approach, delegates tasks
- **Subagents** (Claude Sonnet): Execute parallel searches with independent contexts
- **Result**: 90.2% improvement over single-agent Claude Opus

Key insight: Token usage explains 80% of performance variance. More tokens = better research.

### 2. Eight Core Prompting Principles (from Anthropic)

1. **Mental modeling**: Simulate step-by-step to catch edge cases
2. **Delegation clarity**: Clear objectives, output formats, task boundaries
3. **Effort scaling**: Simple queries = 1 agent, 3-10 calls. Complex = 10+ subagents
4. **Tool ergonomics**: Distinct tool purposes, clear descriptions
5. **Self-improvement**: Agent can diagnose failures and improve (40% time reduction)
6. **Breadth-first search**: Start broad, progressively narrow
7. **Extended thinking**: Use visible thinking for planning
8. **Parallel execution**: 3-5 parallel subagents, 3+ parallel tool calls (90% time reduction)

### 3. Search Strategy: Breadth-First, Then Deep

From Anthropic's research system:
> "Search strategy should mirror expert human research: explore the landscape before drilling into specifics."

Pattern:
1. Start with short, broad queries
2. Evaluate what's available
3. Progressively narrow focus
4. Deep crawl promising sources (follow links 1-2 levels)

Anti-pattern: Starting with narrow, specific queries misses context.

### 4. Source Quality Evaluation

**ACCEPT (High Quality)**
- Official documentation
- Active GitHub repos with contributors
- Domain expert content (verify credentials)
- Peer-reviewed research
- Stack Overflow (high votes + recent)
- Content < 2 years old

**REJECT (Low Quality)**
- AI-generated SEO content (signs: "In today's fast-paced world", no code, keyword stuffing)
- No code examples or concrete details
- Outdated (>2 years unless foundational)
- Forum posts without verification
- "Top 10 best X" listicles
- Contradicts official docs

### 5. Verification Techniques

**Triangulation** (from research methodology):
- Data triangulation: Verify across multiple data sources
- Methodological triangulation: Use multiple approaches
- Cross-reference: Claims must appear in 2+ independent sources

**Chain-of-Verification (CoVe)**:
1. Generate baseline response
2. Generate verification questions targeting weak points
3. Answer verification questions independently
4. Compare for consistency
5. Regenerate response using only consistent facts

**Multi-agent consensus**:
- Run multiple agents on same query
- Compare outputs
- Flag disagreements as potential hallucinations

### 6. Question Decomposition

**Self-Ask Pattern** (proven effective for factual research):
```
Question: [complex question]
Are follow up questions needed here: Yes.
Follow up: [sub-question 1]
Intermediate answer: [answer 1]
Follow up: [sub-question 2]
Intermediate answer: [answer 2]
...
So the final answer is: [synthesis]
```

**Decomposed Prompting**:
1. Decomposer breaks task into sub-tasks
2. Each sub-task delegated to specialized handler
3. Results aggregated

### 7. Claude 4.5 Specific: Research Prompting

From official docs:
```
Search for this information in a structured way. As you gather data, develop
several competing hypotheses. Track your confidence levels in your progress
notes to improve calibration. Regularly self-critique your approach and plan.
Update a hypothesis tree or research notes file to persist information and
provide transparency. Break down this complex research task systematically.
```

Key elements:
- Competing hypotheses (not just one answer)
- Confidence tracking
- Self-critique
- Hypothesis tree / research notes
- Systematic breakdown

### 8. Output Quality Standards

From Anthropic's evaluation:
- **Factual accuracy**: Do claims match sources?
- **Citation accuracy**: Do cited sources support claims?
- **Completeness**: Are all requested aspects covered?
- **Source quality**: Primary sources over secondary?
- **Tool efficiency**: Minimal unnecessary calls?

### 9. Anti-Patterns to Avoid

1. **Stopping at landing pages**: Real info is 1-2 clicks deeper
2. **Single-source claims**: Always cross-reference
3. **Accepting first results**: SEO spam often ranks high
4. **Narrow initial queries**: Miss context and alternatives
5. **No verification step**: Hallucinations slip through
6. **Unstructured findings**: Hard to verify and synthesize

## Comparison with User's Current Patterns

| User Pattern | Assessment | Recommendation |
|--------------|------------|----------------|
| "do deep research" | Good intent | Add structure: hypothesis tree, confidence tracking |
| "research online" | Good | Add: breadth-first, then narrow |
| "find out if X exists" | Good | Add: prior-art checklist |
| "get 20 examples" | Good specificity | Keep - explicit quantity helps |
| "reject low quality" | Good | Add: CRAAP criteria, specific rejection rules |
| "save to file" | Good | Keep - persistence is crucial |
| "deep crawl links" | Excellent | Keep - matches Anthropic's approach |
| "latest info (today is date)" | Good | Keep - recency filter |

**Gaps to address:**
1. No explicit verification/cross-reference step
2. No hypothesis tracking
3. No confidence levels
4. No self-critique phase
5. No structured decomposition of complex questions

## Recommended Skill Design

Based on research, the optimal research skill should:

1. **Start with question decomposition** (Self-Ask pattern)
2. **Use breadth-first search** (broad → narrow)
3. **Apply strict quality filters** (CRAAP-based)
4. **Require cross-verification** (2+ sources for claims)
5. **Track hypotheses and confidence** (Claude 4.5 pattern)
6. **Include self-critique phase** (before finalizing)
7. **Save structured findings** (persistence)
8. **Support depth scaling** (quick vs full modes)
