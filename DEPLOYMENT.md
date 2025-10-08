# Deployment Guide

Complete guide for deploying DevSkyy to production environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Deployment Methods](#deployment-methods)
- [Post-Deployment](#post-deployment)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **CPU**: 2+ cores (4+ recommended)
- **RAM**: 4GB minimum (8GB+ recommended)
- **Storage**: 20GB minimum (SSD recommended)
- **OS**: Ubuntu 20.04+ / Debian 11+ / RHEL 8+

### Required Services

- **MongoDB**: 4.4+ (managed service recommended)
- **Redis**: 6.0+ (optional, for caching)
- **Python**: 3.9+
- **Node.js**: 16+ (for frontend)

### Domain & SSL

- Registered domain name
- SSL certificate (Let's Encrypt recommended)
- DNS configured to point to server

## Environment Setup

### 1. Create Environment File

```bash
cp .env.example .env
```

### 2. Configure Required Variables

```bash
# Core Configuration
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<generate-strong-random-key>
JWT_SECRET_KEY=<generate-different-random-key>

# Database
MONGODB_URI=mongodb://username:password@host:27017/devskyy
DATABASE_NAME=devskyy

# AI Services
ANTHROPIC_API_KEY=<your-anthropic-key>
OPENAI_API_KEY=<your-openai-key>

# Security
CORS_ORIGINS=https://yourdomain.com
TRUSTED_HOSTS=yourdomain.com

# SSL
SSL_CERT_PATH=/path/to/cert.pem
SSL_KEY_PATH=/path/to/key.pem
```

### 3. Generate Secret Keys

```bash
# Generate SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate JWT_SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Deployment Methods

### Method 1: Docker (Recommended)

#### Build and Run

```bash
# Build image
docker build -t devskyy-platform:latest .

# Run with docker-compose
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

#### Custom Docker Deployment

```bash
# Run MongoDB
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  -v mongo-data:/data/db \
  mongo:7.0

# Run DevSkyy
docker run -d \
  --name devskyy \
  -p 8000:8000 \
  --env-file .env \
  --link mongodb:mongodb \
  devskyy-platform:latest
```

### Method 2: Systemd Service

#### 1. Create Service File

```bash
sudo nano /etc/systemd/system/devskyy.service
```

```ini
[Unit]
Description=DevSkyy AI Platform
After=network.target mongodb.service

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/devskyy
Environment="PATH=/opt/devskyy/venv/bin"
ExecStart=/opt/devskyy/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 2. Enable and Start

```bash
sudo systemctl daemon-reload
sudo systemctl enable devskyy
sudo systemctl start devskyy
sudo systemctl status devskyy
```

### Method 3: Cloud Platforms

#### AWS Elastic Beanstalk

```bash
# Install EB CLI
pip install awsebcli

# Initialize
eb init -p python-3.11 devskyy-platform

# Create environment
eb create devskyy-prod

# Deploy
eb deploy
```

#### Google Cloud Run

```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT-ID/devskyy

# Deploy
gcloud run deploy devskyy \
  --image gcr.io/PROJECT-ID/devskyy \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### Heroku

```bash
# Login
heroku login

# Create app
heroku create devskyy-platform

# Add MongoDB
heroku addons:create mongolab:sandbox

# Deploy
git push heroku main
```

### Method 4: Traditional Server

#### 1. Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python
sudo apt install python3.11 python3.11-venv python3-pip -y

# Install MongoDB
wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt update
sudo apt install mongodb-org -y
sudo systemctl start mongod
sudo systemctl enable mongod
```

#### 2. Setup Application

```bash
# Create directory
sudo mkdir -p /opt/devskyy
sudo chown $USER:$USER /opt/devskyy

# Clone repository
cd /opt/devskyy
git clone https://github.com/SkyyRoseLLC/DevSkyy.git .

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Edit with your settings
```

#### 3. Setup Nginx

```bash
# Install Nginx
sudo apt install nginx -y

# Create configuration
sudo nano /etc/nginx/sites-available/devskyy
```

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /opt/devskyy/frontend/dist;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/devskyy /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 4. Setup SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo systemctl enable certbot.timer
```

## Post-Deployment

### 1. Verify Deployment

```bash
# Check health
curl https://yourdomain.com/health

# Check API docs
curl https://yourdomain.com/docs

# Test authentication
curl -X POST https://yourdomain.com/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'
```

### 2. Run Safety Check

```bash
# Skipped: production_safety_check.py not included in this repository.
# Perform manual verification using the health and docs endpoints above.
```

### 3. Setup Monitoring

```bash
# Create monitoring user
python3 scripts/create_monitoring_user.py

# Setup health checks (every 5 minutes)
*/5 * * * * curl -f https://yourdomain.com/health || echo "Health check failed"
```

### 4. Configure Backups

```bash
# MongoDB backup script
cat > /opt/devskyy/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
mongodump --uri="$MONGODB_URI" --out="/backups/mongodb_$DATE"
find /backups -type d -mtime +7 -exec rm -rf {} +
EOF

chmod +x /opt/devskyy/backup.sh

# Add to crontab (daily at 2 AM)
0 2 * * * /opt/devskyy/backup.sh
```

## Monitoring

### Application Logs

```bash
# View logs (systemd)
sudo journalctl -u devskyy -f

# View logs (Docker)
docker-compose logs -f

# Application log file
tail -f /opt/devskyy/logs/app.log
```

### Performance Monitoring

```bash
# CPU and Memory
htop

# Disk usage
df -h

# MongoDB stats
mongo --eval "db.stats()"

# API response times
curl -w "@curl-format.txt" -o /dev/null -s https://yourdomain.com/api/v1/agents
```

### Setup Monitoring Tools

- **Prometheus**: Metrics collection
- **Grafana**: Visualization
- **Sentry**: Error tracking
- **UptimeRobot**: Uptime monitoring

## Troubleshooting

### Application Won't Start

```bash
# Check logs
sudo journalctl -u devskyy -n 50

# Verify Python dependencies
source venv/bin/activate
pip check

# Test import
python3 -c "from main import app"
```

### Database Connection Issues

```bash
# Test MongoDB connection
mongosh "$MONGODB_URI"

# Check MongoDB status
sudo systemctl status mongod

# View MongoDB logs
sudo tail -f /var/log/mongodb/mongod.log
```

### High Memory Usage

```bash
# Check processes
ps aux | grep python

# Restart service
sudo systemctl restart devskyy

# Scale workers (reduce in .env)
WORKERS=2  # Instead of 4
```

### SSL Certificate Issues

```bash
# Renew certificate
sudo certbot renew

# Check certificate
sudo certbot certificates

# Test renewal
sudo certbot renew --dry-run
```

## Scaling

### Horizontal Scaling

```bash
# Deploy multiple instances
docker-compose scale api=3

# Load balancer (Nginx)
upstream devskyy_backend {
    server 10.0.0.1:8000;
    server 10.0.0.2:8000;
    server 10.0.0.3:8000;
}
```

### Vertical Scaling

- Increase server resources (CPU/RAM)
- Optimize MongoDB indexes
- Enable Redis caching
- Use CDN for static assets

## Security Checklist

- [ ] Environment variables set correctly
- [ ] Secret keys are strong and unique
- [ ] SSL/TLS enabled
- [ ] Firewall configured
- [ ] MongoDB authentication enabled
- [ ] Rate limiting configured
- [ ] CORS properly configured
- [ ] Security headers enabled
- [ ] Regular backups configured
- [ ] Monitoring and alerts set up

## Maintenance

### Regular Updates

```bash
# Update code
cd /opt/devskyy
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Restart service
sudo systemctl restart devskyy
```

### Database Maintenance

```bash
# Compact database
mongo devskyy --eval "db.runCommand({compact: 'collection_name'})"

# Rebuild indexes
mongo devskyy --eval "db.products.reIndex()"
```

## Support

For deployment assistance:
- Email: support@skyyrose.com
- Documentation: https://github.com/SkyyRoseLLC/DevSkyy/tree/main/docs
- Issues: https://github.com/SkyyRoseLLC/DevSkyy/issues