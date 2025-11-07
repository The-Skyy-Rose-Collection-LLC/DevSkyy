# HuggingFace Best Practices for DevSkyy Platform

Enterprise-grade implementation patterns for HuggingFace models in production.

## Table of Contents
1. [Model Loading and Caching](#model-loading-and-caching)
2. [Model Quantization (8-bit/4-bit)](#model-quantization-8-bit4-bit)
3. [CLIP Image Embeddings](#clip-image-embeddings)
4. [Validation and Error Handling](#validation-and-error-handling)
5. [Performance Optimization](#performance-optimization)

---

## Model Loading and Caching

### Best Practice: Use Model Registry

```python
from ml.model_registry import ModelRegistry

registry = ModelRegistry()
model = registry.get_model("clip-vit-base")
```

### Cache Models Locally

```python
import os
from transformers import CLIPVisionModel, CLIPImageProcessor

# Set cache directory
os.environ["HF_HOME"] = "/app/.cache/huggingface"
os.environ["TRANSFORMERS_CACHE"] = "/app/.cache/transformers"

# Models will be cached here
model = CLIPVisionModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPImageProcessor.from_pretrained("openai/clip-vit-base-patch32")
```


---

## Model Quantization (8-bit/4-bit)

### Correct Quantization Patterns for Diffusers Pipelines

**⚠️ IMPORTANT:** Do NOT pass `BitsAndBytesConfig` directly to pipeline `from_pretrained()`. Use one of the correct patterns below.

---

### ✅ Pattern 1: PipelineQuantizationConfig (Recommended - Diffusers 0.30+)

Use `PipelineQuantizationConfig` with `quant_backend` set to `"bitsandbytes_8bit"` or `"bitsandbytes_4bit"`:

```python
"""
Correct Stable Diffusion XL Quantization - Method 1
Uses diffusers' PipelineQuantizationConfig
"""

import torch
from diffusers import StableDiffusionXLPipeline, PipelineQuantizationConfig
from core.exceptions import MLError
import logging

logger = logging.getLogger(__name__)


def load_sdxl_pipeline_with_quantization_v1(
    model_id: str = "stabilityai/stable-diffusion-xl-base-1.0",
    use_4bit: bool = True,
    device: str = "cuda"
) -> StableDiffusionXLPipeline:
    """
    Load SDXL pipeline with proper quantization using PipelineQuantizationConfig.

    Args:
        model_id: HuggingFace model identifier
        use_4bit: Use 4-bit quantization (True) or 8-bit (False)
        device: Device to load on

    Returns:
        Quantized SDXL pipeline

    Raises:
        MLError: If pipeline loading fails
    """
    try:
        # ✅ CORRECT: Create PipelineQuantizationConfig
        quant_backend = "bitsandbytes_4bit" if use_4bit else "bitsandbytes_8bit"
        
        # Configure quantization parameters
        quant_config = PipelineQuantizationConfig(
            quant_backend=quant_backend,
            quant_kwargs={
                # BitsAndBytes parameters go in quant_kwargs
                "load_in_4bit": use_4bit,
                "load_in_8bit": not use_4bit,
                "bnb_4bit_compute_dtype": torch.float16,
                "bnb_4bit_quant_type": "nf4",
                "bnb_4bit_use_double_quant": True,
            }
        )

        # ✅ CORRECT: Pass quantization_config to from_pretrained
        pipeline = StableDiffusionXLPipeline.from_pretrained(
            model_id,
            quantization_config=quant_config,  # ✅ Use quantization_config parameter
            torch_dtype=torch.float16,         # Keep torch_dtype as before
            use_safetensors=True,
            variant="fp16"
        )

        pipeline = pipeline.to(device)
        logger.info(f"✅ SDXL pipeline loaded with {quant_backend} quantization")
        
        return pipeline

    except Exception as e:
        raise MLError(
            f"Failed to load SDXL pipeline with quantization",
            details={
                "model_id": model_id,
                "quant_backend": quant_backend,
                "device": device
            },
            original_error=e
        )
```

---

### ✅ Pattern 2: Component-Level Quantization

Quantize individual pipeline components (UNet, VAE, text encoders) separately:

```python
"""
Correct Stable Diffusion XL Quantization - Method 2
Quantize components individually, then build pipeline
"""

import torch
from diffusers import (
    StableDiffusionXLPipeline,
    UNet2DConditionModel,
    AutoencoderKL,
)
from transformers import (
    CLIPTextModel,
    CLIPTextModelWithProjection,
    CLIPTokenizer,
    BitsAndBytesConfig  # ✅ Only for individual components
)
from core.exceptions import MLError
import logging

logger = logging.getLogger(__name__)


def load_sdxl_pipeline_with_quantization_v2(
    model_id: str = "stabilityai/stable-diffusion-xl-base-1.0",
    quantize_unet: bool = True,
    quantize_text_encoders: bool = True,
    use_4bit: bool = True,
    device: str = "cuda"
) -> StableDiffusionXLPipeline:
    """
    Load SDXL pipeline with component-level quantization.

    This approach gives fine-grained control over which components
    are quantized and their settings.

    Args:
        model_id: HuggingFace model identifier
        quantize_unet: Quantize the UNet model
        quantize_text_encoders: Quantize CLIP text encoders
        use_4bit: Use 4-bit (True) or 8-bit (False) quantization
        device: Device to load on

    Returns:
        SDXL pipeline with quantized components

    Raises:
        MLError: If loading fails
    """
    try:
        # ✅ CORRECT: Create BitsAndBytesConfig for individual components
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=use_4bit,
            load_in_8bit=not use_4bit,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
        )

        # Load components individually with quantization
        components = {}

        # 1. UNet (main diffusion model)
        if quantize_unet:
            logger.info("Loading quantized UNet...")
            components["unet"] = UNet2DConditionModel.from_pretrained(
                model_id,
                subfolder="unet",
                quantization_config=bnb_config,  # ✅ Per-component quantization
                torch_dtype=torch.float16
            )
        else:
            components["unet"] = UNet2DConditionModel.from_pretrained(
                model_id,
                subfolder="unet",
                torch_dtype=torch.float16
            ).to(device)

        # 2. VAE (usually not quantized for quality)
        logger.info("Loading VAE (not quantized)...")
        components["vae"] = AutoencoderKL.from_pretrained(
            model_id,
            subfolder="vae",
            torch_dtype=torch.float16
        ).to(device)

        # 3. Text Encoder 1
        if quantize_text_encoders:
            logger.info("Loading quantized Text Encoder 1...")
            components["text_encoder"] = CLIPTextModel.from_pretrained(
                model_id,
                subfolder="text_encoder",
                quantization_config=bnb_config,  # ✅ Per-component quantization
                torch_dtype=torch.float16
            )
        else:
            components["text_encoder"] = CLIPTextModel.from_pretrained(
                model_id,
                subfolder="text_encoder",
                torch_dtype=torch.float16
            ).to(device)

        # 4. Text Encoder 2 (SDXL has two)
        if quantize_text_encoders:
            logger.info("Loading quantized Text Encoder 2...")
            components["text_encoder_2"] = CLIPTextModelWithProjection.from_pretrained(
                model_id,
                subfolder="text_encoder_2",
                quantization_config=bnb_config,  # ✅ Per-component quantization
                torch_dtype=torch.float16
            )
        else:
            components["text_encoder_2"] = CLIPTextModelWithProjection.from_pretrained(
                model_id,
                subfolder="text_encoder_2",
                torch_dtype=torch.float16
            ).to(device)

        # 5. Tokenizers (never quantized)
        logger.info("Loading tokenizers...")
        components["tokenizer"] = CLIPTokenizer.from_pretrained(
            model_id,
            subfolder="tokenizer"
        )
        components["tokenizer_2"] = CLIPTokenizer.from_pretrained(
            model_id,
            subfolder="tokenizer_2"
        )

        # 6. Load scheduler config
        from diffusers import DDIMScheduler
        components["scheduler"] = DDIMScheduler.from_pretrained(
            model_id,
            subfolder="scheduler"
        )

        # ✅ CORRECT: Construct pipeline with quantized components
        pipeline = StableDiffusionXLPipeline(**components)

        logger.info(
            f"✅ SDXL pipeline constructed with quantized components "
            f"(UNet: {quantize_unet}, Text Encoders: {quantize_text_encoders})"
        )

        return pipeline

    except Exception as e:
        raise MLError(
            f"Failed to load SDXL pipeline with component-level quantization",
            details={
                "model_id": model_id,
                "quantize_unet": quantize_unet,
                "quantize_text_encoders": quantize_text_encoders,
                "use_4bit": use_4bit
            },
            original_error=e
        )
```

---

### ❌ WRONG: Direct BitsAndBytesConfig to Pipeline

**DO NOT DO THIS - It will fail or be ignored:**

```python
# ❌ INCORRECT - This does NOT work
from transformers import BitsAndBytesConfig
from diffusers import StableDiffusionXLPipeline

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.float16
)

# ❌ WRONG: Cannot pass BitsAndBytesConfig directly
pipeline = StableDiffusionXLPipeline.from_pretrained(
    model_id,
    quantization_config=bnb_config,  # ❌ Wrong! This is transformers config
    torch_dtype=torch.float16
)
# This will either fail or silently ignore quantization
```

**Why this fails:**
- `BitsAndBytesConfig` is from **transformers** library
- `StableDiffusionXLPipeline` is from **diffusers** library
- They use different quantization interfaces
- Must use `PipelineQuantizationConfig` (Pattern 1) or component-level (Pattern 2)

---

### Memory Usage Comparison

| Configuration | VRAM Usage (SDXL) | Quality | Speed |
|---------------|-------------------|---------|-------|
| FP32 (no quant) | ~24 GB | Best | Slowest |
| FP16 (no quant) | ~12 GB | Excellent | Fast |
| 8-bit quantization | ~8 GB | Very Good | Medium |
| 4-bit quantization | ~6 GB | Good | Faster |
| 4-bit + double quant | ~5 GB | Good | Fastest |

**Recommendation:**
- Use **Pattern 1** (PipelineQuantizationConfig) for simplicity
- Use **Pattern 2** (component-level) for fine-grained control
- 4-bit quantization is good for most use cases
- Keep VAE unquantized for better image quality

---

### Complete Usage Example

```python
"""
Production usage with error handling and validation
"""

from typing import Optional
import torch
from core.exceptions import MLError, ValidationError
import logging

logger = logging.getLogger(__name__)


class QuantizedSDXLGenerator:
    """Production SDXL generator with quantization support."""

    def __init__(
        self,
        model_id: str = "stabilityai/stable-diffusion-xl-base-1.0",
        use_quantization: bool = True,
        use_4bit: bool = True,
        device: Optional[str] = None
    ):
        """
        Initialize SDXL generator with optional quantization.

        Args:
            model_id: HuggingFace model ID
            use_quantization: Enable quantization to save VRAM
            use_4bit: Use 4-bit (True) or 8-bit (False) quantization
            device: Device to use (auto-detected if None)
        """
        self.model_id = model_id
        self.device = device or self._detect_device()
        self.use_quantization = use_quantization
        self.use_4bit = use_4bit

        # Load pipeline with appropriate method
        if use_quantization:
            logger.info(f"Loading SDXL with {'4-bit' if use_4bit else '8-bit'} quantization")
            self.pipeline = load_sdxl_pipeline_with_quantization_v1(
                model_id=model_id,
                use_4bit=use_4bit,
                device=self.device
            )
        else:
            logger.info("Loading SDXL without quantization")
            from diffusers import StableDiffusionXLPipeline
            self.pipeline = StableDiffusionXLPipeline.from_pretrained(
                model_id,
                torch_dtype=torch.float16,
                use_safetensors=True,
                variant="fp16"
            ).to(self.device)

        self.pipeline.enable_attention_slicing()
        logger.info(f"✅ SDXL pipeline ready on {self.device}")

    def _detect_device(self) -> str:
        """Detect best available device."""
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"

    def generate(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        num_inference_steps: int = 30,
        guidance_scale: float = 7.5,
        width: int = 1024,
        height: int = 1024,
        seed: Optional[int] = None
    ) -> torch.Tensor:
        """
        Generate image with SDXL.

        Args:
            prompt: Text prompt
            negative_prompt: Negative prompt
            num_inference_steps: Number of denoising steps
            guidance_scale: Guidance scale (higher = more faithful to prompt)
            width: Image width (multiples of 64)
            height: Image height (multiples of 64)
            seed: Random seed for reproducibility

        Returns:
            Generated image tensor

        Raises:
            ValidationError: If inputs are invalid
            MLError: If generation fails
        """
        # Validate inputs
        if not prompt or not isinstance(prompt, str):
            raise ValidationError(
                "prompt must be a non-empty string",
                details={"provided": type(prompt).__name__}
            )

        if width % 64 != 0 or height % 64 != 0:
            raise ValidationError(
                "width and height must be multiples of 64",
                details={"width": width, "height": height}
            )

        try:
            # Set seed for reproducibility
            generator = None
            if seed is not None:
                generator = torch.Generator(device=self.device).manual_seed(seed)

            # Generate image
            with torch.inference_mode():
                output = self.pipeline(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    num_inference_steps=num_inference_steps,
                    guidance_scale=guidance_scale,
                    width=width,
                    height=height,
                    generator=generator
                )

            return output.images[0]

        except Exception as e:
            raise MLError(
                "Failed to generate image with SDXL",
                details={
                    "prompt": prompt[:100],  # Truncate for logging
                    "width": width,
                    "height": height,
                    "quantization": self.use_quantization
                },
                original_error=e
            )


# Usage example
if __name__ == "__main__":
    # Initialize with 4-bit quantization (saves ~6GB VRAM)
    generator = QuantizedSDXLGenerator(
        use_quantization=True,
        use_4bit=True
    )

    # Generate image
    image = generator.generate(
        prompt="A majestic mountain landscape at sunset, cinematic lighting",
        negative_prompt="blurry, low quality, distorted",
        num_inference_steps=30,
        seed=42
    )

    # Save
    image.save("output.png")
```

---

### Production Checklist: Quantization

✅ **Configuration:**
- [ ] Use `PipelineQuantizationConfig` for simple quantization
- [ ] OR use component-level quantization for fine control
- [ ] Never pass `BitsAndBytesConfig` directly to pipeline
- [ ] Keep `torch_dtype=torch.float16` for computation

✅ **Components:**
- [ ] Quantize UNet (largest component, biggest savings)
- [ ] Quantize text encoders (moderate savings)
- [ ] Keep VAE unquantized (quality preservation)
- [ ] Never quantize tokenizers/schedulers

✅ **Quality vs Performance:**
- [ ] 4-bit for maximum VRAM savings (~6GB for SDXL)
- [ ] 8-bit for better quality (~8GB for SDXL)
- [ ] FP16 for best quality (~12GB for SDXL)
- [ ] Test quality on your use case

✅ **Error Handling:**
- [ ] Wrap loading in try-except
- [ ] Log quantization settings
- [ ] Validate VRAM availability
- [ ] Fallback to FP16 if quantization fails



---

## CLIP Image Embeddings

### Correct Implementation (Using Transformers)

**✅ DO: Use CLIPVisionModel and CLIPImageProcessor from transformers**

```python
"""
CLIP Image Embedding - Production Implementation
Uses transformers library (NOT diffusers) for proper CLIP usage
"""

import torch
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from PIL import Image
import logging

from transformers import CLIPVisionModel, CLIPImageProcessor
from core.exceptions import ValidationError, MLError, FileNotFoundError

logger = logging.getLogger(__name__)


class CLIPImageEmbedder:
    """
    Production-ready CLIP image embedder using transformers library.

    Features:
    - Proper CLIP model usage (CLIPVisionModel, not diffusers)
    - Defensive validation of inputs
    - Clear error messages
    - Type hints and documentation
    - Batch processing support
    """

    def __init__(
        self,
        model_name: str = "openai/clip-vit-base-patch32",
        device: Optional[str] = None,
        cache_dir: Optional[str] = None
    ):
        """
        Initialize CLIP image embedder.

        Args:
            model_name: HuggingFace model identifier
            device: Device to use (cuda, cpu, mps). Auto-detected if None.
            cache_dir: Directory to cache models

        Raises:
            MLError: If model loading fails
        """
        self.model_name = model_name
        self.device = device or self._detect_device()
        self.cache_dir = cache_dir

        try:
            # Load CLIP vision model (correct approach)
            self.model = CLIPVisionModel.from_pretrained(
                model_name,
                cache_dir=cache_dir
            ).to(self.device)
            self.model.eval()  # Set to evaluation mode

            # Load image processor
            self.processor = CLIPImageProcessor.from_pretrained(
                model_name,
                cache_dir=cache_dir
            )

            logger.info(f"✅ CLIP model loaded: {model_name} on {self.device}")

        except Exception as e:
            raise MLError(
                f"Failed to load CLIP model: {model_name}",
                details={"model": model_name, "device": self.device},
                original_error=e
            )

    def _detect_device(self) -> str:
        """Detect best available device."""
        if torch.cuda.is_available():
            return "cuda"
        elif torch.backends.mps.is_available():
            return "mps"
        else:
            return "cpu"

    def _load_image(self, image_input: Union[str, Path, Image.Image]) -> Image.Image:
        """
        Load image from various input types.

        Args:
            image_input: Path string, Path object, or PIL Image

        Returns:
            PIL Image

        Raises:
            FileNotFoundError: If image file doesn't exist
            ValidationError: If image cannot be loaded
        """
        if isinstance(image_input, Image.Image):
            return image_input

        image_path = Path(image_input)

        if not image_path.exists():
            raise FileNotFoundError(
                f"Image file not found: {image_path}",
                details={"path": str(image_path)}
            )

        try:
            image = Image.open(image_path).convert("RGB")
            return image
        except Exception as e:
            raise ValidationError(
                f"Failed to load image: {image_path}",
                details={"path": str(image_path)},
                original_error=e
            )

    def _encode_with_clip(
        self,
        processed_tensors: Dict[str, torch.Tensor]
    ) -> torch.Tensor:
        """
        Encode processed image tensors with CLIP.

        Args:
            processed_tensors: Dict containing 'pixel_values' tensor
                              from CLIPImageProcessor

        Returns:
            Image embeddings tensor of shape (batch_size, embedding_dim)

        Raises:
            ValidationError: If input tensors are invalid
            MLError: If encoding fails
        """
        # Validate input
        if not isinstance(processed_tensors, dict):
            raise ValidationError(
                "processed_tensors must be a dictionary",
                details={"type": type(processed_tensors).__name__}
            )

        if "pixel_values" not in processed_tensors:
            raise ValidationError(
                "processed_tensors must contain 'pixel_values' key",
                details={"keys": list(processed_tensors.keys())}
            )

        pixel_values = processed_tensors["pixel_values"]

        if not isinstance(pixel_values, torch.Tensor):
            raise ValidationError(
                "pixel_values must be a torch.Tensor",
                details={"type": type(pixel_values).__name__}
            )

        try:
            # Move tensors to device
            pixel_values = pixel_values.to(self.device)

            # Encode with CLIP (no gradients needed)
            with torch.no_grad():
                outputs = self.model(pixel_values=pixel_values)
                embeddings = outputs.last_hidden_state[:, 0, :]  # CLS token

                # Normalize embeddings (CLIP standard practice)
                embeddings = embeddings / embeddings.norm(dim=-1, keepdim=True)

            return embeddings

        except Exception as e:
            raise MLError(
                "Failed to encode images with CLIP",
                details={
                    "tensor_shape": pixel_values.shape,
                    "device": self.device
                },
                original_error=e
            )

    def encode_image(
        self,
        image_input: Union[str, Path, Image.Image]
    ) -> torch.Tensor:
        """
        Encode a single image to CLIP embedding.

        Args:
            image_input: Image path or PIL Image

        Returns:
            Embedding tensor of shape (1, embedding_dim)

        Raises:
            FileNotFoundError: If image file doesn't exist
            ValidationError: If image is invalid
            MLError: If encoding fails
        """
        # Load image
        image = self._load_image(image_input)

        # Process image with CLIP processor
        inputs = self.processor(images=image, return_tensors="pt")

        # Encode
        embedding = self._encode_with_clip(inputs)

        return embedding

    def encode_images_batch(
        self,
        image_inputs: List[Union[str, Path, Image.Image]],
        batch_size: int = 32
    ) -> torch.Tensor:
        """
        Encode multiple images in batches.

        Args:
            image_inputs: List of image paths or PIL Images
            batch_size: Number of images to process at once

        Returns:
            Embeddings tensor of shape (num_images, embedding_dim)

        Raises:
            ValidationError: If image_inputs is invalid
            MLError: If encoding fails
        """
        if not isinstance(image_inputs, list):
            raise ValidationError(
                "image_inputs must be a list",
                details={"type": type(image_inputs).__name__}
            )

        if len(image_inputs) == 0:
            raise ValidationError("image_inputs cannot be empty")

        all_embeddings = []

        for i in range(0, len(image_inputs), batch_size):
            batch = image_inputs[i:i + batch_size]

            # Load images
            images = [self._load_image(img) for img in batch]

            # Process batch
            inputs = self.processor(images=images, return_tensors="pt")

            # Encode batch
            embeddings = self._encode_with_clip(inputs)
            all_embeddings.append(embeddings)

        # Concatenate all batches
        return torch.cat(all_embeddings, dim=0)


# ============================================================================
# VALIDATION LOOP WITH DEFENSIVE CODING
# ============================================================================

def validate_image_embeddings(
    image_set: Dict[str, Any],
    embedder: CLIPImageEmbedder,
    validation_threshold: float = 0.8
) -> Dict[str, Any]:
    """
    Validate image embeddings with defensive coding and clear error handling.

    **Expected image_set Schema:**
    ```python
    {
        "images": [
            {"path": "/path/to/image1.jpg"},
            {"path": "/path/to/image2.jpg", "label": "cat"},
            {"image": PIL.Image.Image(), "id": "img_001"}
        ],
        "metadata": {  # Optional
            "dataset_name": "validation_set",
            "version": "1.0"
        }
    }
    ```

    Each image dict must contain either:
    - "path": str - Path to image file
    - "image": PIL.Image - PIL Image object

    Args:
        image_set: Dictionary containing "images" list and optional metadata
        embedder: CLIPImageEmbedder instance
        validation_threshold: Minimum similarity threshold

    Returns:
        Validation results dictionary with embeddings and metrics

    Raises:
        ValidationError: If image_set schema is invalid
        FileNotFoundError: If image file doesn't exist
        MLError: If embedding generation fails
    """
    # ========================================================================
    # DEFENSIVE VALIDATION: Check image_set structure
    # ========================================================================

    if not isinstance(image_set, dict):
        raise ValidationError(
            "image_set must be a dictionary",
            details={
                "type": type(image_set).__name__,
                "expected": "dict with 'images' key"
            }
        )

    if "images" not in image_set:
        raise ValidationError(
            "image_set must contain 'images' key",
            details={
                "keys": list(image_set.keys()),
                "expected_schema": {
                    "images": "list of image dicts",
                    "metadata": "optional metadata dict"
                }
            }
        )

    images_list = image_set.get("images")

    if not isinstance(images_list, list):
        raise ValidationError(
            "image_set['images'] must be a list",
            details={
                "type": type(images_list).__name__,
                "expected": "list of dicts with 'path' or 'image' keys"
            }
        )

    if len(images_list) == 0:
        raise ValidationError(
            "image_set['images'] cannot be empty",
            details={"provided_count": 0}
        )

    # ========================================================================
    # VALIDATION LOOP: Process each image with error tracking
    # ========================================================================

    results = {
        "total_images": len(images_list),
        "successful": 0,
        "failed": 0,
        "embeddings": [],
        "errors": [],
        "metadata": image_set.get("metadata", {})
    }

    logger.info(f"Starting validation of {len(images_list)} images")

    for idx, image_dict in enumerate(images_list):
        # Validate each image dictionary
        if not isinstance(image_dict, dict):
            error_msg = f"Image at index {idx} is not a dictionary"
            results["errors"].append({
                "index": idx,
                "error": error_msg,
                "type": type(image_dict).__name__
            })
            results["failed"] += 1
            logger.warning(error_msg)
            continue

        # Check for required keys
        has_path = "path" in image_dict
        has_image = "image" in image_dict

        if not has_path and not has_image:
            error_msg = f"Image at index {idx} missing 'path' or 'image' key"
            results["errors"].append({
                "index": idx,
                "error": error_msg,
                "keys": list(image_dict.keys())
            })
            results["failed"] += 1
            logger.warning(error_msg)
            continue

        # Extract image input
        try:
            if has_path:
                image_input = image_dict["path"]
                image_id = image_dict.get("id", f"image_{idx}")
            else:
                image_input = image_dict["image"]
                image_id = image_dict.get("id", f"image_{idx}")

            # Generate embedding
            embedding = embedder.encode_image(image_input)

            # Store result
            results["embeddings"].append({
                "id": image_id,
                "index": idx,
                "embedding": embedding,
                "shape": tuple(embedding.shape),
                "label": image_dict.get("label"),
                "metadata": {k: v for k, v in image_dict.items()
                           if k not in ["path", "image", "id", "label"]}
            })
            results["successful"] += 1

            logger.debug(f"✅ Encoded image {idx}: {image_id}")

        except (FileNotFoundError, ValidationError, MLError) as e:
            # Expected errors - log and continue
            error_msg = f"Failed to process image at index {idx}: {str(e)}"
            results["errors"].append({
                "index": idx,
                "error": str(e),
                "error_type": type(e).__name__,
                "image_id": image_dict.get("id", "unknown")
            })
            results["failed"] += 1
            logger.warning(error_msg)

        except Exception as e:
            # Unexpected errors - log and continue
            error_msg = f"Unexpected error at index {idx}: {str(e)}"
            results["errors"].append({
                "index": idx,
                "error": str(e),
                "error_type": type(e).__name__,
                "unexpected": True
            })
            results["failed"] += 1
            logger.error(error_msg, exc_info=True)

    # ========================================================================
    # FINAL VALIDATION: Check if we have enough successful embeddings
    # ========================================================================

    success_rate = results["successful"] / results["total_images"]
    results["success_rate"] = success_rate

    if success_rate < validation_threshold:
        raise ValidationError(
            f"Validation failed: success rate {success_rate:.2%} below threshold {validation_threshold:.2%}",
            details={
                "total": results["total_images"],
                "successful": results["successful"],
                "failed": results["failed"],
                "threshold": validation_threshold
            }
        )

    logger.info(
        f"✅ Validation complete: {results['successful']}/{results['total_images']} "
        f"images ({success_rate:.2%})"
    )

    return results


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

def example_usage():
    """Example usage of CLIP embedder with validation."""

    # Initialize embedder
    embedder = CLIPImageEmbedder(
        model_name="openai/clip-vit-base-patch32",
        device="cuda"  # or "cpu", "mps"
    )

    # Example 1: Single image
    embedding = embedder.encode_image("/path/to/image.jpg")
    print(f"Single embedding shape: {embedding.shape}")

    # Example 2: Batch of images
    image_paths = [
        "/path/to/image1.jpg",
        "/path/to/image2.jpg",
        "/path/to/image3.jpg"
    ]
    embeddings = embedder.encode_images_batch(image_paths, batch_size=32)
    print(f"Batch embeddings shape: {embeddings.shape}")

    # Example 3: Validation with proper schema
    image_set = {
        "images": [
            {"path": "/path/to/cat1.jpg", "label": "cat", "id": "cat_001"},
            {"path": "/path/to/cat2.jpg", "label": "cat", "id": "cat_002"},
            {"path": "/path/to/dog1.jpg", "label": "dog", "id": "dog_001"},
        ],
        "metadata": {
            "dataset": "pets_validation",
            "version": "1.0"
        }
    }

    results = validate_image_embeddings(
        image_set=image_set,
        embedder=embedder,
        validation_threshold=0.8
    )

    print(f"Validation results:")
    print(f"  Success rate: {results['success_rate']:.2%}")
    print(f"  Successful: {results['successful']}")
    print(f"  Failed: {results['failed']}")
    print(f"  Embeddings shape: {len(results['embeddings'])}")


# ============================================================================
# COMMON MISTAKES TO AVOID
# ============================================================================

"""
❌ WRONG: Using diffusers CLIP (outdated pattern)

from diffusers import CLIPModel  # Wrong!
model = CLIPModel.from_pretrained(...)

✅ CORRECT: Using transformers CLIP

from transformers import CLIPVisionModel, CLIPImageProcessor
model = CLIPVisionModel.from_pretrained(...)
processor = CLIPImageProcessor.from_pretrained(...)


❌ WRONG: No input validation

def encode(images):
    return model(images)  # What if images is None? Wrong type?

✅ CORRECT: Defensive validation

def encode(images):
    if not isinstance(images, list):
        raise ValidationError(...)
    if len(images) == 0:
        raise ValidationError(...)
    # Now safe to process


❌ WRONG: Ambiguous indexing

for img in image_set["images"]:  # KeyError if "images" missing
    process(img["path"])  # KeyError if "path" missing

✅ CORRECT: Defensive iteration

images_list = image_set.get("images", [])
if not isinstance(images_list, list):
    raise ValidationError(...)

for idx, img in enumerate(images_list):
    if not isinstance(img, dict):
        log_error(f"Invalid image at {idx}")
        continue

    path = img.get("path")
    if not path:
        log_error(f"Missing path at {idx}")
        continue

    process(path)
"""


# ============================================================================
# PRODUCTION CHECKLIST
# ============================================================================

"""
✅ Model Loading:
   □ Use CLIPVisionModel + CLIPImageProcessor (not diffusers)
   □ Set cache directory
   □ Move to correct device
   □ Set to eval mode

✅ Input Validation:
   □ Check types (dict, list, tensor)
   □ Check required keys exist
   □ Validate tensor shapes
   □ Clear error messages

✅ Error Handling:
   □ Use specific exception types
   □ Log errors with context
   □ Continue on individual failures
   □ Track success/failure metrics

✅ Performance:
   □ Batch processing
   □ GPU acceleration
   □ No gradients in eval mode
   □ Normalize embeddings

✅ Documentation:
   □ Document expected schemas
   □ Type hints on all functions
   □ Usage examples
   □ Common mistakes listed
"""
