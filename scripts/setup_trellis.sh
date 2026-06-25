#!/usr/bin/env bash
# Scaffold the Microsoft TRELLIS repo under vendor/trellis/ for local inference.
#
# Usage:
#   bash scripts/setup_trellis.sh                          # default: clone, no model download
#   bash scripts/setup_trellis.sh --with-weights           # also pull image-large weights
#   bash scripts/setup_trellis.sh --upgrade                # pull latest from origin
#   TRELLIS_REPO=https://github.com/microsoft/TRELLIS.git bash scripts/setup_trellis.sh
#
# After this:
#   pip install -r requirements-trellis.txt
#   pip install -e vendor/trellis
#   TRELLIS_BACKEND=local python -m pipelines.clothing_3d.cli health
#
# Environment:
#   TRELLIS_REPO       — git URL (default: https://github.com/microsoft/TRELLIS.git)
#   TRELLIS_LOCAL_PATH — where to clone (default: vendor/trellis)
#   TRELLIS_BRANCH     — branch / tag to check out (default: main)

set -euo pipefail

REPO_URL="${TRELLIS_REPO:-https://github.com/microsoft/TRELLIS.git}"
LOCAL_PATH="${TRELLIS_LOCAL_PATH:-vendor/trellis}"
BRANCH="${TRELLIS_BRANCH:-main}"

WITH_WEIGHTS=false
UPGRADE=false

for arg in "$@"; do
  case "$arg" in
    --with-weights) WITH_WEIGHTS=true ;;
    --upgrade)      UPGRADE=true ;;
    -h|--help)
      sed -n '2,17p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown flag: $arg" >&2
      exit 2
      ;;
  esac
done

cd "$(dirname "$0")/.."

mkdir -p "$(dirname "$LOCAL_PATH")"

if [ -d "$LOCAL_PATH/.git" ]; then
  if [ "$UPGRADE" = true ]; then
    echo ">>> Updating existing TRELLIS clone at $LOCAL_PATH"
    git -C "$LOCAL_PATH" fetch origin
    git -C "$LOCAL_PATH" checkout "$BRANCH"
    git -C "$LOCAL_PATH" pull --ff-only origin "$BRANCH"
  else
    echo ">>> TRELLIS already present at $LOCAL_PATH (pass --upgrade to pull latest)"
  fi
else
  echo ">>> Cloning $REPO_URL into $LOCAL_PATH (branch=$BRANCH)"
  git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$LOCAL_PATH"
fi

# Mark the vendor copy as not-tracked by this repo's git.
GITIGNORE="vendor/.gitignore"
if [ ! -f "$GITIGNORE" ]; then
  cat > "$GITIGNORE" <<'EOF'
# All vendored third-party trees are excluded — see scripts/setup_trellis.sh.
*
!.gitignore
EOF
fi

echo ">>> Verifying TRELLIS layout"
required=(trellis pipelines.py setup.py)
for f in "${required[@]}"; do
  if [ ! -e "$LOCAL_PATH/$f" ]; then
    echo "WARN: expected $LOCAL_PATH/$f — repo layout may have changed" >&2
  fi
done

if [ "$WITH_WEIGHTS" = true ]; then
  echo ">>> Pre-downloading microsoft/TRELLIS-image-large via HuggingFace"
  if ! command -v python >/dev/null 2>&1; then
    echo "python not found on PATH; skipping weight prefetch" >&2
  else
    python - <<'PY'
import os
from huggingface_hub import snapshot_download

cache = os.environ.get("TRELLIS_CACHE_DIR", "./.cache/trellis")
snapshot_download(
    repo_id="microsoft/TRELLIS-image-large",
    cache_dir=cache,
    local_dir_use_symlinks=False,
)
print(f">>> Weights cached under {cache}")
PY
  fi
fi

cat <<EOF

TRELLIS is ready at: $LOCAL_PATH

Next steps:
  pip install -r requirements-trellis.txt
  pip install -e $LOCAL_PATH

Then test the local backend:
  TRELLIS_BACKEND=local python -m pipelines.clothing_3d.cli health

Or run a dry-run against the stub backend (no GPU required):
  python -m pipelines.clothing_3d.cli generate \\
    --image path/to/garment.jpg \\
    --product "Test" --garment-type tee \\
    --quality draft --dry-run

EOF
