# Vendored repositories

This directory holds third-party repositories scaffolded by setup scripts.
Contents are intentionally git-ignored — fetch them on demand.

| Subdir         | Setup script                  | Purpose                              |
|----------------|-------------------------------|--------------------------------------|
| `trellis/`     | `scripts/setup_trellis.sh`    | Microsoft TRELLIS 3D generation repo |

To bootstrap TRELLIS:

```bash
bash scripts/setup_trellis.sh                # clone only
bash scripts/setup_trellis.sh --with-weights # also pre-download image-large
pip install -r requirements-trellis.txt
pip install -e vendor/trellis
```

The clothing 3D pipeline (`services/three_d/trellis/`) reads from
`vendor/trellis/` only when `TRELLIS_BACKEND=local`. Default is `hf_space`,
which calls the public HuggingFace Space and needs no local TRELLIS install.
