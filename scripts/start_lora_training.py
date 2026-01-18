#!/usr/bin/env python3
"""
Start LoRA training on HuggingFace Space via API.

Usage:
    python3 scripts/start_lora_training.py
"""

from gradio_client import Client

# Connect to your LoRA Training Monitor Space
client = Client("damBruh/skyyrose-lora-training-monitor")

print("🚀 Starting SkyyRose LoRA Training...")
print("=" * 70)

# Training configuration
config = {
    "dataset_id": "damBruh/skyyrose-lora-dataset-v3",
    "trigger_word": "skyyrose",
    "collections": ["BLACK_ROSE", "SIGNATURE", "LOVE_HURTS"],
    "epochs": 100,
    "learning_rate": 1e-4,
    "lora_rank": 16,
    "batch_size": 1,
    "resolution": 512,
}

print("\n📋 Configuration:")
for key, value in config.items():
    print(f"  {key}: {value}")

print("\n🎯 Submitting training job to HuggingFace Space...")

try:
    # Start training (adjust function name based on your Space's API)
    result = client.predict(
        dataset_id=config["dataset_id"],
        trigger_word=config["trigger_word"],
        epochs=config["epochs"],
        learning_rate=config["learning_rate"],
        lora_rank=config["lora_rank"],
        api_name="/start_training",  # Adjust based on your Space's endpoint
    )

    print("\n✅ Training Started!")
    print(f"Result: {result}")
    print("\n📊 Monitor progress at:")
    print("https://huggingface.co/spaces/damBruh/skyyrose-lora-training-monitor")

except Exception as e:
    print(f"\n❌ Error: {e}")
    print("\n💡 Troubleshooting:")
    print(
        "  1. Check Space is running: https://huggingface.co/spaces/damBruh/skyyrose-lora-training-monitor"
    )
    print("  2. Verify API endpoint name with: client.view_api()")
    print("  3. Check HuggingFace authentication")

    print("\n🔍 Available API endpoints:")
    print(client.view_api())
