---
name: tutorial-writer
description: Creates step-by-step tutorials with screenshot placeholders, code snippets, and troubleshooting sections. Use this skill when a user needs to write a how-to guide, help documentation, onboarding walkthrough, or educational tutorial for their product, tool, or process.
allowed-tools: Read Grep Glob Bash(ls:*) Write Edit
---

# Tutorial Writer

## When to Use This Skill

- User needs a how-to guide for their product or tool
- User wants to create help documentation or a knowledge base article
- User is building an onboarding walkthrough for new customers
- User needs a technical tutorial with code examples
- User wants to document a process with clear visual references
- User asks for educational content with step-by-step instructions

## Core Principle

EVERY STEP MUST PASS THE "CAN I DO THIS RIGHT NOW?" TEST — IF A READER CANNOT TAKE IMMEDIATE ACTION FROM A STEP, THE STEP IS TOO VAGUE.

## Workflow

### Phase 1: Scope the Tutorial

1. Identify the tutorial topic and target reader skill level (beginner, intermediate, advanced)
2. Define the single outcome the reader will achieve by the end
3. List prerequisites the reader needs before starting
4. Estimate completion time for the full tutorial

Ask the user:
- What is the reader trying to accomplish?
- What do they already know coming in?
- What tool/platform/language is involved?

### Phase 2: Outline the Steps

5. Break the process into 5-12 major steps (fewer for beginners, more granularity is fine for advanced)
6. Order steps chronologically — never jump ahead or reference future steps
7. Identify where screenshots or visuals would help (mark with `[SCREENSHOT: description]`)
8. Note any decision points where the reader might take different paths

### Phase 3: Write Each Step

9. Write each step using this structure:
   - **Step title** as a heading (action verb + object)
   - One sentence explaining WHY this step matters
   - Numbered sub-steps with exact UI paths or commands
   - Screenshot placeholder where the reader needs visual confirmation
   - Expected result after completing the step
   - Common mistake callout if applicable

10. For code snippets, always include:
    - The complete code block (not fragments)
    - Language identifier on the code fence
    - Inline comments explaining non-obvious lines
    - Expected output or result

### Phase 4: Add Troubleshooting

11. Create a "Troubleshooting" section at the end covering:
    - 3-5 most common errors or confusion points
    - Exact error messages the reader might see
    - Step-by-step fix for each issue
    - "If this doesn't work" escalation path

12. Add a "What's Next" section linking to logical follow-up tutorials or resources

### Phase 5: Format and Polish

13. Add a title, estimated time, difficulty level, and prerequisites at the top
14. Ensure every screenshot placeholder has a descriptive label
15. Add tip/warning/note callouts using blockquote formatting
16. Review for jargon — replace or define any term a beginner wouldn't know

## Output Format

```markdown
# How to [Achieve Specific Outcome]

**Difficulty:** Beginner | Intermediate | Advanced
**Time:** X minutes
**Prerequisites:** [List what's needed]

---

## Step 1: [Action Verb] + [Object]

Why this matters: [one sentence].

1. Go to **Settings > Account > API Keys**
2. Click **Generate New Key**
3. Name your key `production-api`

[SCREENSHOT: The API Keys panel showing the Generate New Key button]

**Expected result:** You see a new key starting with `sk-` in your key list.

> **Common mistake:** Don't copy the key ID — copy the full key value that starts with `sk-`.

---

## Troubleshooting

### "Invalid API Key" error
1. Confirm you copied the full key (starts with `sk-`)
2. Check there are no trailing spaces
3. Regenerate the key if the issue persists

---

## What's Next
- [Link to next tutorial]
```

## Example 1: Setting Up Stripe Payments in Shopify

**Input:** "Write a tutorial for adding Stripe to a Shopify store"

**Output:**

# How to Connect Stripe Payments to Your Shopify Store

**Difficulty:** Beginner
**Time:** 15 minutes
**Prerequisites:** Active Shopify store, Stripe account (free to create)

---

## Step 1: Create Your Stripe Account

Why this matters: Stripe processes your credit card payments and deposits funds to your bank.

1. Go to [stripe.com](https://stripe.com) and click **Start now**
2. Enter your email, full name, and create a password
3. Click **Create account**

[SCREENSHOT: Stripe signup page with the three fields highlighted]

**Expected result:** You land on the Stripe Dashboard with a banner saying "Welcome to Stripe."

---

## Step 2: Activate Stripe in Shopify

Why this matters: This links your Stripe account to your store so payments flow correctly.

1. In Shopify admin, go to **Settings > Payments**
2. Under "Payment providers," click **Choose a provider**
3. Select **Stripe** from the list
4. Click **Activate Stripe**
5. Log in with your Stripe credentials when prompted

[SCREENSHOT: Shopify Payments settings page with Stripe listed under providers]

**Expected result:** Stripe appears as your active payment provider with a green "Active" badge.

> **Warning:** If you already have Shopify Payments active, you must deactivate it first. Go to **Settings > Payments > Manage > Deactivate Shopify Payments**.

---

## Step 3: Run a Test Transaction

Why this matters: Confirms payments actually work before real customers try to buy.

1. In Stripe Dashboard, toggle **Test mode** (top right)
2. In Shopify, go to **Settings > Payments > Manage**
3. Check **Enable test mode**
4. Place an order on your store using test card `4242 4242 4242 4242`, any future expiration, any CVC
5. Confirm the order appears in Stripe Dashboard under **Payments**

[SCREENSHOT: Stripe Dashboard showing the test payment with "Succeeded" status]

**Expected result:** The test payment shows "Succeeded" in Stripe and the order appears in Shopify.

> **Tip:** Always disable test mode before going live. Real customers cannot pay while test mode is on.

---

## Troubleshooting

### "Connection failed" when activating Stripe
1. Clear your browser cache and cookies
2. Try in an incognito/private browser window
3. Ensure your Stripe account email matches your login
4. If the issue persists, contact Shopify support at **Help > Contact Support**

### Test payment shows "Failed"
1. Confirm you used test card number `4242 4242 4242 4242`
2. Ensure test mode is enabled in BOTH Stripe and Shopify
3. Check that the expiration date is in the future

### Payments not appearing in bank account
1. Stripe holds first payouts for 7-14 days (normal for new accounts)
2. Go to **Stripe Dashboard > Payouts** to see your payout schedule
3. Ensure your bank account is verified under **Settings > Bank accounts**

---

## What's Next
- Set up automatic tax calculation in Shopify
- Configure shipping rates for your store
- Create your first discount code

## Example 2: Creating a Mailchimp Email Automation

**Input:** "Tutorial for setting up a welcome email sequence in Mailchimp"

**Output:**

# How to Create a Welcome Email Sequence in Mailchimp

**Difficulty:** Intermediate
**Time:** 30 minutes
**Prerequisites:** Mailchimp account (Standard plan or higher), at least one audience/list

---

## Step 1: Navigate to Automations

1. Log in to Mailchimp and click **Automations** in the left sidebar
2. Click **Create Automation**
3. Select **Welcome new subscribers**
4. Choose your audience from the dropdown
5. Click **Begin**

[SCREENSHOT: Mailchimp automation builder showing the "Welcome new subscribers" template selected]

**Expected result:** You see the automation builder with one email pre-loaded.

---

## Step 2: Configure Email 1 — The Instant Welcome

1. Click on **Email 1** in the automation flow
2. Set the trigger to **Immediately** after signup
3. Set the subject line: `Welcome to the crew — here's what to expect`
4. Click **Design Email** and choose a template
5. Write your welcome content: introduce yourself, set expectations for email frequency, deliver any promised lead magnet
6. Click **Save and Continue**

[SCREENSHOT: Email editor with subject line and body content filled in]

**Expected result:** Email 1 shows a green checkmark in the automation flow.

---

## Step 3: Add Email 2 — The Value Email (Day 3)

1. Click **Add Email** below Email 1
2. Set the delay to **3 days** after the previous email
3. Subject line: `The #1 mistake I see new store owners make`
4. Write content that delivers genuine value — a tip, framework, or resource
5. Click **Save and Continue**

[SCREENSHOT: Delay settings showing "3 days after previous email"]

---

## Step 4: Add Email 3 — The Soft Ask (Day 7)

1. Click **Add Email** below Email 2
2. Set the delay to **4 days** after the previous email
3. Subject line: `Quick question for you`
4. Write content that invites a reply or introduces your product/service naturally
5. Click **Save and Continue**

---

## Step 5: Activate the Automation

1. Review all three emails in the flow view
2. Click **Start Sending** in the top right
3. Confirm in the popup dialog

> **Warning:** Once activated, you cannot reorder emails. You can edit content and pause individual emails, but the sequence order is locked.

[SCREENSHOT: Completed automation flow showing all three emails with green checkmarks]

**Expected result:** The automation status changes to "Sending" and new subscribers will receive the sequence.

---

## Troubleshooting

### Subscribers not receiving the welcome email
1. Check if the automation is set to "Sending" (not "Paused")
2. Verify the subscriber joined the correct audience
3. Go to **Audience > All contacts** and check if the contact shows as "Subscribed" (not "Cleaned" or "Unsubscribed")

### Emails landing in spam
1. Authenticate your domain: go to **Website > Domains > Authenticate**
2. Remove spam trigger words from subject lines (FREE, ACT NOW, etc.)
3. Ensure you have a physical mailing address in your email footer

### Cannot add more than 3 emails
1. Confirm you are on Mailchimp Standard plan or higher
2. Free and Essentials plans limit automation emails

---

## What's Next
- Set up abandoned cart email automation
- Create a re-engagement sequence for inactive subscribers
- Build a post-purchase follow-up automation

## Recovery and Fallback

- If the user's topic is too broad, narrow it: "Let's focus on just the setup portion first. We can create a separate tutorial for advanced configuration."
- If the process has more than 15 steps, split into a multi-part series with clear links between parts
- If the user cannot provide screenshots, describe the exact UI location in text: "the blue button labeled 'Save' in the top-right corner of the page"
- If the user's tool has no public documentation, ask for a screen recording or live walkthrough to extract the steps
- After 3 failed attempts to clarify the process, stop and say: "I need more context about how this feature works. Can you walk me through it once so I can document it?"

## Constraints

- **NEVER** skip the troubleshooting section — every tutorial must have at least 3 common issues
- **NEVER** use vague instructions like "configure the settings" — name every button, field, and menu path
- **NEVER** assume the reader knows keyboard shortcuts — always provide the menu path first
- Keep each step to ONE action — if you write "and then," it should be two steps
- Screenshot placeholders must describe WHAT the reader should see, not just WHERE to look
- All code blocks must include the language identifier for syntax highlighting
- Do not exceed 20 major steps — split into multiple tutorials if needed
- Total output must stay under 500 lines
