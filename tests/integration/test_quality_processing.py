#!/usr/bin/env python3
"""
Test script for production-grade bulk quality processing
Tests the enhanced quality update functionality with comprehensive error handling
"""

from pathlib import Path
import shutil
import sys
import time

from PIL import Image
import requests


# Test configuration
API_BASE = "http://localhost:8001"
TEST_DIR = Path("test_quality_images")


def create_test_images():
    """Create test images for quality processing."""

    TEST_DIR.mkdir(exist_ok=True)

    # Create test images with different characteristics
    test_images = []

    # Test image 1: Standard RGB image
    img1 = Image.new("RGB", (800, 600), color="red")
    img1_path = TEST_DIR / "test_rgb.jpg"
    img1.save(img1_path, "JPEG", quality=80)
    test_images.append(str(img1_path))

    # Test image 2: RGBA image (with transparency)
    img2 = Image.new("RGBA", (1200, 900), color=(0, 255, 0, 128))
    img2_path = TEST_DIR / "test_rgba.png"
    img2.save(img2_path, "PNG")
    test_images.append(str(img2_path))

    # Test image 3: Large image
    img3 = Image.new("RGB", (2048, 1536), color="blue")
    img3_path = TEST_DIR / "test_large.jpg"
    img3.save(img3_path, "JPEG", quality=90)
    test_images.append(str(img3_path))

    # Test image 4: Small image
    img4 = Image.new("RGB", (200, 150), color="yellow")
    img4_path = TEST_DIR / "test_small.jpg"
    img4.save(img4_path, "JPEG", quality=70)
    test_images.append(str(img4_path))

    return test_images


def test_quality_settings_validation():
    """Test quality settings validation."""

    # Test valid settings
    valid_settings = {
        "image_paths": ["test.jpg"],
        "resize_dimensions": [1024, 1024],
        "quality_enhancement": True,
        "auto_contrast": True,
        "equalize": True,
        "remove_background": False,
    }

    response = requests.post(f"{API_BASE}/bulk/preview", json={"operation_type": "quality_update", **valid_settings})

    if response.status_code == 200:
        pass
    else:
        return False

    # Test invalid dimensions
    invalid_settings = {
        "image_paths": ["test.jpg"],
        "resize_dimensions": [50, 50],  # Too small
        "quality_enhancement": True,
        "auto_contrast": True,
        "equalize": True,
        "remove_background": False,
    }

    response = requests.post(f"{API_BASE}/bulk/quality-update", json=invalid_settings)

    if response.status_code != 200:
        pass
    else:
        return False

    return True


def test_bulk_quality_processing(test_images):
    """Test the bulk quality processing functionality."""

    # Test settings
    quality_settings = {
        "image_paths": test_images,
        "resize_dimensions": [1024, 1024],
        "quality_enhancement": True,
        "auto_contrast": True,
        "equalize": True,
        "remove_background": False,
    }

    # Start bulk quality update
    response = requests.post(f"{API_BASE}/bulk/quality-update", json=quality_settings)

    if response.status_code != 200:
        return False

    result = response.json()
    if not result.get("success"):
        return False

    operation_id = result.get("operation_id")

    # Monitor operation progress
    max_wait_time = 120  # 2 minutes
    wait_time = 0

    while wait_time < max_wait_time:
        time.sleep(5)
        wait_time += 5

        # Check operation status
        status_response = requests.get(f"{API_BASE}/bulk/operations/{operation_id}")

        if status_response.status_code != 200:
            return False

        status_result = status_response.json()
        operation = status_result.get("operation", {})
        status = operation.get("status", "unknown")

        if status == "completed":
            results = operation.get("results", {})
            successful = results.get("successful_updates", 0)
            results.get("failed_updates", 0)
            results.get("skipped_updates", 0)

            return successful > 0

        elif status == "failed":
            operation.get("error", "Unknown error")
            return False

    return False


def test_error_handling():
    """Test error handling with invalid inputs."""

    # Test with non-existent files
    invalid_settings = {
        "image_paths": ["nonexistent1.jpg", "nonexistent2.jpg"],
        "resize_dimensions": [1024, 1024],
        "quality_enhancement": True,
        "auto_contrast": True,
        "equalize": True,
        "remove_background": False,
    }

    response = requests.post(f"{API_BASE}/bulk/quality-update", json=invalid_settings)

    if response.status_code == 200:
        result = response.json()
        operation_id = result.get("operation_id")

        # Wait for operation to complete
        time.sleep(10)

        status_response = requests.get(f"{API_BASE}/bulk/operations/{operation_id}")
        if status_response.status_code == 200:
            status_result = status_response.json()
            operation = status_result.get("operation", {})
            results = operation.get("results", {})

            skipped = results.get("skipped_updates", 0)
            if skipped > 0:
                return True

    return False


def verify_processed_images(test_images):
    """Verify that images were actually processed."""

    processed_count = 0

    for image_path in test_images:
        path_obj = Path(image_path)
        if not path_obj.exists():
            continue

        # Check if image was resized to 1024x1024
        try:
            with Image.open(path_obj) as img:
                if img.size == (1024, 1024):
                    processed_count += 1
                else:
                    pass
        except Exception:
            pass

    return processed_count > 0


def cleanup_test_files():
    """Clean up test files."""

    try:
        if TEST_DIR.exists():
            shutil.rmtree(TEST_DIR)
    except Exception:
        pass


def main():
    """Run all quality processing tests."""

    # Check if server is running
    try:
        response = requests.get(f"{API_BASE}/bulk/operations")
        if response.status_code != 200:
            sys.exit(1)
    except Exception:
        sys.exit(1)

    # Run tests
    tests_passed = 0
    total_tests = 4

    try:
        # Create test images
        test_images = create_test_images()

        # Test 1: Quality settings validation
        if test_quality_settings_validation():
            tests_passed += 1

        # Test 2: Bulk quality processing
        if test_bulk_quality_processing(test_images):
            tests_passed += 1

        # Test 3: Error handling
        if test_error_handling():
            tests_passed += 1

        # Test 4: Verify processed images
        if verify_processed_images(test_images):
            tests_passed += 1

    finally:
        # Always cleanup
        cleanup_test_files()

    # Results

    if tests_passed == total_tests:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
