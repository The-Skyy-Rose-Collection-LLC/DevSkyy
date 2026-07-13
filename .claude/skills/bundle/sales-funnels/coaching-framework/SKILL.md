---
name: coaching-framework
description: Builds systematized coaching session structures with intake forms, session agendas, progress tracking frameworks, and client communication templates. Use when a coach, consultant, or service provider wants to systematize their 1-on-1 client work, create a repeatable coaching process, or professionalize their client experience.
allowed-tools: Read Write Bash(mkdir:*)
---

# Coaching Framework

## When to Use This Skill

- User is a coach, consultant, or service provider doing 1-on-1 client work
- User says "systematize my coaching" or "create a coaching program" or "client process"
- User wants to stop winging sessions and create a repeatable structure
- User is onboarding new clients and needs intake/kickoff templates
- User wants to track client progress across multiple sessions

## Core Principle

A COACHING FRAMEWORK IS NOT A CURRICULUM — IT IS A REPEATABLE CONTAINER. The content changes per client; the structure stays the same every time.

## Workflow

### Phase 1: Define the Coaching Container

Gather from the user:

1. **Niche** — Who do they coach? (e.g., career changers, new managers, health clients)
2. **Engagement length** — How many sessions? Over what period? (default: 6 sessions over 12 weeks)
3. **Session format** — Duration, frequency, video/phone/in-person
4. **Desired outcome** — What transformation does the client achieve by the end?
5. **Current pain** — What is broken in their current process? (winging it, no tracking, clients ghosting)

### Phase 2: Build the Intake System

Create an intake process with three components:

**1. Pre-Engagement Questionnaire (sent before first session)**

Must include:
- Current situation (where they are now)
- Desired outcome (where they want to be)
- Timeline and urgency
- Previous attempts to solve this
- Commitment level and potential obstacles
- Communication preferences
- How they will measure success

**2. Welcome Package (sent after booking)**

Must include:
- What to expect from the engagement
- Session logistics (scheduling, rescheduling, cancellation policy)
- How to prepare for each session
- Communication boundaries (response times, between-session support)
- Confidentiality agreement

**3. Kickoff Session Agenda (first session)**

Must follow this structure:
- Review questionnaire answers (10 min)
- Clarify and deepen the goal (15 min)
- Identify top 3 obstacles (10 min)
- Set milestone markers for the engagement (10 min)
- Agree on accountability structure (5 min)
- Assign first action item (5 min)
- Confirm next session logistics (5 min)

### Phase 3: Design the Session Template

Create a repeatable session agenda:

```
STANDARD SESSION TEMPLATE (60 minutes)
======================================

OPENING: Check-In (5 min)
- "What's happened since our last session?"
- "Did you complete your action item? What did you learn?"
- Rate current state 1-10

REVIEW: Progress Against Milestones (10 min)
- Reference milestone tracker
- Celebrate wins explicitly
- Note any stalls or regression

CORE: Session Focus (30 min)
- Client sets the topic: "What would make today most valuable?"
- Use coaching methodology (see framework options below)
- Stay in questions, not advice, for first 20 min
- Offer frameworks/tools only after client has explored

PLANNING: Action Items (10 min)
- One primary action item (specific, measurable, time-bound)
- One stretch goal (optional but encouraged)
- Identify potential obstacles and pre-solve

CLOSE: Reflection (5 min)
- "What's your biggest takeaway today?"
- Confirm next session date
- Note any between-session support needed
```

**Coaching methodology options (pick one default):**

| Method | Best For | Core Move |
|--------|----------|-----------|
| **GROW** | Goal-oriented clients | Goal > Reality > Options > Will |
| **Solution-Focused** | Clients stuck in problems | Scale questions, miracle question, exceptions |
| **Accountability** | Clients who know what to do but don't do it | Commitments, check-ins, consequence setting |
| **Exploratory** | Clients who don't know what they want | Open questions, reflective listening, reframing |

Default to GROW unless the user specifies otherwise.

### Phase 4: Build Progress Tracking

Create a tracking system with:

**Client Milestone Tracker:**
```
CLIENT: [Name]
ENGAGEMENT: [Start Date] - [End Date]
TRANSFORMATION GOAL: [One sentence]

Session | Date       | Focus Topic           | Action Item          | Status    | Notes
--------|------------|----------------------|---------------------|-----------|------
Kickoff | 2026-01-15 | Goal setting          | Define 90-day target | Completed | Strong clarity
2       | 2026-01-29 | Obstacle mapping      | Talk to 3 mentors    | Completed | Found mentor
3       | 2026-02-12 | Strategy development  | Draft action plan    | Partial   | Needs review
4       | 2026-02-26 | Implementation review | Execute phase 1      | Pending   | —
5       | 2026-03-12 | Mid-point assessment  | Adjust plan          | —         | —
6       | 2026-03-26 | Wrap-up + next steps  | 90-day solo plan     | —         | —

MILESTONE MARKERS:
[ ] Milestone 1 by Session 2: Clear goal with measurable target
[ ] Milestone 2 by Session 4: Strategy tested and refined
[ ] Milestone 3 by Session 6: Outcome achieved or clear path forward
```

**Progress Indicators:**
- Client self-rating (1-10) at each session start
- Action item completion rate
- Milestone achievement
- Client's own words about their progress (direct quotes)

### Phase 5: Create Between-Session and Close-Out Materials

**Between-session check-in template (email/message):**
```
Subject: Quick check-in — how's [action item] going?

Hi [Name],

Just checking in on your action item from our last session:
[Specific action item]

Quick questions:
1. Have you started? If yes, what's working?
2. If not, what's getting in the way?
3. Anything you want to flag for our next session on [date]?

No pressure to reply at length — even a one-liner helps me prepare.

[Coach name]
```

**End-of-engagement package:**
- Progress summary with milestones achieved
- Client's growth trajectory (session 1 state vs final state)
- Recommendations for continued development
- Testimonial request
- Information about continued/advanced engagement options

## Example 1: Business Coach for Freelancers

**Niche:** Freelance designers and developers transitioning to agency owners
**Engagement:** 8 sessions over 16 weeks, 60 min each, Zoom
**Transformation:** Freelancer hires first subcontractor and lands first $10K+ project

```
INTAKE QUESTIONNAIRE: Freelancer-to-Agency Coaching
====================================================

1. What type of freelance work do you do, and for how long?
2. What's your average monthly revenue over the last 6 months?
3. What's the largest single project you've completed? (dollar value)
4. Have you ever hired a subcontractor or assistant? If yes, what happened?
5. What does "running an agency" look like to you in 12 months?
   - Revenue target:
   - Team size:
   - Types of clients:
   - Your role (still doing client work, or managing):
6. What scares you most about making this transition?
7. What have you already tried? (courses, coaching, books)
8. On a scale of 1-10, how committed are you to making this shift
   in the next 4 months? What would make it a 10?
9. How do you prefer to communicate between sessions?
   (email / Slack / text / don't contact me)
10. How will you know this coaching engagement was worth it?

KICKOFF SESSION AGENDA (Session 1)
===================================
0:00 - 0:10  Review questionnaire — clarify revenue and experience
0:10 - 0:25  Define the 16-week transformation goal using GROW:
             Goal: "I want to hire my first subcontractor and land
                    a $10K+ project by week 16"
             Reality: Current revenue, capacity, pipeline
             Options: Which path — hire first or land project first?
             Will: Commitment level, time available per week
0:25 - 0:35  Identify top 3 obstacles:
             (common: fear of delegation, pricing too low, no SOPs)
0:35 - 0:45  Set 4 milestones across 8 sessions
0:45 - 0:50  Accountability structure: weekly text check-in on Fridays
0:50 - 0:55  Action item: "Write a job description for your first
             subcontractor role by next session. Use the template I'll
             send you."
0:55 - 1:00  Confirm session 2 date, logistics
```

## Example 2: Health Coach for Busy Professionals

**Niche:** Corporate professionals wanting sustainable energy and weight management
**Engagement:** 6 sessions over 12 weeks, 45 min each, phone
**Transformation:** Client establishes 3 sustainable health habits that survive a busy workweek

```
INTAKE QUESTIONNAIRE: Sustainable Energy Coaching
==================================================

1. Describe a typical workday — wake time to bed time.
2. What's your current exercise routine? (frequency, type, duration)
3. Walk me through what you eat on a typical Tuesday.
4. How many hours of sleep do you average? How's the quality?
5. What's your energy like at 10am? At 3pm? At 8pm?
6. What health changes have you tried in the past 2 years?
   What stuck? What didn't? Why?
7. What does "feeling great" look like for you specifically?
8. What are your biggest obstacles to consistency?
   (travel, late meetings, family obligations, stress eating)
9. Are there any medical conditions or dietary restrictions
   I should know about?
10. If we could only change ONE thing in 12 weeks, what would
    make the biggest difference in your daily life?

SESSION TEMPLATE (45 minutes)
==============================
0:00 - 0:05  Check-in: energy level today (1-10), sleep quality
             this week, action item status
0:05 - 0:12  Review habit tracker: what worked, what broke down
0:12 - 0:35  Core coaching (GROW framework):
             - "What felt hardest this week?"
             - "When it did work, what was different?"
             - "What's one small adjustment for next week?"
             Focus: root cause, not symptoms
0:35 - 0:42  Action item: one specific habit change
             (e.g., "Pack lunch on Sunday and Wednesday nights
              using the meal prep template")
0:42 - 0:45  Reflection + confirm next session

PROGRESS TRACKER
=================
Session | Energy (1-10) | Sleep hrs | Habit 1 (exercise) | Habit 2 (meals) | Habit 3 (wind-down)
--------|--------------|-----------|-------------------|----------------|-------------------
1       | 4            | 5.5       | 0/week            | 1 prepped/week | None
2       | 5            | 6.0       | 1/week            | 2 prepped/week | Reading 2x/week
3       | 5            | 6.5       | 2/week            | 3 prepped/week | Reading 3x/week
4       | 6            | 6.5       | 2/week            | 4 prepped/week | Reading 4x/week
5       | 7            | 7.0       | 3/week            | 4 prepped/week | Reading 5x/week
6       | 7            | 7.0       | 3/week            | 5 prepped/week | Nightly routine set
```

## Recovery and Fallback

- If the user has never coached before, start with a 4-session engagement (not 8+) and use the Accountability method instead of GROW
- If the user cannot articulate the transformation, ask: "After your best client engagement ever, what did they say to you? What changed for them?"
- If the client is not completing action items for 2 consecutive sessions, add a mid-week check-in and simplify the action item to one micro-step
- If the engagement stalls at session 3-4 (common), revisit the original goal — it may need to be revised based on new information
- If the user serves multiple niches, build the framework for their most common client type first, then adapt

## Constraints

- **NEVER create a coaching framework without a session template** — the repeatable structure is the whole point
- **ALWAYS include an intake questionnaire** — sessions without context waste time
- **ALWAYS include progress tracking** — if you cannot measure change, you cannot prove value
- **ALWAYS use the GROW framework as default** unless the user specifies otherwise
- Session templates must include minute-by-minute timing
- One coaching methodology per framework (do not mix GROW and Solution-Focused)
- Keep intake questionnaires to 10 questions maximum
- End-of-engagement must include a testimonial request
