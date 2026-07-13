---
name: youtube-thumbnail
description: "Generates three YouTube thumbnail options optimized for click-through rate using Canva, applying high-contrast colors, emotional expressions, and concise text overlays. Use when a user needs a thumbnail for a YouTube video, wants to A/B test thumbnail designs, or needs click-optimized visual assets at 1280x720."
allowed-tools: Read Write Glob mcp__claude_ai_Canva__generate-design mcp__claude_ai_Canva__list-brand-kits mcp__claude_ai_Canva__export-design mcp__claude_ai_Canva__get-export-formats mcp__claude_ai_Canva__get-design-thumbnail mcp__claude_ai_Canva__start-editing-transaction mcp__claude_ai_Canva__perform-editing-operations mcp__claude_ai_Canva__commit-editing-transaction mcp__claude_ai_Canva__cancel-editing-transaction
metadata:
  author: matthewhitcham
  version: "1.0"
---

# YouTube Thumbnail Generator

3 CTR-optimized options per video. 1280x720 JPG export. High-contrast colors, emotional faces, 3 words max. User picks one, refine, deliver.

## When to Use This Skill

Use this skill when you need to:
- Create a click-optimized YouTube thumbnail for an upcoming or published video
- Generate 3 distinct thumbnail concepts to A/B test or pick from
- Apply CTR best practices (contrast, emotion, minimal text) to a thumbnail design
- Refresh an underperforming video's thumbnail with a higher-CTR alternative

**DO NOT** use this skill for:
- YouTube channel art or banners (different dimensions and goals)
- Video editing, intros, or end screens
- Social media graphics for non-YouTube platforms (use social-media-graphics instead)

---

## Quick Reference: Thumbnail Specifications

| Spec | Value | Why It Matters |
|------|-------|----------------|
| **Dimensions** | 1280 x 720 px | YouTube required minimum; 16:9 aspect ratio |
| **Max file size** | 2 MB | YouTube upload limit |
| **Format** | JPG | Smallest file size at high quality; YouTube standard |
| **Text overlay** | **3 WORDS MAXIMUM** | Must be readable at 168x94 (mobile suggested video) |
| **Font size** | Fills 30-40% of thumbnail width | Legibility at all screen sizes |
| **Safe zone** | Key elements in center 80% | Edges get cropped on some devices |
| **Color contrast** | Minimum 4.5:1 text-to-background | Visibility on white and dark YouTube backgrounds |
| **Faces** | Visible, emotional, eye contact | Faces with strong emotion lift CTR 30-40% on average |

## Quick Reference: CTR Best Practices

| Practice | Impact | Implementation |
|----------|--------|----------------|
| High-contrast colors | CRITICAL | Complementary pairs: yellow/black, red/white, blue/orange |
| Emotional face expression | CRITICAL | Surprise, excitement, shock, curiosity — exaggerated beats subtle |
| 3 words or fewer | CRITICAL | Every extra word reduces readability at small sizes |
| Rule of thirds | HIGH | Face on one third, text on the opposite third |
| No clutter | HIGH | One focal element + one text element maximum |
| Color pop background | MEDIUM | Solid or gradient in a bold color behind the subject |
| Outline/stroke on text | MEDIUM | White or black stroke ensures readability on any background |
| Avoid red/green together | LOW | Color-blind viewers cannot distinguish these |

**THE #1 RULE: IF THE THUMBNAIL IS NOT READABLE AT THE SIZE OF YOUR THUMB, IT WILL NOT GET CLICKED.**

---

## Quick Reference: Thumbnail Style Types

| Style | Layout | Best For | Text Placement | Visual Focus |
|-------|--------|----------|----------------|--------------|
| **Reaction** | Face on left third, text on right | Commentary, reactions, vlogs | 1-2 bold words beside face | Exaggerated facial expression |
| **Tutorial** | Step visual on right, text on left | How-to, walkthroughs, guides | Action verb + subject ("Edit FASTER") | Screenshot or tool visual |
| **Listicle** | Large number left, subject montage right | Top 5, rankings, comparisons | Bold number as anchor element | Collage of items being ranked |
| **Story** | Dramatic full-bleed image, text overlay | Challenges, experiences, storytime | Question or cliffhanger centered | Cinematic photo or dramatic moment |
| **Before/After** | Split screen, left vs right | Transformations, results, reviews | Labels for each half | Clear visual contrast between halves |
| **Bold Text** | Text dominates 60%+ of frame | Hot takes, opinions, announcements | Statement fills the canvas | Minimal imagery, maximum text impact |

---

## Core Workflow

GENERATE 3 DISTINCT THUMBNAIL OPTIONS WITH DIFFERENT STYLE APPROACHES — NEVER 3 VARIATIONS OF THE SAME CONCEPT.

### Step 1: Gather Video Details

Collect before generating anything:

1. **Video title** — exact or working title of the video
2. **Topic/subject** — what the video is about in one sentence
3. **Style preference** — preferred style from the table above, or let the skill pick 3 contrasting styles
4. **Face/person** — include a face? If yes, describe expression and framing
5. **Brand colors** — Canva brand kit or manual hex codes
6. **Competing thumbnails** — thumbnails they want to stand out from (optional)

If the user provides items 1-2, proceed with defaults for the rest.

**Brief template for vague requests:**
```
I'll generate 3 thumbnail options. Quick details needed:
1. Video title?
2. What's it about? (one sentence)
3. Preferred style? (Reaction / Tutorial / Listicle / Story / Bold Text — or I'll pick 3)
4. Include a face? (describe expression if yes)
5. Use your Canva brand kit? (Y/N)
```

### Step 2: Load Brand Kit from Canva

1. Call `list-brand-kits` to retrieve available brand kits
2. Select matching kit or ask user to choose if multiple exist
3. Note brand colors, fonts, and logo references for generation prompts

**IF NO BRAND KIT EXISTS:**
- Ask for primary color, secondary color, and preferred font weight (bold/heavy recommended)
- **DEFAULT PALETTE IF NO PREFERENCE:** Yellow (#FFD700) text on dark navy (#0A0E27) background with white (#FFFFFF) stroke — high visibility on both light and dark YouTube interfaces

### Step 3: Generate 3 Thumbnail Options

Generate 3 thumbnails using 3 different style approaches. Each must be a completely different creative direction.

**Option selection logic (when no user preference):**
- Commentary/opinion videos: Reaction + Bold Text + Story
- How-to/educational videos: Tutorial + Listicle + Bold Text
- Challenge/experience videos: Story + Reaction + Before/After
- Review/comparison videos: Listicle + Before/After + Tutorial

For each option:
1. Condense the video title to **3 words or fewer** for overlay text
2. Build generation prompt with: overlay text, brand colors, style layout, 1280x720 landscape, high-contrast treatment, text stroke/outline
3. Call `generate-design` with the prompt
4. Call `get-design-thumbnail` to preview

**Example prompt — Reaction style:**
```
YouTube thumbnail, 1280x720, landscape orientation.
Style: Reaction thumbnail.
Layout: Exaggerated surprised face on the left third of frame.
Background: Solid bold red (#FF2D55) with subtle radial gradient.
Text overlay on right side: "NO WAY" in Impact font, white (#FFFFFF) with
thick black stroke outline. Text fills 35% of frame width.
High contrast. Bold colors. Clean composition. No clutter.
Rule of thirds composition. Safe margins on all edges.
```

**Example prompt — Tutorial style:**
```
YouTube thumbnail, 1280x720, landscape orientation.
Style: Tutorial thumbnail.
Layout: Software screenshot or tool visual on the right two-thirds.
Text on left third: "Edit FASTER" in Bebas Neue, yellow (#FFD700) on
dark navy (#0A0E27) block. White stroke on text.
Arrow pointing from text to the visual.
High contrast. Clean layout. One focal point. No clutter.
```

**Example prompt — Bold Text style:**
```
YouTube thumbnail, 1280x720, landscape orientation.
Style: Bold text-dominant thumbnail.
Layout: Text fills 60% of the frame, centered.
Text: "$10K" in massive Impact font, bright yellow (#FFD700).
Background: Dark navy (#0A0E27) solid.
Subtle money/cash imagery at 20% opacity behind text.
White stroke outline on all text. Extremely readable at small sizes.
```

Present all 3 options with style name, layout description, design ID, and thumbnail preview. **Wait for the user to pick a favorite before proceeding.**

**IF THE USER DISLIKES ALL 3:**
- Ask what element was closest and what feels wrong
- Generate 2 new options incorporating the feedback
- **If 5 total attempts miss, stop and provide specs for manual Canva creation**

### Step 4: Refine the Selected Thumbnail

Once the user picks a favorite:

1. Ask if refinements are needed (text wording, colors, repositioning, add/remove elements)
2. If refinements requested:
   - Call `start-editing-transaction` on the selected design ID
   - Call `perform-editing-operations` with the specific changes
   - Call `get-design-thumbnail` to preview the edit
   - If approved: call `commit-editing-transaction`
   - If not approved: call `cancel-editing-transaction` and repeat
3. If no changes needed, proceed directly to export

**REFINEMENT LIMIT:** Maximum 3 rounds of edits. After 3 rounds, regenerate from scratch with all feedback baked into the prompt rather than continuing to patch.

### Step 5: Export at 1280x720 as JPG

1. Call `get-export-formats` to confirm JPG availability
2. Call `export-design` with: design ID, format `jpg`, dimensions 1280x720
3. Verify: file under 2 MB, dimensions exactly 1280x720
4. Present the final export with file name, dimensions, format, size, and export URL

**FILE NAMING:** `youtube-thumbnail-{topic-slug}.jpg` — all lowercase, hyphens only

**DEFAULT FORMAT: JPG** — keeps files under YouTube's 2 MB limit. Use PNG only if user requests it or design is purely text/vector.

---

## Example 1: "5 Tools Every Solopreneur Needs" — Tutorial Thumbnail

**User brief:** "Publishing a video called '5 Tools Every Solopreneur Needs' about productivity apps. Professional but eye-catching. Brand colors: teal and white."

**Execution:**

1. **Details:** Title: "5 Tools Every Solopreneur Needs" | Topic: productivity apps | Style: auto-select Tutorial + Listicle + Bold Text (educational) | No face | Brand: teal/white

2. **Brand kit:** `list-brand-kits` returns "Solopreneur Studio" — teal (#00BFA6), white (#FFFFFF), dark gray (#1A1A2E). Loaded.

3. **3 options generated:**
   - **Option A (Tutorial):** "5 TOOLS" in white on teal block left, app screenshot mockup right. `generate-design` + `get-design-thumbnail`.
   - **Option B (Listicle):** Massive "5" in white left, app icon grid on dark gray right, teal accent line. `generate-design` + `get-design-thumbnail`.
   - **Option C (Bold Text):** "5 TOOLS" fills 60% of frame, dark gray background, teal underline. `generate-design` + `get-design-thumbnail`.

4. **User picks Option B.** Requests pure black background instead of dark gray.

5. **Refine:** `start-editing-transaction` > `perform-editing-operations` (background #1A1A2E to #000000) > `get-design-thumbnail` > user approves > `commit-editing-transaction`.

6. **Export:** `export-design` as JPG, 1280x720. File: 142 KB.

**Delivered:**
```
Thumbnail ready for "5 Tools Every Solopreneur Needs":

  File: youtube-thumbnail-5-tools-solopreneur.jpg
  Dimensions: 1280 x 720 px
  Format: JPG | Size: 142 KB
  Export URL: [URL]

Design: Listicle style — bold "5" left, app icon grid right, pure black
background with teal accents. Upload to YouTube Studio as custom thumbnail.
```

---

## Example 2: "I Made $10K in 30 Days" — Reaction/Story Thumbnail

**User brief:** "New video: 'I Made $10K in 30 Days' about first month freelancing. Dramatic, makes people click. Include my face looking shocked. Brand: gold and black."

**Execution:**

1. **Details:** Title: "I Made $10K in 30 Days" | Topic: freelancing income milestone | Style: auto-select Reaction + Story + Bold Text (challenge/experience) | Face: shocked expression | Brand: gold (#FFD700), black (#000000)

2. **Brand kit:** `list-brand-kits` returns "Freelance Gold" — gold (#FFD700), black (#000000), white (#FFFFFF). Loaded.

3. **3 options generated:**
   - **Option A (Reaction):** Shocked face left third, "$10K" in massive gold right, black background, subtle money imagery at 10% opacity. `generate-design` + `get-design-thumbnail`.
   - **Option B (Story):** Full-bleed cinematic desk scene, "$10K?" question in gold centered, dark moody tones, vignette. `generate-design` + `get-design-thumbnail`.
   - **Option C (Bold Text):** "$10K" in gold top half, "30 DAYS" in white below, black background, gold arrow between. `generate-design` + `get-design-thumbnail`.

4. **User picks Option A.** Requests bigger gold text and subtle green money rain in background.

5. **Refine:** `start-editing-transaction` > `perform-editing-operations` (scale "$10K" text up 20%, add green money particles at 15% opacity) > `get-design-thumbnail` > user approves > `commit-editing-transaction`.

6. **Export:** `export-design` as JPG, 1280x720. File: 198 KB.

**Delivered:**
```
Thumbnail ready for "I Made $10K in 30 Days":

  File: youtube-thumbnail-10k-30-days.jpg
  Dimensions: 1280 x 720 px
  Format: JPG | Size: 198 KB
  Export URL: [URL]

Design: Reaction style — shocked face left, massive "$10K" in gold right,
black background with subtle green money rain. Upload to YouTube Studio.
```

---

## Pre-Delivery Checklist

Run before delivering. **DO NOT SKIP ANY ITEM.**

| # | Check | Verify |
|---|-------|--------|
| 1 | **Text readable at thumb size** | Legible at 168x94 px (YouTube mobile suggested size) |
| 2 | **3 words or fewer** | Count overlay words — if >3, cut to most impactful |
| 3 | **Face visible and emotional** | Expression obvious at small sizes (if face included) |
| 4 | **High contrast** | 4.5:1+ text-to-background ratio — no medium tones |
| 5 | **No clutter** | Max 2 focal elements (one text, one visual) |
| 6 | **Rule of thirds** | Key elements on thirds grid intersections |
| 7 | **Safe zone** | All key content within center 80% of frame |
| 8 | **1280 x 720 px** | Exact dimensions verified in export |
| 9 | **Under 2 MB** | JPG file size within YouTube limit |
| 10 | **No title duplication** | Thumbnail text complements, not duplicates, video title |

```
Pre-Delivery Checklist:
  [x] Text readable at thumb size (168x94)
  [x] 3 words or fewer on overlay
  [x] Face visible and emotional (if applicable)
  [x] High contrast (4.5:1+ ratio)
  [x] No clutter (max 2 focal elements)
  [x] Rule of thirds composition
  [x] Safe zone (center 80%)
  [x] Dimensions: 1280 x 720 px
  [x] File size: under 2 MB
  [x] Text complements (not duplicates) video title
```

---

## Recovery and Troubleshooting

### Brand Kit Not Found
1. Inform user: "No brand kits found in your Canva account."
2. Ask for primary color, secondary color, font weight preference
3. No preference? Apply default: Yellow (#FFD700) text, dark navy (#0A0E27) background, white (#FFFFFF) stroke
4. Suggest creating a brand kit in Canva for future consistency

### All 3 Options Rejected
1. Ask: "Which was closest? What did you like/dislike?"
2. Ask for a reference thumbnail URL or description of what they envision
3. Generate 2 new options with specific feedback
4. **After 5 total options, stop and provide text specs for manual Canva creation**

### Editing Transaction Fails
1. Call `cancel-editing-transaction` to clean up
2. Retry `start-editing-transaction` on the same design
3. Simplify edits — one change at a time instead of batching
4. If still failing, regenerate from scratch with refinements in the prompt

### Export Fails
1. Verify design ID with `get-design-thumbnail`
2. Try PNG instead of JPG (inform user of format change)
3. If both fail, provide design ID for manual export: Canva > Find design > Share > Download > JPG > 1280x720

### Design Generation Fails
1. Simplify prompt to essentials: text, colors, dimensions
2. Retry once with simplified prompt
3. Try Bold Text style (fewest layout demands, most reliable)
4. **After 3 failures, stop and provide specs for manual creation**

### Text Overlay Exceeds 3 Words
1. Do NOT put full title on thumbnail
2. Extract 1-3 most powerful words
3. Present condensed options to user:
   ```
   Title too long for thumbnail. Condensed options:
     A) "6 FIGURES"
     B) "$100K+"
     C) "BEDROOM BIZ"
   Which one? Or suggest your own (3 words max).
   ```
4. Use chosen text in all 3 options

---

## Anti-Patterns

- **DO NOT** put the full video title on the thumbnail — 3 words maximum
- **DO NOT** use low-contrast combinations (gray/gray, light yellow/white, navy/black)
- **DO NOT** generate 3 variations of the same concept — each must be a different style
- **DO NOT** export before the user picks and approves a favorite
- **DO NOT** use small or thin fonts — must be readable at 168x94 px
- **DO NOT** crowd with multiple text elements, logos, and imagery — one text + one visual max
- **DO NOT** skip the refinement step — always ask if changes are needed before export
- **DO NOT** export as PNG by default — JPG is the YouTube thumbnail standard
- **DO NOT** duplicate the video title word-for-word on the thumbnail
