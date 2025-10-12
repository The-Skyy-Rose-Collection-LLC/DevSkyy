# Environment Setup Guide - DevSkyy

## Quick Setup (3 Steps)

### Step 1: Copy the Template

```bash
cd /Users/coreyfoster/DevSkyy
cp .env.template .env
```

### Step 2: Generate SECRET_KEY

Run this command and copy the output:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

You'll get something like: `xK8_vQm9-NpL2RtY5sW7dF3gH6jK9mN0pQ4rT8uV1xY`

Open `.env` and replace:
```bash
SECRET_KEY=REPLACE_WITH_SECURE_RANDOM_32_CHAR_STRING
```

With:
```bash
SECRET_KEY=xK8_vQm9-NpL2RtY5sW7dF3gH6jK9mN0pQ4rT8uV1xY
```

### Step 3: Add Your Anthropic API Key

**Get your key:**
1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Create an API key
4. Copy the key (starts with `sk-ant-`)

**Add to .env:**

Open `/Users/coreyfoster/DevSkyy/.env` and replace:
```bash
ANTHROPIC_API_KEY=sk-ant-REPLACE_WITH_YOUR_ANTHROPIC_KEY
```

With your actual key:
```bash
ANTHROPIC_API_KEY=sk-ant-api03-YOUR_ACTUAL_KEY_HERE
```

---

## Your .env File Location

**File Path:** `/Users/coreyfoster/DevSkyy/.env`

**Edit with:**
```bash
# Using nano (simple)
nano /Users/coreyfoster/DevSkyy/.env

# Using VS Code
code /Users/coreyfoster/DevSkyy/.env

# Using vim
vim /Users/coreyfoster/DevSkyy/.env
```

---

## Minimum Required Configuration

For basic deployment, you only need these 3 variables:

```bash
SECRET_KEY=your_generated_secret_key_here
ANTHROPIC_API_KEY=sk-ant-your_anthropic_key_here
MONGODB_URI=mongodb://localhost:27017/devSkyy
```

Everything else is optional!

---

## MongoDB Setup Options

### Option 1: Local MongoDB (Easiest for Development)

**Install:**
```bash
# macOS
brew install mongodb-community

# Ubuntu/Linux
sudo apt-get install mongodb
```

**Start:**
```bash
# macOS
brew services start mongodb-community

# Ubuntu/Linux
sudo systemctl start mongodb
```

**Your .env setting:**
```bash
MONGODB_URI=mongodb://localhost:27017/devSkyy
```

### Option 2: MongoDB Atlas (Best for Production)

**Setup:**
1. Go to https://www.mongodb.com/cloud/atlas
2. Create free account
3. Create a free cluster (512MB)
4. Click "Connect" → "Connect your application"
5. Copy the connection string

**Your .env setting:**
```bash
MONGODB_URI=mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/devSkyy
```

Replace `username`, `password`, and cluster URL with your actual values.

### Option 3: Docker MongoDB

**Start:**
```bash
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

**Your .env setting:**
```bash
MONGODB_URI=mongodb://localhost:27017/devSkyy
```

---

## Optional Features

### Add OpenAI (For GPT-4 Features)

**Get key:** https://platform.openai.com/api-keys

**Add to .env:**
```bash
OPENAI_API_KEY=sk-your_openai_key_here
```

### Add Meta/Facebook (For Social Media Automation)

**Get token:** https://developers.facebook.com/

**Add to .env:**
```bash
META_ACCESS_TOKEN=your_meta_token_here
```

### Add ElevenLabs (For Voice Features)

**Get key:** https://elevenlabs.io/

**Add to .env:**
```bash
ELEVENLABS_API_KEY=your_elevenlabs_key_here
```

---

## Complete Example .env File

Here's what your final `.env` file should look like:

```bash
# ==============================================================================
# CRITICAL - REQUIRED
# ==============================================================================

SECRET_KEY=xK8_vQm9-NpL2RtY5sW7dF3gH6jK9mN0pQ4rT8uV1xY
ANTHROPIC_API_KEY=sk-ant-api03-abc123xyz789youractualkey
MONGODB_URI=mongodb://localhost:27017/devSkyy

# ==============================================================================
# APPLICATION SETTINGS
# ==============================================================================

APP_NAME=DevSkyy Enhanced Platform
APP_VERSION=2.0.0
ENVIRONMENT=development
DEBUG=True

HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# ==============================================================================
# RECOMMENDED (Optional but useful)
# ==============================================================================

OPENAI_API_KEY=sk-your_openai_key_here
META_ACCESS_TOKEN=
ELEVENLABS_API_KEY=
REDIS_URL=redis://localhost:6379

# ==============================================================================
# Everything else is optional
# ==============================================================================
```

---

## Verify Setup

After creating your `.env` file, verify it works:

```bash
cd /Users/coreyfoster/DevSkyy

# Check if environment loads
python3 -c "from dotenv import load_dotenv; load_dotenv(); import os; print('✅ ANTHROPIC_API_KEY:', 'SET' if os.getenv('ANTHROPIC_API_KEY') else 'MISSING'); print('✅ MONGODB_URI:', 'SET' if os.getenv('MONGODB_URI') else 'MISSING'); print('✅ SECRET_KEY:', 'SET' if os.getenv('SECRET_KEY') else 'MISSING')"
```

You should see:
```
✅ ANTHROPIC_API_KEY: SET
✅ MONGODB_URI: SET
✅ SECRET_KEY: SET
```

---

## Quick Commands Reference

```bash
# Navigate to project
cd /Users/coreyfoster/DevSkyy

# Copy template
cp .env.template .env

# Generate secret key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Edit .env
nano .env

# Verify setup
python3 -c "from dotenv import load_dotenv; load_dotenv(); import os; print('ANTHROPIC_API_KEY:', 'SET' if os.getenv('ANTHROPIC_API_KEY') else 'MISSING')"

# Start MongoDB (if local)
brew services start mongodb-community

# Start backend
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Start frontend (in new terminal)
cd frontend && npm run dev
```

---

## Troubleshooting

### "Cannot find .env file"
```bash
# Make sure you're in the right directory
cd /Users/coreyfoster/DevSkyy
pwd  # Should show: /Users/coreyfoster/DevSkyy

# Check if .env exists
ls -la .env
```

### "ANTHROPIC_API_KEY not set"
```bash
# Check if the variable is in the file
grep ANTHROPIC_API_KEY .env

# Make sure there's no space around the =
# WRONG: ANTHROPIC_API_KEY = sk-ant-key
# RIGHT: ANTHROPIC_API_KEY=sk-ant-key
```

### "MongoDB connection failed"
```bash
# Check if MongoDB is running
mongosh  # or: mongo

# If not installed, install it:
brew install mongodb-community

# Start it:
brew services start mongodb-community
```

---

## Next Steps

Once your `.env` is configured:

1. **Start the backend:**
   ```bash
   python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Start the frontend (new terminal):**
   ```bash
   cd frontend && npm run dev
   ```

3. **Access the application:**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

4. **For production deployment:**
   - See `DEPLOYMENT_CHECKLIST.md`
   - Run `bash run_enterprise.sh`

---

**Need Help?**
- Check `DEPLOYMENT_CHECKLIST.md` for deployment steps
- Review `CLAUDE.md` for architecture details
- Run `python production_safety_check.py` to verify setup
