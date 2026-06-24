"""
scripts.flux_lora.cli — Command-line interface for FLUX LoRA operations.

Commands:
  train          Pack dataset, show manifest, gate on 'y', submit training.
  generate       Run inference with latest (or specified) LoRA.
  status         Fetch live status of a training run by ID.
  list           List all saved training run records.
  dataset-info   Validate dataset and print summary.

Usage:
  python -m scripts.flux_lora.cli train [--dataset-dir PATH] [--steps N] ...
  python -m scripts.flux_lora.cli generate PROMPT [--lora-url URL] ...
  python -m scripts.flux_lora.cli status TRAINING_ID
  python -m scripts.flux_lora.cli list
  python -m scripts.flux_lora.cli dataset-info [--dataset-dir PATH]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from scripts.flux_lora import (
    DatasetError,
    FluxLoraError,
    RequiresConfirmationError,
    UserAbortError,
)
from scripts.flux_lora.config import (
    DATASET_DIR,
    DEFAULT_BATCH_SIZE,
    DEFAULT_LEARNING_RATE,
    DEFAULT_LORA_RANK,
    DEFAULT_OPTIMIZER,
    DEFAULT_RESOLUTION,
    DEFAULT_STEPS,
    DEFAULT_TRIGGER_WORD,
    api_key_present,
)
from scripts.flux_lora.dataset import dataset_summary, pack_zip, validate_dataset
from scripts.flux_lora.inference import DEFAULT_NUM_OUTPUTS, generate, load_latest_lora
from scripts.flux_lora.status import format_status, get_status, list_runs
from scripts.flux_lora.trainer import (
    build_manifest,
    save_run_record,
    show_stopandshow,
    start_training,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _confirm(prompt: str = "Proceed? [y/N] ") -> bool:
    """Read a single line from stdin; return True only on 'y' / 'yes'."""
    try:
        answer = input(prompt).strip().lower()
    except (EOFError, KeyboardInterrupt):
        return False
    return answer in ("y", "yes")


def _abort(msg: str = "Aborted.") -> None:
    print(msg, file=sys.stderr)
    sys.exit(1)


# ---------------------------------------------------------------------------
# Subcommand: dataset-info
# ---------------------------------------------------------------------------


def cmd_dataset_info(args: argparse.Namespace) -> None:
    dataset_dir = Path(args.dataset_dir)
    try:
        validate_dataset(dataset_dir)
        summary = dataset_summary(dataset_dir)
    except DatasetError as exc:
        print(f"Dataset error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Dataset dir   : {summary['dataset_dir']}")
    print(f"Images        : {summary['image_count']}")
    print(f"Captions      : {summary['caption_count']}")
    print(f"Total size    : {summary['total_bytes']:,} bytes")
    print("Validation    : OK")


# ---------------------------------------------------------------------------
# Subcommand: train
# ---------------------------------------------------------------------------


def cmd_train(args: argparse.Namespace) -> None:
    dataset_dir = Path(args.dataset_dir)

    # Validate first — fast fail before spending money.
    try:
        validate_dataset(dataset_dir)
    except DatasetError as exc:
        print(f"Dataset error: {exc}", file=sys.stderr)
        sys.exit(1)

    if not api_key_present():
        print(
            "REPLICATE_API_TOKEN not set. Export it before training.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Pack zip
    print(f"Packing dataset from {dataset_dir} …")
    try:
        zip_path = pack_zip(dataset_dir)
    except DatasetError as exc:
        print(f"Pack error: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"Packed: {zip_path}")

    # Build manifest
    try:
        manifest = build_manifest(
            zip_path,
            trigger_word=args.trigger_word,
            steps=args.steps,
            lora_rank=args.lora_rank,
            optimizer=args.optimizer,
            batch_size=args.batch_size,
            resolution=args.resolution,
            learning_rate=args.learning_rate,
            destination_model=args.destination_model,
        )
    except ValueError as exc:
        print(f"Manifest error: {exc}", file=sys.stderr)
        sys.exit(1)

    # STOP-AND-SHOW
    show_stopandshow(manifest)
    if not _confirm():
        raise UserAbortError("Training cancelled by user.")

    # Require upload URL
    input_images_url = (args.input_images_url or "").strip()
    if not input_images_url:
        print(
            "Error: --input-images-url is required. Upload the zip to a public URL and supply it.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Submit
    print("Submitting training job …")
    try:
        training_resp = start_training(manifest, confirmed=True, input_images_url=input_images_url)
    except FluxLoraError as exc:
        print(f"Training error: {exc}", file=sys.stderr)
        sys.exit(1)

    # Save record
    record_path = save_run_record(training_resp, manifest)
    print(f"Training submitted. ID: {training_resp.get('id', 'unknown')}")
    print(f"Run record saved to: {record_path}")
    if training_resp.get("urls", {}).get("get"):
        print(f"Track at: {training_resp['urls']['get']}")


# ---------------------------------------------------------------------------
# Subcommand: generate
# ---------------------------------------------------------------------------


def cmd_generate(args: argparse.Namespace) -> None:
    lora_url = args.lora_url
    if not lora_url:
        lora_url = load_latest_lora()
        if not lora_url:
            print(
                "No succeeded training run found. Supply --lora-url explicitly.",
                file=sys.stderr,
            )
            sys.exit(1)
        print(f"Using latest LoRA: {lora_url}")

    if not api_key_present():
        print(
            "REPLICATE_API_TOKEN not set. Export it before generating.",
            file=sys.stderr,
        )
        sys.exit(1)

    # STOP-AND-SHOW is printed inside generate() when confirmed=False.
    # We call with confirmed=False first so the user sees the manifest,
    # then re-call with confirmed=True after 'y'.
    try:
        generate(
            args.prompt,
            lora_url,
            confirmed=False,
            num_outputs=args.num_outputs,
        )
    except RequiresConfirmationError:
        pass  # Expected — manifest was printed, now gate on user input.

    if not _confirm():
        raise UserAbortError("Generation cancelled by user.")

    try:
        urls = generate(
            args.prompt,
            lora_url,
            confirmed=True,
            num_outputs=args.num_outputs,
        )
    except FluxLoraError as exc:
        print(f"Inference error: {exc}", file=sys.stderr)
        sys.exit(1)

    print("Output images:")
    for url in urls:
        print(f"  {url}")


# ---------------------------------------------------------------------------
# Subcommand: status
# ---------------------------------------------------------------------------


def cmd_status(args: argparse.Namespace) -> None:
    try:
        status_dict = get_status(args.training_id)
    except FluxLoraError as exc:
        print(f"Status error: {exc}", file=sys.stderr)
        sys.exit(1)
    print(format_status(status_dict))


# ---------------------------------------------------------------------------
# Subcommand: list
# ---------------------------------------------------------------------------


def cmd_list(args: argparse.Namespace) -> None:
    runs = list_runs()
    if not runs:
        print("No training run records found.")
        return
    print(f"{'ID':<30}  {'Status':<12}  {'Timestamp':<22}  {'Cost'}")
    print("-" * 80)
    for run in runs:
        resp = run.get("replicate_response", {})
        manifest = run.get("manifest", {})
        print(
            f"{run.get('training_id', 'unknown'):<30}  "
            f"{resp.get('status', 'unknown'):<12}  "
            f"{run.get('timestamp', ''):<22}  "
            f"${manifest.get('cost_usd', 0):.2f}"
        )


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m scripts.flux_lora.cli",
        description="FLUX LoRA training + inference for SkyyRose brand.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # dataset-info
    p_info = sub.add_parser("dataset-info", help="Validate dataset and print summary.")
    p_info.add_argument(
        "--dataset-dir",
        default=str(DATASET_DIR),
        help="Path to dataset directory.",
    )
    p_info.set_defaults(func=cmd_dataset_info)

    # train
    p_train = sub.add_parser("train", help="Pack dataset and submit training job.")
    p_train.add_argument("--dataset-dir", default=str(DATASET_DIR))
    p_train.add_argument("--trigger-word", default=DEFAULT_TRIGGER_WORD)
    p_train.add_argument("--steps", type=int, default=DEFAULT_STEPS)
    p_train.add_argument("--lora-rank", type=int, default=DEFAULT_LORA_RANK)
    p_train.add_argument("--optimizer", default=DEFAULT_OPTIMIZER)
    p_train.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    p_train.add_argument("--resolution", default=DEFAULT_RESOLUTION)
    p_train.add_argument("--learning-rate", type=float, default=DEFAULT_LEARNING_RATE)
    p_train.add_argument(
        "--destination-model",
        required=True,
        help="REQUIRED. Replicate model slug to push the LoRA to, e.g. 'skyyrose/skyyrose-lora'.",
    )
    p_train.add_argument(
        "--input-images-url",
        default=None,
        help="Public URL of the uploaded dataset zip (required for actual submission).",
    )
    p_train.set_defaults(func=cmd_train)

    # generate
    p_gen = sub.add_parser("generate", help="Run FLUX inference with a trained LoRA.")
    p_gen.add_argument("prompt", help="Text prompt (include trigger word).")
    p_gen.add_argument("--lora-url", default=None, help="Override LoRA URL.")
    p_gen.add_argument("--num-outputs", type=int, default=DEFAULT_NUM_OUTPUTS)
    p_gen.set_defaults(func=cmd_generate)

    # status
    p_status = sub.add_parser("status", help="Fetch live training status.")
    p_status.add_argument("training_id", help="Replicate training ID.")
    p_status.set_defaults(func=cmd_status)

    # list
    p_list = sub.add_parser("list", help="List all saved training run records.")
    p_list.set_defaults(func=cmd_list)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except UserAbortError as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
    except FluxLoraError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
