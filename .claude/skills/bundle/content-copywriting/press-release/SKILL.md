---
name: press-release
description: "Writes professional press releases following AP style with headline, dateline, lead paragraph, body, boilerplate, and media contact sections. Use when a user is launching a product, announcing a milestone, making a hire, forming a partnership, or has any newsworthy event to share with media outlets."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Press Release

## When to Use This Skill

Use this skill when you need to:
- Announce a product launch, feature release, or service expansion to media outlets
- Share a funding round, revenue milestone, or company achievement with the press
- Publicize a new hire, promotion, or advisory board appointment
- Announce a partnership, acquisition, or strategic alliance
- Promote an event, grand opening, or community initiative
- Distribute an award, certification, or industry recognition

**DO NOT** use this skill for blog posts, social media announcements, internal memos, or marketing copy. This is for structured press releases intended for journalists and media distribution only.

---

## Core Principle

A PRESS RELEASE IS A NEWS DOCUMENT, NOT AN ADVERTISEMENT. EVERY SENTENCE MUST REPORT FACTS A JOURNALIST CAN VERIFY AND PUBLISH WITHOUT REWRITING.

---

## Phase 1: Brief

Before writing a single word, gather the information that shapes the entire release. No brief, no draft.

### Required Inputs

Ask the user for each of these. Group them into two rounds to avoid overwhelming the conversation.

**Round 1 -- The News (ask all at once):**

| Input | What to Ask | Default |
|-------|------------|---------|
| **The news** | "What is the announcement? One sentence." | No default -- must be provided |
| **Release type** | "Which category: Product Launch, Funding/Milestone, Partnership, Hire/Promotion, Event, or Award?" | Infer from the news |
| **Who is involved** | "Company name, key people, and their titles." | No default -- must be provided |
| **Timing** | "Is this for immediate release, or is there an embargo date?" | For Immediate Release |
| **Quote attribution** | "Who should be quoted in the release? Name, title, company." | Company founder or CEO |

**Round 2 -- Context and Distribution (ask after Round 1 is answered):**

| Input | What to Ask | Default |
|-------|------------|---------|
| **Why it matters** | "Why should a journalist care? What is the impact on customers, the industry, or the community?" | No default -- push for this |
| **Supporting details** | "Any numbers, dates, features, pricing, or availability info to include?" | Include what the user provides |
| **Company boilerplate** | "Do you have an existing 'About [Company]' paragraph? If not, give me a 2-3 sentence description: what the company does, who it serves, and where it is based." | Generate from user info |
| **Media contact** | "Name, email, and phone number for the media contact." | No default -- must be provided |
| **Target outlets** | "Which media outlets or journalist types are you targeting? (Industry trade press, local newspapers, national tech blogs, etc.)" | General industry and local media |

### Brief Template

Present this to the user before proceeding:

```
## Press Release Brief

**Release type:** Product Launch
**Embargo:** FOR IMMEDIATE RELEASE
**The news:** Greenline Analytics launches an AI-powered inventory forecasting tool for independent retailers
**Company:** Greenline Analytics, Denver, CO
**Key person:** Jordan Reeves, Founder and CEO
**Quote attribution:** Jordan Reeves + one customer quote (Maria Santos, Owner, The Corner Pantry)
**Why it matters:** Independent retailers lose an average of 8% of revenue to overstock and stockouts -- this tool reduces that by 60% at a price point small shops can afford ($49/month)
**Supporting details:** Available starting March 15, integrates with Shopify and Square, 200 beta users, free 30-day trial
**Boilerplate:** Will generate from company info
**Media contact:** Jordan Reeves, press@greenlineanalytics.com, (720) 555-0198
**Target outlets:** Retail trade press, Denver business journals, SaaS/startup blogs
```

**GATE: Do not proceed to Phase 2 until the user confirms the brief. At minimum, you must have: the news, a quotable person with their title, company information, and a media contact.**

---

## Phase 2: Write

With an approved brief, write the press release following this exact structure. Every section is required unless marked optional.

### Press Release Structure

```
**FOR IMMEDIATE RELEASE**
(or: **EMBARGOED UNTIL [Date], [Time] [Timezone]**)

# [Headline]

## [Subheadline -- optional]

**[CITY, STATE]** -- [Lead paragraph: who, what, when, where, why
in 2-3 sentences. The news goes here.]

[Body paragraph 1: supporting details, context, market problem]

"[Quote from primary spokesperson -- forward-looking, ties back
to the impact on customers or the market]," said [Full Name],
[Title] of [Company].

[Body paragraph 2: additional details -- features, pricing,
availability, partnerships]

"[Second quote -- optional -- from a partner, customer, or team
member providing external validation]," said [Full Name],
[Title] of [Company/Organization].

[Closing paragraph: availability, call to action, where to learn more]

### About [Company Name]

[Boilerplate: 2-4 sentences. What the company does, who it serves,
when it was founded, where it is headquartered. End with website URL.]

### Media Contact

[Full Name]
[Title]
[Company]
[Email]
[Phone]

###
```

### Section-by-Section Writing Rules

**Release Line:**
- "FOR IMMEDIATE RELEASE" in bold, all caps -- this is standard and non-negotiable
- If embargoed, include exact date, time, and timezone: "EMBARGOED UNTIL March 10, 2025, 9:00 AM ET"

**Headline:**
- Starts with an action verb (Launches, Announces, Secures, Expands, Appoints, Partners)
- Contains the company name
- Under 80 characters
- Title case (AP style: capitalize words with 4+ letters, all verbs, first and last word)
- No periods at the end

**Subheadline (optional):**
- Adds context the headline cannot fit
- Sentence case
- Under 120 characters
- Use when the headline alone does not convey enough for a journalist to decide whether to read further

**Dateline:**
- Format: CITY, STATE (abbreviated per AP: Calif., Colo., N.Y.) followed by an em dash
- Use the company's headquarters city unless the news is location-specific (e.g., a store opening in a different city)

**Lead Paragraph:**
- Answers who, what, when, where, and why in 2-3 sentences
- The most important fact goes in the first sentence
- Company name, product name, and the core news must all appear here
- No adjectives like "leading" or "innovative" -- just the facts

**Body Paragraph 1:**
- Context: why this matters to the target audience
- Market problem or industry backdrop (1-2 sentences with a data point if available)
- How the announcement addresses that problem

**Primary Quote:**
- Attributed to the most senior relevant person (founder, CEO, president)
- Forward-looking: what this means for customers, the market, or the company's mission
- Must sound like something a human would actually say out loud
- Format: "Quote text," said Full Name, Title of Company.
- Use "said" -- not "stated," "shared," "expressed," or "noted"

**Body Paragraph 2:**
- Specific details: features, pricing, availability dates, technical specs, partner names
- If a product launch, this is where you list 2-4 key features as bullet points
- If a funding announcement, this is where you name investors and intended use of funds

**Second Quote (optional):**
- Use when external validation strengthens the announcement
- Best sources: a customer, partner, investor, or industry figure
- Must add a perspective the primary quote does not cover

**Closing Paragraph:**
- Where to find more info (website URL, landing page)
- Availability date or how to sign up / attend / apply
- No new information -- this is the wrap-up

**Boilerplate ("About [Company]"):**
- 2-4 sentences, present tense
- What the company does (core product/service)
- Who it serves (target market)
- Where it is headquartered
- End with the company website URL
- No superlatives ("the leading," "the best," "world-class")

**Media Contact:**
- Full name, title, company, email, phone -- each on its own line
- This is for journalists, not customers

**End Marker:**
- Three hash marks centered: ###
- This is the universal press release end marker

### AP Style Quick Reference

Follow these rules throughout the release:

| Rule | Correct | Incorrect |
|------|---------|-----------|
| Headline case | Title Case for Headlines | title case for headlines |
| Oxford comma | red, white and blue | red, white, and blue |
| Numbers under 10 | spelled out: "five locations" | 5 locations |
| Numbers 10+ | numerals: "12 employees" | twelve employees |
| Percent | 8% (numeral + symbol) | eight percent |
| Dates | March 15 (no "th" or "st") | March 15th |
| States | abbreviated in datelines: Colo. | Colorado (in dateline) |
| Titles before names | CEO Jordan Reeves | Jordan Reeves, the CEO |
| Titles after names | Jordan Reeves, founder and CEO | Jordan Reeves, Founder and CEO |
| Company reference | first mention: full name; after: short name | full name every time |

### Length Target

**400-600 words total.** Most journalists stop reading after 400 words. Every word must earn its place. If the release exceeds 600 words, cut supporting details before cutting quotes or the lead.

---

## Phase 3: Review

After writing the draft, read it back and verify every required section is present.

### Review Checklist (internal -- do not show to user)

1. FOR IMMEDIATE RELEASE (or embargo notice) appears at the top
2. Headline starts with an action verb, contains company name, under 80 characters
3. Dateline format is correct (CITY, STATE -- )
4. Lead paragraph answers who, what, when, where, why
5. At least one attributed quote using "said"
6. Boilerplate paragraph exists with company description and URL
7. Media contact includes name, email, and phone
8. End marker (###) is present
9. Total word count is 400-600
10. No marketing superlatives ("revolutionary," "game-changing," "world-class")

Present the complete press release to the user.

Then ask:
1. "Does the headline capture the news accurately?"
2. "Do the quotes sound like something [Name] would actually say?"
3. "Any details to add, change, or remove?"

**GATE: Do not save to file until the user explicitly approves.** Acceptable approvals: "looks good," "approved," "yes," "save it," "perfect," or similar affirmative. If the user requests changes, revise and re-present.

**If the user requests more than 3 rounds of revisions, pause and ask:** "We have been through several rounds. Would you like to finalize what we have and note remaining edits for later, or keep refining?"

---

## Phase 4: Deliver

After user approval, complete these steps:

**Step 1:** Determine the output path.

Default filename: `[company-name]-[topic-keyword]-press-release.md`

If the user specified a path, use that. Otherwise, write to the current working directory.

**Step 2:** Write the file using the Write tool.

**Step 3:** Confirm delivery. Report: "Your press release has been saved to [file path]. The document is [X] words and includes [headline summary]."

**Step 4:** Suggest distribution channels based on the release type:

| Release Type | Recommended Channels |
|-------------|---------------------|
| Product Launch | PR Newswire or Business Wire, industry trade publications, product review blogs, LinkedIn company page |
| Funding/Milestone | TechCrunch / Crunchbase News submission, local business journal, LinkedIn post by founder |
| Partnership | Both companies' newsrooms, shared LinkedIn announcements, industry trade press |
| Hire/Promotion | Local business journal "People on the Move" section, LinkedIn, industry associations |
| Event | Local newspaper event calendars, community Facebook groups, Eventbrite, industry newsletters |
| Award | Award-granting organization's press list, local media, industry trade publications |

**Step 5:** Offer next steps: "Would you like me to write a pitch email to send to journalists alongside this release?"

---

## Example 1: SaaS Startup Announces $2M Seed Round

**Brief:**
- Release type: Funding/Milestone
- The news: Greenline Analytics raises $2M seed round to expand AI-powered inventory forecasting for independent retailers
- Company: Greenline Analytics, Denver, CO, founded 2023
- Key person: Jordan Reeves, Founder and CEO
- Quote attribution: Jordan Reeves + investor quote (Priya Nair, Partner, Foothills Ventures)
- Why it matters: 70% of independent retailers still forecast inventory manually, leading to 8% average revenue loss from stockouts and overstock
- Supporting details: Led by Foothills Ventures with participation from Range Capital and three angel investors; funds will go toward engineering hires and retail integrations; currently 200 paying customers
- Media contact: Jordan Reeves, press@greenlineanalytics.com, (720) 555-0198

**Full press release:**

**FOR IMMEDIATE RELEASE**

# Greenline Analytics Raises $2M Seed Round to Bring AI Inventory Forecasting to Independent Retailers

**DENVER, Colo.** -- Greenline Analytics, a software company that builds AI-powered inventory tools for independent retailers, has raised $2 million in seed funding led by Foothills Ventures with participation from Range Capital and three angel investors.

The funding will accelerate Greenline's engineering team and expand integrations with point-of-sale systems used by small and mid-size retailers. Independent retailers represent more than 40% of U.S. retail storefronts, yet 70% still forecast inventory using spreadsheets or gut instinct -- leading to an average 8% revenue loss from stockouts and excess stock.

"Independent retailers are competing against chains with billion-dollar supply chain budgets, and they are doing it with a spreadsheet," said Jordan Reeves, founder and CEO of Greenline Analytics. "This funding lets us put enterprise-grade forecasting into the hands of a shop owner for less than the cost of one wasted pallet."

Greenline's platform analyzes sales velocity, seasonal patterns, and supplier lead times to generate automated reorder recommendations. The product integrates with Shopify POS and Square, with plans to add Clover and Lightspeed by year-end. The company currently serves 200 paying retail customers across 34 states.

"Jordan's team has built something that solves a real, measurable problem for a market that has been underserved by enterprise software," said Priya Nair, partner at Foothills Ventures. "The early traction speaks for itself."

Retailers interested in Greenline Analytics can start a free 30-day trial at www.greenlineanalytics.com.

### About Greenline Analytics

Greenline Analytics builds AI-powered inventory forecasting software for independent retailers. Founded in 2023 and headquartered in Denver, Colo., the company helps small and mid-size retailers reduce waste, prevent stockouts, and make data-driven purchasing decisions. Learn more at www.greenlineanalytics.com.

### Media Contact

Jordan Reeves
Founder and CEO
Greenline Analytics
press@greenlineanalytics.com
(720) 555-0198

###

---

## Example 2: Local Bakery Opens Second Location

**Brief:**
- Release type: Event (grand opening)
- The news: Sweet Crumb Bakery opens second location in Riverside with a community grand opening event
- Company: Sweet Crumb Bakery, Portland, OR, founded 2019
- Key person: Lisa Martinez, Owner
- Quote attribution: Lisa Martinez
- Why it matters: Sweet Crumb grew from a weekend farmers market stand to a neighborhood staple; second location brings jobs and a community gathering space to the Riverside district
- Supporting details: Grand opening on April 5, first 100 customers get a free pastry box, new location is 2,400 sq ft with a coffee bar and event space, creating 12 new jobs
- Media contact: Lisa Martinez, lisa@sweetcrumbbakery.com, (503) 555-0147

**Full press release:**

**FOR IMMEDIATE RELEASE**

# Sweet Crumb Bakery Opens Second Location in Portland's Riverside District

New 2,400-square-foot bakery and coffee bar creates 12 jobs and adds community event space

**PORTLAND, Ore.** -- Sweet Crumb Bakery, a from-scratch bakery known for its sourdough breads and seasonal pastries, will open its second Portland location in the Riverside district on April 5. The grand opening celebration runs from 7 a.m. to 3 p.m., and the first 100 customers will receive a complimentary pastry box.

The new location at 842 Riverside Ave. spans 2,400 square feet and features a full coffee bar, expanded pastry cases, and a reservable event space for community gatherings, birthday parties, and small workshops. The expansion creates 12 new full-time and part-time positions, all filled by local hires from the Riverside neighborhood.

"We started as a folding table at the Hawthorne farmers market in 2019, and the fact that we are opening a second location still does not feel real," said Lisa Martinez, owner of Sweet Crumb Bakery. "Riverside has been asking for a neighborhood bakery, and we want this space to be more than a shop -- it is a place where people sit down, slow down, and know their baker by name."

The Riverside location will carry Sweet Crumb's full menu of sourdough loaves, croissants, cinnamon rolls, and seasonal specialties, along with espresso drinks, drip coffee, and a rotating selection of local teas. Hours will be Tuesday through Sunday, 7 a.m. to 4 p.m.

Grand opening visitors can expect live music from Portland acoustic duo River Pine, free samples throughout the day, and a "name our house blend" contest for the new coffee bar.

### About Sweet Crumb Bakery

Sweet Crumb Bakery is a from-scratch bakery in Portland, Ore., specializing in sourdough breads, pastries, and seasonal baked goods. Founded in 2019 by Lisa Martinez, Sweet Crumb operates two locations and sources ingredients from Pacific Northwest farms and mills. Visit www.sweetcrumbbakery.com.

### Media Contact

Lisa Martinez
Owner
Sweet Crumb Bakery
lisa@sweetcrumbbakery.com
(503) 555-0147

###

---

## Anti-Patterns

**NEVER do these when writing a press release:**

- **DO NOT use marketing superlatives.** "Revolutionary," "game-changing," "world-class," "best-in-class," and "cutting-edge" are advertising words, not news words. Journalists delete releases that read like ads. Say what the product does; let the journalist decide if it is revolutionary.
- **DO NOT bury the news.** The announcement must appear in the first sentence of the lead paragraph. If a journalist has to read three paragraphs to find out what happened, they will not read three paragraphs.
- **DO NOT write quotes no human would say.** "We are thrilled to leverage our synergistic capabilities to disrupt the paradigm" is not something a person says. Read the quote out loud. If it sounds like a corporate chatbot, rewrite it.
- **DO NOT skip the boilerplate.** Journalists use the boilerplate to fact-check your company description. Without it, they either make something up or skip your release.
- **DO NOT skip the media contact.** A press release without contact information is a dead end. Journalists on deadline need a phone number and an email.
- **DO NOT use exclamation marks.** Not in the headline, not in the body, not in the quotes. Press releases are factual documents. Excitement is conveyed through the news itself, not punctuation.
- **DO NOT include an Oxford comma.** AP style omits the serial comma: "red, white and blue" not "red, white, and blue." This is a common error that signals the writer does not know press release conventions.
- **DO NOT exceed 600 words.** Wire services and journalist inboxes have attention limits. A press release is not a white paper. Cut details that a journalist would not include in a 300-word article.
- **DO NOT use first person.** Press releases are written in third person. "We are excited" becomes "[Company Name] announced." The only first person allowed is inside a direct quote.
- **DO NOT send without proofreading names and titles.** Misspelling the CEO's name or getting a job title wrong is an instant credibility killer with media contacts.

---

## Recovery

### User Cannot Articulate the News

If the user struggles to state what the announcement is:
1. Ask: "If a journalist wrote one sentence about your company tomorrow, what would it say?"
2. If still unclear, ask: "What changed? A new product? A new number? A new person? A new relationship?"
3. If after 3 attempts the news remains vague: "A press release needs a concrete, specific piece of news. 'We are doing great things' is not a press release -- 'We hired a former Nike VP as our new COO' is. Can you identify a specific fact or event we can anchor this around?"

### No Quotable Person Available

If the user says nobody wants to be quoted:
1. Explain: "Every press release needs at least one attributed quote. It gives journalists a human voice to include in their coverage."
2. Suggest: "The quote does not need to be crafted by the person -- I will write it and they just need to approve it. Who is the most senior person connected to this announcement?"
3. If the user truly cannot identify anyone: write the release with a placeholder attribution ("[SPOKESPERSON NAME], [TITLE]") and flag it: "You will need to fill in the quote attribution before distributing."

### No Boilerplate Exists

If the company has never written an "About" paragraph:
1. Ask for three inputs: "What does your company do in one sentence? Who are your customers? Where are you based?"
2. Write the boilerplate from those answers. Keep it to 2-3 sentences with no superlatives.
3. Tell the user: "I have written your company boilerplate. Save this -- you will reuse it on every press release, your website About page, and speaker bios."

### User Wants to Announce Something That Is Not News

If the announcement lacks a concrete news hook (e.g., "We want to announce that we exist" or "We updated our website"):
1. Be direct: "Journalists receive hundreds of releases a day. They publish stories with a clear news hook -- a launch date, a number, a name, or a milestone. Can we tie this to something specific?"
2. Suggest framing: "Instead of 'we updated our website,' could we angle this as 'Company X launches new e-commerce platform, expects to increase online sales by 30%'? The data point makes it newsworthy."
3. If no news hook can be found: "This announcement may be better suited for a blog post or social media update rather than a press release. Would you like me to help with one of those instead?"

### File Write Fails

If the Write tool fails:
1. Report the error to the user.
2. Present the complete press release as formatted text in the chat so the user can copy it manually.
3. Offer to retry with a different file path.
4. **If 3 write attempts fail, stop attempting and present the release in chat.** Tell the user: "I was unable to save the file. The complete press release is above -- you can copy it directly."

---

## Pre-Delivery Checklist

Before delivering the final press release, verify:

- [ ] "FOR IMMEDIATE RELEASE" or embargo notice appears at the top
- [ ] Headline starts with an action verb and contains the company name
- [ ] Headline is under 80 characters and in title case
- [ ] Dateline uses correct AP state abbreviation format
- [ ] Lead paragraph answers who, what, when, where, and why
- [ ] At least one attributed quote using "said" (not "stated" or "shared")
- [ ] Quote sounds like something the attributed person would actually say out loud
- [ ] Body paragraphs include specific details (numbers, dates, features, pricing)
- [ ] Boilerplate paragraph describes the company without superlatives
- [ ] Boilerplate ends with the company website URL
- [ ] Media contact includes name, email, and phone number
- [ ] End marker (###) is present
- [ ] Total word count is 400-600
- [ ] No marketing language ("revolutionary," "game-changing," "cutting-edge")
- [ ] No exclamation marks anywhere in the document
- [ ] No Oxford commas (AP style)
- [ ] No first-person language outside of direct quotes
- [ ] Numbers under 10 are spelled out; 10 and above use numerals
- [ ] Company names and person names are spelled correctly throughout
- [ ] All dates use AP format (March 15, not March 15th)
