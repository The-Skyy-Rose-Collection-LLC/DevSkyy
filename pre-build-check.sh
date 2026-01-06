#!/bin/bash
# DevSkyy Pre-Build Verification
# Ensures all components are ready before Docker build

set -e

echo "🔍 DevSkyy Pre-Build Verification"
echo "=================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track errors
ERRORS=0
WARNINGS=0

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${RED}✗${NC} $1 - MISSING"
        ((ERRORS++))
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} $1/"
    else
        echo -e "${RED}✗${NC} $1/ - MISSING"
        ((ERRORS++))
    fi
}

warn_if_missing() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${YELLOW}⚠${NC} $1 - Optional (recommended)"
        ((WARNINGS++))
    fi
}

echo "📁 Core Configuration Files"
echo "----------------------------"
check_file "requirements.txt"
check_file "package.json"
check_file "Dockerfile"
check_file "Dockerfile.worker"
check_file "docker-compose.yml"
check_file "init.sql"
check_file "nginx.conf"
check_file "prometheus.yml"
warn_if_missing ".env"
check_file ".env.example"
echo ""

echo "🐍 Backend Structure"
echo "--------------------"
check_file "main_enterprise.py"
check_file "devskyy_mcp.py"
check_dir "agents"
check_dir "llm"
check_dir "agent_sdk"
check_dir "api"
check_dir "security"
check_dir "orchestration"
check_dir "core"
check_dir "runtime"
check_dir "mcp_servers"
echo ""

echo "⚛️  Frontend Structure"
echo "---------------------"
check_dir "src"
check_file "src/index.ts"
check_dir "src/collections"
check_dir "src/components"
check_file "config/typescript/tsconfig.json"
echo ""

echo "🔧 Message Queue Infrastructure"
echo "-------------------------------"
check_file "agent_sdk/task_queue.py"
check_file "agent_sdk/worker.py"
echo ""

echo "🤖 Agents"
echo "---------"
check_file "agents/tripo_agent.py"
check_file "agents/commerce_agent.py"
check_file "agents/marketing_agent.py"
check_file "agents/support_agent.py"
check_file "agents/operations_agent.py"
check_file "agents/analytics_agent.py"
echo ""

echo "🧠 LLM Infrastructure"
echo "--------------------"
check_file "llm/router.py"
check_file "llm/round_table.py"
check_file "llm/ab_testing.py"
check_file "llm/base.py"
check_dir "llm/providers"
echo ""

echo "📊 Environment Variables Check"
echo "------------------------------"
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} .env file exists"

    # Check critical variables
    if grep -q "^JWT_SECRET_KEY=" .env && ! grep -q "your-jwt-secret" .env; then
        echo -e "${GREEN}✓${NC} JWT_SECRET_KEY configured"
    else
        echo -e "${RED}✗${NC} JWT_SECRET_KEY not configured or using default"
        ((ERRORS++))
    fi

    if grep -q "^ENCRYPTION_MASTER_KEY=" .env && ! grep -q "your-base64" .env; then
        echo -e "${GREEN}✓${NC} ENCRYPTION_MASTER_KEY configured"
    else
        echo -e "${RED}✗${NC} ENCRYPTION_MASTER_KEY not configured or using default"
        ((ERRORS++))
    fi

    if grep -q "^REDIS_URL=" .env; then
        echo -e "${GREEN}✓${NC} REDIS_URL configured"
    else
        echo -e "${YELLOW}⚠${NC} REDIS_URL not set (will use default)"
        ((WARNINGS++))
    fi

    if grep -q "^DATABASE_URL=" .env; then
        echo -e "${GREEN}✓${NC} DATABASE_URL configured"
    else
        echo -e "${YELLOW}⚠${NC} DATABASE_URL not set (will use SQLite)"
        ((WARNINGS++))
    fi
else
    echo -e "${RED}✗${NC} .env file missing - copy from .env.example"
    ((ERRORS++))
fi
echo ""

echo "🔒 Security Check"
echo "----------------"
if [ -f ".env" ] && grep -q "changeme\|your-jwt-secret\|your-base64" .env; then
    echo -e "${RED}✗${NC} Default/placeholder values detected in .env"
    echo -e "${YELLOW}   Please generate secure keys:${NC}"
    echo '   python -c "import secrets; print(secrets.token_urlsafe(64))"'
    echo '   python -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"'
    ((ERRORS++))
else
    echo -e "${GREEN}✓${NC} No placeholder values detected"
fi
echo ""

echo "📦 Python Dependencies"
echo "---------------------"
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✓${NC} Python 3 installed"
    python3 --version

    # Check if pip is available
    if command -v pip3 &> /dev/null; then
        echo -e "${GREEN}✓${NC} pip installed"
    else
        echo -e "${RED}✗${NC} pip not found"
        ((ERRORS++))
    fi
else
    echo -e "${RED}✗${NC} Python 3 not found"
    ((ERRORS++))
fi
echo ""

echo "📦 Node.js Dependencies"
echo "----------------------"
if command -v node &> /dev/null; then
    echo -e "${GREEN}✓${NC} Node.js installed"
    node --version

    if command -v npm &> /dev/null; then
        echo -e "${GREEN}✓${NC} npm installed"
        npm --version
    else
        echo -e "${RED}✗${NC} npm not found"
        ((ERRORS++))
    fi

    if [ -d "node_modules" ]; then
        echo -e "${GREEN}✓${NC} node_modules exists"
    else
        echo -e "${YELLOW}⚠${NC} node_modules not found - run 'npm install'"
        ((WARNINGS++))
    fi
else
    echo -e "${RED}✗${NC} Node.js not found"
    ((ERRORS++))
fi
echo ""

echo "🐳 Docker Check"
echo "--------------"
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker installed"
    docker --version

    if docker info &> /dev/null; then
        echo -e "${GREEN}✓${NC} Docker daemon running"
    else
        echo -e "${RED}✗${NC} Docker daemon not running"
        ((ERRORS++))
    fi
else
    echo -e "${RED}✗${NC} Docker not found"
    ((ERRORS++))
fi

if command -v docker-compose &> /dev/null; then
    echo -e "${GREEN}✓${NC} docker-compose installed"
    docker-compose --version
else
    echo -e "${YELLOW}⚠${NC} docker-compose not found (will use 'docker compose')"
fi
echo ""

echo "🔍 Code Quality"
echo "--------------"
if [ -f "agent_sdk/task_queue.py" ]; then
    # Check if enterprise hardening markers are present
    if grep -q "max_connections=50" agent_sdk/task_queue.py; then
        echo -e "${GREEN}✓${NC} Redis connection pooling enabled"
    else
        echo -e "${YELLOW}⚠${NC} Redis connection pooling not found"
        ((WARNINGS++))
    fi

    if grep -q "Pub/Sub" agent_sdk/task_queue.py; then
        echo -e "${GREEN}✓${NC} Pub/Sub result delivery enabled"
    else
        echo -e "${YELLOW}⚠${NC} Pub/Sub not found (using polling)"
        ((WARNINGS++))
    fi
fi

if [ -f "agent_sdk/worker.py" ]; then
    if grep -q "SET NX EX\|atomic lock" agent_sdk/worker.py; then
        echo -e "${GREEN}✓${NC} Atomic task locking enabled"
    else
        echo -e "${YELLOW}⚠${NC} Atomic task locking not found"
        ((WARNINGS++))
    fi

    if grep -q "DLQ\|Dead Letter Queue" agent_sdk/worker.py; then
        echo -e "${GREEN}✓${NC} Dead Letter Queue enabled"
    else
        echo -e "${YELLOW}⚠${NC} Dead Letter Queue not found"
        ((WARNINGS++))
    fi
fi

if [ -f "llm/router.py" ]; then
    if grep -q "CircuitBreaker" llm/router.py; then
        echo -e "${GREEN}✓${NC} Circuit breaker pattern enabled"
    else
        echo -e "${YELLOW}⚠${NC} Circuit breaker not found"
        ((WARNINGS++))
    fi
fi
echo ""

echo "=================================="
echo "Summary"
echo "=================================="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✓ No critical errors detected${NC}"
else
    echo -e "${RED}✗ $ERRORS critical error(s) found${NC}"
fi

if [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠ $WARNINGS warning(s)${NC}"
fi
echo ""

if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ Ready to build!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Install dependencies: npm install && pip install -r requirements.txt"
    echo "  2. Build images: docker-compose build"
    echo "  3. Start services: docker-compose up -d"
    echo "  4. Check logs: docker-compose logs -f"
    echo "  5. Monitor: http://localhost:3000 (Grafana), http://localhost:5555 (Flower)"
    exit 0
else
    echo -e "${RED}❌ Fix errors before building${NC}"
    exit 1
fi
