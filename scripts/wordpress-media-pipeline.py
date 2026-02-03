#!/usr/bin/env python3
"""
WordPress Media Enhancement Pipeline
Batch processes existing WordPress product images with AI enhancement

Usage:
    python scripts/wordpress-media-pipeline.py --wp-url https://skyyrose.co --api-key YOUR_API_KEY

Requirements:
    - WordPress site with REST API enabled
    - SkyyRose AI enhancement service running
    - API credentials configured
"""

import asyncio
import argparse
import sys
from pathlib import Path
from typing import Optional, List, Dict
import requests
from tqdm import tqdm
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.ai_image_enhancement import LuxuryImageEnhancer


class WordPressMediaPipeline:
    """
    Batch processes WordPress media library images with AI enhancement
    """

    def __init__(
        self,
        wp_url: str,
        wp_username: str,
        wp_password: str,
        enhancer: LuxuryImageEnhancer,
        output_dir: Optional[str] = None,
    ):
        self.wp_url = wp_url.rstrip('/')
        self.wp_username = wp_username
        self.wp_password = wp_password
        self.enhancer = enhancer
        self.output_dir = Path(output_dir) if output_dir else Path('./enhanced_media')
        self.output_dir.mkdir(exist_ok=True)

        # WordPress REST API endpoints
        self.api_base = f"{self.wp_url}/wp-json/wp/v2"
        self.media_endpoint = f"{self.api_base}/media"

    def get_all_media(self, per_page: int = 100) -> List[Dict]:
        """
        Fetch all media items from WordPress REST API

        Args:
            per_page: Number of items per page

        Returns:
            List of media items
        """
        all_media = []
        page = 1

        print(f"Fetching media from {self.wp_url}...")

        while True:
            response = requests.get(
                self.media_endpoint,
                params={
                    'per_page': per_page,
                    'page': page,
                    'media_type': 'image',
                },
                auth=(self.wp_username, self.wp_password),
            )

            if response.status_code != 200:
                print(f"Error fetching media: {response.status_code}")
                break

            media_items = response.json()

            if not media_items:
                break

            all_media.extend(media_items)
            page += 1

            # Check if there are more pages
            total_pages = int(response.headers.get('X-WP-TotalPages', 1))
            if page > total_pages:
                break

        print(f"Found {len(all_media)} images")
        return all_media

    def download_image(self, url: str, filename: str) -> Optional[str]:
        """
        Download image from WordPress media library

        Args:
            url: Image URL
            filename: Local filename to save

        Returns:
            Local file path or None on error
        """
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            file_path = self.output_dir / filename
            file_path.write_bytes(response.content)

            return str(file_path)

        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return None

    def update_media_metadata(self, media_id: int, metadata: Dict) -> bool:
        """
        Update WordPress media metadata

        Args:
            media_id: WordPress media ID
            metadata: Metadata to update

        Returns:
            Success status
        """
        try:
            response = requests.post(
                f"{self.media_endpoint}/{media_id}",
                json={'meta': metadata},
                auth=(self.wp_username, self.wp_password),
            )

            return response.status_code == 200

        except Exception as e:
            print(f"Error updating metadata for media {media_id}: {e}")
            return False

    async def process_media_item(self, media_item: Dict) -> Dict:
        """
        Process single media item with AI enhancement

        Args:
            media_item: WordPress media item

        Returns:
            Processing result
        """
        media_id = media_item['id']
        title = media_item['title']['rendered']
        source_url = media_item['source_url']

        print(f"Processing: {title} (ID: {media_id})")

        # Download image
        filename = Path(source_url).name
        local_path = self.download_image(source_url, filename)

        if not local_path:
            return {
                'id': media_id,
                'title': title,
                'success': False,
                'error': 'Download failed',
            }

        try:
            # Apply luxury filter
            enhanced_path = str(self.output_dir / f"enhanced_{filename}")
            await self.enhancer.apply_luxury_filter(local_path, enhanced_path)

            # Generate blurhash
            blurhash_result = await self.enhancer.interrogate_image(local_path)

            # Update WordPress metadata
            metadata = {
                '_skyyrose_enhancement_status': 'completed',
                '_skyyrose_enhanced_at': '',
                '_skyyrose_blurhash': blurhash_result.get('fast_prompt', ''),
            }

            self.update_media_metadata(media_id, metadata)

            return {
                'id': media_id,
                'title': title,
                'success': True,
                'enhanced_path': enhanced_path,
                'blurhash': blurhash_result.get('fast_prompt', ''),
            }

        except Exception as e:
            return {
                'id': media_id,
                'title': title,
                'success': False,
                'error': str(e),
            }

    async def process_all_media(
        self,
        apply_filter: bool = True,
        remove_bg: bool = False,
        upscale: bool = False,
    ) -> List[Dict]:
        """
        Process all media items in WordPress library

        Args:
            apply_filter: Apply luxury color grading
            remove_bg: Remove backgrounds
            upscale: Upscale images

        Returns:
            List of processing results
        """
        media_items = self.get_all_media()

        if not media_items:
            print("No media items found")
            return []

        results = []

        # Process with progress bar
        with tqdm(total=len(media_items), desc="Enhancing images") as pbar:
            for media_item in media_items:
                result = await self.process_media_item(media_item)
                results.append(result)
                pbar.update(1)

        return results

    def generate_report(self, results: List[Dict]) -> None:
        """
        Generate processing report

        Args:
            results: List of processing results
        """
        total = len(results)
        success = sum(1 for r in results if r['success'])
        failed = total - success

        print("\n" + "=" * 60)
        print("PROCESSING REPORT")
        print("=" * 60)
        print(f"Total images processed: {total}")
        print(f"Successfully enhanced: {success} ({success/total*100:.1f}%)")
        print(f"Failed: {failed} ({failed/total*100:.1f}%)")
        print("=" * 60)

        # Save detailed report
        report_path = self.output_dir / 'enhancement_report.json'
        report_path.write_text(json.dumps(results, indent=2))
        print(f"\nDetailed report saved to: {report_path}")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Batch process WordPress media with AI enhancement'
    )
    parser.add_argument(
        '--wp-url',
        required=True,
        help='WordPress site URL (e.g., https://skyyrose.co)',
    )
    parser.add_argument(
        '--wp-username',
        required=True,
        help='WordPress username',
    )
    parser.add_argument(
        '--wp-password',
        required=True,
        help='WordPress application password',
    )
    parser.add_argument(
        '--output-dir',
        default='./enhanced_media',
        help='Output directory for enhanced images',
    )
    parser.add_argument(
        '--replicate-key',
        help='Replicate API key',
    )
    parser.add_argument(
        '--fal-key',
        help='FAL API key',
    )
    parser.add_argument(
        '--stability-key',
        help='Stability AI API key',
    )
    parser.add_argument(
        '--together-key',
        help='Together AI API key',
    )
    parser.add_argument(
        '--runway-key',
        help='RunwayML API key',
    )
    parser.add_argument(
        '--remove-bg',
        action='store_true',
        help='Remove backgrounds from images',
    )
    parser.add_argument(
        '--upscale',
        action='store_true',
        help='Upscale images 4x',
    )

    args = parser.parse_args()

    # Initialize enhancer
    enhancer = LuxuryImageEnhancer(
        replicate_api_key=args.replicate_key,
        fal_api_key=args.fal_key,
        stability_api_key=args.stability_key,
        together_api_key=args.together_key,
        runway_api_key=args.runway_key,
    )

    # Initialize pipeline
    pipeline = WordPressMediaPipeline(
        wp_url=args.wp_url,
        wp_username=args.wp_username,
        wp_password=args.wp_password,
        enhancer=enhancer,
        output_dir=args.output_dir,
    )

    # Process all media
    print("Starting WordPress media enhancement pipeline...")
    results = await pipeline.process_all_media(
        apply_filter=True,
        remove_bg=args.remove_bg,
        upscale=args.upscale,
    )

    # Generate report
    pipeline.generate_report(results)


if __name__ == '__main__':
    asyncio.run(main())
