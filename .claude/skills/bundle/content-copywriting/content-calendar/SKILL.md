---
name: content-calendar
description: "Generates a 30-day content calendar as a Notion database with posts mapped to content pillars, platforms, and dates, plus starter graphic templates in Canva for each content pillar. Use when a user needs to plan their content for the month, wants a structured posting schedule, or needs to batch-create content across multiple platforms."
allowed-tools: Read Write Glob mcp__claude_ai_Notion__notion-create-database mcp__claude_ai_Notion__notion-create-pages mcp__claude_ai_Notion__notion-search mcp__claude_ai_Canva__generate-design mcp__claude_ai_Canva__list-brand-kits mcp__claude_ai_Canva__create-folder mcp__claude_ai_Canva__move-item-to-folder mcp__claude_ai_Canva__get-design-thumbnail
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Content Calendar

## When to Use This Skill

Use this skill when the user needs to:
- Plan 30 days of content across one or more platforms
- Build a structured posting schedule mapped to content pillars and post types
- Create a Notion database to track content status from idea through published
- Generate starter Canva graphic templates for each content pillar
- Batch-plan content for Instagram, LinkedIn, X/Twitter, YouTube, TikTok, newsletter, or podcast

**DO NOT** use this skill for:
- Writing full-length blog posts or articles (use a content writing skill)
- Creating individual social media graphics on demand (use social-media-graphics)
- Managing an existing content calendar that already lives in Notion (the user should edit it directly)
- One-off post creation with no broader monthly plan

---

## Content Pillar Framework

Every calendar is built on 3-5 content pillars. Pillars prevent random posting and make batching possible.

| Pillar Type | Purpose | Example (Fitness Coach) | Example (SaaS Founder) |
|-------------|---------|------------------------|----------------------|
| **Education** | Teach your audience something actionable | "3 exercises for desk workers" | "How to reduce churn with onboarding emails" |
| **Authority** | Showcase expertise, results, credentials | "Client transformation: 12 weeks" | "We hit $50K MRR — here's what worked" |
| **Connection** | Build trust through personality and story | "Why I became a trainer after burnout" | "The worst bug I shipped and what it taught me" |
| **Promotion** | Drive sales, signups, or conversions | "Spots open for 1:1 coaching" | "Try our free plan — no credit card needed" |
| **Community** | Engage and involve the audience | "What's your biggest gym struggle?" | "Poll: What feature should we build next?" |

**DEFAULT: 4 pillars** — Education, Authority, Connection, Promotion. Add Community only if the user's strategy relies on audience engagement.

---

## Common Posting Frequencies

| Schedule | Posts/Week | Best For | Monthly Total |
|----------|-----------|----------|---------------|
| Light | 3 | Solopreneurs with limited time, B2B LinkedIn-only | 12-13 |
| Standard | 5 | Most creators, coaches, consultants | 21-22 |
| Active | 7 | Full-time creators, brand accounts | 30 |
| Aggressive | 10-14 | Multi-platform creators, agencies | 42-60 |

**DEFAULT: 5 posts/week (Standard)** — covers weekdays, leaves weekends free for batch creation.

---

## Post Type Reference

| Post Type | Platform Fit | Engagement Level | Production Effort |
|-----------|-------------|-----------------|-------------------|
| Carousel | Instagram, LinkedIn | High | Medium |
| Reel/Short | Instagram, TikTok, YouTube Shorts | Very High | High |
| Story | Instagram, Facebook | Medium | Low |
| Text post | X/Twitter, LinkedIn | Medium | Low |
| Link post | LinkedIn, X/Twitter, Facebook | Low | Low |
| Thread | X/Twitter | High | Medium |
| Image post | Instagram, LinkedIn, Facebook | Medium | Medium |
| Newsletter | Email | High | High |
| Long-form video | YouTube | Very High | Very High |

---

## Core Workflow

EVERY CALENDAR STARTS WITH CONTENT PILLARS — NEVER GENERATE POST IDEAS WITHOUT ESTABLISHING PILLARS FIRST.

### Step 1: Understand

Gather these inputs from the user before generating anything:

1. **Business/niche** — what they do and who they serve
2. **Content pillars** — their 3-5 core topics (offer the framework table if they are unsure)
3. **Target platforms** — which platforms they post on
4. **Posting frequency** — how many posts per week (offer the frequency table if unsure)
5. **Audience** — who they are trying to reach (demographics, pain points, goals)
6. **Upcoming events** — product launches, sales, holidays, or milestones in the next 30 days
7. **Brand voice** — tone descriptors (professional, casual, witty, motivational, direct)

**If the user provides items 1-3, proceed with defaults for items 4-7.** Ask only about missing critical details.

**Brief template to present if the user gives a vague request:**

```
I'll build your 30-day content calendar. Quick answers needed:

1. What's your business/niche?
2. What 3-5 topics do you post about? (I can help you pick)
3. Which platforms? (e.g., Instagram, LinkedIn, X/Twitter)
4. How many posts per week? (default: 5)
5. Who's your audience?
6. Any launches, sales, or events in the next 30 days?
7. Brand voice? (default: professional but approachable)
```

**GATE: Do not proceed to Step 2 until you have at minimum: business/niche, platforms, and either user-provided or default-assigned content pillars.**

---

### Step 2: Generate

Build 30 days of content ideas mapped to pillars, platforms, post types, and dates.

1. **Assign pillar distribution** across the posting frequency:

   For 5 posts/week with 4 pillars, the default split is:
   - Education: 2x/week (40%)
   - Authority: 1x/week (20%)
   - Connection: 1x/week (20%)
   - Promotion: 1x/week (20%)

   Education always gets the highest share. Promotion never exceeds 25%.

2. **Map post types to platforms** — assign post types that match each platform's strengths:
   - Instagram: carousel (2x), reel (1x), image (1x), story (bonus)
   - LinkedIn: text post (2x), carousel (1x), link post (1x), image (1x)
   - X/Twitter: text post (2x), thread (1x), link post (1x), image (1x)

3. **Generate 30 days of post ideas** with these fields per entry:
   - Date (Day 1 through Day 30, starting from the user's preferred start date or next Monday)
   - Platform
   - Content Pillar
   - Post Type (carousel, reel, story, text, link, thread, image, newsletter, video)
   - Caption Idea (one sentence describing the post concept)
   - Status (default: "Idea")

4. **Weave in any upcoming events** the user mentioned — place promotional posts 3 days before, day-of, and 1 day after each event.

5. **Verify balance:**
   - Each pillar appears at least once per week
   - No more than 2 promotional posts in a row
   - Post types vary within each week (no 5 consecutive text posts)
   - Platform coverage matches the user's list

---

### Step 3: Present

Show the full calendar to the user for approval before creating anything in Notion or Canva.

1. **Present a summary table** showing the first 7 days in detail:

```
## 30-Day Content Calendar Preview (Week 1)

| Day | Date | Platform | Pillar | Post Type | Caption Idea |
|-----|------|----------|--------|-----------|--------------|
| Mon | Mar 3 | Instagram | Education | Carousel | 5 morning habits that boosted my energy |
| Tue | Mar 4 | LinkedIn | Authority | Text post | How I helped a client lose 30 lbs in 12 weeks |
| Wed | Mar 5 | Instagram | Connection | Reel | Behind the scenes: my meal prep routine |
| Thu | Mar 6 | LinkedIn | Education | Carousel | The #1 mistake people make with protein intake |
| Fri | Mar 7 | Instagram | Promotion | Image | Spring coaching spots are open — link in bio |

Remaining 23 days follow the same pillar rotation and post type variety.
Total posts: 22 (5/week for 4 weeks + 2 bonus)
Pillar split: Education 40% | Authority 20% | Connection 20% | Promotion 20%
```

2. **Ask for approval:**

```
Does this direction look right? I can:
- Swap any pillar assignments
- Change post types for specific days
- Add or remove platforms
- Adjust the posting frequency

Once approved, I'll create the full Notion database and Canva pillar templates.
```

**GATE: Do not proceed to Step 4 until the user approves the calendar direction.**

---

### Step 4: Act

Create the Notion database and Canva starter templates.

#### 4A: Create the Notion Database

1. **Search for existing workspace context** — call `notion-search` to check if the user has a content-related page or database already. If found, confirm whether to create the new database alongside it or independently.

2. **Create the database** — call `notion-create-database` with these properties:

   | Property | Type | Purpose |
   |----------|------|---------|
   | **Post Title** | Title | The caption idea or working title |
   | **Date** | Date | Scheduled publish date |
   | **Platform** | Select | Instagram, LinkedIn, X/Twitter, YouTube, TikTok, Newsletter, Podcast |
   | **Pillar** | Select | Education, Authority, Connection, Promotion, Community |
   | **Post Type** | Select | Carousel, Reel, Story, Text Post, Link Post, Thread, Image, Newsletter, Video |
   | **Status** | Select | Idea, Drafting, Ready, Scheduled, Published |
   | **Canva Link** | URL | Link to the Canva graphic template for this post |
   | **Notes** | Rich text | Additional context, hooks, references |

   Database title: `Content Calendar — [Month Year]` (e.g., "Content Calendar — March 2026")

3. **Populate the database** — call `notion-create-pages` to add all 30 days of content as individual entries. Each page gets:
   - Post Title set to the caption idea
   - Date set to the scheduled date
   - Platform, Pillar, Post Type, and Status filled from the generated calendar
   - Status defaults to "Idea" for all entries
   - Canva Link left empty (filled after Step 4B)

4. **Confirm the database:**

```
Notion database created: "Content Calendar — March 2026"

  30 posts added across 4 weeks
  Properties: Date, Platform, Pillar, Post Type, Status, Canva Link, Notes
  All entries set to "Idea" status

  Notion link: [database URL]
```

#### 4B: Create Canva Starter Templates

Generate one starter graphic template per content pillar so the user has a branded starting point for each category of post.

1. **Check for brand kit** — call `list-brand-kits` to load the user's brand colors, fonts, and logo

2. **Create a Canva folder** — call `create-folder` with the name: `Content Calendar — [Month Year]`

3. **Generate one template per pillar** — for each of the user's content pillars, call `generate-design` with a prompt tailored to that pillar's purpose:

   | Pillar | Template Prompt Direction | Dimensions |
   |--------|--------------------------|------------|
   | Education | Clean layout with numbered list or tip format, room for 3-5 bullet points | 1080 x 1080 |
   | Authority | Bold headline with space for a metric or testimonial quote | 1080 x 1080 |
   | Connection | Casual, story-style layout with space for a personal photo or behind-the-scenes feel | 1080 x 1080 |
   | Promotion | Eye-catching CTA-focused design with urgency element and link/button placeholder | 1080 x 1080 |
   | Community | Question-centered design with engagement prompt and poll/response space | 1080 x 1080 |

   Example generation prompt for an Education pillar template:
   ```
   Social media post template, square 1080x1080.
   Clean educational layout with a bold headline placeholder at top.
   Space for 3-5 numbered tips or bullet points in the body.
   Brand colors: [primary hex] background header, [secondary hex] accents.
   Footer area with small logo placement and handle.
   Modern, professional feel. Template style — text should look replaceable.
   ```

4. **Get thumbnail for each template** — call `get-design-thumbnail` for each generated design to verify quality

5. **Move all templates to the folder** — call `move-item-to-folder` for each template

6. **Update Notion entries with Canva links** — for posts matching each pillar, note the corresponding Canva template design link in the presentation to the user (bulk updating Notion page URLs is handled by informing the user which template maps to which pillar)

7. **Deliver the complete package:**

```
## Content Calendar Complete

### Notion Database
"Content Calendar — March 2026" — [Notion link]
- 22 posts across 30 days
- Platforms: Instagram, LinkedIn
- Pillars: Education (40%), Authority (20%), Connection (20%), Promotion (20%)
- All entries set to "Idea" — update status as you draft and schedule

### Canva Pillar Templates
Folder: "Content Calendar — March 2026" — [Canva folder]

  Education template  — dsg_edu123  [thumbnail]
  Authority template  — dsg_auth456 [thumbnail]
  Connection template — dsg_conn789 [thumbnail]
  Promotion template  — dsg_promo012 [thumbnail]

Each template matches your brand kit. Duplicate a template in Canva
when creating a new post, then paste the design link into the
"Canva Link" property on the matching Notion entry.

### Suggested Workflow
1. Each week, open the Notion database and filter by the current week
2. Write captions and hooks for each post (update status to "Drafting")
3. Duplicate the matching Canva pillar template and customize the graphic
4. Paste the Canva link into the Notion entry
5. Schedule in your platform's scheduler (update status to "Scheduled")
6. After publishing, mark as "Published"
```

---

## Example 1: Fitness Coach — Instagram + LinkedIn, 5 Posts/Week

**User says:** "I'm a fitness coach specializing in strength training for busy professionals. I post on Instagram and LinkedIn. I want 5 posts a week. I have a 6-week challenge launching on the 15th."

**Step 1 — Understand:**
- Business: Fitness coaching, strength training for busy professionals
- Pillars: Education (training tips), Authority (client results), Connection (personal story), Promotion (coaching offers)
- Platforms: Instagram, LinkedIn
- Frequency: 5/week (Standard)
- Audience: Professionals aged 28-45 with limited gym time
- Upcoming event: 6-week challenge launch on the 15th
- Voice: Motivational, direct, no fluff

**Step 2 — Generate (Week 1 sample):**

| Day | Platform | Pillar | Post Type | Caption Idea |
|-----|----------|--------|-----------|--------------|
| Mon | Instagram | Education | Carousel | 5 compound exercises that replace a 60-min gym session |
| Tue | LinkedIn | Authority | Text post | My client dropped 4% body fat in 8 weeks training 3x/week — here is exactly what we did |
| Wed | Instagram | Connection | Reel | What my 5 AM workout routine actually looks like (unfiltered) |
| Thu | LinkedIn | Education | Carousel | The minimum effective dose for strength: how little you can train and still grow |
| Fri | Instagram | Promotion | Image | 6-week strength challenge starts the 15th — 12 spots left |

**Step 3 — Present:** Full 30-day table shown. Promotional posts cluster around the 12th, 15th, and 16th for the challenge launch. User approves with one swap: move Wednesday's reel to Thursday and Thursday's carousel to Wednesday.

**Step 4 — Act:**
- Notion database created: "Content Calendar — March 2026" with 22 posts
- Canva folder created: "Content Calendar — March 2026"
- 4 pillar templates generated (Education: numbered tips layout, Authority: bold stat + quote layout, Connection: casual behind-the-scenes layout, Promotion: CTA-heavy launch design)
- All templates moved to folder, thumbnails verified

---

## Example 2: SaaS Founder — X/Twitter + LinkedIn, 3 Posts/Week

**User says:** "I run a SaaS tool for email deliverability. My audience is email marketers and startup founders. I want to post on X and LinkedIn, 3 times a week. Keep it professional but not boring."

**Step 1 — Understand:**
- Business: Email deliverability SaaS
- Pillars: Education (deliverability tips), Authority (product metrics and wins), Promotion (free trial, demos)
- Platforms: X/Twitter, LinkedIn
- Frequency: 3/week (Light)
- Audience: Email marketers, startup founders, growth teams
- Upcoming events: None mentioned
- Voice: Professional but not boring — confident, slightly witty

**Step 2 — Generate (Week 1 sample):**

| Day | Platform | Pillar | Post Type | Caption Idea |
|-----|----------|--------|-----------|--------------|
| Mon | X/Twitter | Education | Thread | Your emails are landing in spam because of these 5 DNS mistakes — here is how to fix each one |
| Wed | LinkedIn | Authority | Text post | We scanned 2M emails last month and found 73% of deliverability issues come from 3 fixable problems |
| Fri | X/Twitter | Promotion | Text post | We built a free deliverability audit tool — paste your domain and get a score in 30 seconds |

**Step 3 — Present:** Full 30-day table shown. 13 posts total (3/week for 4 weeks + 1 bonus). Pillar split: Education 46%, Authority 31%, Promotion 23%. User approves as-is.

**Step 4 — Act:**
- Notion database created: "Content Calendar — March 2026" with 13 posts
- Canva folder created: "Content Calendar — March 2026"
- 3 pillar templates generated (Education: clean tip-style with code/technical feel, Authority: data-forward layout with large stat placeholder, Promotion: CTA-centered with product screenshot space)
- All templates moved to folder, thumbnails verified

---

## Recovery and Troubleshooting

### Notion Database Creation Fails

1. Call `notion-search` to verify workspace access — if no results return, the user may not have connected their Notion workspace
2. Inform the user: "I cannot access your Notion workspace. Please make sure the Notion integration is connected."
3. **Fallback:** Generate the full 30-day calendar as a markdown table and save it to a local file at the user's preferred path. The user can import it into Notion manually.

### Notion Page Creation Fails Partway

1. Note which entries were successfully created and which failed
2. Retry the failed batch once (reduce batch size if the original was large)
3. If retry fails, list the remaining entries as a markdown table and inform the user: "15 of 22 posts were added to Notion. Here are the remaining 7 — you can add them manually or I can retry."

### Canva Design Generation Fails

1. Simplify the template prompt — remove detailed layout instructions, keep to colors + style + purpose
2. Retry once with the simplified prompt
3. **If 2 attempts fail for a pillar template:** Skip that template and inform the user: "I could not generate the Authority template. The other 3 templates are ready. You can create the Authority template manually in Canva using these brand specs: [colors, fonts, dimensions]."
4. **If all template generation fails:** Inform the user that Canva generation is unavailable. Deliver the Notion database without Canva links. Provide the template specs (dimensions, colors, layout descriptions) so they can create templates manually.

### Brand Kit Not Found in Canva

1. Inform the user: "No brand kit found in your Canva account."
2. Ask for: primary color (hex), secondary color (hex), font preference (serif/sans-serif)
3. Proceed with manual color and font values in the generation prompts
4. Suggest: "Create a brand kit in Canva to speed up future template generation."

### User Has No Content Pillars

1. Present the Content Pillar Framework table from this skill
2. Recommend the default 4 (Education, Authority, Connection, Promotion)
3. Ask: "Which of these fit your business? Or tell me 3-5 topics you already post about and I will map them to pillars."
4. **Do not proceed without at least 3 defined pillars.**

### Calendar Feels Repetitive

If the user reviews the 30-day plan and says it feels repetitive:
1. Check if any single post type appears more than 3 times in one week — swap one for a different type
2. Vary the caption angles within the same pillar (problem-focused, story-focused, data-focused, how-to)
3. Alternate platforms day by day instead of clustering the same platform on consecutive days
4. Regenerate the flagged week(s) only — do not rebuild the entire calendar

---

## Anti-Patterns

- **DO NOT** generate post ideas without establishing content pillars first — random ideas do not batch or compound
- **DO NOT** schedule more than 25% promotional content — audiences disengage when every post is a sales pitch
- **DO NOT** assign the same post type to the same platform 3+ days in a row — variety drives reach
- **DO NOT** create Canva templates before the user approves the calendar — templates depend on confirmed pillars
- **DO NOT** leave the Canva Link property empty without telling the user how to fill it — always explain the template-to-post workflow
- **DO NOT** assume posting days — ask the user or default to weekdays (Mon-Fri)
- **DO NOT** front-load promotional posts in week 1 — warm the audience with education and connection content first
