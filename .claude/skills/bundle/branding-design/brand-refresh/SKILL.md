---
name: brand-refresh
description: "Batch updates text and imagery across existing Canva designs when brand elements change, searching for affected designs and applying find-and-replace operations across all confirmed files. Use when a user has updated their brand colors, fonts, tagline, logo, or contact info and needs to propagate those changes across multiple existing Canva designs."
allowed-tools: Read Write Glob mcp__claude_ai_Canva__search-designs mcp__claude_ai_Canva__get-design mcp__claude_ai_Canva__get-design-content mcp__claude_ai_Canva__start-editing-transaction mcp__claude_ai_Canva__perform-editing-operations mcp__claude_ai_Canva__commit-editing-transaction mcp__claude_ai_Canva__cancel-editing-transaction mcp__claude_ai_Canva__get-design-thumbnail mcp__claude_ai_Canva__list-brand-kits
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Brand Refresh

## When to Use This Skill

Use this skill when you need to:
- Propagate a new tagline, slogan, or brand statement across existing Canva designs
- Replace an old phone number, email address, or website URL across marketing materials
- Update brand colors or font references embedded in design text elements
- Swap a logo URL or image asset across multiple designs after a rebrand
- Find every design that contains outdated brand information and batch-update them

**DO NOT** use this skill for:
- Creating brand-new designs from scratch (use social-media-graphics or similar skills)
- Updating a Canva Brand Kit itself (do that directly in Canva settings)
- Redesigning layouts, restructuring content, or changing visual concepts
- Editing a single design (just open it in Canva manually)

---

## Quick Reference: Common Brand Change Types

| Change Type | Old Value Example | New Value Example | Search Strategy |
|-------------|-------------------|-------------------|-----------------|
| Tagline | "Build Better" | "Ship Faster" | Search design content for exact old text |
| Website URL | www.oldsite.com | www.newsite.com | Search for domain string |
| Phone number | (555) 123-4567 | (555) 987-6543 | Search for old number with/without formatting |
| Email address | hello@oldco.com | hello@newco.com | Search for old email string |
| Company name | OldCo Inc. | NewCo Inc. | Search for old company name |
| Color hex code | #FF6B35 | #2D5BFF | Search text elements referencing the old hex |
| Street address | 123 Main St | 456 Oak Ave | Search for old street address |

---

## Core Workflow

EVERY BRAND REFRESH STARTS WITH A COMPLETE CHANGE LIST BEFORE TOUCHING ANY DESIGNS -- NEVER EDIT DESIGNS WITHOUT KNOWING ALL THE CHANGES UPFRONT.

### Step 1: Understand the Changes

Collect every brand change from the user before searching for designs.

1. Ask the user to list all elements that changed, in explicit old-to-new pairs
2. Confirm each pair with the user before proceeding
3. Group changes by type for efficient searching

**Template to present if the user gives a vague request:**

```
I'll update your Canva designs. I need the exact old-to-new values for each change:

1. What text changed? (old tagline -> new tagline, old URL -> new URL, etc.)
2. Any contact info changes? (phone, email, address)
3. Any visual changes? (colors, logo image URL)
4. How many designs do you think are affected? (rough estimate helps me search)
```

**Build a change manifest like this:**

```
Brand Refresh — Change Manifest
================================
Change 1: Tagline
  OLD: "Build Better"
  NEW: "Ship Faster"

Change 2: Website URL
  OLD: www.acmecorp.com
  NEW: www.acme.io

Change 3: Phone Number
  OLD: (555) 123-4567
  NEW: (555) 987-6543

Total changes: 3
```

**DO NOT proceed to Step 2 until the user confirms the change manifest is complete and correct.**

### Step 2: Search for Affected Designs

Find every design that contains any of the old values from the change manifest.

1. Call `search-designs` with keywords from each old value:
   - For taglines: search the key words (e.g., "Build Better")
   - For URLs: search the domain (e.g., "acmecorp")
   - For phone/email: search the full string and partial matches
   - For company names: search the old name

2. For each design returned by search, call `get-design-content` to inspect the actual text elements

3. Check every text element in the design content against every old value in the change manifest

4. Build an affected designs list with specifics:

```
Scanning designs for old brand values...

Search: "Build Better" — 23 designs returned
  Checking content... 15 contain the tagline in text elements

Search: "acmecorp" — 18 designs returned
  Checking content... 12 contain the old URL in text elements

Search: "(555) 123-4567" — 9 designs returned
  Checking content... 8 contain the old phone number
```

5. Deduplicate the list — a single design may match multiple changes

**IF SEARCH RETURNS TOO MANY RESULTS:**
- Narrow the search by adding context words (e.g., "Build Better tagline" instead of just "Build")
- Filter by design type if the user specifies (social posts, presentations, flyers)
- Process in batches of 20 designs at a time

**IF SEARCH RETURNS NO RESULTS:**
- Try alternate phrasings or partial strings
- Ask the user if the old value is spelled differently in some designs
- Try searching for the brand name alone to find all branded designs, then inspect content manually
- **After 3 failed search strategies, inform the user:** "No designs found containing those values. Please verify the old text is exactly as it appears in your Canva designs."

### Step 3: Present Affected Designs for Confirmation

Show the user exactly which designs will be modified and what changes apply to each.

1. Call `get-design-thumbnail` for each affected design to provide visual context

2. Present the full list grouped by design:

```
AFFECTED DESIGNS — REVIEW BEFORE UPDATING
==========================================

1. "Summer Sale Instagram Post" (dsg_abc123)
   [thumbnail displayed]
   Changes to apply:
     - Tagline: "Build Better" -> "Ship Faster"
     - URL: www.acmecorp.com -> www.acme.io

2. "Company Overview Presentation" (dsg_def456)
   [thumbnail displayed]
   Changes to apply:
     - Tagline: "Build Better" -> "Ship Faster"
     - Phone: (555) 123-4567 -> (555) 987-6543
     - URL: www.acmecorp.com -> www.acme.io

3. "Business Card Template" (dsg_ghi789)
   [thumbnail displayed]
   Changes to apply:
     - Phone: (555) 123-4567 -> (555) 987-6543
     - URL: www.acmecorp.com -> www.acme.io

... (12 more designs)

==========================================
Total: 15 designs, 34 individual text replacements

Confirm: Update all 15 designs? Or tell me which to skip.
```

3. **Wait for user confirmation** before editing anything
4. If the user wants to skip specific designs, remove them from the batch
5. If the user identifies designs that should be affected but are missing, run additional searches

**DO NOT edit any designs until the user explicitly confirms the list.**

### Step 4: Apply Changes via Editing Transactions

Process each confirmed design using Canva's editing transaction workflow.

**For each design in the confirmed list:**

1. Call `start-editing-transaction` for the design ID
2. Call `perform-editing-operations` with all text replacements for that design:
   - Replace each old value with the new value in every text element where it appears
   - Apply all changes for the design in a single `perform-editing-operations` call when possible
3. Call `commit-editing-transaction` to save the changes

4. Call `get-design-thumbnail` to verify the update visually

5. Log the result:

```
[1/15] "Summer Sale Instagram Post" (dsg_abc123)
  - Replaced "Build Better" with "Ship Faster" — 1 text element updated
  - Replaced "www.acmecorp.com" with "www.acme.io" — 1 text element updated
  STATUS: Committed successfully
```

**Process designs sequentially — one transaction at a time.** Do not start a new transaction before the previous one is committed or cancelled.

6. After all designs are processed, present the final summary:

```
BRAND REFRESH COMPLETE
======================
Designs updated: 15 of 15 successful
Total replacements made: 34

Breakdown by change:
  "Build Better" -> "Ship Faster"       — updated in 15 designs
  www.acmecorp.com -> www.acme.io        — updated in 12 designs
  (555) 123-4567 -> (555) 987-6543       — updated in 8 designs

All designs saved. Changes are live in your Canva account.
```

---

## Example 1: Company Changes Tagline Across Social Graphics

**User request:** "We just changed our tagline from 'Build Better' to 'Ship Faster'. I need to update all our social media graphics in Canva — I think there are about 15 of them."

**Step-by-step execution:**

1. **Change manifest:**
   ```
   Brand Refresh — Change Manifest
   ================================
   Change 1: Tagline
     OLD: "Build Better"
     NEW: "Ship Faster"

   Total changes: 1
   ```
   User confirms.

2. **Search:** Call `search-designs` with query "Build Better". Returns 23 results. Call `get-design-content` on each. 15 designs contain "Build Better" in text elements.

3. **Present:** Show all 15 designs with thumbnails and the tagline change noted for each. User confirms all 15.

4. **Apply:** For each of the 15 designs:
   - `start-editing-transaction` with design ID
   - `perform-editing-operations` — replace "Build Better" with "Ship Faster"
   - `commit-editing-transaction`
   - `get-design-thumbnail` to verify

   **Result:**

   ```
   BRAND REFRESH COMPLETE
   ======================
   Designs updated: 15 of 15 successful
   Total replacements made: 15

   Updated designs:
     [1]  Instagram Post — Q1 Campaign
     [2]  Instagram Post — Product Launch
     [3]  Instagram Story — Weekly Tips
     [4]  Facebook Cover Photo
     [5]  Facebook Post — About Us
     [6]  X/Twitter Header
     [7]  X/Twitter Post — Welcome
     [8]  LinkedIn Banner
     [9]  LinkedIn Post — Hiring
     [10] Pinterest Pin — Brand Overview
     [11] YouTube Thumbnail — Episode 12
     [12] YouTube Thumbnail — Episode 13
     [13] Email Header Graphic
     [14] Newsletter Banner
     [15] Website Hero Banner

   Tagline "Ship Faster" is now live across all 15 designs.
   ```

---

## Example 2: Updating Phone Number and Website Across Marketing Materials

**User request:** "We moved offices and changed our phone number. Old number was (312) 555-0142, new one is (773) 555-0198. Also our website changed from www.greenleafco.com to www.greenleaf.io. Can you update everything in Canva?"

**Step-by-step execution:**

1. **Change manifest:**
   ```
   Brand Refresh — Change Manifest
   ================================
   Change 1: Phone Number
     OLD: (312) 555-0142
     NEW: (773) 555-0198

   Change 2: Website URL
     OLD: www.greenleafco.com
     NEW: www.greenleaf.io

   Total changes: 2
   ```
   User confirms.

2. **Search:**
   - `search-designs` with query "(312) 555-0142" — 6 results. Content check: 5 contain the phone number.
   - `search-designs` with query "greenleafco" — 14 results. Content check: 8 contain the URL.
   - Deduplicated total: 10 unique designs (3 designs have both phone and URL).

3. **Present:** Show 10 designs with thumbnails. For each, list which changes apply:

   ```
   AFFECTED DESIGNS — REVIEW BEFORE UPDATING
   ==========================================

   1. "Business Card — Front" (dsg_bc001)
      [thumbnail displayed]
      Changes: phone + URL

   2. "Business Card — Back" (dsg_bc002)
      [thumbnail displayed]
      Changes: phone + URL

   3. "Tri-fold Brochure — Page 3" (dsg_br003)
      [thumbnail displayed]
      Changes: phone + URL

   4. "Email Signature Banner" (dsg_es004)
      [thumbnail displayed]
      Changes: phone + URL (contact block, no phone)
      ** Note: contains URL but phone not found in this design

   5. "Trade Show Banner" (dsg_ts005)
      [thumbnail displayed]
      Changes: phone only

   ... (5 more designs)

   ==========================================
   Total: 10 designs, 13 individual text replacements

   Confirm: Update all 10 designs?
   ```

   User confirms but says: "Skip the trade show banner, we're not using that anymore."
   Remove design 5 from the batch. Proceeding with 9 designs.

4. **Apply:** For each of the 9 designs:
   - Start transaction, perform replacements, commit, verify thumbnail

   **Result:**

   ```
   BRAND REFRESH COMPLETE
   ======================
   Designs updated: 9 of 9 successful
   Skipped: 1 (Trade Show Banner — user requested skip)
   Total replacements made: 12

   Breakdown:
     (312) 555-0142 -> (773) 555-0198  — updated in 4 designs
     www.greenleafco.com -> www.greenleaf.io — updated in 8 designs

   All designs saved. Changes are live in your Canva account.
   ```

---

## Pre-Update Checklist

Run this checklist before committing any edits. **DO NOT SKIP ANY ITEM.**

| Check | What to Verify | How |
|-------|----------------|-----|
| Change manifest confirmed | User reviewed and approved all old-to-new pairs | Explicit user confirmation at Step 1 |
| All old values searched | Every old value was searched, not just the first one | Verify each search was executed |
| Content inspected | `get-design-content` was called on every search result | Confirm content check logs |
| Designs deduplicated | No design appears twice in the affected list | Check for duplicate design IDs |
| Thumbnails shown | User saw a thumbnail preview for each affected design | Confirm thumbnails were displayed |
| User approved list | User explicitly confirmed which designs to update | Must happen at Step 3 |
| Changes per design listed | Each design shows exactly which replacements apply | Verify in the presented list |
| Sequential transactions | Only one editing transaction is open at a time | Process one design, commit, then next |

```
Pre-Update Checklist:
  [x] Change manifest confirmed by user
  [x] All old values searched
  [x] Design content inspected for each result
  [x] Affected designs list deduplicated
  [x] Thumbnails shown for all affected designs
  [x] User approved the final list
  [x] Per-design change list accurate
  [x] Sequential transaction processing
```

---

## Recovery and Troubleshooting

### Edit Transaction Fails Mid-Design

If `perform-editing-operations` or `commit-editing-transaction` returns an error:

1. Call `cancel-editing-transaction` to cleanly abort the failed transaction
2. Log the design as failed — do not retry immediately
3. Continue processing the remaining designs
4. After the batch completes, retry each failed design individually
5. **If a design fails twice:** "Design '[name]' (dsg_xxx) could not be updated. The design may be locked, corrupted, or use an unsupported element type. Open it in Canva to update manually. Changes needed: [list the specific replacements]."

### Design Is Locked or Read-Only

If `start-editing-transaction` returns a permission or lock error:

1. Inform the user: "Design '[name]' is currently locked. It may be open in another session or shared with restricted permissions."
2. Skip the design and continue with the rest of the batch
3. After the batch completes, ask the user to close the design in Canva and retry

### Search Finds Designs the User Does Not Recognize

If the affected designs list includes unexpected items:

1. Show the thumbnail and design name — let the user decide
2. The user may have old or archived designs they forgot about
3. **Default: include them in the update unless the user explicitly excludes them** — outdated designs with wrong brand info are exactly what this skill fixes

### Partial Text Match Creates Unintended Replacements

If the old value is a common word or substring that could match unintended text:

1. Before editing, show the exact text elements that will change and their surrounding context
2. Example: replacing "Go" (old company name) could match "Go to our website" — flag this for the user
3. **Use exact, case-sensitive matching** when performing replacements
4. If a replacement is too broad, ask the user for a more specific search string

### User Wants to Undo Changes

If the user realizes a change was wrong after edits are committed:

1. Canva has built-in version history — instruct the user to restore previous versions
2. Alternatively, run the skill again with the values reversed (swap old and new)
3. **This skill does not maintain its own undo history** — rely on Canva's versioning

---

## Anti-Patterns

- **DO NOT** edit designs without user confirmation of the affected list — accidental edits across 20+ designs are difficult to reverse
- **DO NOT** open multiple editing transactions simultaneously — one at a time, commit before starting the next
- **DO NOT** skip the content inspection step — search results may include designs that mention the keyword but do not contain the actual brand element
- **DO NOT** assume formatting — if the old phone number appears as "(555) 123-4567" in some designs and "555-123-4567" in others, search for both formats
- **DO NOT** proceed with a partial change manifest — if the user mentions "a few things changed," press for the complete list before searching
- **DO NOT** replace text blindly — always verify the match is the intended brand element, not part of unrelated content
