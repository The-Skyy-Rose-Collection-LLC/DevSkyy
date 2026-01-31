# SkyyRose WordPress Theme - Security Hardening

**Version**: 2.0.0
**Last Updated**: 2026-01-30

---

## Security Measures Implemented

### 1. XML-RPC Disabled ✅

**Why**: XML-RPC is a legacy WordPress API that's commonly exploited for:
- Brute force attacks (amplification via `system.multicall`)
- DDoS attacks via pingback
- Password enumeration
- Resource exhaustion

**What we did**:
```php
// Completely disable XML-RPC
add_filter('xmlrpc_enabled', '__return_false');

// Remove pingback header
add_filter('wp_headers', function($headers) {
    unset($headers['X-Pingback']);
    return $headers;
});

// Block specific XML-RPC methods
add_filter('xmlrpc_methods', function($methods) {
    unset($methods['pingback.ping']);
    unset($methods['pingback.extensions.getPingbacks']);
    return $methods;
});

// Block authentication to xmlrpc.php
add_filter('authenticate', function($user, $username, $password) {
    if (isset($_SERVER['REQUEST_URI']) && strpos($_SERVER['REQUEST_URI'], 'xmlrpc.php') !== false) {
        return new WP_Error('xmlrpc_disabled', __('XML-RPC services are disabled on this site.'));
    }
    return $user;
}, 20, 3);
```

**Impact**: XML-RPC completely disabled. If you need it for mobile apps or JetPack, remove these filters.

---

### 2. Security Headers ✅

**Why**: Modern browsers respect security headers to prevent common attacks.

**What we did**:
```php
header('X-Content-Type-Options: nosniff');           // Prevent MIME sniffing
header('X-Frame-Options: SAMEORIGIN');               // Prevent clickjacking
header('X-XSS-Protection: 1; mode=block');           // Enable XSS filter
header('Referrer-Policy: strict-origin-when-cross-origin'); // Control referrer
header('Permissions-Policy: geolocation=(), microphone=(), camera=()'); // Disable sensitive APIs
```

**Impact**: Enhanced browser-level security. No functional changes.

---

### 3. REST API Protection ✅

**Why**: WordPress REST API can leak sensitive data to unauthenticated users.

**What we did**:
```php
// Block unauthenticated REST API access
// EXCEPT WooCommerce endpoints (needed for cart/checkout)
add_filter('rest_authentication_errors', function($result) {
    // Allow WooCommerce REST API
    if (strpos($_SERVER['REQUEST_URI'], '/wc/') !== false) {
        return $result;
    }

    // Allow logged-in users
    if (is_user_logged_in()) {
        return $result;
    }

    // Block everyone else
    return new WP_Error('rest_disabled', __('REST API is disabled for unauthorized users.'), array('status' => 403));
});
```

**Impact**: REST API disabled for guests, except WooCommerce endpoints. Admin users can still use it.

---

### 4. Login Rate Limiting ✅

**Why**: Prevent brute force attacks on wp-login.php.

**What we did**:
```php
// Track failed login attempts by IP
add_action('wp_login_failed', function($username) {
    $ip = $_SERVER['REMOTE_ADDR'];
    $attempts = get_transient('login_attempts_' . md5($ip)) ?: 0;
    $attempts++;
    set_transient('login_attempts_' . md5($ip), $attempts, 15 * MINUTE_IN_SECONDS);

    if ($attempts >= 5) {
        wp_die('Too many failed login attempts. Try again in 15 minutes.', 403);
    }
});

// Reset on successful login
add_action('wp_login', function($username, $user) {
    $ip = $_SERVER['REMOTE_ADDR'];
    delete_transient('login_attempts_' . md5($ip));
}, 10, 2);
```

**Impact**: Max 5 failed login attempts per IP per 15 minutes. Legitimate users unaffected.

---

### 5. File Editing Disabled ✅

**Why**: Prevent theme/plugin editing from WordPress admin (common attack vector after compromise).

**What we did**:
```php
define('DISALLOW_FILE_EDIT', true);
```

**Impact**: "Theme Editor" and "Plugin Editor" removed from admin. Must edit files via FTP/SSH.

---

### 6. WordPress Version Hidden ✅

**Why**: Prevent version fingerprinting used to identify vulnerable installations.

**What we did**:
```php
remove_action('wp_head', 'wp_generator');  // Remove version from HTML
remove_action('wp_head', 'rsd_link');      // Remove RSD link (XML-RPC related)
```

**Impact**: WordPress version not visible in HTML. Minor security-through-obscurity improvement.

---

## Additional Recommendations

### Server-Level Security (Not in Theme)

1. **Force HTTPS**
   ```apache
   # .htaccess
   RewriteEngine On
   RewriteCond %{HTTPS} off
   RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
   ```

2. **Block xmlrpc.php at server level**
   ```apache
   # .htaccess
   <Files xmlrpc.php>
   Order Deny,Allow
   Deny from all
   </Files>
   ```

3. **Limit wp-login.php access**
   ```apache
   # .htaccess (allow only your IP)
   <Files wp-login.php>
   Order Deny,Allow
   Deny from all
   Allow from 123.456.789.0
   </Files>
   ```

4. **Hide wp-config.php**
   ```apache
   # .htaccess
   <Files wp-config.php>
   Order Deny,Allow
   Deny from all
   </Files>
   ```

### Plugin Recommendations

1. **Wordfence** or **Sucuri Security** - Comprehensive security suite
2. **iThemes Security** - Additional hardening options
3. **WP Fail2Ban** - Advanced brute force protection
4. **Disable XML-RPC-API** - Extra XML-RPC protection (though theme already disables it)

### Environment Variables

Store sensitive data in `.env` (never commit to git):

```bash
# .env
DB_NAME=skyyrose_db
DB_USER=skyyrose_user
DB_PASSWORD=strong_random_password_here
DB_HOST=localhost

# WooCommerce API Keys
WC_CONSUMER_KEY=ck_xxxxxxxxxxxxx
WC_CONSUMER_SECRET=cs_xxxxxxxxxxxxx

# Email settings
SMTP_HOST=smtp.example.com
SMTP_USER=hello@skyyrose.co
SMTP_PASS=strong_email_password
```

Load in `wp-config.php`:
```php
require_once(__DIR__ . '/vendor/autoload.php');
$dotenv = Dotenv\Dotenv::createImmutable(__DIR__);
$dotenv->load();

define('DB_NAME', $_ENV['DB_NAME']);
define('DB_USER', $_ENV['DB_USER']);
define('DB_PASSWORD', $_ENV['DB_PASSWORD']);
define('DB_HOST', $_ENV['DB_HOST']);
```

---

## Testing Security

### 1. Test XML-RPC Disabled

```bash
# Should return error or 403
curl -X POST https://yoursite.com/xmlrpc.php \
  -H 'Content-Type: application/xml' \
  -d '<?xml version="1.0"?><methodCall><methodName>demo.sayHello</methodName></methodCall>'
```

### 2. Test REST API Protection

```bash
# Should return 403 (unless logged in)
curl https://yoursite.com/wp-json/wp/v2/users

# WooCommerce endpoints should still work
curl https://yoursite.com/wp-json/wc/v3/products
```

### 3. Test Login Rate Limiting

Try logging in with wrong password 6 times - should be blocked on 6th attempt.

### 4. Check Security Headers

```bash
curl -I https://yoursite.com | grep -i "x-frame\|x-xss\|x-content"
```

Should see:
```
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
X-XSS-Protection: 1; mode=block
```

---

## Security Checklist

Before going live:

- [ ] XML-RPC disabled (test with curl)
- [ ] HTTPS enforced (test HTTP redirect)
- [ ] Security headers present (check with curl -I)
- [ ] REST API protected (test unauthenticated access)
- [ ] Login rate limiting active (test failed logins)
- [ ] File editing disabled (check WordPress admin)
- [ ] wp-config.php permissions set to 400
- [ ] Database credentials in .env (not in git)
- [ ] WooCommerce API keys secured
- [ ] Admin username not "admin"
- [ ] Strong passwords for all users
- [ ] Two-factor authentication enabled
- [ ] Regular backups configured
- [ ] Security plugin installed (Wordfence/Sucuri)
- [ ] SSL certificate valid and auto-renewing

---

## Incident Response

If compromised:

1. **Immediate Actions**
   - Take site offline (maintenance mode)
   - Change all passwords (WordPress, database, FTP, hosting)
   - Revoke all API keys
   - Check for backdoors in theme/plugin files

2. **Investigation**
   - Check access logs for suspicious IPs
   - Review file modifications (last modified dates)
   - Scan for malware (Wordfence/Sucuri)
   - Check database for injected content

3. **Recovery**
   - Restore from clean backup
   - Update WordPress core, plugins, themes
   - Re-apply security hardening
   - Monitor logs for 48 hours

4. **Prevention**
   - Review how breach occurred
   - Update security measures
   - Consider WAF (Web Application Firewall)
   - Enable file integrity monitoring

---

## Contact

**Security Issues**: security@skyyrose.co
**General Support**: hello@skyyrose.co

**SkyyRose LLC**
Oakland, California

---

**Last Updated**: 2026-01-30
**Review Frequency**: Quarterly
