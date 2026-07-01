"""Command-line interface for the PNG-to-font generator.

Two subcommands:
  template  -- generate a blank fill-in template PNG + manifest.json
  build     -- vectorize a filled-in scan against a manifest into a .ttf font

Usage:
  python -m scripts.font_generator.cli template --out DIR [--chars STR] [--cols N] \
      [--cell-width W --cell-height H]
  python -m scripts.font_generator.cli build --filled PATH --manifest PATH --out FONT.ttf \
      [--family NAME] [--style NAME] [--threshold N]
"""

from __future__ import annotations

import argparse
import sys

from scripts.font_generator import pipeline, template

# The filled-in scan submitted to `build` MUST have the exact same pixel
# dimensions as the template PNG produced by `template` -- pipeline.build_font
# hard-fails (ValueError) on any mismatch, no silent resize.
DIMENSION_WARNING = (
    "IMPORTANT: the filled-in scan/photo you submit to 'build' MUST have the "
    "exact same pixel dimensions as the generated template.png. Do not crop, "
    "resize, or re-export at a different resolution -- the manifest's pixel "
    "bounding boxes only line up at the original size."
)


def _add_template_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "template",
        help="Generate a blank fill-in template PNG and manifest.json",
        description=(
            "Generate a blank, hand-fillable character template PNG plus its "
            f"manifest.json describing cell layout. {DIMENSION_WARNING}"
        ),
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output directory for template.png and manifest.json (created if missing)",
    )
    parser.add_argument(
        "--chars",
        default=template.DEFAULT_CHARS,
        help="Characters to lay out in the template (default: A-Z, a-z, 0-9, .,!?'-)",
    )
    parser.add_argument(
        "--cols",
        type=int,
        default=10,
        help="Number of grid columns (default: 10)",
    )
    parser.add_argument(
        "--cell-width",
        type=int,
        default=240,
        help="Cell width in pixels (default: 240)",
    )
    parser.add_argument(
        "--cell-height",
        type=int,
        default=240,
        help="Cell height in pixels (default: 240)",
    )
    parser.set_defaults(func=_run_template)


def _add_build_parser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "build",
        help="Vectorize a filled-in template scan into a .ttf font",
        description=(
            "Build a .ttf font from a filled-in template scan and its "
            f"manifest.json. {DIMENSION_WARNING}"
        ),
    )
    parser.add_argument(
        "--filled",
        required=True,
        help="Path to the filled-in template image (must match template.png pixel dimensions)",
    )
    parser.add_argument(
        "--manifest",
        required=True,
        help="Path to manifest.json produced by the 'template' subcommand",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output path for the generated .ttf font",
    )
    parser.add_argument(
        "--family",
        default="MyFont",
        help="Font family name (default: MyFont)",
    )
    parser.add_argument(
        "--style",
        default="Regular",
        help="Font style name (default: Regular)",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=140,
        help="Grayscale ink threshold, 0-255; pixels darker than this count as ink (default: 140)",
    )
    parser.set_defaults(func=_run_build)


def _run_template(args: argparse.Namespace) -> None:
    png_path, manifest_path = template.save_template(
        args.out,
        chars=args.chars,
        cols=args.cols,
        cell_size=(args.cell_width, args.cell_height),
    )
    print(f"Wrote template image:  {png_path}")
    print(f"Wrote manifest:        {manifest_path}")
    print(f"\n{DIMENSION_WARNING}")


def _run_build(args: argparse.Namespace) -> None:
    result = pipeline.build_font(
        args.filled,
        args.manifest,
        args.out,
        family=args.family,
        style=args.style,
        threshold=args.threshold,
    )
    built = result["built"]
    skipped = result["skipped_blank"]
    print(f"Glyphs built: {len(built)}")
    if built:
        print(f"  Built chars: {''.join(built)}")
    if skipped:
        print(f"Skipped (blank cell): {len(skipped)}")
        print(f"  Skipped chars: {''.join(skipped)}")
    print(f"Output font: {result['out_path']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.font_generator.cli",
        description="Generate a fill-in-the-blank template, then build a .ttf font from it.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    _add_template_parser(subparsers)
    _add_build_parser(subparsers)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        args.func(args)
    except (ValueError, RuntimeError, OSError) as exc:
        # OSError covers FileNotFoundError, PermissionError, IsADirectoryError —
        # any filesystem failure from a subcommand surfaces as a clean message,
        # not a traceback.
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
