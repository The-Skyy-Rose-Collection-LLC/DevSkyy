# DevSkyy Vercel Build Configuration Guide

## 🚀 **Vercel Build Settings Overview**

This document outlines the optimal Vercel build configuration for the DevSkyy Enterprise Fashion E-commerce Automation Platform.

---

## **📋 Framework Settings**

### **Framework Preset**
- **Selected**: `Other` (Custom Python FastAPI application)
- **Reason**: DevSkyy is a Python FastAPI application, not a traditional frontend framework

### **Build Command**
- **Command**: `pip install -r requirements.txt`
- **Override**: ✅ Enabled
- **Purpose**: Install Python dependencies for the FastAPI application

### **Output Directory**
- **Directory**: `.` (root directory)
- **Override**: ✅ Enabled
- **Purpose**: Serve the entire application from root since it's a serverless function

### **Install Command**
- **Command**: `pip install --upgrade pip && pip install -r requirements.txt`
- **Override**: ✅ Enabled
- **Purpose**: Ensure latest pip and install all dependencies

### **Development Command**
- **Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT --reload`
- **Override**: ✅ Enabled
- **Purpose**: Run FastAPI development server with hot reload

---

## **🔧 Advanced Configuration**

### **Runtime Settings**
```json
{
  "runtime": "python3.11",
  "maxLambdaSize": "50mb",
  "maxDuration": 30,
  "memory": 1024
}
```

### **Environment Variables**
```json
{
  "PYTHONPATH": ".",
  "ENVIRONMENT": "production",
  "LOG_LEVEL": "INFO",
  "PYTHONDONTWRITEBYTECODE": "1",
  "PYTHONUNBUFFERED": "1"
}
```

### **Routing Configuration**
```json
{
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "main.py"
    },
    {
      "src": "/(.*)",
      "dest": "main.py"
    }
  ]
}
```

---

## **📊 Build Optimization Features**

### **Shallow Clone Configuration**
- **Depth**: 10 commits (Vercel default)
- **Command**: `git clone --depth=10`
- **Benefit**: Faster builds with reduced repository size

### **Concurrent Builds**
- **Auto Deployment**: ✅ Enabled
- **Auto Job Cancelation**: ✅ Enabled
- **Priority**: Production builds prioritized

### **Regional Deployment**
- **Primary Region**: `iad1` (US East)
- **Benefit**: Optimized for North American users

---

## **🛠️ Required Vercel Project Settings**

### **1. Framework Settings**
Navigate to Project Settings → Build & Development Settings:

- **Framework Preset**: Other
- **Build Command**: `pip install -r requirements.txt` (Override: ON)
- **Output Directory**: `.` (Override: ON)
- **Install Command**: `pip install --upgrade pip && pip install -r requirements.txt` (Override: ON)
- **Development Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT --reload` (Override: ON)

### **2. Environment Variables**
Add these environment variables in Project Settings → Environment Variables:

```bash
PYTHONPATH=.
ENVIRONMENT=production
LOG_LEVEL=INFO
PYTHONDONTWRITEBYTECODE=1
PYTHONUNBUFFERED=1
```

### **3. Function Configuration**
- **Runtime**: Python 3.11
- **Memory**: 1024 MB
- **Max Duration**: 30 seconds
- **Max Lambda Size**: 50 MB

---

## **🔍 Build Process Flow**

### **1. Repository Clone**
```bash
git clone --depth=10 https://github.com/SkyyRoseLLC/DevSkyy.git
```

### **2. Dependency Installation**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### **3. Build Execution**
```bash
# Build command runs (pip install -r requirements.txt)
# Python dependencies installed
# FastAPI application prepared for serverless deployment
```

### **4. Function Deployment**
```bash
# main.py deployed as serverless function
# Routes configured for API endpoints
# Environment variables applied
```

---

## **⚡ Performance Optimizations**

### **Build Speed**
- **Shallow Clone**: 10 commit depth reduces clone time
- **Dependency Caching**: pip cache enabled for faster installs
- **Concurrent Builds**: Multiple builds can run simultaneously

### **Runtime Performance**
- **Memory**: 1024 MB for complex ML operations
- **Duration**: 30 seconds for comprehensive API responses
- **Region**: US East for optimal latency

### **Cost Optimization**
- **Auto Job Cancelation**: Prevents redundant builds
- **Production Priority**: Ensures critical deployments complete first

---

## **🚨 Troubleshooting Common Issues**

### **Build Failures**
1. **Dependency Issues**: Check requirements.txt for version conflicts
2. **Memory Limits**: Increase function memory if needed
3. **Timeout Issues**: Optimize code or increase maxDuration

### **Runtime Errors**
1. **Import Errors**: Verify PYTHONPATH is set correctly
2. **Environment Variables**: Ensure all required vars are configured
3. **Function Size**: Check if deployment exceeds 50MB limit

### **Performance Issues**
1. **Cold Starts**: Consider keeping functions warm
2. **Memory Usage**: Monitor and adjust memory allocation
3. **Response Times**: Optimize database queries and API calls

---

## **📈 Monitoring and Analytics**

### **Build Metrics**
- Build duration and success rate
- Dependency installation time
- Function deployment size

### **Runtime Metrics**
- Function execution time
- Memory usage patterns
- Error rates and types

### **Deployment Health**
- Uptime monitoring
- Response time tracking
- Error logging and alerting

---

## **🎯 Best Practices**

1. **Keep Dependencies Minimal**: Only include necessary packages
2. **Optimize Function Size**: Remove unused files and dependencies
3. **Use Environment Variables**: Keep sensitive data in environment variables
4. **Monitor Performance**: Regularly check build and runtime metrics
5. **Test Locally**: Use `vercel dev` for local development and testing

---

This configuration ensures optimal build performance, reliability, and cost-effectiveness for the DevSkyy Enterprise Platform on Vercel.
