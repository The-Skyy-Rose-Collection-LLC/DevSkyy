"""
Enhance Training Captions for Exact Replica Mode
=================================================

Updates all captions in skyyrose_lora_v2 dataset to emphasize:
- Exact replica preservation
- Logo/color/design preservation
- Quality enhancement only (no creative alterations)

Usage:
    python scripts/enhance_captions_exact_replica.py
"""

import json
from pathlib import Path

# Caption templates for exact replica mode
CAPTION_TEMPLATES = {
    "signature": "exact replica, SkyyRose signature collection {product_name}, preserve all logos and colors, enhance clarity and sharpness only, professional studio photography, preserve original rose gold accents #B76E79",
    "love_hurts": "exact replica, SkyyRose love hurts collection {product_name}, preserve all logos and colors, enhance clarity and sharpness only, professional studio photography, preserve original design and branding",
    "black_rose": "exact replica, SkyyRose black rose collection {product_name}, preserve all logos and colors, enhance clarity and sharpness only, professional studio photography, preserve exclusive premium design",
}

# Quality enhancement keywords (allowed)
ALLOWED_ENHANCEMENTS = [
    "enhance clarity",
    "improve sharpness",
    "reduce noise",
    "professional lighting",
    "studio quality",
    "high resolution",
    "color accuracy",
]

# Preservation keywords (critical)
PRESERVATION_KEYWORDS = [
    "exact replica",
    "preserve all logos",
    "preserve all colors",
    "preserve original design",
    "no alterations",
    "no modifications",
]

# Forbidden keywords (must NOT appear)
FORBIDDEN_KEYWORDS = [
    "creative",
    "artistic",
    "style transfer",
    "color grading",
    "modified",
    "altered",
    "reimagined",
    "inspired by",
]


def extract_product_name(image_name: str) -> str:
    """Extract human-readable product name from image filename."""
    # Remove collection prefix and file extension
    name = image_name.replace("SIG_", "").replace("LH_", "").replace("BR_", "")
    name = name.replace(".jpg", "").replace(".png", "")

    # Convert underscores to spaces
    name = name.replace("_", " ")

    # Capitalize words
    name = name.title()

    return name


def detect_collection(image_name: str) -> str:
    """Detect collection from image filename prefix."""
    if image_name.startswith("SIG_"):
        return "signature"
    elif image_name.startswith("LH_"):
        return "love_hurts"
    elif image_name.startswith("BR_"):
        return "black_rose"
    else:
        # Default to signature if no prefix
        return "signature"


def create_exact_replica_caption(image_name: str, original_caption: str = "") -> str:
    """
    Create enhanced caption with exact replica emphasis.

    Args:
        image_name: Image filename (e.g., "SIG_COTTON_CANDY_TEE.jpg")
        original_caption: Original caption (optional, for context)

    Returns:
        Enhanced caption with preservation keywords
    """
    collection = detect_collection(image_name)
    product_name = extract_product_name(image_name)

    # Get template for collection
    template = CAPTION_TEMPLATES.get(collection, CAPTION_TEMPLATES["signature"])

    # Fill in product name
    caption = template.format(product_name=product_name.lower())

    # Add negative prompt (what NOT to do)
    negative_keywords = ", ".join([f"no {kw}" for kw in FORBIDDEN_KEYWORDS[:4]])
    caption += f", {negative_keywords}"

    return caption


def enhance_dataset_captions(dataset_path: Path):
    """
    Enhance all captions in metadata.jsonl with exact replica emphasis.

    Args:
        dataset_path: Path to dataset directory containing metadata.jsonl
    """
    metadata_path = dataset_path / "metadata.jsonl"

    if not metadata_path.exists():
        print(f"❌ Metadata file not found: {metadata_path}")
        return

    print(f"📝 Enhancing captions in {metadata_path}")
    print("   Focus: Exact replica + preservation keywords")

    # Read all lines
    enhanced_lines = []
    original_count = 0
    enhanced_count = 0

    with open(metadata_path) as f:
        for line in f:
            original_count += 1
            entry = json.loads(line.strip())

            # Get image filename
            image_file = entry.get("file_name", "")

            # Create enhanced caption
            original_caption = entry.get("text", "")
            enhanced_caption = create_exact_replica_caption(image_file, original_caption)

            # Update entry
            entry["text"] = enhanced_caption
            entry["original_caption"] = original_caption  # Keep original for reference

            enhanced_lines.append(json.dumps(entry))
            enhanced_count += 1

    # Backup original
    backup_path = dataset_path / "metadata.jsonl.backup"
    if not backup_path.exists():
        print(f"💾 Backing up original to {backup_path}")
        with open(metadata_path) as f:
            with open(backup_path, "w") as fb:
                fb.write(f.read())

    # Write enhanced captions
    with open(metadata_path, "w") as f:
        f.write("\n".join(enhanced_lines))

    print(f"\n✅ Enhanced {enhanced_count}/{original_count} captions")
    print(f"   Backup saved to {backup_path}")
    print("\n📊 Sample Enhanced Captions:")

    # Show 3 random samples
    import random

    samples = random.sample(enhanced_lines, min(3, len(enhanced_lines)))
    for i, sample in enumerate(samples, 1):
        entry = json.loads(sample)
        print(f"\n   {i}. {entry['file_name']}:")
        print(f"      {entry['text'][:150]}...")


def validate_captions(dataset_path: Path):
    """
    Validate that all captions have preservation keywords and no forbidden keywords.

    Args:
        dataset_path: Path to dataset directory
    """
    metadata_path = dataset_path / "metadata.jsonl"

    print("\n🔍 Validating enhanced captions...")

    issues = []
    total = 0
    has_preservation = 0
    has_forbidden = 0

    with open(metadata_path) as f:
        for line in f:
            total += 1
            entry = json.loads(line.strip())
            caption = entry.get("text", "").lower()

            # Check for preservation keywords
            if any(kw in caption for kw in PRESERVATION_KEYWORDS):
                has_preservation += 1
            else:
                issues.append(f"Missing preservation keywords: {entry['file_name']}")

            # Check for forbidden keywords
            if any(kw in caption for kw in FORBIDDEN_KEYWORDS):
                has_forbidden += 1
                issues.append(f"Contains forbidden keywords: {entry['file_name']}")

    print("\n📊 Validation Results:")
    print(f"   Total captions: {total}")
    print(
        f"   With preservation keywords: {has_preservation} ({100 * has_preservation / total:.1f}%)"
    )
    print(f"   With forbidden keywords: {has_forbidden} ({100 * has_forbidden / total:.1f}%)")

    if issues:
        print(f"\n⚠️  {len(issues)} issues found:")
        for issue in issues[:5]:  # Show first 5
            print(f"   - {issue}")
        if len(issues) > 5:
            print(f"   ... and {len(issues) - 5} more")
    else:
        print("\n✅ All captions validated!")
        print("   - 100% have preservation keywords")
        print("   - 0% have forbidden keywords")


def main():
    """Main entry point."""
    dataset_path = Path("datasets/skyyrose_lora_v2")

    if not dataset_path.exists():
        print(f"❌ Dataset not found: {dataset_path}")
        print("   Expected structure:")
        print(f"   {dataset_path}/")
        print("     ├── metadata.jsonl")
        print("     └── images/")
        return 1

    print("=" * 70)
    print("SkyyRose LoRA - Caption Enhancement for Exact Replica Mode")
    print("=" * 70)

    # Enhance captions
    enhance_dataset_captions(dataset_path)

    # Validate
    validate_captions(dataset_path)

    print("\n" + "=" * 70)
    print("Caption enhancement complete!")
    print("=" * 70)
    print("\n🎯 Next Steps:")
    print("   1. Review sample captions above")
    print("   2. Upload enhanced dataset to HuggingFace:")
    print("      python scripts/upload_lora_dataset_v2.py")
    print("   3. Start Phase 2 training:")
    print("      python scripts/train_phase2_exact_replica.py")

    return 0


if __name__ == "__main__":
    exit(main())
