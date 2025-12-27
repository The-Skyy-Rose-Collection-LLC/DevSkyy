# DevSkyy Platform Maintenance Best Practices

> **Version:** 1.0.0 | **Last Updated:** December 17, 2025
> **Applies To:** Python 3.11+/FastAPI Backend, TypeScript/Three.js Frontend, 6-Agent Ecosystem

---

## Table of Contents

1. [Code Quality & Standards](#1-code-quality--standards)
2. [Testing Strategy](#2-testing-strategy)
3. [Security Maintenance](#3-security-maintenance)
4. [Monitoring & Observability](#4-monitoring--observability)
5. [Dependency Management](#5-dependency-management)
6. [Documentation](#6-documentation)
7. [Dashboard Integration](#7-dashboard-integration)

---

## 1. Code Quality & Standards

### 1.1 Linting & Formatting

#### Python (Backend)

```bash
# Ruff - Fast Python linter (replaces flake8, isort, pyupgrade)
ruff check .                    # Check for issues
ruff check . --fix              # Auto-fix issues
ruff format .                   # Format code (replaces Black)

# Run before every commit
ruff check . --fix && ruff format .
```

**Configuration** (`pyproject.toml`):

```toml
[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "W", "I", "N", "UP", "S", "B", "A", "C4", "DTZ", "T10", "ISC", "ICN", "PIE", "PT", "RET", "SIM", "TID", "ARG", "ERA", "PL", "TRY", "RUF"]
```

#### TypeScript (Frontend)

```bash
# ESLint + Prettier
npm run lint                    # Check for issues
npm run lint:fix                # Auto-fix issues
npm run format                  # Format with Prettier

# Add to package.json scripts:
"format": "prettier --write \"src/**/*.{ts,tsx,js,jsx,json}\"",
"format:check": "prettier --check \"src/**/*.{ts,tsx,js,jsx,json}\""
```

### 1.2 TypeScript Strict Mode Compliance

DevSkyy uses **maximum strictness** for type safety:

```json
// config/typescript/tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noPropertyAccessFromIndexSignature": true,
    "exactOptionalPropertyTypes": true
  }
}
```

**Key Patterns:**

```typescript
// ✅ Correct: Bracket notation for index signatures
const value = config['key'];

// ✅ Correct: Null checks for array access
const first = items[0];
if (first) { /* use first */ }

// ✅ Correct: Optional chaining
const name = user?.profile?.name;
```

### 1.3 Code Review Guidelines

#### PR Requirements Checklist

| Requirement | Details |
|-------------|---------|
| **Title Format** | `type(scope): description` (e.g., `feat(auth): Add rate limiting`) |
| **Description** | What, Why, How, Testing done |
| **Tests** | All new code has tests, coverage maintained |
| **Types** | No `any` types, proper interfaces defined |
| **Security** | No secrets, no SQL injection, input validated |
| **Performance** | No N+1 queries, proper async/await |

#### Commit Message Convention

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `security`

**Scopes:** `auth`, `agents`, `3d`, `api`, `db`, `wordpress`, `security`, `deps`

---

## 2. Testing Strategy

### 2.1 Coverage Thresholds

| Metric | Threshold | Current | Target |
|--------|-----------|---------|--------|
| **Statements** | 80% | 93.58% | ≥85% |
| **Branches** | 77% | 73.34% | ≥80% |
| **Functions** | 80% | 87.61% | ≥85% |
| **Lines** | 80% | 94.01% | ≥85% |

### 2.2 Test Pyramid

```
                    ┌─────────────┐
                    │    E2E      │  ~10% (Cypress/Playwright)
                    │   Tests     │  Full user flows
                    ├─────────────┤
                    │ Integration │  ~20% (pytest + Jest)
                    │   Tests     │  API endpoints, DB
                    ├─────────────┤
                    │    Unit     │  ~70% (pytest + Jest)
                    │   Tests     │  Functions, Classes
                    └─────────────┘
```

### 2.3 Running Tests

```bash
# Python Tests
pytest tests/ -v                      # All tests
pytest tests/ -m "not slow"           # Skip slow tests
pytest tests/ --cov --cov-report=html # With coverage

# TypeScript Tests
npm run test                          # All tests
npm run test -- --watch               # Watch mode
npm run test -- --coverage            # With coverage

# CI/CD Pipeline
npm run test:ci                       # Non-interactive
pytest tests/ -q --tb=short           # Quick summary
```

### 2.4 Test Organization

```
tests/
├── unit/                    # Fast, isolated tests
│   ├── test_encryption.py
│   └── test_jwt.py
├── integration/             # API, database tests
│   ├── test_api_endpoints.py
│   └── test_wordpress.py
├── security/                # Security-specific tests
│   └── test_vulnerability_scanner.py
└── conftest.py              # Shared fixtures

src/
├── services/__tests__/      # TypeScript unit tests
├── collections/__tests__/   # Three.js experience tests
└── utils/__tests__/         # Utility tests
```

---

## 3. Security Maintenance

### 3.1 Secret Rotation Schedule

| Secret | Rotation Frequency | Method |
|--------|-------------------|--------|
| `JWT_SECRET_KEY` | 90 days | `python scripts/generate_secrets.py` |
| `ENCRYPTION_MASTER_KEY` | 180 days | Requires data re-encryption |
| `API Keys` (OpenAI, etc.) | On compromise | Regenerate in provider dashboard |
| `Database Credentials` | 90 days | Rotate via cloud provider |

**Rotation Commands:**

```bash
# Generate new secrets
python scripts/generate_secrets.py --show-only

# Verify current secrets
python scripts/verify_env.py
```

### 3.2 Dependency Vulnerability Monitoring

```bash
# Python
pip-audit                              # Scan for vulnerabilities
safety check                           # Alternative scanner

# JavaScript/TypeScript
npm audit                              # Check vulnerabilities
npm audit fix                          # Auto-fix
npm audit fix --force                  # Force major updates

# Automated (GitHub)
# Dependabot configured in .github/dependabot.yml
```

**Dependabot Configuration:**

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5

  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 5
```

### 3.3 Security Audit Schedule

| Audit Type | Frequency | Tools |
|------------|-----------|-------|
| **Dependency Scan** | Weekly (automated) | Dependabot, npm audit, pip-audit |
| **Code Analysis** | Per PR | Ruff security rules, ESLint |
| **Penetration Testing** | Quarterly | Manual + automated tools |
| **Secret Scan** | Per commit | git-secrets, truffleHog |

---

## 4. Monitoring & Observability

### 4.1 Logging Best Practices

#### Python (structlog)

```python
import structlog

logger = structlog.get_logger(__name__)

# Good: Structured logging with context
logger.info("user_authenticated", user_id=user.id, method="oauth2")

# Good: Error with stack trace
logger.error("payment_failed", error=str(e), order_id=order.id, exc_info=True)

# Bad: Unstructured logging
logger.info(f"User {user.id} logged in")  # No structure
```

#### TypeScript (Logger utility)

```typescript
import { Logger } from '../utils/Logger';

const logger = new Logger('AgentService');

// Good: Contextual logging
logger.info('Task created', { taskId, agentType, priority });
logger.error('Task execution failed', { taskId, error: e.message });

// Performance logging for 3D
logger.debug('Frame rendered', { fps, drawCalls, triangles });
```

### 4.2 Log Levels

| Level | Use Case | Example |
|-------|----------|---------|
| `ERROR` | Failures requiring attention | Authentication failed, DB connection lost |
| `WARN` | Potential issues | Deprecated API used, rate limit approaching |
| `INFO` | Business events | User registered, order placed, agent task completed |
| `DEBUG` | Development details | Request payload, 3D render stats |

### 4.3 Error Tracking & Alerting

**Recommended Setup:**

```python
# Sentry integration (main_enterprise.py)
import sentry_sdk

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    environment=os.getenv("ENVIRONMENT", "development"),
    traces_sample_rate=0.1,  # 10% of transactions
    profiles_sample_rate=0.1,
)
```

**Alert Thresholds:**
| Metric | Warning | Critical |
|--------|---------|----------|
| Error Rate | >1% | >5% |
| Response Time (P95) | >500ms | >2s |
| Memory Usage | >70% | >90% |
| CPU Usage | >70% | >90% |

### 4.4 Performance Monitoring for 3D Experiences

```typescript
// Three.js performance metrics
class PerformanceMonitor {
  private stats = {
    fps: 0,
    drawCalls: 0,
    triangles: 0,
    geometries: 0,
    textures: 0,
  };

  update(renderer: THREE.WebGLRenderer): void {
    const info = renderer.info;
    this.stats.drawCalls = info.render.calls;
    this.stats.triangles = info.render.triangles;
    this.stats.geometries = info.memory.geometries;
    this.stats.textures = info.memory.textures;
  }

  getMetrics(): PerformanceStats {
    return { ...this.stats };
  }
}
```

**Key 3D Metrics:**

- **FPS**: Target ≥30fps on mobile, ≥60fps on desktop
- **Draw Calls**: Target <100 per frame
- **Memory**: Monitor for leaks on dispose()
- **Load Time**: Target <3s for initial experience

---

## 5. Dependency Management

### 5.1 Update Cadence

| Category | Frequency | Action |
|----------|-----------|--------|
| **Security Patches** | Immediate | Same-day update |
| **Minor Updates** | Weekly | Batch with Dependabot PRs |
| **Major Updates** | Monthly | Planned upgrade sprint |
| **Framework Updates** | Quarterly | Dedicated testing cycle |

### 5.2 Handling Breaking Changes

```bash
# 1. Create upgrade branch
git checkout -b upgrade/fastapi-0.110

# 2. Update dependency
pip install fastapi==0.110.0

# 3. Run tests
pytest tests/ -v

# 4. Check deprecation warnings
pytest tests/ -W error::DeprecationWarning

# 5. Update code for breaking changes
# 6. Update documentation
# 7. PR with detailed changelog
```

### 5.3 Lock File Management

```bash
# Python - requirements.txt + pip-tools
pip-compile requirements.in -o requirements.txt
pip-compile requirements-dev.in -o requirements-dev.txt

# JavaScript - package-lock.json
npm ci                         # Install from lock file (CI)
npm install                    # Update lock file (dev)

# Never manually edit lock files!
```

---

## 6. Documentation

### 6.1 Keeping Docs in Sync

**Pre-commit Hook:**

```bash
# .pre-commit-config.yaml
- repo: local
  hooks:
    - id: check-docs
      name: Check documentation freshness
      entry: python scripts/check_docs.py
      language: system
      pass_filenames: false
```

**Documentation Checklist:**

- [ ] API changes reflected in OpenAPI schema
- [ ] New features documented in relevant guide
- [ ] Breaking changes noted in CHANGELOG.md
- [ ] Code comments updated for complex logic

### 6.2 API Documentation Standards

```python
@router.post("/agents/{agent_id}/tasks", response_model=TaskResponse)
async def create_task(
    agent_id: str,
    task: TaskCreate,
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    """
    Create a new task for an agent.

    Args:
        agent_id: The unique identifier of the target agent
        task: Task creation parameters

    Returns:
        TaskResponse: The created task with ID and status

    Raises:
        HTTPException 404: Agent not found
        HTTPException 429: Rate limit exceeded
        HTTPException 403: Insufficient permissions

    Example:
        POST /api/v1/agents/agent_123/tasks
        {
            "type": "content_generation",
            "payload": {"prompt": "Write a product description"},
            "priority": "high"
        }
    """
```

### 6.3 Changelog Maintenance

**Format (Keep a Changelog):**

```markdown
# Changelog

## [Unreleased]

### Added
- Rate limiting on login endpoint (5 attempts/5 min)

### Changed
- Three.js experiences now properly dispose resources

### Fixed
- Memory leak in LoveHurtsExperience particle system

### Security
- Updated cryptography to 42.0.5
```

---

## 7. Dashboard Integration

### 7.1 Recommended Dashboard Stack

| Component | Tool | Purpose |
|-----------|------|---------|
| **Metrics** | Grafana | Visualization, alerting |
| **Time-series DB** | Prometheus | Metric storage |
| **Logs** | Loki + Grafana | Log aggregation |
| **Tracing** | Jaeger | Distributed tracing |
| **APM** | Sentry | Error tracking, performance |

### 7.2 DevSkyy Dashboard Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Grafana Dashboard                            │
├──────────────┬──────────────┬──────────────┬───────────────────────┤
│   Platform   │    Agent     │     3D       │      Security         │
│   Health     │  Ecosystem   │  Experiences │      Metrics          │
└──────────────┴──────────────┴──────────────┴───────────────────────┘
       │               │               │               │
       ▼               ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Prometheus                                   │
│  - API latency       - Task counts      - FPS metrics  - Auth events│
│  - Error rates       - Queue depth      - Memory usage - Rate limits│
│  - Request volume    - Agent health     - Load times   - Failed auth│
└─────────────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Application Metrics                               │
│                                                                      │
│  FastAPI (Python)          Three.js (Browser)      Agent Service    │
│  ┌─────────────────┐       ┌─────────────────┐    ┌──────────────┐  │
│  │ prometheus-client│       │ Custom metrics │    │ Event emitter│  │
│  │ fastapi-metrics  │       │ via WebSocket  │    │ to Prometheus│  │
│  └─────────────────┘       └─────────────────┘    └──────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 7.3 Key Dashboard Panels

#### Platform Health Dashboard

```yaml
# grafana/dashboards/platform-health.json
panels:
  - title: "API Response Time (P95)"
    type: graph
    query: histogram_quantile(0.95, http_request_duration_seconds_bucket)

  - title: "Error Rate"
    type: singlestat
    query: sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))

  - title: "Active Users"
    type: gauge
    query: sum(active_sessions_total)

  - title: "Database Connections"
    type: graph
    query: pg_stat_activity_count
```

#### Agent Ecosystem Dashboard

```yaml
panels:
  - title: "Tasks by Agent Type"
    type: piechart
    query: sum by (agent_type) (agent_tasks_total)

  - title: "Task Queue Depth"
    type: graph
    query: agent_task_queue_size

  - title: "Task Success Rate"
    type: gauge
    query: sum(agent_tasks_completed) / sum(agent_tasks_total)
    thresholds: [0.9, 0.95]  # Yellow <95%, Green ≥95%

  - title: "Agent Health Status"
    type: table
    query: agent_health_status
    columns: [agent_id, status, last_heartbeat]
```

#### 3D Experience Dashboard

```yaml
panels:
  - title: "Average FPS by Experience"
    type: bargauge
    query: avg by (experience) (threejs_fps)

  - title: "Memory Usage Trend"
    type: graph
    query: threejs_memory_geometries + threejs_memory_textures

  - title: "WebGL Context Losses"
    type: singlestat
    query: sum(increase(webgl_context_lost_total[24h]))

  - title: "Load Time Distribution"
    type: heatmap
    query: experience_load_time_seconds_bucket
```

### 7.4 Prometheus Metrics Implementation

#### Python (FastAPI)

```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import APIRouter

# Define metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

AGENT_TASKS = Counter(
    'agent_tasks_total',
    'Total agent tasks',
    ['agent_type', 'status']
)

ACTIVE_SESSIONS = Gauge(
    'active_sessions_total',
    'Number of active user sessions'
)

# Metrics endpoint
metrics_router = APIRouter()

@metrics_router.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

#### TypeScript (Browser → Backend)

```typescript
// metrics/PerformanceReporter.ts
interface ThreeJSMetrics {
  experience: string;
  fps: number;
  drawCalls: number;
  triangles: number;
  geometries: number;
  textures: number;
  loadTimeMs: number;
}

class PerformanceReporter {
  private ws: WebSocket;
  private reportInterval = 5000; // 5 seconds

  constructor(wsUrl: string) {
    this.ws = new WebSocket(wsUrl);
  }

  reportMetrics(metrics: ThreeJSMetrics): void {
    if (this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'threejs_metrics',
        timestamp: Date.now(),
        data: metrics
      }));
    }
  }

  startAutoReport(getMetrics: () => ThreeJSMetrics): void {
    setInterval(() => {
      this.reportMetrics(getMetrics());
    }, this.reportInterval);
  }
}
```

### 7.5 Alert Rules

```yaml
# prometheus/alerts.yml
groups:
  - name: devskyy-platform
    rules:
      - alert: HighErrorRate
        expr: sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }}"

      - alert: AgentTaskQueueBacklog
        expr: agent_task_queue_size > 100
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Agent task queue growing"
          description: "Queue size: {{ $value }}"

      - alert: Low3DFPS
        expr: avg(threejs_fps) < 20
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "3D experience performance degraded"
          description: "Average FPS: {{ $value }}"

      - alert: SecurityAuthFailures
        expr: sum(rate(auth_failures_total[5m])) > 10
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High authentication failure rate"
          description: "Possible brute force attack"
```

### 7.6 Docker Compose for Monitoring Stack

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus:/etc/prometheus
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    ports:
      - "3000:3000"
    depends_on:
      - prometheus

  loki:
    image: grafana/loki:latest
    volumes:
      - loki_data:/loki
    ports:
      - "3100:3100"

  sentry:
    image: sentry/sentry:latest
    environment:
      - SENTRY_SECRET_KEY=${SENTRY_SECRET}
    ports:
      - "9000:9000"

volumes:
  prometheus_data:
  grafana_data:
  loki_data:
```

---

## 8. Quick Reference Commands

### Daily Operations

```bash
# Start development
npm run dev                            # TypeScript watch
uvicorn main_enterprise:app --reload   # Python server

# Run tests
pytest tests/ -v && npm run test

# Check code quality
ruff check . && npm run lint

# Security scan
npm audit && pip-audit
```

### Weekly Maintenance

```bash
# Update dependencies (review changes)
npm outdated
pip list --outdated

# Generate coverage report
pytest tests/ --cov --cov-report=html
npm run test:coverage
```

### Monthly Tasks

```bash
# Full security audit
npm audit --audit-level=high
pip-audit --strict

# Performance review
# Check Grafana dashboards for trends

# Documentation review
# Verify all docs are current
```

---

## 9. CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
          npm ci

      - name: Lint
        run: |
          ruff check .
          npm run lint

      - name: Type check
        run: |
          npx tsc -p config/typescript/tsconfig.json --noEmit

      - name: Test
        run: |
          pytest tests/ -v --cov
          npm run test:ci

      - name: Security scan
        run: |
          pip-audit
          npm audit --audit-level=high
```

---

**Document Version:** 1.0.0
**Maintainer:** DevSkyy Platform Team
**Review Cycle:** Quarterly
