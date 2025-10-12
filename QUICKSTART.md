# DevSkyy - Quick Start Guide

🚀 **Enterprise AI Platform for Luxury E-Commerce**

## Prerequisites

- **Python 3.11+** (with pip)
- **Node.js 18+** (with npm)
- **Git**

## 🎯 Quick Start (5 minutes)

### 1. Clone & Setup

```bash
# Clone the repository
git clone https://github.com/SkyyRoseLLC/DevSkyy.git
cd DevSkyy

# Create environment file
cp .env.example .env

# Edit .env and add your API keys:
# - ANTHROPIC_API_KEY (required)
# - OPENAI_API_KEY (optional)
```

### 2. Install Dependencies

**Backend:**
```bash
pip install -r requirements.txt
```
⏱️ Takes ~60-90 seconds

**Frontend:**
```bash
cd frontend
npm install
cd ..
```
⏱️ Takes ~30-45 seconds

### 3. Run the Application

**Terminal 1 - Backend:**
```bash
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### 4. Access the Application

- 🌐 **Frontend**: http://localhost:5173
- 📚 **API Docs**: http://localhost:8000/docs
- ❤️ **Health Check**: http://localhost:8000/health

## 📦 What's Included

### Backend (`/`)
- **FastAPI** - High-performance async API framework
- **57 AI Agents** - Specialized agents in `agent/modules/`
- **SQLAlchemy** - Database ORM with SQLite/PostgreSQL/MySQL support
- **Enterprise Security** - JWT auth, rate limiting, CORS

### Frontend (`/frontend`)
- **React 18 + TypeScript** - Modern React with full type safety
- **Vite** - Lightning-fast build tool
- **Tailwind CSS** - Utility-first styling
- **Framer Motion** - Smooth animations

## 🔧 Configuration

### Required Environment Variables

```env
# Core AI (Required)
ANTHROPIC_API_KEY=your_key_here

# Database (Optional - defaults to SQLite)
DATABASE_URL=sqlite+aiosqlite:///./devskyy.db

# Security
SECRET_KEY=your_secret_key_here
JWT_SECRET=your_jwt_secret_here
```

### Optional Environment Variables

```env
# Additional AI Models
OPENAI_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here

# Social Media
META_ACCESS_TOKEN=your_token_here
ELEVENLABS_API_KEY=your_key_here

# See .env.example for complete list
```

## 🧪 Testing

### Backend Tests
```bash
pytest tests/
```

### Frontend Build
```bash
cd frontend
npm run build
```

### Production Safety Check
```bash
python production_safety_check.py
```

## 🚀 Production Deployment

### Using Docker
```bash
docker build -t devskyy .
docker run -p 8000:8000 --env-file .env devskyy
```

### Manual Deployment
```bash
# Install dependencies
pip install -r requirements.txt
cd frontend && npm install && npm run build && cd ..

# Run with Uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📁 Project Structure

```
DevSkyy/
├── main.py                 # FastAPI application entry point
├── agent/
│   ├── modules/            # 57 specialized AI agents
│   ├── orchestrator.py     # Agent coordination
│   ├── registry.py         # Agent registry
│   └── security_manager.py # Security controls
├── backend/                # Backend utilities
├── frontend/               # React TypeScript app
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── types/         # TypeScript definitions
│   │   └── App.tsx        # Main app component
│   └── package.json
├── requirements.txt        # Python dependencies
└── .env.example           # Environment template
```

## 🤝 Common Issues

### Port Already in Use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Kill process on port 5173
lsof -ti:5173 | xargs kill -9
```

### Module Import Errors
```bash
# Reinstall Python packages
pip install --force-reinstall -r requirements.txt
```

### Frontend Build Errors
```bash
# Clear cache and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

## 📚 Documentation

- **API Documentation**: http://localhost:8000/docs (when running)
- **CLAUDE.md**: Comprehensive developer guide
- **SECURITY.md**: Security policies and practices
- **DEPLOYMENT_*.md**: Deployment guides

## 🆘 Support

- **Issues**: https://github.com/SkyyRoseLLC/DevSkyy/issues
- **Discussions**: https://github.com/SkyyRoseLLC/DevSkyy/discussions

## 🎯 Next Steps

1. ✅ **Start the application** (follow steps above)
2. 📖 **Read CLAUDE.md** for detailed architecture
3. 🔒 **Review SECURITY.md** for security best practices
4. 🚀 **Check DEPLOYMENT_READY.md** for production deployment

---

**Built with ❤️ by Skyy Rose LLC**
