# Docker — DevSkyy Production Stack

The canonical containerized stack for the Python API + background workers. The
Next.js dashboard is **not** in here — it deploys to Vercel (`devskyy.app`).

## TL;DR

```bash
make docker-secrets     # 1. generate .env.docker with strong random secrets
#   edit .env.docker → paste your OPENAI_API_KEY / ANTHROPIC_API_KEY / etc.
make docker-up          # 2. build + start core stack (detached)
make docker-logs        # 3. watch it boot
curl localhost:8000/health
make docker-down        # stop (keeps data)
```

## What runs

One image — `devskyy:local` — serves three roles, selected by the compose
`command:` and dispatched by `docker-entrypoint.sh`:

| Service        | Role                              | Command                                   |
|----------------|-----------------------------------|-------------------------------------------|
| `app`          | FastAPI REST + GraphQL + MCP      | *(default)* → uvicorn `main_enterprise:app` |
| `worker`       | async task queue poller (3D/ML)   | `python -m agent_sdk.worker`              |
| `elite-worker` | Elite Studio render jobs          | `python -m skyyrose.elite_studio worker`  |
| `postgres`     | PostgreSQL 15 (extensions only; schema via `create_all`) | —                     |
| `redis`        | task queue + cache (authed)       | —                                         |

Opt-in profiles:

```bash
docker compose --env-file .env.docker --profile monitoring up -d   # + prometheus + grafana
docker compose --env-file .env.docker --profile proxy up -d        # + nginx (:80 → app)
```

## Secrets

`.env.docker` (gitignored) holds everything. `make docker-secrets` fills the
infra passwords and the two security keys with random values; you paste the API
keys. Compose **fails loudly** (`${VAR:?...}`) if a required secret is missing —
there is no silent `changeme` fallback.

> **`JWT_SECRET_KEY` and `ENCRYPTION_MASTER_KEY` must stay stable.** If unset,
> the entrypoint generates ephemeral keys every boot, which rotates the
> encryption key (data becomes unreadable) and invalidates all JWTs. The
> generator persists both — keep `.env.docker` safe and backed up.

## Build targets

```bash
make docker-build       # builds devskyy:local (INSTALL_TARGET=all default)
```

`INSTALL_TARGET` selects which `pyproject.toml` *extras* to add on top of the
base dependencies. **It does not give you a slim, torch-free image**: the ML
stack (torch, transformers, diffusers, chromadb) lives in the base
`[project.dependencies]`, so every build pulls it. The first build downloads
that wheel stack (multi-GB, ~15–20 min) and produces a large (~6 GB) image;
subsequent builds hit the BuildKit cache. A genuinely slim API image would
require moving the ML deps into an optional group in `pyproject.toml` first.

The `.dockerignore` is an **allowlist** (ignore everything, re-include only the
first-party Python packages + canonical text data). It cut the build context
from ~1 GB to ~43 MB by excluding the unbounded local scratch at the repo root
(`backups/`, `ci_mirror/`, `editorial-staging/`, `.claude/` worktrees, etc.),
all binary media, the 465 MB PHP theme (only its `data/` subdir — catalog CSV +
36 dossiers + logo registry — is re-included), the frontend, and `.git`.

## Scaling

`docker compose up` ignores `deploy.replicas`; scale a role explicitly:

```bash
docker compose --env-file .env.docker up -d --scale worker=3
```

## Make targets

| Target                   | Does                                              |
|--------------------------|---------------------------------------------------|
| `make docker-secrets`    | generate `.env.docker` (won't clobber an existing one) |
| `make docker-config`     | validate + render the merged compose config       |
| `make docker-build`      | build `devskyy:local`                             |
| `make docker-up`         | build + start core stack (detached)               |
| `make docker-up-monitoring` | core + prometheus + grafana                    |
| `make docker-logs`       | tail all services                                 |
| `make docker-ps`         | container status                                  |
| `make docker-down`       | stop (keeps volumes)                              |
| `make docker-clean`      | stop **and delete volumes** (destroys data)       |

## Other Dockerfiles in the repo

- `Dockerfile.mcp` — slim standalone MCP HTTP service (`mcp_service:app`, no ML
  stack), selected by `fly.toml` for Fly.io.
- `Dockerfile.api` — slim production image for the full backend
  (`main_enterprise:app`), installs `.[api]` only. Not yet wired into
  `fly.toml`/compose — build and run it standalone, or point a deploy target
  at it explicitly.
- `deploy/clothing_3d/` — standalone 3D service, separate concern.
