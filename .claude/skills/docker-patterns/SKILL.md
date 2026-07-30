---
name: docker-patterns
description: Docker and Docker Compose patterns for local development, container security, networking, volume strategies, and multi-service orchestration. Use when authoring or debugging a Dockerfile / compose file, bringing the local DevSkyy stack up, or diagnosing container networking, healthcheck, or volume failures. Do NOT use for production orchestration on Fly/Vercel/Kubernetes, for WordPress theme deploys (that is wp-deploy — skyyrose.co is WP.com Atomic, not containerized), or for schema changes inside the DB container (that is database-migrations).
origin: ECC
---

# Docker Patterns

Docker and Docker Compose best practices for containerized development.

## When to use

- Setting up Docker Compose for local development
- Designing multi-container architectures
- Troubleshooting container networking, healthchecks, or volume issues
- Reviewing Dockerfiles for security and size
- Migrating from local dev to containerized workflow

**When NOT to use:**

- skyyrose.co — WP.com Atomic hosting, no containers involved. Theme changes go through `wp-deploy`.
- Production orchestration (Fly.io for `api.devskyy.app`, Vercel for `devskyy.app`) — Compose is a
  local-dev tool here; `docker-compose.prod.yml` patterns below are reference, not this repo's
  production path.
- Schema/data changes inside `devskyy-postgres` → `database-migrations` (Alembic is canonical).
- Cache key design or eviction inside `devskyy-redis` → `redis-patterns`.

## Inputs

**Absent input = STOP. A compose stack started with guessed secrets is worse than one that
refuses to start — it silently gets a different DB than every other developer.**

1. **`.env.docker` with real values.** `docker-compose.yml` interpolates `POSTGRES_PASSWORD`,
   `REDIS_PASSWORD`, and friends into the shared `x-app-env` anchor. Absent → `docker compose`
   refuses to even parse the file (see Worked example — this is the correct fail-closed behavior).
   Generate it with `make docker-secrets`, then paste API keys in. Never invent a password to get
   past the error.
2. **A running Docker daemon.** `docker info` must succeed. A dead daemon makes every subsequent
   command fail in ways that look like config bugs.
3. **The repo root as the compose working directory** — `docker-compose.yml`, `Dockerfile`, and
   `.env.docker` all resolve relative to it. Never use repo-relative paths from a random cwd
   (bug-288: cwd persists silently between calls; use absolute paths).
4. **Free host ports** for anything you publish (`APP_PORT` defaults to 8000). A port already bound
   by another stack surfaces as a container that starts then dies.

## Procedure

1. `make docker-secrets` if `.env.docker` does not exist; fill in API keys.
2. Validate the compose file *before* starting anything: `docker compose config --services`
   (Verification check 1). A parse/interpolation error here is a stop, not a warning.
3. `make docker-up` (build + start the core stack: app, postgres, redis, workers).
4. Wait for healthchecks, then confirm every service reports `(healthy)` — not merely `Up`
   (Verification check 2). `depends_on: condition: service_healthy` means an unhealthy postgres
   silently holds the app in "Created".
5. Probe the app's own health endpoint through the published port (Verification check 3).
6. On failure, read logs for the specific service (`docker compose logs --tail=50 <svc>`) before
   changing config — most "networking" bugs are a service that never became healthy.
7. Tear down with `docker compose down`. **`docker compose down -v` destroys the named volumes
   (`postgres_data`, `redis_data`) — that is irreversible data loss and a STOP-AND-SHOW action.**

## Verification

Every check below can return "no". A command that errored or timed out is an artifact, not a pass —
re-run it (bug-230). `docker compose ps` showing `Up` is **not** the same as `(healthy)`; treating
"started" as "working" is the fail-open shape this stack is most prone to.

```bash
cd /Users/theceo/DevSkyy && docker compose config --services
```
**PASS:** exits 0 and lists the expected services. Any interpolation error means a required secret
is missing — fix `.env.docker`, never hand-edit the compose file to dodge it. `[repro]`

```bash
docker compose ps --format '{{.Name}} {{.Status}}'
```
**PASS:** every core service line contains `(healthy)`. Observed 2026-07-28: `devskyy-app`,
`devskyy-postgres`, `devskyy-redis`, `devskyy-worker`, `devskyy-elite-worker` all
`Up 35 hours (healthy)` `[repro]`. A service stuck at `Up (health: starting)` past its
`start_period` (40s for app) is failing, not booting.

```bash
docker exec devskyy-postgres sh -c 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"' && \
docker exec devskyy-redis  sh -c 'REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli ping'
```
**PASS:** `accepting connections` and `PONG`. Observed 2026-07-28: `PONG` `[repro]`. These mirror
the healthchecks at `docker-compose.yml:73` (`pg_isready -U devskyy -d devskyy`) and `:94`
(`redis-cli -a "$$REDIS_PASSWORD" ping | grep -q PONG`), but pass credentials via env
(`REDISCLI_AUTH`) instead of argv; running them by hand is how you distinguish "healthcheck is
wrong" from "service is down". A bare `redis-cli ping` returning `NOAUTH Authentication required.`
is the password being enforced, not an outage. `[repro]`

```bash
curl -fsS "http://localhost:${APP_PORT:-8000}/health"
```
**PASS:** exits 0 with a JSON health body — the same probe as the app healthcheck
(`docker-compose.yml:127`), but from the host, which additionally proves the port publish works.
`[repro]`

Prove the checks can fail (rule 3): `docker compose stop redis`, re-run check 2 — the app must go
unhealthy — then `docker compose start redis`. A health gate never observed going red is a guess
with a citation.

## Docker Compose for Local Development

### Standard Web App Stack

```yaml
# docker-compose.yml
services:
  app:
    build:
      context: .
      target: dev                     # Use dev stage of multi-stage Dockerfile
    ports:
      - "3000:3000"
    volumes:
      - .:/app                        # Bind mount for hot reload
      - /app/node_modules             # Anonymous volume -- preserves container deps
    environment:
      - DATABASE_URL=postgres://postgres:postgres@db:5432/app_dev
      - REDIS_URL=redis://redis:6379/0
      - NODE_ENV=development
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    command: npm run dev

  db:
    image: postgres:16-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: app_dev
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 3s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redisdata:/data

  mailpit:                            # Local email testing
    image: axllent/mailpit
    ports:
      - "8025:8025"                   # Web UI
      - "1025:1025"                   # SMTP

volumes:
  pgdata:
  redisdata:
```

### Development vs Production Dockerfile

```dockerfile
# Stage: dependencies
FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# Stage: dev (hot reload, debug tools)
FROM node:22-alpine AS dev
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]

# Stage: build
FROM node:22-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build && npm prune --production

# Stage: production (minimal image)
FROM node:22-alpine AS production
WORKDIR /app
RUN addgroup -g 1001 -S appgroup && adduser -S appuser -u 1001
USER appuser
COPY --from=build --chown=appuser:appgroup /app/dist ./dist
COPY --from=build --chown=appuser:appgroup /app/node_modules ./node_modules
COPY --from=build --chown=appuser:appgroup /app/package.json ./
ENV NODE_ENV=production
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s CMD wget -qO- http://localhost:3000/health || exit 1
CMD ["node", "dist/server.js"]
```

### Override Files

```yaml
# docker-compose.override.yml (auto-loaded, dev-only settings)
services:
  app:
    environment:
      - DEBUG=app:*
      - LOG_LEVEL=debug
    ports:
      - "9229:9229"                   # Node.js debugger

# docker-compose.prod.yml (explicit for production)
services:
  app:
    build:
      target: production
    restart: always
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 512M
```

```bash
# Development (auto-loads override)
docker compose up

# Production
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Networking

### Service Discovery

Services in the same Compose network resolve by service name:
```
# From "app" container:
postgres://postgres:postgres@db:5432/app_dev    # "db" resolves to the db container
redis://redis:6379/0                             # "redis" resolves to the redis container
```

### Custom Networks

```yaml
services:
  frontend:
    networks:
      - frontend-net

  api:
    networks:
      - frontend-net
      - backend-net

  db:
    networks:
      - backend-net              # Only reachable from api, not frontend

networks:
  frontend-net:
  backend-net:
```

### Exposing Only What's Needed

```yaml
services:
  db:
    ports:
      - "127.0.0.1:5432:5432"   # Only accessible from host, not network
    # Omit ports entirely in production -- accessible only within Docker network
```

## Volume Strategies

```yaml
volumes:
  # Named volume: persists across container restarts, managed by Docker
  pgdata:

  # Bind mount: maps host directory into container (for development)
  # - ./src:/app/src

  # Anonymous volume: preserves container-generated content from bind mount override
  # - /app/node_modules
```

### Common Patterns

```yaml
services:
  app:
    volumes:
      - .:/app                   # Source code (bind mount for hot reload)
      - /app/node_modules        # Protect container's node_modules from host
      - /app/.next               # Protect build cache

  db:
    volumes:
      - pgdata:/var/lib/postgresql/data          # Persistent data
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql  # Init scripts
```

## Container Security

### Dockerfile Hardening

```dockerfile
# 1. Use specific tags (never :latest)
FROM node:22.12-alpine3.20

# 2. Run as non-root
RUN addgroup -g 1001 -S app && adduser -S app -u 1001
USER app

# 3. Drop capabilities (in compose)
# 4. Read-only root filesystem where possible
# 5. No secrets in image layers
```

### Compose Security

```yaml
services:
  app:
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
      - /app/.cache
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE          # Only if binding to ports < 1024
```

### Secret Management

```yaml
# GOOD: Use environment variables (injected at runtime)
services:
  app:
    env_file:
      - .env                     # Never commit .env to git
    environment:
      - API_KEY                  # Inherits from host environment

# GOOD: Docker secrets (Swarm mode)
secrets:
  db_password:
    file: ./secrets/db_password.txt

services:
  db:
    secrets:
      - db_password

# BAD: Hardcoded in image
# ENV API_KEY=sk-proj-xxxxx      # NEVER DO THIS
```

## .dockerignore

```
node_modules
.git
.env
.env.*
dist
coverage
*.log
.next
.cache
docker-compose*.yml
Dockerfile*
README.md
tests/
```

## Debugging

### Common Commands

```bash
# View logs
docker compose logs -f app           # Follow app logs
docker compose logs --tail=50 db     # Last 50 lines from db

# Execute commands in running container
docker compose exec app sh           # Shell into app
docker compose exec db psql -U postgres  # Connect to postgres

# Inspect
docker compose ps                     # Running services
docker compose top                    # Processes in each container
docker stats                          # Resource usage

# Rebuild
docker compose up --build             # Rebuild images
docker compose build --no-cache app   # Force full rebuild

# Clean up
docker compose down                   # Stop and remove containers
docker compose down -v                # Also remove volumes (DESTRUCTIVE)
docker system prune                   # Remove unused images/containers
```

### Debugging Network Issues

```bash
# Check DNS resolution inside container
docker compose exec app nslookup db

# Check connectivity
docker compose exec app wget -qO- http://api:3000/health

# Inspect network
docker network ls
docker network inspect <project>_default
```

## Worked example

Real invocation in this repo, 2026-07-28 — the fail-closed path first:

```bash
cd /Users/theceo/DevSkyy/.claude/worktrees/glimmering-crafting-shannon
docker compose config --services; echo "exit=$?"
docker info >/dev/null 2>&1 && echo "daemon=UP" || echo "daemon=DOWN"
```

Observed `[repro]`:

```
error while interpolating x-app-env.DATABASE_URL: required variable POSTGRES_PASSWORD is missing a value: set POSTGRES_PASSWORD in .env.docker
exit=1
daemon=UP
```

That is the gate working exactly as it should: the daemon is fine, but `.env.docker` is absent in
this worktree, so Compose refuses to produce a config at all rather than interpolating an empty
password into `DATABASE_URL` and quietly connecting to a different database. The fix is
`make docker-secrets` — never "just export POSTGRES_PASSWORD=postgres to get past it".

The already-running stack (started from the main checkout, which has `.env.docker`):

```bash
docker ps --format '{{.Names}} {{.Status}}'
docker exec devskyy-postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "SELECT current_database(), version();"'
docker exec devskyy-redis sh -c 'REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli ping'
```

Observed `[repro]`:

```
devskyy-elite-worker Up 35 hours (healthy)
devskyy-worker       Up 35 hours (healthy)
devskyy-app          Up 35 hours (healthy)
devskyy-postgres     Up 35 hours (healthy)
devskyy-redis        Up 35 hours (healthy)
devskyy|PostgreSQL 15.18 on aarch64-unknown-linux-musl, compiled by gcc (Alpine 15.2.0) 15.2.0, 64-bit
PONG
```

Two lessons in that output. First, `redis-cli ping` **without** the password returns
`NOAUTH Authentication required.` — observed in the same session; the healthcheck at
`docker-compose.yml:94` passes `-a "$$REDIS_PASSWORD"` precisely because of this, and a hand-run
probe that omits it looks like an outage that is not there. Second, the service names in exec
commands are container names (`devskyy-postgres`), while in-network DNS uses the *service* name
(`postgres`) — mixing them up is the most common "networking is broken" false alarm.

## Anti-Patterns

```
# BAD: Using docker compose in production without orchestration
# Use Kubernetes, ECS, or Docker Swarm for production multi-container workloads

# BAD: Storing data in containers without volumes
# Containers are ephemeral -- all data lost on restart without volumes

# BAD: Running as root
# Always create and use a non-root user

# BAD: Using :latest tag
# Pin to specific versions for reproducible builds

# BAD: One giant container with all services
# Separate concerns: one process per container

# BAD: Putting secrets in docker-compose.yml
# Use .env files (gitignored) or Docker secrets
```
