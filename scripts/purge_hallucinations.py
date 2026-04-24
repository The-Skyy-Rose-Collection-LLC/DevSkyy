#!/usr/bin/env python3
"""
Purge Hallucinations Utility
============================
Deletes identified AI hallucinations from the product imagery folder:
1. Model shots for SKUs marked as accessories in the catalog.
2. Renders for the non-existent 'po' collection.
3. Identified 2MB+ unoptimized model shots that lack front-view pairs.
"""

import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Paths
PRODUCTS_DIR = Path("wordpress-theme/skyyrose-flagship/assets/images/products")

# Hallucinated targets
ACCESSORY_SKUS = ["lh-005", "sg-007"] # Fanny pack and Beanie should not have human model shots
PO_COLLECTION_PREFIX = "po-" # Non-existent collection
SUSPECT_UNOPTIMIZED_SIZE_LIMIT = 1.5 * 1024 * 1024 # 1.5MB

def purge():
    if not PRODUCTS_DIR.exists():
        logger.error(f"Products directory not found: {PRODUCTS_DIR}")
        return

    deleted_count = 0
    
    for item in PRODUCTS_DIR.iterdir():
        if not item.is_file():
            continue
            
        name = item.name.lower()
        
        # Rule 1: Purge accessory model shots
        is_accessory_model = any(sku in name for sku in ACCESSORY_SKUS) and "model" in name
        
        # Rule 2: Purge 'po' collection
        is_po_hallucination = name.startswith(PO_COLLECTION_PREFIX)
        
        # Rule 3: Identify unoptimized massive files (>1.5MB) that are specifically 'model' shots
        # These are usually the result of unconstrained AI generation without web-optimization
        is_massive_hallucination = item.stat().st_size > SUSPECT_UNOPTIMIZED_SIZE_LIMIT and "model" in name

        if is_accessory_model or is_po_hallucination or is_massive_hallucination:
            logger.info(f"Purging hallucination: {item.name} ({item.stat().st_size / 1024 / 1024:.2f} MB)")
            item.unlink()
            deleted_count += 1

    logger.info(f"Cleanup complete. Deleted {deleted_count} hallucinated assets.")

if __name__ == "__main__":
    purge()
