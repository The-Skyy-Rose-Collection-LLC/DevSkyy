# No Built-In Production PRD

The source archive's bundled PRD was intentionally removed from executable use.
It contained stale SkyyRose product facts, retired fonts, generic glass/gradient/
orb defaults, animation-everywhere guidance, and unapproved image-provider rules.

Use the repository's current brand canon, SOT, design-system contract, and a
founder-approved task PRD. Pass that file explicitly to `run.py --prd`.

The runtime is planning-only by default. Provider execution additionally
requires `--execute --approved-paid-providers --routing <approved.json>`.
