# DevSkyy Phase 2 - Staging Testing Checklist

**Version:** 2.0.0
**Last Updated:** 2025-12-19
**Environment:** Staging

---

## Table of Contents

1. [Pre-Deployment Tests](#pre-deployment-tests)
2. [Post-Deployment Smoke Tests](#post-deployment-smoke-tests)
3. [Feature Verification Tests](#feature-verification-tests)
4. [Security Feature Tests](#security-feature-tests)
5. [Performance Baseline Tests](#performance-baseline-tests)
6. [Monitoring & Alerting Verification](#monitoring--alerting-verification)
7. [Integration Tests](#integration-tests)
8. [API Endpoint Tests](#api-endpoint-tests)
9. [Agent System Tests](#agent-system-tests)
10. [Regression Test Suite](#regression-test-suite)

---

## Pre-Deployment Tests

### Infrastructure Readiness

- [ ] **Server Resources**
  ```bash
  # Check available RAM
  free -h
  # Expected: Minimum 8GB free

  # Check disk space
  df -h
  # Expected: Minimum 50GB free on /opt/devskyy

  # Check CPU cores
  nproc
  # Expected: Minimum 4 cores
  ```

- [ ] **Docker Installation**
  ```bash
  docker --version
  # Expected: Docker version 20.10+

  docker-compose --version
  # Expected: Docker Compose version 2.0+
  ```

- [ ] **Network Connectivity**
  ```bash
  # Test external API connectivity
  curl -I https://api.openai.com
  curl -I https://api.anthropic.com
  curl -I https://generativelanguage.googleapis.com

  # Expected: 200 OK responses
  ```

- [ ] **DNS Resolution**
  ```bash
  nslookup staging.devskyy.com
  # Expected: Resolves to staging server IP
  ```

- [ ] **Port Availability**
  ```bash
  sudo netstat -tulpn | grep -E ':(80|443|8000|3000|9090|9093|5432|6379)\s'
  # Expected: All ports available (no conflicts)
  ```

### Configuration Validation

- [ ] **Environment Variables**
  ```bash
  # Verify .env file exists
  test -f /opt/devskyy/.env && echo "OK" || echo "MISSING"

  # Check critical variables are set
  grep -q "POSTGRES_PASSWORD=CHANGE" .env && echo "ERROR: Password not changed" || echo "OK"
  grep -q "JWT_SECRET_KEY=staging-jwt" .env && echo "ERROR: JWT key not changed" || echo "OK"
  ```

- [ ] **API Keys Validation**
  ```bash
  # Test OpenAI API key
  curl https://api.openai.com/v1/models \
    -H "Authorization: Bearer $OPENAI_API_KEY" | jq '.data[0].id'
  # Expected: Valid model ID returned

  # Test Anthropic API key
  curl https://api.anthropic.com/v1/messages \
    -H "x-api-key: $ANTHROPIC_API_KEY" \
    -H "anthropic-version: 2023-06-01" \
    -H "content-type: application/json" \
    -d '{"model":"claude-3-haiku-20240307","max_tokens":1,"messages":[{"role":"user","content":"hi"}]}'
  # Expected: Valid response (even with minimal tokens)
  ```

- [ ] **SSL Certificates**
  ```bash
  # Check certificate files exist
  ls -lh config/nginx/ssl/
  # Expected: cert.pem and key.pem present

  # Verify certificate validity
  openssl x509 -in config/nginx/ssl/cert.pem -noout -dates
  # Expected: Valid dates (not expired)
  ```

### Code Quality Checks

- [ ] **Linting**
  ```bash
  make lint
  # Expected: No errors
  ```

- [ ] **Type Checking**
  ```bash
  cd frontend && npm run type-check
  # Expected: No type errors
  ```

- [ ] **Unit Tests**
  ```bash
  make test
  # Expected: All tests pass
  ```

- [ ] **Security Scan**
  ```bash
  # Scan for secrets in code
  git secrets --scan

  # Check dependencies for vulnerabilities
  pip audit
  npm audit
  # Expected: No critical vulnerabilities
  ```

---

## Post-Deployment Smoke Tests

### Service Health Checks

- [ ] **All Services Running**
  ```bash
  docker-compose -f docker-compose.staging.yml ps
  # Expected: All services in "Up" state
  ```

- [ ] **Application Health**
  ```bash
  curl -f http://localhost:8000/health
  # Expected: {"status": "healthy"}
  ```

- [ ] **Database Health**
  ```bash
  docker-compose -f docker-compose.staging.yml exec postgres pg_isready -U staging_user
  # Expected: accepting connections
  ```

- [ ] **Redis Health**
  ```bash
  docker-compose -f docker-compose.staging.yml exec redis redis-cli ping
  # Expected: PONG
  ```

- [ ] **Prometheus Health**
  ```bash
  curl -f http://localhost:9090/-/healthy
  # Expected: HTTP 200
  ```

- [ ] **Grafana Health**
  ```bash
  curl -f http://localhost:3000/api/health
  # Expected: {"database": "ok"}
  ```

- [ ] **Loki Health**
  ```bash
  curl -f http://localhost:3100/ready
  # Expected: ready
  ```

### Basic Functionality Tests

- [ ] **API Root Endpoint**
  ```bash
  curl http://localhost:8000/
  # Expected: API info response
  ```

- [ ] **Database Connection**
  ```bash
  docker-compose -f docker-compose.staging.yml exec postgres \
    psql -U staging_user -d devskyy_staging -c "SELECT 1;"
  # Expected: Query returns 1
  ```

- [ ] **Redis Connection**
  ```bash
  docker-compose -f docker-compose.staging.yml exec redis \
    redis-cli SET test_key "test_value" && \
    docker-compose -f docker-compose.staging.yml exec redis \
    redis-cli GET test_key
  # Expected: test_value
  ```

- [ ] **Static File Serving**
  ```bash
  curl -I http://localhost/static/test.css
  # Expected: HTTP 200 (if test file exists)
  ```

---

## Feature Verification Tests

### LLM Integration Tests

- [ ] **OpenAI Integration**
  ```python
  # Run test script
  python -c "
  from llm.providers.openai import OpenAIProvider
  provider = OpenAIProvider()
  response = provider.generate('Say hello', model='gpt-3.5-turbo')
  print('OK' if response else 'FAILED')
  "
  ```

- [ ] **Anthropic Integration**
  ```python
  python -c "
  from llm.providers.anthropic import AnthropicProvider
  provider = AnthropicProvider()
  response = provider.generate('Say hello', model='claude-3-haiku-20240307')
  print('OK' if response else 'FAILED')
  "
  ```

- [ ] **Google Integration**
  ```python
  python -c "
  from llm.providers.google import GoogleProvider
  provider = GoogleProvider()
  response = provider.generate('Say hello', model='gemini-pro')
  print('OK' if response else 'FAILED')
  "
  ```

- [ ] **LLM Router**
  ```python
  python -c "
  from llm.router import LLMRouter
  router = LLMRouter()
  provider = router.route_task('reasoning', priority='balanced')
  print(f'Routed to: {provider}')
  "
  ```

- [ ] **Round Table Competition**
  ```python
  python -c "
  from llm.round_table import RoundTable
  rt = RoundTable()
  result = rt.compete('What is 2+2?')
  print(f'Winner: {result.winner}')
  "
  ```

### Agent System Tests

- [ ] **CommerceAgent**
  ```bash
  curl -X POST http://localhost:8000/api/v1/agents/commerce/analyze \
    -H "Content-Type: application/json" \
    -d '{"task": "analyze_pricing", "product_id": "test-123"}'
  # Expected: JSON response with analysis
  ```

- [ ] **CreativeAgent**
  ```bash
  curl -X POST http://localhost:8000/api/v1/agents/creative/generate \
    -H "Content-Type: application/json" \
    -d '{"task": "describe_product", "description": "gothic rose pendant"}'
  # Expected: JSON response with creative output
  ```

- [ ] **MarketingAgent**
  ```bash
  curl -X POST http://localhost:8000/api/v1/agents/marketing/campaign \
    -H "Content-Type: application/json" \
    -d '{"task": "seo_keywords", "topic": "luxury jewelry"}'
  # Expected: JSON response with keywords
  ```

- [ ] **SupportAgent**
  ```bash
  curl -X POST http://localhost:8000/api/v1/agents/support/handle \
    -H "Content-Type: application/json" \
    -d '{"task": "classify_intent", "message": "I want to return my order"}'
  # Expected: JSON response with intent classification
  ```

- [ ] **OperationsAgent**
  ```bash
  curl -X POST http://localhost:8000/api/v1/agents/operations/status \
    -H "Content-Type: application/json"
  # Expected: JSON response with system status
  ```

- [ ] **AnalyticsAgent**
  ```bash
  curl -X POST http://localhost:8000/api/v1/agents/analytics/report \
    -H "Content-Type: application/json" \
    -d '{"task": "summary", "period": "day"}'
  # Expected: JSON response with analytics
  ```

### Visual Generation Tests

- [ ] **Google Imagen Integration**
  ```python
  python -c "
  from agents.visual_generation import VisualGenerationAgent
  agent = VisualGenerationAgent()
  # Test with small image for speed
  result = agent.generate_image('test product', size='256x256')
  print('OK' if result else 'FAILED')
  "
  ```

- [ ] **Tripo3D Integration**
  ```python
  python -c "
  from agents.visual_generation import VisualGenerationAgent
  agent = VisualGenerationAgent()
  # Test 3D generation
  result = agent.generate_3d_model('simple cube')
  print('OK' if result else 'FAILED')
  "
  ```

- [ ] **FASHN Virtual Try-On**
  ```python
  python -c "
  from agents.visual_generation import VisualGenerationAgent
  agent = VisualGenerationAgent()
  # Test virtual try-on
  result = agent.virtual_tryon('model.jpg', 'garment.jpg')
  print('OK' if result else 'FAILED')
  "
  ```

### RAG System Tests

- [ ] **Document Ingestion**
  ```python
  python -c "
  from orchestration.document_ingestion import DocumentIngestion
  di = DocumentIngestion()
  result = di.ingest_text('Test document content', metadata={'source': 'test'})
  print('OK' if result else 'FAILED')
  "
  ```

- [ ] **Vector Search**
  ```python
  python -c "
  from orchestration.vector_store import VectorStore
  vs = VectorStore()
  results = vs.search('test query', top_k=5)
  print(f'Found {len(results)} results')
  "
  ```

- [ ] **RAG Query**
  ```python
  python -c "
  from orchestration.prompt_engineering import PromptEngineer
  pe = PromptEngineer()
  result = pe.apply_technique('rag', 'What is SkyyRose?', {})
  print('OK' if result else 'FAILED')
  "
  ```

### WordPress Integration Tests

- [ ] **WordPress Connection**
  ```bash
  curl -I $WORDPRESS_URL
  # Expected: HTTP 200
  ```

- [ ] **WordPress API Access**
  ```bash
  curl -u "$WORDPRESS_USERNAME:$WORDPRESS_PASSWORD" \
    "$WORDPRESS_URL/wp-json/wp/v2/posts?per_page=1"
  # Expected: JSON array of posts
  ```

- [ ] **Collection Page Deployment**
  ```python
  python -c "
  from wordpress.collection_page_manager import CollectionPageManager
  manager = CollectionPageManager()
  result = manager.deploy_collection('test-collection', dry_run=True)
  print('OK' if result else 'FAILED')
  "
  ```

---

## Security Feature Tests

### Authentication & Authorization

- [ ] **Login Endpoint**
  ```bash
  curl -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username": "admin", "password": "test123"}'
  # Expected: JWT token in response
  ```

- [ ] **JWT Validation**
  ```bash
  TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username": "admin", "password": "test123"}' | jq -r '.token')

  curl -H "Authorization: Bearer $TOKEN" \
    http://localhost:8000/api/v1/protected
  # Expected: Access granted
  ```

- [ ] **Unauthorized Access**
  ```bash
  curl -I http://localhost:8000/api/v1/protected
  # Expected: HTTP 401 Unauthorized
  ```

- [ ] **Invalid Token**
  ```bash
  curl -I -H "Authorization: Bearer invalid_token" \
    http://localhost:8000/api/v1/protected
  # Expected: HTTP 401 Unauthorized
  ```

### Rate Limiting

- [ ] **Rate Limit Enforcement**
  ```bash
  # Send 110 requests rapidly (exceeds 100/hour default)
  for i in {1..110}; do
    curl -s http://localhost:8000/api/v1/test > /dev/null
  done

  # Next request should be rate limited
  curl -I http://localhost:8000/api/v1/test
  # Expected: HTTP 429 Too Many Requests
  ```

- [ ] **Rate Limit Headers**
  ```bash
  curl -I http://localhost:8000/api/v1/test
  # Expected: X-RateLimit-Limit, X-RateLimit-Remaining headers
  ```

### Encryption & Data Protection

- [ ] **PII Masking**
  ```python
  python -c "
  from security.pii_protection import mask_pii
  text = 'My SSN is 123-45-6789 and email is test@example.com'
  masked = mask_pii(text)
  print('OK' if '***' in masked else 'FAILED')
  "
  ```

- [ ] **Data Encryption**
  ```python
  python -c "
  from security.encryption import encrypt_data, decrypt_data
  plaintext = 'sensitive data'
  encrypted = encrypt_data(plaintext)
  decrypted = decrypt_data(encrypted)
  print('OK' if decrypted == plaintext else 'FAILED')
  "
  ```

- [ ] **Password Hashing**
  ```python
  python -c "
  from security.auth import hash_password, verify_password
  password = 'test123'
  hashed = hash_password(password)
  verified = verify_password(password, hashed)
  print('OK' if verified else 'FAILED')
  "
  ```

### CORS & Security Headers

- [ ] **CORS Headers**
  ```bash
  curl -I -H "Origin: https://staging.devskyy.com" \
    http://localhost:8000/api/v1/test
  # Expected: Access-Control-Allow-Origin header present
  ```

- [ ] **Security Headers**
  ```bash
  curl -I http://localhost:8000/
  # Expected: X-Content-Type-Options, X-Frame-Options, X-XSS-Protection headers
  ```

### MFA (Multi-Factor Authentication)

- [ ] **MFA Setup**
  ```bash
  curl -X POST http://localhost:8000/api/v1/auth/mfa/setup \
    -H "Authorization: Bearer $TOKEN"
  # Expected: QR code data or secret
  ```

- [ ] **MFA Verification**
  ```bash
  curl -X POST http://localhost:8000/api/v1/auth/mfa/verify \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"code": "123456"}'
  # Expected: Verification result
  ```

---

## Performance Baseline Tests

### Response Time Benchmarks

- [ ] **API Latency**
  ```bash
  # Use Apache Bench for load testing
  ab -n 1000 -c 10 http://localhost:8000/health
  # Expected: Mean response time < 100ms
  ```

- [ ] **Database Query Performance**
  ```bash
  docker-compose -f docker-compose.staging.yml exec postgres \
    psql -U staging_user -d devskyy_staging -c "EXPLAIN ANALYZE SELECT * FROM users LIMIT 100;"
  # Expected: Query time < 50ms
  ```

- [ ] **Redis Performance**
  ```bash
  docker-compose -f docker-compose.staging.yml exec redis \
    redis-benchmark -q -n 10000
  # Expected: > 10000 requests/sec
  ```

### Load Testing

- [ ] **Concurrent Users (10)**
  ```bash
  ab -n 1000 -c 10 http://localhost:8000/api/v1/test
  # Expected: 0% failed requests
  ```

- [ ] **Concurrent Users (50)**
  ```bash
  ab -n 5000 -c 50 http://localhost:8000/api/v1/test
  # Expected: < 1% failed requests
  ```

- [ ] **Sustained Load (5 minutes)**
  ```bash
  ab -t 300 -c 20 http://localhost:8000/api/v1/test
  # Expected: Consistent response times, no degradation
  ```

### Resource Utilization

- [ ] **Memory Usage**
  ```bash
  docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}"
  # Expected: All services < 80% of allocated memory
  ```

- [ ] **CPU Usage**
  ```bash
  docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}"
  # Expected: All services < 70% CPU under load
  ```

- [ ] **Disk I/O**
  ```bash
  iostat -x 1 10
  # Expected: Disk utilization < 80%
  ```

---

## Monitoring & Alerting Verification

### Prometheus Metrics

- [ ] **Prometheus Targets**
  ```bash
  curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'
  # Expected: All targets "up"
  ```

- [ ] **Application Metrics**
  ```bash
  curl -s http://localhost:8000/metrics | grep -E '(http_requests_total|http_request_duration_seconds)'
  # Expected: Metrics present and incrementing
  ```

- [ ] **Database Metrics**
  ```bash
  curl -s http://localhost:9187/metrics | grep postgres_up
  # Expected: postgres_up 1
  ```

- [ ] **Redis Metrics**
  ```bash
  curl -s http://localhost:9121/metrics | grep redis_up
  # Expected: redis_up 1
  ```

### Grafana Dashboards

- [ ] **Grafana Login**
  ```bash
  curl -c cookies.txt -X POST http://localhost:3000/login \
    -H "Content-Type: application/json" \
    -d '{"user":"'$GRAFANA_ADMIN_USER'","password":"'$GRAFANA_ADMIN_PASSWORD'"}'
  # Expected: HTTP 200
  ```

- [ ] **Datasources Healthy**
  ```bash
  curl -b cookies.txt http://localhost:3000/api/datasources | jq '.[] | {name: .name, type: .type}'
  # Expected: Prometheus and Loki datasources
  ```

- [ ] **Dashboards Load**
  ```bash
  curl -b cookies.txt http://localhost:3000/api/search | jq '.[].title'
  # Expected: List of dashboard titles
  ```

### Alert Rules

- [ ] **Alert Rules Loaded**
  ```bash
  curl -s http://localhost:9090/api/v1/rules | jq '.data.groups[].rules[] | {alert: .name, state: .state}'
  # Expected: Alert rules present
  ```

- [ ] **Test Alert Firing**
  ```bash
  # Trigger high CPU alert by running stress test
  docker-compose -f docker-compose.staging.yml exec devskyy-app \
    python -c "while True: pass" &

  # Wait 2 minutes, then check alerts
  sleep 120
  curl -s http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | {name: .labels.alertname, state: .state}'
  # Expected: HighCPUUsage alert firing

  # Kill stress process
  pkill -f "while True"
  ```

- [ ] **AlertManager Routing**
  ```bash
  curl -s http://localhost:9093/api/v2/alerts
  # Expected: JSON array of alerts
  ```

- [ ] **Slack Notification**
  ```bash
  # Send test alert
  curl -X POST http://localhost:9093/api/v1/alerts \
    -H "Content-Type: application/json" \
    -d '[{"labels":{"alertname":"TestAlert","severity":"warning"},"annotations":{"description":"Test alert from staging"}}]'

  # Check Slack channel for notification
  # Expected: Alert appears in #staging-alerts
  ```

### Loki Logs

- [ ] **Loki Ready**
  ```bash
  curl -s http://localhost:3100/ready
  # Expected: ready
  ```

- [ ] **Query Logs**
  ```bash
  curl -G -s http://localhost:3100/loki/api/v1/query_range \
    --data-urlencode 'query={job="devskyy-app"}' \
    --data-urlencode 'limit=10' | jq '.data.result[].values[]'
  # Expected: Log entries returned
  ```

- [ ] **Log Ingestion Rate**
  ```bash
  curl -s http://localhost:3100/metrics | grep loki_ingester_streams_created_total
  # Expected: Counter incrementing
  ```

---

## Integration Tests

### End-to-End Workflows

- [ ] **Product Analysis Workflow**
  ```bash
  # 1. Create product
  PRODUCT_ID=$(curl -X POST http://localhost:8000/api/v1/products \
    -H "Content-Type: application/json" \
    -d '{"name":"Gothic Rose Pendant","price":129.99}' | jq -r '.id')

  # 2. Analyze with CommerceAgent
  curl -X POST http://localhost:8000/api/v1/agents/commerce/analyze \
    -H "Content-Type: application/json" \
    -d "{\"product_id\":\"$PRODUCT_ID\"}"

  # 3. Generate visuals with CreativeAgent
  curl -X POST http://localhost:8000/api/v1/agents/creative/generate \
    -H "Content-Type: application/json" \
    -d "{\"product_id\":\"$PRODUCT_ID\"}"

  # Expected: All steps complete successfully
  ```

- [ ] **Customer Support Workflow**
  ```bash
  # 1. Create support ticket
  TICKET_ID=$(curl -X POST http://localhost:8000/api/v1/support/tickets \
    -H "Content-Type: application/json" \
    -d '{"subject":"Product inquiry","message":"What is shipping time?"}' | jq -r '.id')

  # 2. Classify intent with SupportAgent
  curl -X POST http://localhost:8000/api/v1/agents/support/classify \
    -H "Content-Type: application/json" \
    -d "{\"ticket_id\":\"$TICKET_ID\"}"

  # 3. Generate response
  curl -X POST http://localhost:8000/api/v1/agents/support/respond \
    -H "Content-Type: application/json" \
    -d "{\"ticket_id\":\"$TICKET_ID\"}"

  # Expected: Ticket classified and response generated
  ```

- [ ] **Collection Deployment Workflow**
  ```bash
  # 1. Generate 3D assets
  curl -X POST http://localhost:8000/api/v1/agents/creative/3d \
    -H "Content-Type: application/json" \
    -d '{"collection":"Black Rose Garden"}'

  # 2. Create collection page
  curl -X POST http://localhost:8000/api/v1/collections/create \
    -H "Content-Type: application/json" \
    -d '{"name":"Black Rose Garden","template":"production"}'

  # 3. Deploy to WordPress
  curl -X POST http://localhost:8000/api/v1/wordpress/deploy \
    -H "Content-Type: application/json" \
    -d '{"collection_id":"black-rose-garden"}'

  # Expected: Collection deployed to WordPress
  ```

---

## API Endpoint Tests

### Public Endpoints

- [ ] **GET /** - API Root
  ```bash
  curl http://localhost:8000/
  ```

- [ ] **GET /health** - Health Check
  ```bash
  curl http://localhost:8000/health
  ```

- [ ] **GET /docs** - API Documentation
  ```bash
  curl -I http://localhost:8000/docs
  ```

- [ ] **GET /metrics** - Prometheus Metrics
  ```bash
  curl http://localhost:8000/metrics
  ```

### Authentication Endpoints

- [ ] **POST /api/v1/auth/register**
  ```bash
  curl -X POST http://localhost:8000/api/v1/auth/register \
    -H "Content-Type: application/json" \
    -d '{"username":"testuser","email":"test@example.com","password":"Test123!"}'
  ```

- [ ] **POST /api/v1/auth/login**
  ```bash
  curl -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"testuser","password":"Test123!"}'
  ```

- [ ] **POST /api/v1/auth/refresh**
  ```bash
  curl -X POST http://localhost:8000/api/v1/auth/refresh \
    -H "Authorization: Bearer $REFRESH_TOKEN"
  ```

- [ ] **POST /api/v1/auth/logout**
  ```bash
  curl -X POST http://localhost:8000/api/v1/auth/logout \
    -H "Authorization: Bearer $TOKEN"
  ```

### Agent Endpoints

- [ ] **GET /api/v1/agents/status**
  ```bash
  curl http://localhost:8000/api/v1/agents/status
  ```

- [ ] **POST /api/v1/agents/commerce/analyze**
  ```bash
  curl -X POST http://localhost:8000/api/v1/agents/commerce/analyze \
    -H "Content-Type: application/json" \
    -d '{"task":"pricing_optimization","data":{}}'
  ```

- [ ] **POST /api/v1/agents/creative/generate**
  ```bash
  curl -X POST http://localhost:8000/api/v1/agents/creative/generate \
    -H "Content-Type: application/json" \
    -d '{"task":"product_image","prompt":"gothic jewelry"}'
  ```

- [ ] **POST /api/v1/agents/roundtable**
  ```bash
  curl -X POST http://localhost:8000/api/v1/agents/roundtable \
    -H "Content-Type: application/json" \
    -d '{"query":"What is the best pricing strategy?"}'
  ```

---

## Agent System Tests

### Base Agent Functionality

- [ ] **Agent Initialization**
  ```python
  python -c "
  from agents.base_super_agent import EnhancedSuperAgent
  agent = EnhancedSuperAgent(name='TestAgent')
  print('OK' if agent.name == 'TestAgent' else 'FAILED')
  "
  ```

- [ ] **Prompt Technique Selection**
  ```python
  python -c "
  from agents.base_super_agent import EnhancedSuperAgent, TaskCategory
  agent = EnhancedSuperAgent(name='TestAgent')
  technique = agent._select_technique(TaskCategory.REASONING)
  print(f'Selected: {technique}')
  "
  ```

- [ ] **Tool Execution**
  ```python
  python -c "
  from agents.base_super_agent import EnhancedSuperAgent
  agent = EnhancedSuperAgent(name='TestAgent')
  result = agent.use_tool('echo', {'message': 'test'})
  print('OK' if result else 'FAILED')
  "
  ```

### ML Capabilities

- [ ] **Regression Model**
  ```python
  python -c "
  from agents.base_super_agent import EnhancedSuperAgent
  agent = EnhancedSuperAgent(name='TestAgent')
  import numpy as np
  X = np.array([[1], [2], [3], [4]])
  y = np.array([2, 4, 6, 8])
  model = agent.ml.train_regression(X, y)
  pred = agent.ml.predict(model, [[5]])
  print('OK' if abs(pred[0] - 10) < 1 else 'FAILED')
  "
  ```

- [ ] **Classification Model**
  ```python
  python -c "
  from agents.base_super_agent import EnhancedSuperAgent
  agent = EnhancedSuperAgent(name='TestAgent')
  import numpy as np
  X = np.array([[1, 2], [2, 3], [3, 4], [4, 5]])
  y = np.array([0, 0, 1, 1])
  model = agent.ml.train_classification(X, y)
  pred = agent.ml.predict(model, [[5, 6]])
  print(f'Predicted class: {pred[0]}')
  "
  ```

- [ ] **Time Series Forecasting**
  ```python
  python -c "
  from agents.base_super_agent import EnhancedSuperAgent
  import pandas as pd
  agent = EnhancedSuperAgent(name='TestAgent')
  df = pd.DataFrame({
    'ds': pd.date_range('2024-01-01', periods=30),
    'y': list(range(30))
  })
  forecast = agent.ml.forecast(df, periods=7)
  print(f'Forecasted {len(forecast)} periods')
  "
  ```

---

## Regression Test Suite

### Critical User Journeys

- [ ] **User Registration & Login Flow**
- [ ] **Product Creation & Management**
- [ ] **Agent Task Execution**
- [ ] **Round Table Competition**
- [ ] **3D Asset Generation**
- [ ] **WordPress Deployment**
- [ ] **Alert Notification Delivery**
- [ ] **Backup & Restore**

### Data Integrity

- [ ] **Database Constraints**
- [ ] **Foreign Key Relationships**
- [ ] **Data Validation Rules**
- [ ] **Transaction Rollback**

### Performance Regression

- [ ] **API Response Times** (compare to baseline)
- [ ] **Database Query Performance**
- [ ] **Memory Footprint**
- [ ] **Startup Time**

---

## Test Completion Summary

**Date Tested:** _________________
**Tested By:** _________________
**Overall Status:** [ ] PASS [ ] FAIL [ ] PARTIAL

### Failed Tests

| Test Name | Expected | Actual | Notes |
|-----------|----------|--------|-------|
|           |          |        |       |
|           |          |        |       |

### Known Issues

1. _______________________________________________
2. _______________________________________________
3. _______________________________________________

### Sign-Off

- [ ] All critical tests passed
- [ ] Known issues documented
- [ ] Stakeholders notified of results
- [ ] Deployment approved for production

**Approved By:** _________________
**Date:** _________________

---

**Document Version:** 1.0
**Last Updated:** 2025-12-19
