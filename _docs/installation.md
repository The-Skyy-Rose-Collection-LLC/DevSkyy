---
layout: default
title: Installation Guide
permalink: /docs/installation/
---

# Installation Guide

Get started with The Skyy Rose Collection DevSkyy Platform in minutes.

## Prerequisites

- Python 3.8+ for backend
- Node.js 18+ for frontend
- Git for version control
- Ruby 3.0+ for Jekyll (optional)

## Quick Setup Options

### Option 1: GitHub Pages (Static Site)

1. **Fork the Repository**
   ```bash
   # Visit: https://github.com/SkyyRoseLLC/DevSkyy
   # Click "Fork" to create your copy
   ```

2. **Enable GitHub Pages**
   - Go to your fork's Settings
   - Navigate to Pages section
   - Set source to "GitHub Actions"
   - Your site will be live at `https://yourusername.github.io/DevSkyy`

### Option 2: Local Jekyll Development

1. **Clone the Repository**
   ```bash
   git clone https://github.com/SkyyRoseLLC/DevSkyy.git
   cd DevSkyy
   ```

2. **Install Jekyll Dependencies**
   ```bash
   gem install bundler jekyll
   bundle install
   ```

3. **Start Jekyll Server**
   ```bash
   bundle exec jekyll serve
   # Visit: http://localhost:4000
   ```

### Option 3: Full Platform Deployment

1. **Clone and Setup**
   ```bash
   git clone https://github.com/SkyyRoseLLC/DevSkyy.git
   cd DevSkyy
   ```

2. **Backend Setup**
   ```bash
   # Install Python dependencies
   pip install -r backend/requirements.txt
   
   # Configure environment variables
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```

4. **Start the Platform**
   ```bash
   # Start backend server
   uvicorn main:app --host 0.0.0.0 --port 8000
   
   # In another terminal, start frontend
   cd frontend && npm run dev
   ```

### Option 4: Replit Deployment

1. **Import to Replit**
   - Visit [Replit](https://replit.com)
   - Click "Import from GitHub"
   - Enter: `SkyyRoseLLC/DevSkyy`

2. **Auto-Configuration**
   - The `.replit` file handles automatic setup
   - Click "Run" to start the platform
   - Access via your Replit URL

## Environment Configuration

### Required Environment Variables

```bash
# API Configuration
OPENAI_API_KEY=your_openai_key_here
WORDPRESS_SITE_URL=https://your-site.com
WORDPRESS_USERNAME=your_username
WORDPRESS_PASSWORD=your_app_password

# Database (optional for local development)
MONGODB_URI=your_mongodb_connection_string

# Email Services (optional)
SMTP_HOST=your_smtp_host
SMTP_USER=your_smtp_user
SMTP_PASS=your_smtp_password
```

### WordPress Integration

For full platform functionality, configure WordPress:

1. **Create Application Password**
   - Go to your WordPress admin: Users → Profile
   - Scroll to "Application Passwords"
   - Generate new password for "DevSkyy Platform"

2. **Configure Connection**
   ```bash
   WORDPRESS_SITE_URL=https://yoursite.com
   WORDPRESS_USERNAME=your_username
   WORDPRESS_PASSWORD=your_app_password
   ```

## Verification

### Test Jekyll Site
```bash
bundle exec jekyll serve
# Visit: http://localhost:4000
```

### Test Full Platform
```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend
curl http://localhost:3000
```

### Test API Endpoints
```bash
# Dashboard
curl http://localhost:8000/dashboard

# Run agent workflow
curl -X POST http://localhost:8000/run
```

## Troubleshooting

### Common Issues

**Jekyll Build Errors**
```bash
# Update gems
bundle update

# Clear cache
bundle exec jekyll clean
bundle exec jekyll build
```

**Python Dependencies**
```bash
# Use virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

pip install -r backend/requirements.txt
```

**Node.js Issues**
```bash
# Clear cache
rm -rf frontend/node_modules
cd frontend && npm install
```

**Port Conflicts**
```bash
# Use different ports
uvicorn main:app --port 8001
cd frontend && npm run dev -- --port 3001
```

## Next Steps

- [Explore API Reference](/docs/api-reference/)
- [Configure AI Agents](/docs/agent-guide/)
- [Deploy WordPress Themes](/docs/theme-deployment/)
- [Monitor Performance](/docs/monitoring/)

## Support

Need help? Join our community:
- 📧 Email: [support@skyyrose.co](mailto:support@skyyrose.co)
- 💬 GitHub Issues: [Report a bug](https://github.com/SkyyRoseLLC/DevSkyy/issues)
- 🌟 Star the repo if you find it helpful!