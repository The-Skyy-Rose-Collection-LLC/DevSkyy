# Content Repurpose Skill

Turn one piece of content into 5+ platform-ready posts — without writing anything from scratch.

## What It Does

You give it a blog post, transcript, newsletter, or any long-form content. It extracts the core ideas and rewrites them as native content for each platform:

- **X/Twitter** — thread (5-10 tweets with hooks and CTA)
- **LinkedIn** — professional post with engagement question
- **Instagram** — caption with hashtag block
- **Email newsletter** — snippet with subject line and P.S. hook
- **Short-form video** — 30-60 second script with visual cues

Every output sounds native to its platform — not like a copy-paste with minor edits.

## Installation

Copy the `content-repurpose` folder to your Claude Code skills directory:

**Personal (available in all projects):**
```bash
cp -r content-repurpose ~/.claude/skills/content-repurpose
```

**Single project only:**
```bash
cp -r content-repurpose your-project/.claude/skills/content-repurpose
```

After copying, the skill is immediately available — no restart needed.

## How to Use

Open Claude Code and type the slash command:

```
/content-repurpose
```

Then provide your source content in one of three ways:

### Option 1: Paste directly
```
/content-repurpose

Here's my blog post:

The biggest mistake solopreneurs make is trying to be everywhere at once...
```

### Option 2: Point to a file
```
/content-repurpose blog-post.md
```

### Option 3: Give a URL or description
```
/content-repurpose

Repurpose my latest newsletter about pricing strategies. Here's the text: [paste]
```

## What Happens Next

1. **You'll see a "Content Core" summary** — the big idea, supporting points, best quotes, and tactical takeaways extracted from your content. Review this and confirm or adjust before it continues.

2. **You'll get all 5 platform outputs** — each clearly labeled with word/character counts, formatted and ready to post.

3. **You'll get a posting plan** — which platform to post first and a 3-5 day stagger schedule for maximum reach.

## Customizing the Output

Skip platforms you don't need:

```
/content-repurpose

Repurpose this for Twitter and LinkedIn only. Skip everything else.

[your content]
```

Request a platform not included by default:

```
/content-repurpose

Also create a YouTube community post and a Threads post.

[your content]
```

Save outputs to files:

```
/content-repurpose

Save each platform's content to separate files in ./repurposed/

[your content]
```

## Tips for Best Results

- **Longer source content = better outputs.** A 500+ word blog post gives much more to work with than a 3-sentence idea.
- **Mention your audience.** Say "my audience is freelance designers" and the tone/examples will be tailored.
- **Specify your voice.** Say "I write in a casual, direct tone" if the defaults don't match your brand.
- **Provide your best-performing content.** Repurposing proven content beats repurposing untested ideas.
