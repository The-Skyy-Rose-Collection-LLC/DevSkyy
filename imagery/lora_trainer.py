"""SkyyRose LoRA Trainer.

Fine-tune SDXL on SkyyRose brand aesthetic using existing product images.
Creates custom LoRA weights for brand-consistent generation.

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

import json
import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class TrainingConfig:
    """Configuration for LoRA training."""

    # Model settings
    base_model: str = "stabilityai/stable-diffusion-xl-base-1.0"
    resolution: int = 1024
    train_batch_size: int = 1
    gradient_accumulation_steps: int = 4

    # LoRA settings
    lora_rank: int = 32  # Higher = better quality
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    target_modules: list[str] = field(default_factory=lambda: ["to_k", "to_q", "to_v", "to_out.0"])

    # Training settings
    num_epochs: int = 100
    learning_rate: float = 1e-4
    lr_scheduler: str = "cosine"
    lr_warmup_steps: int = 100

    # Output
    output_dir: str = "./models/skyyrose-luxury-lora"
    logging_steps: int = 10
    save_steps: int = 500
    checkpointing_steps: int = 500


@dataclass
class TrainingImage:
    """Training image with caption."""

    path: Path
    caption: str
    collection: str
    garment_type: str = ""
    quality_score: float = 1.0


@dataclass
class TrainingDataset:
    """Prepared training dataset."""

    images: list[TrainingImage] = field(default_factory=list)
    total_images: int = 0
    collections: dict[str, int] = field(default_factory=dict)
    metadata_path: Path | None = None

    def save_metadata(self, path: Path) -> None:
        """Save dataset metadata to JSON."""
        metadata = {
            "total_images": self.total_images,
            "collections": self.collections,
            "images": [
                {
                    "path": str(img.path),
                    "caption": img.caption,
                    "collection": img.collection,
                    "garment_type": img.garment_type,
                    "quality_score": img.quality_score,
                }
                for img in self.images
            ],
            "created_at": datetime.utcnow().isoformat(),
        }

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(metadata, f, indent=2)

        self.metadata_path = path


class SkyyRoseLoRATrainer:
    """Train custom LoRA on SkyyRose brand aesthetic.

    Uses existing product images and brand guidelines to create
    fine-tuned weights for consistent brand representation.

    Example:
        >>> trainer = SkyyRoseLoRATrainer()
        >>> dataset = await trainer.prepare_training_data(
        ...     image_dirs={
        ...         "BLACK_ROSE": Path("assets/black-rose"),
        ...         "LOVE_HURTS": Path("assets/love-hurts"),
        ...         "SIGNATURE": Path("assets/signature"),
        ...     }
        ... )
        >>> await trainer.train(dataset, epochs=100)
    """

    BRAND_DNA = {
        "aesthetic": "luxury streetwear, Oakland culture, high-fashion editorial",
        "colors": "rose gold #B76E79, black #1A1A1A, elegant neutrals",
        "mood": "bold, sophisticated, premium, empowering",
        "style": "gender-neutral, inclusive, authentic, aspirational",
    }

    COLLECTION_DESCRIPTIONS = {
        "BLACK_ROSE": (
            "dark romantic aesthetic, gothic elegance, midnight florals, "
            "noir photography, moody lighting, limited edition mystique"
        ),
        "LOVE_HURTS": (
            "edgy romance, heart motifs, vulnerable strength, "
            "romantic rebellion, artistic expression, passionate design"
        ),
        "SIGNATURE": (
            "classic SkyyRose style, rose gold accents, cotton candy pastels, "
            "timeless sophistication, versatile luxury, essential pieces"
        ),
    }

    GARMENT_DESCRIPTIONS = {
        "hoodie": "premium heavyweight hoodie, relaxed fit, embroidered details",
        "tee": "soft cotton tee, premium fabric, screen printed graphics",
        "shorts": "athletic shorts, comfortable fit, branded waistband",
        "sherpa": "sherpa jacket, plush fleece, streetwear luxury",
        "dress": "hooded dress, casual elegance, versatile styling",
        "bomber": "bomber jacket, satin finish, embroidered back panel",
        "windbreaker": "lightweight windbreaker, water resistant, retro athletic",
        "joggers": "jogger pants, tapered fit, side stripe detail",
        "beanie": "knit beanie, embroidered logo, cozy accessory",
    }

    def __init__(
        self,
        config: TrainingConfig | None = None,
        device: str = "auto",
        version_db_path: Path | None = None,
    ) -> None:
        """Initialize trainer.

        Args:
            config: Training configuration
            device: Device to use (auto, cuda, mps)
            version_db_path: Path to version tracking database (defaults to models/lora-versions.db)
        """
        self.config = config or TrainingConfig()
        self.device = self._resolve_device(device)

        # Initialize version tracker
        if version_db_path is None:
            version_db_path = Path("models/lora-versions.db")
        self.version_db_path = version_db_path
        self._version_tracker = None  # Lazy initialization

    async def get_version_tracker(self):
        """Get or initialize version tracker (lazy initialization).

        Returns:
            LoRAVersionTracker instance
        """
        if self._version_tracker is None:
            from imagery.lora_version_tracker import LoRAVersionTracker

            self._version_tracker = LoRAVersionTracker(self.version_db_path)
            await self._version_tracker.initialize()

        return self._version_tracker

    def _resolve_device(self, device: str) -> str:
        """Resolve the best available device."""
        if device != "auto":
            return device

        try:
            import torch

            if torch.cuda.is_available():
                return "cuda"
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return "mps"
        except ImportError:
            pass

        return "cpu"

    def _generate_caption(
        self,
        collection: str,
        garment_type: str = "",
        additional_details: str = "",
    ) -> str:
        """Generate training caption for image.

        Captions emphasize brand identity and collection aesthetics.
        """
        parts = [
            "SkyyRose luxury streetwear",
            self.COLLECTION_DESCRIPTIONS.get(collection.upper(), ""),
            self.GARMENT_DESCRIPTIONS.get(garment_type, garment_type) if garment_type else "",
            self.BRAND_DNA["aesthetic"],
            additional_details,
            "professional product photography, 8k, ultra detailed",
        ]

        return ", ".join(filter(None, parts))

    async def prepare_training_data(
        self,
        image_dirs: dict[str, Path],
        output_dir: Path | None = None,
        min_quality_score: float = 0.7,
    ) -> TrainingDataset:
        """Prepare training dataset from product images.

        Args:
            image_dirs: Mapping of collection names to image directories
            output_dir: Optional directory to copy and organize images
            min_quality_score: Minimum quality score to include (0-1)

        Returns:
            TrainingDataset ready for training
        """
        dataset = TrainingDataset()

        for collection, image_dir in image_dirs.items():
            if not image_dir.exists():
                logger.warning(f"Directory not found: {image_dir}")
                continue

            # Find images
            extensions = ("*.jpg", "*.jpeg", "*.png", "*.webp")
            images = []
            for ext in extensions:
                images.extend(image_dir.glob(f"**/{ext}"))

            logger.info(f"Found {len(images)} images in {collection}")

            for img_path in images:
                # Evaluate quality
                quality_score = await self._evaluate_image_quality(img_path)

                if quality_score < min_quality_score:
                    logger.debug(f"Skipping low quality image: {img_path.name}")
                    continue

                # Infer garment type from filename
                garment_type = self._infer_garment_type(img_path.name)

                # Generate caption
                caption = self._generate_caption(collection, garment_type)

                # Add to dataset
                training_img = TrainingImage(
                    path=img_path,
                    caption=caption,
                    collection=collection,
                    garment_type=garment_type,
                    quality_score=quality_score,
                )
                dataset.images.append(training_img)

                # Track collection counts
                dataset.collections[collection] = dataset.collections.get(collection, 0) + 1

        dataset.total_images = len(dataset.images)

        # Copy to output directory if specified
        if output_dir and dataset.images:
            await self._organize_training_images(dataset, output_dir)

        logger.info(
            f"Prepared dataset: {dataset.total_images} images "
            f"across {len(dataset.collections)} collections"
        )

        return dataset

    async def _evaluate_image_quality(self, image_path: Path) -> float:
        """Evaluate image quality for training suitability."""
        try:
            import cv2
            import numpy as np

            img = cv2.imread(str(image_path))
            if img is None:
                return 0.0

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            height, width = gray.shape

            # Blur detection
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            blur_score = min(1.0, laplacian_var / 500)

            # Resolution check
            resolution = width * height
            resolution_score = min(1.0, resolution / (1024 * 1024))

            # Brightness/exposure
            brightness = np.mean(gray)
            brightness_score = 1.0 - abs(brightness - 128) / 128

            # Overall score
            return blur_score * 0.4 + resolution_score * 0.3 + brightness_score * 0.3

        except Exception as e:
            logger.warning(f"Quality evaluation failed for {image_path}: {e}")
            return 0.5

    def _infer_garment_type(self, filename: str) -> str:
        """Infer garment type from filename."""
        filename_lower = filename.lower()

        for garment_type in self.GARMENT_DESCRIPTIONS:
            if garment_type in filename_lower:
                return garment_type

        return ""

    async def _organize_training_images(
        self,
        dataset: TrainingDataset,
        output_dir: Path,
    ) -> None:
        """Copy and organize images for training."""
        output_dir.mkdir(parents=True, exist_ok=True)

        for i, img in enumerate(dataset.images):
            collection_dir = output_dir / img.collection.lower()
            collection_dir.mkdir(exist_ok=True)

            # Copy image
            dest_path = collection_dir / f"{i:04d}_{img.path.name}"
            shutil.copy2(img.path, dest_path)

            # Write caption
            caption_path = dest_path.with_suffix(".txt")
            with open(caption_path, "w") as f:
                f.write(img.caption)

            # Update path in dataset
            img.path = dest_path

        # Save metadata
        dataset.save_metadata(output_dir / "dataset_metadata.json")

    async def train(
        self,
        dataset: TrainingDataset,
        resume_from_checkpoint: Path | None = None,
    ) -> Path:
        """Train LoRA on the prepared dataset.

        Args:
            dataset: Prepared training dataset
            resume_from_checkpoint: Optional checkpoint to resume from

        Returns:
            Path to trained LoRA weights
        """
        if not dataset.images:
            raise ValueError("Dataset is empty, cannot train")

        logger.info(
            f"Starting LoRA training on {dataset.total_images} images (device={self.device})"
        )

        try:
            import torch
            from accelerate import Accelerator
            from diffusers import StableDiffusionXLPipeline
            from peft import LoraConfig, get_peft_model
            from torch.utils.data import DataLoader

        except ImportError as e:
            raise ImportError(
                "Training dependencies not installed. Run: pip install peft accelerate transformers"
            ) from e

        # Initialize accelerator
        accelerator = Accelerator(
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            mixed_precision="fp16" if self.device == "cuda" else "no",
        )

        # Load base model
        logger.info("Loading base model...")
        dtype = torch.float16 if self.device == "cuda" else torch.float32

        pipeline = StableDiffusionXLPipeline.from_pretrained(
            self.config.base_model,
            torch_dtype=dtype,
            variant="fp16" if dtype == torch.float16 else None,
        )

        # Configure LoRA
        lora_config = LoraConfig(
            r=self.config.lora_rank,
            lora_alpha=self.config.lora_alpha,
            target_modules=self.config.target_modules,
            lora_dropout=self.config.lora_dropout,
            bias="none",
        )

        # Apply LoRA to UNet
        unet = pipeline.unet
        unet = get_peft_model(unet, lora_config)

        logger.info(f"LoRA parameters: {unet.print_trainable_parameters()}")

        # Prepare dataset and dataloader
        train_dataset = self._create_torch_dataset(dataset, pipeline.tokenizer)
        train_dataloader = DataLoader(
            train_dataset,
            batch_size=self.config.train_batch_size,
            shuffle=True,
        )

        # Optimizer
        optimizer = torch.optim.AdamW(
            unet.parameters(),
            lr=self.config.learning_rate,
        )

        # Learning rate scheduler
        from transformers import get_scheduler

        lr_scheduler = get_scheduler(
            self.config.lr_scheduler,
            optimizer=optimizer,
            num_warmup_steps=self.config.lr_warmup_steps,
            num_training_steps=len(train_dataloader) * self.config.num_epochs,
        )

        # Prepare with accelerator
        unet, optimizer, train_dataloader, lr_scheduler = accelerator.prepare(
            unet, optimizer, train_dataloader, lr_scheduler
        )

        # Resume from checkpoint if specified
        start_epoch = 0
        if resume_from_checkpoint:
            accelerator.load_state(str(resume_from_checkpoint))
            logger.info(f"Resumed from {resume_from_checkpoint}")

        # Training loop
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        global_step = 0

        for epoch in range(start_epoch, self.config.num_epochs):
            unet.train()
            epoch_loss = 0.0

            for step, batch in enumerate(train_dataloader):
                with accelerator.accumulate(unet):
                    # Training step (simplified)
                    loss = self._training_step(batch, unet, pipeline)

                    accelerator.backward(loss)
                    optimizer.step()
                    lr_scheduler.step()
                    optimizer.zero_grad()

                    epoch_loss += loss.item()
                    global_step += 1

                    if global_step % self.config.logging_steps == 0:
                        logger.info(
                            f"Epoch {epoch + 1}/{self.config.num_epochs}, "
                            f"Step {step + 1}/{len(train_dataloader)}, "
                            f"Loss: {loss.item():.4f}"
                        )

                    if global_step % self.config.save_steps == 0:
                        checkpoint_path = output_dir / f"checkpoint-{global_step}"
                        accelerator.save_state(str(checkpoint_path))

            avg_loss = epoch_loss / len(train_dataloader)
            logger.info(f"Epoch {epoch + 1} completed, Average Loss: {avg_loss:.4f}")

        # Save final model
        accelerator.wait_for_everyone()
        if accelerator.is_main_process:
            unet = accelerator.unwrap_model(unet)
            unet.save_pretrained(output_dir)

            # Save training metadata
            metadata = {
                "config": {
                    "base_model": self.config.base_model,
                    "lora_rank": self.config.lora_rank,
                    "lora_alpha": self.config.lora_alpha,
                    "num_epochs": self.config.num_epochs,
                    "learning_rate": self.config.learning_rate,
                },
                "dataset": {
                    "total_images": dataset.total_images,
                    "collections": dataset.collections,
                },
                "training_completed": datetime.utcnow().isoformat(),
            }

            with open(output_dir / "training_metadata.json", "w") as f:
                json.dump(metadata, f, indent=2)

        logger.info(f"Training complete! LoRA saved to: {output_dir}")
        return output_dir

    def _create_torch_dataset(self, dataset: TrainingDataset, tokenizer: Any) -> Any:
        """Create PyTorch dataset from training images."""
        from PIL import Image
        from torch.utils.data import Dataset
        from torchvision import transforms

        class SkyyRoseDataset(Dataset):
            def __init__(self, images: list[TrainingImage], tokenizer, resolution: int):
                self.images = images
                self.tokenizer = tokenizer
                self.transform = transforms.Compose(
                    [
                        transforms.Resize(
                            resolution, interpolation=transforms.InterpolationMode.BILINEAR
                        ),
                        transforms.CenterCrop(resolution),
                        transforms.ToTensor(),
                        transforms.Normalize([0.5], [0.5]),
                    ]
                )

            def __len__(self):
                return len(self.images)

            def __getitem__(self, idx):
                img_data = self.images[idx]
                image = Image.open(img_data.path).convert("RGB")
                image = self.transform(image)

                # Tokenize caption
                tokens = self.tokenizer(
                    img_data.caption,
                    padding="max_length",
                    max_length=77,
                    truncation=True,
                    return_tensors="pt",
                )

                return {
                    "pixel_values": image,
                    "input_ids": tokens.input_ids.squeeze(),
                }

        return SkyyRoseDataset(dataset.images, tokenizer, self.config.resolution)

    def _training_step(self, batch: dict, unet: Any, pipeline: Any) -> Any:
        """Single training step."""
        import torch

        # This is a simplified training step
        # Full implementation would include:
        # - Noise scheduling
        # - Latent encoding
        # - Text conditioning
        # - Loss computation

        pixel_values = batch["pixel_values"]
        input_ids = batch["input_ids"]

        # Encode images to latents
        with torch.no_grad():
            latents = pipeline.vae.encode(pixel_values).latent_dist.sample()
            latents = latents * pipeline.vae.config.scaling_factor

        # Add noise
        noise = torch.randn_like(latents)
        timesteps = torch.randint(
            0,
            pipeline.scheduler.config.num_train_timesteps,
            (latents.shape[0],),
            device=latents.device,
        )
        noisy_latents = pipeline.scheduler.add_noise(latents, noise, timesteps)

        # Get text embeddings
        with torch.no_grad():
            encoder_hidden_states = pipeline.text_encoder(input_ids)[0]

        # Predict noise
        noise_pred = unet(
            noisy_latents,
            timesteps,
            encoder_hidden_states=encoder_hidden_states,
        ).sample

        # MSE loss
        loss = torch.nn.functional.mse_loss(noise_pred, noise)

        return loss

    # =========================================================================
    # WooCommerce Integration Methods
    # =========================================================================

    async def prepare_from_woocommerce(
        self,
        collections: list[str] | None = None,
        min_quality_score: float = 0.7,
        max_products: int | None = None,
        woocommerce_url: str | None = None,
        consumer_key: str | None = None,
        consumer_secret: str | None = None,
    ) -> Any:  # ProductTrainingDataset
        """Prepare training data from WooCommerce products.

        Fetches products from WooCommerce, downloads images, evaluates quality,
        and prepares them for LoRA training.

        Args:
            collections: Filter by collections (BLACK_ROSE, LOVE_HURTS, SIGNATURE)
            min_quality_score: Minimum quality threshold (0.0-1.0)
            max_products: Maximum number of products to fetch
            woocommerce_url: WordPress URL (uses env var if None)
            consumer_key: WooCommerce consumer key (uses env var if None)
            consumer_secret: WooCommerce consumer secret (uses env var if None)

        Returns:
            ProductTrainingDataset ready for training

        Example:
            >>> trainer = SkyyRoseLoRATrainer()
            >>> dataset = await trainer.prepare_from_woocommerce(
            ...     collections=["BLACK_ROSE"],
            ...     max_products=50
            ... )
            >>> await trainer.train(dataset)
        """
        from imagery.product_training_dataset import (
            download_product_images,
            fetch_products_from_woocommerce,
            filter_by_quality,
            prepare_training_dataset,
        )

        logger.info(
            "Preparing training data from WooCommerce",
            extra={
                "collections": collections,
                "max_products": max_products,
                "min_quality": min_quality_score,
            },
        )

        # Step 1: Fetch products from WooCommerce
        logger.info("Step 1/4: Fetching products from WooCommerce...")
        products = await fetch_products_from_woocommerce(
            collections=collections,
            max_products=max_products,
            woocommerce_url=woocommerce_url,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
        )

        if not products:
            msg = "No products found matching criteria"
            raise ValueError(msg)

        logger.info(f"Fetched {len(products)} products")

        # Step 2: Download and cache images
        logger.info("Step 2/4: Downloading product images...")
        products = await download_product_images(products)

        total_images = sum(len(p.local_image_paths) for p in products)
        logger.info(f"Downloaded {total_images} images")

        # Step 3: Filter by quality
        logger.info("Step 3/4: Evaluating image quality...")
        products = await filter_by_quality(products, min_quality_score)

        if not products:
            msg = f"No products passed quality threshold {min_quality_score}"
            raise ValueError(msg)

        logger.info(f"{len(products)} products passed quality check")

        # Step 4: Prepare training dataset
        logger.info("Step 4/4: Preparing training dataset...")
        collection_filter = ",".join(collections) if collections else None
        dataset = prepare_training_dataset(
            products=products,
            collection_filter=collection_filter,
            version="v1.0.0",  # Will be updated by version tracker
        )

        logger.info(
            f"Dataset prepared: {dataset.total_images} images from {len(products)} products",
            extra={"collections": dataset.collections},
        )

        return dataset

    async def train_from_products(
        self,
        collections: list[str] | None = None,
        epochs: int = 100,
        max_products: int | None = None,
        min_quality_score: float = 0.7,
        version: str | None = None,
        resume_from: str | None = None,
        woocommerce_url: str | None = None,
        consumer_key: str | None = None,
        consumer_secret: str | None = None,
    ) -> Path:
        """End-to-end training from WooCommerce products.

        Fetches products, prepares dataset, trains LoRA, and saves metadata.

        Args:
            collections: Filter by collections (BLACK_ROSE, LOVE_HURTS, SIGNATURE)
            epochs: Number of training epochs
            max_products: Maximum number of products to use
            min_quality_score: Minimum quality threshold
            version: LoRA version (auto-increments if None)
            resume_from: Path to checkpoint to resume from
            woocommerce_url: WordPress URL (uses env var if None)
            consumer_key: WooCommerce consumer key (uses env var if None)
            consumer_secret: WooCommerce consumer secret (uses env var if None)

        Returns:
            Path to trained LoRA weights

        Example:
            >>> trainer = SkyyRoseLoRATrainer()
            >>> lora_path = await trainer.train_from_products(
            ...     collections=["BLACK_ROSE", "SIGNATURE"],
            ...     epochs=100,
            ...     max_products=50
            ... )
            >>> print(f"LoRA saved to: {lora_path}")
        """
        logger.info(
            "Starting end-to-end training from WooCommerce products",
            extra={
                "collections": collections,
                "epochs": epochs,
                "max_products": max_products,
                "version": version,
            },
        )

        # Step 1: Prepare dataset from WooCommerce
        dataset = await self.prepare_from_woocommerce(
            collections=collections,
            min_quality_score=min_quality_score,
            max_products=max_products,
            woocommerce_url=woocommerce_url,
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
        )

        # Step 2: Update config with epochs
        self.config.num_epochs = epochs

        # Step 3: Save dataset metadata
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        metadata_path = output_dir / "dataset_metadata.json"
        dataset.save_metadata(metadata_path)

        logger.info(f"Saved dataset metadata to {metadata_path}")

        # Step 4: Train LoRA
        logger.info(f"Starting training for {epochs} epochs...")
        await self.train(dataset, resume_from=resume_from)

        # Determine version (auto-increment if not specified)
        final_version = version or "v1.0.0"
        if version is None:
            # Auto-generate version from latest + 1
            tracker = await self.get_version_tracker()
            latest = await tracker.get_latest_version()
            if latest:
                # Simple patch version increment (v1.0.0 -> v1.0.1)
                import re

                match = re.match(r"v(\d+)\.(\d+)\.(\d+)", latest.version)
                if match:
                    major, minor, patch = map(int, match.groups())
                    final_version = f"v{major}.{minor}.{patch + 1}"
                else:
                    final_version = "v1.0.1"
            logger.info(f"Auto-generated version: {final_version}")

        # Step 5: Save product-enhanced metadata (JSON)
        training_metadata_path = output_dir / "training_metadata.json"
        self._save_product_training_metadata(
            dataset=dataset,
            metadata_path=training_metadata_path,
            version=final_version,
        )

        # Step 6: Save version to tracker (SQLite)
        await self._save_version_to_tracker(
            dataset=dataset,
            version=final_version,
        )

        logger.info(f"Training complete! LoRA saved to {output_dir} (version: {final_version})")

        return output_dir

    def _save_product_training_metadata(
        self,
        dataset: Any,  # ProductTrainingDataset
        metadata_path: Path,
        version: str,
    ) -> None:
        """Save enhanced metadata including product information.

        Args:
            dataset: ProductTrainingDataset with product tracking
            metadata_path: Path to save metadata JSON
            version: LoRA version string
        """
        # Build product metadata
        products_metadata = []
        for product in dataset.products:
            products_metadata.append(
                {
                    "sku": product.sku,
                    "name": product.name,
                    "product_id": product.product_id,
                    "collection": product.collection,
                    "garment_type": product.garment_type,
                    "images_used": len(product.local_image_paths),
                    "quality_score": product.quality_score,
                }
            )

        # Build complete metadata
        metadata = {
            "lora_version": version,
            "base_model": self.config.base_model,
            "training_config": {
                "resolution": self.config.resolution,
                "batch_size": self.config.train_batch_size,
                "epochs": self.config.num_epochs,
                "learning_rate": self.config.learning_rate,
                "lora_rank": self.config.lora_rank,
                "lora_alpha": self.config.lora_alpha,
            },
            "dataset": {
                "total_images": dataset.total_images,
                "total_products": len(dataset.products),
                "collections": dataset.collections,
            },
            "products": products_metadata,
            "training_started": dataset.woocommerce_sync_timestamp.isoformat(),
            "training_completed": datetime.now().isoformat(),
            "woocommerce_sync_timestamp": dataset.woocommerce_sync_timestamp.isoformat(),
        }

        # Save metadata
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Saved product training metadata to {metadata_path}")

    async def _save_version_to_tracker(
        self,
        dataset: Any,  # ProductTrainingDataset
        version: str,
    ) -> None:
        """Save version to SQLite version tracker.

        Args:
            dataset: ProductTrainingDataset with product tracking
            version: LoRA version string
        """
        logger.info(f"Saving version {version} to version tracker...")

        # Get version tracker
        tracker = await self.get_version_tracker()

        # Check if version already exists
        if await tracker.version_exists(version):
            logger.warning(f"Version {version} already exists, skipping tracker save")
            return

        # Build training config for tracker
        training_config = {
            "resolution": self.config.resolution,
            "batch_size": self.config.train_batch_size,
            "epochs": self.config.num_epochs,
            "learning_rate": self.config.learning_rate,
            "lora_rank": self.config.lora_rank,
            "lora_alpha": self.config.lora_alpha,
            "lr_scheduler": self.config.lr_scheduler,
            "lr_warmup_steps": self.config.lr_warmup_steps,
            "gradient_accumulation_steps": self.config.gradient_accumulation_steps,
        }

        # Save version
        await tracker.create_version(
            version=version,
            products=dataset.products,
            config=training_config,
            model_path=str(self.config.output_dir),
            base_model=self.config.base_model,
        )

        logger.info(f"Version {version} saved to tracker successfully")


__all__ = [
    "SkyyRoseLoRATrainer",
    "TrainingConfig",
    "TrainingDataset",
    "TrainingImage",
]
