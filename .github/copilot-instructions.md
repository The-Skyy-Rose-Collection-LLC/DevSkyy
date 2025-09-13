# DevSkyy AI Agent Platform - Developer Instructions

**Always reference these instructions first and fallback to search or bash commands only when you encounter unexpected information that does not match the info here.**

DevSkyy is a production-ready luxury streetwear AI agent management platform featuring 14+ specialized AI agents, FastAPI backend, React frontend, and Jekyll documentation deployment.

## Core Architecture
- **Backend**: Python 3.12+ FastAPI application with 14+ specialized AI agents for luxury fashion e-commerce
- **Frontend**: React 18 + Vite development server with Tailwind CSS luxury theming
- **Database**: MongoDB (required for production operations)
- **Documentation**: Jekyll-based GitHub Pages deployment
- **AI Agents**: Brand Intelligence, E-commerce, Financial, WordPress, SEO, Customer Service, and more

## Working Effectively

### Bootstrap and Build Commands (VALIDATED)
Run these commands in exact order:

1. **Install Python dependencies** (takes ~35 seconds):
   ```bash
   pip install -r backend/requirements.txt
   ```
   - NEVER CANCEL: Set timeout to 120+ seconds minimum
   - Dependencies include FastAPI, MongoDB, OpenAI, computer vision, and ML libraries

2. **Test backend loading** (takes ~2 seconds):
   ```bash
   python3 -c "from main import app; print('✅ Backend loads successfully')"
   ```
   - Should output: "✅ Backend loads successfully"
   - May show INFO logs for Brand Intelligence and Enhanced Learning initialization

3. **Install frontend dependencies** (takes ~10 seconds):
   ```bash
   cd frontend && npm install
   ```
   - NEVER CANCEL: Set timeout to 60+ seconds minimum
   - Automatically installs React, Vite, Tailwind CSS, and luxury UI components

4. **Install terser for production builds**:
   ```bash
   cd frontend && npm install terser --save-dev
   ```
   - Required for production builds to work

5. **Build frontend** (takes ~5 seconds):
   ```bash
   cd frontend && npm run build
   ```
   - Creates optimized production build in `frontend/build/`
   - Outputs bundle size analysis

### Running the Platform

#### Backend Server (Primary)
```bash
cd /home/runner/work/DevSkyy/DevSkyy
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```
- Starts FastAPI server with all 14+ AI agents
- Access at: http://localhost:8000
- API documentation: http://localhost:8000/docs
- Health check: http://localhost:8000/health

#### Frontend Development Server
```bash
cd frontend && npm run dev
```
- Starts Vite development server at http://localhost:3000
- Hot reload enabled for development
- Connects to backend at localhost:8000

#### Quick Setup Script (VALIDATED - works in 10 seconds)
```bash
bash scripts/quick_start.sh
```
- Runs complete setup: dependencies + build + test + .env creation
- NEVER CANCEL: Set timeout to 300+ seconds
- Creates `.env` file with required configuration templates

## Validation and Testing

### Manual Validation Requirements
**ALWAYS run through these complete scenarios after making changes:**

1. **Backend API Validation**:
   ```bash
   # Test core endpoints
   curl http://localhost:8000/                    # Should return platform info
   curl http://localhost:8000/health              # Should return service status
   curl http://localhost:8000/docs                # Should return OpenAPI docs
   ```

2. **Agent Functionality Test**:
   ```bash
   # Test brand intelligence
   curl http://localhost:8000/brand/intelligence | python3 -m json.tool
   ```

3. **Product Creation Workflow** (requires all fields):
   ```bash
   curl -X POST http://localhost:8000/products/add \
     -H "Content-Type: application/json" \
     -d '{"name": "Test Item", "category": "clothing", "price": 299.99, "description": "Test", "cost": 150.00, "stock_quantity": 10, "sku": "TST-001"}'
   ```

### Build Time Expectations
- **Python dependencies**: 30-40 seconds - NEVER CANCEL, set timeout 120+ seconds
- **Frontend dependencies**: 8-12 seconds - NEVER CANCEL, set timeout 60+ seconds  
- **Frontend build**: 4-6 seconds - NEVER CANCEL, set timeout 60+ seconds
- **Backend startup**: 1-3 seconds
- **Quick start script**: 8-12 seconds total - NEVER CANCEL, set timeout 300+ seconds

### Known Issues and Workarounds
- **Jekyll Build**: Requires `bundle install` - Jekyll dependencies not installed by default
- **Tests**: Use pytest but not installed - focus on manual API testing instead
- **Linting**: autopep8 installed but has lib2to3 dependency issues - use basic syntax checking
- **MongoDB**: Platform runs without DB but agent operations will fail - this is expected for development

## Project Structure

### Key Files and Directories
```
/home/runner/work/DevSkyy/DevSkyy/
├── main.py                 # FastAPI application entry point with all endpoints
├── startup.py              # Platform initialization and MongoDB connection
├── config.py               # Environment configuration management
├── backend/
│   ├── requirements.txt    # Python dependencies (validated working)
│   └── server.py          # Additional backend server configuration
├── frontend/
│   ├── package.json       # Node.js dependencies (validated working)
│   ├── vite.config.js     # Build configuration
│   └── src/               # React application source
├── agent/
│   ├── modules/           # 14+ specialized AI agent implementations
│   ├── scheduler/         # Background task scheduling
│   └── config/            # Agent configuration files
├── scripts/
│   ├── quick_start.sh     # Complete setup script (VALIDATED)
│   ├── start_replit.sh    # Replit deployment script
│   └── build_*.sh         # Various build scripts
└── tests/                 # Test files (require pytest)
```

### Agent Modules (Key Components)
- `brand_intelligence_agent.py` - Brand analysis and market intelligence
- `ecommerce_agent.py` - Product management and order processing  
- `financial_agent.py` - Payment processing and financial analysis
- `wordpress_agent.py` - WordPress integration and management
- `seo_marketing_agent.py` - SEO optimization and marketing automation
- `customer_service_agent.py` - Customer support automation

## Development Workflow

### Making Changes
1. **Always start servers first** to establish baseline functionality
2. **Test endpoints manually** after making backend changes
3. **Check frontend hot reload** after making UI changes
4. **Run validation scenarios** before committing

### Before Committing
1. **Validate backend loads**: `python3 -c "from main import app; print('✅ OK')"`
2. **Test critical endpoints**: health, brand intelligence, product creation
3. **Verify frontend builds**: `cd frontend && npm run build`
4. **Document any new timing requirements**

### Environment Variables (Optional)
The platform creates `.env` template automatically. Key variables:
- `OPENAI_API_KEY` - For AI agent capabilities
- `MONGODB_URL` - Database connection (defaults to localhost)
- `WORDPRESS_URL` - WordPress integration endpoint
- `NODE_ENV` - Environment setting (development/production)

## Deployment Options

### Local Development
- Use `scripts/quick_start.sh` for complete setup
- Backend: `python3 -m uvicorn main:app --host 0.0.0.0 --port 8000`
- Frontend: `cd frontend && npm run dev`

### Replit Deployment  
- Use `scripts/start_replit.sh` (includes MongoDB setup)
- Handles service management and auto-configuration

### GitHub Pages (Jekyll)
- Automatic deployment via `.github/workflows/jekyll-gh-pages.yml`
- Builds documentation and marketing site
- Requires bundle install for local Jekyll testing

## Common Tasks Reference

### Backend Health Check
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","services":{"api":"operational"}}
```

### Agent Status Check
```bash
curl http://localhost:8000/brand/intelligence | python3 -m json.tool
# Expected: JSON with brand identity and values
```

### Frontend Development
```bash
cd frontend && npm run dev
# Access at http://localhost:3000 with hot reload
```

### Production Build Test
```bash
cd frontend && npm run build
# Should complete in ~5 seconds with bundle analysis
```
