# Deployment catalog replica

`skyyrose-catalog.csv` is a byte-for-byte deployment replica of
`wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv`, which remains
the sole editable SkyyRose catalog SOT. Vercel deploys this project from
`frontend/`, so its serverless functions cannot read the monorepo parent at
runtime. Update this replica only by copying the canonical file in the same
change, then verify with `cmp`.
