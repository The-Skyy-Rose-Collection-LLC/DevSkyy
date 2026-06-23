#!/usr/bin/env bash
# Generate .env.docker from .env.docker.example with strong random secrets.
# Refuses to clobber an existing .env.docker (it holds your real secrets/keys).
set -euo pipefail

cd "$(dirname "$0")/.."

TEMPLATE=".env.docker.example"
OUT=".env.docker"

if [ -f "$OUT" ]; then
    echo "✋ $OUT already exists — refusing to overwrite (it holds your secrets)."
    echo "   Delete it first if you really want a fresh set: rm $OUT && make docker-secrets"
    exit 1
fi
[ -f "$TEMPLATE" ] || { echo "ERROR: $TEMPLATE not found"; exit 1; }

# URL-safe tokens (chars [-_A-Za-z0-9]) are safe inside the postgres:// / redis:// URLs.
gen() { python3 -c "import secrets; print(secrets.token_urlsafe($1))"; }
# Matches the entrypoint's ENCRYPTION_MASTER_KEY format: base64(32 random bytes).
enc() { python3 -c "import secrets,base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"; }

PG=$(gen 24); RD=$(gen 24); GF=$(gen 18); JWT=$(gen 64); JWTR=$(gen 64); ENC=$(enc)

cp "$TEMPLATE" "$OUT"

# Secrets go via stdin (newline-delimited), not argv — argv is world-readable in
# /proc/<pid>/cmdline and `ps` while the process runs.
printf '%s\n' "$PG" "$RD" "$GF" "$JWT" "$JWTR" "$ENC" | python3 - "$OUT" <<'PY'
import sys

path = sys.argv[1]
pg, rd, gf, jwt, jwtr, enc = sys.stdin.read().splitlines()
repl = {
    "POSTGRES_PASSWORD": pg,
    "REDIS_PASSWORD": rd,
    "GRAFANA_ADMIN_PASSWORD": gf,
    "JWT_SECRET_KEY": jwt,
    "JWT_REFRESH_SECRET_KEY": jwtr,
    "ENCRYPTION_MASTER_KEY": enc,
}
with open(path) as f:
    src = f.readlines()
lines = []
for line in src:
    key = line.split("=", 1)[0].strip()
    lines.append(f"{key}={repl[key]}\n" if key in repl else line)
with open(path, "w") as f:
    f.writelines(lines)
PY

chmod 600 "$OUT"
echo "✅ Wrote $OUT (chmod 600) with random POSTGRES/REDIS/GRAFANA passwords + JWT/ENCRYPTION keys."
echo "   Next: paste your API keys into $OUT, then run 'make docker-up'."
