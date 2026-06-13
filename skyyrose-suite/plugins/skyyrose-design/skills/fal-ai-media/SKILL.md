---
name: fal-ai-media
description: Video and audio generation via fal.ai MCP. Covers text/image-to-video (Seedance, Kling, Veo 3), text-to-speech (CSM-1B), and video-to-audio (ThinkSound). For product or still images use the ai-image-generation skill (OpenAI Image 2 is the canonical SkyyRose engine) — fal.ai image models are not used for product imagery. Use when the user wants to generate videos or audio with AI.
origin: ECC
---

# fal.ai Media Generation

Generate images, videos, and audio using fal.ai models via MCP.

## When to Activate

- Creating videos from text or images
- Generating speech, music, or sound effects
- Any video/audio generation task
- User says "create video", "text to speech", "make a video", or similar

> **Product / still images → use the `ai-image-generation` skill** (OpenAI Image 2 / `gpt-image-2`, the canonical SkyyRose product-image engine). fal.ai image models (Nano Banana, etc.) are not used here.

## MCP Requirement

fal.ai MCP server must be configured. Add to `~/.claude.json`:

```json
"fal-ai": {
  "command": "npx",
  "args": ["-y", "fal-ai-mcp-server"],
  "env": { "FAL_KEY": "YOUR_FAL_KEY_HERE" }
}
```

Get an API key at [fal.ai](https://fal.ai).

## MCP Tools

The fal.ai MCP provides these tools:
- `search` — Find available models by keyword
- `find` — Get model details and parameters
- `generate` — Run a model with parameters
- `result` — Check async generation status
- `status` — Check job status
- `cancel` — Cancel a running job
- `estimate_cost` — Estimate generation cost
- `models` — List popular models
- `upload` — Upload files for use as inputs

---

## Image Generation → use `ai-image-generation`

SkyyRose product and still imagery is generated with **OpenAI Image 2 (`gpt-image-2`, high fidelity)** via the `ai-image-generation` skill — the locked canonical engine (`project_imagery_engine_oai2`), chosen for repeatable, identity-preserving product renders. **Do not** use fal.ai image models for product imagery. fal.ai's role in this skill is **video and audio only** (below).

Any paid image generation is gated by STOP-AND-SHOW (Action / SKU / Source / Cost → wait for `y`); see the `ai-image-generation` skill for the gate and the `belt`/`gpt-image-2` invocation.

---

## Video Generation

### Seedance 1.0 Pro (ByteDance)
Best for: text-to-video, image-to-video with high motion quality.

```
generate(
  model_name: "fal-ai/seedance-1-0-pro",
  input: {
    "prompt": "a drone flyover of a mountain lake at golden hour, cinematic",
    "duration": "5s",
    "aspect_ratio": "16:9",
    "seed": 42
  }
)
```

### Kling Video v3 Pro
Best for: text/image-to-video with native audio generation.

```
generate(
  model_name: "fal-ai/kling-video/v3/pro",
  input: {
    "prompt": "ocean waves crashing on a rocky coast, dramatic clouds",
    "duration": "5s",
    "aspect_ratio": "16:9"
  }
)
```

### Veo 3 (Google DeepMind)
Best for: video with generated sound, high visual quality.

```
generate(
  model_name: "fal-ai/veo-3",
  input: {
    "prompt": "a bustling Tokyo street market at night, neon signs, crowd noise",
    "aspect_ratio": "16:9"
  }
)
```

### Image-to-Video
Start from an existing image:

```
generate(
  model_name: "fal-ai/seedance-1-0-pro",
  input: {
    "prompt": "camera slowly zooms out, gentle wind moves the trees",
    "image_url": "<uploaded_image_url>",
    "duration": "5s"
  }
)
```

### Video Parameters

| Param | Type | Options | Notes |
|-------|------|---------|-------|
| `prompt` | string | required | Describe the video |
| `duration` | string | `"5s"`, `"10s"` | Video length |
| `aspect_ratio` | string | `"16:9"`, `"9:16"`, `"1:1"` | Frame ratio |
| `seed` | number | any integer | Reproducibility |
| `image_url` | string | URL | Source image for image-to-video |

---

## Audio Generation

### CSM-1B (Conversational Speech)
Text-to-speech with natural, conversational quality.

```
generate(
  model_name: "fal-ai/csm-1b",
  input: {
    "text": "Hello, welcome to the demo. Let me show you how this works.",
    "speaker_id": 0
  }
)
```

### ThinkSound (Video-to-Audio)
Generate matching audio from video content.

```
generate(
  model_name: "fal-ai/thinksound",
  input: {
    "video_url": "<video_url>",
    "prompt": "ambient forest sounds with birds chirping"
  }
)
```

### ElevenLabs (via API, no MCP)
For professional voice synthesis, use ElevenLabs directly:

```python
import os
import requests

resp = requests.post(
    "https://api.elevenlabs.io/v1/text-to-speech/<voice_id>",
    headers={
        "xi-api-key": os.environ["ELEVENLABS_API_KEY"],
        "Content-Type": "application/json"
    },
    json={
        "text": "Your text here",
        "model_id": "eleven_turbo_v2_5",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }
)
with open("output.mp3", "wb") as f:
    f.write(resp.content)
```

### VideoDB Generative Audio
If VideoDB is configured, use its generative audio:

```python
# Voice generation
audio = coll.generate_voice(text="Your narration here", voice="alloy")

# Music generation
music = coll.generate_music(prompt="upbeat electronic background music", duration=30)

# Sound effects
sfx = coll.generate_sound_effect(prompt="thunder crack followed by rain")
```

---

## Cost Estimation

Before generating, check estimated cost:

```
estimate_cost(model_name: "fal-ai/seedance-1-0-pro", input: {...})
```

## Model Discovery

Find models for specific tasks:

```
search(query: "text to video")
find(model_name: "fal-ai/seedance-1-0-pro")
models()
```

## Tips

- Use `seed` for reproducible results when iterating on prompts
- Start with shorter durations and lower-cost video models when iterating, then switch to higher-fidelity models for finals
- For video, keep prompts descriptive but concise — focus on motion and scene
- Image-to-video produces more controlled results than pure text-to-video
- Check `estimate_cost` before running expensive video generations

## Related Skills

- `videodb` — Video processing, editing, and streaming
- `video-editing` — AI-powered video editing workflows
- `content-engine` — Content creation for social platforms
