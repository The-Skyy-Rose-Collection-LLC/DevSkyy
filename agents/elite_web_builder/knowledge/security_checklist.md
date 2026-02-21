# Security Checklist (OWASP Top 10 for Web Themes)

## Input Validation
- Sanitize all user input (esc_html, esc_attr, esc_url)
- Parameterized queries for all database access
- Validate file uploads (type, size, extension)

## Authentication
- Never store passwords in plaintext
- Use WordPress nonces for form submissions
- CSRF protection on all state-changing operations

## Output Encoding
- HTML: esc_html()
- Attributes: esc_attr()
- URLs: esc_url()
- JavaScript: wp_json_encode()

## Headers
- Content-Security-Policy
- X-Content-Type-Options: nosniff
- X-Frame-Options: DENY
- Referrer-Policy: strict-origin-when-cross-origin

## Secrets
- Never hardcode API keys, passwords, or tokens
- Use environment variables or wp-config.php constants
- Never commit .env files
