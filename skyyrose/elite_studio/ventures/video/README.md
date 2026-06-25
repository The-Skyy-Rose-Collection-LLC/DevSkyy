# Video & Animation Venture

> Status: **alpha** — surface scaffolded, providers minimal, agent wiring deferred.

Animated product video pipeline. Targets vertical (9:16) social-ready
output. Composes the existing `AnigenAgent` (root) and Elite Studio's
`TryOnAgent` (for try-on video output).

## Surface

```python
from skyyrose.elite_studio.ventures.video import VideoPipeline, MANIFEST

pipeline = VideoPipeline()
result = pipeline.run_smoke(sku="br-001")
```

## CLI

```bash
python -m skyyrose.elite_studio.ventures.video info
python -m skyyrose.elite_studio.ventures.video agents
python -m skyyrose.elite_studio.ventures.video status
python -m skyyrose.elite_studio.ventures.video smoke --sku br-001
```

## Agent Roster

| Role         | Agent          | Wired |
| ------------ | -------------- | ----- |
| animation    | AniGenAgent    | no    |
| tryon_video  | TryOnAgent     | no    |

## Roadmap

1. Wire `AniGenAgent` into a `storyboard` + `frame_gen` node pair.
2. Wire `TryOnAgent` into a `tryon_video` node for model-wearing-garment clips.
3. Add an `audio_bed` node (royalty-free or generated).
4. Add an `encode` node (ffmpeg → mp4 + webm).
5. Add an `upload` node (WordPress media + Cloudflare R2).
6. Add provider expansion: FASHN video, Runway, Pika, Sora when available.
