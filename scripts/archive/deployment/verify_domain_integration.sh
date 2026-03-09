#!/bin/bash

# Domain Integration Verification Script for devskyy.app
# Tests DNS, services, CORS, and configuration readiness

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Domains to test
FRONTEND_DOMAIN="app.devskyy.app"
BACKEND_DOMAIN="api.devskyy.app"
ROOT_DOMAIN="devskyy.app"

# Ports
BACKEND_PORT=8000
FRONTEND_PORT=3000

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}DevSkyy Domain Integration Verification${NC}"
echo -e "${BLUE}=========================================${NC}\n"

# ==========================================
# 1. DNS PROPAGATION CHECK
# ==========================================
echo -e "${BLUE}[1/6] DNS Propagation Check${NC}"
echo "-------------------------------------------"

echo -e "\n${YELLOW}Checking ${FRONTEND_DOMAIN}...${NC}"
if dig +short ${FRONTEND_DOMAIN} | grep -q '^[0-9]'; then
    IP=$(dig +short ${FRONTEND_DOMAIN} | head -n1)
    echo -e "${GREEN}✓ DNS resolved: ${FRONTEND_DOMAIN} → ${IP}${NC}"
else
    echo -e "${RED}✗ DNS not resolved: ${FRONTEND_DOMAIN}${NC}"
    echo -e "${YELLOW}  Action: Create A record or CNAME for ${FRONTEND_DOMAIN}${NC}"
fi

echo -e "\n${YELLOW}Checking ${BACKEND_DOMAIN}...${NC}"
if dig +short ${BACKEND_DOMAIN} | grep -q '^[0-9]'; then
    IP=$(dig +short ${BACKEND_DOMAIN} | head -n1)
    echo -e "${GREEN}✓ DNS resolved: ${BACKEND_DOMAIN} → ${IP}${NC}"
else
    echo -e "${RED}✗ DNS not resolved: ${BACKEND_DOMAIN}${NC}"
    echo -e "${YELLOW}  Action: Create A record or CNAME for ${BACKEND_DOMAIN}${NC}"
fi

echo -e "\n${YELLOW}Checking root domain ${ROOT_DOMAIN}...${NC}"
if dig +short ${ROOT_DOMAIN} | grep -q '^[0-9]'; then
    IP=$(dig +short ${ROOT_DOMAIN} | head -n1)
    echo -e "${GREEN}✓ DNS resolved: ${ROOT_DOMAIN} → ${IP}${NC}"
else
    echo -e "${RED}✗ DNS not resolved: ${ROOT_DOMAIN}${NC}"
fi

# ==========================================
# 2. BACKEND HEALTH CHECK
# ==========================================
echo -e "\n${BLUE}[2/6] Backend Health Check${NC}"
echo "-------------------------------------------"

echo -e "\n${YELLOW}Testing local backend (port ${BACKEND_PORT})...${NC}"
if curl -s -o /dev/null -w "%{http_code}" http://localhost:${BACKEND_PORT}/health 2>/dev/null | grep -q '^200$'; then
    echo -e "${GREEN}✓ Backend running locally on port ${BACKEND_PORT}${NC}"
    HEALTH_RESPONSE=$(curl -s http://localhost:${BACKEND_PORT}/health 2>/dev/null || echo '{"status":"error"}')
    echo -e "${GREEN}  Response: ${HEALTH_RESPONSE}${NC}"
else
    echo -e "${RED}✗ Backend not accessible on localhost:${BACKEND_PORT}${NC}"
    echo -e "${YELLOW}  Action: Start backend with 'uvicorn main_enterprise:app --host 0.0.0.0 --port ${BACKEND_PORT}'${NC}"
fi

echo -e "\n${YELLOW}Testing production backend (${BACKEND_DOMAIN})...${NC}"
if curl -s -o /dev/null -w "%{http_code}" https://${BACKEND_DOMAIN}/health 2>/dev/null | grep -q '^200$'; then
    echo -e "${GREEN}✓ Backend accessible at https://${BACKEND_DOMAIN}/health${NC}"
    PROD_HEALTH=$(curl -s https://${BACKEND_DOMAIN}/health 2>/dev/null || echo '{"status":"error"}')
    echo -e "${GREEN}  Response: ${PROD_HEALTH}${NC}"
else
    echo -e "${YELLOW}⊗ Backend not yet deployed to ${BACKEND_DOMAIN}${NC}"
    echo -e "${YELLOW}  Expected after deployment: 200 OK with {\"status\":\"healthy\"}${NC}"
fi

# ==========================================
# 3. FRONTEND ACCESSIBILITY
# ==========================================
echo -e "\n${BLUE}[3/6] Frontend Accessibility${NC}"
echo "-------------------------------------------"

echo -e "\n${YELLOW}Testing local frontend (port ${FRONTEND_PORT})...${NC}"
if curl -s -o /dev/null -w "%{http_code}" http://localhost:${FRONTEND_PORT} 2>/dev/null | grep -q '^200$'; then
    echo -e "${GREEN}✓ Frontend running locally on port ${FRONTEND_PORT}${NC}"
    TITLE=$(curl -s http://localhost:${FRONTEND_PORT} 2>/dev/null | grep -o '<title>.*</title>' || echo 'No title found')
    echo -e "${GREEN}  Page title: ${TITLE}${NC}"
else
    echo -e "${RED}✗ Frontend not accessible on localhost:${FRONTEND_PORT}${NC}"
    echo -e "${YELLOW}  Action: Start frontend with 'cd frontend && npm run dev'${NC}"
fi

echo -e "\n${YELLOW}Testing production frontend (${FRONTEND_DOMAIN})...${NC}"
if curl -s -o /dev/null -w "%{http_code}" https://${FRONTEND_DOMAIN} 2>/dev/null | grep -q '^200$'; then
    echo -e "${GREEN}✓ Frontend accessible at https://${FRONTEND_DOMAIN}${NC}"
    PROD_TITLE=$(curl -s https://${FRONTEND_DOMAIN} 2>/dev/null | grep -o '<title>.*</title>' || echo 'No title found')
    echo -e "${GREEN}  Page title: ${PROD_TITLE}${NC}"
else
    echo -e "${YELLOW}⊗ Frontend not yet deployed to ${FRONTEND_DOMAIN}${NC}"
    echo -e "${YELLOW}  Expected after deployment: 200 OK with HTML content${NC}"
fi

# ==========================================
# 4. CORS VERIFICATION
# ==========================================
echo -e "\n${BLUE}[4/6] CORS Configuration${NC}"
echo "-------------------------------------------"

echo -e "\n${YELLOW}Testing CORS headers from backend...${NC}"
if curl -s -I http://localhost:${BACKEND_PORT}/health 2>/dev/null | grep -i 'access-control-allow-origin'; then
    CORS_HEADER=$(curl -s -I http://localhost:${BACKEND_PORT}/health 2>/dev/null | grep -i 'access-control-allow-origin')
    echo -e "${GREEN}✓ CORS headers present: ${CORS_HEADER}${NC}"
else
    echo -e "${RED}✗ No CORS headers found${NC}"
    echo -e "${YELLOW}  Action: Verify CORS_ORIGINS in .env includes ${FRONTEND_DOMAIN}${NC}"
fi

echo -e "\n${YELLOW}Testing preflight request simulation...${NC}"
PREFLIGHT=$(curl -s -X OPTIONS \
    -H "Origin: https://${FRONTEND_DOMAIN}" \
    -H "Access-Control-Request-Method: POST" \
    http://localhost:${BACKEND_PORT}/health 2>/dev/null || echo "Backend not running")
if echo "$PREFLIGHT" | grep -q "access-control-allow-origin"; then
    echo -e "${GREEN}✓ CORS preflight working${NC}"
else
    echo -e "${YELLOW}⊗ Could not verify CORS preflight (backend may not be running)${NC}"
fi

# ==========================================
# 5. CONFIGURATION FILES
# ==========================================
echo -e "\n${BLUE}[5/6] Configuration Files${NC}"
echo "-------------------------------------------"

# Check .env
echo -e "\n${YELLOW}Checking .env file...${NC}"
if [ -f /Users/coreyfoster/DevSkyy/.env ]; then
    echo -e "${GREEN}✓ .env exists${NC}"

    if grep -q "CORS_ORIGINS" /Users/coreyfoster/DevSkyy/.env; then
        CORS_VALUE=$(grep "CORS_ORIGINS" /Users/coreyfoster/DevSkyy/.env)
        echo -e "${GREEN}  CORS_ORIGINS configured: ${CORS_VALUE}${NC}"

        if echo "$CORS_VALUE" | grep -q "${FRONTEND_DOMAIN}"; then
            echo -e "${GREEN}  ✓ Includes ${FRONTEND_DOMAIN}${NC}"
        else
            echo -e "${YELLOW}  ⊗ Missing ${FRONTEND_DOMAIN}${NC}"
            echo -e "${YELLOW}  Action: Add 'https://${FRONTEND_DOMAIN}' to CORS_ORIGINS${NC}"
        fi
    else
        echo -e "${YELLOW}  ⊗ CORS_ORIGINS not found${NC}"
        echo -e "${YELLOW}  Action: Add CORS_ORIGINS=https://${FRONTEND_DOMAIN},http://localhost:3000${NC}"
    fi
else
    echo -e "${RED}✗ .env file not found${NC}"
    echo -e "${YELLOW}  Action: Copy .env.example to .env and configure${NC}"
fi

# Check main_enterprise.py CORS
echo -e "\n${YELLOW}Checking main_enterprise.py CORS middleware...${NC}"
if [ -f /Users/coreyfoster/DevSkyy/main_enterprise.py ]; then
    if grep -q "CORSMiddleware" /Users/coreyfoster/DevSkyy/main_enterprise.py; then
        echo -e "${GREEN}✓ CORSMiddleware configured in main_enterprise.py${NC}"
    else
        echo -e "${RED}✗ CORSMiddleware not found in main_enterprise.py${NC}"
        echo -e "${YELLOW}  Action: Add CORSMiddleware to FastAPI app${NC}"
    fi
else
    echo -e "${RED}✗ main_enterprise.py not found${NC}"
fi

# Check frontend/.env.production
echo -e "\n${YELLOW}Checking frontend/.env.production...${NC}"
if [ -f /Users/coreyfoster/DevSkyy/frontend/.env.production ]; then
    echo -e "${GREEN}✓ frontend/.env.production exists${NC}"

    if grep -q "NEXT_PUBLIC_API_URL" /Users/coreyfoster/DevSkyy/frontend/.env.production; then
        API_URL=$(grep "NEXT_PUBLIC_API_URL" /Users/coreyfoster/DevSkyy/frontend/.env.production)
        echo -e "${GREEN}  API URL configured: ${API_URL}${NC}"

        if echo "$API_URL" | grep -q "${BACKEND_DOMAIN}"; then
            echo -e "${GREEN}  ✓ Points to ${BACKEND_DOMAIN}${NC}"
        else
            echo -e "${YELLOW}  ⊗ Does not point to ${BACKEND_DOMAIN}${NC}"
            echo -e "${YELLOW}  Action: Set NEXT_PUBLIC_API_URL=https://${BACKEND_DOMAIN}${NC}"
        fi
    else
        echo -e "${YELLOW}  ⊗ NEXT_PUBLIC_API_URL not found${NC}"
    fi
else
    echo -e "${YELLOW}⊗ frontend/.env.production does not exist${NC}"
    echo -e "${YELLOW}  Action: Create with NEXT_PUBLIC_API_URL=https://${BACKEND_DOMAIN}${NC}"
fi

# Check next.config.js
echo -e "\n${YELLOW}Checking next.config.js API rewrites...${NC}"
if [ -f /Users/coreyfoster/DevSkyy/frontend/next.config.js ]; then
    echo -e "${GREEN}✓ next.config.js exists${NC}"

    if grep -q "rewrites" /Users/coreyfoster/DevSkyy/frontend/next.config.js; then
        echo -e "${GREEN}  ✓ Rewrites configured${NC}"
    else
        echo -e "${YELLOW}  ⊗ No rewrites found${NC}"
        echo -e "${YELLOW}  Action: Add API rewrite rules for /api/backend/*${NC}"
    fi
else
    echo -e "${RED}✗ next.config.js not found${NC}"
fi

# ==========================================
# 6. SUMMARY & ACTION ITEMS
# ==========================================
echo -e "\n${BLUE}[6/6] Summary & Action Items${NC}"
echo "-------------------------------------------"

echo -e "\n${YELLOW}Current Service Status:${NC}"
if curl -s -o /dev/null -w "%{http_code}" http://localhost:${BACKEND_PORT}/health 2>/dev/null | grep -q '^200$'; then
    echo -e "${GREEN}  Backend: Running on port ${BACKEND_PORT}${NC}"
else
    echo -e "${RED}  Backend: Not running${NC}"
fi

if curl -s -o /dev/null -w "%{http_code}" http://localhost:${FRONTEND_PORT} 2>/dev/null | grep -q '^200$'; then
    echo -e "${GREEN}  Frontend: Running on port ${FRONTEND_PORT}${NC}"
else
    echo -e "${RED}  Frontend: Not running${NC}"
fi

echo -e "\n${YELLOW}DNS Records Needed:${NC}"
echo -e "  ${FRONTEND_DOMAIN} → Vercel/Netlify (CNAME) or your server IP (A record)"
echo -e "  ${BACKEND_DOMAIN} → Your backend server IP (A record)"

echo -e "\n${YELLOW}Configuration Readiness:${NC}"
[ -f /Users/coreyfoster/DevSkyy/.env ] && echo -e "${GREEN}  ✓ Backend .env exists${NC}" || echo -e "${RED}  ✗ Backend .env missing${NC}"
[ -f /Users/coreyfoster/DevSkyy/frontend/.env.production ] && echo -e "${GREEN}  ✓ Frontend .env.production exists${NC}" || echo -e "${YELLOW}  ⊗ Frontend .env.production missing${NC}"

echo -e "\n${YELLOW}Deployment Steps Remaining:${NC}"
echo "  1. Configure DNS records at your domain registrar"
echo "  2. Update .env with production CORS_ORIGINS"
echo "  3. Create frontend/.env.production with NEXT_PUBLIC_API_URL"
echo "  4. Deploy backend to server with HTTPS/SSL"
echo "  5. Deploy frontend to Vercel with environment variables"
echo "  6. Verify HTTPS certificates are valid"
echo "  7. Test end-to-end API calls from frontend to backend"

echo -e "\n${BLUE}=========================================${NC}"
echo -e "${BLUE}Verification Complete${NC}"
echo -e "${BLUE}=========================================${NC}\n"
