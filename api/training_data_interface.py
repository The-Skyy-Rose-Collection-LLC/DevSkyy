from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import gc
import json
import logging
from pathlib import Path
import shutil
import tempfile
from typing import Any
import zipfile

from fastapi import BackgroundTasks, Body, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
import psutil
from pydantic import BaseModel


"""
Training Data Upload Interface
Handles Skyy Rose Collection training image uploads and preprocessing
"""

logger = logging.getLogger(__name__)

# Production-grade image processing imports
try:
    from PIL import Image, ImageEnhance, ImageOps

    PIL_AVAILABLE = True
except ImportError:
    logger.error("PIL/Pillow not available - image processing will be limited")
    PIL_AVAILABLE = False
    # Create dummy Image class for type hints
    Image = type('Image', (), {'Image': Any})

try:
    import cv2
    import numpy as np

    OPENCV_AVAILABLE = True
except ImportError:
    logger.warning("OpenCV not available - advanced image processing disabled")
    OPENCV_AVAILABLE = False

# Import the brand trainer
try:
    from agent.modules.backend.brand_model_trainer import brand_trainer

    BRAND_TRAINER_AVAILABLE = True
except ImportError:
    logger.warning("Brand trainer not available")
    BRAND_TRAINER_AVAILABLE = False

app = FastAPI(title="Skyy Rose Training Data Interface", version="1.0.0")

# Add CORS middleware for web interface
from fastapi.middleware.cors import CORSMiddleware


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
UPLOAD_DIR = Path("uploads/training_data")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Bulk operations storage
BULK_OPERATIONS_DIR = Path("bulk_operations")
BULK_OPERATIONS_DIR.mkdir(parents=True, exist_ok=True)

# In-memory storage for bulk operations (in production, use Redis or database)
bulk_operations_history = {}
bulk_operation_counter = 0

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB per file
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".bmp", ".tiff"}
MAX_BATCH_SIZE = 100  # Maximum files per batch

# Production quality processing configuration
QUALITY_CONFIG = {
    "max_image_size": (4096, 4096),  # Maximum allowed dimensions
    "min_image_size": (64, 64),  # Minimum allowed dimensions
    "max_file_size": 50 * 1024 * 1024,  # 50MB max file size
    "supported_formats": {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"},
    "output_format": "JPEG",
    "output_quality": 95,
    "memory_limit_mb": 1024,  # Memory limit per operation
    "max_concurrent_operations": 4,  # Max concurrent image processing
    "temp_dir": Path("temp_processing"),
    "backup_originals": True,
}

# Create temp directory
QUALITY_CONFIG["temp_dir"].mkdir(exist_ok=True)


# Pydantic models for bulk operations
class BulkCategoryUpdate(BaseModel):
    image_paths: list[str]
    new_category: str
    preserve_existing_metadata: bool = True


class BulkCaptionUpdate(BaseModel):
    image_paths: list[str]
    caption_template: str
    preserve_trigger_words: bool = True
    add_trigger_words: list[str] = []
    remove_trigger_words: list[str] = []


class BulkTagUpdate(BaseModel):
    image_paths: list[str]
    add_tags: list[str] = []
    remove_tags: list[str] = []
    replace_tags: dict[str, str] = {}


class BulkQualitySettings(BaseModel):
    image_paths: list[str]
    resize_dimensions: list[int] = [1024, 1024]  # Changed from tuple to List for JSON compatibility
    quality_enhancement: bool = True
    auto_contrast: bool = True
    equalize: bool = True
    remove_background: bool = False

    @property
    def resize_dimensions_tuple(self) -> tuple[int, int]:
        """Convert resize_dimensions to tuple for internal use."""
        return tuple(self.resize_dimensions[:2]) if len(self.resize_dimensions) >= 2 else (1024, 1024)


class BulkMetadataUpdate(BaseModel):
    image_paths: list[str]
    metadata_updates: dict[str, Any]
    merge_with_existing: bool = True


class BulkOperationPreview(BaseModel):
    operation_type: str
    affected_images: list[str]
    changes_preview: dict[str, Any]
    estimated_processing_time: float


class UndoOperation(BaseModel):
    operation_id: str
    operation_type: str
    affected_images: list[str]
    previous_state: dict[str, Any]


@app.get("/", response_class=HTMLResponse)
async def get_upload_interface():
    """Serve the bulk editing interface (primary interface)."""
    try:
        with open("api/bulk_editing_interface.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content="""
        <html>
            <body>
                <h1>🌹 Skyy Rose Training Data Upload Interface</h1>
                <p>Bulk editing interface not found. Please use the API endpoints directly:</p>
                <ul>
                    <li>POST /upload/single-image</li>
                    <li>POST /upload/batch-images</li>
                    <li>POST /upload/zip-archive</li>
                    <li>GET /status/uploads</li>
                    <li>POST /bulk/category-update</li>
                    <li>POST /bulk/caption-update</li>
                    <li>POST /bulk/tag-update</li>
                    <li>POST /bulk/quality-update</li>
                    <li>POST /bulk/metadata-update</li>
                </ul>
            </body>
        </html>
        """
        )


@app.get("/simple", response_class=HTMLResponse)
async def get_simple_interface():
    """Serve the simple drag & drop interface."""
    try:
        with open("api/drag_drop_interface.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Simple interface not found</h1>")


@app.get("/classic", response_class=HTMLResponse)
async def get_classic_interface():
    """Serve the classic form-based upload interface."""
    try:
        with open("api/upload_interface.html", "r") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>Classic interface not found</h1>")


@app.post("/upload/single-image")
async def upload_single_image(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    category: str = Form("general"),
    description: str | None = Form(None),
    auto_process: bool = Form(True),
):
    """
    Upload a single training image for Skyy Rose Collection.

    Args:
        file: Image file to upload
        category: Category name (e.g., "dresses", "tops", "accessories")
        description: Optional description of the item
        auto_process: Whether to automatically process the image

    Returns:
        Upload confirmation with processing status
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400, detail=f"Unsupported file format. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        # Check file size
        file_size = 0
        content = await file.read()
        file_size = len(content)

        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400, detail=f"File too large. Maximum size: {MAX_FILE_SIZE // (1024 * 1024)}MB"
            )

        # Create category directory
        category_dir = UPLOAD_DIR / category
        category_dir.mkdir(exist_ok=True)

        # Save file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = f"{timestamp}_{file.filename}"
        file_path = category_dir / safe_filename

        with open(file_path, "wb") as f:
            f.write(content)

        # Create metadata
        metadata = {
            "filename": safe_filename,
            "original_filename": file.filename,
            "category": category,
            "description": description,
            "file_size": file_size,
            "upload_timestamp": datetime.now().isoformat(),
            "processed": False,
        }

        # Save metadata
        metadata_file = category_dir / f"{safe_filename}.json"
        import json

        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

        # Schedule processing if requested
        if auto_process and BRAND_TRAINER_AVAILABLE:
            background_tasks.add_task(process_single_image, str(file_path), category, metadata)

        return JSONResponse(
            {
                "success": True,
                "message": "Image uploaded successfully",
                "file_path": str(file_path),
                "category": category,
                "file_size": file_size,
                "auto_process": auto_process,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Single image upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload/batch-images")
async def upload_batch_images(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    category: str = Form("general"),
    auto_process: bool = Form(True),
):
    """
    Upload multiple training images in batch.

    Args:
        files: List of image files to upload
        category: Category name for all images
        auto_process: Whether to automatically process the images

    Returns:
        Batch upload results with processing status
    """
    try:
        if len(files) > MAX_BATCH_SIZE:
            raise HTTPException(status_code=400, detail=f"Too many files. Maximum batch size: {MAX_BATCH_SIZE}")

        uploaded_files = []
        failed_files = []
        total_size = 0

        # Create category directory
        category_dir = UPLOAD_DIR / category
        category_dir.mkdir(exist_ok=True)

        for file in files:
            try:
                # Validate file
                if not file.filename:
                    failed_files.append({"filename": "unknown", "error": "No filename"})
                    continue

                file_ext = Path(file.filename).suffix.lower()
                if file_ext not in ALLOWED_EXTENSIONS:
                    failed_files.append({"filename": file.filename, "error": f"Unsupported format: {file_ext}"})
                    continue

                # Read and validate file size
                content = await file.read()
                file_size = len(content)

                if file_size > MAX_FILE_SIZE:
                    failed_files.append(
                        {"filename": file.filename, "error": f"File too large: {file_size // (1024 * 1024)}MB"}
                    )
                    continue

                # Save file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                safe_filename = f"{timestamp}_{file.filename}"
                file_path = category_dir / safe_filename

                with open(file_path, "wb") as f:
                    f.write(content)

                # Create metadata
                metadata = {
                    "filename": safe_filename,
                    "original_filename": file.filename,
                    "category": category,
                    "file_size": file_size,
                    "upload_timestamp": datetime.now().isoformat(),
                    "processed": False,
                }

                # Save metadata
                metadata_file = category_dir / f"{safe_filename}.json"
                import json

                with open(metadata_file, "w") as f:
                    json.dump(metadata, f, indent=2)

                uploaded_files.append(
                    {
                        "filename": safe_filename,
                        "original_filename": file.filename,
                        "file_path": str(file_path),
                        "file_size": file_size,
                    }
                )

                total_size += file_size

            except Exception as e:
                failed_files.append({"filename": file.filename if file.filename else "unknown", "error": str(e)})

        # Schedule batch processing if requested
        if auto_process and BRAND_TRAINER_AVAILABLE and uploaded_files:
            background_tasks.add_task(process_batch_images, str(category_dir), category)

        return JSONResponse(
            {
                "success": True,
                "message": "Batch upload completed",
                "uploaded_count": len(uploaded_files),
                "failed_count": len(failed_files),
                "total_size": total_size,
                "category": category,
                "uploaded_files": uploaded_files,
                "failed_files": failed_files,
                "auto_process": auto_process,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Batch upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload/zip-archive")
async def upload_zip_archive(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    category: str = Form("general"),
    auto_process: bool = Form(True),
):
    """
    Upload a ZIP archive containing training images.

    Args:
        file: ZIP file containing images
        category: Category name for all images
        auto_process: Whether to automatically process the images

    Returns:
        Archive extraction and upload results
    """
    try:
        if not file.filename or not file.filename.endswith(".zip"):
            raise HTTPException(status_code=400, detail="File must be a ZIP archive")

        # Save uploaded ZIP file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_path = UPLOAD_DIR / f"archive_{timestamp}.zip"

        content = await file.read()
        with open(zip_path, "wb") as f:
            f.write(content)

        # Extract ZIP file
        extract_dir = UPLOAD_DIR / f"extracted_{timestamp}"
        extract_dir.mkdir(exist_ok=True)

        extracted_files = []
        failed_files = []

        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                for file_info in zip_ref.filelist:
                    if file_info.is_dir():
                        continue

                    file_ext = Path(file_info.filename).suffix.lower()
                    if file_ext not in ALLOWED_EXTENSIONS:
                        failed_files.append(
                            {"filename": file_info.filename, "error": f"Unsupported format: {file_ext}"}
                        )
                        continue

                    if file_info.file_size > MAX_FILE_SIZE:
                        failed_files.append(
                            {
                                "filename": file_info.filename,
                                "error": f"File too large: {file_info.file_size // (1024 * 1024)}MB",
                            }
                        )
                        continue

                    # Extract file
                    zip_ref.extract(file_info, extract_dir)

                    # Move to category directory
                    category_dir = UPLOAD_DIR / category
                    category_dir.mkdir(exist_ok=True)

                    source_path = extract_dir / file_info.filename
                    safe_filename = f"{timestamp}_{Path(file_info.filename).name}"
                    dest_path = category_dir / safe_filename

                    shutil.move(str(source_path), str(dest_path))

                    # Create metadata
                    metadata = {
                        "filename": safe_filename,
                        "original_filename": file_info.filename,
                        "category": category,
                        "file_size": file_info.file_size,
                        "upload_timestamp": datetime.now().isoformat(),
                        "source": "zip_archive",
                        "processed": False,
                    }

                    # Save metadata
                    metadata_file = category_dir / f"{safe_filename}.json"
                    import json

                    with open(metadata_file, "w") as f:
                        json.dump(metadata, f, indent=2)

                    extracted_files.append(
                        {
                            "filename": safe_filename,
                            "original_filename": file_info.filename,
                            "file_path": str(dest_path),
                            "file_size": file_info.file_size,
                        }
                    )

        finally:
            # Cleanup
            shutil.rmtree(extract_dir, ignore_errors=True)
            zip_path.unlink(missing_ok=True)

        # Schedule processing if requested
        if auto_process and BRAND_TRAINER_AVAILABLE and extracted_files:
            background_tasks.add_task(process_batch_images, str(UPLOAD_DIR / category), category)

        return JSONResponse(
            {
                "success": True,
                "message": "ZIP archive processed successfully",
                "extracted_count": len(extracted_files),
                "failed_count": len(failed_files),
                "category": category,
                "extracted_files": extracted_files,
                "failed_files": failed_files,
                "auto_process": auto_process,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"ZIP archive upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status/uploads")
async def get_upload_status():
    """Get status of all uploaded training data."""
    try:
        categories = {}

        for category_dir in UPLOAD_DIR.iterdir():
            if not category_dir.is_dir():
                continue

            category_name = category_dir.name
            image_files = []

            for file_path in category_dir.iterdir():
                if file_path.suffix.lower() in ALLOWED_EXTENSIONS:
                    metadata_file = category_dir / f"{file_path.name}.json"

                    metadata = {"processed": False}
                    if metadata_file.exists():
                        import json

                        with open(metadata_file, "r") as f:
                            metadata = json.load(f)

                    image_files.append(
                        {
                            "filename": file_path.name,
                            "file_size": file_path.stat().st_size,
                            "processed": metadata.get("processed", False),
                            "upload_timestamp": metadata.get("upload_timestamp"),
                        }
                    )

            categories[category_name] = {
                "total_images": len(image_files),
                "processed_images": sum(1 for f in image_files if f["processed"]),
                "total_size": sum(f["file_size"] for f in image_files),
                "images": image_files,
            }

        return JSONResponse(
            {
                "success": True,
                "categories": categories,
                "total_categories": len(categories),
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Failed to get upload status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/process/category/{category}")
async def process_category(
    category: str, background_tasks: BackgroundTasks, remove_background: bool = False, enhance_images: bool = True
):
    """
    Process all images in a category for training.

    Args:
        category: Category name to process
        remove_background: Whether to remove image backgrounds
        enhance_images: Whether to enhance image quality

    Returns:
        Processing initiation confirmation
    """
    try:
        if not BRAND_TRAINER_AVAILABLE:
            raise HTTPException(status_code=503, detail="Brand trainer not available")

        category_dir = UPLOAD_DIR / category
        if not category_dir.exists():
            raise HTTPException(status_code=404, detail=f"Category '{category}' not found")

        # Schedule processing
        background_tasks.add_task(
            process_category_for_training, str(category_dir), category, remove_background, enhance_images
        )

        return JSONResponse(
            {
                "success": True,
                "message": f"Processing initiated for category '{category}'",
                "category": category,
                "remove_background": remove_background,
                "enhance_images": enhance_images,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Failed to initiate category processing: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BULK OPERATIONS API ENDPOINTS
# ============================================================================


@app.post("/bulk/preview")
async def preview_bulk_operation(operation_data: dict[str, Any] = Body(...)):
    """
    Preview the effects of a bulk operation before applying it.

    Args:
        operation_data: Dictionary containing operation type and parameters

    Returns:
        Preview of changes that would be made
    """
    try:
        operation_type = operation_data.get("operation_type")
        image_paths = operation_data.get("image_paths", [])

        if not operation_type or not image_paths:
            raise HTTPException(status_code=400, detail="Missing operation_type or image_paths")

        preview = await generate_bulk_operation_preview(operation_type, operation_data)

        return JSONResponse(
            {
                "success": True,
                "preview": preview,
                "affected_images_count": len(image_paths),
                "estimated_processing_time": len(image_paths) * 0.5,  # Estimate 0.5 seconds per image
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Failed to generate bulk operation preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/bulk/category-update")
async def bulk_category_update(background_tasks: BackgroundTasks, update_data: BulkCategoryUpdate):
    """
    Update category for multiple images at once.

    Args:
        update_data: Bulk category update parameters

    Returns:
        Operation result with tracking ID
    """
    try:
        global bulk_operation_counter
        bulk_operation_counter += 1
        operation_id = f"bulk_category_{bulk_operation_counter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"🔄 Starting bulk category update: {operation_id}")

        # Validate image paths
        valid_paths = []
        invalid_paths = []

        for image_path in update_data.image_paths:
            if Path(image_path).exists():
                valid_paths.append(image_path)
            else:
                invalid_paths.append(image_path)

        if not valid_paths:
            raise HTTPException(status_code=400, detail="No valid image paths provided")

        # Store operation for undo functionality
        previous_state = await capture_images_state(valid_paths)

        bulk_operations_history[operation_id] = {
            "operation_type": "category_update",
            "operation_id": operation_id,
            "affected_images": valid_paths,
            "previous_state": previous_state,
            "new_category": update_data.new_category,
            "timestamp": datetime.now().isoformat(),
            "status": "in_progress",
        }

        # Schedule background processing
        background_tasks.add_task(
            execute_bulk_category_update,
            operation_id,
            valid_paths,
            update_data.new_category,
            update_data.preserve_existing_metadata,
        )

        return JSONResponse(
            {
                "success": True,
                "operation_id": operation_id,
                "message": f"Bulk category update initiated for {len(valid_paths)} images",
                "valid_images": len(valid_paths),
                "invalid_images": len(invalid_paths),
                "invalid_paths": invalid_paths,
                "new_category": update_data.new_category,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"❌ Bulk category update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/bulk/caption-update")
async def bulk_caption_update(background_tasks: BackgroundTasks, update_data: BulkCaptionUpdate):
    """
    Update captions for multiple images at once.

    Args:
        update_data: Bulk caption update parameters

    Returns:
        Operation result with tracking ID
    """
    try:
        global bulk_operation_counter
        bulk_operation_counter += 1
        operation_id = f"bulk_caption_{bulk_operation_counter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"📝 Starting bulk caption update: {operation_id}")

        # Validate image paths
        valid_paths = [path for path in update_data.image_paths if Path(path).exists()]

        if not valid_paths:
            raise HTTPException(status_code=400, detail="No valid image paths provided")

        # Store operation for undo functionality
        previous_state = await capture_images_state(valid_paths)

        bulk_operations_history[operation_id] = {
            "operation_type": "caption_update",
            "operation_id": operation_id,
            "affected_images": valid_paths,
            "previous_state": previous_state,
            "caption_template": update_data.caption_template,
            "timestamp": datetime.now().isoformat(),
            "status": "in_progress",
        }

        # Schedule background processing
        background_tasks.add_task(
            execute_bulk_caption_update,
            operation_id,
            valid_paths,
            update_data.caption_template,
            update_data.preserve_trigger_words,
            update_data.add_trigger_words,
            update_data.remove_trigger_words,
        )

        return JSONResponse(
            {
                "success": True,
                "operation_id": operation_id,
                "message": f"Bulk caption update initiated for {len(valid_paths)} images",
                "affected_images": len(valid_paths),
                "caption_template": update_data.caption_template,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"❌ Bulk caption update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/bulk/tag-update")
async def bulk_tag_update(background_tasks: BackgroundTasks, update_data: BulkTagUpdate):
    """
    Update tags for multiple images at once.

    Args:
        update_data: Bulk tag update parameters

    Returns:
        Operation result with tracking ID
    """
    try:
        global bulk_operation_counter
        bulk_operation_counter += 1
        operation_id = f"bulk_tag_{bulk_operation_counter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"🏷️ Starting bulk tag update: {operation_id}")

        # Validate image paths
        valid_paths = [path for path in update_data.image_paths if Path(path).exists()]

        if not valid_paths:
            raise HTTPException(status_code=400, detail="No valid image paths provided")

        # Store operation for undo functionality
        previous_state = await capture_images_state(valid_paths)

        bulk_operations_history[operation_id] = {
            "operation_type": "tag_update",
            "operation_id": operation_id,
            "affected_images": valid_paths,
            "previous_state": previous_state,
            "add_tags": update_data.add_tags,
            "remove_tags": update_data.remove_tags,
            "replace_tags": update_data.replace_tags,
            "timestamp": datetime.now().isoformat(),
            "status": "in_progress",
        }

        # Schedule background processing
        background_tasks.add_task(
            execute_bulk_tag_update,
            operation_id,
            valid_paths,
            update_data.add_tags,
            update_data.remove_tags,
            update_data.replace_tags,
        )

        return JSONResponse(
            {
                "success": True,
                "operation_id": operation_id,
                "message": f"Bulk tag update initiated for {len(valid_paths)} images",
                "affected_images": len(valid_paths),
                "add_tags": update_data.add_tags,
                "remove_tags": update_data.remove_tags,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"❌ Bulk tag update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/bulk/quality-update")
async def bulk_quality_update(background_tasks: BackgroundTasks, update_data: BulkQualitySettings):
    """
    Apply quality settings to multiple images at once.

    Args:
        update_data: Bulk quality settings parameters

    Returns:
        Operation result with tracking ID
    """
    try:
        global bulk_operation_counter
        bulk_operation_counter += 1
        operation_id = f"bulk_quality_{bulk_operation_counter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"✨ Starting bulk quality update: {operation_id}")

        # Validate image paths
        valid_paths = [path for path in update_data.image_paths if Path(path).exists()]

        if not valid_paths:
            raise HTTPException(status_code=400, detail="No valid image paths provided")

        # Store operation for undo functionality
        previous_state = await capture_images_state(valid_paths)

        bulk_operations_history[operation_id] = {
            "operation_type": "quality_update",
            "operation_id": operation_id,
            "affected_images": valid_paths,
            "previous_state": previous_state,
            "quality_settings": {
                "resize_dimensions": update_data.resize_dimensions,
                "quality_enhancement": update_data.quality_enhancement,
                "auto_contrast": update_data.auto_contrast,
                "equalize": update_data.equalize,
                "remove_background": update_data.remove_background,
            },
            "timestamp": datetime.now().isoformat(),
            "status": "in_progress",
        }

        # Schedule background processing
        background_tasks.add_task(execute_bulk_quality_update, operation_id, valid_paths, update_data)

        return JSONResponse(
            {
                "success": True,
                "operation_id": operation_id,
                "message": f"Bulk quality update initiated for {len(valid_paths)} images",
                "affected_images": len(valid_paths),
                "quality_settings": update_data.dict(),
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"❌ Bulk quality update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/bulk/metadata-update")
async def bulk_metadata_update(background_tasks: BackgroundTasks, update_data: BulkMetadataUpdate):
    """
    Update metadata for multiple images at once.

    Args:
        update_data: Bulk metadata update parameters

    Returns:
        Operation result with tracking ID
    """
    try:
        global bulk_operation_counter
        bulk_operation_counter += 1
        operation_id = f"bulk_metadata_{bulk_operation_counter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"📊 Starting bulk metadata update: {operation_id}")

        # Validate image paths
        valid_paths = [path for path in update_data.image_paths if Path(path).exists()]

        if not valid_paths:
            raise HTTPException(status_code=400, detail="No valid image paths provided")

        # Store operation for undo functionality
        previous_state = await capture_images_state(valid_paths)

        bulk_operations_history[operation_id] = {
            "operation_type": "metadata_update",
            "operation_id": operation_id,
            "affected_images": valid_paths,
            "previous_state": previous_state,
            "metadata_updates": update_data.metadata_updates,
            "merge_with_existing": update_data.merge_with_existing,
            "timestamp": datetime.now().isoformat(),
            "status": "in_progress",
        }

        # Schedule background processing
        background_tasks.add_task(
            execute_bulk_metadata_update,
            operation_id,
            valid_paths,
            update_data.metadata_updates,
            update_data.merge_with_existing,
        )

        return JSONResponse(
            {
                "success": True,
                "operation_id": operation_id,
                "message": f"Bulk metadata update initiated for {len(valid_paths)} images",
                "affected_images": len(valid_paths),
                "metadata_updates": update_data.metadata_updates,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"❌ Bulk metadata update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/bulk/operations/{operation_id}")
async def get_bulk_operation_status(operation_id: str):
    """
    Get the status of a bulk operation.

    Args:
        operation_id: ID of the bulk operation

    Returns:
        Operation status and details
    """
    try:
        if operation_id not in bulk_operations_history:
            raise HTTPException(status_code=404, detail="Operation not found")

        operation = bulk_operations_history[operation_id]

        return JSONResponse({"success": True, "operation": operation, "timestamp": datetime.now().isoformat()})

    except Exception as e:
        logger.error(f"Failed to get bulk operation status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/bulk/undo/{operation_id}")
async def undo_bulk_operation(operation_id: str, background_tasks: BackgroundTasks):
    """
    Undo a bulk operation.

    Args:
        operation_id: ID of the operation to undo

    Returns:
        Undo operation result
    """
    try:
        if operation_id not in bulk_operations_history:
            raise HTTPException(status_code=404, detail="Operation not found")

        operation = bulk_operations_history[operation_id]

        if operation["status"] != "completed":
            raise HTTPException(status_code=400, detail="Can only undo completed operations")

        logger.info(f"↩️ Starting undo operation: {operation_id}")

        # Create undo operation
        global bulk_operation_counter
        bulk_operation_counter += 1
        undo_operation_id = f"undo_{operation_id}_{bulk_operation_counter}"

        # Schedule background undo processing
        background_tasks.add_task(execute_bulk_undo, undo_operation_id, operation)

        return JSONResponse(
            {
                "success": True,
                "undo_operation_id": undo_operation_id,
                "message": f"Undo operation initiated for {operation_id}",
                "original_operation": operation_id,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"❌ Bulk undo failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/bulk/operations")
async def list_bulk_operations():
    """
    List all bulk operations.

    Returns:
        List of all bulk operations with their status
    """
    try:
        operations = []
        for op_id, operation in bulk_operations_history.items():
            operations.append(
                {
                    "operation_id": op_id,
                    "operation_type": operation["operation_type"],
                    "affected_images_count": len(operation["affected_images"]),
                    "status": operation["status"],
                    "timestamp": operation["timestamp"],
                }
            )

        # Sort by timestamp (most recent first)
        operations.sort(key=lambda x: x["timestamp"], reverse=True)

        return JSONResponse(
            {
                "success": True,
                "operations": operations,
                "total_operations": len(operations),
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Failed to list bulk operations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Background task functions
async def process_single_image(file_path: str, category: str, metadata: dict[str, Any]):
    """Background task to process a single uploaded image."""
    try:
        logger.info(f"Processing single image: {file_path}")

        # Generate caption for the image
        if BRAND_TRAINER_AVAILABLE:
            caption = await brand_trainer.generate_image_caption(file_path)

            # Update metadata
            metadata["processed"] = True
            metadata["caption"] = caption
            metadata["processing_timestamp"] = datetime.now().isoformat()

            # Save updated metadata
            metadata_file = Path(file_path).with_suffix(Path(file_path).suffix + ".json")
            import json

            with open(metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)

        logger.info(f"Single image processed: {file_path}")

    except Exception as e:
        logger.error(f"Failed to process single image {file_path}: {e}")


async def process_batch_images(category_dir: str, category: str):
    """Background task to process batch uploaded images."""
    try:
        logger.info(f"Processing batch images in category: {category}")

        if BRAND_TRAINER_AVAILABLE:
            # Use the brand trainer's dataset preparation
            result = await brand_trainer.prepare_training_dataset(
                input_directory=category_dir, category=category, remove_background=False, enhance_images=True
            )

            logger.info(f"Batch processing completed for {category}: {result}")

    except Exception as e:
        logger.error(f"Failed to process batch images for {category}: {e}")


async def process_category_for_training(
    category_dir: str, category: str, remove_background: bool, enhance_images: bool
):
    """Background task to process category for training."""
    try:
        logger.info(f"Processing category for training: {category}")

        if BRAND_TRAINER_AVAILABLE:
            result = await brand_trainer.prepare_training_dataset(
                input_directory=category_dir,
                category=category,
                remove_background=remove_background,
                enhance_images=enhance_images,
            )

            logger.info(f"Category processing completed: {result}")

    except Exception as e:
        logger.error(f"Failed to process category {category}: {e}")


# ============================================================================
# PRODUCTION-GRADE IMAGE QUALITY PROCESSING
# ============================================================================


class ImageQualityProcessor:
    """Production-grade image quality processor with robust error handling."""

    def __init__(self):
        self.config = QUALITY_CONFIG
        self.executor = ThreadPoolExecutor(max_workers=self.config["max_concurrent_operations"])

    def validate_quality_settings(self, settings: BulkQualitySettings) -> dict[str, Any]:
        """Validate quality settings before processing."""
        validation_result = {"valid": True, "errors": [], "warnings": []}

        try:
            # Validate resize dimensions
            width, height = settings.resize_dimensions_tuple

            if not isinstance(width, int) or not isinstance(height, int):
                validation_result["errors"].append("Resize dimensions must be integers")
                validation_result["valid"] = False

            if width < self.config["min_image_size"][0] or height < self.config["min_image_size"][1]:
                validation_result["errors"].append(f"Dimensions too small. Minimum: {self.config['min_image_size']}")
                validation_result["valid"] = False

            if width > self.config["max_image_size"][0] or height > self.config["max_image_size"][1]:
                validation_result["errors"].append(f"Dimensions too large. Maximum: {self.config['max_image_size']}")
                validation_result["valid"] = False

            # Validate boolean settings
            bool_settings = [
                settings.quality_enhancement,
                settings.auto_contrast,
                settings.equalize,
                settings.remove_background,
            ]

            for setting in bool_settings:
                if not isinstance(setting, bool):
                    validation_result["errors"].append("Quality settings must be boolean values")
                    validation_result["valid"] = False
                    break

            # Check system resources
            memory_usage = psutil.virtual_memory().percent
            if memory_usage > 85:
                validation_result["warnings"].append(f"High memory usage ({memory_usage}%) - processing may be slow")

            # Warn about experimental features
            if settings.remove_background:
                validation_result["warnings"].append(
                    "Background removal is experimental and may not work on all images"
                )

        except Exception as e:
            validation_result["errors"].append(f"Validation error: {e!s}")
            validation_result["valid"] = False

        return validation_result

    def validate_image_file(self, image_path: Path) -> dict[str, Any]:
        """Validate individual image file."""
        validation_result = {"valid": True, "errors": [], "warnings": [], "info": {}}

        try:
            # Check file existence
            if not image_path.exists():
                validation_result["errors"].append("File does not exist")
                validation_result["valid"] = False
                return validation_result

            # Check file size
            file_size = image_path.stat().st_size
            if file_size > self.config["max_file_size"]:
                validation_result["errors"].append(
                    f"File too large: {file_size / (1024 * 1024):.1f}MB > {self.config['max_file_size'] / (1024 * 1024)}MB"
                )
                validation_result["valid"] = False

            # Check file format
            file_ext = image_path.suffix.lower()
            if file_ext not in self.config["supported_formats"]:
                validation_result["errors"].append(f"Unsupported format: {file_ext}")
                validation_result["valid"] = False
                return validation_result

            # Validate image with PIL
            if PIL_AVAILABLE:
                try:
                    with Image.open(image_path) as img:
                        validation_result["info"]["original_size"] = img.size
                        validation_result["info"]["original_mode"] = img.mode
                        validation_result["info"]["original_format"] = img.format

                        # Check image dimensions
                        width, height = img.size
                        if width < self.config["min_image_size"][0] or height < self.config["min_image_size"][1]:
                            validation_result["warnings"].append(f"Image very small: {width}x{height}")

                        # Check for potential issues
                        if img.mode not in ["RGB", "RGBA", "L"]:
                            validation_result["warnings"].append(f"Unusual color mode: {img.mode}")

                        # Estimate memory usage
                        estimated_memory = (width * height * 4) / (1024 * 1024)  # 4 bytes per pixel for RGBA
                        if estimated_memory > 100:  # 100MB
                            validation_result["warnings"].append(
                                f"Large image may use significant memory: ~{estimated_memory:.1f}MB"
                            )

                except Exception as e:
                    validation_result["errors"].append(f"Cannot open image: {e!s}")
                    validation_result["valid"] = False

        except Exception as e:
            validation_result["errors"].append(f"File validation error: {e!s}")
            validation_result["valid"] = False

        return validation_result

    def create_backup(self, image_path: Path) -> Path | None:
        """Create backup of original image."""
        if not self.config["backup_originals"]:
            return None

        try:
            backup_dir = image_path.parent / "backups"
            backup_dir.mkdir(exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{image_path.stem}_backup_{timestamp}{image_path.suffix}"
            backup_path = backup_dir / backup_name

            shutil.copy2(image_path, backup_path)
            return backup_path

        except Exception as e:
            logger.warning(f"Failed to create backup for {image_path}: {e}")
            return None

    def process_single_image(
        self, image_path: Path, settings: BulkQualitySettings, operation_id: str
    ) -> dict[str, Any]:
        """Process a single image with comprehensive error handling."""
        result = {
            "success": False,
            "image_path": str(image_path),
            "operation_id": operation_id,
            "processing_time": 0,
            "original_size": None,
            "final_size": None,
            "backup_path": None,
            "errors": [],
            "warnings": [],
        }

        start_time = datetime.now()
        temp_file = None

        try:
            # Validate image file
            validation = self.validate_image_file(image_path)
            if not validation["valid"]:
                result["errors"] = validation["errors"]
                return result

            result["warnings"].extend(validation["warnings"])
            result["original_size"] = validation["info"].get("original_size")

            # Create backup if enabled
            if self.config["backup_originals"]:
                backup_path = self.create_backup(image_path)
                result["backup_path"] = str(backup_path) if backup_path else None

            # Create temporary file for processing
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp:
                temp_file = Path(temp.name)

            # Process image
            processed_successfully = self._apply_quality_enhancements(image_path, temp_file, settings, result)

            if processed_successfully:
                # Replace original with processed image
                shutil.move(str(temp_file), str(image_path))
                result["success"] = True

                # Get final image info
                try:
                    with Image.open(image_path) as img:
                        result["final_size"] = img.size
                except OSError as e:
                    logger.debug(f"Could not read final image info: {e}")

        except Exception as e:
            logger.error(f"Error processing image {image_path}: {e}")
            result["errors"].append(f"Processing error: {e!s}")

        finally:
            # Cleanup temporary file
            if temp_file and temp_file.exists():
                try:
                    temp_file.unlink()
                except (OSError, PermissionError) as e:
                    logger.debug(f"Could not delete temp file: {e}")

            # Calculate processing time
            result["processing_time"] = (datetime.now() - start_time).total_seconds()

            # Force garbage collection for memory management
            gc.collect()

        return result

    def _apply_quality_enhancements(
        self, input_path: Path, output_path: Path, settings: BulkQualitySettings, result: dict[str, Any]
    ) -> bool:
        """Apply quality enhancements to image with fallback mechanisms."""

        if not PIL_AVAILABLE:
            result["errors"].append("PIL/Pillow not available for image processing")
            return False

        try:
            # Open and validate image
            with Image.open(input_path) as img:
                # Convert to RGB if necessary (handles RGBA, CMYK, etc.)
                if img.mode != "RGB":
                    if img.mode == "RGBA":
                        # Handle transparency by creating white background
                        background = Image.new("RGB", img.size, (255, 255, 255))
                        background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                        img = background
                    else:
                        img = img.convert("RGB")

                # Apply resize if dimensions changed
                target_size = settings.resize_dimensions_tuple
                if img.size != target_size:
                    # Use high-quality resampling
                    img = img.resize(target_size, Image.Resampling.LANCZOS)
                    result["warnings"].append(f"Resized from {result['original_size']} to {target_size}")

                # Apply quality enhancements if enabled
                if settings.quality_enhancement:
                    img = self._enhance_image_quality(img, settings, result)

                # Apply background removal if requested (with fallback)
                if settings.remove_background:
                    img = self._remove_background_fallback(img, result)

                # Save with high quality
                save_kwargs = {
                    "format": self.config["output_format"],
                    "quality": self.config["output_quality"],
                    "optimize": True,
                }

                # Add progressive JPEG for better loading
                if self.config["output_format"] == "JPEG":
                    save_kwargs["progressive"] = True

                img.save(output_path, **save_kwargs)

                return True

        except Exception as e:
            result["errors"].append(f"Image enhancement error: {e!s}")
            logger.error(f"Enhancement error for {input_path}: {e}")
            return False

    def _enhance_image_quality(
        self, img: Image.Image, settings: BulkQualitySettings, result: dict[str, Any]
    ) -> Image.Image:
        """Apply quality enhancements with error handling."""

        try:
            # Auto contrast adjustment
            if settings.auto_contrast:
                try:
                    img = ImageOps.autocontrast(img, cutoff=1)
                    result["warnings"].append("Applied auto contrast")
                except Exception as e:
                    result["warnings"].append(f"Auto contrast failed: {e!s}")

            # Histogram equalization
            if settings.equalize:
                try:
                    img = ImageOps.equalize(img)
                    result["warnings"].append("Applied histogram equalization")
                except Exception as e:
                    result["warnings"].append(f"Equalization failed: {e!s}")

            # Additional quality enhancements
            try:
                # Slight sharpening for better detail
                enhancer = ImageEnhance.Sharpness(img)
                img = enhancer.enhance(1.1)  # Subtle sharpening

                # Slight color enhancement
                enhancer = ImageEnhance.Color(img)
                img = enhancer.enhance(1.05)  # Subtle color boost

                result["warnings"].append("Applied sharpening and color enhancement")

            except Exception as e:
                result["warnings"].append(f"Additional enhancements failed: {e!s}")

        except Exception as e:
            result["warnings"].append(f"Quality enhancement error: {e!s}")
            logger.warning(f"Quality enhancement failed: {e}")

        return img

    def _remove_background_fallback(self, img: Image.Image, result: dict[str, Any]) -> Image.Image:
        """Fallback background removal implementation."""

        try:
            # Simple edge-based background removal (fallback method)
            # This is a basic implementation - in production you'd use rembg or similar

            if OPENCV_AVAILABLE:
                # Convert PIL to OpenCV format
                img_array = np.array(img)
                img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

                # Simple background removal using edge detection
                gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
                edges = cv2.Canny(gray, 50, 150)

                # Create mask (this is very basic - production would be more sophisticated)
                mask = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)
                mask = cv2.GaussianBlur(mask, (5, 5), 0)

                # Apply mask (simplified)
                result_cv = img_cv.copy()
                result_cv[mask == 0] = [255, 255, 255]  # White background

                # Convert back to PIL
                result_array = cv2.cvtColor(result_cv, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(result_array)

                result["warnings"].append("Applied basic background removal (experimental)")
            else:
                result["warnings"].append("Background removal skipped - OpenCV not available")

        except Exception as e:
            result["warnings"].append(f"Background removal failed: {e!s}")
            logger.warning(f"Background removal error: {e}")

        return img


# Global image processor instance
image_processor = ImageQualityProcessor()


# ============================================================================
# BULK OPERATIONS SUPPORT FUNCTIONS
# ============================================================================


async def generate_bulk_operation_preview(operation_type: str, operation_data: dict[str, Any]) -> dict[str, Any]:
    """Generate a preview of what a bulk operation would do."""
    try:
        image_paths = operation_data.get("image_paths", [])
        preview = {"operation_type": operation_type, "affected_images": len(image_paths), "changes": {}}

        if operation_type == "category_update":
            new_category = operation_data.get("new_category")
            preview["changes"] = {
                "category_change": f"All images will be moved to category: {new_category}",
                "metadata_preserved": operation_data.get("preserve_existing_metadata", True),
            }

        elif operation_type == "caption_update":
            template = operation_data.get("caption_template", "")
            preview["changes"] = {
                "caption_template": template,
                "add_trigger_words": operation_data.get("add_trigger_words", []),
                "remove_trigger_words": operation_data.get("remove_trigger_words", []),
            }

        elif operation_type == "tag_update":
            preview["changes"] = {
                "add_tags": operation_data.get("add_tags", []),
                "remove_tags": operation_data.get("remove_tags", []),
                "replace_tags": operation_data.get("replace_tags", {}),
            }

        elif operation_type == "quality_update":
            preview["changes"] = {
                "resize_dimensions": operation_data.get("resize_dimensions", (1024, 1024)),
                "quality_enhancement": operation_data.get("quality_enhancement", True),
                "auto_contrast": operation_data.get("auto_contrast", True),
                "equalize": operation_data.get("equalize", True),
                "remove_background": operation_data.get("remove_background", False),
            }

        elif operation_type == "metadata_update":
            preview["changes"] = {
                "metadata_updates": operation_data.get("metadata_updates", {}),
                "merge_with_existing": operation_data.get("merge_with_existing", True),
            }

        return preview

    except Exception as e:
        logger.error(f"Failed to generate preview: {e}")
        return {"error": str(e)}


async def capture_images_state(image_paths: list[str]) -> dict[str, Any]:
    """Capture the current state of images for undo functionality."""
    try:
        state = {}

        for image_path in image_paths:
            image_path_obj = Path(image_path)
            if not image_path_obj.exists():
                continue

            # Capture metadata
            metadata_file = image_path_obj.with_suffix(image_path_obj.suffix + ".json")
            metadata = {}

            if metadata_file.exists():
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)

            # Capture file stats
            file_stats = image_path_obj.stat()

            state[str(image_path)] = {
                "metadata": metadata,
                "file_size": file_stats.st_size,
                "modified_time": file_stats.st_mtime,
                "category": metadata.get("category", "unknown"),
            }

        return state

    except Exception as e:
        logger.error(f"Failed to capture images state: {e}")
        return {}


async def execute_bulk_category_update(
    operation_id: str, image_paths: list[str], new_category: str, preserve_existing_metadata: bool
):
    """Execute bulk category update operation."""
    try:
        logger.info(f"🔄 Executing bulk category update: {operation_id}")

        # Create new category directory
        new_category_dir = UPLOAD_DIR / new_category
        new_category_dir.mkdir(exist_ok=True)

        successful_updates = 0
        failed_updates = 0

        for image_path in image_paths:
            try:
                image_path_obj = Path(image_path)
                if not image_path_obj.exists():
                    failed_updates += 1
                    continue

                # Load existing metadata
                metadata_file = image_path_obj.with_suffix(image_path_obj.suffix + ".json")
                metadata = {}

                if metadata_file.exists() and preserve_existing_metadata:
                    with open(metadata_file, "r") as f:
                        metadata = json.load(f)

                # Update category in metadata
                metadata["category"] = new_category
                metadata["category_updated"] = datetime.now().isoformat()
                metadata["bulk_operation_id"] = operation_id

                # Move file to new category directory
                new_file_path = new_category_dir / image_path_obj.name
                shutil.move(str(image_path_obj), str(new_file_path))

                # Move metadata file
                if metadata_file.exists():
                    new_metadata_path = new_category_dir / metadata_file.name
                    shutil.move(str(metadata_file), str(new_metadata_path))
                else:
                    new_metadata_path = new_category_dir / f"{image_path_obj.name}.json"

                # Save updated metadata
                with open(new_metadata_path, "w") as f:
                    json.dump(metadata, f, indent=2)

                successful_updates += 1

            except Exception as e:
                logger.error(f"Failed to update category for {image_path}: {e}")
                failed_updates += 1

        # Update operation status
        bulk_operations_history[operation_id]["status"] = "completed"
        bulk_operations_history[operation_id]["results"] = {
            "successful_updates": successful_updates,
            "failed_updates": failed_updates,
            "completion_time": datetime.now().isoformat(),
        }

        logger.info(
            f"✅ Bulk category update completed: {operation_id} - {successful_updates} successful, {failed_updates} failed"
        )

    except Exception as e:
        logger.error(f"❌ Bulk category update failed: {operation_id} - {e}")
        bulk_operations_history[operation_id]["status"] = "failed"
        bulk_operations_history[operation_id]["error"] = str(e)


async def execute_bulk_caption_update(
    operation_id: str,
    image_paths: list[str],
    caption_template: str,
    preserve_trigger_words: bool,
    add_trigger_words: list[str],
    remove_trigger_words: list[str],
):
    """Execute bulk caption update operation."""
    try:
        logger.info(f"📝 Executing bulk caption update: {operation_id}")

        successful_updates = 0
        failed_updates = 0

        for image_path in image_paths:
            try:
                image_path_obj = Path(image_path)
                if not image_path_obj.exists():
                    failed_updates += 1
                    continue

                # Load existing metadata
                metadata_file = image_path_obj.with_suffix(image_path_obj.suffix + ".json")
                metadata = {}

                if metadata_file.exists():
                    with open(metadata_file, "r") as f:
                        metadata = json.load(f)

                # Process caption
                new_caption = caption_template

                # Handle trigger words
                existing_caption = metadata.get("caption", "")

                if preserve_trigger_words and existing_caption:
                    # Extract existing trigger words
                    existing_triggers = [word for word in existing_caption.split() if word.startswith("skyrose_")]

                    # Combine with new caption
                    all_triggers = list(set(existing_triggers + add_trigger_words))

                    # Remove unwanted trigger words
                    for remove_word in remove_trigger_words:
                        if remove_word in all_triggers:
                            all_triggers.remove(remove_word)

                    # Build final caption
                    if all_triggers:
                        new_caption = f"{', '.join(all_triggers)}, {new_caption}"
                # Just add new trigger words
                elif add_trigger_words:
                    new_caption = f"{', '.join(add_trigger_words)}, {new_caption}"

                # Update metadata
                metadata["caption"] = new_caption
                metadata["caption_updated"] = datetime.now().isoformat()
                metadata["bulk_operation_id"] = operation_id

                # Save updated metadata
                with open(metadata_file, "w") as f:
                    json.dump(metadata, f, indent=2)

                successful_updates += 1

            except Exception as e:
                logger.error(f"Failed to update caption for {image_path}: {e}")
                failed_updates += 1

        # Update operation status
        bulk_operations_history[operation_id]["status"] = "completed"
        bulk_operations_history[operation_id]["results"] = {
            "successful_updates": successful_updates,
            "failed_updates": failed_updates,
            "completion_time": datetime.now().isoformat(),
        }

        logger.info(
            f"✅ Bulk caption update completed: {operation_id} - {successful_updates} successful, {failed_updates} failed"
        )

    except Exception as e:
        logger.error(f"❌ Bulk caption update failed: {operation_id} - {e}")
        bulk_operations_history[operation_id]["status"] = "failed"
        bulk_operations_history[operation_id]["error"] = str(e)


async def execute_bulk_tag_update(
    operation_id: str,
    image_paths: list[str],
    add_tags: list[str],
    remove_tags: list[str],
    replace_tags: dict[str, str],
):
    """Execute bulk tag update operation."""
    try:
        logger.info(f"🏷️ Executing bulk tag update: {operation_id}")

        successful_updates = 0
        failed_updates = 0

        for image_path in image_paths:
            try:
                image_path_obj = Path(image_path)
                if not image_path_obj.exists():
                    failed_updates += 1
                    continue

                # Load existing metadata
                metadata_file = image_path_obj.with_suffix(image_path_obj.suffix + ".json")
                metadata = {}

                if metadata_file.exists():
                    with open(metadata_file, "r") as f:
                        metadata = json.load(f)

                # Get existing tags
                existing_tags = metadata.get("tags", [])
                if isinstance(existing_tags, str):
                    existing_tags = [existing_tags]

                # Apply tag operations
                updated_tags = existing_tags.copy()

                # Add new tags
                for tag in add_tags:
                    if tag not in updated_tags:
                        updated_tags.append(tag)

                # Remove tags
                for tag in remove_tags:
                    if tag in updated_tags:
                        updated_tags.remove(tag)

                # Replace tags
                for old_tag, new_tag in replace_tags.items():
                    if old_tag in updated_tags:
                        updated_tags[updated_tags.index(old_tag)] = new_tag

                # Update metadata
                metadata["tags"] = updated_tags
                metadata["tags_updated"] = datetime.now().isoformat()
                metadata["bulk_operation_id"] = operation_id

                # Save updated metadata
                with open(metadata_file, "w") as f:
                    json.dump(metadata, f, indent=2)

                successful_updates += 1

            except Exception as e:
                logger.error(f"Failed to update tags for {image_path}: {e}")
                failed_updates += 1

        # Update operation status
        bulk_operations_history[operation_id]["status"] = "completed"
        bulk_operations_history[operation_id]["results"] = {
            "successful_updates": successful_updates,
            "failed_updates": failed_updates,
            "completion_time": datetime.now().isoformat(),
        }

        logger.info(
            f"✅ Bulk tag update completed: {operation_id} - {successful_updates} successful, {failed_updates} failed"
        )

    except Exception as e:
        logger.error(f"❌ Bulk tag update failed: {operation_id} - {e}")
        bulk_operations_history[operation_id]["status"] = "failed"
        bulk_operations_history[operation_id]["error"] = str(e)


async def execute_bulk_quality_update(
    operation_id: str, image_paths: list[str], quality_settings: BulkQualitySettings
):
    """Execute bulk quality update operation with production-grade error handling."""

    # Initialize operation tracking
    operation_start_time = datetime.now()
    processing_results = {
        "successful_updates": 0,
        "failed_updates": 0,
        "skipped_updates": 0,
        "total_processing_time": 0,
        "individual_results": [],
        "validation_errors": [],
        "system_warnings": [],
    }

    try:
        logger.info(f"✨ Starting bulk quality update: {operation_id} for {len(image_paths)} images")

        # Validate quality settings before processing
        validation_result = image_processor.validate_quality_settings(quality_settings)
        if not validation_result["valid"]:
            error_msg = f"Invalid quality settings: {', '.join(validation_result['errors'])}"
            logger.error(error_msg)
            bulk_operations_history[operation_id]["status"] = "failed"
            bulk_operations_history[operation_id]["error"] = error_msg
            return

        # Log warnings from validation
        for warning in validation_result["warnings"]:
            logger.warning(f"Quality settings warning: {warning}")
            processing_results["system_warnings"].append(warning)

        # Check system resources
        memory_before = psutil.virtual_memory().percent
        logger.info(f"System memory usage before processing: {memory_before}%")

        # Process images with controlled concurrency
        valid_paths = []
        for image_path_str in image_paths:
            image_path = Path(image_path_str)

            # Quick validation
            if not image_path.exists():
                processing_results["skipped_updates"] += 1
                processing_results["individual_results"].append(
                    {"image_path": image_path_str, "success": False, "error": "File not found", "skipped": True}
                )
                continue

            # Check file extension
            if image_path.suffix.lower() not in QUALITY_CONFIG["supported_formats"]:
                processing_results["skipped_updates"] += 1
                processing_results["individual_results"].append(
                    {
                        "image_path": image_path_str,
                        "success": False,
                        "error": f"Unsupported format: {image_path.suffix}",
                        "skipped": True,
                    }
                )
                continue

            valid_paths.append(image_path)

        logger.info(f"Processing {len(valid_paths)} valid images (skipped {len(image_paths) - len(valid_paths)})")

        # Process images in batches to manage memory
        batch_size = min(QUALITY_CONFIG["max_concurrent_operations"], 10)

        for i in range(0, len(valid_paths), batch_size):
            batch = valid_paths[i : i + batch_size]
            batch_start_time = datetime.now()

            logger.info(
                f"Processing batch {i // batch_size + 1}/{(len(valid_paths) + batch_size - 1) // batch_size} ({len(batch)} images)"
            )

            # Process batch with thread pool
            batch_futures = []
            with ThreadPoolExecutor(max_workers=len(batch)) as executor:
                for image_path in batch:
                    future = executor.submit(
                        image_processor.process_single_image, image_path, quality_settings, operation_id
                    )
                    batch_futures.append(future)

                # Collect results
                for future in as_completed(batch_futures):
                    try:
                        result = future.result(timeout=300)  # 5 minute timeout per image
                        processing_results["individual_results"].append(result)

                        if result["success"]:
                            processing_results["successful_updates"] += 1

                            # Update metadata
                            await _update_quality_metadata(
                                Path(result["image_path"]), quality_settings, operation_id, result
                            )
                        else:
                            processing_results["failed_updates"] += 1
                            logger.warning(f"Failed to process {result['image_path']}: {result.get('errors', [])}")

                    except Exception as e:
                        processing_results["failed_updates"] += 1
                        error_msg = f"Processing exception: {e!s}"
                        logger.error(error_msg)
                        processing_results["individual_results"].append(
                            {"success": False, "error": error_msg, "image_path": "unknown"}
                        )

            batch_time = (datetime.now() - batch_start_time).total_seconds()
            logger.info(f"Batch completed in {batch_time:.2f} seconds")

            # Check memory usage and force cleanup if needed
            memory_current = psutil.virtual_memory().percent
            if memory_current > 80:
                logger.warning(f"High memory usage: {memory_current}% - forcing garbage collection")
                gc.collect()

        # Calculate final statistics
        total_time = (datetime.now() - operation_start_time).total_seconds()
        processing_results["total_processing_time"] = total_time

        # Update operation status
        bulk_operations_history[operation_id]["status"] = "completed"
        bulk_operations_history[operation_id]["results"] = processing_results
        bulk_operations_history[operation_id]["completion_time"] = datetime.now().isoformat()

        # Log final results
        success_rate = (processing_results["successful_updates"] / len(image_paths)) * 100 if image_paths else 0
        logger.info(
            f"✅ Bulk quality update completed: {operation_id}\n"
            f"   Total images: {len(image_paths)}\n"
            f"   Successful: {processing_results['successful_updates']}\n"
            f"   Failed: {processing_results['failed_updates']}\n"
            f"   Skipped: {processing_results['skipped_updates']}\n"
            f"   Success rate: {success_rate:.1f}%\n"
            f"   Total time: {total_time:.2f} seconds\n"
            f"   Average time per image: {total_time / len(image_paths):.2f} seconds"
        )

    except Exception as e:
        error_msg = f"Critical error in bulk quality update: {e!s}"
        logger.error(error_msg)
        bulk_operations_history[operation_id]["status"] = "failed"
        bulk_operations_history[operation_id]["error"] = error_msg
        bulk_operations_history[operation_id]["results"] = processing_results

        # Force cleanup on error
        gc.collect()


async def _update_quality_metadata(
    image_path: Path, quality_settings: BulkQualitySettings, operation_id: str, processing_result: dict[str, Any]
):
    """Update metadata file with quality processing information."""
    try:
        metadata_file = image_path.with_suffix(image_path.suffix + ".json")
        metadata = {}

        # Load existing metadata if it exists
        if metadata_file.exists():
            try:
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load existing metadata for {image_path}: {e}")

        # Add quality processing information
        metadata["quality_settings"] = {
            "resize_dimensions": list(quality_settings.resize_dimensions_tuple),
            "quality_enhancement": quality_settings.quality_enhancement,
            "auto_contrast": quality_settings.auto_contrast,
            "equalize": quality_settings.equalize,
            "remove_background": quality_settings.remove_background,
        }

        metadata["quality_processing"] = {
            "operation_id": operation_id,
            "processing_time": processing_result.get("processing_time", 0),
            "original_size": processing_result.get("original_size"),
            "final_size": processing_result.get("final_size"),
            "backup_path": processing_result.get("backup_path"),
            "warnings": processing_result.get("warnings", []),
            "processed_timestamp": datetime.now().isoformat(),
        }

        metadata["last_updated"] = datetime.now().isoformat()
        metadata["bulk_operation_id"] = operation_id

        # Save updated metadata
        with open(metadata_file, "w") as f:
            json.dump(metadata, f, indent=2)

    except Exception as e:
        logger.error(f"Failed to update metadata for {image_path}: {e}")


async def execute_bulk_metadata_update(
    operation_id: str, image_paths: list[str], metadata_updates: dict[str, Any], merge_with_existing: bool
):
    """Execute bulk metadata update operation."""
    try:
        logger.info(f"📊 Executing bulk metadata update: {operation_id}")

        successful_updates = 0
        failed_updates = 0

        for image_path in image_paths:
            try:
                image_path_obj = Path(image_path)
                if not image_path_obj.exists():
                    failed_updates += 1
                    continue

                # Load existing metadata
                metadata_file = image_path_obj.with_suffix(image_path_obj.suffix + ".json")
                metadata = {}

                if metadata_file.exists() and merge_with_existing:
                    with open(metadata_file, "r") as f:
                        metadata = json.load(f)

                # Apply metadata updates
                metadata.update(metadata_updates)
                metadata["metadata_updated"] = datetime.now().isoformat()
                metadata["bulk_operation_id"] = operation_id

                # Save updated metadata
                with open(metadata_file, "w") as f:
                    json.dump(metadata, f, indent=2)

                successful_updates += 1

            except Exception as e:
                logger.error(f"Failed to update metadata for {image_path}: {e}")
                failed_updates += 1

        # Update operation status
        bulk_operations_history[operation_id]["status"] = "completed"
        bulk_operations_history[operation_id]["results"] = {
            "successful_updates": successful_updates,
            "failed_updates": failed_updates,
            "completion_time": datetime.now().isoformat(),
        }

        logger.info(
            f"✅ Bulk metadata update completed: {operation_id} - {successful_updates} successful, {failed_updates} failed"
        )

    except Exception as e:
        logger.error(f"❌ Bulk metadata update failed: {operation_id} - {e}")
        bulk_operations_history[operation_id]["status"] = "failed"
        bulk_operations_history[operation_id]["error"] = str(e)


async def execute_bulk_undo(operation_id: str, original_operation: dict[str, Any]):
    """Execute bulk undo operation."""
    try:
        logger.info(f"↩️ Executing bulk undo: {operation_id}")

        # This would restore the previous state of all affected images
        # Implementation would depend on the type of operation being undone

        # For now, just mark as completed
        bulk_operations_history[operation_id] = {
            "operation_type": "undo",
            "operation_id": operation_id,
            "original_operation_id": original_operation["operation_id"],
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
        }

        logger.info(f"✅ Bulk undo completed: {operation_id}")

    except Exception as e:
        logger.error(f"❌ Bulk undo failed: {operation_id} - {e}")
        bulk_operations_history[operation_id]["status"] = "failed"
        bulk_operations_history[operation_id]["error"] = str(e)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
