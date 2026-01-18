#!/usr/bin/env python3
"""
Local LoRA training using PyTorch MPS (Apple Silicon).

Trains SDXL LoRA on SkyyRose V3 dataset (604 product images).
Uses Apple Metal Performance Shaders for GPU acceleration.

Usage:
    python3 scripts/train_lora_local.py --epochs 10 --batch-size 1
"""

import argparse
import gc
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import torch
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from tqdm import tqdm

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class SkyyRoseDataset(Dataset):
    """Dataset for SkyyRose LoRA training."""

    def __init__(self, dataset_dir: Path, resolution: int = 512):
        self.resolution = resolution
        self.images = []
        self.captions = []

        images_dir = dataset_dir / "images"
        metadata_path = dataset_dir / "metadata.jsonl"

        # Load captions from metadata
        caption_map = {}
        if metadata_path.exists():
            with open(metadata_path) as f:
                for line in f:
                    entry = json.loads(line.strip())
                    caption_map[entry["file_name"]] = entry["text"]

        # Load images
        for img_path in sorted(images_dir.glob("*")):
            if img_path.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"):
                self.images.append(img_path)
                self.captions.append(
                    caption_map.get(img_path.name, "skyyrose luxury streetwear product")
                )

        logger.info(f"Loaded {len(self.images)} images from {dataset_dir}")

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        img_path = self.images[idx]
        caption = self.captions[idx]

        # Load and preprocess image
        image = Image.open(img_path).convert("RGB")
        image = image.resize((self.resolution, self.resolution), Image.LANCZOS)

        # Convert to tensor (normalize to [-1, 1])
        import torchvision.transforms as T

        transform = T.Compose(
            [
                T.ToTensor(),
                T.Normalize([0.5], [0.5]),
            ]
        )
        pixel_values = transform(image)

        return {
            "pixel_values": pixel_values,
            "caption": caption,
        }


def get_device():
    """Get best available device."""
    if torch.backends.mps.is_available():
        return torch.device("mps")
    elif torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def train_lora(
    dataset_dir: Path,
    output_dir: Path,
    epochs: int = 10,
    batch_size: int = 1,
    learning_rate: float = 1e-4,
    lora_rank: int = 16,
    resolution: int = 512,
):
    """Train LoRA on SDXL UNet."""
    from diffusers import AutoencoderKL, UNet2DConditionModel
    from peft import LoraConfig, get_peft_model
    from transformers import CLIPTextModel, CLIPTokenizer

    device = get_device()
    logger.info(f"Training on device: {device}")

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load dataset
    dataset = SkyyRoseDataset(dataset_dir, resolution=resolution)
    dataloader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    logger.info("Loading SDXL components...")

    # Load tokenizer and text encoder (CPU to save memory)
    tokenizer = CLIPTokenizer.from_pretrained(
        "stabilityai/stable-diffusion-xl-base-1.0",
        subfolder="tokenizer",
    )
    text_encoder = CLIPTextModel.from_pretrained(
        "stabilityai/stable-diffusion-xl-base-1.0",
        subfolder="text_encoder",
        torch_dtype=torch.float16,
    )

    # Load VAE (CPU, only used for encoding)
    vae = AutoencoderKL.from_pretrained(
        "stabilityai/stable-diffusion-xl-base-1.0",
        subfolder="vae",
        torch_dtype=torch.float16,
    )

    # Load UNet and add LoRA
    logger.info("Loading UNet and configuring LoRA...")
    unet = UNet2DConditionModel.from_pretrained(
        "stabilityai/stable-diffusion-xl-base-1.0",
        subfolder="unet",
        torch_dtype=torch.float16,
    )

    # Configure LoRA
    lora_config = LoraConfig(
        r=lora_rank,
        lora_alpha=lora_rank,
        target_modules=["to_k", "to_q", "to_v", "to_out.0"],
        lora_dropout=0.05,
    )

    # Apply LoRA to UNet
    unet = get_peft_model(unet, lora_config)
    unet.print_trainable_parameters()

    # Move to device
    unet = unet.to(device)
    vae = vae.to(device)
    text_encoder = text_encoder.to(device)

    # Freeze everything except LoRA
    vae.requires_grad_(False)
    text_encoder.requires_grad_(False)

    # Optimizer
    optimizer = torch.optim.AdamW(
        unet.parameters(),
        lr=learning_rate,
        weight_decay=0.01,
    )

    # Training loop
    logger.info(f"Starting training: {epochs} epochs, {len(dataset)} images")

    progress_file = output_dir / "progress.json"
    best_loss = float("inf")

    for epoch in range(epochs):
        unet.train()
        epoch_loss = 0.0

        progress_bar = tqdm(dataloader, desc=f"Epoch {epoch + 1}/{epochs}")

        for batch in progress_bar:
            pixel_values = batch["pixel_values"].to(device, dtype=torch.float16)
            captions = batch["caption"]

            # Encode text
            text_inputs = tokenizer(
                captions,
                padding="max_length",
                max_length=77,
                truncation=True,
                return_tensors="pt",
            )
            text_embeds = text_encoder(text_inputs.input_ids.to(device))[0]

            # Encode images to latents
            with torch.no_grad():
                latents = vae.encode(pixel_values).latent_dist.sample()
                latents = latents * vae.config.scaling_factor

            # Add noise
            noise = torch.randn_like(latents)
            timesteps = torch.randint(0, 1000, (latents.shape[0],), device=device)

            # Get noisy latents
            alpha_t = 1 - (timesteps.float() / 1000).view(-1, 1, 1, 1)
            noisy_latents = alpha_t.sqrt() * latents + (1 - alpha_t).sqrt() * noise

            # Predict noise
            noise_pred = unet(
                noisy_latents,
                timesteps,
                encoder_hidden_states=text_embeds,
            ).sample

            # MSE loss
            loss = torch.nn.functional.mse_loss(noise_pred, noise)

            # Backward
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item()
            progress_bar.set_postfix(loss=loss.item())

        avg_loss = epoch_loss / len(dataloader)
        logger.info(f"Epoch {epoch + 1}/{epochs} - Loss: {avg_loss:.4f}")

        # Save progress
        progress = {
            "epoch": epoch + 1,
            "total_epochs": epochs,
            "loss": avg_loss,
            "best_loss": min(best_loss, avg_loss),
            "status": "training",
        }
        with open(progress_file, "w") as f:
            json.dump(progress, f, indent=2)

        # Save checkpoint if best
        if avg_loss < best_loss:
            best_loss = avg_loss
            checkpoint_dir = output_dir / "best_checkpoint"
            unet.save_pretrained(checkpoint_dir)
            logger.info(f"Saved best checkpoint (loss: {best_loss:.4f})")

        # Clear memory
        gc.collect()
        if device.type == "mps":
            torch.mps.empty_cache()

    # Save final model
    logger.info("Saving final LoRA weights...")
    final_dir = output_dir / "final"
    unet.save_pretrained(final_dir)

    # Update progress
    progress["status"] = "completed"
    progress["model_path"] = str(final_dir)
    with open(progress_file, "w") as f:
        json.dump(progress, f, indent=2)

    # Save training info
    info = {
        "completed_at": datetime.now().isoformat(),
        "epochs": epochs,
        "final_loss": avg_loss,
        "best_loss": best_loss,
        "lora_rank": lora_rank,
        "resolution": resolution,
        "dataset_size": len(dataset),
        "trigger_word": "skyyrose",
    }
    with open(output_dir / "training_info.json", "w") as f:
        json.dump(info, f, indent=2)

    logger.info(f"Training complete! Model saved to {final_dir}")
    return final_dir


def main():
    parser = argparse.ArgumentParser(description="Train SkyyRose LoRA locally")
    parser.add_argument("--epochs", type=int, default=10, help="Training epochs")
    parser.add_argument("--batch-size", type=int, default=1, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--lora-rank", type=int, default=16, help="LoRA rank")
    parser.add_argument("--resolution", type=int, default=512, help="Image resolution")
    args = parser.parse_args()

    print("=" * 70)
    print("  SKYYROSE LORA LOCAL TRAINING (MPS)")
    print("  Training on 604 exact product images")
    print("=" * 70 + "\n")

    dataset_dir = project_root / "datasets" / "skyyrose_lora_v3"
    output_dir = project_root / "models" / "skyyrose-lora-v3-local"

    if not dataset_dir.exists():
        print(f"ERROR: Dataset not found: {dataset_dir}")
        return 1

    print(f"Dataset: {dataset_dir}")
    print(f"Output: {output_dir}")
    print(f"Device: {get_device()}")
    print(f"Config: epochs={args.epochs}, batch={args.batch_size}, lr={args.lr}")
    print()

    try:
        train_lora(
            dataset_dir=dataset_dir,
            output_dir=output_dir,
            epochs=args.epochs,
            batch_size=args.batch_size,
            learning_rate=args.lr,
            lora_rank=args.lora_rank,
            resolution=args.resolution,
        )
        return 0
    except Exception as e:
        logger.error(f"Training failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
