# Final Decision Required: WordPress.com CSP Limitation

**Date**: 2026-02-06
**Status**: ⛔ ALL THEME-LEVEL FIXES EXHAUSTED

---

## Situation

After systematic debugging and **4 failed fix attempts**, I've confirmed that WordPress.com's Business plan injects Content Security Policy headers at the **infrastructure level** (Nginx reverse proxy) which **cannot be modified** by:
- Theme code
- Plugins
- custom-redirects.php
- WordPress filters/hooks
- Any PHP code

This is an **architectural limitation**, not a bug.

---

## Impact

**Current State**:
- 109 console errors on every page
- 3D product viewer (Babylon.js) completely non-functional
- Elementor advanced features broken
- WordPress.com's own domains blocked (stats.wp.com, widgets.wp.com)
- Poor user experience for luxury fashion brand

**Business Impact**:
- Core brand feature (3D immersive viewer) unavailable
- Degraded shopping experience
- Potential revenue loss
- Brand reputation risk

---

## Failed Fix Attempts (Evidence of Due Diligence)

### Attempt 1: wpcom_csp_allowed_sources Filter
```php
add_filter('wpcom_csp_allowed_sources', [$this, 'add_domains'], 999);
```
**Result**: ❌ Filter doesn't exist
**Evidence**: No hook fired, domains not added to CSP

### Attempt 2: Theme header() Override
```php
header('Content-Security-Policy: ...');
```
**Result**: ❌ Overridden by platform
**Evidence**: `curl -sI` shows platform CSP, not theme CSP

### Attempt 3: Nonce Extraction
```php
$headers = headers_list();
preg_match("/'nonce-([^']+)'/", $headers, $matches);
```
**Result**: ❌ Platform headers invisible to PHP
**Evidence**: `headers_list()` doesn't include CSP header

### Attempt 4: custom-redirects.php
```php
<?php header('Content-Security-Policy: ...'); ?>
```
**Result**: ❌ Also overridden by platform
**Evidence**: Deployed to /htdocs/custom-redirects.php, CSP unchanged

**Conclusion**: Platform CSP is set at Nginx layer BEFORE PHP executes. No PHP code can modify it.

---

## Options (Decision Required)

### Option A: Migrate to Self-Hosted WordPress ⭐ RECOMMENDED

**Pros**:
- ✅ Full control over CSP and all headers
- ✅ Can use any CDN (Babylon.js, Elementor, etc.)
- ✅ SSH/root access for optimization
- ✅ No platform restrictions
- ✅ Better performance (no WordPress.com overhead)
- ✅ One-time migration vs. permanent limitations

**Cons**:
- ⏱️ Migration effort (4-6 hours)
- 💰 Hosting cost ($10-25/month for managed)
- 🔒 Manage security updates yourself (or use managed hosting)

**Hosting Recommendations**:
1. **Cloudways** ($10/mo) - Managed WordPress, good support
2. **DigitalOcean** ($6/mo) - Full control, requires more setup
3. **WP Engine** ($25/mo) - Premium managed, best support
4. **AWS Lightsail** ($5/mo) - Budget option, more technical

**Migration Steps** (I can guide you):
1. Export WordPress.com site (WP Admin → Tools → Export)
2. Set up WordPress on new host
3. Import content
4. Configure DNS
5. Deploy theme with full CSP control
6. Test and launch

**Timeline**: 4-6 hours total, can be done in stages

---

### Option B: Contact WordPress.com Support

**Pros**:
- ✅ No migration needed
- ✅ Might work if they whitelist domains

**Cons**:
- ⏳ Unknown timeline (days to weeks)
- ❓ May refuse (policy restrictions)
- 🔒 No guarantee it won't break in future
- ⚠️ Still dependent on platform policies
- 📝 Must provide business justification

**Support Channels**:
- Live Chat: https://wordpress.com/help/contact
- Email: support@wordpress.com
- Phone: Available for Business plans

**What to Request**:
- Add domains to platform CSP for skyyrose.co
- Include: cdn.babylonjs.com, stats.wp.com, widgets.wp.com, s0.wp.com, cdn.elementor.com, fonts-api.wp.com, cdnjs.cloudflare.com

**Escalation Strategy**:
- Emphasize business impact (109 errors, broken features)
- Note that WordPress.com's OWN domains are blocked (stats.wp.com, widgets.wp.com)
- Request escalation to platform engineering team

**Success Probability**: 30-50% (many users report "not possible" response)

---

### Option C: Remove Blocked Features

**Pros**:
- ✅ No migration needed
- ✅ Stay on WordPress.com

**Cons**:
- ❌ Remove 3D viewer (CORE brand feature)
- ❌ Limit Elementor usage
- ❌ Use only WordPress.com-approved CDNs
- ❌ Accept degraded luxury experience
- ❌ Competitive disadvantage

**What to Remove**:
- Babylon.js 3D product viewer
- Elementor advanced widgets
- Custom JavaScript libraries
- External CDN dependencies

**Impact**: This defeats the purpose of your luxury immersive brand experience.

---

### Option D: Hybrid Approach

**Split architecture**:
- Keep WordPress.com for content management
- Host immersive 3D pages on separate subdomain with full CSP control
- Use iframe/redirect to link between them

**Pros**:
- ✅ Keep WordPress.com for easy content updates
- ✅ Full CSP control for 3D experiences

**Cons**:
- ⚠️ Complex architecture (two systems)
- ⚠️ SEO complications (split domains)
- ⚠️ User experience friction (domain switching)
- 💰 Cost of second hosting

---

## Recommendation

**Migrate to self-hosted WordPress** (Option A) because:

1. **SkyyRose is a luxury brand** - You need full control over user experience
2. **3D immersive viewer is core to brand identity** - Can't compromise
3. **One-time effort vs. permanent limitations** - 4-6 hours migration vs. forever restricted
4. **Future-proof** - Full control for future features
5. **Better performance** - No WordPress.com overhead/restrictions
6. **Professional hosting is affordable** - $10-25/mo for managed solutions

**WordPress.com Business plan ($25/mo) vs. Cloudways ($10/mo)**:
- Cloudways: Full CSP control, SSH access, better performance
- WordPress.com: Platform restrictions, no root access, CSP locked

The migration pays for itself in flexibility and control.

---

## Decision Matrix

| Criteria | Self-Hosted (A) | Support (B) | Remove Features (C) | Hybrid (D) |
|----------|----------------|-------------|---------------------|------------|
| **3D Viewer Works** | ✅ Yes | ❓ Maybe | ❌ No | ✅ Yes |
| **Elementor Works** | ✅ Yes | ❓ Maybe | ⚠️ Limited | ⚠️ Split |
| **Timeline** | 4-6 hours | Days-Weeks | Immediate | 1-2 days |
| **Cost** | $10-25/mo | $25/mo (current) | $25/mo (current) | $35-50/mo |
| **Control** | ✅ Full | ❌ Limited | ❌ Limited | ⚠️ Split |
| **Risk** | Low | Medium-High | High | Medium |
| **Brand Impact** | ✅ Positive | ❓ Unknown | ❌ Negative | ⚠️ Neutral |

---

## What I Need from You

Please choose one of these options:

**A. Migrate to self-hosted WordPress**
- I'll guide you through entire process
- Can start immediately
- Minimal downtime (< 1 hour)

**B. Contact WordPress.com support**
- I've prepared support request documents
- You contact them, I provide technical details if needed
- Wait for response (timeline unknown)

**C. Remove blocked features**
- I'll modify theme to remove 3D viewer
- Simplify to WordPress.com-compatible features
- Accept limitations

**D. Explore hybrid approach**
- Design split architecture
- Estimate complexity and cost
- Implement if approved

**E. Other solution** (you suggest)

---

## Files Created for Reference

1. **CSP-ROOT-CAUSE-ANALYSIS.md** - Complete technical diagnosis
2. **WPCOM-CSP-SUPPORT-REQUEST.md** - Formatted support ticket
3. **FINAL-DECISION-REQUIRED.md** - This document
4. **custom-redirects.php** - Attempted fix (didn't work)

---

**Status**: ⏸️ WAITING FOR DECISION

Please let me know which option you'd like to pursue, and I'll proceed immediately.
