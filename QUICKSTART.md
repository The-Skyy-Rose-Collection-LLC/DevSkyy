# DevSkyy Quick Start Guide

Get the DevSkyy Platform running in under 5 minutes.

## Prerequisites

- Python 3.11+
- Git

## Option 1: Quick Start (Recommended)

```bash
# Clone the repository
git clone https://github.com/The-Skyy-Rose-Collection-LLC/DevSkyy.git
cd DevSkyy

# Run the startup script
chmod +x start.sh
./start.sh
```

That's it! The application will be available at:
- **Dashboard**: http://localhost:8000/dashboard
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Option 2: Manual Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements-minimal.txt

# Create .env file
cp .env.example .env

# Start the server
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Option 3: Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or use the startup script
./start.sh --docker
```

## Verify It Works

```bash
# Health check
curl http://localhost:8000/health
# Expected: {"status":"healthy","version":"5.1.0-enterprise",...}

# System status
curl http://localhost:8000/status
# Expected: {"status":"operational",...}
```

## Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `/dashboard` | Modern enterprise dashboard |
| `/docs` | Interactive API documentation (Swagger) |
| `/redoc` | Alternative API documentation |
| `/health` | Health check endpoint |
| `/status` | Detailed system status |
| `/api/v1/...` | REST API endpoints |

## Architecture Overview

```
DevSkyy Platform
├── main.py              # FastAPI application entry point
├── api/v1/              # REST API endpoints (25+ routes)
├── agent/               # AI agent modules (40+)
├── security/            # Authentication, encryption (15+)
├── ml/                  # Machine learning modules
├── services/            # Business logic services
├── templates/           # Dashboard HTML templates
└── docker-compose.yml   # Docker orchestration
```

## Environment Variables

Create a `.env` file with these minimum settings:

```env
ENVIRONMENT=development
SECRET_KEY=your-secret-key-here
LOG_LEVEL=INFO
DATABASE_URL=sqlite:///./devskyy.db
```

## Troubleshooting

**Port already in use?**
```bash
./start.sh --port 8001
```

**Missing dependencies?**
```bash
pip install -r requirements-minimal.txt
```

**Docker not starting?**
```bash
docker-compose down -v
docker-compose up --build
```

## What's Next?

See the full [README.md](./README.md) for:
- Production deployment
- Security configuration
- API integration guides
- Agent development

---

**DevSkyy Platform v5.3.0** | Built with FastAPI + Claude AI
