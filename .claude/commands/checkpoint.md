# Checkpoint Command

Create or verify workflow checkpoints.

## Usage
`/checkpoint [create|verify|list] [name]`

## Create
1. Run `/verify quick`
2. Git stash or commit with name
3. Log to `.claude/checkpoints.log`

## Verify
Compare current state to checkpoint:
- Files changed, Tests diff, Coverage diff, Build status

## Output
```
CHECKPOINT: $NAME
Files: X, Tests: +Y/-Z, Coverage: +X%
Build: [PASS/FAIL]
```

## Arguments
- `create <name>` - Create checkpoint
- `verify <name>` - Compare to checkpoint
- `list` - Show all checkpoints
- `clear` - Remove old (keeps last 5)
