# LangChain Image Generation Models — Ghost Mannequin Pipeline

**Project:** SkyyRose v1.2 — Ghost Mannequin Batch Generation
**Research scope:** LangChain/LangGraph image generation integrations for luxury streetwear product photography
**Researched:** 2026-04-22
**Overall confidence:** HIGH (integration patterns), HIGH (model rankings), MEDIUM (ghost-mannequin-specific benchmarks — no garment-specific published benchmarks exist; assessments derived from general text-rendering and product photography benchmarks)

---

## The Core Question

> Which image generation model should be PRIMARY in the Elite Studio ghost mannequin LangGraph pipeline, and how do you wire it into a LangGraph node?

**Answer first:** Keep Gemini 2.5 Flash Image as primary for cost, speed, and existing integration. Add GPT-Image-1 (medium quality) as the first fallback, specifically for jerseys with critical text (numbers, stitched lettering). Ideogram v3 as a specialized text-rescue fallback. Skip Recraft v3, SD 3.5, and FLUX Kontext as LangGraph-native generation nodes.

---

## LangChain Native Image Generation Integrations (2025–2026)

LangChain's image generation surface is narrower than its text model surface. There are two distinct integration patterns:

### Pattern A — Native LangChain Tools (langchain-community)

These have first-class `Tool` wrappers usable directly in LangGraph `ToolNode`.

| Tool Class | Package | Models | Status |
|------------|---------|--------|--------|
| `OpenAIDALLEImageGenerationTool` | `langchain-community` | `dall-e-2`, `dall-e-3` | Buggy — `quality` param throws 400 (open bug #183, #177 in langchain-community as of 2026-04). Do NOT use. |
| `DallEAPIWrapper` | `langchain-community` | `dall-e-2`, `dall-e-3` | Same wrapper, same bug. Deprecated by Pattern B. |

**DALL-E 2/3 are NOT the right models for this pipeline** — they are text-to-image only (no image input for transformation), and DALL-E 3 has known poor text-on-image performance. The `OpenAIDALLEImageGenerationTool` wrapper is broken as of early 2026.

### Pattern B — ChatOpenAI Responses API (langchain-openai >= 0.3.19)

The modern integration. Works with the OpenAI Responses API, not the Images API. Uses `bind_tools`.

```python
# Requires: pip install langchain-openai>=0.3.19
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o")  # or a Responses API-capable model
tool = {"type": "image_generation", "quality": "medium"}
llm_with_gen = llm.bind_tools([tool])

ai_message = llm_with_gen.invoke("Generate image: ...")
# Image returned in ai_message.content_blocks where block["type"] == "image"
```

**Limitation:** This generates images as part of a chat turn, not as a standalone `client.images.generate()` call. The model decides when to invoke generation. For a pipeline that needs guaranteed, direct generation from a reference image, the raw OpenAI SDK (`client.images.edit()`) is more reliable — see Pattern D below.

**gpt-image-1 via this pattern:** The `bind_tools` approach targets Responses API-capable chat models, not `gpt-image-1` directly. To use `gpt-image-1` for image editing (which is what ghost mannequin needs — transforming an input image), use Pattern D.

### Pattern C — ChatGoogleGenerativeAI Image Generation (langchain-google-genai)

**This is the right pattern for Gemini 2.5 Flash Image**, and it works natively today.

```python
# Requires: pip install langchain-google-genai
from langchain_google_genai import ChatGoogleGenerativeAI, Modality

model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-image",
    response_modalities=[Modality.IMAGE],  # image-only output
)

response = model.invoke("Transform this flat garment techflat into a ghost mannequin...")

# Extract image from response
def extract_image_b64(response) -> str:
    image_block = next(
        block for block in response.content
        if isinstance(block, dict) and block.get("image_url")
    )
    return image_block["image_url"]["url"].split(",")[-1]
```

Multi-image input (techflat + reference):
```python
from langchain_core.messages import HumanMessage
import base64

with open("techflat.png", "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()

response = model.invoke([
    HumanMessage(content=[
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
        {"type": "text", "text": "Transform this flat techflat into a ghost mannequin product shot..."}
    ])
])
```

**This is the production-ready pattern for the Elite Studio LangGraph node.**

### Pattern D — Direct SDK Calls Wrapped as Custom LangGraph Tools

For models without native LangChain integrations (GPT-Image-1 for editing, Ideogram v3, Recraft v3, fal.ai models), wrap the provider SDK in a `@tool` function. LangGraph nodes can call these directly — they don't need to be LangChain `Tool` instances to work as graph nodes.

```python
from langchain_core.tools import tool
from openai import OpenAI
import base64

openai_client = OpenAI()

@tool
def gpt_image_edit(source_image_path: str, prompt: str) -> str:
    """Transform a garment techflat into a ghost mannequin product shot using GPT-Image-1."""
    with open(source_image_path, "rb") as f:
        result = openai_client.images.edit(
            model="gpt-image-1",
            image=f,
            prompt=prompt,
            size="1024x1024",
            quality="medium",
        )
    # Returns base64 image data
    return result.data[0].b64_json
```

No official LangChain integration exists for: Ideogram v3, Recraft v3, fal.ai (FLUX Kontext, BRIA), Replicate. All require this custom-tool pattern. The LangChain forum has an open feature request for fal.ai integration (unresolved as of 2026-04).

---

## Model Ranking: Ghost Mannequin + Text Fidelity

### Ranked Comparison Table

| Rank | Model | Provider | LangChain Integration | Ghost Mannequin Quality | Text Fidelity (Jersey) | Cost/Image | Recommendation |
|------|-------|----------|-----------------------|------------------------|------------------------|------------|----------------|
| 1 | **Gemini 2.5 Flash Image** | Google AI / Gemini API | Native — `ChatGoogleGenerativeAI` (Pattern C) | HIGH — multi-image input, spatial 3D understanding, proven in nano-banana-vton.py | MEDIUM — known text iteration needed, "do not hallucinate" instruction required | $0.039 | **PRIMARY** |
| 2 | **GPT-Image-1** (medium quality) | OpenAI | Direct SDK only (Pattern D) — no native LangChain wrapper for `images.edit()` | HIGH — accepts input images via `images.edit()`, garment editing confirmed, jersey color/text editing tested | HIGH — LMArena #1 ranked Dec 2025, jersey text handling confirmed in Cybernews review | $0.042 | **FALLBACK #1 for jersey text** |
| 3 | **Ideogram v3** | Ideogram API / fal.ai | Custom tool only (Pattern D) via `fal_client` at `fal-ai/ideogram/v3` | MEDIUM — text-to-image primary, image editing support via Edit endpoint with mask | VERY HIGH — industry-leading 90-95% text accuracy, designed for text-in-image use case | $0.05 (via fal.ai) | **FALLBACK #2 for text-critical rescues** |
| 4 | **Recraft v3** | Recraft / fal.ai / Replicate | Custom tool only (Pattern D) | MEDIUM-HIGH — product photography trained, #1 Hugging Face leaderboard for 5+ months, but text-to-image only (no image input transform) | VERY HIGH — only model capable of long text, precise text positioning | $0.04 (fal.ai raster) | **SKIP for ghost mannequin** — no image-to-image transform; useful only if generating from scratch without techflat reference |
| 5 | **GPT-Image-1.5** | OpenAI | Direct SDK only (Pattern D) | HIGH — 4x faster than gpt-image-1, 20% cheaper, same editing API | HIGH — inherits gpt-image-1 text capabilities | ~$0.034 (estimated, 20% less than gpt-image-1) | **ALTERNATE PRIMARY** if cost is priority over model maturity |
| 6 | **FLUX.1 Kontext [pro]** | Black Forest Labs / fal.ai | Custom tool (Pattern D) via `fal_client` at `fal-ai/flux-pro/kontext` | MEDIUM — instruction-based local edits, not full transformation | LOW — not designed for text preservation | $0.04 | **EXISTING FALLBACK** (keep as collar inpaint only, not generation primary) |
| 7 | **Stable Diffusion 3.5** | Stability AI / HuggingFace | Via `langchain-community` Replicate integration or HuggingFace Hub | LOW-MEDIUM — no 3D spatial understanding for ghost mannequin | LOW — known poor text rendering in image generation | ~$0.03 (Replicate) | **SKIP** — no advantage over existing stack |
| 8 | **DALL-E 3** | OpenAI | `langchain-community` `OpenAIDALLEImageGenerationTool` (broken) | LOW — text-to-image only, no image input | LOW — known weak text rendering | $0.04–$0.08 | **SKIP** — broken LangChain wrapper, no image-to-image |

---

## Detailed Assessments

### Gemini 2.5 Flash Image — PRIMARY (stay the course)

**Strengths:**
- Multi-image input supports techflat + brand reference in a single call
- Spatial 3D understanding verified for garment reconstruction
- Already integrated in `nano-banana-vton.py` — zero new auth, zero new dependencies
- `ChatGoogleGenerativeAI` with `response_modalities=[Modality.IMAGE]` is the cleanest LangChain native pattern
- $0.039/image — cheapest viable option

**Weaknesses:**
- Text rendering "not expected to be perfect on first try" (Google's own docs)
- Complex jersey text (multi-line, alternating fills) needs explicit "preserve text exactly" prompt instructions
- Back-of-jersey shots are less reliable than fronts

**Verdict for this pipeline:** Stays as primary. The prompt engineering additions in STACK.md (`CRITICAL: Preserve all jersey text...`) are the right mitigation. For back-of-jersey with complex alternating number fills, route to GPT-Image-1 fallback automatically.

---

### GPT-Image-1 — FALLBACK #1 (add for jersey text)

**Strengths:**
- `client.images.edit()` accepts up to 10 input images — techflat as edit target
- LMArena human preference #1 ranking (Text-to-Image) as of December 2025
- Cybernews review confirmed jersey text handling: "inserting the text in the right context and with consistent font"
- Strong prompt adherence for small details (garment features, stitching)

**Weaknesses:**
- No native LangChain tool — requires direct OpenAI SDK via custom `@tool`
- Requires org verification before first use
- Medium quality ($0.042) is the right tier — low quality ($0.011) is too compressed, high quality ($0.167) is overkill for product catalog batch
- The Responses API `bind_tools` pattern (Pattern B) does NOT work here — must use `client.images.edit()` directly

**How to call in LangGraph node:**
```python
from openai import OpenAI
openai_client = OpenAI()

def generate_ghost_mannequin_node(state: GraphState) -> GraphState:
    source = state["source_image_path"]
    prompt = build_ghost_mannequin_prompt(state["sku"], state["garment_type"])
    
    with open(source, "rb") as f:
        result = openai_client.images.edit(
            model="gpt-image-1",
            image=f,
            prompt=prompt,
            size="1024x1024",
            quality="medium",
        )
    return {**state, "generated_image_b64": result.data[0].b64_json}
```

**Routing logic:** Route to this fallback when:
1. Gemini QA gate rejects for text hallucination
2. SKU is a jersey with back-of-garment text (auto-detect from `garment_type == "jersey"` and `view == "back"`)

---

### Ideogram v3 — FALLBACK #2 (text rescue only)

**Strengths:**
- 90-95% text accuracy — industry-leading, designed specifically for text-in-image
- Supports mask-based editing via Edit endpoint (`fal-ai/ideogram/v3/edit`)
- Available via `fal_client` — same library already in `.venv/`

**Weaknesses:**
- More expensive than Gemini ($0.05 vs $0.039)
- Text-heavy specialization means less focus on 3D garment spatial understanding
- Edit endpoint is mask-based — need to compute a text-region mask, adding complexity
- No direct LangChain integration; custom `fal_client` wrapper required

**Use case:** Jersey back shots where both Gemini AND GPT-Image-1 fail text fidelity QA. This should be rare (< 5% of jobs).

---

### Recraft v3 — SKIP for this pipeline

Recraft v3 excels at text rendering and product design but is fundamentally a text-to-image model. It cannot take a techflat as an input reference and transform it. The ghost mannequin pipeline requires image-to-image: the techflat IS the source. Recraft v3 would generate a generic jersey, not the specific SkyyRose product. Skip it.

If a future need arises for generating conceptual product mockups without techflat references, Recraft v3 at $0.04/image (fal.ai) is worth evaluating.

---

### Stable Diffusion 3.5 — SKIP

Available via LangChain through `langchain-community` Replicate integration or HuggingFace Hub, but:
- No 3D spatial understanding for ghost mannequin transformation
- Known poor text rendering on fabric (a long-standing SD weakness)
- Requires prompt engineering expertise that Gemini/GPT-Image handles automatically
- No marginal cost advantage over Gemini

---

## LangGraph Node Pattern — Production Implementation

### State Schema

```python
from typing import TypedDict, Optional, Literal

class GhostMannequinState(TypedDict):
    sku: str
    garment_type: str          # "jersey" | "tshirt" | "hoodie" | etc.
    view: str                  # "front" | "back"
    source_image_path: str
    generated_image_b64: Optional[str]
    qa_result: Optional[dict]
    provider_used: Optional[str]
    retry_count: int
    error: Optional[str]
```

### Primary Node (Gemini)

```python
from langchain_google_genai import ChatGoogleGenerativeAI, Modality
from langchain_core.messages import HumanMessage
import base64

_gemini_model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash-image",
    response_modalities=[Modality.IMAGE],
)

def gemini_generation_node(state: GhostMannequinState) -> GhostMannequinState:
    prompt = _build_prompt(state)
    
    with open(state["source_image_path"], "rb") as f:
        img_b64 = base64.b64encode(f.read()).decode()
    
    ext = state["source_image_path"].rsplit(".", 1)[-1].lower()
    mime = "image/png" if ext == "png" else "image/jpeg"
    
    response = _gemini_model.invoke([
        HumanMessage(content=[
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{img_b64}"}},
            {"type": "text", "text": prompt},
        ])
    ])
    
    image_block = next(
        (b for b in response.content if isinstance(b, dict) and b.get("image_url")),
        None,
    )
    if not image_block:
        return {**state, "error": "gemini_no_image_output", "generated_image_b64": None}
    
    b64 = image_block["image_url"]["url"].split(",")[-1]
    return {**state, "generated_image_b64": b64, "provider_used": "gemini-2.5-flash-image", "error": None}
```

### Fallback Node (GPT-Image-1)

```python
from openai import OpenAI

_openai_client = OpenAI()

def gpt_image_generation_node(state: GhostMannequinState) -> GhostMannequinState:
    prompt = _build_prompt(state)
    
    with open(state["source_image_path"], "rb") as f:
        result = _openai_client.images.edit(
            model="gpt-image-1",
            image=f,
            prompt=prompt,
            size="1024x1024",
            quality="medium",
        )
    
    return {
        **state,
        "generated_image_b64": result.data[0].b64_json,
        "provider_used": "gpt-image-1",
        "error": None,
    }
```

### Router (Conditional Edge)

```python
def route_after_generation(state: GhostMannequinState) -> str:
    if state.get("error") or state.get("generated_image_b64") is None:
        if state["retry_count"] < 1:
            return "gpt_image_fallback"
        return "fail"
    return "qa_gate"

def route_after_qa(state: GhostMannequinState) -> str:
    qa = state.get("qa_result", {})
    if qa.get("passed"):
        return "post_process"
    
    # Text failure on jersey back → escalate to Ideogram
    if (
        state["garment_type"] == "jersey"
        and state["view"] == "back"
        and qa.get("failure_reason") == "text_hallucination"
        and state["provider_used"] != "ideogram-v3"
    ):
        return "ideogram_text_rescue"
    
    if state["retry_count"] < 2:
        return "gemini_generation" if state["retry_count"] == 0 else "gpt_image_fallback"
    
    return "fail"
```

### Graph Assembly

```python
from langgraph.graph import StateGraph, END

graph = StateGraph(GhostMannequinState)

graph.add_node("gemini_generation", gemini_generation_node)
graph.add_node("gpt_image_fallback", gpt_image_generation_node)
graph.add_node("ideogram_text_rescue", ideogram_generation_node)  # custom fal_client wrapper
graph.add_node("qa_gate", qa_gate_node)
graph.add_node("post_process", post_process_node)    # PIL composite on #FFFFFF
graph.add_node("fail", fail_node)

graph.set_entry_point("gemini_generation")

graph.add_conditional_edges("gemini_generation", route_after_generation, {
    "qa_gate": "qa_gate",
    "gpt_image_fallback": "gpt_image_fallback",
    "fail": "fail",
})
graph.add_conditional_edges("gpt_image_fallback", route_after_generation, {
    "qa_gate": "qa_gate",
    "fail": "fail",
})
graph.add_conditional_edges("qa_gate", route_after_qa, {
    "post_process": "post_process",
    "gemini_generation": "gemini_generation",
    "gpt_image_fallback": "gpt_image_fallback",
    "ideogram_text_rescue": "ideogram_text_rescue",
    "fail": "fail",
})
graph.add_edge("ideogram_text_rescue", "qa_gate")
graph.add_edge("post_process", END)
graph.add_edge("fail", END)

app = graph.compile()
```

---

## Routing Decision Matrix (Operational)

| Trigger | Route To | Why |
|---------|----------|-----|
| Normal run, any garment | Gemini 2.5 Flash Image | Cheapest, fastest, proven |
| Gemini output: no image returned / API error | GPT-Image-1 (medium) | Hard fallback |
| QA fail: text_hallucination, jersey back | Ideogram v3 (text rescue) | Best text accuracy |
| QA fail: background not white | Post-process (PIL) | PIL composite handles this |
| QA fail: mannequin visible / flat appearance | Retry Gemini with stronger prompt | Prompt engineering fix first |
| 2+ QA fails, any reason | Fail → review queue | Log SKU, manual review |

---

## Installation Requirements

All primary path dependencies already exist in `.venv/`. Two additions for fallbacks:

```bash
# Already in .venv/ (no action):
# google-genai (or langchain-google-genai for ChatGoogleGenerativeAI pattern)
# fal_client
# openai
# Pillow

# Add for LangChain native pattern (if not already installed):
pip install "langchain-google-genai>=2.0.0" "langchain-openai>=0.3.19"

# langchain-google-genai wraps google-genai — check if both are needed
# or if direct google-genai SDK (already in .venv/) is sufficient for the node
```

**Note:** `ChatGoogleGenerativeAI` from `langchain-google-genai` vs. `google.genai.Client` directly both work for this pipeline. If the goal is maximum LangGraph integration (checkpointing, streaming, LangSmith tracing), use `langchain-google-genai`. If minimizing dependencies, the direct `google.genai.Client` approach already in `config.py` (`GENERATION_MODEL = "gemini-3-pro-image-preview"`) is equivalent — just wrap it in a node function without the LangChain layer.

---

## Cost Impact of Adding Fallbacks

| Scenario | Cost per image | Frequency estimate | Added cost per 30-product batch |
|----------|----------------|-------------------|----------------------------------|
| Gemini primary (all pass) | $0.039 | 85% | $0.99 |
| GPT-Image-1 fallback (medium) | $0.042 | 10% | +$0.13 |
| Ideogram v3 text rescue | $0.050 | 5% | +$0.075 |
| **Total batch estimate** | | | **~$1.20** |

This is actually cheaper than the Stage 2b FLUX Fill Pro collar fallback estimate in STACK.md ($0–$0.40), because GPT-Image-1 handles the full image not just collar inpainting. FLUX Fill Pro should still be used for collar-region-specific inpainting (sub-task, not full regeneration).

---

## What NOT to Change

| Current config | Verdict | Reason |
|----------------|---------|--------|
| `GENERATION_MODEL = "gemini-3-pro-image-preview"` in `config.py` | Keep for compositor | This is the compositor agent — different pipeline, higher quality needed |
| `gemini-2.5-flash-image` in STACK.md | Keep as primary for ghost mannequin batch | Correct choice |
| FLUX Kontext as collar fallback | Keep | Still the right tool for surgical collar/neck inpainting |
| BRIA RMBG 2.0 at Stage 1 | Keep | No LangChain alternative is better |

The model referenced in `config.py` as `GENERATION_MODEL = "gemini-3-pro-image-preview"` is the compositor pipeline's generation model (scene compositing for editorial images). The ghost mannequin pipeline is a separate workflow and should use `gemini-2.5-flash-image` as documented in STACK.md.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| LangChain integration patterns | HIGH | Verified via official docs: ChatGoogleGenerativeAI image gen, ChatOpenAI bind_tools, direct SDK |
| Gemini 2.5 Flash Image for ghost mannequin | HIGH | Proven in existing pipeline (nano-banana-vton.py) |
| GPT-Image-1 text fidelity | HIGH | LMArena rank #1, jersey text test confirmed (Cybernews review) |
| Ideogram v3 text accuracy | HIGH | 90-95% per official claims, multiple sources confirm industry-leading text |
| Recraft v3 ghost mannequin | HIGH (for skip) | Confirmed text-to-image only — no image input transform |
| Cost figures | MEDIUM | Gemini/OpenAI from official pricing; Ideogram via fal.ai (third-party) |
| ghost-mannequin-specific benchmark data | LOW | No published benchmarks for ghost mannequin by model — all assessments derived from general quality rankings and text rendering benchmarks |

---

## Sources

- [LangChain DALL-E tool docs](https://docs.langchain.com/oss/python/integrations/tools/dalle_image_generator)
- [langchain-community DallEAPIWrapper bug #183](https://github.com/langchain-ai/langchain-community/issues/183)
- [ChatOpenAI image generation via Responses API](https://docs.langchain.com/oss/python/integrations/chat/openai)
- [ChatGoogleGenerativeAI image generation](https://docs.langchain.com/oss/python/integrations/chat/google_generative_ai)
- [OpenAI GPT-Image-1 images.edit API](https://developers.openai.com/cookbook/examples/generate_images_with_gpt_image)
- [OpenAI GPT Image 1.5 review — jersey text test](https://cybernews.com/ai-tools/gpt-image-1-5-review/)
- [Ideogram v3 release and text accuracy (90-95%)](https://ideogram.ai/features/3.0)
- [Ideogram v3 API docs](https://developer.ideogram.ai/ideogram-api/api-overview)
- [Ideogram v3 on fal.ai](https://fal.ai/models/fal-ai/ideogram/v3)
- [Recraft v3 docs](https://www.recraft.ai/docs/recraft-models/recraft-V3)
- [Recraft v3 on fal.ai — $0.04/image](https://fal.ai/models/fal-ai/recraft/v3/text-to-image)
- [AI Image pricing comparison 2026 (GPT vs Gemini)](https://intuitionlabs.ai/articles/ai-image-generation-pricing-google-openai)
- [Artificial Analysis Text-to-Image Leaderboard](https://artificialanalysis.ai/image/leaderboard/text-to-image)
- [fal.ai LangGraph integration feature request](https://forum.langchain.com/t/feature-request-add-integration-for-fal-ai-image-generation/1451)
- [Gemini 2.5 Flash Image prompting guide](https://developers.googleblog.com/en/how-to-prompt-gemini-2-5-flash-image-generation-for-the-best-results/)
- [Gemini image generation docs (response_modalities)](https://ai.google.dev/gemini-api/docs/image-generation)

---
*Research completed: 2026-04-22 | Milestone: v1.2 Ghost Mannequin Pipeline*
