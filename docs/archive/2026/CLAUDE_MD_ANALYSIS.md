# CLAUDE.md Analysis & Recommendations

**Date**: 2026-02-08
**Based on**: Boris Cherny's best practices
**Current Main CLAUDE.md**: 161 lines, 908 words

---

## Boris Cherny's Key Principles

Based on research from multiple sources, here are Boris Cherny's core recommendations:

### 1. **Keep It Concise** ⭐
- Boris's CLAUDE.md: **~100 lines** (2.5k tokens)
- Our current file: **161 lines** (closer but could be tighter)
- **Finding**: One developer had an **847-line CLAUDE.md** that was 8x longer and producing **worse results**

### 2. **Self-Correcting System** ⭐⭐⭐
- **Rule**: "When Claude does something wrong, add it so it doesn't repeat"
- Update **multiple times weekly**
- Transform codebase into a "self-correcting organism"
- Focus on **mistakes** and **corrections**, not exhaustive documentation

### 3. **Team Ownership**
- Each team maintains their own CLAUDE.md in git
- Shared standards encode "safety rails" (never touch prod, always run tests)
- Use in PR reviews: tag `@.claude` to update the file

### 4. **Verification Loops** ⭐⭐
- Most important tip: Give Claude a way to **verify its work**
- Run bash commands, test suites, browser/simulator tests
- Optimize for **cost per reliable change**, not cost per token

### 5. **Short Cycles**
- One behavior change → one PR-sized diff → one verification path
- **Ethics-by-design**: Write clear rules once, not constant oversight

---

## Current CLAUDE.md Analysis

### ✅ What We're Doing Right

1. **Concise Protocol** (lines 5-11): Clear 6-step workflow
2. **Testing Emphasis**: "pytest AFTER EVERY CHANGE" (repeated 3 times)
3. **Gotchas Section**: Captures past mistakes (WP.com API, 3D CDNs, Collection Pages)
4. **Actionable Rules**: "Use Serena", "ALWAYS query Context7"
5. **Reasonable Length**: 161 lines (vs Boris's ~100, not the 847-line anti-pattern)

### ⚠️ Potential Improvements Based on Boris's Principles

#### 1. **Too Much Reference Material** (Lines 13-77)
**Issue**: Extensive tool listings, dependency lists, codebase structure
**Boris's Approach**: Focus on **mistakes and corrections**, not comprehensive docs
**Impact**: 64 lines (40% of file) are reference material

**Recommendation**:
- Move detailed tool catalogs to separate docs (e.g., `docs/MCP_TOOLS.md`)
- Move dependency lists to `docs/DEPENDENCIES.md`
- Keep only **gotchas** and **corrections** in CLAUDE.md

#### 2. **Static Information vs Dynamic Corrections**
**Issue**: Lines 146-161 describe completed phases (v1.3.1, v3.0.0)
**Boris's Approach**: CLAUDE.md should be **living corrections**, not project history
**Impact**: 16 lines (10% of file) are historical status

**Recommendation**:
- Move project phases to `CHANGELOG.md` or `README.md`
- Use CLAUDE.md for "what went wrong and how to avoid it"

#### 3. **Missing Self-Correction Cadence**
**Issue**: No explicit "update CLAUDE.md" rule in workflow
**Boris's Approach**: Update **multiple times weekly** when Claude makes mistakes

**Recommendation**:
- Add explicit self-correction step to Protocol:
  ```
  7. **Learn** → After any correction, update CLAUDE.md with rule
  ```

#### 4. **Verification Loops Could Be Stronger**
**Issue**: "pytest -v" is mandated but no broader verification strategy
**Boris's Approach**: Give Claude multiple ways to verify its work

**Recommendation**:
- Add verification commands for each module type
- Examples: health checks, linting, type checking, build verification

#### 5. **No Documented Mistake Patterns**
**Issue**: Gotchas section exists but doesn't use Boris's "self-correcting" language
**Boris's Approach**: Frame as "Claude did X wrong, now do Y instead"

**Recommendation**:
- Reframe gotchas as learnings:
  ```markdown
  ## Learnings (Updated Weekly)
  - ❌ **Mistake**: Using `/wp-json/` for WordPress.com API
    ✅ **Correct**: Use `index.php?rest_route=` instead
  ```

---

## Recommended CLAUDE.md Structure

Based on Boris Cherny's principles:

```markdown
# DevSkyy — Claude Config

## Protocol (Do This Every Time)
1. Context7 → Serena → Navigate → Implement → Test → Format → Learn

## Verification Commands (Run After Changes)
- Python: pytest -v && mypy . && ruff check
- JavaScript: npm test && npm run type-check
- WordPress: wp theme list && wp theme verify

## Learnings (Updated Weekly When Claude Makes Mistakes)

### WordPress
- ❌ Using /wp-json/ → ✅ Use index.php?rest_route= (WordPress.com)
- ❌ Assuming page purpose → ✅ Read PAGES-DOCUMENTATION.md first
- ❌ Immersive = catalog → ✅ Immersive = 3D storytelling, catalog = shopping

### Testing
- ❌ Skipping tests → ✅ pytest -v after EVERY file touch
- ❌ <80% coverage → ✅ 90%+ coverage required

### Architecture
- ❌ Circular dependencies → ✅ One-way flow: core → adk → security → agents → api
- ❌ Using base_legacy.py → ✅ Use adk/base_super_agent.py

### 3D Development
- ❌ Using CDN URLs without checking → ✅ VERIFY URLs exist first
- ❌ Forgetting correlation IDs → ✅ ALWAYS propagate correlation_id

## Critical Rules
- NO deletions, refactor only
- Context7 BEFORE any library code
- Serena for WordPress file operations
- pytest AFTER EVERY CHANGE

## Quick Reference
- Brand: #B76E79 "Where Love Meets Luxury"
- Health: /health /health/ready /health/live /metrics
- Docs: docs/CONTRIB.md, docs/RUNBOOK.md, docs/ENV_VARS_REFERENCE.md
```

**New Structure Benefits**:
- **Shorter**: ~80-100 lines (vs current 161)
- **Self-Correcting**: "Learnings" section grows as mistakes happen
- **Action-Oriented**: Focus on "do this, not that"
- **Verification-First**: Multiple verification commands upfront

---

## Proposed Changes

### Immediate Actions

1. **Create Supporting Documents** (move reference material out):
   - `docs/MCP_TOOLS.md` - Complete MCP tool catalog
   - `docs/DEPENDENCIES.md` - Python/JS dependency lists
   - `docs/ARCHITECTURE.md` - Codebase structure and phases

2. **Restructure Main CLAUDE.md**:
   - Keep Protocol (with added "Learn" step)
   - Keep Verification Commands (expand)
   - Reframe Gotchas as "Learnings" (mistake → correction format)
   - Move reference material to docs/
   - Target: **~100 lines**

3. **Add Self-Correction Workflow**:
   - Add to Protocol: "7. **Learn** → Update CLAUDE.md after corrections"
   - Add to docs/CONTRIB.md: "Update CLAUDE.md weekly with mistakes"
   - Create `scripts/claude-md-reminder.sh` to prompt updates

4. **Update Subdirectory CLAUDE.md Files**:
   - Apply same principles to: `core/`, `agents/`, `llm/`, `security/`, etc.
   - Each should focus on module-specific learnings
   - Keep to <50 lines each

### Secondary Actions (Optional)

5. **PR Integration** (like Boris):
   - Add GitHub Action to tag @.claude on PRs
   - Prompt to update CLAUDE.md during code review
   - Treat code review as meta-process for improving AI

6. **Metrics Tracking**:
   - Track CLAUDE.md updates per week
   - Measure correlation between updates and fewer repeated mistakes
   - Goal: 2-3 updates per week minimum

---

## Key Insights from Research

From the sources analyzed:

1. **[VentureBeat Article](https://venturebeat.com/technology/the-creator-of-claude-code-just-revealed-his-workflow-and-developers-are)**: Boris's CLAUDE.md is 2.5k tokens (~100 lines). Teams update multiple times weekly.

2. **[Karo Zieminski Substack](https://karozieminski.substack.com/p/boris-cherny-claude-code-workflow)**: CLAUDE.md serves as **institutional memory**. Rule: "When Claude does something wrong, add it so it doesn't repeat."

3. **[InfoQ Article](https://www.infoq.com/news/2026/01/claude-code-creator-workflow/)**: Boris uses CLAUDE.md in **PR reviews** by tagging @.claude. This treats code review as a meta-process that improves future outputs.

4. **[UC Strategies](https://ucstrategies.com/news/12-tips-from-claude-codes-creator-to-vibe-code-faster-and-safer/)**: Most important tip: Give Claude a way to **verify its work** through feedback loops (bash commands, test suites, browser testing).

5. **[Medium Article](https://alirezarezvani.medium.com/your-claude-md-is-probably-wrong-7-mistakes-boris-cherny-never-makes-6d3e5e41f4b7)**: One developer's **847-line CLAUDE.md** was 8x longer than Boris's and producing **worse results**. Fixed 7 configuration mistakes in 3 hours.

---

## Anti-Patterns to Avoid

Based on Boris's principles and research:

1. ❌ **Over-Documentation**: 847 lines of comprehensive reference material
2. ❌ **Static Information**: Project history, completed phases, version logs
3. ❌ **Exhaustive Lists**: Every tool, every dependency, every file path
4. ❌ **No Updates**: "Set it and forget it" approach
5. ❌ **Missing Verification**: No clear way for Claude to check its work
6. ❌ **Generic Rules**: "Write good code" vs "❌ Using X → ✅ Use Y instead"

## Best Practices to Adopt

1. ✅ **Concise & Focused**: ~100 lines, mistakes and corrections only
2. ✅ **Self-Correcting**: Update weekly when Claude makes mistakes
3. ✅ **Verification-First**: Multiple verification commands upfront
4. ✅ **Specific Learnings**: "❌ Mistake → ✅ Correction" format
5. ✅ **Living Document**: Git-tracked, team-owned, PR-integrated
6. ✅ **Actionable**: "Do this, not that" - clear, testable rules

---

## Summary

**Current State**: 161 lines, good foundation but too much reference material

**Target State**: ~100 lines, focused on mistakes/corrections with strong verification loops

**Next Steps**:
1. Create supporting docs (MCP_TOOLS.md, DEPENDENCIES.md, ARCHITECTURE.md)
2. Restructure main CLAUDE.md (Protocol + Verification + Learnings)
3. Add self-correction workflow (update weekly)
4. Apply to subdirectory CLAUDE.md files

**Expected Impact**:
- Shorter, more actionable CLAUDE.md
- Self-correcting system that improves over time
- Fewer repeated mistakes
- Better alignment with Boris Cherny's proven approach

---

## Sources

- [VentureBeat: The creator of Claude Code just revealed his workflow](https://venturebeat.com/technology/the-creator-of-claude-code-just-revealed-his-workflow-and-developers-are)
- [Karo Zieminski: How Boris Cherny Uses Claude Code](https://karozieminski.substack.com/p/boris-cherny-claude-code-workflow)
- [InfoQ: Inside the Development Workflow of Claude Code's Creator](https://www.infoq.com/news/2026/01/claude-code-creator-workflow/)
- [UC Strategies: 12 Tips From Claude Code's Creator](https://ucstrategies.com/news/12-tips-from-claude-codes-creator-to-vibe-code-faster-and-safer/)
- [Medium: Your CLAUDE.md Is Probably Wrong: 7 Mistakes Boris Cherny Never Makes](https://alirezarezvani.medium.com/your-claude-md-is-probably-wrong-7-mistakes-boris-cherny-never-makes-6d3e5e41f4b7)
- [Threads: Boris Cherny's Claude Code Tips](https://www.threads.com/@boris_cherny/post/DUMZr4VElyb)
- [Twitter: Boris Cherny's Setup](https://x.com/bcherny/status/2007179832300581177)

**Document Owner**: DevSkyy Platform Team
**Next Review**: After implementing changes
