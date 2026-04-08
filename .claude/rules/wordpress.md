# WordPress Coding Rules

> Source of truth for ALL WordPress/PHP constraints. Referenced from CLAUDE.md.

## Core Principles

- Extend via hooks (actions/filters), never modify core
- API: `index.php?rest_route=` NOT `/wp-json/`

## Output Escaping

Escape ALL output:
- `esc_html()` — text content
- `esc_attr()` — HTML attributes
- `esc_url()` — URLs
- `wp_kses_post()` — rich HTML (post content)

## Input Sanitization

Sanitize ALL input:
- `sanitize_text_field()` — plain text
- `absint()` — positive integers
- `sanitize_email()` — email addresses

## Database Security

- Always `$wpdb->prepare()` — never concatenate untrusted input
- Nonce + capability checks on all write actions

## JavaScript in WordPress

- No `innerHTML` — use `createElement` + `textContent`
- Use `wp_localize_script()` or `wp_add_inline_script()` for data passing
