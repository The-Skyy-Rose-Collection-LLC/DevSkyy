# XSS (Cross-Site Scripting) Attack Response

**Severity Level**: HIGH
**Last Updated**: 2025-12-19
**Owner**: Security Operations Team
**Related**: [Security Incident Response Master Procedure](/Users/coreyfoster/DevSkyy/docs/runbooks/security-incident-response.md)

## Overview

Cross-Site Scripting (XSS) attacks inject malicious scripts into web pages viewed by other users, potentially leading to session hijacking, credential theft, or malware distribution. This runbook covers detection, containment, and remediation of XSS vulnerabilities.

## Detection

### Alert Triggers

**Automated Alerts:**

- WAF detecting XSS patterns (<script>, onerror=, javascript:)
- Content Security Policy (CSP) violations
- Unusual JavaScript execution patterns
- User reports of unexpected popups or behavior
- Session hijacking attempts
- Anomalous POST requests with HTML/JS payloads

**XSS Pattern Detection:**

```regex
# Common XSS patterns
<script[^>]*>.*?</script>
javascript:
onerror\s*=
onload\s*=
<iframe[^>]*src=
eval\(
document\.cookie
window\.location
<img[^>]*onerror=
```

### How to Identify

1. **Check WAF Logs**

   ```bash
   # Cloudflare WAF XSS blocks
   curl "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/firewall/events" \
     -H "X-Auth-Email: $CF_EMAIL" \
     -H "X-Auth-Key: $CF_API_KEY" | \
     jq '.result[] | select(.ruleId | contains("xss"))'

   # ModSecurity logs
   grep -i "cross-site scripting\|XSS" /var/log/modsec_audit.log | tail -50
   ```

2. **Check CSP Violation Reports**

   ```bash
   # Review CSP violation reports
   psql $DATABASE_URL -c "
   SELECT
     created_at,
     document_uri,
     blocked_uri,
     violated_directive,
     source_file,
     line_number
   FROM csp_violations
   WHERE created_at > NOW() - INTERVAL '24 hours'
   ORDER BY created_at DESC;
   "
   ```

3. **Analyze User Input Storage**

   ```bash
   # Check for suspicious content in user-generated fields
   psql $DATABASE_URL -c "
   SELECT
     id,
     username,
     bio,
     created_at
   FROM users
   WHERE bio ILIKE '%<script%'
      OR bio ILIKE '%javascript:%'
      OR bio ILIKE '%onerror=%'
      OR bio ILIKE '%onload=%'
   ORDER BY created_at DESC;
   "

   # Check comments/reviews for XSS
   psql $DATABASE_URL -c "
   SELECT
     id,
     user_id,
     content,
     created_at
   FROM product_reviews
   WHERE content ILIKE '%<script%'
      OR content ILIKE '%<iframe%'
   ORDER BY created_at DESC;
   "
   ```

4. **Check Application Logs**

   ```bash
   # Search for XSS attempts in request logs
   grep -E "(<script|javascript:|onerror=|onload=)" /var/log/nginx/access.log | tail -100

   # Check for encoded XSS attempts
   grep -E "(%3Cscript|%3C%2Fscript|&#x3C;script)" /var/log/nginx/access.log
   ```

5. **Session Hijacking Detection**

   ```bash
   # Check for unusual session activity
   psql $DATABASE_URL -c "
   SELECT
     user_id,
     session_id,
     ip_address,
     user_agent,
     created_at,
     last_activity
   FROM sessions
   WHERE last_activity > NOW() - INTERVAL '1 hour'
   GROUP BY user_id
   HAVING COUNT(DISTINCT ip_address) > 2;
   "
   ```

## Triage

### Severity Assessment

**CRITICAL - Immediate Response:**

- Stored XSS in production affecting multiple users
- Session hijacking attacks in progress
- XSS stealing authentication tokens
- Admin panel affected by XSS
- Payment forms affected
- Sensitive data exfiltration

**HIGH - Urgent Response (< 1 hour):**

- Reflected XSS in commonly used endpoints
- DOM-based XSS in main application
- XSS in user-generated content
- Multiple XSS vectors identified

**MEDIUM - Response within 4 hours:**

- Reflected XSS in rarely used endpoint
- XSS blocked by WAF but code not fixed
- Self-XSS (requires user interaction)
- XSS in deprecated features

### Initial Containment Steps

**IMMEDIATE ACTIONS (within 15 minutes):**

1. **Deploy Strict CSP**

   ```nginx
   # Add to nginx config
   add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'nonce-RANDOM'; object-src 'none'; base-uri 'self';" always;
   add_header X-Content-Type-Options "nosniff" always;
   add_header X-Frame-Options "DENY" always;
   add_header X-XSS-Protection "1; mode=block" always;

   nginx -s reload
   ```

2. **Sanitize Stored XSS**

   ```bash
   # Identify and clean malicious content
   psql $DATABASE_URL -c "
   UPDATE users
   SET bio = regexp_replace(bio, '<script[^>]*>.*?</script>', '', 'gi')
   WHERE bio ILIKE '%<script%';

   UPDATE product_reviews
   SET content = regexp_replace(content, '<.*?>', '', 'g')
   WHERE content ~ '<.*?>';
   "
   ```

3. **Revoke Compromised Sessions**

   ```bash
   # If session hijacking detected, invalidate all sessions
   redis-cli FLUSHDB

   # Force re-authentication
   psql $DATABASE_URL -c "UPDATE sessions SET invalidated = true;"
   ```

4. **Enable WAF XSS Protection**

   ```bash
   # Enable Cloudflare XSS protection
   curl -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/settings/security_level" \
     -H "X-Auth-Email: $CF_EMAIL" \
     -H "X-Auth-Key: $CF_API_KEY" \
     --data '{"value":"high"}'
   ```

### Escalation Procedures

**CRITICAL XSS:**

1. Alert Security Lead: [PHONE]
2. Alert Frontend/Backend leads
3. Create war room: `#incident-xss-YYYYMMDD`
4. Notify affected users if session hijacking occurred

## Investigation

### Vulnerability Analysis

1. **Identify XSS Type**

   ```bash
   # Reflected XSS - payload in URL/request immediately reflected
   curl "https://api.skyyrose.com/search?q=<script>alert('XSS')</script>"

   # Stored XSS - payload stored in database
   psql $DATABASE_URL -c "SELECT content FROM reviews WHERE content ILIKE '%<script%';"

   # DOM-based XSS - payload executed via DOM manipulation
   # Check JavaScript files for unsafe DOM operations
   grep -rn "innerHTML\|outerHTML\|document.write" frontend/src/
   ```

2. **Check Input Validation**

   ```bash
   # Review validation code
   grep -rn "sanitize\|escape\|clean" apps/ --include="*.py"

   # Check for missing validation
   grep -rn "request.args\|request.form\|request.json" apps/ --include="*.py" | \
   grep -v "sanitize\|escape"
   ```

3. **Review Output Encoding**

   ```bash
   # Check template files for unescaped output
   grep -rn "{{ .*|safe }}\|{% autoescape off %}" templates/

   # React components with dangerouslySetInnerHTML
   grep -rn "dangerouslySetInnerHTML" frontend/src/
   ```

### Data Collection Checklist

- [ ] XSS type (stored, reflected, DOM-based)
- [ ] Vulnerable endpoint(s)
- [ ] Vulnerable code location
- [ ] Attack payloads used
- [ ] Number of affected users
- [ ] Session hijacking attempts
- [ ] Data exfiltration attempts
- [ ] CSP violations logged
- [ ] WAF block/allow decisions

### Root Cause Analysis

**Common Causes:**

1. **Missing Output Encoding**

   ```javascript
   // VULNERABLE
   element.innerHTML = userInput;

   // SECURE
   element.textContent = userInput;
   ```

2. **Unsafe Template Rendering**

   ```python
   # VULNERABLE
   return render_template('page.html', content=user_input|safe)

   # SECURE
   return render_template('page.html', content=escape(user_input))
   ```

3. **DOM Manipulation**

   ```javascript
   // VULNERABLE
   document.write(location.hash);

   // SECURE
   const div = document.createElement('div');
   div.textContent = location.hash;
   ```

## Remediation

### Step-by-Step Fix Procedures

**1. Implement Output Encoding**

```python
from markupsafe import escape
from bleach import clean

# HTML output encoding
@app.route('/profile/<user_id>')
def profile(user_id):
    user = get_user(user_id)
    # Jinja2 auto-escapes by default (don't use |safe)
    return render_template('profile.html', user=user)

# For user-generated HTML (rich text), use sanitizer
allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'a']
allowed_attrs = {'a': ['href', 'title']}

def sanitize_html(content):
    return clean(
        content,
        tags=allowed_tags,
        attributes=allowed_attrs,
        strip=True
    )

@app.route('/api/reviews', methods=['POST'])
def create_review():
    content = request.json.get('content')
    sanitized = sanitize_html(content)
    Review.create(content=sanitized)
```

**2. Implement CSP**

```nginx
# /etc/nginx/conf.d/security-headers.conf
map $sent_http_content_type $csp_header {
    default "default-src 'self'; script-src 'self' 'nonce-${request_id}'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self';";
}

add_header Content-Security-Policy $csp_header always;
add_header Content-Security-Policy-Report-Only "default-src 'self'; report-uri /api/csp-violations;" always;
```

```python
# CSP violation reporting endpoint
@app.post('/api/csp-violations')
async def csp_violation_report(request: Request):
    body = await request.json()
    await db.execute(
        "INSERT INTO csp_violations (document_uri, blocked_uri, violated_directive, source_file) VALUES ($1, $2, $3, $4)",
        body.get('document-uri'),
        body.get('blocked-uri'),
        body.get('violated-directive'),
        body.get('source-file')
    )
    return {"status": "received"}
```

**3. Sanitize Frontend**

```typescript
// frontend/src/utils/sanitize.ts
import DOMPurify from 'dompurify';

export function sanitizeHtml(dirty: string): string {
  return DOMPurify.sanitize(dirty, {
    ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'u', 'a'],
    ALLOWED_ATTR: ['href', 'title'],
  });
}

// Usage in React component
import { sanitizeHtml } from '@/utils/sanitize';

function UserBio({ bio }: { bio: string }) {
  return (
    <div
      dangerouslySetInnerHTML={{ __html: sanitizeHtml(bio) }}
    />
  );
}

// Better: avoid dangerouslySetInnerHTML entirely
function UserBio({ bio }: { bio: string }) {
  return <div>{bio}</div>; // React auto-escapes
}
```

**4. Implement Input Validation**

```python
from pydantic import BaseModel, validator, Field
import re

class ReviewInput(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)

    @validator('content')
    def validate_content(cls, v):
        # Block obvious XSS attempts
        dangerous_patterns = [
            r'<script[^>]*>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe',
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError('Invalid content detected')

        return v
```

**5. Deploy WAF Rules**

```bash
# Cloudflare WAF rule for XSS
curl -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/firewall/rules" \
  -H "X-Auth-Email: $CF_EMAIL" \
  -H "X-Auth-Key: $CF_API_KEY" \
  --data '{
    "filter": {
      "expression": "(http.request.uri.query contains \"<script\") or (http.request.uri.query contains \"javascript:\") or (http.request.body contains \"<script\")"
    },
    "action": "block",
    "description": "Block XSS Attempts"
  }'
```

### Verification Steps

```bash
# 1. Test XSS is blocked
curl -X GET "https://api.skyyrose.com/search?q=<script>alert('XSS')</script>"
# Should return 403 or sanitized output

# 2. Test CSP is active
curl -I https://api.skyyrose.com/ | grep -i "content-security-policy"
# Should show CSP header

# 3. Test output encoding
curl https://api.skyyrose.com/api/reviews/1 | grep "<script"
# Should find no script tags

# 4. Run automated XSS scanner
python scripts/xss_scanner.py --target https://api.skyyrose.com

# 5. Manual testing with XSS payloads
# Test common vectors are sanitized
```

## Recovery

### Service Restoration Process

**Phase 1: Immediate Cleanup (0-2 hours)**

1. Deploy output encoding fixes
2. Sanitize stored malicious content
3. Enable CSP
4. Revoke compromised sessions
5. Monitor for continued attacks

**Phase 2: Comprehensive Fix (2-24 hours)**

1. Audit all user input fields
2. Implement validation everywhere
3. Deploy WAF rules
4. Update frontend sanitization
5. Security testing

**Phase 3: Monitoring (24-72 hours)**

1. Monitor CSP violations
2. Track WAF blocks
3. User behavior analysis
4. Complete security audit

### Communication Plan

**Internal:**

```
#security-alerts

:shield: **XSS Vulnerability Patched**

**Status**: RESOLVED
**Severity**: HIGH

**Vulnerability**: Stored XSS in product review system
**Impact**: ~500 reviews contained malicious scripts

**Actions Taken**:
- Sanitized all existing content
- Deployed output encoding
- Enabled strict CSP
- Revoked potentially compromised sessions
- Deployed WAF rules

**User Impact**: None detected
**Follow-up**: Security training scheduled for [DATE]
```

## Post-Mortem

### Preventive Measures

- [ ] Implement automatic output encoding in all templates
- [ ] Deploy strict CSP on all pages
- [ ] Enable XSS protection headers
- [ ] Implement input validation framework
- [ ] Deploy automated XSS scanning in CI/CD
- [ ] Conduct security code review
- [ ] Security training for developers
- [ ] Regular penetration testing

## Contact Information

| Role | Contact | Email |
|------|---------|-------|
| Security Lead | @security-lead | <security-lead@skyyrose.com> |
| Frontend Lead | @frontend-lead | <frontend@skyyrose.com> |

## Slack Notification Template

```
:warning: **XSS VULNERABILITY DETECTED** :warning:

**Incident ID**: INC-XSS-YYYYMMDD-HHmm
**Severity**: HIGH
**Status**: MITIGATING

**Vulnerability Details**:
- Type: [Stored / Reflected / DOM-based]
- Location: [Endpoint/Component]
- Impact: [Users affected]

**IMMEDIATE ACTIONS**:
- Deployed output encoding
- Enabled strict CSP
- Sanitized stored content
- WAF rules activated

**Incident Commander**: @security-lead
**War Room**: #incident-xss-YYYYMMDD
```

## Related Runbooks

- [Security Incident Response Master Procedure](/Users/coreyfoster/DevSkyy/docs/runbooks/security-incident-response.md)
- [Data Breach](/Users/coreyfoster/DevSkyy/docs/runbooks/data-breach.md)
