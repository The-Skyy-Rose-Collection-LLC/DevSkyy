"""
Image Cache Manager for Performance Optimization
Handles caching of frequently accessed images and processing results.
"""

import logging
import hashlib
import json
import time
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime, timedelta
import pickle
import threading
from collections import OrderedDict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImageCacheManager:
    """Performance-optimized caching system for image processing."""
    
    def __init__(self, cache_dir: str = "cache/images", max_size_mb: int = 500, ttl_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.ttl_seconds = ttl_hours * 3600
        
        # In-memory cache for hot data
        self.memory_cache = OrderedDict()
        self.memory_cache_max_items = 100
        
        # Thread lock for cache operations
        self.cache_lock = threading.RLock()
        
        # Cache metadata
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self.metadata = self._load_metadata()
        
        logger.info(f"🗄️ Image Cache Manager initialized - Max size: {max_size_mb}MB, TTL: {ttl_hours}h")
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load cache metadata from disk."""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cache metadata: {str(e)}")
        
        return {
            "entries": {},
            "total_size": 0,
            "last_cleanup": datetime.now().isoformat()
        }
    
    def _save_metadata(self):
        """Save cache metadata to disk."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache metadata: {str(e)}")
    
    def _generate_cache_key(self, image_path: str, operation: str, params: Dict[str, Any] = None) -> str:
        """Generate unique cache key for image and operation."""
        key_data = f"{image_path}:{operation}"
        if params:
            # Sort parameters for consistent hashing
            sorted_params = json.dumps(params, sort_keys=True)
            key_data += f":{sorted_params}"
        
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    def _get_cache_file_path(self, cache_key: str) -> Path:
        """Get file path for cache entry."""
        return self.cache_dir / f"{cache_key}.cache"
    
    def _is_entry_valid(self, entry_metadata: Dict[str, Any]) -> bool:
        """Check if cache entry is still valid."""
        try:
            created_time = datetime.fromisoformat(entry_metadata['created'])
            age_seconds = (datetime.now() - created_time).total_seconds()
            return age_seconds < self.ttl_seconds
        except Exception:
            return False
    
    def get(self, image_path: str, operation: str, params: Dict[str, Any] = None) -> Optional[Any]:
        """Retrieve cached result for image operation."""
        with self.cache_lock:
            cache_key = self._generate_cache_key(image_path, operation, params)
            
            # Check memory cache first
            if cache_key in self.memory_cache:
                self.memory_cache.move_to_end(cache_key)  # Update LRU order
                logger.debug(f"Cache hit (memory): {operation} for {Path(image_path).name}")
                return self.memory_cache[cache_key]
            
            # Check disk cache
            if cache_key in self.metadata["entries"]:
                entry_metadata = self.metadata["entries"][cache_key]
                
                if not self._is_entry_valid(entry_metadata):
                    # Entry expired, remove it
                    self._remove_cache_entry(cache_key)
                    return None
                
                try:
                    cache_file = self._get_cache_file_path(cache_key)
                    if cache_file.exists():
                        with open(cache_file, 'rb') as f:
                            cached_data = pickle.load(f)
                        
                        # Add to memory cache
                        self._add_to_memory_cache(cache_key, cached_data)
                        
                        logger.debug(f"Cache hit (disk): {operation} for {Path(image_path).name}")
                        return cached_data
                    else:
                        # File missing, remove metadata entry
                        self._remove_cache_entry(cache_key)
                        
                except Exception as e:
                    logger.warning(f"Failed to read cache entry {cache_key}: {str(e)}")
                    self._remove_cache_entry(cache_key)
            
            return None
    
    def set(self, image_path: str, operation: str, result: Any, params: Dict[str, Any] = None):
        """Cache result for image operation."""
        with self.cache_lock:
            cache_key = self._generate_cache_key(image_path, operation, params)
            
            try:
                # Serialize data
                cache_file = self._get_cache_file_path(cache_key)
                with open(cache_file, 'wb') as f:
                    pickle.dump(result, f)
                
                # Get file size
                file_size = cache_file.stat().st_size
                
                # Update metadata
                entry_metadata = {
                    "image_path": image_path,
                    "operation": operation,
                    "params": params,
                    "size": file_size,
                    "created": datetime.now().isoformat(),
                    "accessed": datetime.now().isoformat()
                }
                
                # Remove old entry if exists
                if cache_key in self.metadata["entries"]:
                    old_size = self.metadata["entries"][cache_key]["size"]
                    self.metadata["total_size"] -= old_size
                
                self.metadata["entries"][cache_key] = entry_metadata
                self.metadata["total_size"] += file_size
                
                # Add to memory cache
                self._add_to_memory_cache(cache_key, result)
                
                # Cleanup if needed
                self._cleanup_if_needed()
                
                # Save metadata
                self._save_metadata()
                
                logger.debug(f"Cached: {operation} for {Path(image_path).name} ({file_size} bytes)")
                
            except Exception as e:
                logger.error(f"Failed to cache result for {cache_key}: {str(e)}")
    
    def _add_to_memory_cache(self, cache_key: str, data: Any):
        """Add entry to memory cache with LRU eviction."""
        self.memory_cache[cache_key] = data
        
        # Maintain size limit
        while len(self.memory_cache) > self.memory_cache_max_items:
            oldest_key = next(iter(self.memory_cache))
            del self.memory_cache[oldest_key]
    
    def _remove_cache_entry(self, cache_key: str):
        """Remove cache entry from disk and metadata."""
        try:
            # Remove from metadata
            if cache_key in self.metadata["entries"]:
                entry_size = self.metadata["entries"][cache_key]["size"]
                self.metadata["total_size"] -= entry_size
                del self.metadata["entries"][cache_key]
            
            # Remove from memory cache
            if cache_key in self.memory_cache:
                del self.memory_cache[cache_key]
            
            # Remove file
            cache_file = self._get_cache_file_path(cache_key)
            if cache_file.exists():
                cache_file.unlink()
                
        except Exception as e:
            logger.warning(f"Failed to remove cache entry {cache_key}: {str(e)}")
    
    def _cleanup_if_needed(self):
        """Cleanup cache if it exceeds size limits."""
        if self.metadata["total_size"] <= self.max_size_bytes:
            return
        
        logger.info("🧹 Cache size limit exceeded, starting cleanup...")
        
        # Sort entries by access time (oldest first)
        entries_by_access = sorted(
            self.metadata["entries"].items(),
            key=lambda x: x[1]["accessed"]
        )
        
        cleaned_size = 0
        cleaned_count = 0
        
        for cache_key, entry_metadata in entries_by_access:
            if self.metadata["total_size"] - cleaned_size <= self.max_size_bytes:
                break
            
            cleaned_size += entry_metadata["size"]
            cleaned_count += 1
            self._remove_cache_entry(cache_key)
        
        logger.info(f"✅ Cache cleanup completed: {cleaned_count} entries removed, {cleaned_size} bytes freed")
        self._save_metadata()
    
    def invalidate(self, image_path: str, operation: str = None, params: Dict[str, Any] = None):
        """Invalidate cached entries for specific image or operation."""
        with self.cache_lock:
            if operation:
                # Invalidate specific operation
                cache_key = self._generate_cache_key(image_path, operation, params)
                if cache_key in self.metadata["entries"]:
                    self._remove_cache_entry(cache_key)
                    logger.debug(f"Invalidated cache: {operation} for {Path(image_path).name}")
            else:
                # Invalidate all operations for this image
                keys_to_remove = []
                for cache_key, entry_metadata in self.metadata["entries"].items():
                    if entry_metadata["image_path"] == image_path:
                        keys_to_remove.append(cache_key)
                
                for cache_key in keys_to_remove:
                    self._remove_cache_entry(cache_key)
                
                logger.debug(f"Invalidated all cache entries for {Path(image_path).name}")
            
            self._save_metadata()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.cache_lock:
            return {
                "total_entries": len(self.metadata["entries"]),
                "total_size_mb": self.metadata["total_size"] / (1024 * 1024),
                "max_size_mb": self.max_size_bytes / (1024 * 1024),
                "memory_cache_entries": len(self.memory_cache),
                "ttl_hours": self.ttl_seconds / 3600,
                "last_cleanup": self.metadata.get("last_cleanup", "never"),
                "cache_utilization": (self.metadata["total_size"] / self.max_size_bytes) * 100
            }
    
    def clear_cache(self):
        """Clear all cache entries."""
        with self.cache_lock:
            logger.info("🗑️ Clearing all cache entries...")
            
            # Remove all files
            for cache_key in list(self.metadata["entries"].keys()):
                self._remove_cache_entry(cache_key)
            
            # Clear memory cache
            self.memory_cache.clear()
            
            # Reset metadata
            self.metadata = {
                "entries": {},
                "total_size": 0,
                "last_cleanup": datetime.now().isoformat()
            }
            
            self._save_metadata()
            logger.info("✅ Cache cleared successfully")
    
    def cleanup_expired_entries(self):
        """Manual cleanup of expired cache entries."""
        with self.cache_lock:
            logger.info("🧹 Starting manual cleanup of expired entries...")
            
            expired_keys = []
            for cache_key, entry_metadata in self.metadata["entries"].items():
                if not self._is_entry_valid(entry_metadata):
                    expired_keys.append(cache_key)
            
            for cache_key in expired_keys:
                self._remove_cache_entry(cache_key)
            
            if expired_keys:
                logger.info(f"✅ Cleaned up {len(expired_keys)} expired entries")
                self._save_metadata()
            else:
                logger.info("✅ No expired entries found")


class CachedImageProcessor:
    """Image processor with integrated caching."""
    
    def __init__(self, base_processor, cache_manager: ImageCacheManager = None):
        self.base_processor = base_processor
        self.cache_manager = cache_manager or ImageCacheManager()
        logger.info("🚀 Cached Image Processor initialized")
    
    async def ai_categorize_image_cached(self, image_path: str, custom_categories: List[str] = None) -> Dict[str, Any]:
        """Cached version of AI image categorization."""
        params = {"custom_categories": custom_categories} if custom_categories else None
        
        # Try cache first
        cached_result = self.cache_manager.get(image_path, "ai_categorize", params)
        if cached_result is not None:
            return cached_result
        
        # Process and cache result
        result = await self.base_processor.ai_categorize_image(image_path, custom_categories)
        self.cache_manager.set(image_path, "ai_categorize", result, params)
        
        return result
    
    async def analyze_image_quality_cached(self, image_path: str) -> Dict[str, Any]:
        """Cached version of image quality analysis."""
        # Try cache first
        cached_result = self.cache_manager.get(image_path, "quality_analysis")
        if cached_result is not None:
            return cached_result
        
        # Process and cache result
        result = await self.base_processor.analyze_image_quality(image_path)
        self.cache_manager.set(image_path, "quality_analysis", result)
        
        return result
    
    async def generate_alt_text_cached(self, image_path: str, context: str = "") -> Dict[str, Any]:
        """Cached version of alt text generation."""
        params = {"context": context} if context else None
        
        # Try cache first
        cached_result = self.cache_manager.get(image_path, "alt_text", params)
        if cached_result is not None:
            return cached_result
        
        # Process and cache result
        result = await self.base_processor.generate_alt_text(image_path, context)
        self.cache_manager.set(image_path, "alt_text", result, params)
        
        return result
    
    def invalidate_image_cache(self, image_path: str):
        """Invalidate all cached data for an image."""
        self.cache_manager.invalidate(image_path)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get caching statistics."""
        return self.cache_manager.get_cache_stats()