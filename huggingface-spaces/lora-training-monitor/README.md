---
title: SkyyRose LoRA Training Monitor
emoji: 🚀
colorFrom: pink
colorTo: red
sdk: gradio
sdk_version: 5.0.0
app_file: app.py
pinned: false
---

# 🚀 SkyyRose LoRA Training Monitor

Real-time monitoring for SkyyRose LoRA training jobs. Connects to DevSkyy backend API to track training progress, metrics, and history.

## Features

- 📊 Real-time training status
- 📉 Loss and learning rate monitoring
- 🔄 Auto-refresh every 10 seconds
- 📜 Training job history
- ➕ Start new training jobs
- 🎯 SkyyRose brand DNA learning

## Configuration

### Environment Variables

Set these in HuggingFace Space secrets:

- `DEVSKYY_API_KEY` (required): API key for DevSkyy backend
- `DEVSKYY_API_URL` (optional): Backend API URL (default: https://api.devskyy.app)

## Training Pipeline

1. **Dataset**: 254 SkyyRose product photos with metadata
2. **Base Model**: SDXL (Stable Diffusion XL)
3. **LoRA Training**: Learn brand DNA (rose gold accents, luxury aesthetic)
4. **Integration**: Use trained LoRA in Product Photography Space

## Backend Integration

Connects to DevSkyy API endpoints:

- `GET /api/v1/training/status` - Current training status
- `GET /api/v1/training/jobs` - Training job history
- `POST /api/v1/training/start` - Start new training job

## Built With

- Gradio 5.0
- httpx for async HTTP
- DevSkyy Platform backend

---

Built by [SkyyRose](https://skyyrose.com) | [DevSkyy Platform](https://app.devskyy.app)
