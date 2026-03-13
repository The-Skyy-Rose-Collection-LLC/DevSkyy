#!/usr/bin/env python3
"""
LLM Landscape Benchmark Chart — SkyyRose Pipeline
===================================================

Generates comparison charts for:
  1. Text/Language LLMs  — Reasoning, Coding, Science, Speed, Cost
  2. Image Generation    — Photorealism, Text Rendering, Artistic, Prompt Adherence, Fashion

Data sources (March 2026):
  - GPQA Diamond:    https://pricepertoken.com/leaderboards/benchmark/gpqa
  - SWE-bench:       https://klu.ai/llm-leaderboard
  - Intelligence:    https://lmcouncil.ai/benchmarks
  - Image gen:       https://medium.com/@cliprise/ai-image-generation-in-2026 (consensus)
  - Cost/Speed:      https://artificialanalysis.ai/models

Usage:
    python scripts/llm_benchmark_chart.py
    python scripts/llm_benchmark_chart.py --text-only
    python scripts/llm_benchmark_chart.py --image-only
    python scripts/llm_benchmark_chart.py --pipeline    # annotate your pipeline's routing
    python scripts/llm_benchmark_chart.py --out /path/to/dir
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

try:
    import matplotlib
    import matplotlib.patches as mpatches
    import matplotlib.pyplot as plt
    import numpy as np
except ImportError:
    print("Missing deps. Run: pip install matplotlib numpy", file=sys.stderr)
    sys.exit(1)

matplotlib.use("Agg")  # headless / file output

# ── Brand palette ──────────────────────────────────────────────────────────────
DARK_BG = "#0A0A0A"
CARD_BG = "#141414"
GRID_COLOR = "#2A2A2A"
TEXT_COLOR = "#E8E8E8"
ROSE_GOLD = "#B76E79"
GOLD = "#D4AF37"
SILVER = "#C0C0C0"

# ── Text / Language LLM data ───────────────────────────────────────────────────
# Scores are 0-100 scale. Benchmark sources cited in module docstring.
# "?" dimensions are excluded from that model's radar fill (plotted as 0).

TEXT_MODELS = [
    {
        "label": "GPT-5.4",
        "provider": "OpenAI",
        "color": "#74AA9C",
        # GPQA Diamond 92.0%, SWE-bench ~80%, HLE estimated 72%, speed moderate, cost high
        "scores": {
            "Reasoning\n(GPQA)": 92.0,
            "Coding\n(SWE-bench)": 80.0,
            "Science\n(HLE)": 72.0,
            "Vision\n(MMMU)": 85.0,
            "Speed\n(normalized)": 62.0,
            "Cost\nEfficiency": 30.0,  # expensive — inverted: lower cost → higher bar
        },
    },
    {
        "label": "GPT-5.3 Codex",
        "provider": "OpenAI",
        "color": "#5B8FA8",
        "scores": {
            "Reasoning\n(GPQA)": 91.5,
            "Coding\n(SWE-bench)": 80.0,
            "Science\n(HLE)": 68.0,
            "Vision\n(MMMU)": 82.0,
            "Speed\n(normalized)": 58.0,
            "Cost\nEfficiency": 28.0,
        },
    },
    {
        "label": "Gemini 3.1 Pro",
        "provider": "Google",
        "color": "#4285F4",
        "scores": {
            "Reasoning\n(GPQA)": 90.8,
            "Coding\n(SWE-bench)": 68.0,
            "Science\n(HLE)": 74.2,  # Humanity's Last Exam — highest of any model
            "Vision\n(MMMU)": 88.0,
            "Speed\n(normalized)": 55.0,
            "Cost\nEfficiency": 45.0,
        },
    },
    {
        "label": "Claude Sonnet 4.6",
        "provider": "Anthropic",
        "color": ROSE_GOLD,
        "scores": {
            "Reasoning\n(GPQA)": 83.8,
            "Coding\n(SWE-bench)": 79.6,
            "Science\n(HLE)": 60.0,
            "Vision\n(MMMU)": 80.0,
            "Speed\n(normalized)": 72.0,
            "Cost\nEfficiency": 65.0,  # balanced cost
        },
    },
    {
        "label": "Claude Opus 4.6",
        "provider": "Anthropic",
        "color": "#DC143C",
        "scores": {
            "Reasoning\n(GPQA)": 83.3,
            "Coding\n(SWE-bench)": 80.8,  # highest SWE-bench of any model
            "Science\n(HLE)": 62.0,
            "Vision\n(MMMU)": 79.0,
            "Speed\n(normalized)": 48.0,
            "Cost\nEfficiency": 35.0,
        },
    },
    {
        "label": "Gemini 2.5 Pro",
        "provider": "Google",
        "color": "#34A853",
        "scores": {
            "Reasoning\n(GPQA)": 83.0,
            "Coding\n(SWE-bench)": 63.8,
            "Science\n(HLE)": 55.0,
            "Vision\n(MMMU)": 84.0,
            "Speed\n(normalized)": 68.0,
            "Cost\nEfficiency": 55.0,
        },
    },
    {
        "label": "DeepSeek V3.1",
        "provider": "DeepSeek",
        "color": "#FBBC04",
        "scores": {
            "Reasoning\n(GPQA)": 75.0,
            "Coding\n(SWE-bench)": 66.0,
            "Science\n(HLE)": 50.0,
            "Vision\n(MMMU)": 70.0,
            "Speed\n(normalized)": 85.0,  # fast open-weight
            "Cost\nEfficiency": 90.0,  # very cheap
        },
    },
    {
        "label": "Gemini 2.5 Flash",
        "provider": "Google",
        "color": "#00B1BF",
        "scores": {
            "Reasoning\n(GPQA)": 75.0,
            "Coding\n(SWE-bench)": 55.0,
            "Science\n(HLE)": 48.0,
            "Vision\n(MMMU)": 80.0,
            "Speed\n(normalized)": 92.0,  # fastest in the Gemini family
            "Cost\nEfficiency": 88.0,  # very affordable
        },
    },
]

# ── Image Generation data ──────────────────────────────────────────────────────
# Qualitative consensus from March 2026 reviews + LM Arena rankings.
# Scale: 0-100 per dimension.

IMAGE_MODELS = [
    {
        "label": "FLUX.2 Pro",
        "provider": "Black Forest Labs",
        "color": "#FF6B35",
        "scores": {
            "Photorealism": 96,
            "Text Rendering": 62,
            "Artistic Quality": 80,
            "Prompt Adherence": 84,
            "Fashion / Product": 90,
            "Speed": 82,
        },
    },
    {
        "label": "Imagen 4 Ultra",
        "provider": "Google",
        "color": "#4285F4",
        "scores": {
            "Photorealism": 89,
            "Text Rendering": 97,  # best text rendering (jerseys, typography)
            "Artistic Quality": 74,
            "Prompt Adherence": 88,
            "Fashion / Product": 93,  # best product photography
            "Speed": 58,
        },
    },
    {
        "label": "GPT-Image-1.5",
        "provider": "OpenAI",
        "color": "#74AA9C",
        "scores": {
            "Photorealism": 91,
            "Text Rendering": 88,
            "Artistic Quality": 76,
            "Prompt Adherence": 96,  # #1 on LM Arena for prompt adherence
            "Fashion / Product": 86,
            "Speed": 65,
        },
    },
    {
        "label": "Midjourney v7",
        "provider": "Midjourney",
        "color": "#9B59B6",
        "scores": {
            "Photorealism": 86,
            "Text Rendering": 64,
            "Artistic Quality": 99,  # unmatched aesthetic quality
            "Prompt Adherence": 76,
            "Fashion / Product": 84,
            "Speed": 70,
        },
    },
    {
        "label": "Gemini Flash Image",
        "provider": "Google",
        "color": ROSE_GOLD,
        "scores": {
            "Photorealism": 80,
            "Text Rendering": 70,
            "Artistic Quality": 74,
            "Prompt Adherence": 81,
            "Fashion / Product": 79,
            "Speed": 94,  # fastest of the group
        },
    },
]


# ── Chart helpers ──────────────────────────────────────────────────────────────


def _apply_dark_theme(fig: plt.Figure) -> None:
    fig.patch.set_facecolor(DARK_BG)


def _dark_ax(ax: plt.Axes) -> None:
    ax.set_facecolor(CARD_BG)
    ax.tick_params(colors=TEXT_COLOR, labelsize=8)
    ax.xaxis.label.set_color(TEXT_COLOR)
    ax.yaxis.label.set_color(TEXT_COLOR)
    ax.title.set_color(TEXT_COLOR)
    for spine in ax.spines.values():
        spine.set_edgecolor(GRID_COLOR)
    ax.yaxis.grid(True, color=GRID_COLOR, linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)


# ── Chart 1: Text LLM grouped bar chart ────────────────────────────────────────


def plot_text_llms(out_path: Path, annotate_pipeline: bool = False) -> None:
    dimensions = list(TEXT_MODELS[0]["scores"].keys())
    n_dims = len(dimensions)
    n_models = len(TEXT_MODELS)

    bar_width = 0.10
    group_gap = 0.15
    group_width = n_models * bar_width + group_gap
    x_centers = np.arange(n_dims) * group_width

    fig, ax = plt.subplots(figsize=(16, 7))
    _apply_dark_theme(fig)
    _dark_ax(ax)

    for i, model in enumerate(TEXT_MODELS):
        scores = [model["scores"][d] for d in dimensions]
        offsets = x_centers + (i - n_models / 2 + 0.5) * bar_width
        bars = ax.bar(
            offsets,
            scores,
            width=bar_width * 0.88,
            color=model["color"],
            alpha=0.88,
            zorder=3,
        )
        # Value labels on tallest bars
        for bar, score in zip(bars, scores, strict=False):
            if score >= 70:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.8,
                    f"{score:.0f}",
                    ha="center",
                    va="bottom",
                    fontsize=5.5,
                    color=model["color"],
                    fontweight="bold",
                )

    # Pipeline annotations
    if annotate_pipeline:
        pipeline_notes = {
            "Reasoning\n(GPQA)": "Orchestration\n(Claude Opus 4.6)",
            "Coding\n(SWE-bench)": "Code Gen\n(Claude Opus 4.6)",
            "Vision\n(MMMU)": "QC Gate\n(Claude Sonnet 4.6)",
            "Speed\n(normalized)": "Vision Batch\n(Gemini 2.5 Flash)",
            "Cost\nEfficiency": "Bulk tasks\n(Gemini Flash)",
        }
        for dim, note in pipeline_notes.items():
            if dim in dimensions:
                idx = dimensions.index(dim)
                ax.annotate(
                    note,
                    xy=(x_centers[idx], 102),
                    xytext=(x_centers[idx], 108),
                    ha="center",
                    fontsize=5.5,
                    color=ROSE_GOLD,
                    arrowprops={"arrowstyle": "->", "color": ROSE_GOLD, "lw": 0.8},
                )

    ax.set_xticks(x_centers)
    ax.set_xticklabels(dimensions, fontsize=9, color=TEXT_COLOR)
    ax.set_ylim(0, 118 if annotate_pipeline else 105)
    ax.set_ylabel("Score (0-100)", color=TEXT_COLOR, fontsize=9)
    ax.set_title(
        "Text / Language LLM Benchmark Landscape  ·  March 2026",
        color=TEXT_COLOR,
        fontsize=13,
        fontweight="bold",
        pad=14,
    )

    # Legend
    handles = [
        mpatches.Patch(color=m["color"], label=f"{m['label']}  ({m['provider']})")
        for m in TEXT_MODELS
    ]
    ax.legend(
        handles=handles,
        loc="upper right",
        fontsize=7.5,
        facecolor=CARD_BG,
        edgecolor=GRID_COLOR,
        labelcolor=TEXT_COLOR,
        ncol=2,
    )

    # Source note
    fig.text(
        0.01,
        0.01,
        "Sources: GPQA — pricepertoken.com/leaderboards/benchmark/gpqa  |  "
        "SWE-bench — klu.ai/llm-leaderboard  |  HLE — lmcouncil.ai/benchmarks  |  "
        "Cost/Speed — artificialanalysis.ai",
        fontsize=5,
        color="#555555",
        ha="left",
    )

    plt.tight_layout(rect=[0, 0.03, 1, 1])
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close(fig)
    print(f"  Saved: {out_path}")


# ── Chart 2: Image generation radar ────────────────────────────────────────────


def plot_image_models_radar(out_path: Path, annotate_pipeline: bool = False) -> None:
    dimensions = list(IMAGE_MODELS[0]["scores"].keys())
    n_dims = len(dimensions)

    angles = [n / n_dims * 2 * math.pi for n in range(n_dims)]
    angles += angles[:1]  # close the polygon

    fig, ax = plt.subplots(figsize=(10, 9), subplot_kw={"polar": True})
    _apply_dark_theme(fig)

    ax.set_facecolor(CARD_BG)
    ax.set_theta_offset(math.pi / 2)
    ax.set_theta_direction(-1)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(dimensions, size=9, color=TEXT_COLOR)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.set_yticklabels(["20", "40", "60", "80", "100"], size=6, color="#555555")
    ax.grid(color=GRID_COLOR, linewidth=0.6, alpha=0.7)
    ax.spines["polar"].set_color(GRID_COLOR)

    for model in IMAGE_MODELS:
        values = [model["scores"][d] for d in dimensions]
        values += values[:1]

        # Pipeline highlight: thicker line for Gemini (in current pipeline)
        lw = 3.0 if (annotate_pipeline and model["label"] == "Gemini Flash Image") else 1.6
        alpha = 0.85 if (annotate_pipeline and model["label"] == "Gemini Flash Image") else 0.70

        ax.plot(angles, values, color=model["color"], linewidth=lw, linestyle="solid")
        ax.fill(angles, values, color=model["color"], alpha=0.12)

        # Label the peak dimension
        peak_idx = values[:-1].index(max(values[:-1]))
        ax.annotate(
            model["label"],
            xy=(angles[peak_idx], values[peak_idx]),
            xytext=(angles[peak_idx], min(values[peak_idx] + 8, 100)),
            fontsize=6.5,
            color=model["color"],
            ha="center",
            fontweight="bold",
        )

    # Pipeline annotation
    if annotate_pipeline:
        ax.set_title(
            "Image Generation Models  ·  March 2026\n"
            "(bold ring = currently used in SkyyRose pipeline)",
            color=TEXT_COLOR,
            fontsize=12,
            fontweight="bold",
            pad=20,
        )
    else:
        ax.set_title(
            "Image Generation Models  ·  March 2026",
            color=TEXT_COLOR,
            fontsize=12,
            fontweight="bold",
            pad=20,
        )

    handles = [
        mpatches.Patch(color=m["color"], label=f"{m['label']}  ({m['provider']})")
        for m in IMAGE_MODELS
    ]
    ax.legend(
        handles=handles,
        loc="lower left",
        bbox_to_anchor=(-0.15, -0.12),
        fontsize=8,
        facecolor=CARD_BG,
        edgecolor=GRID_COLOR,
        labelcolor=TEXT_COLOR,
    )

    fig.text(
        0.01,
        0.01,
        "Sources: Image gen consensus — medium.com/@cliprise / wavespeed.ai/blog / awesomeagents.ai  |  "
        "LM Arena — lmcouncil.ai  |  Qualitative composite scores (0-100)",
        fontsize=5,
        color="#555555",
        ha="left",
    )

    plt.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close(fig)
    print(f"  Saved: {out_path}")


# ── Chart 3: Image generation bar chart (easier to read side-by-side) ──────────


def plot_image_models_bar(out_path: Path) -> None:
    dimensions = list(IMAGE_MODELS[0]["scores"].keys())
    n_dims = len(dimensions)
    n_models = len(IMAGE_MODELS)

    bar_width = 0.14
    group_gap = 0.18
    group_width = n_models * bar_width + group_gap
    x_centers = np.arange(n_dims) * group_width

    fig, ax = plt.subplots(figsize=(14, 6))
    _apply_dark_theme(fig)
    _dark_ax(ax)

    for i, model in enumerate(IMAGE_MODELS):
        scores = [model["scores"][d] for d in dimensions]
        offsets = x_centers + (i - n_models / 2 + 0.5) * bar_width
        bars = ax.bar(
            offsets,
            scores,
            width=bar_width * 0.88,
            color=model["color"],
            alpha=0.88,
            zorder=3,
        )
        for bar, score in zip(bars, scores, strict=False):
            if score >= 85:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.5,
                    f"{score}",
                    ha="center",
                    va="bottom",
                    fontsize=6,
                    color=model["color"],
                    fontweight="bold",
                )

    ax.set_xticks(x_centers)
    ax.set_xticklabels(dimensions, fontsize=9.5, color=TEXT_COLOR)
    ax.set_ylim(0, 108)
    ax.set_ylabel("Score (0-100)", color=TEXT_COLOR, fontsize=9)
    ax.set_title(
        "Image Generation Model Comparison  ·  March 2026",
        color=TEXT_COLOR,
        fontsize=13,
        fontweight="bold",
        pad=12,
    )

    handles = [
        mpatches.Patch(color=m["color"], label=f"{m['label']}  ({m['provider']})")
        for m in IMAGE_MODELS
    ]
    ax.legend(
        handles=handles,
        loc="lower right",
        fontsize=8,
        facecolor=CARD_BG,
        edgecolor=GRID_COLOR,
        labelcolor=TEXT_COLOR,
    )

    # "Best for" annotations
    best_for = {
        "Photorealism": ("FLUX.2 Pro", "#FF6B35"),
        "Text Rendering": ("Imagen 4 Ultra", "#4285F4"),
        "Prompt Adherence": ("GPT-Image-1.5", "#74AA9C"),
        "Artistic Quality": ("Midjourney v7", "#9B59B6"),
        "Speed": ("Gemini Flash\nImage", ROSE_GOLD),
    }
    for dim, (winner, color) in best_for.items():
        if dim in dimensions:
            idx = dimensions.index(dim)
            ax.text(
                x_centers[idx],
                3,
                f"Best:\n{winner}",
                ha="center",
                va="bottom",
                fontsize=5.5,
                color=color,
                alpha=0.85,
            )

    fig.text(
        0.01,
        0.01,
        "Sources: Review consensus from wavespeed.ai, awesomeagents.ai, cliprise.app  |  "
        "Scores are qualitative composites from published reviews (not formal benchmarks)",
        fontsize=5,
        color="#555555",
        ha="left",
    )

    plt.tight_layout(rect=[0, 0.03, 1, 1])
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close(fig)
    print(f"  Saved: {out_path}")


# ── Chart 4: Combined summary heatmap ─────────────────────────────────────────


def plot_heatmap_summary(out_path: Path) -> None:
    """Single-page landscape summary — all models, all dims, color-coded."""
    all_models = TEXT_MODELS + IMAGE_MODELS
    labels = [m["label"] for m in all_models]
    all_dims = list(
        dict.fromkeys(
            list(TEXT_MODELS[0]["scores"].keys()) + list(IMAGE_MODELS[0]["scores"].keys())
        )
    )

    # Build matrix; NaN where model doesn't have that dimension
    matrix = np.full((len(all_models), len(all_dims)), np.nan)
    for i, model in enumerate(all_models):
        for j, dim in enumerate(all_dims):
            # Normalize dim key for lookup (strip newlines)
            clean_dim = dim.replace("\n", " ").strip()
            for k, v in model["scores"].items():
                if k.replace("\n", " ").strip() == clean_dim:
                    matrix[i, j] = v

    fig, ax = plt.subplots(figsize=(18, 8))
    _apply_dark_theme(fig)
    ax.set_facecolor(CARD_BG)

    # Plot heatmap manually with pcolormesh
    masked = np.ma.masked_invalid(matrix)
    cmap = matplotlib.colormaps.get_cmap("RdYlGn")
    cmap.set_bad(color="#1A1A1A")

    im = ax.imshow(masked, cmap=cmap, vmin=0, vmax=100, aspect="auto")

    # Annotate cells
    for i in range(len(all_models)):
        for j in range(len(all_dims)):
            val = matrix[i, j]
            if not np.isnan(val):
                color = "black" if 35 < val < 80 else TEXT_COLOR
                ax.text(
                    j,
                    i,
                    f"{val:.0f}",
                    ha="center",
                    va="center",
                    fontsize=7.5,
                    color=color,
                    fontweight="bold",
                )

    ax.set_xticks(range(len(all_dims)))
    ax.set_xticklabels(
        [d.replace("\n", " ") for d in all_dims],
        fontsize=8,
        color=TEXT_COLOR,
        rotation=22,
        ha="right",
    )
    ax.set_yticks(range(len(all_models)))
    ax.set_yticklabels(labels, fontsize=8.5, color=TEXT_COLOR)

    # Separator line between text and image models
    sep_y = len(TEXT_MODELS) - 0.5
    ax.axhline(sep_y, color=ROSE_GOLD, linewidth=1.5, alpha=0.8)
    ax.text(
        len(all_dims) - 0.4,
        sep_y - len(TEXT_MODELS) / 2,
        "TEXT\nLLMs",
        color=ROSE_GOLD,
        fontsize=7,
        ha="left",
        va="center",
        alpha=0.7,
    )
    ax.text(
        len(all_dims) - 0.4,
        sep_y + len(IMAGE_MODELS) / 2,
        "IMAGE\nGEN",
        color=GOLD,
        fontsize=7,
        ha="left",
        va="center",
        alpha=0.7,
    )

    cbar = plt.colorbar(im, ax=ax, fraction=0.018, pad=0.12)
    cbar.ax.tick_params(colors=TEXT_COLOR, labelsize=7)
    cbar.set_label("Score (0-100)", color=TEXT_COLOR, fontsize=8)

    ax.set_title(
        "Full LLM Landscape — Text & Image Models  ·  March 2026",
        color=TEXT_COLOR,
        fontsize=13,
        fontweight="bold",
        pad=12,
    )

    fig.text(
        0.01,
        0.005,
        "Text LLMs: GPQA/SWE-bench from verified benchmarks  |  "
        "Image Gen: qualitative composite from 2026 review consensus  |  "
        "Grey cells = dimension not applicable for that model type",
        fontsize=5.5,
        color="#555555",
        ha="left",
    )

    plt.tight_layout(rect=[0, 0.02, 0.97, 1])
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=DARK_BG)
    plt.close(fig)
    print(f"  Saved: {out_path}")


# ── Main ────────────────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="LLM landscape benchmark charts")
    parser.add_argument("--text-only", action="store_true", help="Only generate text LLM chart")
    parser.add_argument("--image-only", action="store_true", help="Only generate image gen charts")
    parser.add_argument(
        "--pipeline", action="store_true", help="Annotate with SkyyRose pipeline routing"
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(__file__).parent.parent / ".devskyy" / "benchmark",
        help="Output directory (default: .devskyy/benchmark/)",
    )
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)

    print("\nLLM Landscape Benchmark Chart Generator — March 2026")
    print(f"Output: {args.out}\n")

    if not args.image_only:
        print("Generating text LLM chart...")
        plot_text_llms(args.out / "llm-text-landscape.png", annotate_pipeline=args.pipeline)

    if not args.text_only:
        print("Generating image gen radar chart...")
        plot_image_models_radar(args.out / "llm-image-radar.png", annotate_pipeline=args.pipeline)
        print("Generating image gen bar chart...")
        plot_image_models_bar(args.out / "llm-image-bar.png")

    print("Generating full heatmap summary...")
    plot_heatmap_summary(args.out / "llm-full-heatmap.png")

    print(f"\nDone. 4 charts saved to {args.out}/")
    if args.pipeline:
        print(
            "\nPipeline routing highlighted:\n"
            "  Vision/Garment Analysis  → Gemini 2.5 Flash  (speed + cost)\n"
            "  Text-Heavy Jerseys       → Imagen 4 Ultra     (best text rendering)\n"
            "  Tech Flat → Photorealistic → FLUX.2 Pro       (best photorealism)\n"
            "  Default Image Gen        → Gemini Flash Image (speed + cost)\n"
            "  Orchestration / Agents   → Claude Opus 4.6   (best coding + reasoning)\n"
            "  QC / Quality Gate        → Claude Sonnet 4.6 (balanced, fast)\n"
        )


if __name__ == "__main__":
    main()
