# Full-Stack AI Provider Wiring — Design Doc

**Date:** 2026-03-05
**Status:** Approved

## Goal

Wire up OpenAI, Anthropic, and Google AI providers into the SkyyRose flagship WordPress theme using the official WordPress PHP AI Client SDK.

## Capabilities

| Provider | Text Gen | Image Gen | Function Calling |
|----------|----------|-----------|-----------------|
| OpenAI | GPT-4o, GPT-4.1 | DALL-E 3, GPT Image | Yes |
| Anthropic | Claude Opus/Sonnet | No | Yes |
| Google | Gemini 2.5 | Imagen 3 | Yes |

## Architecture

```
functions.php
  └── inc/ai-providers.php (provider registration + helpers)
        ├── wp-ai-client/ (WordPress plugin layer)
        │     └── php-ai-client/ (core SDK)
        │           ├── ai-provider-for-openai (Composer)
        │           ├── ai-provider-for-anthropic (Composer)
        │           └── ai-provider-for-google (Composer)
        └── Helper functions:
              ├── skyyrose_ai_text($prompt, $provider?)
              ├── skyyrose_ai_image($prompt, $provider?)
              └── skyyrose_ai_function_call($prompt, $tools, $provider?)
```

## Implementation Steps

1. Install Composer via Homebrew
2. Update composer.json with provider dependencies
3. Run composer install
4. Create inc/ai-providers.php with registration + helpers
5. Wire into functions.php
6. Test provider availability

## API Key Management

WordPress admin: Settings > AI Credentials
Keys stored in wp_options (wp_ai_client_provider_credentials)

## Files

| File | Action |
|------|--------|
| composer.json | Update dependencies |
| inc/ai-providers.php | New — registration + helpers |
| functions.php | Add require_once |
