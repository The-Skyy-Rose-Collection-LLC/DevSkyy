---
name: microcopy-writer
description: "Writes UX microcopy for buttons, tooltips, error messages, empty states, and onboarding flows. Use when you need clear, human interface text that guides users through your product."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Microcopy Writer

## When to Use This Skill

Use this skill when you need to:
- Write button labels, form fields, tooltips, and error messages
- Create onboarding flow copy that guides new users
- Write empty state messages that encourage action
- Produce confirmation, success, and loading state copy

**DO NOT** use this skill for marketing copy, landing pages, or long-form content. This is for in-product interface text only.

---

## Core Principle

MICROCOPY MUST BE INVISIBLE WHEN THINGS GO RIGHT AND HELPFUL WHEN THINGS GO WRONG — THE BEST INTERFACE TEXT IS THE TEXT THE USER BARELY NOTICES.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Product / app** | "What product or app is this microcopy for?" | No default — must be provided |
| **Copy type** | "What do you need? Buttons, errors, onboarding, empty states, tooltips, or all?" | All types |
| **Brand voice** | "How should the product sound? Friendly, professional, playful, minimal?" | Friendly and clear |
| **Target user** | "Who is using this product?" | Non-technical users |
| **Specific screens** | "Which screens or flows need copy?" | User will describe or list |

**GATE: Confirm scope and voice before writing.**

---

## Phase 2: Outline

### Microcopy Categories

```
1. Buttons & CTAs — action labels throughout the product
2. Form Labels & Help Text — field names, placeholders, validation
3. Error Messages — what went wrong and how to fix it
4. Empty States — what to show when there is no data
5. Success Messages — confirmations and celebrations
6. Onboarding — first-time user guidance
7. Tooltips & Help Text — contextual explanations
8. Loading & Wait States — progress and patience copy
```

**GATE: Confirm which categories to cover.**

---

## Phase 3: Write

### Buttons & CTAs

```
## Button Copy Rules

- Use verbs: "Save changes" not "OK"
- Be specific: "Send invoice" not "Submit"
- Match the user's mental model: "Create account" not "Register"
- Primary action: bold, active verb. Secondary: softer ("Cancel" / "Go back")

| Screen | Primary Button | Secondary Button |
|--------|---------------|-----------------|
| [Screen name] | [Label] | [Label] |
| Sign-up | Create my account | Already have an account? Log in |
| Checkout | Place my order | Continue shopping |
| Settings | Save changes | Discard changes |
```

### Error Messages

Every error message follows this formula: **What happened + Why + How to fix it**

```
## Error Message Template

**What happened:** [Plain language — no error codes]
**Why (if helpful):** [Brief explanation]
**How to fix it:** [Specific action the user can take]

### Examples

| Error | Bad | Good |
|-------|-----|------|
| Wrong password | "Error: Authentication failed" | "That password didn't work. Try again or reset it." |
| Empty required field | "Error: Field required" | "Add your email address to continue." |
| Server error | "500 Internal Server Error" | "Something went wrong on our end. Try again in a minute." |
| File too large | "Error: File exceeds limit" | "That file is too large. Max size is 10MB — try compressing it first." |
```

### Empty States

```
## Empty State Template

**Headline:** [What this section will contain]
**Description:** [Why it is empty and what to do]
**CTA:** [Action to fill it]

### Examples

| Screen | Headline | Description | CTA |
|--------|----------|-------------|-----|
| No invoices | "No invoices yet" | "Create your first invoice and get paid faster." | "Create invoice" |
| No projects | "Your project list is empty" | "Start a project to track your work and deadlines." | "New project" |
| Empty search | "No results for '[query]'" | "Try a different search term or check your spelling." | "Clear search" |
```

### Onboarding Flow

```
## Onboarding Copy

**Step 1: Welcome**
Headline: "Welcome to [Product], [Name]!"
Body: "[One sentence about what the product does for them]"
CTA: "Let's get started"

**Step 2: [First key action]**
Headline: "[Action-oriented instruction]"
Body: "[Why this step matters — 1 sentence]"
CTA: "[Specific action]"

**Step 3: [Second key action]**
...

**Completion:**
Headline: "You're all set!"
Body: "[What they can do now — 1 sentence]"
CTA: "[Primary action in the product]"
```

### Tooltips

```
## Tooltip Rules

- Under 20 words
- Answer "What is this?" or "Why should I care?"
- No jargon — explain like the user is seeing this for the first time

| Element | Tooltip |
|---------|---------|
| [Feature name] | "[Plain explanation of what it does]" |
| [Setting toggle] | "[What happens when this is on/off]" |
```

---

## Phase 4: Polish

### 1. Microcopy Checklist

```
## Quality Checklist

- [ ] Every button uses an active verb
- [ ] Error messages explain what happened AND how to fix it
- [ ] Empty states encourage action (not just state "nothing here")
- [ ] Onboarding flow is 3-5 steps maximum
- [ ] Tooltips are under 20 words each
- [ ] Tone is consistent across all copy
- [ ] No technical jargon unless the audience is technical
- [ ] Copy reads naturally when spoken aloud
- [ ] Success messages feel rewarding, not robotic
- [ ] All copy is concise — every word earns its place
```

### 2. Voice Consistency Check

Review all microcopy together and flag any tonal inconsistencies.

---

## Example: Invoice App Microcopy

```
Buttons: "Create invoice" / "Send to client" / "Mark as paid"
Error: "We couldn't send that invoice. Check the client's email address and try again."
Empty state: "No invoices yet — create your first one and get paid faster."
Onboarding: "Welcome! Let's set up your business details so your invoices look professional."
Tooltip (due date field): "When payment is due. Most freelancers use Net 15 or Net 30."
```

---

## Anti-Patterns

- **Technical error codes** — "Error 403: Forbidden" means nothing to users. Translate to plain language.
- **Vague buttons** — "Submit," "OK," and "Continue" tell the user nothing about what happens next.
- **Blaming the user** — "You entered an invalid email" feels accusatory. "That email address doesn't look right — check for typos" is better.
- **Empty empty states** — a blank screen with no guidance is a dead end. Always tell the user what to do.
- **Inconsistent tone** — playful onboarding followed by robotic error messages feels broken. Match tone across all states.
- **Too clever** — "Oopsie! Something went boom!" is cute once and annoying forever. Be clear before being clever.

---

## Recovery

- **No product screens to reference:** Ask the user to describe the key flows and screens in plain language. Write copy based on the described user journey.
- **Voice is undefined:** Write 3 versions of the same error message in different tones (professional, friendly, playful). Let the user pick.
- **Too many screens to cover:** Prioritize the 5 most critical user flows. Cover those first, then expand.
- **Copy needs to be bilingual:** Write the primary language first, then note cultural considerations for translation.
