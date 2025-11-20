# Tier 1 SDK Setup Status

**Date:** 2025-11-20
**Status:** 5 of 6 SDKs Installed Successfully

---

## ✅ Successfully Installed (5/6)

### 1. Stripe (11.1.1) ✅
**Purpose:** Payment processing and subscriptions
**Status:** Installed and ready
**Documentation:** https://stripe.com/docs/api

**Quick Test:**
```python
import stripe
import os

stripe.api_key = os.getenv("STRIPE_API_KEY")
print("✅ Stripe SDK ready")
```

**Environment Variables Needed:**
```bash
# Add to .env
STRIPE_API_KEY=sk_test_your_key_here  # Test mode
# STRIPE_API_KEY=sk_live_your_key_here  # Production
```

**Get API Key:**
1. Go to: https://dashboard.stripe.com/apikeys
2. Copy "Secret key" (starts with `sk_test_` or `sk_live_`)
3. Add to `.env` file

---

### 2. LiteLLM (1.52.16) ✅
**Purpose:** Multi-LLM routing with automatic fallbacks
**Status:** Installed and ready
**Documentation:** https://docs.litellm.ai/

**Quick Test:**
```python
from litellm import completion

response = completion(
    model="claude-3-sonnet-20240229",
    messages=[{"role": "user", "content": "Hello!"}],
    fallbacks=["gpt-4", "gpt-3.5-turbo"]
)
print(response.choices[0].message.content)
```

**Features:**
- Single interface for 100+ LLMs
- Automatic fallback (Claude → GPT-4 → GPT-3.5)
- Cost optimization (route to cheapest model)
- Load balancing

**Environment Variables:**
```bash
# Already configured in .env
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-key-here
```

---

### 3. PyGithub (2.5.0) ✅
**Purpose:** GitHub API automation
**Status:** Installed and ready
**Documentation:** https://pygithub.readthedocs.io/

**Quick Test:**
```python
from github import Github
import os

g = Github(os.getenv("GITHUB_TOKEN"))
repo = g.get_repo("The-Skyy-Rose-Collection-LLC/DevSkyy")
print(f"✅ GitHub API: {repo.name}")
```

**Environment Variables Needed:**
```bash
# Add to .env
GITHUB_TOKEN=ghp_your_token_here
```

**Get Token:**
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo`, `workflow`, `admin:org`
4. Copy token and add to `.env`

---

### 4. PostHog (3.8.4) ✅
**Purpose:** Product analytics and feature flags
**Status:** Installed and ready
**Documentation:** https://posthog.com/docs

**Quick Test:**
```python
from posthog import Posthog
import os

posthog = Posthog(
    project_api_key=os.getenv("POSTHOG_API_KEY"),
    host='https://app.posthog.com'
)

posthog.capture(
    distinct_id='user_123',
    event='test_event',
    properties={'environment': 'development'}
)
print("✅ PostHog event sent")
```

**Environment Variables Needed:**
```bash
# Add to .env
POSTHOG_API_KEY=phc_your_api_key_here
```

**Get API Key:**
1. Go to: https://app.posthog.com/
2. Sign up (free tier: 1M events/month)
3. Go to Project Settings → API Keys
4. Copy "Project API Key"
5. Add to `.env`

---

### 5. Pinecone (5.0.1) ✅
**Purpose:** Production-grade vector database
**Status:** Installed and configured
**Documentation:** See `PINECONE_SETUP.md`

**Quick Test:**
```python
from pinecone import Pinecone
import os

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
print(f"✅ Pinecone connected: {len(pc.list_indexes().names())} indexes")
```

**Environment Variables:**
```bash
# Already configured in .env
PINECONE_API_KEY=pcsk_***  # ✅ Configured
PINECONE_ENVIRONMENT=gcp-starter
PINECONE_INDEX_NAME=devskyy
```

---

## ⚠️ Installation Issues (1/6)

### 6. SendGrid (6.11.0) ❌
**Purpose:** Email delivery service
**Status:** Installation failed (dependency issue)
**Issue:** `starkbank-ecdsa` dependency has build errors with Python 3.11+

**Error:**
```
AttributeError: install_layout. Did you mean: 'install_platlib'?
ERROR: Failed building wheel for starkbank-ecdsa
```

**Root Cause:**
- SendGrid depends on `starkbank-ecdsa`
- `starkbank-ecdsa` uses old `setup.py` incompatible with Python 3.11+
- This is a known issue: https://github.com/sendgrid/sendgrid-python/issues/1035

### Alternative Solutions

#### Option 1: Use SMTP Directly (Recommended)

SendGrid provides SMTP relay - use Python's built-in SMTP library:

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def send_email_via_sendgrid_smtp(to: str, subject: str, html_body: str):
    """Send email using SendGrid SMTP relay."""
    sender = os.getenv("SENDGRID_FROM_EMAIL", "noreply@your-domain.com")
    api_key = os.getenv("SENDGRID_API_KEY")

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to

    html_part = MIMEText(html_body, 'html')
    msg.attach(html_part)

    # SendGrid SMTP server
    with smtplib.SMTP('smtp.sendgrid.net', 587) as server:
        server.starttls()
        server.login('apikey', api_key)  # Username is literally "apikey"
        server.send_message(msg)

    print(f"✅ Email sent to {to}")

# Usage
send_email_via_sendgrid_smtp(
    to="user@example.com",
    subject="Welcome to DevSkyy",
    html_body="<h1>Welcome!</h1><p>Get started with DevSkyy.</p>"
)
```

**Environment Variables:**
```bash
# Add to .env
SENDGRID_API_KEY=SG.your_api_key_here
SENDGRID_FROM_EMAIL=noreply@your-domain.com
```

**Get API Key:**
1. Go to: https://app.sendgrid.com/settings/api_keys
2. Create API Key with "Mail Send" permission
3. Add to `.env`

#### Option 2: Use requests Library

SendGrid has a REST API - use `httpx` (already installed):

```python
import httpx
import os

async def send_email_via_sendgrid_api(to: str, subject: str, html_body: str):
    """Send email using SendGrid REST API."""
    api_key = os.getenv("SENDGRID_API_KEY")
    sender = os.getenv("SENDGRID_FROM_EMAIL", "noreply@your-domain.com")

    url = "https://api.sendgrid.com/v3/mail/send"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    data = {
        "personalizations": [{
            "to": [{"email": to}],
            "subject": subject
        }],
        "from": {"email": sender},
        "content": [{
            "type": "text/html",
            "value": html_body
        }]
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=data, headers=headers)
        response.raise_for_status()

    print(f"✅ Email sent to {to}")

# Usage
import asyncio

asyncio.run(send_email_via_sendgrid_api(
    to="user@example.com",
    subject="Welcome to DevSkyy",
    html_body="<h1>Welcome!</h1>"
))
```

#### Option 3: Alternative Email SDKs

**Mailgun:**
```bash
pip install mailgun~=0.1.1
```

**Resend (Modern, Simple):**
```bash
pip install resend~=2.5.0
```

**AWS SES (via boto3):**
```bash
# Already installed: boto3~=1.36.7
import boto3

ses = boto3.client('ses', region_name='us-east-1')
ses.send_email(
    Source='noreply@your-domain.com',
    Destination={'ToAddresses': ['user@example.com']},
    Message={
        'Subject': {'Data': 'Subject'},
        'Body': {'Html': {'Data': '<h1>Body</h1>'}}
    }
)
```

### Recommendation

**For DevSkyy:** Use **SendGrid SMTP** (Option 1)

Advantages:
- No additional dependencies needed
- Uses Python's built-in `smtplib`
- Same SendGrid infrastructure
- Same reliability and deliverability
- Same free tier (100 emails/day)

---

## Summary

| SDK | Status | Version | Alternative |
|-----|--------|---------|-------------|
| **Stripe** | ✅ Installed | 11.1.1 | - |
| **SendGrid** | ❌ Failed | - | Use SMTP |
| **LiteLLM** | ✅ Installed | 1.52.16 | - |
| **PyGithub** | ✅ Installed | 2.5.0 | - |
| **PostHog** | ✅ Installed | 3.8.4 | - |
| **Pinecone** | ✅ Installed | 5.0.1 | - |

**Overall:** 5/6 successfully installed (83%)
**Impact:** Minimal - SendGrid functionality available via SMTP

---

## Next Steps

### 1. Configure Environment Variables

Add to `.env` file:

```bash
# Stripe
STRIPE_API_KEY=sk_test_your_key_here

# SendGrid (SMTP)
SENDGRID_API_KEY=SG.your_api_key_here
SENDGRID_FROM_EMAIL=noreply@your-domain.com

# GitHub
GITHUB_TOKEN=ghp_your_token_here

# PostHog
POSTHOG_API_KEY=phc_your_api_key_here

# Pinecone (already configured)
# PINECONE_API_KEY=pcsk_*** ✅
```

### 2. Create Email Helper Module

Create `core/email_service.py`:

```python
"""Email service using SendGrid SMTP."""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from typing import Optional

class EmailService:
    """SendGrid email service using SMTP."""

    def __init__(self):
        self.api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("SENDGRID_FROM_EMAIL", "noreply@devskyy.com")

        if not self.api_key:
            raise ValueError("SENDGRID_API_KEY not configured")

    def send_email(
        self,
        to: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> bool:
        """
        Send email via SendGrid SMTP.

        Args:
            to: Recipient email
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text version (optional)

        Returns:
            bool: True if sent successfully
        """
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to

            if text_body:
                msg.attach(MIMEText(text_body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))

            with smtplib.SMTP('smtp.sendgrid.net', 587) as server:
                server.starttls()
                server.login('apikey', self.api_key)
                server.send_message(msg)

            return True

        except Exception as e:
            print(f"❌ Email send failed: {e}")
            return False

# Usage example
email_service = EmailService()
email_service.send_email(
    to="user@example.com",
    subject="Welcome to DevSkyy",
    html_body="<h1>Welcome!</h1>"
)
```

### 3. Test SDKs

Run test scripts to verify all SDKs work:

```bash
# Test Stripe
python -c "import stripe; print('✅ Stripe OK')"

# Test LiteLLM
python -c "import litellm; print('✅ LiteLLM OK')"

# Test PyGithub
python -c "from github import Github; print('✅ PyGithub OK')"

# Test PostHog
python -c "from posthog import Posthog; print('✅ PostHog OK')"

# Test Pinecone
python scripts/pinecone_setup.py verify
```

### 4. Update SDK Recommendations

Document SendGrid alternative in `SDK_RECOMMENDATIONS.md`.

---

## Cost Summary (Free Tiers)

| Service | Free Tier | Monthly Value |
|---------|-----------|---------------|
| **Stripe** | Transaction fees only | $0 + 2.9% |
| **SendGrid** | 100 emails/day | $0 (worth ~$15) |
| **LiteLLM** | Pay per use | Pay as you go |
| **PostHog** | 1M events/month | $0 (worth ~$50) |
| **Pinecone** | 100K vectors | $0 (worth ~$70) |

**Total Monthly Savings:** ~$135 on free tiers

---

## Resources

- **Stripe Docs:** https://stripe.com/docs/api
- **SendGrid SMTP:** https://docs.sendgrid.com/for-developers/sending-email/smtp-api-reference
- **LiteLLM Docs:** https://docs.litellm.ai/
- **PyGithub Docs:** https://pygithub.readthedocs.io/
- **PostHog Docs:** https://posthog.com/docs
- **Pinecone Docs:** See `PINECONE_SETUP.md`

---

**Status:** 5/6 Tier 1 SDKs Ready ✅
**Workaround:** SendGrid via SMTP (no SDK needed)
**Next:** Configure environment variables and test

