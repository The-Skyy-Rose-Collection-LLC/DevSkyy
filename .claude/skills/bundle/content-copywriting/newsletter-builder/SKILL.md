---
name: newsletter-builder
description: "Creates complete newsletters from editorial brief to final visual layout, planning content in Notion and generating the designed version in Canva. Use when a user needs to produce a recurring newsletter issue, build a newsletter from scratch, or transform raw ideas into a polished send-ready newsletter."
allowed-tools: Read Write Glob mcp__claude_ai_Notion__notion-create-pages mcp__claude_ai_Notion__notion-search mcp__claude_ai_Notion__notion-fetch mcp__claude_ai_Canva__generate-design-structured mcp__claude_ai_Canva__list-brand-kits mcp__claude_ai_Canva__export-design mcp__claude_ai_Canva__get-export-formats mcp__claude_ai_Canva__get-design-thumbnail
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Newsletter Builder

## When to Use This Skill

Use this skill when you need to:
- Produce a recurring newsletter issue from topic to send-ready output
- Build a new newsletter from scratch with structure, content, and visual design
- Transform raw notes or ideas into a polished newsletter with a designed layout
- Create both plain-text and visually designed PDF versions of a newsletter

**DO NOT** use for one-off promotional emails, social media content, or blog posts.

---

## Core Principle

EVERY NEWSLETTER EARNS ITS OPEN WITH THE SUBJECT LINE, EARNS ITS READ WITH THE INTRO HOOK, AND EARNS ITS CLICK WITH ONE CLEAR CTA — IF ANY OF THESE THREE FAIL, THE NEWSLETTER FAILS.

---

## Newsletter Structure Template

```
SUBJECT LINE:   [Curiosity gap or specific benefit — under 50 chars]
PREVIEW TEXT:    [Expands on subject — 40-90 chars, visible in inbox]

── HEADER ──        Newsletter name, issue number, date
── INTRO HOOK ──    2-3 sentences. Bold claim, story beat, or question.
── SECTION 1 ──     200-300 words. Primary topic. Deepest value.
── SECTION 2 ──     150-250 words. Supporting angle or practical application.
── SECTION 3 ──     3-5 bullet points. Quick hits, links, tools. (optional)
── CTA ──           One clear ask. Direct sentence, not buried in a paragraph.
── SIGN-OFF ──      1-2 personal sentences. First-name basis.
── FOOTER ──        Unsubscribe placeholder, social links, legal line.
```

---

## Phase 1: Editorial Brief

Collect before writing anything:

1. **Newsletter name** — brand name (e.g., "The Growth Wire")
2. **Issue topic** — theme for this issue
3. **Target audience** — who reads it and what they care about
4. **Tone** — casual, professional, witty, conversational (default: conversational)
5. **Sections** — how many body sections (default: 2 + quick hits)
6. **Primary CTA** — the one action readers should take
7. **Key links** — any URLs, tools, or resources to include
8. **Recurring elements** — standing segments (e.g., "Tool of the Week")

If the user provides items 1, 2, and 6, proceed with defaults for the rest.

**Brief template for vague requests:**
```
I'll build your newsletter. Quick details needed:
1. Newsletter name?
2. What's this issue about?
3. Who's your audience?
4. Tone? (default: conversational)
5. How many sections? (default: 2 + quick hits)
6. What's the ONE thing you want readers to do after reading?
7. Any links or resources to include?
8. Any recurring segments?
```

Compile into a structured brief:
```
## Editorial Brief — "The Growth Wire: Why Most Funnels Leak"
Newsletter: The Growth Wire
Audience: Solo founders and early-stage SaaS operators
Tone: Conversational, data-backed
Sections: Intro + 2 body + quick hits + CTA
CTA: Reply with their biggest funnel question
Links: [link1], [link2]
Recurring: "Tool of the Week" in quick hits
```

**GATE: Present the editorial brief. Do not proceed until the user confirms or adjusts.**

---

## Phase 2: Write Content

Write the full newsletter following the structure template.

1. **Subject line and preview text** — provide 2 subject line options. Subject: curiosity gap or specific number, under 50 chars. Preview: expands on subject, 40-90 chars.

2. **Intro hook (2-3 sentences)** — open with a surprising stat, short story, or direct question. End by telling readers what they get from this issue.

3. **Body sections:**
   - **Section 1 (Primary):** 200-300 words. Must include a specific example, number, or case study. Never abstract advice alone.
   - **Section 2 (Supporting):** 150-250 words. Different angle, practical application, or contrarian take. Must feel distinct from Section 1.
   - **Section 3 (Quick Hits):** 3-5 bullets with bolded lead-ins. Under 30 seconds to scan.

4. **CTA section** — one sentence, framed as a benefit to the reader. Example: "Hit reply and tell me your biggest funnel question — I'll answer the best ones next week."

5. **Sign-off** — 1-2 sentences. Example: "Talk next Tuesday. — Matt"

### Save Brief to Notion

After writing, save the editorial brief:

1. Call `notion-search` for "Newsletter," "Editorial," or the newsletter name
2. If found, call `notion-create-pages` with title "{Newsletter} — {Topic}", content including topic, audience, tone, CTA, subject line, and status "Draft"
3. If no database found, create a standalone page with the full brief in the body

**GATE: Present the full newsletter copy. Do not proceed until approved. Maximum 3 revision rounds.**

---

## Phase 3: Design in Canva

### Step 1: Load Brand Kit

1. Call `list-brand-kits` to retrieve kits
2. Present names if multiple exist — let user choose
3. Note brand colors, fonts, and logo for the design prompt

**IF NO BRAND KIT:** Ask for primary color, secondary color, and font preference. Embed directly in generation prompt.

### Step 2: Generate Layout

Build a structured prompt including:
- Newsletter name and issue identifier
- All section headings and body text from approved copy
- Brand colors, fonts, and style
- Layout: single-column, 600px width, mobile-friendly
- CTA styled as a button or highlighted block

Example design prompt:
```
Professional email newsletter layout, single column, 600px width.
Newsletter: "The Growth Wire" — Issue #14
Header: Name with logo area, issue number, date. Color accent bar #F4A261.
Body: White background, #1A3D5C text. Section dividers between blocks.
Section 1: "The Three Places Every Funnel Breaks" — 200-300 words.
Section 2: "The Fix That Takes 20 Minutes" — 150-250 words.
Section 3: "Quick Hits" — 3-5 bullet items.
CTA button: #F4A261 background, white text.
Footer: Light gray, unsubscribe placeholder.
Font: Inter Bold headings, Inter Regular body. Clean, generous whitespace.
```

1. Call `generate-design-structured` with the prompt
2. Call `get-design-thumbnail` to preview
3. Present thumbnail: "Does this look good, or would you like adjustments?"
4. **Wait for approval** before exporting

**IF DESIGN MISSES:** Regenerate with adjusted prompt. Maximum 2 attempts. After 2, ask user for a reference image or specific layout description.

---

## Phase 4: Export and Deliver

### Step 1: Export PDF
1. Call `get-export-formats` to confirm formats
2. Call `export-design` with format `pdf` (default — preserves layout)
3. Collect the export URL

### Step 2: Save Plain-Text Version
Save as markdown to `newsletter-output/{name}-{topic}.md` (all lowercase, hyphens). Include subject line, preview text, all sections, CTA, sign-off, footer.

### Step 3: Update Notion
Call `notion-search` to find the brief page, then `notion-fetch` for the page ID. Update status to "Designed" if supported, or add a note to the page body.

### Step 4: Deliver
```
Newsletter complete: "The Growth Wire — Issue #14: Why Most Funnels Leak"

PLAIN-TEXT: newsletter-output/the-growth-wire-why-most-funnels-leak.md
DESIGNED PDF: [export URL]  |  Design ID: dsg_nl789abc
NOTION: "The Growth Wire — Why Most Funnels Leak" — Status: Designed
Subject: "Why most funnels leak (and a 20-min fix)"
Preview: "Plus 5 tools I found this week that actually help."
```

---

## Example 1: Weekly Business Tips Newsletter

**User:** "I run 'Solo Ops' for solopreneurs. This week: 3 automations that saved me 10 hours. CTA: reply with their most time-consuming task. Casual tone."

**Phase 1:** Brief confirmed — Solo Ops, solopreneurs, casual/practical, 2 sections + quick hits.

**Phase 2:** Subject line options: A) "3 automations that gave me 10 hours back" B) "I automated my way out of busywork" — user picks A. Preview: "No code required. Just 3 tools and 30 minutes of setup."

Newsletter written:
- Intro hook: tracked tasks for a week, found 10 hours of automatable work
- Section 1 (280 words): three automations — client onboarding via Zapier (saved 3 hrs/mo), invoice reminders via Stripe (collections 82% to 96%), social scheduling via Buffer (saved 4 hrs/wk). Total setup: 90 minutes.
- Section 2 (180 words): why solopreneurs do not automate — the "I'll just do it quick" trap. Fix: track time for one week, automate top 3 by hours spent.
- Quick hits: Zapier vs Make comparison, HubSpot free CRM, podcast rec, quote of the week
- CTA: "Hit reply — what task eats most of your time?"

Notion page created: "Solo Ops — 3 Automations That Saved Me 10 Hours" (Draft).

**Phase 3:** Brand kit "Solo Ops" loaded (#222831 primary, #00ADB5 secondary, Space Grotesk). Design generated — dark header, teal accents, teal CTA button. User approves.

**Phase 4:** PDF exported. Plain-text saved to `newsletter-output/solo-ops-3-automations-saved-10-hours.md`. Notion status updated to "Designed."

---

## Example 2: Monthly Product Update Newsletter

**User:** "Monthly product update called 'Buildlog' for paying customers. Shipped new dashboard, fixed export bug, launching beta for team collaboration. CTA: sign up for beta. Professional but friendly."

**Phase 1:** Brief confirmed — Buildlog, paying SaaS customers, professional-friendly, 3 sections (feature + fixes + beta). User provides beta URL.

**Phase 2:** Subject: "New dashboard is live + beta invite inside." Preview: "Plus we finally squashed that export bug."

Newsletter written:
- Intro hook: big build month — dashboard live, export bug gone, beta launching
- Section 1 (250 words): new analytics dashboard — real-time data (30-sec updates), custom date ranges, drag-and-drop widget layout
- Section 2 (150 words): bug fixes — CSV export UTF-8 fix, notification latency reduced to <15s, mobile sidebar overlap resolved
- Section 3 (200 words): team collaboration beta — shared workspaces with roles, comment threads with @mentions, activity audit log. First 500 spots.
- CTA: "Sign up for the beta — first 500 spots, no credit card required."

User approves after one edit (changed beta limit 200 to 500). Notion page created.

**Phase 3:** Brand kit "Buildlog" loaded (#0F172A, #3B82F6, #10B981, IBM Plex Sans). Design: dark header, blue accent, green CTA button. Approved.

**Phase 4:** PDF exported. Plain-text saved. Notion updated.

---

## Anti-Patterns

- **Walls of text** — no paragraph over 4 lines. Readers scan, they do not read newsletters like articles.
- **Skipping the CTA** — every issue needs exactly one clear call to action. "Hope you enjoyed this" is not a CTA.
- **Same-length sections** — vary lengths (long, medium, scannable). Uniform 200-word sections feel monotonous.
- **Generic subject lines** — "Monthly Update" or "Newsletter #14" will not get opened. Create curiosity or promise a specific benefit.
- **Burying the best content** — strongest section goes first. Readers drop off after the intro.
- **Multiple CTAs** — "Reply AND follow AND check this link AND sign up." Pick one.
- **No preview text** — blank preview pulls "View in browser" or header code. Always write custom preview text.
- **Writing for everyone** — a newsletter for "anyone in business" is for no one. Each issue speaks to a specific reader with a specific problem.

---

## Recovery

**Notion search finds nothing:** Ask user for a Notion page URL or create a standalone page. Notion is for records, not a blocker.

**Notion page creation fails:** Retry once simplified (title + plain text only). If still fails, save brief locally to `newsletter-output/{name}-brief.md`. Continue to Phase 3.

**No Canva brand kit:** Ask for primary color, secondary color, font preference. Embed in prompt. Suggest creating a brand kit for future issues.

**Canva design generation fails:** Simplify prompt (headline + colors + CTA only), retry once. **If 2 attempts fail:** deliver plain-text only and suggest manual Canva template.

**Canva export fails:** Verify design ID via `get-design-thumbnail`. Try PNG instead of PDF. If both fail, provide design ID for manual export from canva.com.

**Custom sections requested:** Add between last body section and CTA. Same length guidelines (100-250 words or 3-5 bullets). Include in Canva prompt.

**If 3 attempts at any step fail:** Stop and deliver what is complete. Brief only, plain-text only, or plain-text + brief without design. Explain which step failed.

---

## Pre-Delivery Checklist

| Check | Verify |
|-------|--------|
| Subject line under 50 chars | Mobile inboxes truncate aggressively |
| Preview text written | Never blank or defaulted |
| Intro hook 2-3 sentences | Not a paragraph, not a single line |
| Clear heading on every section | Readers scan headings first |
| Section lengths vary | Mix long, medium, scannable |
| Exactly one CTA | Not zero, not three |
| CTA framed as reader benefit | "Get X" not "Help me by doing X" |
| No section over 300 words | Newsletters are not blog posts |
| Plain-text file saved | Pasteable into any email platform |
| Notion brief saved | Editorial record for future reference |
| Canva design approved | Thumbnail shown and confirmed |
| PDF exported | Designed version ready for sharing |
