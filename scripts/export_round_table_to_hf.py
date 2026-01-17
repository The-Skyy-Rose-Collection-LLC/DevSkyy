#!/usr/bin/env python3
"""
Export Round Table Results to HuggingFace
=========================================

This script exports winning scene specifications from the LLM Round Table
competition to a HuggingFace dataset for training and sharing.

Usage:
    # Dry run - see what would be exported
    python scripts/export_round_table_to_hf.py --dry-run

    # Export to local file only
    python scripts/export_round_table_to_hf.py --local-only

    # Full export to HuggingFace
    python scripts/export_round_table_to_hf.py

    # Export specific collections
    python scripts/export_round_table_to_hf.py --collections signature black-rose

Features:
    - Reads ROUND_TABLE_ELITE_RESULTS.json
    - Transforms to HuggingFace datasets format
    - Includes Three.js scene specifications
    - Preserves scoring metrics for analysis
"""

import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

# =============================================================================
# Input Validation
# =============================================================================

# Safe dataset name pattern (alphanumeric, hyphens, underscores)
DATASET_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,64}$")
VALID_COLLECTIONS = frozenset({"signature", "black-rose", "black_rose", "love-hurts", "love_hurts"})
# Maximum JSON file size (10MB)
MAX_JSON_FILE_SIZE = 10 * 1024 * 1024


def validate_dataset_name(name: str) -> str:
    """Validate dataset name is safe for file/URL use."""
    if not DATASET_NAME_PATTERN.match(name):
        raise argparse.ArgumentTypeError(
            f"Invalid dataset name '{name}'. "
            "Must be 1-64 alphanumeric chars, hyphens, or underscores."
        )
    return name


def validate_collections(collections: list[str] | None) -> list[str] | None:
    """Validate collection names against whitelist."""
    if collections is None:
        return None
    invalid = set(collections) - VALID_COLLECTIONS
    if invalid:
        raise argparse.ArgumentTypeError(
            f"Invalid collections: {invalid}. Valid: {sorted(VALID_COLLECTIONS)}"
        )
    return collections


# =============================================================================
# Configuration
# =============================================================================

ROUND_TABLE_RESULTS_PATH = Path("assets/ai-enhanced-images/ROUND_TABLE_ELITE_RESULTS.json")
EXPORTS_DIR = Path("assets/exports")
DEFAULT_DATASET_NAME = "skyyrose-scene-specs"

HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_ACCESS_TOKEN")
HF_USERNAME = os.getenv("HF_USERNAME", "damBruh")


# =============================================================================
# Data Transformation
# =============================================================================


def load_round_table_results() -> dict | None:
    """Load Round Table elite results with safety checks."""
    if not ROUND_TABLE_RESULTS_PATH.exists():
        logger.error(f"Round Table results not found: {ROUND_TABLE_RESULTS_PATH}")
        return None

    # Check file size before loading
    file_size = ROUND_TABLE_RESULTS_PATH.stat().st_size
    if file_size > MAX_JSON_FILE_SIZE:
        logger.error(f"File too large: {file_size} bytes (max: {MAX_JSON_FILE_SIZE})")
        return None

    try:
        with open(ROUND_TABLE_RESULTS_PATH) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in Round Table results: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to load Round Table results: {e}")
        return None


def transform_to_hf_dataset(
    rt_data: dict,
    collections: list[str] | None = None,
) -> list[dict]:
    """
    Transform Round Table results to HuggingFace dataset format.

    Args:
        rt_data: Raw Round Table results
        collections: Specific collections to include (None = all)

    Returns:
        List of dataset items
    """
    items = []

    collections_data = rt_data.get("collections", {})

    if not collections_data:
        logger.warning("No collections found in Round Table results")
        return items

    for collection_name, collection_data in collections_data.items():
        # Filter if specific collections requested
        if collections and collection_name not in collections:
            continue

        winner = collection_data.get("winner", {})

        if not winner:
            logger.warning(f"No winner found for collection: {collection_name}")
            continue

        # Extract scene spec
        scene_spec = winner.get("scene_spec", {})
        if isinstance(scene_spec, str):
            try:
                scene_spec = json.loads(scene_spec)
            except json.JSONDecodeError:
                scene_spec = {"raw": scene_spec}

        # Build dataset item
        item = {
            # Identifiers
            "id": f"{collection_name}_{datetime.utcnow().strftime('%Y%m%d')}",
            "collection": collection_name,
            "generated_at": rt_data.get("generated_at", datetime.utcnow().isoformat()),
            # Winner info
            "provider": winner.get("provider", "unknown"),
            "model": winner.get("model", ""),
            # Scores
            "total_score": float(winner.get("total_score", 0.0) or 0.0),
            "verdict": winner.get("verdict", "UNKNOWN"),
            "prompt_quality": float(winner.get("prompt_quality", 0.0) or 0.0),
            "execution_quality": float(winner.get("execution_quality", 0.0) or 0.0),
            "brand_dna_alignment": float(winner.get("brand_dna_alignment", 0.0) or 0.0),
            # Content
            "summary": str(winner.get("summary", ""))[:1000],  # Truncate
            "scene_spec_json": json.dumps(scene_spec, indent=2),
            # Metadata
            "competition_type": "elite_3pillar",
            "brand": "SkyyRose",
        }

        items.append(item)
        logger.info(
            f"Transformed {collection_name}: {item['provider']} ({item['total_score']:.1f})"
        )

    return items


def save_local_export(items: list[dict], dataset_name: str) -> Path:
    """
    Save export to local JSON file.

    Args:
        items: Dataset items
        dataset_name: Name for the export

    Returns:
        Path to exported file
    """
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    export_path = EXPORTS_DIR / f"{dataset_name}.json"

    export_data = {
        "dataset_name": dataset_name,
        "exported_at": datetime.utcnow().isoformat(),
        "source": str(ROUND_TABLE_RESULTS_PATH),
        "item_count": len(items),
        "schema": {
            "id": "string - unique identifier",
            "collection": "string - collection name (signature, black-rose, love-hurts)",
            "provider": "string - winning LLM provider",
            "total_score": "float - overall score (0-100)",
            "verdict": "string - quality verdict (EXCELLENT, GOOD, etc.)",
            "scene_spec_json": "string - Three.js scene specification as JSON",
        },
        "items": items,
    }

    with open(export_path, "w") as f:
        json.dump(export_data, f, indent=2)

    logger.info(f"Saved local export to: {export_path}")
    return export_path


def upload_to_huggingface(items: list[dict], dataset_name: str) -> str | None:
    """
    Upload dataset to HuggingFace Hub.

    Args:
        items: Dataset items
        dataset_name: HuggingFace dataset name

    Returns:
        Dataset URL or None if failed
    """
    if not HF_TOKEN:
        logger.error("HF_TOKEN not configured - cannot upload to HuggingFace")
        return None

    try:
        from datasets import Dataset

        # Create HuggingFace dataset
        dataset = Dataset.from_list(items)

        # Push to Hub
        repo_id = f"{HF_USERNAME}/{dataset_name}"
        dataset.push_to_hub(
            repo_id,
            token=HF_TOKEN,
            private=False,  # Make public for SkyyRose community
        )

        dataset_url = f"https://huggingface.co/datasets/{repo_id}"
        logger.info(f"Uploaded to HuggingFace: {dataset_url}")

        return dataset_url

    except ImportError:
        logger.error("datasets library not installed. Run: pip install datasets")
        return None
    except Exception as e:
        logger.error(f"Failed to upload to HuggingFace: {e}")
        return None


# =============================================================================
# Main
# =============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="Export Round Table results to HuggingFace dataset"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be exported without saving",
    )
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="Save to local file only, skip HuggingFace upload",
    )
    parser.add_argument(
        "--dataset-name",
        default=DEFAULT_DATASET_NAME,
        type=validate_dataset_name,
        help=f"Dataset name (default: {DEFAULT_DATASET_NAME})",
    )
    parser.add_argument(
        "--collections",
        nargs="+",
        help="Specific collections to export (default: all)",
    )

    args = parser.parse_args()

    # Validate collections if provided
    if args.collections:
        try:
            validate_collections(args.collections)
        except argparse.ArgumentTypeError as e:
            parser.error(str(e))

    logger.info("=" * 60)
    logger.info("Round Table → HuggingFace Export")
    logger.info("=" * 60)

    # Load Round Table results
    logger.info(f"Loading results from: {ROUND_TABLE_RESULTS_PATH}")
    rt_data = load_round_table_results()

    if not rt_data:
        logger.error("Failed to load Round Table results")
        sys.exit(1)

    # Transform to dataset format
    logger.info("Transforming to HuggingFace dataset format...")
    items = transform_to_hf_dataset(rt_data, collections=args.collections)

    if not items:
        logger.error("No items to export")
        sys.exit(1)

    logger.info(f"Prepared {len(items)} items for export")

    # Dry run - just show what would be exported
    if args.dry_run:
        logger.info("\n[DRY RUN] Would export:")
        for item in items:
            logger.info(f"  • {item['collection']}: {item['provider']} ({item['total_score']:.1f})")
        logger.info(f"\n[DRY RUN] Would save to: {EXPORTS_DIR / args.dataset_name}.json")
        if not args.local_only:
            logger.info(
                f"[DRY RUN] Would upload to: https://huggingface.co/datasets/{HF_USERNAME}/{args.dataset_name}"
            )
        return

    # Save local export
    export_path = save_local_export(items, args.dataset_name)
    logger.info(f"✓ Local export saved: {export_path}")

    # Upload to HuggingFace (unless local-only)
    if not args.local_only:
        dataset_url = upload_to_huggingface(items, args.dataset_name)
        if dataset_url:
            logger.info(f"✓ HuggingFace upload complete: {dataset_url}")
        else:
            logger.warning("⚠ HuggingFace upload skipped (see errors above)")

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Export Summary")
    logger.info("=" * 60)
    logger.info(f"Items exported: {len(items)}")
    logger.info(f"Collections: {', '.join(item['collection'] for item in items)}")
    logger.info(f"Local file: {export_path}")

    for item in items:
        logger.info(f"\n{item['collection'].upper()}:")
        logger.info(f"  Winner: {item['provider']}")
        logger.info(f"  Score: {item['total_score']:.1f}/100 ({item['verdict']})")


if __name__ == "__main__":
    main()
