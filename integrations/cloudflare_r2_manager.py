# cloudflare_r2_manager.py
import hashlib
import io
from datetime import datetime

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from PIL import Image


class CloudflareR2Manager:
    """
    Complete Cloudflare R2 CDN management for SkyyRose
    Handles uploads, optimization, and public URL generation
    """

    def __init__(
        self,
        account_id: str,
        access_key_id: str,
        secret_access_key: str,
        bucket_name: str = "skyyrose-products",
        public_domain: str | None = None,
    ):
        """
        Initialize R2 client

        Setup:
        1. Go to Cloudflare Dashboard → R2
        2. Create bucket: skyyrose-products
        3. Generate API token with R2 read/write permissions
        4. Enable public access for bucket
        5. Optional: Setup custom domain (cdn.skyyrose.co)
        """

        self.account_id = account_id
        self.bucket_name = bucket_name

        # Public domain (either R2 public URL or custom domain)
        self.public_domain = public_domain or f"https://pub-{account_id}.r2.dev"

        # Initialize S3-compatible client for R2
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
            region_name="auto",  # R2 uses 'auto' for region
        )

        print(f"✅ R2 Manager initialized for bucket: {bucket_name}")

    def upload_product_image(
        self,
        image_path: str,
        product_sku: str,
        image_type: str,
        optimize: bool = True,
        max_size_kb: int = 500,
    ) -> dict[str, str]:
        """
        Upload product image with optimization

        Args:
            image_path: Local path or URL to image
            product_sku: Product SKU (e.g., 'SRS-SIG-001')
            image_type: Type (e.g., 'hero', 'detail_fabric', 'back')
            optimize: Whether to optimize image size
            max_size_kb: Maximum file size in KB

        Returns:
            {
                'url': 'https://cdn.skyyrose.co/products/SRS-SIG-001/hero_2k.webp',
                'size_bytes': 245678,
                'format': 'webp',
                'dimensions': [2048, 2048]
            }
        """

        print(f"  → Uploading {image_type} for {product_sku}...")

        # Load image
        if image_path.startswith("http"):
            # Download from URL
            import requests

            response = requests.get(image_path, timeout=30)
            response.raise_for_status()
            img = Image.open(io.BytesIO(response.content))
        else:
            # Load from local file
            img = Image.open(image_path)

        # Optimize if requested
        if optimize:
            img = self._optimize_image(img, max_size_kb)

        # Convert to WebP (better compression than PNG)
        img_byte_arr = io.BytesIO()
        img.save(
            img_byte_arr,
            format="WEBP",
            quality=90,
            method=6,  # High quality  # Best compression
        )
        img_byte_arr.seek(0)

        # Generate object key
        # Format: products/{sku}/{image_type}_2k.webp
        object_key = f"products/{product_sku}/{image_type}_2k.webp"

        # Generate content hash for cache busting
        content_hash = hashlib.md5(img_byte_arr.getvalue(), usedforsecurity=False).hexdigest()[:8]

        # Upload to R2
        try:
            self.s3_client.upload_fileobj(
                img_byte_arr,
                self.bucket_name,
                object_key,
                ExtraArgs={
                    "ContentType": "image/webp",
                    "CacheControl": "public, max-age=31536000",  # 1 year cache
                    "Metadata": {
                        "product_sku": product_sku,
                        "image_type": image_type,
                        "upload_date": datetime.now().isoformat(),
                        "content_hash": content_hash,
                    },
                },
            )

            # Generate public URL
            public_url = f"{self.public_domain}/{object_key}"

            print(f"    ✓ Uploaded: {public_url}")

            return {
                "url": public_url,
                "size_bytes": len(img_byte_arr.getvalue()),
                "format": "webp",
                "dimensions": list(img.size),
                "object_key": object_key,
            }

        except ClientError as e:
            print(f"    ✗ Upload failed: {e}")
            raise

    def _optimize_image(self, img: Image.Image, max_size_kb: int) -> Image.Image:
        """
        Optimize image to target file size while maintaining quality
        """

        # Start with current image
        optimized = img.copy()

        # Convert RGBA to RGB if needed (WebP handles both, but RGB is smaller)
        if optimized.mode == "RGBA":
            background = Image.new("RGB", optimized.size, (255, 255, 255))
            background.paste(optimized, mask=optimized.split()[3])
            optimized = background

        # Try different quality settings to hit target size
        quality = 95
        while quality > 60:
            buffer = io.BytesIO()
            optimized.save(buffer, format="WEBP", quality=quality, method=6)
            size_kb = len(buffer.getvalue()) / 1024

            if size_kb <= max_size_kb:
                break

            quality -= 5

        print(f"    → Optimized to {size_kb:.1f}KB (quality: {quality})")

        return optimized

    def upload_batch(
        self, images: dict[str, str], product_sku: str, optimize: bool = True
    ) -> dict[str, dict]:
        """
        Upload multiple images in batch

        Args:
            images: {'hero': '/path/to/hero.png', 'back': '/path/to/back.png', ...}
            product_sku: Product SKU
            optimize: Whether to optimize images

        Returns:
            {'hero': {...upload_result...}, 'back': {...upload_result...}, ...}
        """

        results = {}

        for image_type, image_path in images.items():
            result = self.upload_product_image(
                image_path=image_path,
                product_sku=product_sku,
                image_type=image_type,
                optimize=optimize,
            )
            results[image_type] = result

        return results

    def delete_product_images(self, product_sku: str) -> int:
        """
        Delete all images for a product

        Returns:
            Number of files deleted
        """

        prefix = f"products/{product_sku}/"

        # List all objects with prefix
        response = self.s3_client.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)

        if "Contents" not in response:
            print(f"  → No images found for {product_sku}")
            return 0

        # Delete all objects
        objects_to_delete = [{"Key": obj["Key"]} for obj in response["Contents"]]

        self.s3_client.delete_objects(
            Bucket=self.bucket_name, Delete={"Objects": objects_to_delete}
        )

        deleted_count = len(objects_to_delete)
        print(f"  ✓ Deleted {deleted_count} images for {product_sku}")

        return deleted_count

    def get_product_images(self, product_sku: str) -> list[dict]:
        """
        List all images for a product

        Returns:
            [
                {
                    'key': 'products/SKU/hero_2k.webp',
                    'url': 'https://cdn.skyyrose.co/...',
                    'size_bytes': 123456,
                    'last_modified': '2025-01-03T...'
                },
                ...
            ]
        """

        prefix = f"products/{product_sku}/"

        response = self.s3_client.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)

        if "Contents" not in response:
            return []

        images = []
        for obj in response["Contents"]:
            images.append(
                {
                    "key": obj["Key"],
                    "url": f"{self.public_domain}/{obj['Key']}",
                    "size_bytes": obj["Size"],
                    "last_modified": obj["LastModified"].isoformat(),
                }
            )

        return images

    def setup_bucket_lifecycle(self):
        """
        Configure bucket lifecycle rules
        - Delete old product images after 2 years
        - Move to infrequent access after 6 months
        """

        lifecycle_config = {
            "Rules": [
                {
                    "Id": "DeleteOldProducts",
                    "Status": "Enabled",
                    "Prefix": "products/",
                    "Expiration": {"Days": 730},  # 2 years
                },
                {
                    "Id": "DeleteTempFiles",
                    "Status": "Enabled",
                    "Prefix": "temp/",
                    "Expiration": {"Days": 7},  # 1 week
                },
            ]
        }

        try:
            self.s3_client.put_bucket_lifecycle_configuration(
                Bucket=self.bucket_name, LifecycleConfiguration=lifecycle_config
            )
            print("✅ Bucket lifecycle rules configured")
        except ClientError as e:
            print(f"⚠️  Could not set lifecycle rules: {e}")

    def setup_cors(self):
        """
        Configure CORS for web access
        """

        cors_config = {
            "CORSRules": [
                {
                    "AllowedOrigins": ["https://skyyrose.co", "https://*.skyyrose.co"],
                    "AllowedMethods": ["GET", "HEAD"],
                    "AllowedHeaders": ["*"],
                    "MaxAgeSeconds": 3600,
                }
            ]
        }

        try:
            self.s3_client.put_bucket_cors(Bucket=self.bucket_name, CORSConfiguration=cors_config)
            print("✅ CORS rules configured")
        except ClientError as e:
            print(f"⚠️  Could not set CORS rules: {e}")

    def get_storage_stats(self) -> dict:
        """
        Get storage usage statistics
        """

        # List all objects
        paginator = self.s3_client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=self.bucket_name)

        total_size = 0
        total_count = 0

        for page in pages:
            if "Contents" in page:
                for obj in page["Contents"]:
                    total_size += obj["Size"]
                    total_count += 1

        return {
            "total_files": total_count,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "total_size_gb": round(total_size / (1024 * 1024 * 1024), 3),
            "free_tier_remaining_gb": max(0, 10 - total_size / (1024 * 1024 * 1024)),
        }


def setup_r2_bucket():
    """
    First-time setup script for R2 bucket
    Run this once to configure your bucket
    """

    print("🌹 SkyyRose R2 Bucket Setup")
    print("=" * 80)

    account_id = input("Enter Cloudflare Account ID: ")
    access_key = input("Enter R2 Access Key: ")
    secret_key = input("Enter R2 Secret Key: ")
    bucket_name = input("Enter Bucket Name [skyyrose-products]: ") or "skyyrose-products"

    r2 = CloudflareR2Manager(
        account_id=account_id,
        access_key_id=access_key,
        secret_access_key=secret_key,
        bucket_name=bucket_name,
    )

    # Create bucket if it doesn't exist
    try:
        r2.s3_client.create_bucket(Bucket=bucket_name)
        print(f"✅ Created bucket: {bucket_name}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "BucketAlreadyOwnedByYou":
            print(f"✅ Bucket already exists: {bucket_name}")
        else:
            print(f"❌ Error creating bucket: {e}")
            return

    # Setup lifecycle rules
    r2.setup_bucket_lifecycle()

    # Setup CORS
    r2.setup_cors()

    print("\n✅ R2 Setup Complete!")
    print(f"Public URL: {r2.public_domain}")
    print("\nAdd these to your .env file:")
    print(f"R2_ACCOUNT_ID={account_id}")
    print(f"R2_ACCESS_KEY={access_key}")
    print(f"R2_SECRET_KEY={secret_key}")
    print(f"R2_BUCKET={bucket_name}")


if __name__ == "__main__":
    setup_r2_bucket()
