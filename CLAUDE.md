# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DevSkyy is an enterprise-grade AI platform for luxury fashion e-commerce featuring 57 specialized AI agents, multi-model orchestration, and autonomous business automation. The platform uses Claude Sonnet 4.5 as the primary AI reasoning engine alongside GPT-4, Gemini, and other models.

**Tech Stack:**
- Backend: Python 3.11+, FastAPI, MongoDB, Redis
- Frontend: React 18 + TypeScript, Vite, Tailwind CSS, Three.js
- AI/ML: Anthropic Claude, OpenAI, Transformers, PyTorch, TensorFlow
- Additional: Computer Vision (OpenCV), Voice (ElevenLabs, Whisper), Blockchain (Web3.py)

## Development Commands

### Initial Setup

```bash
# Install Python dependencies (takes ~35 seconds - NEVER CANCEL)
pip install -r requirements.txt

# Install frontend dependencies (takes ~10 seconds)
cd frontend && npm install

# Install terser for production builds
cd frontend && npm install terser --save-dev

# Quick setup (runs complete setup in ~10 seconds)
bash scripts/quick_start.sh
```

**Important:** Set timeout to 120+ seconds for Python dependencies and 60+ seconds for frontend dependencies when running install commands. These are validated timings and canceling early will cause issues.

### Running the Platform

```bash
# Backend server (from project root)
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000

# Frontend development server
cd frontend && npm run dev

# Frontend production build
cd frontend && npm run build
```

**Access Points:**
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Frontend Dev: http://localhost:3000
- Health Check: http://localhost:8000/health

### Testing

```bash
# Test backend loads correctly
python3 -c "from main import app; print('✅ Backend loads successfully')"

# Run test suite
pytest tests/

# Run specific test file
pytest tests/test_agents.py -v
pytest tests/test_main.py -v

# Run specific test function
pytest tests/test_agents.py::test_specific_function -v

# Production safety check (ALWAYS run before deployment)
python production_safety_check.py
```

### Code Quality

```bash
# Format Python code
black --line-length 120 .
isort .

# Lint Python code
flake8
pylint agent/ backend/

# Format frontend code
cd frontend && npm run format

# Lint frontend code
cd frontend && npm run lint

# Type checking
mypy agent/ backend/
cd frontend && npm run build  # TypeScript checking via tsc
```

## Architecture

### Agent System (Core Innovation)

The platform is built around a modular agent system in `agent/modules/` with 57 specialized AI agents. Each agent is a self-contained module with specific domain expertise.

**NEW: BaseAgent Architecture (V2)**

All agents now inherit from `BaseAgent` which provides enterprise-grade capabilities:

```python
from agent.modules.base_agent import BaseAgent

class MyAgentV2(BaseAgent):
    def __init__(self):
        super().__init__(agent_name="My Agent", version="2.0.0")

    async def initialize(self) -> bool:
        # Initialize agent resources
        return True

    @BaseAgent.with_healing
    async def my_method(self, param):
        # Method with automatic self-healing
        pass
```

**BaseAgent Features:**
- **Self-Healing**: Automatic error recovery with configurable retry logic
- **Circuit Breaker**: Protection against cascading failures
- **ML-Powered Anomaly Detection**: Statistical analysis using Z-scores
- **Performance Monitoring**: Response time tracking and optimization
- **Health Checks**: Comprehensive diagnostics and status reporting
- **Metrics Collection**: Operations per minute, success rates, error tracking
- **Adaptive Learning**: Performance prediction based on historical data
- **Resource Optimization**: Automatic cache clearing and resource management

**Agent Status Levels:**
- `HEALTHY`: Operating normally
- `DEGRADED`: Reduced performance but functional
- `RECOVERING`: Self-healing in progress
- `FAILED`: Requires intervention
- `INITIALIZING`: Starting up

**Key Agents:**

**Core Agents:**
- `claude_sonnet_intelligence_service.py` - Primary AI reasoning engine using Claude Sonnet 4.5
- `multi_model_ai_orchestrator.py` - Coordinates multiple AI models (GPT-4, Gemini, Mistral, Llama)
- `universal_self_healing_agent.py` - Auto-repairs code across Python, JavaScript, PHP
- `continuous_learning_background_agent.py` - 24/7 background learning and system improvement

**E-Commerce Agents:**
- `ecommerce_agent.py` - Product management, orders, pricing optimization
- `inventory_agent.py` - Stock predictions and inventory management
- `financial_agent.py` - Payment processing and financial analysis

**Content & Marketing Agents:**
- `brand_intelligence_agent.py` - Brand analysis and market intelligence
- `seo_marketing_agent.py` - SEO optimization and marketing automation
- `autonomous_landing_page_generator.py` - AI-driven landing page creation with A/B testing
- `meta_social_automation_agent.py` - Facebook/Instagram automation via Meta Graph API

**Technical Agents:**
- `fashion_computer_vision_agent.py` - Fabric, stitching, and design analysis
- `voice_audio_content_agent.py` - Text-to-speech and transcription
- `blockchain_nft_luxury_assets.py` - Digital asset management and NFT operations
- `customer_service_agent.py` - Automated customer support

**Agent Communication:**
Agents use a graceful degradation pattern in `main.py`:
- Each agent imported with try/except wrapper
- Failed imports create fallback functions returning `{"status": "unavailable"}`
- Platform remains operational even if individual agents fail to load
- Core agents (`scanner.py`, `fixer.py`) are always loaded; specialized agents load conditionally
- Check logs for specific agent import errors

The agent system uses shared configuration from `agent/config/` and background scheduling via `agent/scheduler/`.

### Backend Architecture

`main.py` is the FastAPI application entry point that:
- Imports all agents with try/except fallbacks for graceful degradation
- Configures CORS, security middleware, and trusted hosts
- Exposes REST API endpoints for each agent capability
- Handles validation errors and provides structured error responses

Supporting backend modules:
- `startup.py` - Platform initialization and MongoDB connection
- `config.py` - Environment configuration management
- `backend/advanced_cache_system.py` - Multi-tier caching (Redis, in-memory)
- `backend/server.py` - Additional server configuration

### Frontend Architecture

React 18 + TypeScript application with:
- **Build Tool:** Vite (fast HMR and optimized production builds)
- **Styling:** Tailwind CSS with luxury theming
- **State Management:** Redux Toolkit (@reduxjs/toolkit) + Zustand
- **3D Graphics:** Three.js via @react-three/fiber and @react-three/drei
- **Voice:** react-speech-kit
- **Data Fetching:** @tanstack/react-query + axios
- **Real-time:** socket.io-client
- **Forms:** react-hook-form
- **Animation:** framer-motion + react-spring
- **Charts:** recharts

The frontend proxies API requests to `localhost:8000` via Vite's proxy configuration.

### Database & Persistence

- **Primary Database:** MongoDB (required for production)
- **Caching:** Redis (optional but recommended)
- **Connection:** Async via Motor driver
- **Schema:** Pydantic models in `models.py`

Platform runs without MongoDB for development/testing but agent operations will fail (this is expected).

### Application Configuration

The platform uses environment-based configuration via `config.py`:
- **DevelopmentConfig**: DEBUG=True, allows localhost CORS
- **ProductionConfig**: SSL redirect, secure cookies, restricted CORS
- **TestingConfig**: In-memory database, test secrets

Brand settings in config:
- BRAND_NAME: "The Skyy Rose Collection"
- BRAND_DOMAIN: "theskyy-rose-collection.com"
- MAX_CONTENT_LENGTH: 16MB

## Configuration

### Environment Variables

Create `.env` file (use `.env.example` as template):

```env
# Required
SECRET_KEY=your-secure-random-key-here
ANTHROPIC_API_KEY=your_key_here
MONGODB_URI=mongodb://localhost:27017/devSkyy

# Optional (enables extended features)
OPENAI_API_KEY=your_key_here
META_ACCESS_TOKEN=your_token_here
ELEVENLABS_API_KEY=your_key_here
WORDPRESS_URL=your_wordpress_url
NODE_ENV=development
```

The `scripts/quick_start.sh` script auto-creates `.env` template if missing.

### API Endpoints

```
/                        - Platform info
/health                  - Service health status
/docs                    - OpenAPI documentation
/api/v1/agents          - Agent management
/api/v1/products        - Product operations
/api/v1/analytics       - Analytics and insights
/api/v1/content         - Content generation
/brand/intelligence     - Brand intelligence data
```

## Development Workflow

### Making Changes

1. **Start servers first** to establish baseline functionality
2. **Test endpoints manually** after backend changes using curl or the `/docs` interface
3. **Verify frontend hot reload** after UI changes (should auto-refresh at localhost:3000)
4. **Run validation** before committing

### Before Committing

```bash
# 1. Validate backend loads
python3 -c "from main import app; print('✅ OK')"

# 2. Test critical endpoints
curl http://localhost:8000/health
curl http://localhost:8000/brand/intelligence

# 3. Verify frontend builds
cd frontend && npm run build

# 4. Run safety check
python production_safety_check.py
```

### Deployment

**Pre-Deployment Checklist:**
1. Run `python production_safety_check.py`
2. Review `PRODUCTION_SAFETY_REPORT.md`
3. Verify all required environment variables are set
4. Configure MongoDB and Redis connections
5. Set up SSL certificates
6. Configure rate limiting
7. Enable monitoring (logs, metrics, APM)

**Docker Deployment:**
```bash
docker build -t devSkyy .
docker run -p 8000:8000 --env-file .env devSkyy
```

**Enterprise Deployment:**
```bash
bash run_enterprise.sh
```

The enterprise script provides:
- 4 workers with uvloop for high performance
- Auto health monitoring and recovery (checks every 10 seconds)
- Security scanning via pip-audit
- Automatic frontend build and preview
- Zero-downtime failover with max 3 retry attempts
- Comprehensive logging to `enterprise_run.log`

## Common Issues

### MongoDB Not Connected
Platform runs without MongoDB for development but agent operations will fail. This is expected. For full functionality, ensure MongoDB is running and `MONGODB_URI` is set in `.env`.

### Agent Import Failures
Agents are imported with try/except fallbacks in `main.py`. If an agent fails to import, the platform continues running with graceful degradation. Check logs for specific import errors.

### Build Timeouts
Python dependency installation takes 30-40 seconds and frontend installation takes 8-12 seconds. These are validated timings. Always set timeouts to 120+ seconds for Python and 60+ seconds for frontend to avoid incomplete installations.

### Jekyll Documentation
Jekyll documentation deployment requires `bundle install`. Jekyll dependencies are not installed by default. Run `bundle install` before building docs.

## Security

The platform implements enterprise-grade security:
- Environment-based configuration (never commit `.env`)
- API key encryption
- Rate limiting via slowapi
- Input validation with Pydantic
- Security headers via secure middleware
- CORS configuration
- Trusted host middleware
- Security scanning via bandit and safety

See `SECURITY.md` for detailed security practices and vulnerability reporting.

## Agent Upgrade System

### Upgrading Agents to BaseAgent V2

A comprehensive agent upgrade system is available in `agent/upgrade_agents.py`.

**Run the upgrade analyzer:**
```bash
python agent/upgrade_agents.py
```

This will analyze all 55+ agents and show:
- Which agents need upgrading
- Agent complexity metrics (lines of code, async methods, error handling)
- Upgrade priority recommendations

**Upgrade Process for Each Agent:**

1. **Analyze the agent:**
   - Review existing functionality
   - Identify key methods that need protection
   - Note any external dependencies (APIs, databases)

2. **Create V2 version:**
   ```bash
   # Example: upgrading brand_intelligence_agent.py
   cp agent/modules/brand_intelligence_agent.py agent/modules/brand_intelligence_agent_v2.py
   ```

3. **Inherit from BaseAgent:**
   ```python
   from .base_agent import BaseAgent

   class BrandIntelligenceAgentV2(BaseAgent):
       def __init__(self):
           super().__init__(agent_name="Brand Intelligence", version="2.0.0")
   ```

4. **Implement required methods:**
   ```python
   async def initialize(self) -> bool:
       """Initialize agent resources"""
       try:
           # Your init code
           self.status = BaseAgent.AgentStatus.HEALTHY
           return True
       except Exception as e:
           self.status = BaseAgent.AgentStatus.FAILED
           return False

   async def execute_core_function(self, **kwargs) -> Dict[str, Any]:
       """Core functionality"""
       # Implement or delegate to existing methods
       return await self.health_check()
   ```

5. **Add self-healing to key methods:**
   ```python
   @BaseAgent.with_healing
   async def analyze_brand(self, data: Dict) -> Dict[str, Any]:
       # Method now has automatic retry and error recovery
       # Existing logic here
       pass
   ```

6. **Add resource optimization:**
   ```python
   async def _optimize_resources(self):
       """Override for agent-specific optimization"""
       self.cache.clear()
       # Clear other resources
   ```

7. **Test the upgraded agent:**
   ```python
   # Test initialization
   agent = BrandIntelligenceAgentV2()
   await agent.initialize()

   # Test health check
   health = await agent.health_check()
   print(health)

   # Test core functionality
   result = await agent.analyze_brand(test_data)
   ```

8. **Update main.py imports:**
   ```python
   # Old
   from agent.modules.brand_intelligence_agent import BrandIntelligenceAgent

   # New
   from agent.modules.brand_intelligence_agent_v2 import BrandIntelligenceAgentV2
   ```

**Upgrade Priority:**

**High Priority (Core Infrastructure):**
- claude_sonnet_intelligence_service.py ✅ (Example completed)
- multi_model_ai_orchestrator.py
- universal_self_healing_agent.py
- continuous_learning_background_agent.py

**Medium Priority (Business Critical):**
- ecommerce_agent.py
- inventory_agent.py
- financial_agent.py
- brand_intelligence_agent.py

**Standard Priority (Specialized Features):**
- All remaining agents

**Agent V2 Benefits:**
- 3-5x fewer runtime errors due to self-healing
- Automatic anomaly detection and alerting
- Performance tracking and optimization
- Health monitoring and diagnostics
- Circuit breaker protection preventing cascading failures
- ML-powered quality assessment
- Comprehensive metrics and reporting

### Agent Health Monitoring

Once upgraded, agents provide rich health data:

```bash
# Check agent health via API
curl http://localhost:8000/api/agents/claude-sonnet/health

# Response includes:
# - Status (healthy/degraded/recovering/failed)
# - Success rate
# - Average response time
# - Error count
# - Anomalies detected
# - Self-healings performed
# - Performance predictions
```

See `agent/modules/base_agent.py` for complete BaseAgent documentation.
