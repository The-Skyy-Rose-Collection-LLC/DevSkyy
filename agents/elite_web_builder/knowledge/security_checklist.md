# Security Checklist (OWASP Top 10 for Web Themes)

## A01: Broken Access Control
- [ ] Admin pages require authentication
- [ ] No directory listing enabled
- [ ] File permissions correct (644 files, 755 dirs)
- [ ] No direct access to PHP includes (`defined('ABSPATH') || exit`)

## A02: Cryptographic Failures
- [ ] HTTPS enforced (especially checkout)
- [ ] No sensitive data in URL parameters
- [ ] API keys in environment variables, not source code
- [ ] Passwords hashed (WordPress uses phpass)

## A03: Injection
- [ ] All database queries use `$wpdb->prepare()` (WordPress)
- [ ] User input sanitized: `sanitize_text_field()`, `esc_html()`, `esc_attr()`
- [ ] No `eval()`, `exec()`, or `system()` with user input
- [ ] JSON output uses `wp_json_encode()` or `json_encode()`

## A04: Insecure Design
- [ ] Rate limiting on login, registration, and API endpoints
- [ ] CSRF protection via nonces (`wp_nonce_field()`, `check_admin_referer()`)
- [ ] Input validation on all form submissions
- [ ] File upload restrictions (type, size, rename)

## A05: Security Misconfiguration
- [ ] WordPress version hidden (`remove_action('wp_head', 'wp_generator')`)
- [ ] XML-RPC disabled (`add_filter('xmlrpc_enabled', '__return_false')`)
- [ ] Debug mode off in production (`WP_DEBUG = false`)
- [ ] Directory browsing disabled
- [ ] Unused plugins deactivated and removed

## A06: Vulnerable Components
- [ ] All plugins up to date
- [ ] WordPress core up to date
- [ ] No known-vulnerable libraries
- [ ] NPM/Composer audit clean

## A07: Auth Failures
- [ ] Strong password policy enforced
- [ ] Two-factor authentication available
- [ ] Brute-force protection (Jetpack, limit login attempts)
- [ ] Session timeout configured

## A08: Data Integrity
- [ ] CSP headers set (`Content-Security-Policy`)
- [ ] SRI hashes on CDN scripts (`integrity="sha384-..."`)
- [ ] No inline scripts without nonce

## A09: Logging
- [ ] Failed login attempts logged
- [ ] Admin actions logged
- [ ] API errors logged (without sensitive data)
- [ ] Log rotation configured

## A10: SSRF
- [ ] No user-controlled URLs in server-side requests
- [ ] Allowlist for external API calls
- [ ] No file inclusion from user input

## Secret Patterns to Detect

| Pattern | Example |
|---------|---------|
| OpenAI API Key | `sk-proj-...` (20+ chars) |
| Google API Key | `AIza...` (35+ chars) |
| Stripe Key | `sk_live_...` or `sk_test_...` |
| GitHub Token | `ghp_...` or `github_pat_...` |
| AWS Key | `AKIA...` (20 chars) |
| xAI API Key | `xai-...` |
| Generic | `password = "..."` or `secret = "..."` |

## WordPress-Specific

### Nonces
```php
// Create
wp_nonce_field('my_action', 'my_nonce');

// Verify
if (!wp_verify_nonce($_POST['my_nonce'], 'my_action')) {
    wp_die('Security check failed');
}
```

### Escaping Output
```php
echo esc_html($user_input);       // In HTML context
echo esc_attr($user_input);       // In HTML attributes
echo esc_url($user_input);        // In URLs
echo wp_kses_post($user_input);   // Allow safe HTML
```
