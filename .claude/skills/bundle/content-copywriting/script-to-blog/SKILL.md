---
name: script-to-blog
description: "Converts video or podcast transcripts into polished, SEO-optimized blog posts with proper formatting. Use when repurposing audio/video content into written articles."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Script to Blog

## When to Use This Skill

Use this skill when you need to:
- Convert a video transcript or podcast episode into a blog post
- Repurpose spoken content into an SEO-optimized written article
- Transform a rough script or talk into a polished, publishable piece
- Extract key insights from long-form audio/video into a scannable blog format

**DO NOT** use this skill for writing original blog posts from scratch (use blog-post skill) or for creating transcripts from audio files.

---

## Core Principle

SPOKEN CONTENT AND WRITTEN CONTENT ARE DIFFERENT MEDIUMS — A TRANSCRIPT IS NOT A BLOG POST. THE CONVERSION MUST RESTRUCTURE, TIGHTEN, AND OPTIMIZE FOR READING.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Transcript** | "Paste the transcript or provide the file." | No default — must be provided |
| **Source type** | "Is this from a video, podcast, webinar, or presentation?" | Podcast |
| **Target keyword** | "What keyword should this blog post rank for?" | Extract from transcript topic |
| **Audience** | "Who is reading the blog version?" | Same as the video/podcast audience |
| **Word count** | "Target blog post length?" | 1,200-1,800 words |
| **Embed the original?** | "Should the blog post embed or link to the original video/podcast?" | Yes — embed at the top |

**GATE: Confirm brief before analyzing the transcript.**

---

## Phase 2: Outline

### Transcript Analysis

Before outlining, analyze the transcript for:

```
## Transcript Analysis

**Core topic:** [Main subject of the recording]
**Key insights (5-8):** [The most valuable points made]
**Quotable moments:** [2-3 direct quotes worth keeping]
**Tangents to cut:** [Off-topic sections that do not serve the blog reader]
**Missing context:** [Things that were clear in video but need explanation in text]
**Estimated blog word count:** [Based on useful content in the transcript]
```

### Blog Post Outline

Build an outline that restructures the spoken content for reading:

```
**H1:** [SEO-optimized title based on the core topic]

**Intro** (~150 words)
- [Hook — different from how the episode started]
- [What the reader will learn]
- [Embed: original video/podcast player]

**H2: [Section 1]** (~[words])
- [Key points from transcript]

**H2: [Section 2]** (~[words])
- [Key points]
...

**Conclusion + CTA** (~100 words)
```

**GATE: Approve outline before writing.**

---

## Phase 3: Write

### Conversion Rules

| Rule | Detail |
|------|--------|
| **Cut filler** | Remove "um," "you know," "like I said," verbal tics, and repetition |
| **Restructure for logic** | Spoken content meanders — reorganize by topic, not by chronological order |
| **Tighten sentences** | Spoken sentences are long. Written paragraphs are 2-3 sentences. |
| **Add context** | Things obvious in video (gestures, screen shares, visuals) need written explanation |
| **Keep the voice** | Preserve the speaker's personality and key phrases — do not sanitize into corporate tone |
| **Format for scanning** | Add headers, bullet points, bold text, and pull quotes |
| **SEO optimize** | Add keyword to H1, first 100 words, at least one H2, and meta description |

### What to Keep vs Cut

**Keep:**
- Original insights and unique perspectives
- Specific examples, stories, and data
- Direct quotes that are punchy and quotable
- Actionable advice and frameworks

**Cut:**
- Small talk and episode intros ("Welcome back to the show...")
- Tangents and off-topic diversions
- Repeated points (consolidate into one strong version)
- References to visual content ("as you can see on screen...") — translate to text descriptions
- Excessive hedging and filler

### Deliverables

1. **Full blog post** with H1, H2s, formatted body, and CTA
2. **Meta description** (150-160 characters)
3. **Embed placement** note for the original video/podcast
4. **Pull quotes** — 2-3 direct quotes from the speaker formatted as callouts

---

## Phase 4: Polish

### 1. Conversion Quality Checklist

```
## Checklist

- [ ] Blog post reads as a standalone article (no "as I mentioned in the episode" references)
- [ ] Filler words and verbal tics are removed
- [ ] Content is restructured by topic (not transcript chronological order)
- [ ] Speaker's voice and personality are preserved
- [ ] Visual references are translated to written descriptions
- [ ] 2-3 direct quotes are included as pull quotes
- [ ] SEO elements are in place (keyword in H1, first 100 words, H2)
- [ ] Meta description is written (150-160 characters)
- [ ] Embed placement for original video/podcast is noted
- [ ] Word count is within target range
```

### 2. SEO Checklist

Standard blog SEO checklist: keyword placement, heading hierarchy, internal link suggestions, alt text for images.

### 3. Companion Content Suggestions

Suggest 2-3 additional content pieces that could be created from the same transcript:
- Social media post with a key quote
- Email newsletter snippet
- Short-form video clip

---

## Example: Converting a 30-Minute Podcast Episode

```
Transcript: 4,500 words (30-minute episode on freelance pricing)
Blog post target: 1,500 words

Transcript analysis:
- Core topic: How to switch from hourly to value-based pricing
- Key insights: 5 main points across the episode
- Tangents to cut: 800 words of off-topic banter, repeated points
- Quotable: "The moment I stopped selling hours, I started building wealth."

Blog outline:
H1: How to Switch from Hourly to Value-Based Pricing (Without Losing Clients)
H2: Why Hourly Pricing Caps Your Income
H2: The Value-Based Pricing Framework
H2: How to Have the Pricing Conversation
H2: What to Do When Clients Push Back
H2: Your First Value-Based Proposal — Start This Week
```

---

## Anti-Patterns

- **Publishing the raw transcript** — transcripts are not blog posts. They read poorly, rank poorly, and look unprofessional.
- **Cutting too much personality** — the speaker's voice is what makes repurposed content authentic. Keep their phrasing and style.
- **Keeping the chronological order** — podcasts meander. Blog posts should be structured by topic relevance, not recording order.
- **Ignoring visual references** — "as you can see on screen" means nothing in a blog post. Describe what was shown.
- **No SEO optimization** — repurposed content without keyword targeting misses the primary benefit of having a blog version.

---

## Recovery

- **Transcript is too short (<1,000 words):** Expand with additional context, examples, and explanations that complement the original.
- **Transcript is too long (>5,000 words):** Split into 2-3 focused blog posts, each targeting a different keyword.
- **Multiple speakers:** Attribute key insights to each speaker. Use direct quotes with attribution.
- **Poor audio quality / bad transcript:** Work with what is usable. Flag sections that are unclear and ask the user to clarify.
- **Speaker wants every word included:** Explain that written and spoken content serve different purposes. Offer a "full transcript" appendix at the bottom of the blog post as a compromise.
