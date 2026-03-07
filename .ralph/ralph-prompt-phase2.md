# Phase 2: Site Rebuild + Scene Generation

You are Ralph. Read these files FIRST — they are your full directive and task list:

1. `.ralph/ralph-directive.md` — scroll to **"NEW MISSION: Phase 2"** section at the bottom
2. `.ralph/ralph-tasks.md` — scroll to **"PHASE 2: Site Rebuild + Immersive Scene Generation"** section at the bottom

## Rules

- **Context7 HARD GATE**: `resolve-library-id` → `query-docs` BEFORE writing any code
- **Update `.ralph/ralph-tasks.md`** after EVERY iteration — mark `[x]`/`[/]`/`[ ]` + add notes
- **NEVER delete** `.ralph/ralph-context.md` or `.ralph/ralph-tasks.md`
- Immersive templates ARE in scope — you may edit them

## Task Order

1. Regenerate stale `.min.css` / `.min.js` files
2. Create `template-experiences.php` (fixes `/experiences/` 404)
3. Create `template-collections.php` (fixes `/collections/` 404)
4. Deduplicate `homepage.css` & `collection-v4.css`
5. Fix mobile nav two-tap dropdown behavior
6. Generate 3 immersive scenes via `scripts/gemini_scene_gen.py` (use `.venv-imagery`)

## Brand Constants

- Colors: Rose Gold `#B76E79`, Dark `#0A0A0A`, Silver `#C0C0C0`, Crimson `#DC143C`, Gold `#D4AF37`
- Tagline: "Luxury Grows from Concrete." (NEVER "Where Love Meets Luxury")
- API: `index.php?rest_route=` (NOT `/wp-json/`)

Output <promise>COMPLETE</promise> when all 6 tasks + verification are done.
