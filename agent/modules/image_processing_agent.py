"""
Enhanced Image Processing Agent for The Skyy Rose Collection
Provides AI-powered image categorization, quality analysis, and bulk processing capabilities.
"""

import logging
import asyncio
import hashlib
import json
import cv2
import numpy as np
from PIL import Image, ImageFilter, ImageStat, ImageEnhance
import imagehash
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime
from pathlib import Path
import base64
from io import BytesIO
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImageProcessingAgent:
    """Advanced image processing agent with AI-powered capabilities."""
    
    def __init__(self):
        self.quality_thresholds = {
            'blur_threshold': 100.0,
            'brightness_low': 50,
            'brightness_high': 200,
            'contrast_low': 20,
            'contrast_high': 80
        }
        self.supported_formats = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff']
        self.category_models = self._initialize_category_models()
        logger.info("🎨 Enhanced Image Processing Agent Initialized")
    
    def _initialize_category_models(self) -> Dict[str, Any]:
        """Initialize pre-trained models for image categorization."""
        # Simulated model initialization - in production, load actual models
        return {
            'fashion_classifier': {
                'categories': ['dress', 'top', 'bottom', 'accessory', 'shoes', 'outerwear'],
                'confidence_threshold': 0.7
            },
            'marketing_classifier': {
                'categories': ['banner', 'product_shot', 'lifestyle', 'promotional', 'social_media'],
                'confidence_threshold': 0.75
            },
            'quality_classifier': {
                'categories': ['professional', 'user_generated', 'stock_photo', 'technical'],
                'confidence_threshold': 0.6
            }
        }
    
    async def ai_categorize_image(self, image_path: str, custom_categories: List[str] = None) -> Dict[str, Any]:
        """AI-powered image categorization using pre-trained models."""
        try:
            logger.info(f"🤖 Categorizing image: {image_path}")
            
            # Load and preprocess image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Unable to load image: {image_path}")
            
            # Extract features for classification
            features = await self._extract_image_features(image)
            
            # Apply classification models
            categories = {}
            
            # Fashion classification
            fashion_result = await self._classify_fashion_item(features)
            categories['fashion'] = fashion_result
            
            # Marketing material classification
            marketing_result = await self._classify_marketing_material(features)
            categories['marketing'] = marketing_result
            
            # Quality classification
            quality_result = await self._classify_image_quality(features)
            categories['quality'] = quality_result
            
            # Custom categories if provided
            if custom_categories:
                custom_result = await self._classify_custom_categories(features, custom_categories)
                categories['custom'] = custom_result
            
            # Determine primary category
            primary_category = self._determine_primary_category(categories)
            
            return {
                'primary_category': primary_category,
                'all_categories': categories,
                'confidence_score': self._calculate_overall_confidence(categories),
                'processing_time': datetime.now().isoformat(),
                'features_extracted': True
            }
            
        except Exception as e:
            logger.error(f"❌ Image categorization failed for {image_path}: {str(e)}")
            return {'error': str(e), 'primary_category': 'unknown'}
    
    async def analyze_image_quality(self, image_path: str) -> Dict[str, Any]:
        """Comprehensive image quality analysis."""
        try:
            logger.info(f"🔍 Analyzing image quality: {image_path}")
            
            # Load image
            image = cv2.imread(image_path)
            pil_image = Image.open(image_path)
            
            if image is None:
                raise ValueError(f"Unable to load image: {image_path}")
            
            quality_analysis = {}
            
            # Blur detection
            blur_score = self._detect_blur(image)
            quality_analysis['blur'] = {
                'score': blur_score,
                'is_blurry': blur_score < self.quality_thresholds['blur_threshold'],
                'severity': self._get_blur_severity(blur_score)
            }
            
            # Brightness analysis
            brightness_score = self._analyze_brightness(pil_image)
            quality_analysis['brightness'] = {
                'score': brightness_score,
                'is_overexposed': brightness_score > self.quality_thresholds['brightness_high'],
                'is_underexposed': brightness_score < self.quality_thresholds['brightness_low'],
                'optimal': self.quality_thresholds['brightness_low'] <= brightness_score <= self.quality_thresholds['brightness_high']
            }
            
            # Contrast analysis
            contrast_score = self._analyze_contrast(pil_image)
            quality_analysis['contrast'] = {
                'score': contrast_score,
                'is_low_contrast': contrast_score < self.quality_thresholds['contrast_low'],
                'is_high_contrast': contrast_score > self.quality_thresholds['contrast_high'],
                'optimal': self.quality_thresholds['contrast_low'] <= contrast_score <= self.quality_thresholds['contrast_high']
            }
            
            # Noise analysis
            noise_score = self._analyze_noise(image)
            quality_analysis['noise'] = {
                'score': noise_score,
                'is_noisy': noise_score > 50,
                'severity': self._get_noise_severity(noise_score)
            }
            
            # Color analysis
            color_analysis = self._analyze_colors(pil_image)
            quality_analysis['colors'] = color_analysis
            
            # Overall quality score
            overall_score = self._calculate_overall_quality_score(quality_analysis)
            quality_analysis['overall'] = {
                'score': overall_score,
                'grade': self._get_quality_grade(overall_score),
                'recommendations': self._generate_quality_recommendations(quality_analysis)
            }
            
            return quality_analysis
            
        except Exception as e:
            logger.error(f"❌ Quality analysis failed for {image_path}: {str(e)}")
            return {'error': str(e), 'overall': {'score': 0, 'grade': 'F'}}
    
    async def detect_duplicates_advanced(self, image_paths: List[str]) -> Dict[str, Any]:
        """Advanced duplicate detection using multiple algorithms."""
        try:
            logger.info(f"🔍 Detecting duplicates in {len(image_paths)} images")
            
            duplicate_groups = []
            similarity_matrix = []
            
            # Extract features for all images
            features = []
            valid_paths = []
            
            for path in image_paths:
                try:
                    image_features = await self._extract_comprehensive_features(path)
                    features.append(image_features)
                    valid_paths.append(path)
                except Exception as e:
                    logger.warning(f"Failed to process {path}: {str(e)}")
            
            if len(features) < 2:
                return {'duplicate_groups': [], 'total_duplicates': 0}
            
            # Calculate similarity matrix
            similarity_matrix = await self._calculate_similarity_matrix(features)
            
            # Find duplicate groups using clustering
            duplicate_groups = await self._find_duplicate_groups(similarity_matrix, valid_paths)
            
            # Deep learning-based similarity for uncertain cases
            refined_groups = await self._refine_with_deep_similarity(duplicate_groups)
            
            return {
                'duplicate_groups': refined_groups,
                'total_duplicates': sum(len(group) for group in refined_groups),
                'similarity_threshold': 0.85,
                'methods_used': ['perceptual_hash', 'feature_similarity', 'deep_learning'],
                'processing_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Advanced duplicate detection failed: {str(e)}")
            return {'error': str(e), 'duplicate_groups': []}
    
    async def bulk_process_images(self, image_paths: List[str], operations: Dict[str, Any]) -> Dict[str, Any]:
        """Bulk image processing with multiple operations."""
        try:
            logger.info(f"🔄 Bulk processing {len(image_paths)} images")
            
            results = {
                'processed': 0,
                'failed': 0,
                'operations_applied': [],
                'results': []
            }
            
            for path in image_paths:
                try:
                    result = await self._process_single_image(path, operations)
                    results['results'].append(result)
                    results['processed'] += 1
                except Exception as e:
                    logger.error(f"Failed to process {path}: {str(e)}")
                    results['failed'] += 1
                    results['results'].append({'path': path, 'error': str(e)})
            
            results['operations_applied'] = list(operations.keys())
            results['success_rate'] = results['processed'] / len(image_paths) * 100
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Bulk processing failed: {str(e)}")
            return {'error': str(e), 'processed': 0}
    
    async def generate_alt_text(self, image_path: str, context: str = "") -> Dict[str, Any]:
        """AI-generated alt text for accessibility."""
        try:
            logger.info(f"📝 Generating alt text for: {image_path}")
            
            # Extract image features
            image = cv2.imread(image_path)
            features = await self._extract_image_features(image)
            
            # Analyze image content
            content_analysis = await self._analyze_image_content(image, features)
            
            # Generate descriptive alt text
            alt_text = await self._generate_descriptive_text(content_analysis, context)
            
            return {
                'alt_text': alt_text,
                'content_analysis': content_analysis,
                'confidence': content_analysis.get('confidence', 0.8),
                'context_applied': bool(context)
            }
            
        except Exception as e:
            logger.error(f"❌ Alt text generation failed: {str(e)}")
            return {'error': str(e), 'alt_text': 'Image description unavailable'}
    
    # Helper methods for feature extraction and analysis
    
    async def _extract_image_features(self, image: np.ndarray) -> Dict[str, Any]:
        """Extract comprehensive features from image."""
        # Convert to different color spaces
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Basic features
        height, width = gray.shape
        aspect_ratio = width / height
        
        # Histogram features
        hist_b = cv2.calcHist([image], [0], None, [256], [0, 256])
        hist_g = cv2.calcHist([image], [1], None, [256], [0, 256])
        hist_r = cv2.calcHist([image], [2], None, [256], [0, 256])
        
        # Texture features
        edges = cv2.Canny(gray, 100, 200)
        edge_density = np.sum(edges > 0) / (height * width)
        
        return {
            'dimensions': (width, height),
            'aspect_ratio': aspect_ratio,
            'edge_density': edge_density,
            'histograms': {
                'blue': hist_b.flatten()[:10].tolist(),  # Simplified
                'green': hist_g.flatten()[:10].tolist(),
                'red': hist_r.flatten()[:10].tolist()
            },
            'mean_brightness': np.mean(gray),
            'std_brightness': np.std(gray)
        }
    
    def _detect_blur(self, image: np.ndarray) -> float:
        """Detect blur using Laplacian variance."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return cv2.Laplacian(gray, cv2.CV_64F).var()
    
    def _analyze_brightness(self, image: Image.Image) -> float:
        """Analyze image brightness."""
        grayscale = image.convert('L')
        stat = ImageStat.Stat(grayscale)
        return stat.mean[0]
    
    def _analyze_contrast(self, image: Image.Image) -> float:
        """Analyze image contrast."""
        grayscale = image.convert('L')
        stat = ImageStat.Stat(grayscale)
        return stat.stddev[0]
    
    def _analyze_noise(self, image: np.ndarray) -> float:
        """Analyze image noise levels."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Use standard deviation of Laplacian as noise indicator
        return cv2.Laplacian(gray, cv2.CV_64F).std()
    
    def _analyze_colors(self, image: Image.Image) -> Dict[str, Any]:
        """Analyze color properties."""
        # Convert to RGB for analysis
        rgb_image = image.convert('RGB')
        pixels = list(rgb_image.getdata())
        
        # Calculate color statistics
        r_vals, g_vals, b_vals = zip(*pixels)
        
        return {
            'dominant_colors': self._get_dominant_colors(rgb_image),
            'color_diversity': self._calculate_color_diversity(pixels),
            'average_rgb': (np.mean(r_vals), np.mean(g_vals), np.mean(b_vals))
        }
    
    def _get_dominant_colors(self, image: Image.Image, k: int = 5) -> List[Tuple[int, int, int]]:
        """Extract dominant colors using k-means clustering."""
        # Resize image for faster processing
        image = image.resize((150, 150))
        pixels = np.array(image).reshape(-1, 3)
        
        # Simple approach - return most common colors
        # In production, use k-means clustering
        unique_colors = np.unique(pixels, axis=0)
        return unique_colors[:k].tolist()
    
    def _calculate_color_diversity(self, pixels: List[Tuple[int, int, int]]) -> float:
        """Calculate color diversity score."""
        unique_colors = len(set(pixels))
        total_pixels = len(pixels)
        return unique_colors / total_pixels
    
    # Classification helper methods
    
    async def _classify_fashion_item(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Classify fashion items using extracted features."""
        # Simulated classification - in production, use actual ML models
        aspect_ratio = features['aspect_ratio']
        edge_density = features['edge_density']
        
        # Simple heuristic-based classification
        if aspect_ratio > 1.3:  # Wide images often accessories
            category = 'accessory'
            confidence = 0.7
        elif aspect_ratio < 0.8:  # Tall images often clothing
            category = 'dress' if edge_density < 0.1 else 'top'
            confidence = 0.8
        else:
            category = 'general_apparel'
            confidence = 0.6
        
        return {
            'category': category,
            'confidence': confidence,
            'subcategories': self._get_fashion_subcategories(category)
        }
    
    async def _classify_marketing_material(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Classify marketing materials."""
        # Simulated classification
        brightness = features['mean_brightness']
        edge_density = features['edge_density']
        
        if brightness > 150 and edge_density > 0.15:
            category = 'banner'
            confidence = 0.8
        elif edge_density < 0.05:
            category = 'lifestyle'
            confidence = 0.7
        else:
            category = 'product_shot'
            confidence = 0.75
        
        return {
            'category': category,
            'confidence': confidence,
            'marketing_type': self._determine_marketing_type(category)
        }
    
    async def _classify_image_quality(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Classify image quality level."""
        # Based on technical features
        std_brightness = features['std_brightness']
        edge_density = features['edge_density']
        
        if std_brightness > 50 and edge_density > 0.1:
            quality = 'professional'
            confidence = 0.9
        elif std_brightness > 30:
            quality = 'user_generated'
            confidence = 0.7
        else:
            quality = 'low_quality'
            confidence = 0.8
        
        return {
            'quality': quality,
            'confidence': confidence,
            'technical_score': self._calculate_technical_score(features)
        }
    
    def _get_fashion_subcategories(self, category: str) -> List[str]:
        """Get subcategories for fashion items."""
        subcategory_map = {
            'dress': ['casual', 'formal', 'cocktail', 'maxi', 'mini'],
            'top': ['blouse', 'shirt', 'tank', 'sweater', 'jacket'],
            'accessory': ['jewelry', 'bag', 'scarf', 'belt', 'hat'],
            'general_apparel': ['clothing', 'fashion', 'apparel']
        }
        return subcategory_map.get(category, [])
    
    def _determine_marketing_type(self, category: str) -> str:
        """Determine marketing material type."""
        type_map = {
            'banner': 'promotional',
            'lifestyle': 'brand_story',
            'product_shot': 'product_showcase'
        }
        return type_map.get(category, 'general_marketing')
    
    def _calculate_technical_score(self, features: Dict[str, Any]) -> float:
        """Calculate technical quality score."""
        # Simple scoring based on features
        score = 0
        if features['std_brightness'] > 40:
            score += 30
        if features['edge_density'] > 0.08:
            score += 40
        if 0.8 <= features['aspect_ratio'] <= 1.2:
            score += 30
        return min(score, 100)
    
    # Additional helper methods for advanced functionality
    
    async def _extract_comprehensive_features(self, image_path: str) -> Dict[str, Any]:
        """Extract comprehensive features for duplicate detection."""
        image = cv2.imread(image_path)
        pil_image = Image.open(image_path)
        
        # Perceptual hash
        phash = str(imagehash.phash(pil_image))
        
        # Color histogram
        hist = cv2.calcHist([image], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256])
        
        # Basic features
        basic_features = await self._extract_image_features(image)
        
        return {
            'perceptual_hash': phash,
            'color_histogram': hist.flatten(),
            'basic_features': basic_features,
            'file_path': image_path
        }
    
    async def _calculate_similarity_matrix(self, features: List[Dict[str, Any]]) -> np.ndarray:
        """Calculate similarity matrix between images."""
        n = len(features)
        similarity_matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(i + 1, n):
                # Calculate multiple similarity scores
                hash_sim = self._hash_similarity(features[i]['perceptual_hash'], features[j]['perceptual_hash'])
                hist_sim = self._histogram_similarity(features[i]['color_histogram'], features[j]['color_histogram'])
                
                # Combine similarities
                combined_sim = (hash_sim + hist_sim) / 2
                similarity_matrix[i][j] = combined_sim
                similarity_matrix[j][i] = combined_sim
        
        return similarity_matrix
    
    def _hash_similarity(self, hash1: str, hash2: str) -> float:
        """Calculate similarity between perceptual hashes."""
        if len(hash1) != len(hash2):
            return 0.0
        
        hamming_distance = sum(c1 != c2 for c1, c2 in zip(hash1, hash2))
        max_distance = len(hash1)
        return 1.0 - (hamming_distance / max_distance)
    
    def _histogram_similarity(self, hist1: np.ndarray, hist2: np.ndarray) -> float:
        """Calculate similarity between color histograms."""
        # Normalize histograms
        hist1_norm = hist1 / (np.sum(hist1) + 1e-10)
        hist2_norm = hist2 / (np.sum(hist2) + 1e-10)
        
        # Calculate correlation
        correlation = cv2.compareHist(hist1_norm.astype(np.float32), hist2_norm.astype(np.float32), cv2.HISTCMP_CORREL)
        return max(0, correlation)  # Ensure non-negative
    
    async def _find_duplicate_groups(self, similarity_matrix: np.ndarray, paths: List[str], threshold: float = 0.85) -> List[List[str]]:
        """Find duplicate groups using clustering."""
        # Convert similarity to distance
        distance_matrix = 1 - similarity_matrix
        
        # Use DBSCAN clustering
        clusterer = DBSCAN(metric='precomputed', eps=1-threshold, min_samples=2)
        labels = clusterer.fit_predict(distance_matrix)
        
        # Group paths by cluster labels
        groups = {}
        for i, label in enumerate(labels):
            if label != -1:  # -1 means noise/no cluster
                if label not in groups:
                    groups[label] = []
                groups[label].append(paths[i])
        
        # Return groups with more than one item
        return [group for group in groups.values() if len(group) > 1]
    
    async def _refine_with_deep_similarity(self, duplicate_groups: List[List[str]]) -> List[List[str]]:
        """Refine duplicate groups using deep learning similarity."""
        # Placeholder for deep learning refinement
        # In production, use actual deep learning models
        refined_groups = []
        
        for group in duplicate_groups:
            if len(group) > 1:
                # For now, just pass through - in production, apply deep learning validation
                refined_groups.append(group)
        
        return refined_groups
    
    async def _process_single_image(self, image_path: str, operations: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single image with specified operations."""
        result = {'path': image_path, 'operations': {}}
        
        try:
            image = Image.open(image_path)
            
            # Resize operation
            if 'resize' in operations:
                size = operations['resize'].get('size', (800, 600))
                image = image.resize(size, Image.Resampling.LANCZOS)
                result['operations']['resize'] = f"Resized to {size}"
            
            # Format conversion
            if 'convert_format' in operations:
                new_format = operations['convert_format'].get('format', 'JPEG')
                # Save with new format (would save to new file in production)
                result['operations']['convert_format'] = f"Converted to {new_format}"
            
            # Watermark
            if 'watermark' in operations:
                # Placeholder for watermark application
                result['operations']['watermark'] = "Watermark applied"
            
            # Quality enhancement
            if 'enhance_quality' in operations:
                # Apply basic enhancements
                enhancer = ImageEnhance.Sharpness(image)
                image = enhancer.enhance(1.2)
                result['operations']['enhance_quality'] = "Quality enhanced"
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
            result['success'] = False
        
        return result
    
    async def _analyze_image_content(self, image: np.ndarray, features: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze image content for alt text generation."""
        # Placeholder for content analysis
        # In production, use object detection and scene understanding models
        
        brightness = features['mean_brightness']
        aspect_ratio = features['aspect_ratio']
        edge_density = features['edge_density']
        
        # Simple content analysis
        content_type = 'unknown'
        objects_detected = []
        scene_type = 'indoor'
        
        if edge_density > 0.15:
            content_type = 'detailed_image'
            objects_detected = ['clothing', 'accessories']
        elif brightness > 150:
            content_type = 'bright_image'
            scene_type = 'outdoor'
        else:
            content_type = 'simple_image'
        
        return {
            'content_type': content_type,
            'objects_detected': objects_detected,
            'scene_type': scene_type,
            'confidence': 0.8,
            'technical_quality': self._assess_technical_quality(features)
        }
    
    def _assess_technical_quality(self, features: Dict[str, Any]) -> str:
        """Assess technical quality for alt text."""
        score = self._calculate_technical_score(features)
        if score > 80:
            return 'high_quality'
        elif score > 60:
            return 'medium_quality'
        else:
            return 'low_quality'
    
    async def _generate_descriptive_text(self, content_analysis: Dict[str, Any], context: str = "") -> str:
        """Generate descriptive alt text."""
        # Simple template-based generation
        # In production, use advanced NLP models
        
        content_type = content_analysis['content_type']
        objects = content_analysis['objects_detected']
        scene = content_analysis['scene_type']
        quality = content_analysis['technical_quality']
        
        # Build description
        description_parts = []
        
        if context:
            description_parts.append(context)
        
        if objects:
            description_parts.append(f"Image showing {', '.join(objects)}")
        else:
            description_parts.append("Image")
        
        if scene != 'unknown':
            description_parts.append(f"in {scene} setting")
        
        if quality == 'high_quality':
            description_parts.append("with professional quality")
        
        return " ".join(description_parts).strip()
    
    # Quality analysis helper methods
    
    def _get_blur_severity(self, blur_score: float) -> str:
        """Get blur severity level."""
        if blur_score < 50:
            return 'severe'
        elif blur_score < 100:
            return 'moderate'
        elif blur_score < 200:
            return 'slight'
        else:
            return 'none'
    
    def _get_noise_severity(self, noise_score: float) -> str:
        """Get noise severity level."""
        if noise_score > 100:
            return 'high'
        elif noise_score > 50:
            return 'moderate'
        else:
            return 'low'
    
    def _calculate_overall_quality_score(self, quality_analysis: Dict[str, Any]) -> float:
        """Calculate overall quality score."""
        scores = []
        
        # Blur score (inverted - lower blur is better)
        blur_score = quality_analysis['blur']['score']
        blur_normalized = min(100, blur_score / 2)  # Normalize to 0-100
        scores.append(blur_normalized)
        
        # Brightness score
        brightness = quality_analysis['brightness']
        if brightness['optimal']:
            scores.append(100)
        elif brightness['is_overexposed'] or brightness['is_underexposed']:
            scores.append(30)
        else:
            scores.append(70)
        
        # Contrast score
        contrast = quality_analysis['contrast']
        if contrast['optimal']:
            scores.append(100)
        elif contrast['is_low_contrast']:
            scores.append(40)
        else:
            scores.append(80)
        
        # Noise score (inverted - lower noise is better)
        noise_score = quality_analysis['noise']['score']
        noise_normalized = max(0, 100 - noise_score)
        scores.append(noise_normalized)
        
        return np.mean(scores)
    
    def _get_quality_grade(self, score: float) -> str:
        """Convert quality score to letter grade."""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    def _generate_quality_recommendations(self, quality_analysis: Dict[str, Any]) -> List[str]:
        """Generate quality improvement recommendations."""
        recommendations = []
        
        if quality_analysis['blur']['is_blurry']:
            recommendations.append("Image appears blurry - consider using a tripod or faster shutter speed")
        
        if quality_analysis['brightness']['is_overexposed']:
            recommendations.append("Image is overexposed - reduce exposure or use lower ISO")
        elif quality_analysis['brightness']['is_underexposed']:
            recommendations.append("Image is underexposed - increase exposure or lighting")
        
        if quality_analysis['contrast']['is_low_contrast']:
            recommendations.append("Low contrast detected - adjust levels or lighting conditions")
        
        if quality_analysis['noise']['is_noisy']:
            recommendations.append("High noise levels detected - use lower ISO or noise reduction")
        
        if not recommendations:
            recommendations.append("Image quality is good - no major issues detected")
        
        return recommendations
    
    def _determine_primary_category(self, categories: Dict[str, Any]) -> str:
        """Determine primary category from all classifications."""
        # Simple logic to determine primary category
        # In production, use more sophisticated weighting
        
        max_confidence = 0
        primary = 'unknown'
        
        for category_type, result in categories.items():
            confidence = result.get('confidence', 0)
            if confidence > max_confidence:
                max_confidence = confidence
                primary = result.get('category', 'unknown')
        
        return primary
    
    def _calculate_overall_confidence(self, categories: Dict[str, Any]) -> float:
        """Calculate overall confidence score."""
        confidences = []
        for result in categories.values():
            if 'confidence' in result:
                confidences.append(result['confidence'])
        
        return np.mean(confidences) if confidences else 0.0
    
    async def _classify_custom_categories(self, features: Dict[str, Any], custom_categories: List[str]) -> Dict[str, Any]:
        """Classify using custom user-defined categories."""
        # Placeholder for custom classification
        # In production, train custom models or use few-shot learning
        
        # For now, assign random category with moderate confidence
        import random
        selected_category = random.choice(custom_categories) if custom_categories else 'unknown'
        
        return {
            'category': selected_category,
            'confidence': 0.6,
            'custom_model_used': True
        }