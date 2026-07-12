#!/usr/bin/env python3
"""Post-export check: parse `npx @gltf-transform/cli inspect` output and assert
the intended end state -- draco-compressed geometry present, textures at the
target format and dimensions -- rather than trusting the CLI's exit code alone.

A bare `gltf-transform` binary does not resolve in this environment (confirmed
this session -- it maps to a different, nonexistent npm package). This script
always invokes the scoped `@gltf-transform/cli` package via npx.

Usage:
    python3 gltf_export_verify.py <file.glb> --width 1024 --height 1024 \\
        --format jpeg --require-draco
"""

import argparse
import re
import subprocess
import sys


def run_inspect(path):
    result = subprocess.run(
        ["npx", "--no-install", "@gltf-transform/cli", "inspect", path],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"gltf-transform inspect failed (exit {result.returncode}): {result.stderr}"
        )
    return result.stdout


def strip_ansi(text):
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def check(path, expect_width, expect_height, expect_format, require_draco):
    raw = run_inspect(path)
    clean = strip_ansi(raw)
    failures = []

    if require_draco:
        if "KHR_draco_mesh_compression" not in clean:
            failures.append("KHR_draco_mesh_compression not found in extensionsUsed/Required")

    if expect_width and expect_height:
        res_pattern = rf"{expect_width}x{expect_height}"
        if not re.search(res_pattern, clean):
            failures.append(f"no texture reported at {expect_width}x{expect_height} resolution")

    if expect_format:
        mime_map = {"jpeg": "image/jpeg", "jpg": "image/jpeg", "png": "image/png"}
        expected_mime = mime_map.get(expect_format.lower(), expect_format)
        if expected_mime not in clean:
            failures.append(f"no texture reported with mimeType {expected_mime}")

    return raw, failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("glb_path")
    parser.add_argument("--width", type=int, default=None)
    parser.add_argument("--height", type=int, default=None)
    parser.add_argument("--format", default=None, help="e.g. jpeg or png")
    parser.add_argument("--require-draco", action="store_true")
    args = parser.parse_args()

    raw, failures = check(args.glb_path, args.width, args.height, args.format, args.require_draco)

    print(raw)
    if failures:
        print(f"\nFAIL -- {len(failures)} check(s) did not match:")
        for f in failures:
            print(f"  {f}")
        sys.exit(1)

    print("\nPASS -- all requested export properties confirmed via independent inspect parse.")
    sys.exit(0)


if __name__ == "__main__":
    main()
