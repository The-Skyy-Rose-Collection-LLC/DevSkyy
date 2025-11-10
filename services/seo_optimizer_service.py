"""
SEO Optimizer Service
Generate SEO-optimized content for products and pages

Author: DevSkyy Enterprise Team
Date: 2025-11-10
"""

import logging
from typing import Dict, List, Optional
import re

logger = logging.getLogger(__name__)


class SEOOptimizer:
    """Service for generating and optimizing SEO content"""

    def __init__(self):
        """Initialize SEO optimizer"""
        self.max_title_length = 60
        self.max_description_length = 160
        self.max_url_slug_length = 100

    def generate_meta_title(self, product_name: str, category: Optional[str] = None, brand: str = "The Skyy Rose Collection") -> str:
        """
        Generate SEO-optimized meta title

        Args:
            product_name: Product name
            category: Product category (optional)
            brand: Brand name

        Returns:
            SEO-optimized meta title (≤60 characters)
        """
        try:
            # Format: "Product Name - Category | Brand"
            if category:
                title = f"{product_name} - {category} | {brand}"
            else:
                title = f"{product_name} | {brand}"

            # Truncate if too long
            if len(title) > self.max_title_length:
                # Try without category
                title = f"{product_name} | {brand}"

            # Still too long? Truncate product name
            if len(title) > self.max_title_length:
                max_product_length = self.max_title_length - len(f" | {brand}")
                product_name = product_name[:max_product_length-3] + "..."
                title = f"{product_name} | {brand}"

            return title

        except Exception as e:
            logger.error(f"Generate meta title error: {e}")
            return product_name[:self.max_title_length]

    def generate_meta_description(
        self,
        product_name: str,
        description: str,
        price: Optional[float] = None,
        features: Optional[List[str]] = None
    ) -> str:
        """
        Generate SEO-optimized meta description

        Args:
            product_name: Product name
            description: Product description
            price: Product price (optional)
            features: Key product features (optional)

        Returns:
            SEO-optimized meta description (≤160 characters)
        """
        try:
            # Clean description (remove HTML, extra spaces)
            clean_desc = re.sub(r'<[^>]+>', '', description)
            clean_desc = ' '.join(clean_desc.split())

            # Build description
            if price:
                desc = f"{product_name} - {clean_desc[:80]} ${price:.2f}."
            else:
                desc = f"{product_name} - {clean_desc[:120]}"

            # Add features if provided and space available
            if features and len(desc) < self.max_description_length - 20:
                features_str = ", ".join(features[:3])
                desc += f" {features_str}."

            # Truncate if too long
            if len(desc) > self.max_description_length:
                desc = desc[:self.max_description_length-3] + "..."

            return desc

        except Exception as e:
            logger.error(f"Generate meta description error: {e}")
            return description[:self.max_description_length]

    def generate_url_slug(self, text: str) -> str:
        """
        Generate SEO-friendly URL slug

        Args:
            text: Text to convert to slug

        Returns:
            URL-safe slug
        """
        try:
            # Convert to lowercase
            slug = text.lower()

            # Replace special characters with hyphens
            slug = re.sub(r'[^a-z0-9\s-]', '', slug)

            # Replace spaces with hyphens
            slug = re.sub(r'\s+', '-', slug)

            # Remove multiple hyphens
            slug = re.sub(r'-+', '-', slug)

            # Remove leading/trailing hyphens
            slug = slug.strip('-')

            # Truncate if too long
            if len(slug) > self.max_url_slug_length:
                slug = slug[:self.max_url_slug_length].rsplit('-', 1)[0]

            return slug

        except Exception as e:
            logger.error(f"Generate URL slug error: {e}")
            return "product"

    def generate_keywords(self, product_name: str, category: str, tags: List[str]) -> List[str]:
        """
        Generate SEO keywords

        Args:
            product_name: Product name
            category: Product category
            tags: Product tags

        Returns:
            List of SEO keywords
        """
        try:
            keywords = []

            # Add product name words
            product_words = product_name.lower().split()
            keywords.extend([word for word in product_words if len(word) > 3])

            # Add category
            if category:
                keywords.append(category.lower())

            # Add tags
            keywords.extend([tag.lower() for tag in tags if len(tag) > 3])

            # Remove duplicates while preserving order
            seen = set()
            unique_keywords = []
            for keyword in keywords:
                if keyword not in seen:
                    seen.add(keyword)
                    unique_keywords.append(keyword)

            return unique_keywords[:10]  # Limit to 10 keywords

        except Exception as e:
            logger.error(f"Generate keywords error: {e}")
            return []

    def optimize_product(self, product: Dict) -> Dict:
        """
        Generate complete SEO data for a product

        Args:
            product: Product dictionary

        Returns:
            Product dictionary with enhanced SEO data
        """
        try:
            product_name = product.get("name", "")
            description = product.get("description", "")
            category = product.get("category", "")
            price = product.get("price")
            tags = product.get("tags", [])

            # Generate SEO data
            seo_data = {
                "meta_title": self.generate_meta_title(product_name, category),
                "meta_description": self.generate_meta_description(product_name, description, price),
                "url_slug": self.generate_url_slug(product_name),
                "keywords": self.generate_keywords(product_name, category, tags),
                "schema_type": "Product",
                "og_type": "product",
                "og_title": self.generate_meta_title(product_name, category),
                "og_description": self.generate_meta_description(product_name, description, price),
                "twitter_card": "summary_large_image",
            }

            # Update product with SEO data
            product["seo_data"] = seo_data

            logger.info(f"SEO data generated for product: {product_name}")
            return product

        except Exception as e:
            logger.error(f"Optimize product error: {e}")
            return product

    def generate_structured_data(self, product: Dict) -> Dict:
        """
        Generate JSON-LD structured data for product

        Args:
            product: Product dictionary

        Returns:
            JSON-LD structured data dictionary
        """
        try:
            structured_data = {
                "@context": "https://schema.org/",
                "@type": "Product",
                "name": product.get("name", ""),
                "description": product.get("description", ""),
                "sku": product.get("sku", ""),
                "image": product.get("images", [])[0] if product.get("images") else "",
                "brand": {
                    "@type": "Brand",
                    "name": "The Skyy Rose Collection"
                },
                "offers": {
                    "@type": "Offer",
                    "url": f"https://skyyrose.co/products/{product.get('sku', '')}",
                    "priceCurrency": "USD",
                    "price": product.get("price", 0),
                    "availability": "https://schema.org/InStock" if product.get("stock_quantity", 0) > 0 else "https://schema.org/OutOfStock",
                    "itemCondition": "https://schema.org/NewCondition"
                }
            }

            return structured_data

        except Exception as e:
            logger.error(f"Generate structured data error: {e}")
            return {}


def get_seo_optimizer() -> SEOOptimizer:
    """
    Factory function to create SEO optimizer instance

    Returns:
        SEOOptimizer instance
    """
    return SEOOptimizer()
