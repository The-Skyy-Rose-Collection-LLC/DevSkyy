# DevSkyy Video Generation & Brand Model Training Guide

## 🎬 Advanced Video Generation System

The DevSkyy multiagent workflow system now includes state-of-the-art video generation capabilities powered by Stable Video Diffusion and AnimateDiff, along with custom brand model training using LoRA fine-tuning.

## 🚀 Features

### Video Generation
- **Fashion Runway Videos**: 3-5 second luxury fashion runway videos at 1024x576+ resolution
- **Product 360° Animations**: Smooth product rotation videos with 24-step precision
- **Video Upscaling**: Automatic upscaling to maximum quality (up to 2048x1152)
- **H.264 Encoding**: Professional MP4 output with optimized compression

### Brand Model Training
- **LoRA Fine-tuning**: Efficient SDXL customization for brand consistency
- **Automatic Preprocessing**: Support for any image format with intelligent resizing
- **Caption Generation**: Automatic BLIP-2 powered image captioning
- **Trigger Word System**: Brand-specific keywords for consistent generation
- **Quality Validation**: Automated brand consistency checking

## 📋 Quick Start

### 1. Generate Fashion Runway Video

```python
from agent.modules.frontend.fashion_computer_vision_agent import generate_runway_video

# Generate luxury fashion runway video
result = await generate_runway_video(
    prompt="elegant evening gown on luxury runway",
    duration=4,  # seconds
    fps=8       # frames per second
)

print(f"Video saved: {result['video_path']}")
```

### 2. Create Product 360° Animation

```python
from agent.modules.frontend.fashion_computer_vision_agent import generate_product_rotation

# Generate 360° product rotation
result = await generate_product_rotation(
    product_image_path="path/to/product.jpg",
    rotation_steps=24  # 15° per step
)

print(f"360° video saved: {result['video_path']}")
```

### 3. Train Custom Brand Model

```python
from agent.modules.backend.brand_model_trainer import prepare_dataset, train_brand_model

# Prepare training dataset
dataset_result = await prepare_dataset(
    input_dir="skyy_rose_images/",
    category="dresses"
)

# Train custom model
training_result = await train_brand_model(
    dataset_path=dataset_result['output_directory'],
    model_name="skyy_rose_dresses_v1"
)

print(f"Model trained: {training_result['model_path']}")
```

## 🔧 API Reference

### FashionComputerVisionAgent

#### `generate_fashion_runway_video()`
Generate luxury fashion runway videos.

**Parameters:**
- `prompt` (str): Description of the fashion scene
- `duration` (int): Video duration in seconds (3-5 recommended)
- `fps` (int): Frames per second (8-24)
- `width` (int): Video width (minimum 1024)
- `height` (int): Video height (minimum 576)
- `style` (str): Video style description
- `upscale` (bool): Whether to upscale to maximum quality

**Returns:**
```python
{
    "success": True,
    "video_path": "path/to/generated/video.mp4",
    "prompt_used": "enhanced prompt with style keywords",
    "duration": 4,
    "fps": 8,
    "dimensions": {"width": 1024, "height": 576},
    "model": "stable-video-diffusion",
    "timestamp": "2025-10-26T..."
}
```

#### `generate_product_360_video()`
Generate 360° product rotation videos.

**Parameters:**
- `product_image_path` (str|Path): Path to product image
- `rotation_steps` (int): Number of rotation steps (24 = 15° per step)
- `duration` (int): Video duration in seconds
- `upscale` (bool): Whether to upscale to maximum quality

**Returns:**
```python
{
    "success": True,
    "video_path": "path/to/360/video.mp4",
    "product_image": "path/to/source/image.jpg",
    "rotation_steps": 24,
    "duration": 3,
    "fps": 8,
    "model": "animatediff",
    "timestamp": "2025-10-26T..."
}
```

### SkyRoseBrandTrainer

#### `prepare_training_dataset()`
Prepare training dataset from input images.

**Parameters:**
- `input_directory` (str|Path): Directory containing training images
- `category` (str): Category name (e.g., "dresses", "tops", "accessories")
- `remove_background` (bool): Whether to remove image backgrounds
- `enhance_images` (bool): Whether to enhance image quality

**Returns:**
```python
{
    "success": True,
    "category": "dresses",
    "total_processed": 45,
    "train_samples": 36,
    "validation_samples": 9,
    "output_directory": "processed_training_data/dresses",
    "metadata_file": "processed_training_data/dresses/metadata.json",
    "manifest_file": "processed_training_data/dresses/training_manifest.json",
    "timestamp": "2025-10-26T..."
}
```

#### `train_lora_model()`
Train LoRA model for brand-specific generation.

**Parameters:**
- `dataset_path` (str|Path): Path to processed dataset directory
- `model_name` (str): Name for the trained model
- `resume_from_checkpoint` (str, optional): Path to checkpoint to resume from

**Returns:**
```python
{
    "success": True,
    "model_name": "skyy_rose_dresses_v1",
    "model_path": "custom_models/skyy_rose/skyy_rose_dresses_v1/final_model",
    "config_path": "custom_models/skyy_rose/skyy_rose_dresses_v1/training_config.json",
    "training_results": {
        "training_losses": [...],
        "validation_losses": [...],
        "final_train_loss": 0.234,
        "final_val_loss": 0.267,
        "epochs_completed": 100
    },
    "timestamp": "2025-10-26T..."
}
```

## 🔄 Workflow Integration

### Video Generation Workflows

The system integrates with the DevSkyy workflow engine for automated video generation:

```python
from api_integration.workflow_engine import workflow_engine

# Create runway video generation workflow
runway_workflow = {
    "name": "Generate Fashion Runway Video",
    "trigger": {
        "trigger_type": "manual",
        "config": {}
    },
    "steps": [
        {
            "name": "Generate Video",
            "action_type": "video_generation",
            "action": "generate_runway_video",
            "config": {
                "prompt": "{{input.prompt}}",
                "duration": 4,
                "fps": 8,
                "upscale": True
            }
        }
    ]
}

# Register and execute workflow
workflow_id = await workflow_engine.register_workflow(runway_workflow)
result = await workflow_engine.execute_workflow(workflow_id, {
    "prompt": "luxury evening wear fashion show"
})
```

### Brand Training Workflows

```python
# Create brand model training workflow
training_workflow = {
    "name": "Train Skyy Rose Brand Model",
    "trigger": {
        "trigger_type": "manual",
        "config": {}
    },
    "steps": [
        {
            "name": "Prepare Dataset",
            "action_type": "brand_model_training",
            "action": "prepare_dataset",
            "config": {
                "input_directory": "{{input.image_directory}}",
                "category": "{{input.category}}"
            }
        },
        {
            "name": "Train Model",
            "action_type": "brand_model_training",
            "action": "train_brand_model",
            "config": {
                "dataset_path": "{{steps.prepare_dataset.output_directory}}",
                "model_name": "{{input.model_name}}"
            }
        }
    ]
}
```

## 📊 Performance & Quality

### Video Generation Performance
- **Runway Videos**: 60-120 seconds generation time for 4-second videos
- **Product 360°**: 45-90 seconds for 24-frame rotations
- **Memory Usage**: Automatic GPU memory management with model loading/unloading
- **Output Quality**: Up to 2048x1152 resolution with H.264 encoding

### Brand Model Training
- **Dataset Size**: Minimum 20-50 images per category for effective training
- **Training Time**: 2-4 hours for 100 epochs (depending on dataset size)
- **Model Size**: LoRA weights typically 10-50MB (vs 6GB+ for full model)
- **Consistency Score**: Automated validation with 80%+ consistency target

## 🔧 Configuration

### GPU Memory Management
The system automatically manages GPU memory by loading/unloading models as needed:

```python
# Models are loaded on-demand and unloaded after use
await fashion_vision_agent._load_video_generation_models()  # Load SVD + AnimateDiff
# ... generate video ...
fashion_vision_agent._unload_model("svd")  # Free memory
```

### Storage Management
- **Videos**: Stored in `generated_videos/` directory
- **Models**: Custom models in `custom_models/skyy_rose/`
- **Training Data**: Processed datasets in `processed_training_data/`
- **Automatic Cleanup**: Configurable retention policies

## 🚀 Advanced Usage

### Custom Trigger Words
Configure brand-specific trigger words for consistent generation:

```python
brand_config = {
    "trigger_words": [
        "skyrose_dress",
        "skyrose_collection", 
        "skyrose_luxury",
        "skyrose_evening"
    ]
}
```

### Video Post-Processing
Apply additional effects and enhancements:

```python
# Upscale existing video
upscale_result = await fashion_vision_agent.upscale_video(
    video_path="generated_videos/runway_video.mp4",
    target_resolution=(2048, 1152)
)
```

### Batch Processing
Process multiple items efficiently:

```python
# Batch generate product videos
products = ["product1.jpg", "product2.jpg", "product3.jpg"]
results = []

for product in products:
    result = await generate_product_rotation(product)
    results.append(result)
```

## 📈 Monitoring & Analytics

The system provides comprehensive monitoring through the workflow engine:

- **Generation Metrics**: Success rates, processing times, quality scores
- **Resource Usage**: GPU memory, storage consumption, processing queues
- **Brand Consistency**: Automated validation scores and recommendations
- **Error Tracking**: Detailed error logs with automatic retry mechanisms

## 🔒 Security & Compliance

- **Input Validation**: Automatic validation of image formats and sizes
- **Content Filtering**: Built-in safety checks for generated content
- **Access Control**: Role-based permissions for model training and generation
- **Audit Logging**: Complete audit trail for all generation and training activities

## 📞 Support & Troubleshooting

### Common Issues

1. **GPU Memory Errors**: Reduce batch size or enable automatic model unloading
2. **Video Generation Fails**: Check input image quality and format compatibility
3. **Training Data Issues**: Ensure minimum 20 images per category with consistent quality
4. **Model Loading Errors**: Verify model files and dependencies are properly installed

### Performance Optimization

1. **Use GPU**: Ensure CUDA is available for optimal performance
2. **Batch Processing**: Process multiple items together when possible
3. **Memory Management**: Enable automatic model unloading for memory-constrained systems
4. **Storage**: Use SSD storage for faster I/O operations

For additional support, check the logs in `DevSkyy/logs/` or contact the development team.
