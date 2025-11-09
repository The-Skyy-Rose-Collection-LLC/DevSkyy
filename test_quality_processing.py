#!/usr/bin/env python3
"""
Test script for production-grade bulk quality processing
Tests the enhanced quality update functionality with comprehensive error handling
"""

import requests
import time
import sys
from pathlib import Path
from PIL import Image
import shutil

# Test configuration
API_BASE = "http://localhost:8001"
TEST_DIR = Path("test_quality_images")

def create_test_images():
    """Create test images for quality processing."""
    print("🖼️ Creating test images...")
    
    TEST_DIR.mkdir(exist_ok=True)
    
    # Create test images with different characteristics
    test_images = []
    
    # Test image 1: Standard RGB image
    img1 = Image.new('RGB', (800, 600), color='red')
    img1_path = TEST_DIR / "test_rgb.jpg"
    img1.save(img1_path, "JPEG", quality=80)
    test_images.append(str(img1_path))
    
    # Test image 2: RGBA image (with transparency)
    img2 = Image.new('RGBA', (1200, 900), color=(0, 255, 0, 128))
    img2_path = TEST_DIR / "test_rgba.png"
    img2.save(img2_path, "PNG")
    test_images.append(str(img2_path))
    
    # Test image 3: Large image
    img3 = Image.new('RGB', (2048, 1536), color='blue')
    img3_path = TEST_DIR / "test_large.jpg"
    img3.save(img3_path, "JPEG", quality=90)
    test_images.append(str(img3_path))
    
    # Test image 4: Small image
    img4 = Image.new('RGB', (200, 150), color='yellow')
    img4_path = TEST_DIR / "test_small.jpg"
    img4.save(img4_path, "JPEG", quality=70)
    test_images.append(str(img4_path))
    
    print(f"✅ Created {len(test_images)} test images")
    return test_images

def test_quality_settings_validation():
    """Test quality settings validation."""
    print("\n🔍 Testing quality settings validation...")
    
    # Test valid settings
    valid_settings = {
        "image_paths": ["test.jpg"],
        "resize_dimensions": [1024, 1024],
        "quality_enhancement": True,
        "auto_contrast": True,
        "equalize": True,
        "remove_background": False
    }
    
    response = requests.post(f"{API_BASE}/bulk/preview", json={
        "operation_type": "quality_update",
        **valid_settings
    })
    
    if response.status_code == 200:
        print("✅ Valid settings accepted")
    else:
        print(f"❌ Valid settings rejected: {response.status_code}")
        return False
    
    # Test invalid dimensions
    invalid_settings = {
        "image_paths": ["test.jpg"],
        "resize_dimensions": [50, 50],  # Too small
        "quality_enhancement": True,
        "auto_contrast": True,
        "equalize": True,
        "remove_background": False
    }
    
    response = requests.post(f"{API_BASE}/bulk/quality-update", json=invalid_settings)
    
    if response.status_code != 200:
        print("✅ Invalid dimensions properly rejected")
    else:
        print("❌ Invalid dimensions should have been rejected")
        return False
    
    return True

def test_bulk_quality_processing(test_images):
    """Test the bulk quality processing functionality."""
    print(f"\n⚡ Testing bulk quality processing with {len(test_images)} images...")
    
    # Test settings
    quality_settings = {
        "image_paths": test_images,
        "resize_dimensions": [1024, 1024],
        "quality_enhancement": True,
        "auto_contrast": True,
        "equalize": True,
        "remove_background": False
    }
    
    # Start bulk quality update
    response = requests.post(f"{API_BASE}/bulk/quality-update", json=quality_settings)
    
    if response.status_code != 200:
        print(f"❌ Bulk quality update failed: {response.status_code}")
        print(f"Response: {response.text}")
        return False
    
    result = response.json()
    if not result.get("success"):
        print(f"❌ Bulk quality update not successful: {result}")
        return False
    
    operation_id = result.get("operation_id")
    print(f"✅ Bulk quality update started: {operation_id}")
    
    # Monitor operation progress
    max_wait_time = 120  # 2 minutes
    wait_time = 0
    
    while wait_time < max_wait_time:
        time.sleep(5)
        wait_time += 5
        
        # Check operation status
        status_response = requests.get(f"{API_BASE}/bulk/operations/{operation_id}")
        
        if status_response.status_code != 200:
            print(f"❌ Failed to get operation status: {status_response.status_code}")
            return False
        
        status_result = status_response.json()
        operation = status_result.get("operation", {})
        status = operation.get("status", "unknown")
        
        print(f"⏳ Operation status: {status} (waited {wait_time}s)")
        
        if status == "completed":
            results = operation.get("results", {})
            successful = results.get("successful_updates", 0)
            failed = results.get("failed_updates", 0)
            skipped = results.get("skipped_updates", 0)
            
            print(f"✅ Operation completed!")
            print(f"   Successful: {successful}")
            print(f"   Failed: {failed}")
            print(f"   Skipped: {skipped}")
            
            if successful > 0:
                print("✅ Quality processing test PASSED")
                return True
            else:
                print("❌ No images were successfully processed")
                return False
        
        elif status == "failed":
            error = operation.get("error", "Unknown error")
            print(f"❌ Operation failed: {error}")
            return False
    
    print(f"❌ Operation timed out after {max_wait_time} seconds")
    return False

def test_error_handling():
    """Test error handling with invalid inputs."""
    print("\n🛡️ Testing error handling...")
    
    # Test with non-existent files
    invalid_settings = {
        "image_paths": ["nonexistent1.jpg", "nonexistent2.jpg"],
        "resize_dimensions": [1024, 1024],
        "quality_enhancement": True,
        "auto_contrast": True,
        "equalize": True,
        "remove_background": False
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
                print("✅ Non-existent files properly skipped")
                return True
    
    print("❌ Error handling test failed")
    return False

def verify_processed_images(test_images):
    """Verify that images were actually processed."""
    print("\n🔍 Verifying processed images...")
    
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
                    print(f"✅ {path_obj.name}: Correctly resized to {img.size}")
                else:
                    print(f"⚠️ {path_obj.name}: Size is {img.size}, expected (1024, 1024)")
        except Exception as e:
            print(f"❌ {path_obj.name}: Error opening image: {e}")
    
    if processed_count > 0:
        print(f"✅ {processed_count}/{len(test_images)} images were properly processed")
        return True
    else:
        print("❌ No images were properly processed")
        return False

def cleanup_test_files():
    """Clean up test files."""
    print("\n🧹 Cleaning up test files...")
    
    try:
        if TEST_DIR.exists():
            shutil.rmtree(TEST_DIR)
        print("✅ Test files cleaned up")
    except Exception as e:
        print(f"⚠️ Failed to clean up test files: {e}")

def main():
    """Run all quality processing tests."""
    print("🌹 Skyy Rose Collection - Quality Processing Test Suite")
    print("=" * 60)
    
    # Check if server is running
    try:
        response = requests.get(f"{API_BASE}/bulk/operations")
        if response.status_code != 200:
            print("❌ Server is not running or not responding")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        sys.exit(1)
    
    print("✅ Server is running")
    
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
    print("\n" + "=" * 60)
    print(f"🎯 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 ALL TESTS PASSED! Quality processing is working correctly.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the implementation.")
        sys.exit(1)

if __name__ == "__main__":
    main()
