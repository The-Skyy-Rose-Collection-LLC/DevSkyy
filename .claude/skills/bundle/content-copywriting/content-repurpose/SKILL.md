---
name: content-repurpose
description: "Repurposes a single piece of content (blog post, transcript, newsletter, video script) into multiple platform-ready formats including social posts, email copy, threads, and short-form video scripts. Use when a user has existing content they want to distribute across multiple channels without writing everything from scratch."
allowed-tools: Read Grep Glob Write
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Content Repurpose

## When to Use This Skill

Use this skill when you have:
- A blog post, article, or long-form piece you want to distribute across channels
- A video or podcast transcript you want to turn into written content
- A newsletter issue you want to break into social posts
- Any single piece of content that should become 5-10 pieces across platforms

**DO NOT** use this skill for creating original content from scratch — this is for repurposing existing content only.

## How It Works

EVERY PIECE OF REPURPOSED CONTENT MUST SOUND NATIVE TO ITS PLATFORM — NOT LIKE A COPY-PASTE WITH MINOR EDITS.

### Phase 1: Extract the Core

Read the source content and pull out:

1. **The one big idea** — the single takeaway someone should remember
2. **3-5 supporting points** — arguments, examples, or data that back the big idea
3. **Quotable lines** — phrases that work standalone (stats, bold claims, counterintuitive takes)
4. **Story elements** — any anecdotes, case studies, or personal experiences
5. **Tactical advice** — specific how-to steps, frameworks, or actionable tips

Present this extraction to the user before proceeding:

```
## Content Core

**Big idea:** [one sentence]

**Supporting points:**
1. [point]
2. [point]
3. [point]

**Best quotes:** [2-3 standalone lines]

**Story elements:** [brief list]

**Tactical takeaways:** [actionable items]
```

Wait for user confirmation or adjustments before Phase 2.

### Phase 2: Repurpose by Channel

Transform the extracted core into each platform format. **Default channels** (skip any the user doesn't want):

#### X/Twitter Thread (5-10 tweets)
- Hook tweet: bold claim, surprising stat, or contrarian take — no hashtags on hook
- Each tweet = one idea, under 280 characters
- Use line breaks for readability
- End with a CTA tweet (follow, bookmark, repost)
- Add 1-3 relevant hashtags on final tweet ONLY

Example:
```
Most people create content once and let it die.

That one blog post you spent 6 hours on? It could become:
- 1 Twitter thread
- 1 LinkedIn post
- 3 Instagram carousels
- 1 newsletter issue
- 2 short-form video scripts

Here's exactly how (thread):
```

#### LinkedIn Post (150-300 words)
- Open with a hook line, then a line break
- Short paragraphs (1-3 sentences max)
- Professional but conversational tone
- Include a specific result, number, or lesson
- End with a question to drive comments
- 3-5 hashtags at the bottom

Example:
```
I stopped creating new content 3 months ago.

My engagement went UP 40%.

Here's what I did instead:

I took my best-performing blog post and turned it into
12 pieces of content across 4 platforms.

Same ideas. Different formats. Wider reach.

The key? Each piece has to feel NATIVE to the platform...

What's your best-performing piece of content? Drop it below.

#ContentStrategy #Solopreneur #ContentRepurposing
```

#### Instagram Caption (100-200 words)
- Hook in the first line (this shows before "more")
- Use emoji sparingly as bullet points or section breaks
- Conversational, direct tone
- End with a CTA (save, share, comment)
- 15-25 hashtags in a comment block below, NOT in the caption

#### Email Newsletter Snippet (200-400 words)
- Subject line: curiosity gap or specific benefit
- Personal opening (1-2 sentences, like writing to a friend)
- Core insight in 2-3 short paragraphs
- One clear CTA (reply, click, try something)
- P.S. line with a secondary hook

#### Short-Form Video Script (30-60 seconds)
- Hook (first 3 seconds): question, bold statement, or pattern interrupt
- Setup (10 seconds): context for why this matters
- Payoff (15-30 seconds): the key insight or steps
- CTA (5 seconds): follow, comment, or try it
- Include [VISUAL CUE] notes for on-screen text or B-roll

Example:
```
HOOK: "Stop making new content."

[TEXT ON SCREEN: "The repurposing framework"]

SETUP: "That blog post you spent all week on?
Most people post it once and move on.
Here's what to do instead."

PAYOFF: "Take your one big idea and break it into three parts.
Part one becomes a Twitter thread.
Part two becomes a LinkedIn post.
Part three becomes this — a 30-second video.
Same work. Five times the reach."

CTA: "Follow for more content systems that save you time."
```

### Phase 3: Deliver and Organize

Present all repurposed content in a single organized output:

1. **Platform sections** — each clearly labeled with word/character counts
2. **Posting order** — which piece to post first for maximum cross-platform momentum (typically: Twitter thread > LinkedIn > Email > Instagram > Video)
3. **Timing suggestion** — stagger posts across 3-5 days, not all at once

**IMPORTANT:** If the user provides a file path, write each platform's content to a separate file:
```
output/
├── twitter-thread.md
├── linkedin-post.md
├── instagram-caption.md
├── email-snippet.md
└── video-script.md
```

## Recovery

- **Source content is too short** (under 200 words): Ask the user for additional context or talking points before extracting. Do not pad thin content.
- **Source content is off-brand or unclear**: Ask the user to clarify their voice, audience, or main point before repurposing.
- **User wants a platform not listed**: Ask for platform constraints (character limit, tone, format) and create a custom format following the same extract-then-adapt approach.

## Anti-Patterns

- **DO NOT** copy-paste the same text with minor tweaks across platforms
- **DO NOT** use generic hooks like "Here's what I learned" — every hook must be specific
- **DO NOT** add hashtags to Twitter hooks or LinkedIn opening lines
- **DO NOT** exceed platform character/word limits
- **DO NOT** include links in the repurposed content unless the user specifically provides them
