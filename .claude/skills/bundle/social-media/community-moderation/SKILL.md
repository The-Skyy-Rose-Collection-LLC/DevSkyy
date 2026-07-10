---
name: community-moderation
description: "Creates community moderation guidelines with rules, escalation procedures, and automated moderation recommendations. Use when establishing or improving moderation for online communities."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Community Moderation

## When to Use This Skill

Use this skill when you need to:
- Write community rules and moderation guidelines for an online community
- Create escalation procedures for handling violations and conflicts
- Design automated moderation workflows (filters, auto-responses)
- Train moderators with clear guidelines and decision frameworks

**DO NOT** use this skill for community strategy or launch planning (use community-launch skill). This is specifically for moderation systems.

---

## Core Principle

GOOD MODERATION IS INVISIBLE — MEMBERS SHOULD FEEL SAFE AND HEARD WITHOUT NOTICING THE RULES IN ACTION.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Community platform** | "What platform? Discord, Slack, Facebook Group, Circle, Skool?" | No default — must be provided |
| **Community size** | "How many members?" | Under 500 |
| **Community type** | "Free, paid, or course-based?" | Free |
| **Current issues** | "What moderation problems are you facing?" | None yet — building proactively |
| **Moderator count** | "How many moderators (including yourself)?" | 1 (just the founder) |
| **Tone** | "Should moderation be strict, friendly, or minimal?" | Friendly but firm |

**GATE: Confirm brief before building guidelines.**

---

## Phase 2: Outline

```
1. Community Rules — clear, enforceable standards
2. Violation Categories — severity levels and examples
3. Escalation Procedures — step-by-step for each violation level
4. Moderator Guidelines — how moderators should behave and decide
5. Automated Moderation — filters, bots, and auto-responses
6. Appeals Process — how members can contest decisions
```

**GATE: Approve outline before writing.**

---

## Phase 3: Write

### 1. Community Rules

```
## Community Rules

**Rule 1: Be Respectful**
Disagree with ideas, not people. No personal attacks, name-calling, or harassment.

**Rule 2: Add Value**
Share knowledge, ask thoughtful questions, and help others. Low-effort posts ("lol," "same") are discouraged.

**Rule 3: No Spam or Self-Promotion**
Do not drop links to your products, services, or content without context. Share your work when it genuinely answers a question or adds to the discussion.

**Rule 4: Stay On Topic**
Use the right channels for the right discussions. Off-topic posts will be moved or removed.

**Rule 5: No Poaching**
Do not DM members with unsolicited sales pitches, recruitment messages, or service offers.

**Rule 6: Protect Privacy**
Do not share personal information about other members. Do not screenshot private conversations without consent.

**Rule 7: Follow Platform Terms**
All platform-specific rules apply. Violations that break platform TOS may result in immediate removal.
```

### 2. Violation Categories

```
## Violation Severity Levels

| Level | Type | Examples | Action |
|-------|------|----------|--------|
| **Low** | Guideline friction | Off-topic post, low-effort comment, accidental self-promo | Friendly redirect |
| **Medium** | Rule violation | Repeated self-promotion, dismissive/rude comments, ignoring channel rules | Warning + education |
| **High** | Serious violation | Personal attacks, harassment, hate speech, doxxing | Immediate mute + review |
| **Critical** | Zero tolerance | Threats, illegal content, sexual harassment, scams | Immediate ban |
```

### 3. Escalation Procedures

```
## Escalation Playbook

### Low Violations
1. Respond publicly with a friendly redirect: "Hey [Name], this would be a great fit for #[correct-channel]! Mind reposting there?"
2. If repeated: send a private DM explaining the guideline
3. No formal warning unless it continues after DM

### Medium Violations
1. Remove or edit the content
2. Send a private DM: "Hi [Name], I removed your post because [specific rule]. Here's what we'd like to see instead: [guidance]. No hard feelings — just keeping the community valuable for everyone."
3. Log the incident in the moderation log
4. If second offense: formal warning with consequences stated

### High Violations
1. Immediately mute the member (temporary restriction)
2. Remove the offending content
3. Investigate context (was this provoked? is there history?)
4. Senior moderator or founder decides: formal warning, temporary ban, or permanent ban
5. Communicate the decision via DM with clear reasoning

### Critical Violations
1. Immediate permanent ban — no warnings
2. Remove all offending content
3. Report to platform if required (threats, illegal activity)
4. Notify the community only if the incident was public
```

### 4. Moderator Guidelines

```
## How Moderators Should Operate

**Principles:**
- Be fair and consistent — same rules apply to everyone
- Assume good intent first — most violations are accidental
- Be firm but kind — enforce rules without being hostile
- Document everything — log all warnings and bans
- Never moderate when angry — cool down before responding

**Decision Framework:**
1. Is this a rule violation? → If no, leave it.
2. Is this a first offense? → If yes, friendly redirect or DM.
3. Was it intentional or accidental? → Accidents get more grace.
4. Is someone being harmed? → If yes, act immediately.
5. When in doubt, escalate to the founder.

**What moderators should NEVER do:**
- Get into public arguments with members
- Make moderation decisions based on personal dislike
- Share moderation discussions outside the mod team
- Moderate their own conflicts (escalate to another mod)
```

### 5. Automated Moderation

```
## Automation Recommendations

| Tool/Feature | What It Does | Platform |
|-------------|-------------|----------|
| Keyword filter | Auto-flag or remove posts containing banned words | Most platforms |
| Link filter | Hold posts with links for moderator review | Discord, Slack |
| New member slowdown | Restrict posting for new members (first 24-48 hours) | Discord, some forums |
| Auto-welcome | Send onboarding message to new members | Most platforms |
| Report system | Allow members to flag content for moderator review | Most platforms |

**Recommended keyword filters:**
- Obvious slurs and hate speech (platform usually provides defaults)
- Competitor brand names (optional, depends on community)
- Common spam phrases ("DM me for details," "check my bio")
```

### 6. Appeals Process

```
## Member Appeals

If a member believes a moderation action was unfair:
1. DM a moderator (not the one who took the action, if possible)
2. State what happened and why they disagree
3. Moderator team reviews within 48 hours
4. Decision is communicated via DM with reasoning
5. Founder has final say on contested appeals

**Appeals are not available for critical violations (threats, illegal content, harassment).**
```

---

## Phase 4: Polish

### 1. Moderation Checklist

```
## Moderation System Checklist

- [ ] Community rules are written in clear, plain language
- [ ] Violation severity levels are defined with examples
- [ ] Escalation procedures are step-by-step for each level
- [ ] Moderator guidelines include decision framework
- [ ] Automated moderation tools are configured
- [ ] Appeals process is documented
- [ ] Moderation log template is created
- [ ] Rules are posted in a visible, pinned location
```

### 2. Moderation Log Template

```
| Date | Member | Violation | Severity | Action Taken | Moderator | Notes |
|------|--------|-----------|----------|-------------|-----------|-------|
```

---

## Example: Moderation Guidelines for a 200-Person Discord Community

```
Rules: 7 core rules (posted in #rules, accepted on join)
Severity levels: Low (redirect), Medium (warning DM), High (mute + review), Critical (ban)
Automation: Keyword filter for slurs, link hold for new members, auto-welcome DM
Moderators: Founder + 2 community champions
Appeals: DM any mod, 48-hour review window
```

---

## Anti-Patterns

- **No rules posted** — members cannot follow rules they do not know exist. Pin them prominently.
- **Inconsistent enforcement** — applying rules differently based on who the member is destroys trust.
- **Over-moderation** — removing every slightly off-topic post kills spontaneity and makes the community feel sterile.
- **Public arguments with violators** — always handle moderation in DMs. Public confrontations escalate.
- **No documentation** — without a moderation log, repeat offenders slip through and decisions are inconsistent.
- **Moderator burnout** — one person moderating a 500+ community alone will burn out. Recruit help early.

---

## Recovery

- **Community is already toxic:** Post the new rules, announce a fresh start, and enforce consistently from day one. Some members will leave — that is OK.
- **Moderators disagree on decisions:** Create the decision framework above and use it as the standard. The founder has final say on gray areas.
- **Member backlash against a moderation decision:** Share your reasoning (in DMs or publicly if needed) calmly and factually. Stand by fair decisions.
- **Too many violations to handle:** Increase automated moderation, recruit more moderators, and consider whether the community's onboarding is attracting the wrong members.
- **No one to moderate:** Start with automated tools and recruit 1-2 active, trusted members as volunteer moderators with clear guidelines.
