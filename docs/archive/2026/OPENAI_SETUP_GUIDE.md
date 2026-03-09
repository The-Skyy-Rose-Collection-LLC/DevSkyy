# OpenAI API Key Setup Guide

Quick guide to set up your OpenAI API key for DevSkyy.

---

## 🚨 IMPORTANT: Security First

**Before proceeding, please ensure you've revoked the API key that was exposed earlier!**

1. Go to: <https://platform.openai.com/api-keys>
2. Find and revoke the old key (starts with `sk-proj-mxV316lWmUh5x6fW...`)
3. Generate a new key
4. Use the new key in the setup below

---

## 🚀 Quick Setup (Automated)

### Option 1: Interactive Setup Script (Recommended)

```bash
./setup_openai_key.sh
```

This script will:

- ✅ Prompt you for your API key (input is hidden)
- ✅ Add it to your shell config (~/.zshrc or ~/.bash_profile)
- ✅ Create a .env file
- ✅ Add .env to .gitignore
- ✅ Test the connection
- ✅ Set proper file permissions

### Option 2: Manual Setup

**Step 1: Add to shell config**

```bash
# For zsh (macOS default)
echo 'export OPENAI_API_KEY="your-new-key-here"' >> ~/.zshrc
source ~/.zshrc

# For bash
echo 'export OPENAI_API_KEY="your-new-key-here"' >> ~/.bash_profile
source ~/.bash_profile
```

**Step 2: Create .env file**

```bash
# Create .env file
cat > .env << 'EOF'
# DevSkyy Environment Variables
OPENAI_API_KEY=your-new-key-here
EOF

# Secure the file
chmod 600 .env

# Ensure it's in .gitignore
echo ".env" >> .gitignore
```

**Step 3: Test the connection**

```bash
python3 test_openai_connection.py
```

---

## ✅ Verification

After setup, verify everything is working:

```bash
# Test OpenAI connection
python3 test_openai_connection.py

# Verify all LLM clients
python3 scripts/verify_llm_clients.py
```

Expected output:

```
✓ API key found: sk-proj-mxV...I8A
🔄 Testing OpenAI API connection...
✅ SUCCESS! OpenAI API is working!
```

---

## 🔧 Troubleshooting

### "API key not found"

Make sure you've reloaded your shell:

```bash
source ~/.zshrc  # or ~/.bash_profile
```

Or start a new terminal session.

### "Invalid API key"

1. Check the key format (should start with `sk-` or `sk-proj-`)
2. Verify the key at: <https://platform.openai.com/api-keys>
3. Make sure you copied the entire key

### "Authentication failed"

The key may have been revoked. Generate a new one:

1. Go to: <https://platform.openai.com/api-keys>
2. Click "Create new secret key"
3. Copy the new key
4. Run `./setup_openai_key.sh` again

### "Insufficient quota"

Check your OpenAI account:

1. Go to: <https://platform.openai.com/usage>
2. Verify you have credits available
3. Add payment method if needed: <https://platform.openai.com/account/billing>

---

## 📊 Usage Monitoring

Monitor your API usage:

1. **Usage Dashboard:** <https://platform.openai.com/usage>
2. **Billing:** <https://platform.openai.com/account/billing>
3. **Set limits:** <https://platform.openai.com/account/billing/limits>

**Recommended:** Set up billing alerts to avoid unexpected charges.

---

## 🔐 Security Best Practices

### ✅ DO

- Store keys in environment variables
- Use .env files (with .gitignore)
- Rotate keys regularly (every 90 days)
- Set billing limits
- Monitor usage regularly
- Use separate keys for dev/prod

### ❌ DON'T

- Commit keys to git
- Share keys in messages/chat
- Include keys in code
- Post keys in screenshots
- Use the same key everywhere

---

## 🎯 Next Steps

After setting up your OpenAI key:

1. **Test the integration:**

   ```bash
   python3 test_openai_connection.py
   ```

2. **Verify all LLM clients:**

   ```bash
   python3 scripts/verify_llm_clients.py
   ```

3. **Try the orchestrator:**

   ```python
   import asyncio
   from orchestration import LLMOrchestrator, TaskType

   async def test():
       orchestrator = LLMOrchestrator()
       result = await orchestrator.complete(
           prompt="Say hello!",
           task_type=TaskType.CHAT
       )
       print(result.content)

   asyncio.run(test())
   ```

4. **Set up other providers (optional):**
   - Anthropic (Claude): <https://console.anthropic.com/>
   - Google (Gemini): <https://ai.google.dev/>
   - Mistral: <https://console.mistral.ai/>
   - Cohere: <https://dashboard.cohere.com/>
   - Groq: <https://console.groq.com/>

---

## 📚 Resources

- **OpenAI Documentation:** <https://platform.openai.com/docs>
- **API Keys Management:** <https://platform.openai.com/api-keys>
- **Usage Dashboard:** <https://platform.openai.com/usage>
- **DevSkyy LLM Guide:** [docs/LLM_CLIENTS_QUICK_START.md](docs/LLM_CLIENTS_QUICK_START.md)
- **Security Alert:** [SECURITY_ALERT_API_KEY_EXPOSED.md](SECURITY_ALERT_API_KEY_EXPOSED.md)

---

## 🆘 Need Help?

If you encounter issues:

1. Check the troubleshooting section above
2. Review the security alert document
3. Verify your OpenAI account status
4. Check the DevSkyy documentation

---

**Remember:** Always keep your API keys secure and never share them publicly!
