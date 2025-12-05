# 🌹 Skyy Rose Collection - Training Data Setup Guide

## 📋 Overview

This guide will help you download, process, and upload the Skyy Rose Collection images from Google Drive for AI model training. The system will automatically:

- ✅ **Download images** from your Google Drive folder
- ✅ **Categorize images** automatically (dresses, tops, bottoms, accessories, etc.)
- ✅ **Resize to 1024x1024** for optimal training
- ✅ **Enhance image quality** with professional processing
- ✅ **Generate captions** with brand-specific trigger words
- ✅ **Upload to training interface** for immediate use

## 🚀 Quick Start (Recommended Method)

### Step 1: Download Images from Google Drive

**Option A: Web Interface (Easiest)**
1. Open your Google Drive folder: https://drive.google.com/drive/folders/1F19qdkeAxleX-t28OzZk0vN6xAv52Vkt?usp=drive_link
2. Select all images (Ctrl+A or Cmd+A)
3. Right-click and select "Download"
4. Google Drive will create a ZIP file - save it to your computer
5. Extract the ZIP file to get individual images

**Option B: Using rclone (Advanced)**
```bash
# Install rclone
curl https://rclone.org/install.sh | sudo bash

# Configure Google Drive
rclone config

# Download the folder
rclone copy "gdrive:Skyy Rose Collection" ./skyy_rose_images/
```

### Step 2: Process Images Automatically

Once you have the images downloaded, run our automated processor:

```bash
cd DevSkyy

# Process images from downloaded folder
python scripts/google_drive_processor.py --process-local /path/to/your/downloaded/images --upload
```

**Example:**
```bash
# If you extracted images to ~/Downloads/Skyy Rose Collection/
python scripts/google_drive_processor.py --process-local "~/Downloads/Skyy Rose Collection" --upload
```

### Step 3: Verify Upload

Check the training interface at: http://localhost:8001

## 📁 Automatic Categorization

The system automatically categorizes images based on filename patterns:

| Category | Detected Keywords |
|----------|-------------------|
| **Dresses** | dress, gown, evening, cocktail, maxi, midi, mini, sundress, bodycon, a-line, wrap, shift, slip |
| **Tops** | top, blouse, shirt, tee, tank, camisole, crop, tunic, sweater, cardigan, blazer, jacket |
| **Bottoms** | pants, jeans, trousers, leggings, shorts, skirt, palazzo, wide-leg, skinny, straight, bootcut |
| **Accessories** | bag, purse, clutch, belt, scarf, hat, jewelry, necklace, earrings, bracelet, ring, watch, sunglasses |
| **Shoes** | shoes, heels, boots, sandals, flats, sneakers, pumps, stiletto, wedge, ankle-boot, knee-boot |
| **Outerwear** | coat, jacket, blazer, cardigan, vest, poncho, cape, trench, puffer, bomber, denim-jacket |

## 🎯 Brand-Specific Processing

Each image is processed with:

- **Trigger Words**: `skyrose_dresses`, `skyrose_tops`, `skyrose_collection`, etc.
- **Captions**: "skyrose_dresses, luxury fashion item, high-end design"
- **Quality Enhancement**: Auto-contrast and equalization
- **Consistent Sizing**: All images resized to 1024x1024
- **Metadata**: Complete processing history and categorization info

## 🔧 Manual Processing (Alternative)

If you prefer manual control:

### 1. Use the Web Interface

Visit: http://localhost:8001

- **Single Image Upload**: Upload one image at a time with custom descriptions
- **Batch Upload**: Upload multiple images to the same category
- **ZIP Archive Upload**: Upload a ZIP file containing multiple images

### 2. Direct API Usage

```bash
# Upload single image
curl -X POST "http://localhost:8001/upload/single-image" \
  -F "file=@skyy_rose_dress.jpg" \
  -F "category=dresses" \
  -F "auto_process=true"

# Upload batch
curl -X POST "http://localhost:8001/upload/batch-images" \
  -F "files=@dress1.jpg" \
  -F "files=@dress2.jpg" \
  -F "category=dresses"

# Check status
curl "http://localhost:8001/status/uploads"
```

## 📊 Expected Results

After processing, you should see:

```json
{
  "success": true,
  "total_processed": 45,
  "stats": {
    "categories": {
      "dresses": 15,
      "tops": 12,
      "bottoms": 8,
      "accessories": 6,
      "shoes": 4
    }
  },
  "summary": {
    "total_size_mb": 125.6,
    "ready_for_training": true
  }
}
```

## 🎬 Next Steps: Start Training

Once images are processed and uploaded:

### 1. Train Your Custom Model

```python
from agent.modules.backend.brand_model_trainer import train_brand_model

# Train Skyy Rose model
result = await train_brand_model(
    dataset_path="processed_training_data/dresses",
    model_name="skyy_rose_dresses_v1"
)
```

### 2. Generate Brand-Consistent Content

```python
from agent.modules.frontend.fashion_computer_vision_agent import generate_runway_video

# Generate runway video with Skyy Rose styling
video_result = await generate_runway_video(
    prompt="skyrose_collection elegant evening wear fashion show",
    duration=4,
    upscale=True
)
```

### 3. Create Product Videos

```python
# Generate 360° product rotation
rotation_result = await generate_product_rotation(
    product_image_path="skyy_rose_dress.jpg",
    rotation_steps=24
)
```

## 🔍 Troubleshooting

### Issue: "Brand trainer not available"
**Solution**: The brand trainer module is optional for upload. Images will still be processed and stored correctly.

### Issue: "Google Drive folder not accessible"
**Solution**: 
1. Ensure the folder is shared publicly or you have access
2. Try downloading manually via web interface
3. Use rclone with proper authentication

### Issue: "Upload failed"
**Solution**:
1. Check that the training interface is running: http://localhost:8001
2. Verify image formats are supported (JPG, PNG, WEBP, HEIC, BMP, TIFF)
3. Ensure file sizes are under 50MB each

### Issue: "Images not categorizing correctly"
**Solution**:
1. Rename files to include category keywords (e.g., "skyy_rose_evening_dress.jpg")
2. Use manual categorization via web interface
3. Specify category explicitly in API calls

## 📞 Support Commands

```bash
# Check processing status
python scripts/google_drive_processor.py --help

# View upload interface
open http://localhost:8001

# Check server logs
tail -f DevSkyy/logs/training_interface.log

# Test API connectivity
curl http://localhost:8001/status/uploads
```

## 🎯 Success Metrics

Your setup is successful when you see:

- ✅ **Images Downloaded**: All images from Google Drive folder
- ✅ **Automatic Categorization**: Images sorted into appropriate categories
- ✅ **Quality Processing**: All images resized to 1024x1024 with enhancement
- ✅ **Brand Integration**: Trigger words and captions generated
- ✅ **Upload Complete**: Images available in training interface
- ✅ **Ready for Training**: Dataset prepared for model fine-tuning

## 🚀 Production Ready

Once processing is complete, your Skyy Rose Collection will be ready for:

1. **Custom Model Training** with LoRA fine-tuning
2. **Video Generation** with brand-consistent styling
3. **Product Visualization** with 360° rotations
4. **Marketing Content** with automated generation
5. **Quality Control** with brand consistency validation

The system is designed to handle any number of images and will automatically scale processing based on your collection size.

---

**🌹 Ready to transform your Skyy Rose Collection into AI-powered fashion content!**
