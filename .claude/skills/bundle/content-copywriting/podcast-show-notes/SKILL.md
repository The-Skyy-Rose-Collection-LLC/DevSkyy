---
name: podcast-show-notes
description: "Transforms podcast or video transcripts into structured show notes with timestamps, key takeaways, resource links, guest bios, pull quotes, and SEO-optimized episode descriptions. Use when a user has a transcript or recording summary and needs polished show notes for their podcast episode page."
allowed-tools: Read Write Glob Grep
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Podcast Show Notes

## When to Use This Skill

Use this skill when you need to:
- Turn a raw podcast or video transcript into publish-ready show notes
- Generate timestamps, key takeaways, and pull quotes from a recorded conversation
- Write an SEO-optimized episode description for Apple Podcasts, Spotify, or YouTube
- Extract guest bios and resource links mentioned during an episode

**DO NOT** use this skill for:
- Writing a podcast script before recording (use a video-script skill instead)
- Editing raw transcripts for readability (this produces show notes, not cleaned transcripts)
- Creating social media clips or promo assets from episodes (use a content-repurpose skill)

---

## How It Works

EVERY SET OF SHOW NOTES MUST BE DERIVED FROM THE ACTUAL TRANSCRIPT -- NEVER INVENT TIMESTAMPS, QUOTES, OR CLAIMS NOT IN THE SOURCE MATERIAL.

---

### Step 1: Understand -- Read and Analyze the Transcript

1. **Get the transcript.** Accept file paths (`.txt`, `.md`, `.srt`, `.vtt`), pasted text, or recording notes. Read files with `Read` or `Glob`.
2. **Ask for episode context** if not provided: episode number, series name, guest name and title, target audience, specific links to include.
3. **Identify core elements:** episode topic, guest identity, 3-5 key themes, episode format (interview, solo, panel).
4. **Present the overview for confirmation:**

```
## Episode Overview

**Format:** Interview
**Topic:** How to build a referral engine without paid ads
**Guest:** Sarah Chen, founder of GrowthLoop
**Key Themes:**
1. Why referrals outperform cold outreach
2. The 3-email referral ask sequence
3. Building referral incentives that feel genuine
4. Low-tech referral tracking

Ready to extract timestamps and show notes. Proceed?
```

**GATE: Do not proceed until the user confirms the episode overview is accurate.**

---

### Step 2: Extract -- Pull Structured Data from the Transcript

#### Timestamps
- Use existing time codes from SRT/VTT/inline timestamps when available
- If no timestamps exist, estimate from word count at 150 words per minute and mark as `[approx]`
- Format: `[MM:SS]` under 1 hour, `[HH:MM:SS]` over 1 hour
- Mark: intro, each major topic shift, notable stories/tangents, closing/CTA

#### Key Takeaways (3-7)
- Each must be a complete, standalone, actionable statement
- Represent distinct insights from the episode (no duplicates)

#### Pull Quotes (2-4)
- Exact words from the transcript -- never paraphrased
- Under 280 characters (shareable on social media)
- Attributed to the correct speaker

#### Resources Mentioned
- Name exactly as stated; add URL if well-known or stated in transcript
- Mark unknown URLs as `[URL needed]`

#### Guest Bio (interview episodes only)
- 2-3 sentences from what was said in the episode
- Include name, role, one credential, and where to find them
- **NEVER fabricate credentials or social handles.** Flag gaps as `[confirm with guest]`.

---

### Step 3: Present -- Draft Show Notes for Approval

Assemble into this template and present for review:

```markdown
# [Episode Number]: [Episode Title]

## Guest
**[Guest Name]** -- [Title, Company]
[2-3 sentence bio]

## Episode Summary
[2-3 sentences: what this covers, who it is for, core promise to the listener]

## Timestamps
- [00:00] Introduction and guest welcome
- [02:15] [Topic description]
- [08:42] [Topic description]
- [15:30] [Topic description]

## Key Takeaways
1. [Actionable takeaway]
2. [Actionable takeaway]
3. [Actionable takeaway]

## Pull Quotes
> "[Direct quote]" -- [Speaker Name]

## Resources Mentioned
- [Resource Name](URL) -- brief description
- [Resource Name] [URL needed] -- brief description

## SEO Episode Description
[150-250 words optimized for podcast directories. Includes topic, guest name,
3-5 searchable keywords, and a call to action.]
```

Ask: "Are timestamps accurate? Any takeaways to add or cut? Pull quotes correct? Missing resources? Guest bio need changes? SEO description good?"

**GATE: Do not write the final file until the user approves or revisions are applied.**

---

### Step 4: Deliver -- Write Final Show Notes to File

1. **Ask for the output path** if not specified. Default: `show-notes/ep-[number]-[slug].md`
2. **Write the file** with `Write`.
3. **Confirm delivery:**

```
Show notes written to: show-notes/ep-042-referral-engine.md

Contents:
  - Guest bio, episode summary
  - 7 timestamps, 5 takeaways, 2 pull quotes
  - 4 resources (1 needs URL)
  - SEO description (187 words)

Next steps:
  - Add any missing URLs
  - Copy SEO description to your podcast hosting platform
  - Use pull quotes for social media promotion
```

---

## Common Patterns

| Transcript Type | Adjustment |
|----------------|------------|
| SRT/VTT subtitle file | Reconstruct full sentences; use provided timestamps directly |
| Otter.ai / Descript export | Map speaker labels to names; use inline timestamps |
| Manual notes (no transcript) | Mark timestamps as `[timestamp needed]`; work from notes |
| Raw unedited transcript | Ignore filler words; extract clean quotes; flag unclear sections |
| Solo episode | Skip guest bio; focus on timestamps and takeaways |
| Panel / multi-guest | List all guests with bios; attribute quotes carefully |

---

## Example 1: Interview Episode with a Marketing Expert

**User says:** "Here is the transcript for episode 42 of The Growth Lab. I interviewed Sarah Chen from GrowthLoop about referral engines. File is at transcripts/ep42.txt."

**Step 1:** Read the file. Present overview identifying interview format, guest as Sarah Chen (Founder, GrowthLoop), and 4 key themes about referral strategies. Get confirmation.

**Step 3 delivery (excerpt):**

```markdown
# Episode 42: Building a Referral Engine That Replaces Paid Ads

## Guest
**Sarah Chen** -- Founder & CEO, GrowthLoop
Sarah scaled her consulting practice to $500K/year entirely through referrals
and has helped 200+ service businesses systematize their referral process.

## Timestamps
- [00:00] Welcome and Sarah's backstory
- [03:12] Why referrals beat paid acquisition for service businesses
- [09:45] The 3-email referral ask sequence (full breakdown)
- [18:20] Incentive structures that do not feel transactional
- [25:08] Low-tech tracking: spreadsheets vs. CRM tags
- [32:15] Biggest referral program mistakes
- [38:40] Lightning round and where to find Sarah

## Key Takeaways
1. Ask for referrals within 48 hours of delivering a result -- enthusiasm peaks
   right after a win.
2. The "warm intro" email outperforms referral links because it gives the
   referrer control.
3. Non-monetary incentives outperform cash rewards for high-value B2B referrals.

## Pull Quotes
> "Stop asking 'Do you know anyone who needs this?' Start asking 'Who had the
> same problem you had six months ago?'" -- Sarah Chen
```

**Step 4:** Write to `show-notes/ep-042-referral-engine.md` after approval.

---

## Example 2: Solo Episode on Business Systems

**User says:** "I just recorded a solo episode about the 5 systems every solopreneur needs. No guest. Transcript is pasted below."

**Step 1:** Identify solo format, 5 key themes (lead capture, onboarding, content production, financial tracking, weekly review). Confirm with user.

**Step 3 delivery (excerpt):**

```markdown
# Episode 58: 5 Systems Every Solopreneur Needs to Stop Working in Chaos

## Episode Summary
Running a one-person business without systems means you are the bottleneck for
everything. This episode covers 5 core systems and how to build each in under
a day using free tools.

## Timestamps
- [00:00] Why solopreneurs drown without systems
- [02:30] System 1: Lead capture
- [08:15] System 2: Client onboarding
- [14:40] System 3: Content production
- [21:05] System 4: Financial tracking
- [26:50] System 5: Weekly review
- [32:10] How to pick which system to build first

## Key Takeaways
1. Build lead capture first -- no revenue happens without leads entering your
   pipeline consistently.
2. Batch content production into one day per week. Daily creation kills deep work.
3. The weekly review keeps all other systems running. Skip it and everything
   degrades within two weeks.

## Pull Quotes
> "If your onboarding process lives in your head, you do not have a process.
> You have a memory and memories fail." -- Host
```

**Step 4:** Write to `show-notes/ep-058-solopreneur-systems.md` after approval.

---

## Recovery

**Transcript is too messy or incoherent:**
1. Extract from legible sections, flag problematic areas with approximate timestamps
2. Ask the user to clarify unclear sections from memory
3. If more than 50% is unusable: "This transcript needs cleanup first. Run it through Descript or Otter.ai for a cleaner version."

**No timestamps in the transcript:**
1. Estimate from word count at 150 words per minute
2. Mark all timestamps as `[approx]` so the user verifies against their recording
3. Or leave as `[timestamp needed]` for the user to fill in

**Guest information is missing or vague:**
1. Draft what you can from the transcript
2. Flag gaps: "Guest bio incomplete -- missing [company / title / website]. Please confirm with your guest."
3. **NEVER fabricate credentials, titles, or social handles**

**User wants a platform-specific format:**
1. Ask for the platform (WordPress, Buzzsprout, Transistor, etc.)
2. Request a sample of their existing show notes and match that structure
3. Adapt the markdown template to fit (HTML, shortcodes, platform fields)

**If 3 attempts to clarify requirements fail:**
Stop and provide a blank template the user can fill in manually:

```
# Episode [Number]: [Title]
## Guest: [Name] -- [Title, Company]
## Summary: [2-3 sentences]
## Timestamps: [Fill in from your recording]
## Takeaways: [3-7 bullet points]
## Resources: [List with links]
## Pull Quotes: [2-4 direct quotes]
## SEO Description: [150-250 words]
```
