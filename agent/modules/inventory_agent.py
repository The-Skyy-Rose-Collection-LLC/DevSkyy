
import hashlib
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from PIL import Image
import imagehash
from pathlib import Path
import json
from datetime import datetime


@dataclass
class Asset:
    """Represents a digital asset in the inventory."""
    id: str
    path: str
    file_type: str
    file_size: int
    hash_value: str
    perceptual_hash: Optional[str] = None
    similarity_score: float = 0.0
    is_duplicate: bool = False
    created_at: str = ""


class InventoryAgent:
    """Agent for scanning, analyzing, and managing digital assets."""
    
    def __init__(self, base_path: str = "./assets"):
        self.base_path = Path(base_path)
        self.assets: List[Asset] = []
        self.duplicates: List[List[Asset]] = []
        
    def scan_assets(self) -> List[Asset]:
        """Scan directory for all digital assets."""
        self.assets = []
        supported_formats = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', 
                           '.pdf', '.doc', '.docx', '.txt', '.json', '.xml'}
        
        if not self.base_path.exists():
            self.base_path.mkdir(parents=True)
            return self.assets
            
        for file_path in self.base_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in supported_formats:
                asset = self._create_asset(file_path)
                if asset:
                    self.assets.append(asset)
                    
        return self.assets
    
    def _create_asset(self, file_path: Path) -> Optional[Asset]:
        """Create an Asset object from a file path."""
        try:
            file_stats = file_path.stat()
            
            # Calculate file hash
            with open(file_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            
            # Calculate perceptual hash for images
            perceptual_hash = None
            if file_path.suffix.lower() in {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}:
                try:
                    img = Image.open(file_path)
                    perceptual_hash = str(imagehash.phash(img))
                except Exception:
                    pass
            
            return Asset(
                id=file_hash[:12],
                path=str(file_path),
                file_type=file_path.suffix.lower(),
                file_size=file_stats.st_size,
                hash_value=file_hash,
                perceptual_hash=perceptual_hash,
                created_at=datetime.fromtimestamp(file_stats.st_ctime).isoformat()
            )
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return None
    
    def find_duplicates(self, similarity_threshold: float = 0.95) -> List[List[Asset]]:
        """Find duplicate and similar assets."""
        self.duplicates = []
        processed = set()
        
        for i, asset1 in enumerate(self.assets):
            if asset1.id in processed:
                continue
                
            duplicate_group = [asset1]
            processed.add(asset1.id)
            
            for j, asset2 in enumerate(self.assets[i+1:], i+1):
                if asset2.id in processed:
                    continue
                    
                similarity = self._calculate_similarity(asset1, asset2)
                
                if similarity >= similarity_threshold:
                    asset2.similarity_score = similarity
                    asset2.is_duplicate = True
                    duplicate_group.append(asset2)
                    processed.add(asset2.id)
            
            if len(duplicate_group) > 1:
                self.duplicates.append(duplicate_group)
                
        return self.duplicates
    
    def _calculate_similarity(self, asset1: Asset, asset2: Asset) -> float:
        """Calculate similarity between two assets."""
        # Exact file hash match
        if asset1.hash_value == asset2.hash_value:
            return 1.0
        
        # Perceptual hash comparison for images
        if (asset1.perceptual_hash and asset2.perceptual_hash and 
            asset1.file_type == asset2.file_type):
            
            hash1 = imagehash.hex_to_hash(asset1.perceptual_hash)
            hash2 = imagehash.hex_to_hash(asset2.perceptual_hash)
            
            # Calculate hamming distance (lower = more similar)
            hamming_distance = hash1 - hash2
            
            # Convert to similarity score (0-1, higher = more similar)
            max_distance = 64  # For pHash
            similarity = 1 - (hamming_distance / max_distance)
            return max(0, similarity)
        
        # File size similarity for non-images
        if asset1.file_size == asset2.file_size:
            return 0.8
            
        return 0.0
    
    def remove_duplicates(self, keep_strategy: str = "latest") -> Dict[str, Any]:
        """Remove duplicate files based on strategy."""
        removed_count = 0
        space_saved = 0
        
        for duplicate_group in self.duplicates:
            if len(duplicate_group) <= 1:
                continue
                
            # Determine which file to keep
            if keep_strategy == "latest":
                keeper = max(duplicate_group, key=lambda x: x.created_at)
            elif keep_strategy == "largest":
                keeper = max(duplicate_group, key=lambda x: x.file_size)
            else:  # "first"
                keeper = duplicate_group[0]
            
            # Remove duplicates
            for asset in duplicate_group:
                if asset.id != keeper.id:
                    try:
                        os.remove(asset.path)
                        removed_count += 1
                        space_saved += asset.file_size
                        self.assets.remove(asset)
                    except Exception as e:
                        print(f"Error removing {asset.path}: {e}")
        
        return {
            "removed_files": removed_count,
            "space_saved_mb": round(space_saved / (1024 * 1024), 2),
            "remaining_assets": len(self.assets)
        }
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive inventory report."""
        total_size = sum(asset.file_size for asset in self.assets)
        file_types = {}
        
        for asset in self.assets:
            if asset.file_type in file_types:
                file_types[asset.file_type] += 1
            else:
                file_types[asset.file_type] = 1
        
        return {
            "scan_timestamp": datetime.now().isoformat(),
            "total_assets": len(self.assets),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "duplicate_groups": len(self.duplicates),
            "total_duplicates": sum(len(group) - 1 for group in self.duplicates),
            "file_types": file_types,
            "assets": [
                {
                    "id": asset.id,
                    "path": asset.path,
                    "type": asset.file_type,
                    "size_kb": round(asset.file_size / 1024, 2),
                    "is_duplicate": asset.is_duplicate,
                    "similarity_score": asset.similarity_score
                } for asset in self.assets
            ]
        }
    
    def visualize_similarities(self) -> str:
        """Create a visual representation of asset similarities."""
        visualization = []
        visualization.append("🗂️  INVENTORY SIMILARITY ANALYSIS")
        visualization.append("=" * 50)
        
        if not self.duplicates:
            visualization.append("✅ No duplicates found!")
            return "\n".join(visualization)
        
        for i, group in enumerate(self.duplicates, 1):
            visualization.append(f"\n📁 Duplicate Group {i}:")
            for asset in group:
                similarity_indicator = "🎯" if asset.similarity_score >= 0.95 else "🔍"
                size_mb = round(asset.file_size / (1024 * 1024), 2)
                visualization.append(
                    f"  {similarity_indicator} {Path(asset.path).name} "
                    f"({asset.file_type}, {size_mb}MB, {asset.similarity_score:.2%})"
                )
        
        return "\n".join(visualization)
