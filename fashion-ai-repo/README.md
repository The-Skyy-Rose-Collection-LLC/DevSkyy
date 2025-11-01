# Fashion AI Autonomous Commerce Platform

> Comprehensive end-to-end autonomous fashion-commerce infrastructure with multi-agent orchestration, ML-driven design generation, and fully automated operations.

## Overview

The Fashion AI Platform is a self-contained autonomous system for fashion design, commerce, marketing, finance, and operations. It leverages multiple AI agents coordinated through message queues to create a fully automated fashion commerce pipeline.

## Features

- **Multi-Agent Architecture**: 5 specialized agents (Designer, Commerce, Marketing, Finance, Ops)
- **ML Pipeline**: CLIP embeddings, Stable Diffusion generation, quality evaluation
- **Message Queue**: Redis-based pub/sub for agent communication
- **REST API**: FastAPI-powered endpoints for all services
- **Automated Operations**: Health checks, backups, scaling triggers
- **Docker Ready**: Complete containerization with docker-compose
- **Test Coverage**: Unit and integration tests with pytest
- **Monitoring**: Metrics collection, health reporting, alert thresholds

## Architecture

```
[Frontend UI (Next.js)]
        ↓
[API Gateway (FastAPI)] → [Agents Layer]
        ↓                        ↓
  [Redis Queue] ←→ [Postgres DB] ←→ [ML/Storage Layer]
        ↓
     [Ops Monitoring + CI/CD + Docker]
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Redis (via Docker or local install)
- PostgreSQL 15+ (via Docker or local install)

### Installation

```bash
# Clone and navigate
cd fashion-ai-repo

# Install dependencies
make setup

# Start services
make dc-up

# Run the API
make run
```

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov
```

### Running Audits

```bash
# Run all audits, generate manifests, and tests
make all
```

## Agent System

| Agent | Responsibility | I/O Path | Communication |
|-------|---------------|----------|---------------|
| **DesignerAgent** | AI design generation, validation, curation | `/data/designs/` | Redis queue, `/api/design/*` |
| **CommerceAgent** | Product listings, pricing, SKU management | `/data/commerce/` | `/api/products`, `/api/orders` |
| **MarketingAgent** | Campaign creation, content scheduling, analytics | `/data/marketing/` | `/api/marketing/*`, `/api/analytics` |
| **FinanceAgent** | Financial logging, ledger, revenue summaries | `/data/finance/` | `/api/finance/*` |
| **OpsAgent** | Uptime monitoring, health checks, backups | `/logs/` | `/api/system/*` |

## API Endpoints

### Design
- `POST /api/design/generate` - Generate new design
- `GET /api/design/feed` - List recent designs
- `GET /api/design/{id}` - Get specific design

### Commerce
- `GET /api/products` - List products
- `GET /api/products/{sku}` - Get product details
- `POST /api/orders` - Create order

### Marketing
- `POST /api/marketing/campaign` - Create campaign
- `GET /api/analytics` - Get analytics

### Finance
- `GET /api/finance/summary` - Financial summary
- `GET /api/finance/ledger` - Ledger entries

### System
- `GET /api/system/status` - System status
- `GET /api/system/health` - Health check
- `GET /api/system/metrics` - Metrics

## Development

### Project Structure

```
fashion-ai-repo/
├── config/          # Configuration files (YAML)
├── data/            # Data storage (designs, commerce, etc.)
├── docs/            # Documentation
├── logs/            # Application logs
├── scripts/         # Operational scripts
├── src/
│   ├── agents/      # Agent implementations
│   ├── api/         # FastAPI application
│   ├── cli/         # CLI interface
│   ├── core/        # Core modules (config, logging, queue)
│   └── ml/          # ML pipeline
└── tests/           # Test suite

```

### Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
# Edit .env with your settings
```

### Running Individual Agents

```bash
# Start Designer Agent
python -m src.cli start --agent designer

# Start Commerce Agent
python -m src.cli start --agent commerce

# Start all agents
python -m src.cli start-all
```

## Monitoring & Operations

### Health Check

```bash
make health-check
# or
python scripts/run_health_check.py
```

### Backup

```bash
python scripts/backup_db.py
```

### Metrics

Metrics are collected continuously and stored in:
- `/logs/queue_metrics.json` - Queue performance
- `/logs/health_report.txt` - System health

## Deployment

### Docker Deployment

```bash
# Build image
docker build -t fashion-ai:latest .

# Run with docker-compose
docker-compose up -d
```

### Production Checklist

- [ ] Environment variables configured
- [ ] Redis and Postgres deployed
- [ ] Volumes mounted for persistence
- [ ] Health checks enabled
- [ ] Monitoring configured
- [ ] Backups scheduled
- [ ] HTTPS/TLS configured
- [ ] CORS origins restricted

## Testing

```bash
# Run all tests
make test

# Run specific test suite
pytest tests/test_endpoints.py -v

# Run integration tests
pytest tests/test_integration_cycle.py -m integration
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Run tests and linting
4. Submit pull request

## License

MIT License - see LICENSE file

## Support

For issues and questions:
- GitHub Issues: [repository]/issues
- Documentation: `/docs`
- API Docs: `http://localhost:8000/docs`
