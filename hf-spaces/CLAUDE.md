# DevSkyy HuggingFace Spaces

> GPU-optimized, responsive, monitored | 6 spaces

## Spaces
```
hf-spaces/
├── 3d-converter/          # Image to 3D mesh
├── flux-upscaler/         # FLUX upscaling
├── product-analyzer/      # Product analysis
├── product-photography/   # AI product photos
└── virtual-tryon/         # FASHN try-on
```

## Pattern
```python
def create_space_app() -> gr.Blocks:
    with gr.Blocks(theme=gr.themes.Soft()) as demo:
        gr.Markdown("# SkyyRose Product Analyzer")
        input_image = gr.Image(label="Upload Product")
        output = gr.JSON(label="Analysis")
        gr.Button("Analyze").click(fn=analyze, inputs=input_image, outputs=output)
    return demo
```

## Hardware
| Space | Hardware | Purpose |
|-------|----------|---------|
| virtual-tryon | T4 GPU | Real-time try-on |
| 3d-converter | A10G | Mesh generation |

## BEFORE CODING (MANDATORY)
1. **Context7**: `resolve-library-id` → `get-library-docs` for up-to-date docs
2. **Serena**: Use for codebase navigation and symbol lookup
3. **Verify**: `pytest -v` after EVERY change

## USE THESE TOOLS
| Task | Tool |
|------|------|
| 3D generation | **MCP**: `3d_generate` |
| Model search | **MCP**: HuggingFace `model_search` |

**"Every Space is a production service in waiting."**
