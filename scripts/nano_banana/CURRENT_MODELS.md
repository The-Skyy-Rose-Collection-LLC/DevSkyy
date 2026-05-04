# Nano Banana Tournament — Current Model Roster

**Last verified: 2026-05-04** against live model lists from each provider's API.

Re-verify before raising versions. Live discovery commands at the bottom of this file.

---

## Tournament Roster (production)

| Role | Model ID | API Surface | Notes |
|------|----------|-------------|-------|
| **Vision Judge 1** | `gpt-5.5-pro` | OpenAI Responses API | Reasoning Pro tier, multimodal, structured-JSON via `text.format` |
| **Vision Judge 2** | `gemini-3.1-pro-preview` | Google GenAI `models.generate_content` | Thinking-native, dynamic budget, structured-JSON via `response_schema` |
| **Synthesis Judge** | `claude-opus-4-7` | Anthropic Messages API | Adaptive thinking, text-only, reasons over both vision reports |

Defined in `scripts/nano_banana/tournament.py` as `GPT_JUDGE_MODEL`, `GEMINI_JUDGE_MODEL`, `OPUS_SYNTHESIS_MODEL`.

---

## SDK Contract Notes (these bite)

### OpenAI GPT-5.5-pro — must use Responses API

```python
client.responses.create(
    model="gpt-5.5-pro",
    reasoning={"effort": "high"},          # NOT reasoning_effort=
    max_output_tokens=16384,                # NOT max_tokens / max_completion_tokens
    text={"format": {"type": "json_schema", "name": "...", "strict": True, "schema": {...}}},
    input=[{
        "role": "user",
        "content": [
            {"type": "input_text", "text": "..."},      # NOT type: "text"
            {"type": "input_image", "image_url": "data:image/jpeg;base64,..."},  # NOT type: "image_url"
        ],
    }],
)
# Read with: response.output_text
```

`chat.completions.create()` silently produces empty content on Pro reasoning models — we discovered this by getting blank error messages from `concurrent.futures.TimeoutError` (which has empty `__str__`).

### Google Gemini 3.1 Pro Preview

```python
from google import genai
from google.genai import types

response = client.models.generate_content(
    model="gemini-3.1-pro-preview",
    contents=[
        "...",
        types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"),
    ],
    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=SCHEMA_DICT,
        max_output_tokens=16384,
        temperature=1.0,
        thinking_config=types.ThinkingConfig(thinking_budget=-1),  # -1 = dynamic, 0 = off
    ),
)
```

Model ID gotcha: `gemini-3.1-pro` (no suffix) returns 404. The live ID is `gemini-3.1-pro-preview`.

### Anthropic Claude Opus 4.7

```python
client.messages.create(
    model="claude-opus-4-7",
    max_tokens=4096,
    thinking={"type": "adaptive", "display": "summarized"},   # 4.7: adaptive only, no budget_tokens
    output_config={"effort": "xhigh"},                         # xhigh > high > medium > low
    messages=[{"role": "user", "content": "..."}],
)
# Read text from blocks where block.type == "text" (skip "thinking" blocks)
```

Opus 4.7 removed `temperature`/`top_p`/`top_k` and the fixed `budget_tokens` mode. Adaptive thinking is the only on-mode; `display: "summarized"` makes thinking content visible (default is `omitted`).

---

## Live-discovery commands (run before bumping versions)

### OpenAI — list available models

```bash
python3 -c "
import os
from openai import OpenAI
c = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
for m in sorted(c.models.list().data, key=lambda x: x.id):
    if 'gpt-5' in m.id or 'o3' in m.id or 'o4' in m.id:
        print(m.id)
"
```

### Google — list models supporting generateContent

```bash
python3 -c "
import os
from google import genai
c = genai.Client(api_key=os.environ['GOOGLE_API_KEY'])
for m in c.models.list():
    if 'generateContent' in (m.supported_actions or []) and 'gemini-3' in m.name:
        print(f'{m.name}  {m.display_name or \"\"}')
"
```

### Anthropic — list available models

```bash
python3 -c "
import os
from anthropic import Anthropic
c = Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])
for m in c.models.list(limit=50).data:
    if 'opus' in m.id or 'sonnet' in m.id:
        print(f'{m.id}  {m.display_name}')
"
```

---

## Snapshot of full live catalog (2026-05-04)

### OpenAI GPT-5 family (Chat Completions + Responses APIs)

```
gpt-5                      gpt-5.1                    gpt-5.4
gpt-5-2025-08-07           gpt-5.1-2025-11-13         gpt-5.4-2026-03-05
gpt-5-chat-latest          gpt-5.1-chat-latest        gpt-5.4-mini
gpt-5-codex                gpt-5.1-codex              gpt-5.4-mini-2026-03-17
gpt-5-mini                 gpt-5.1-codex-max          gpt-5.4-nano
gpt-5-mini-2025-08-07      gpt-5.1-codex-mini         gpt-5.4-nano-2026-03-17
gpt-5-nano                 gpt-5.2                    gpt-5.4-pro
gpt-5-nano-2025-08-07      gpt-5.2-2025-12-11         gpt-5.4-pro-2026-03-05
gpt-5-pro                  gpt-5.2-chat-latest        gpt-5.5
gpt-5-pro-2025-10-06       gpt-5.2-codex              gpt-5.5-2026-04-23
gpt-5-search-api           gpt-5.2-pro                gpt-5.5-pro          ← chosen
gpt-5-search-api-2025-10-14 gpt-5.2-pro-2025-12-11    gpt-5.5-pro-2026-04-23
                           gpt-5.3-chat-latest
                           gpt-5.3-codex
```

Plus o-series reasoning models: `o3`, `o3-pro`, `o3-deep-research`, `o3-mini`, `o4-mini`, `o4-mini-deep-research`.

### Google Gemini family (generateContent-supporting)

```
gemini-2.5-pro                              Gemini 2.5 Pro
gemini-2.5-pro-preview-tts                  Gemini 2.5 Pro Preview TTS
gemini-3-flash-preview                      Gemini 3 Flash Preview
gemini-3-pro-image-preview                  Nano Banana Pro
gemini-3-pro-preview                        Gemini 3 Pro Preview
gemini-3.1-flash-image-preview              Nano Banana 2
gemini-3.1-flash-lite-preview               Gemini 3.1 Flash Lite Preview
gemini-3.1-flash-tts-preview                Gemini 3.1 Flash TTS Preview
gemini-3.1-pro-preview                      Gemini 3.1 Pro Preview   ← chosen
gemini-3.1-pro-preview-customtools          Gemini 3.1 Pro Preview Custom Tools
```

### Anthropic Claude family (chosen)

```
claude-opus-4-7                             ← chosen for synthesis
claude-opus-4-6                             prior generation
claude-sonnet-4-6                           cheaper, lower-priority work
claude-haiku-4-5                            high-volume / cost-sensitive paths
```

---

## Why these specific picks

- **`gpt-5.5-pro`** is the latest (2026-04-23) Pro-tier reasoning model. Pro tier supports `reasoning={"effort": "high"}` and outperforms standard `gpt-5.5` on the visual-comparison benchmarks our judge prompt mirrors.
- **`gemini-3.1-pro-preview`** is the newest Pro Gemini available. The preview suffix is structural — Google ships 3.1-Pro under `-preview` until the public-stable cutover. `gemini-3-pro-preview` (the older 3.0 Pro preview) is still available but lacks 3.1's improved long-context vision reasoning.
- **`claude-opus-4-7`** is unchanged from the prior config. Opus 4.7 added Task Budgets, removed sampling params, and made thinking content opt-in via `display: "summarized"` — all relevant to the synthesis use case where we want visible reasoning that we don't display directly.

---

## Gitignored env files (each holds one role's key, chmod 600)

```
.env.judge-gpt-vision      → OPENAI_API_KEY     (Vision Judge 1)
.env.judge-gemini-vision   → GOOGLE_API_KEY     (Vision Judge 2)
.env.judge-opus-thinking   → ANTHROPIC_API_KEY  (Synthesis Judge)
```

Per-judge isolation: rotating one key never touches another. The `.env.*` pattern in `.gitignore` covers all three automatically.
