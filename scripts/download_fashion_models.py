#!/usr/bin/env python3
"""
DevSkyy Fashion Orchestrator - Model Downloader
Version: 3.0.0-fashion
Updated: 2025-11-21

Downloads AI models and SDKs for The Skyy Rose Collection Fashion Orchestrator
Per Truth Protocol Rule #1 - All sources verified
"""

import argparse
import logging
import os
from pathlib import Path
import sys


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FashionModelDownloader:
    """Download and cache fashion AI models"""

    def __init__(self, cache_dir: str | None = None):
        """Initialize model downloader"""
        self.cache_dir = Path(cache_dir) if cache_dir else Path.home() / ".cache" / "devskyy" / "models"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Model cache directory: {self.cache_dir}")

    def download_huggingface_model(self, model_id: str, model_type: str = "diffusion") -> bool:
        """
        Download model from Hugging Face.

        Args:
            model_id: Hugging Face model ID (e.g., "yisol/IDM-VTON")
            model_type: Type of model ("diffusion", "transformers", etc.)

        Returns:
            bool: True if successful
        """
        try:
            logger.info(f"Downloading {model_id} from Hugging Face...")

            if model_type == "diffusion":
                from diffusers import DiffusionPipeline

                # Download diffusion model
                pipeline = DiffusionPipeline.from_pretrained(
                    model_id,
                    cache_dir=self.cache_dir,
                    torch_dtype="auto",
                )

                logger.info(f"✓ Downloaded {model_id} (diffusion)")
                return True

            elif model_type == "transformers":
                from transformers import AutoModel, AutoTokenizer

                # Download transformer model
                model = AutoModel.from_pretrained(
                    model_id,
                    cache_dir=self.cache_dir,
                )

                tokenizer = AutoTokenizer.from_pretrained(
                    model_id,
                    cache_dir=self.cache_dir,
                )

                logger.info(f"✓ Downloaded {model_id} (transformers)")
                return True

            else:
                logger.error(f"Unsupported model type: {model_type}")
                return False

        except Exception as e:
            logger.error(f"✗ Failed to download {model_id}: {e}")
            return False

    def download_idm_vton(self) -> bool:
        """
        Download IDM-VTON model for virtual try-on.

        Source: https://huggingface.co/yisol/IDM-VTON
        Paper: https://arxiv.org/abs/2403.05139
        """
        logger.info("=" * 70)
        logger.info("IDM-VTON - Virtual Try-On Model")
        logger.info("Source: https://huggingface.co/yisol/IDM-VTON")
        logger.info("Paper: https://arxiv.org/abs/2403.05139")
        logger.info("=" * 70)

        return self.download_huggingface_model("yisol/IDM-VTON", "diffusion")

    def download_stable_diffusion_xl(self) -> bool:
        """
        Download Stable Diffusion XL for image generation.

        Source: https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0
        """
        logger.info("=" * 70)
        logger.info("Stable Diffusion XL - Image Generation")
        logger.info("Source: https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0")
        logger.info("=" * 70)

        return self.download_huggingface_model(
            "stabilityai/stable-diffusion-xl-base-1.0",
            "diffusion"
        )

    def download_controlnet(self) -> bool:
        """
        Download ControlNet for pose guidance.

        Source: https://huggingface.co/lllyasviel/control_v11p_sd15_openpose
        """
        logger.info("=" * 70)
        logger.info("ControlNet - Pose Guidance")
        logger.info("Source: https://huggingface.co/lllyasviel/control_v11p_sd15_openpose")
        logger.info("=" * 70)

        return self.download_huggingface_model(
            "lllyasviel/control_v11p_sd15_openpose",
            "diffusion"
        )

    def verify_pytorch(self) -> bool:
        """Verify PyTorch installation"""
        try:
            import torch

            logger.info("=" * 70)
            logger.info("PyTorch Verification")
            logger.info("=" * 70)
            logger.info(f"PyTorch version: {torch.__version__}")
            logger.info(f"CUDA available: {torch.cuda.is_available()}")

            if torch.cuda.is_available():
                logger.info(f"CUDA version: {torch.version.cuda}")
                logger.info(f"GPU device: {torch.cuda.get_device_name(0)}")
                logger.info(f"GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
            else:
                logger.warning("⚠ CUDA not available - models will run on CPU (slower)")

            return True

        except ImportError:
            logger.error("✗ PyTorch not installed")
            return False

    def verify_api_keys(self) -> dict[str, bool]:
        """Verify API keys are configured (never logs actual key values)"""
        logger.info("=" * 70)
        logger.info("API Key Verification")
        logger.info("=" * 70)

        # List of API key environment variable names to check
        api_key_names = [
            "ANTHROPIC_API_KEY",
            "OPENAI_API_KEY",
            "STABILITY_API_KEY",
            "REPLICATE_API_TOKEN",
            "HUGGINGFACE_TOKEN",
        ]

        results = {}
        for key_name in api_key_names:
            # Retrieve key value only to check existence, never log it
            # Only the key name is logged, never the actual sensitive value
            key_value = os.getenv(key_name)
            is_configured = key_value is not None and len(key_value) > 0

            if is_configured:
                # Security: Only log the key name, never the value
                logger.info(f"✓ {key_name} configured")
                results[key_name] = True
            else:
                logger.warning(f"⚠ {key_name} not set (required for {key_name.split('_')[0]} models)")
                results[key_name] = False

        return results

    def download_all_models(self) -> dict[str, bool]:
        """Download all fashion models"""
        logger.info("\n" + "=" * 70)
        logger.info("DOWNLOADING ALL FASHION MODELS")
        logger.info("=" * 70 + "\n")

        results = {}

        # Verify PyTorch first
        if not self.verify_pytorch():
            logger.error("PyTorch verification failed. Install PyTorch first.")
            sys.exit(1)

        # Verify API keys
        self.verify_api_keys()

        # Download models
        models = [
            ("IDM-VTON", self.download_idm_vton),
            ("Stable Diffusion XL", self.download_stable_diffusion_xl),
            ("ControlNet", self.download_controlnet),
        ]

        for model_name, download_func in models:
            logger.info(f"\n{'=' * 70}")
            logger.info(f"Downloading {model_name}...")
            logger.info('=' * 70)

            try:
                success = download_func()
                results[model_name] = success

                if success:
                    logger.info(f"✓ {model_name} downloaded successfully")
                else:
                    logger.error(f"✗ {model_name} download failed")

            except Exception as e:
                logger.error(f"✗ {model_name} download failed: {e}")
                results[model_name] = False

        return results

    def print_summary(self, results: dict[str, bool]):
        """Print download summary"""
        logger.info("\n" + "=" * 70)
        logger.info("DOWNLOAD SUMMARY")
        logger.info("=" * 70)

        total = len(results)
        successful = sum(1 for v in results.values() if v)
        failed = total - successful

        for model_name, success in results.items():
            status = "✓" if success else "✗"
            logger.info(f"{status} {model_name}")

        logger.info("=" * 70)
        logger.info(f"Total: {total} | Successful: {successful} | Failed: {failed}")
        logger.info("=" * 70)

        if failed > 0:
            logger.warning(f"\n⚠ {failed} model(s) failed to download")
            logger.info("Check the logs above for error details")
        else:
            logger.info("\n✓ All models downloaded successfully!")

        logger.info(f"\nModels cached in: {self.cache_dir}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Download AI models for DevSkyy Fashion Orchestrator"
    )

    parser.add_argument(
        "--cache-dir",
        type=str,
        help="Custom cache directory for models",
        default=None
    )

    parser.add_argument(
        "--model",
        type=str,
        choices=["idm-vton", "sdxl", "controlnet", "all"],
        default="all",
        help="Specific model to download (default: all)"
    )

    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify installations without downloading"
    )

    args = parser.parse_args()

    # Banner
    print("\n" + "=" * 70)
    print("DevSkyy Fashion Orchestrator - Model Downloader")
    print("The Skyy Rose Collection")
    print("=" * 70 + "\n")

    # Initialize downloader
    downloader = FashionModelDownloader(cache_dir=args.cache_dir)

    # Verify only mode
    if args.verify_only:
        downloader.verify_pytorch()
        downloader.verify_api_keys()
        sys.exit(0)

    # Download specific model or all
    if args.model == "all":
        results = downloader.download_all_models()
        downloader.print_summary(results)
    elif args.model == "idm-vton":
        success = downloader.download_idm_vton()
        sys.exit(0 if success else 1)
    elif args.model == "sdxl":
        success = downloader.download_stable_diffusion_xl()
        sys.exit(0 if success else 1)
    elif args.model == "controlnet":
        success = downloader.download_controlnet()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
