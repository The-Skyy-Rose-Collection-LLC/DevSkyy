# Security Monitoring & Alerting Architecture

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DevSkyy Application                              │
│                      (security_monitoring.py)                            │
│                                                                           │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐      │
│  │ Security Events  │  │  Security Alerts │  │  Threat Tracking │      │
│  │  - Login failed  │  │  - Brute force   │  │  - IP blocking   │      │
│  │  - Injection     │  │  - Rate limit    │  │  - User blocking │      │
│  │  - Rate limit    │  │  - Suspicious    │  │  - Threat score  │      │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘      │
│           │                      │                      │                │
└───────────┼──────────────────────┼──────────────────────┼────────────────┘
            │                      │                      │
            ▼                      ▼                      ▼
    ┌───────────────┐      ┌─────────────────┐   ┌──────────────┐
    │ Metrics       │      │ Alerting        │   │ Prometheus   │
    │ Export        │      │ Integration     │   │ Exporter     │
    │ /metrics      │      │ (alerting.py)   │   │              │
    └───────┬───────┘      └────────┬────────┘   └──────┬───────┘
            │                       │                    │
            │              ┌────────┴────────┐          │
            │              │                 │          │
            │              ▼                 ▼          │
            │     ┌──────────────┐  ┌──────────────┐   │
            │     │ Slack        │  │ Email        │   │
            │     │ #security    │  │ ops@domain   │   │
            │     └──────────────┘  └──────────────┘   │
            │                                           │
            │              ┌──────────────┐            │
            │              │ PagerDuty    │            │
            │              │ Critical     │            │
            │              └──────────────┘            │
            │                                           │
            │              ┌──────────────┐            │
            │              │ Custom       │            │
            │              │ Webhook      │            │
            │              └──────────────┘            │
            │                                           │
            └──────────────────┬────────────────────────┘
                               │
                    ┌──────────▼───────────┐
                    │    Prometheus        │
                    │    :9090             │
                    │  - Scrapes metrics   │
                    │  - Stores time series│
                    │  - Evaluates alerts  │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │   AlertManager       │
                    │   :9093              │
                    │  - Routes alerts     │
                    │  - Deduplicates      │
                    │  - Sends to channels │
                    └──────────┬───────────┘
                               │
                    ┌──────────▼───────────┐
                    │    Grafana           │
                    │    :3000             │
                    │  - Visualizes data   │
                    │  - Security dashboard│
                    │  - Real-time charts  │
                    └──────────────────────┘
```

## Data Flow

### 1. Event Generation

```
Application → SecurityMonitor.log_event() → SecurityEvent created
```

### 2. Metrics Export

```
SecurityEvent → Prometheus metrics → /metrics endpoint → Prometheus scrape
```

### 3. Alert Detection (Two Paths)

**Path A: Application-level**

```
SecurityMonitor → _detect_threats() → SecurityAlert → AlertingIntegration
```

**Path B: Prometheus-level**

```
Prometheus → Evaluate alert rules → AlertManager → Notification channels
```

### 4. Alert Distribution

```
SecurityAlert → AlertingIntegration → [Slack, Email, PagerDuty, Webhook]
                      ↓
              Deduplication (5min window)
                      ↓
              Severity-based routing
                      ↓
              Async delivery
                      ↓
              Track statistics
```

## Service Communication

```
┌──────────────┐   HTTP scrape    ┌──────────────┐
│  DevSkyy App │ ←───────────────  │  Prometheus  │
│  :8000       │                   │  :9090       │
└──────────────┘                   └──────┬───────┘
                                          │
                                          │ Alert events
                                          │
                                   ┌──────▼───────┐
                                   │ AlertManager │
                                   │ :9093        │
                                   └──────┬───────┘
                                          │
                          ┌───────────────┼───────────────┐
                          │               │               │
                   ┌──────▼────┐   ┌──────▼────┐   ┌─────▼─────┐
                   │ Slack     │   │ Email     │   │ PagerDuty │
                   │ Webhook   │   │ SMTP      │   │ API       │
                   └───────────┘   └───────────┘   └───────────┘

┌──────────────┐   PromQL queries  ┌──────────────┐
│  Grafana     │ ────────────────→ │  Prometheus  │
│  :3000       │                   │  :9090       │
└──────────────┘                   └──────────────┘
```

## Metrics Collection

```
Application Metrics (/metrics)
├── security_events_total{event_type}
├── security_threat_score
├── security_alerts_total{severity}
├── security_alerts_active
├── security_blocked_ips_total
└── security_failed_login_attempts{endpoint}

Database Metrics (postgres-exporter:9187)
├── pg_stat_database_*
├── pg_stat_bgwriter_*
└── pg_locks_*

Cache Metrics (redis-exporter:9121)
├── redis_connected_clients
├── redis_memory_used_bytes
└── redis_commands_total

System Metrics (node-exporter:9100)
├── node_cpu_seconds_total
├── node_memory_*
└── node_filesystem_*
```

## Alert Routing Logic

```
SecurityAlert created
    │
    ├─ severity = CRITICAL
    │   └─→ Slack + Email + PagerDuty + Webhook
    │
    ├─ severity = HIGH
    │   └─→ Slack + Email + Webhook
    │
    ├─ severity = MEDIUM
    │   └─→ Slack + Webhook
    │
    └─ severity = LOW/INFO
        └─→ Webhook only
```

## Dashboard Panel Data Sources

```
Real-time Security Events
└─→ rate(security_events_total[5m])

Threat Score Gauge
└─→ security_threat_score

Alert Status
└─→ sum(security_alerts_active)

Top Blocked IPs
└─→ topk(10, sum by (ip_address) (increase(security_blocked_ips_total[24h])))

Failed Login Heatmap
└─→ sum by (endpoint) (increase(security_failed_login_attempts[1h]))

Alerts by Severity
└─→ sum by (severity) (security_alerts_total)

Top Event Types
└─→ topk(10, sum by (event_type) (increase(security_events_total[1h])))
```

## Port Mapping

| Service | Port | Purpose |
|---------|------|---------|
| DevSkyy App | 8000 | Main application + /metrics |
| Grafana | 3000 | Dashboard UI |
| Prometheus | 9090 | Metrics storage & query |
| AlertManager | 9093 | Alert routing |
| Node Exporter | 9100 | System metrics |
| Redis Exporter | 9121 | Cache metrics |
| PostgreSQL Exporter | 9187 | Database metrics |

## Configuration Files

```
config/
├── grafana/
│   ├── dashboards/
│   │   └── security-dashboard.json        # Dashboard definition
│   ├── provisioning/
│   │   ├── datasources/
│   │   │   └── prometheus.yml             # Prometheus datasource
│   │   └── dashboards/
│   │       └── dashboard.yml              # Dashboard provisioning
│   └── README.md                          # Documentation
│
├── prometheus/
│   ├── prometheus.yml                     # Scrape configs
│   └── alerts/
│       └── security_alerts.yml            # 25+ alert rules
│
└── alertmanager/
    └── alertmanager.yml                   # Routing & receivers
```

## Security Boundaries

```
┌─────────────────────────────────────────────────────────┐
│                   Docker Network                        │
│                   (devskyy-network)                     │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ App      │  │ Postgres │  │ Redis    │             │
│  │ :8000    │  │ :5432    │  │ :6379    │             │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘             │
│       │             │              │                    │
│  ┌────┴──────────────┴──────────────┴─────┐            │
│  │        Monitoring Stack                 │            │
│  │  ┌──────────┐  ┌──────────┐            │            │
│  │  │Prometheus│  │ Grafana  │            │            │
│  │  └──────────┘  └──────────┘            │            │
│  └─────────────────────────────────────────┘            │
│                                                          │
└─────────────────────────────────────────────────────────┘
                    │
                    │ External connections only
                    │
        ┌───────────┴───────────┐
        │                       │
  ┌─────▼──────┐         ┌──────▼──────┐
  │ Slack      │         │ PagerDuty   │
  │ Webhook    │         │ API         │
  └────────────┘         └─────────────┘
```

## Time Windows

| Component | Interval | Purpose |
|-----------|----------|---------|
| Metrics scrape | 15-30s | Collect metrics |
| Alert evaluation | 30s | Check alert rules |
| Dashboard refresh | 5s | Update UI |
| Deduplication window | 5min | Prevent duplicate alerts |
| Data retention | 200h | Store metrics |

## High Availability Considerations

```
Load Balancer (future)
    │
    ├─→ DevSkyy App Instance 1
    ├─→ DevSkyy App Instance 2
    └─→ DevSkyy App Instance 3
            │
            ├─→ Prometheus (federation)
            │   ├─→ Prometheus 1 (primary)
            │   └─→ Prometheus 2 (replica)
            │
            └─→ Grafana (stateless)
                └─→ Multiple instances behind LB
```

## Monitoring the Monitors

```
Prometheus self-monitoring
├─→ Scrapes itself (job: prometheus)
├─→ Checks scrape success rates
└─→ Monitors alert evaluation

Grafana health
├─→ Healthcheck: /api/health
├─→ Database connection
└─→ Datasource status

AlertManager health
├─→ Healthcheck: /-/healthy
├─→ Notification success rates
└─→ Queue depth
```

---

This architecture provides:

- ✅ Real-time security monitoring
- ✅ Multi-channel alerting
- ✅ High availability support
- ✅ Comprehensive metrics
- ✅ Scalable design
