---
name: social-media-graphics
description: "Generates coordinated multi-platform social media graphics from a single creative brief using Canva. Use when a user needs consistent branded visuals across Instagram, Facebook, X/Twitter, LinkedIn, or Pinterest from one design concept."
allowed-tools: Read Write Glob mcp__claude_ai_Canva__generate-design mcp__claude_ai_Canva__generate-design-structured mcp__claude_ai_Canva__resize-design mcp__claude_ai_Canva__export-design mcp__claude_ai_Canva__get-export-formats mcp__claude_ai_Canva__list-brand-kits mcp__claude_ai_Canva__create-folder mcp__claude_ai_Canva__move-item-to-folder mcp__claude_ai_Canva__get-design-thumbnail
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Social Media Graphics

## When to Use This Skill

Use this skill when you need to:
- Create branded social media graphics for a product launch, promotion, or announcement
- Generate a coordinated visual set across 2-6 platforms from one brief
- Produce quote graphics, event promotions, or content teasers with consistent branding
- Resize a hero design into platform-specific dimensions without manually recreating each one

**DO NOT** use this skill for:
- Video editing or animation (Canva design generation produces static images)
- Print materials like business cards or flyers (different workflow)
- Logo design or full brand identity creation

---

## Quick Reference: Platform Dimensions

| Platform | Format | Width | Height | Aspect Ratio | Use Case |
|----------|--------|-------|--------|--------------|----------|
| Instagram | Post | 1080 | 1080 | 1:1 | Feed posts, carousels |
| Instagram | Story | 1080 | 1920 | 9:16 | Stories, Reels cover |
| Facebook | Post | 1200 | 630 | 1.91:1 | Feed posts, link shares |
| X/Twitter | Post | 1600 | 900 | 16:9 | Timeline images |
| LinkedIn | Post | 1200 | 627 | 1.91:1 | Feed posts, articles |
| Pinterest | Pin | 1000 | 1500 | 2:3 | Standard pins |

## Quick Reference: Export Formats

| Format | Best For | File Size | Quality |
|--------|----------|-----------|---------|
| PNG | Graphics with text, logos, transparency | Larger | Lossless |
| JPG | Photos, gradients, complex imagery | Smaller | Lossy |
| PDF | Print-ready or archival copies | Varies | Vector-capable |

**DEFAULT EXPORT FORMAT: PNG** — best balance of quality and compatibility for social media graphics. Use JPG only when file size is a hard constraint.

---

## Core Workflow

EVERY GRAPHIC SET STARTS WITH ONE HERO DESIGN THAT GETS RESIZED — NEVER CREATE EACH PLATFORM VARIANT FROM SCRATCH.

### Step 1: Gather the Creative Brief

Collect these details from the user before generating anything:

1. **Topic/occasion** — what is the graphic about (product launch, sale, quote, event, content teaser)
2. **Key message** — the primary text that appears on the graphic (headline, quote, or announcement)
3. **Call to action** — what the viewer should do (visit link, sign up, shop now, swipe, comment)
4. **Target platforms** — which platforms need graphics (default: Instagram Post + Facebook + X/Twitter + LinkedIn)
5. **Brand kit preference** — use existing Canva brand kit or specify colors/fonts manually
6. **Visual style notes** — any preferences for mood, imagery, or layout (minimal, bold, photo-heavy, illustrated)

If the user provides a brief that covers items 1-3, proceed with defaults for items 4-6. Ask only about missing critical details.

**Brief template to present if the user gives a vague request:**

```
I'll generate your graphics. Quick answers needed:

1. What's the graphic about?
2. What text should appear on it?
3. What should viewers do? (CTA)
4. Which platforms? (default: Instagram, Facebook, X/Twitter, LinkedIn)
5. Use your Canva brand kit? (Y/N)
6. Any visual style preference? (default: clean and modern)
```

### Step 2: Load Brand Kit from Canva

1. Call `list-brand-kits` to retrieve available brand kits
2. Present the brand kit names to the user if multiple exist
3. Select the matching brand kit (or use the only one available)
4. Note the brand colors, fonts, and logo references for the generation prompt

```
Brand kit loaded: "Acme Co"
- Primary: #2D5BFF
- Secondary: #FF6B35
- Font: Montserrat Bold / Open Sans Regular
- Logo: Available
```

**IF NO BRAND KIT EXISTS:**
- Ask the user for primary color, secondary color, and preferred font style
- Proceed without brand kit — include color hex codes and font preferences directly in the generation prompt
- Inform the user they can create a brand kit in Canva for future consistency

### Step 3: Generate the Hero Design

The hero design is the main visual concept at the largest or most versatile dimension. **Default hero platform: Instagram Post (1080x1080)** because square crops cleanly to most other formats.

1. Build the generation prompt incorporating:
   - The key message and CTA text
   - Brand colors, fonts, and style from Step 2
   - The user's visual style notes
   - Square (1:1) composition that keeps text and focal elements centered

2. Call `generate-design` with the composed prompt

3. Call `get-design-thumbnail` to preview the hero design

4. Present the thumbnail to the user:

```
Hero design generated: "Summer Sale Launch"
Design ID: dsg_abc123xyz
Preview: [thumbnail displayed]

Does this look good, or would you like adjustments before I resize for all platforms?
```

5. **Wait for user approval** before proceeding to resizing

**IF THE HERO DESIGN MISSES THE MARK:**
- Ask what specific element needs changing (layout, colors, text placement, imagery)
- Regenerate with an adjusted prompt — do not try to fix more than 2 rounds
- If 2 regenerations still miss, ask the user to describe what they see in their head or provide a reference image URL

### Step 4: Resize for Each Target Platform

Once the hero design is approved, resize it for every platform in the brief.

1. For each target platform, call `resize-design` with the hero design ID and target dimensions:

| Target | Resize To | Watch For |
|--------|-----------|-----------|
| Instagram Post | 1080 x 1080 | Already the hero — skip if hero is IG Post |
| Instagram Story | 1080 x 1920 | Tall format — text may need vertical reflow |
| Facebook Post | 1200 x 630 | Wide crop — ensure headline is not cut off |
| X/Twitter Post | 1600 x 900 | Wide crop — similar to Facebook, check text |
| LinkedIn Post | 1200 x 627 | Nearly identical to Facebook dimensions |
| Pinterest Pin | 1000 x 1500 | Tall format — CTA should be in lower third |

2. After each resize, call `get-design-thumbnail` to verify the result

3. **CHECK EVERY RESIZED VARIANT** for these issues:
   - Text cut off at edges
   - Logo cropped or too small to read
   - Key visual elements shifted out of frame
   - CTA not visible

4. Report results to the user:

```
Resized variants generated:

  Instagram Post (1080x1080) — dsg_abc123xyz (hero)
  Facebook Post (1200x630)   — dsg_fb456def
  X/Twitter (1600x900)       — dsg_tw789ghi
  LinkedIn (1200x627)        — dsg_li012jkl

All variants checked. Text and CTA visible on all platforms.
```

**IF A RESIZE CROPS BADLY:**
- Call `generate-design` for that specific platform dimension instead of resizing
- Use the same prompt as the hero but specify the target dimensions
- This creates a native layout for that format rather than forcing a crop

### Step 5: Export All Variants

1. Call `get-export-formats` to confirm available formats

2. Export each design variant as PNG (default) or the user's preferred format:
   - Call `export-design` for each design ID with format `png`
   - Collect the export download URLs

3. Present the export summary:

```
Exports complete:

  instagram-post-summer-sale.png    — [export URL]
  facebook-post-summer-sale.png     — [export URL]
  twitter-post-summer-sale.png      — [export URL]
  linkedin-post-summer-sale.png     — [export URL]

Format: PNG (lossless)
All files ready for download.
```

**FILE NAMING CONVENTION:** `{platform}-{format}-{brief-topic}.{ext}`
- All lowercase, hyphens only, no spaces
- Examples: `instagram-post-summer-sale.png`, `pinterest-pin-weekly-quote.png`

### Step 6: Organize in Canva Folder

1. Call `create-folder` with a descriptive name: `{Topic} - Social Graphics`

2. Call `move-item-to-folder` for each design variant to place it in the new folder

3. Confirm organization:

```
All designs organized in Canva folder: "Summer Sale - Social Graphics"

Contents:
  - Hero: Instagram Post (1080x1080)
  - Facebook Post (1200x630)
  - X/Twitter Post (1600x900)
  - LinkedIn Post (1200x627)

Folder is accessible in your Canva account.
```

---

## Example 1: Product Launch Announcement

**User brief:** "I'm launching a new online course called 'Email Mastery' next Monday. Need graphics for Instagram, Facebook, X/Twitter, and LinkedIn. My brand colors are navy and gold. Headline: 'Email Mastery is Here.' CTA: 'Enroll now at emailmastery.com'"

**Step-by-step execution:**

1. **Brief gathered:**
   - Topic: Online course launch
   - Key message: "Email Mastery is Here"
   - CTA: "Enroll now at emailmastery.com"
   - Platforms: Instagram Post, Facebook, X/Twitter, LinkedIn
   - Brand: Navy (#1B2A4A) and gold (#D4A843)
   - Style: Professional, clean

2. **Brand kit:** Call `list-brand-kits`. Result: user has "Creator Brand" kit with matching navy and gold. Load it.

3. **Hero design:** Call `generate-design` with prompt:
   ```
   Professional course launch announcement graphic, square 1080x1080.
   Headline text: "Email Mastery is Here" in bold centered text.
   Subtext: "Enroll now at emailmastery.com" below headline.
   Color palette: navy (#1B2A4A) background, gold (#D4A843) accent text.
   Clean modern layout with generous whitespace.
   Email/envelope icon motif. No stock photos.
   ```
   Preview thumbnail shown. User approves.

4. **Resize:**
   - Facebook 1200x630 — headline visible, CTA readable
   - X/Twitter 1600x900 — wide format works, text centered
   - LinkedIn 1200x627 — similar to Facebook, verified clean

5. **Export:** All 4 variants exported as PNG.
   ```
   instagram-post-email-mastery-launch.png
   facebook-post-email-mastery-launch.png
   twitter-post-email-mastery-launch.png
   linkedin-post-email-mastery-launch.png
   ```

6. **Organize:** Folder created: "Email Mastery Launch - Social Graphics". All 4 designs moved in.

**Delivered to user:**
```
Your "Email Mastery" launch graphics are ready across 4 platforms:

  Instagram Post (1080x1080) — square feed post
  Facebook Post (1200x630)   — landscape feed/link share
  X/Twitter (1600x900)       — timeline image
  LinkedIn (1200x627)        — feed post

All organized in your Canva folder: "Email Mastery Launch - Social Graphics"

Export URLs:
  - instagram-post-email-mastery-launch.png — [URL]
  - facebook-post-email-mastery-launch.png  — [URL]
  - twitter-post-email-mastery-launch.png   — [URL]
  - linkedin-post-email-mastery-launch.png  — [URL]

Brand kit "Creator Brand" applied. Navy background, gold accents throughout.
```

---

## Example 2: Weekly Quote Post

**User brief:** "I share a weekly motivational quote on Instagram, Pinterest, and LinkedIn. This week's quote: 'The best time to start was yesterday. The second best time is now.' Attribute to unknown. Keep it minimal."

**Step-by-step execution:**

1. **Brief gathered:**
   - Topic: Weekly motivational quote
   - Key message: "The best time to start was yesterday. The second best time is now."
   - CTA: None explicit — default to subtle branding/handle
   - Platforms: Instagram Post, Pinterest Pin, LinkedIn Post
   - Brand: Check for existing brand kit
   - Style: Minimal

2. **Brand kit:** Call `list-brand-kits`. Result: "Minimal Creator" kit found with off-white (#F5F0EB), charcoal (#2C2C2C), serif font. Load it.

3. **Hero design:** Call `generate-design` with prompt:
   ```
   Minimal motivational quote graphic, square 1080x1080.
   Quote text: "The best time to start was yesterday. The second best time is now."
   Attribution: "— Unknown" below quote in smaller text.
   Off-white (#F5F0EB) background, charcoal (#2C2C2C) text.
   Serif font. Centered layout. Generous margins.
   No imagery — typography only. Subtle thin border accent.
   ```
   Preview shown. User approves.

4. **Resize:**
   - Pinterest Pin 1000x1500 — tall format, quote repositioned to upper third, verified readable
   - LinkedIn Post 1200x627 — wide crop, quote stays centered, attribution visible

5. **Export:** All 3 variants exported as PNG.
   ```
   instagram-post-weekly-quote.png
   pinterest-pin-weekly-quote.png
   linkedin-post-weekly-quote.png
   ```

6. **Organize:** Folder created: "Weekly Quote - Social Graphics". All 3 designs moved in.

**Delivered to user:**
```
Your weekly quote graphics are ready:

  Instagram Post (1080x1080) — square feed post
  Pinterest Pin (1000x1500)  — standard pin
  LinkedIn Post (1200x627)   — feed post

All organized in your Canva folder: "Weekly Quote - Social Graphics"

Export URLs:
  - instagram-post-weekly-quote.png  — [URL]
  - pinterest-pin-weekly-quote.png   — [URL]
  - linkedin-post-weekly-quote.png   — [URL]

"Minimal Creator" brand kit applied. Off-white background, charcoal serif text.
```

---

## Pre-Delivery Checklist

Run this checklist before delivering any graphic set to the user. **DO NOT SKIP ANY ITEM.**

| Check | What to Verify | How |
|-------|----------------|-----|
| Brand colors match | Colors in design match brand kit or user-specified hex values | Visual check on thumbnail |
| Text readable at mobile size | Headline text is large enough to read on a phone screen | Thumbnail at small preview — if text is illegible, regenerate with larger font |
| CTA visible | Call to action text is not obscured, cropped, or lost in background | Check each variant thumbnail |
| No cut-off text | All text stays within safe margins on every platform variant | Review each resized thumbnail — text within center 80% of canvas |
| Logo placement | Logo/watermark (if included) is visible but not dominant | Check all variants for consistent placement |
| Consistent style | All variants look like they belong to the same campaign | Compare thumbnails side by side |
| File naming | Files follow `{platform}-{format}-{topic}.{ext}` convention | Verify before export |
| Folder organized | All designs live in one labeled Canva folder | Confirm after move-to-folder calls |
| User approved hero | Hero design was shown and approved before resizing | Must happen at Step 3 |
| Export format correct | PNG default, or user-requested format confirmed | Verify format in export call |

```
Pre-Delivery Checklist:
  [x] Brand colors match kit/specs
  [x] Text readable at mobile size
  [x] CTA visible on all variants
  [x] No cut-off text on any platform
  [x] Logo placement consistent
  [x] Visual style consistent across set
  [x] File naming convention applied
  [x] Canva folder organized
  [x] Hero design approved by user
  [x] Export format confirmed (PNG)
```

---

## Recovery and Troubleshooting

### Brand Kit Not Found

If `list-brand-kits` returns empty or the user's kit name doesn't match:

1. Inform the user: "No brand kits found in your Canva account."
2. Ask for manual brand details:
   - Primary color (hex code or name)
   - Secondary color (hex code or name)
   - Font preference (serif, sans-serif, bold, light)
3. Proceed with manual values embedded in the generation prompt
4. Suggest: "You can create a brand kit in Canva to speed up future graphic generation."

### Resize Crops Text or Key Elements

If a resized variant cuts off the headline, CTA, or focal element:

1. Do not deliver the cropped version
2. Call `generate-design` directly for that platform dimension using the same creative brief
3. Adjust the prompt to specify text placement for that aspect ratio:
   - Wide formats (Facebook, X/Twitter, LinkedIn): "Center text horizontally, keep in middle third vertically"
   - Tall formats (Story, Pinterest): "Place headline in upper third, CTA in lower third"
4. Verify the regenerated variant with `get-design-thumbnail`

### Design Generation Fails

If `generate-design` returns an error:

1. Simplify the prompt — remove complex layout instructions, keep to headline + colors + style
2. Retry once with the simplified prompt
3. If it fails again, try `generate-design-structured` as an alternative
4. **If 3 attempts fail, stop and inform the user:** "Canva design generation is unavailable right now. Please try again in a few minutes or create the design manually in Canva using these specs: [provide dimensions, colors, text]."

### Export Fails

If `export-design` returns an error:

1. Verify the design ID is correct by calling `get-design-thumbnail`
2. Try exporting as JPG instead of PNG
3. If both fail, provide the design IDs and Canva folder name so the user can export manually from their Canva account

### User Wants a Platform Not Listed

If the user requests dimensions not in the quick reference table:

1. Ask for the exact width and height in pixels
2. Use those dimensions in the resize or generation call
3. Apply the same hero-first workflow — resize from the hero, check for cropping
4. Common unlisted formats:
   - YouTube Thumbnail: 1280 x 720
   - TikTok Cover: 1080 x 1920 (same as Instagram Story)
   - Email Header: 600 x 200
   - Etsy Shop Banner: 3360 x 840

---

## Anti-Patterns

- **DO NOT** generate each platform variant from scratch — always start with one hero design and resize
- **DO NOT** export before the user approves the hero design
- **DO NOT** use JPG as the default export — always default to PNG for social graphics
- **DO NOT** skip the thumbnail preview check on resized variants
- **DO NOT** leave designs scattered — always organize into a Canva folder
- **DO NOT** guess brand colors — either load the brand kit or ask the user explicitly
- **DO NOT** overcrowd the design with text — social graphics need a clear visual hierarchy with one headline and one CTA maximum
