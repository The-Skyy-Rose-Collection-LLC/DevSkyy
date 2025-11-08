# i18n/l10n Guide - Bounded Autonomy System

## Overview

The Bounded Autonomy System includes comprehensive **internationalization (i18n)** and **localization (l10n)** support for multi-language deployments.

**Supported Languages:**
- `en-US` - English (United States) - **Default**
- `es-ES` - Spanish (Spain)
- `fr-FR` - French (France)
- `ja-JP` - Japanese (Japan)
- `zh-CN` - Chinese (Simplified, China)

---

## Quick Start

### Basic Usage

```python
from fashion_ai_bounded_autonomy import t, set_language

# Use default language (en-US)
print(t('approval.submitted', action_id='ACT-123', workflow='default'))
# Output: "Action ACT-123 submitted for review (workflow: default)"

# Switch to Spanish
set_language('es-ES')
print(t('approval.submitted', action_id='ACT-123', workflow='default'))
# Output: "Acción ACT-123 enviada para revisión (flujo de trabajo: default)"

# Switch to Japanese
set_language('ja-JP')
print(t('tasks.success', name='test_task', task_id='001'))
# Output: "✅ タスク test_task [001] が正常に完了しました"
```

### Setting Language via Environment Variable

```bash
# Set language for entire system
export LANGUAGE=es-ES

# Or use LANG variable
export LANG=fr-FR.UTF-8

# Run your application
python -m fashion_ai_bounded_autonomy.approval_cli list
```

---

## API Reference

### Functions

#### `t(key: str, **kwargs) -> str`
Translate a key to the current language with variable substitution.

**Parameters:**
- `key` - Translation key in dot notation (e.g., `'approval.submitted'`)
- `**kwargs` - Variables to substitute in the translation string

**Returns:** Translated string

**Example:**
```python
from fashion_ai_bounded_autonomy import t

result = t('approval.timeout', hours=24)
# Returns: "Approval request will expire in 24 hours"
```

#### `set_language(language_code: str) -> bool`
Set the current language globally.

**Parameters:**
- `language_code` - Language code (e.g., `'es-ES'`, `'fr-FR'`)

**Returns:** `True` if successful, `False` if language not available

**Example:**
```python
from fashion_ai_bounded_autonomy import set_language

if set_language('es-ES'):
    print("Language changed to Spanish")
else:
    print("Spanish not available")
```

#### `get_language() -> str`
Get the current language code.

**Returns:** Current language code (e.g., `'en-US'`)

**Example:**
```python
from fashion_ai_bounded_autonomy import get_language

current = get_language()
print(f"Current language: {current}")
```

#### `get_available_languages() -> list[str]`
Get list of all available language codes.

**Returns:** List of language codes

**Example:**
```python
from fashion_ai_bounded_autonomy import get_available_languages

languages = get_available_languages()
print(f"Available: {languages}")
# Output: ['en-US', 'es-ES', 'fr-FR', 'ja-JP', 'zh-CN']
```

---

## Translation Keys

### Approval System

| Key | Variables | Description |
|-----|-----------|-------------|
| `approval.submitted` | `action_id`, `workflow` | Action submitted for review |
| `approval.approved` | `action_id`, `operator` | Action approved by operator |
| `approval.rejected` | `action_id`, `operator` | Action rejected by operator |
| `approval.executed` | `action_id` | Action executed successfully |
| `approval.timeout` | `hours` | Approval expiration time |
| `approval.expired` | `action_id` | Action has expired |
| `approval.not_found` | `action_id` | Action not found |
| `approval.cleanup_expired` | `count` | Cleanup completed |

### CLI Messages

| Key | Variables | Description |
|-----|-----------|-------------|
| `cli.welcome` | - | CLI welcome message |
| `cli.list_pending` | - | Listing pending actions |
| `cli.list_empty` | - | No pending actions |
| `cli.review_action` | `action_id` | Reviewing action |
| `cli.approve_success` | - | Action approved |
| `cli.reject_success` | - | Action rejected |
| `cli.error` | `message` | Error message |

### Task Execution

| Key | Variables | Description |
|-----|-----------|-------------|
| `tasks.success` | `name`, `task_id` | Task completed successfully |
| `tasks.failure` | `name`, `task_id`, `error` | Task failed |
| `tasks.retry` | `name`, `task_id`, `error` | Task retrying |
| `tasks.approval_notification_sent` | `action_id` | Notification sent |
| `tasks.data_processed` | `file_path` | Data processed |
| `tasks.health_check` | - | Health check passed |
| `tasks.unhealthy_agents` | `agents` | Unhealthy agents detected |

### Error Messages

| Key | Variables | Description |
|-----|-----------|-------------|
| `errors.generic` | `error` | Generic error |
| `errors.database` | `error` | Database error |
| `errors.validation` | `error` | Validation error |
| `errors.timeout` | `seconds` | Operation timeout |
| `errors.unauthorized` | - | Unauthorized access |
| `errors.not_found` | `resource` | Resource not found |

### System Messages

| Key | Variables | Description |
|-----|-----------|-------------|
| `system.startup` | - | System starting |
| `system.ready` | - | System ready |
| `system.shutdown` | - | System shutting down |
| `system.redis_connected` | - | Redis connection success |
| `system.redis_error` | - | Redis connection failed |

---

## Adding New Translations

### Step 1: Add Key to All Language Files

Edit all files in `fashion_ai_bounded_autonomy/i18n/`:

**en-US.json:**
```json
{
  "my_module": {
    "my_message": "This is my message with {variable}"
  }
}
```

**es-ES.json:**
```json
{
  "my_module": {
    "my_message": "Este es mi mensaje con {variable}"
  }
}
```

**fr-FR.json:**
```json
{
  "my_module": {
    "my_message": "Ceci est mon message avec {variable}"
  }
}
```

**ja-JP.json:**
```json
{
  "my_module": {
    "my_message": "これは {variable} を含むメッセージです"
  }
}
```

**zh-CN.json:**
```json
{
  "my_module": {
    "my_message": "这是包含 {variable} 的消息"
  }
}
```

### Step 2: Use in Code

```python
from fashion_ai_bounded_autonomy.i18n_loader import t

message = t('my_module.my_message', variable='example')
print(message)
```

---

## Translation File Format

Translation files are JSON with nested structure using dot notation:

```json
{
  "category": {
    "subcategory": {
      "key": "Translation text with {variable}"
    }
  }
}
```

**Access:** `t('category.subcategory.key', variable='value')`

### Variable Substitution

Use `{variable_name}` in translation strings:

```json
{
  "greeting": "Hello {name}, you have {count} messages"
}
```

```python
t('greeting', name='Alice', count=5)
# Returns: "Hello Alice, you have 5 messages"
```

---

## Best Practices

### 1. Always Provide All Languages
When adding a new translation key, add it to **all 5 language files** to avoid fallback behavior.

### 2. Use Descriptive Keys
```python
# Good
t('approval.action_submitted')

# Bad
t('msg1')
```

### 3. Keep Variables Consistent
Use the same variable names across all languages:

```json
// en-US.json
{"msg": "User {username} logged in"}

// es-ES.json
{"msg": "Usuario {username} inició sesión"}
```

### 4. Test All Languages
```python
for lang in get_available_languages():
    set_language(lang)
    print(f"{lang}: {t('test.message')}")
```

### 5. Handle Missing Translations
The system returns the key itself if translation is missing:

```python
result = t('nonexistent.key')
# Returns: "nonexistent.key"
```

---

## CLI Usage

### List Pending Actions in Spanish
```bash
LANGUAGE=es-ES python -m fashion_ai_bounded_autonomy.approval_cli list
```

### Approve Action in French
```bash
LANG=fr-FR python -m fashion_ai_bounded_autonomy.approval_cli approve ACT-123 --operator jean
```

### Review in Japanese
```bash
export LANGUAGE=ja-JP
python -m fashion_ai_bounded_autonomy.approval_cli review ACT-123
```

---

## Programmatic Language Switching

### Context Manager Pattern
```python
from fashion_ai_bounded_autonomy import t, set_language, get_language

def translate_for_user(user_language: str):
    """Switch language temporarily"""
    original = get_language()
    try:
        set_language(user_language)
        return t('approval.submitted', action_id='ACT-123', workflow='default')
    finally:
        set_language(original)

# Use for different users
spanish_msg = translate_for_user('es-ES')
japanese_msg = translate_for_user('ja-JP')
```

### Multi-User Support
```python
from fashion_ai_bounded_autonomy.i18n_loader import TranslationLoader

# Create separate loader instances for different users
user1_i18n = TranslationLoader('es-ES')
user2_i18n = TranslationLoader('ja-JP')

msg1 = user1_i18n.translate('approval.submitted', action_id='A1', workflow='default')
msg2 = user2_i18n.translate('approval.submitted', action_id='A2', workflow='default')
```

---

## Testing i18n

Run the integration test:

```bash
python test_i18n_integration.py
```

**Expected Output:**
```
✅ Test 1: Available Languages
  ✓ en-US loaded
  ✓ es-ES loaded
  ✓ fr-FR loaded
  ✓ ja-JP loaded
  ✓ zh-CN loaded

✅ Test 2: Default Language
Current language: en-US

✅ Test 3: Key Translations
  Language: en-US
    approval.submitted: Action test123 submitted for review...

  Language: es-ES
    approval.submitted: Acción test123 enviada para revisión...

✅ All tests passed!
```

---

## Troubleshooting

### Issue: Translation Not Found
**Symptom:** Key is returned instead of translation

**Solution:**
1. Check that key exists in translation file
2. Verify JSON syntax is valid
3. Reload translation files by restarting application

### Issue: Variables Not Substituted
**Symptom:** `{variable}` appears in output

**Solution:**
1. Ensure variable names match between code and translation file
2. Pass variables as keyword arguments: `t('key', variable='value')`

### Issue: Wrong Language Displayed
**Symptom:** English displayed when Spanish expected

**Solution:**
1. Check language code is correct: `'es-ES'` not `'es'`
2. Verify `set_language()` returned `True`
3. Check `LANGUAGE` or `LANG` environment variable

---

## File Structure

```
fashion_ai_bounded_autonomy/
├── i18n/                      # Translation files directory
│   ├── en-US.json            # English (default)
│   ├── es-ES.json            # Spanish
│   ├── fr-FR.json            # French
│   ├── ja-JP.json            # Japanese
│   └── zh-CN.json            # Chinese (Simplified)
├── i18n_loader.py            # Translation loader module
└── I18N_GUIDE.md             # This documentation
```

---

## Contributing Translations

To add a new language:

1. Create new file: `fashion_ai_bounded_autonomy/i18n/{lang-CODE}.json`
2. Copy structure from `en-US.json`
3. Translate all values (keep keys unchanged)
4. Test with `python test_i18n_integration.py`
5. Update this guide with new language code

---

## License

Copyright © 2025 The Skyy Rose Collection LLC
All translations are proprietary to The Skyy Rose Collection LLC.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-01-08 | Initial i18n implementation with 5 languages |

---

**For questions or issues, see:** `fashion_ai_bounded_autonomy/README.md`
