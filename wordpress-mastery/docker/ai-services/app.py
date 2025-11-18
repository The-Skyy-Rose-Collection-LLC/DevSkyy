"""
Luxury AI Services API
Advanced eCommerce AI capabilities for WordPress WooCommerce

This Flask application provides AI-powered features including:
- Product image analysis and material detection
- Style categorization and quality assessment
- Customer segmentation and behavior analysis
- Dynamic pricing and recommendation algorithms
- Real-time inventory optimization

Registry: docker.io/skyyrosellc/devskyy
Version: 1.0.0
"""

from datetime import datetime

from flask import Flask, jsonify, request
from flask_cors import CORS
from services.customer_segmentation import CustomerSegmentation
from services.dynamic_pricing import DynamicPricing
from services.media_optimizer import MediaOptimizer

# Import AI service modules
from services.product_analyzer import ProductAnalyzer
from services.recommendation_engine import RecommendationEngine
from utils.cache import CacheManager
from utils.logger import setup_logger
from utils.security import validate_request, verify_api_key


# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Setup logging
logger = setup_logger(__name__)

# Initialize services
try:
    product_analyzer = ProductAnalyzer()
    recommendation_engine = RecommendationEngine()
    customer_segmentation = CustomerSegmentation()
    dynamic_pricing = DynamicPricing()
    media_optimizer = MediaOptimizer()
    cache_manager = CacheManager()

    logger.info("🤖 AI Services initialized successfully")
except Exception as e:
    logger.error(f"❌ Failed to initialize AI services: {e!s}")
    raise


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for Docker container monitoring"""
    try:
        # Check service health
        services_status = {
            "product_analyzer": product_analyzer.is_healthy(),
            "recommendation_engine": recommendation_engine.is_healthy(),
            "customer_segmentation": customer_segmentation.is_healthy(),
            "dynamic_pricing": dynamic_pricing.is_healthy(),
            "media_optimizer": media_optimizer.is_healthy(),
            "cache": cache_manager.is_healthy(),
        }

        all_healthy = all(services_status.values())

        return jsonify(
            {
                "status": "healthy" if all_healthy else "degraded",
                "timestamp": datetime.utcnow().isoformat(),
                "services": services_status,
                "version": "1.0.0",
            }
        ), (200 if all_healthy else 503)

    except Exception as e:
        logger.error(f"Health check failed: {e!s}")
        return jsonify({"status": "unhealthy", "error": str(e), "timestamp": datetime.utcnow().isoformat()}), 503


@app.route("/api/v1/analyze_product", methods=["POST"])
@verify_api_key
@validate_request
def analyze_product():
    """
    Analyze product images and descriptions using AI

    Expected payload:
    {
        "product_id": int,
        "product_images": {
            "main": {"url": str, "alt": str, "metadata": dict},
            "gallery": [{"url": str, "alt": str, "metadata": dict}]
        },
        "product_description": str,
        "product_attributes": dict
    }
    """
    try:
        data = request.get_json()
        product_id = data.get("product_id")

        # Check cache first
        cache_key = f"product_analysis_{product_id}"
        cached_result = cache_manager.get(cache_key)
        if cached_result:
            logger.info(f"📋 Returning cached analysis for product {product_id}")
            return jsonify(cached_result)

        logger.info(f"🔍 Analyzing product {product_id}")

        # Perform AI analysis
        analysis_result = product_analyzer.analyze_product(
            product_id=product_id,
            images=data.get("product_images", {}),
            description=data.get("product_description", ""),
            attributes=data.get("product_attributes", {}),
        )

        # Cache the result
        cache_manager.set(cache_key, analysis_result, ttl=3600)  # 1 hour

        logger.info(f"✅ Product {product_id} analysis completed")
        return jsonify(analysis_result)

    except Exception as e:
        logger.error(f"❌ Product analysis failed: {e!s}")
        return jsonify({"error": "Product analysis failed", "message": str(e)}), 500


@app.route("/api/v1/get_recommendations", methods=["POST"])
@verify_api_key
@validate_request
def get_recommendations():
    """
    Get AI-powered product recommendations

    Expected payload:
    {
        "product_id": int,
        "customer_segment": str,
        "recommendation_type": str,  # 'related', 'cross_sell', 'upsell'
        "customer_history": list
    }
    """
    try:
        data = request.get_json()
        product_id = data.get("product_id")
        customer_segment = data.get("customer_segment", "general")
        recommendation_type = data.get("recommendation_type", "related")

        cache_key = f"recommendations_{product_id}_{customer_segment}_{recommendation_type}"
        cached_result = cache_manager.get(cache_key)
        if cached_result:
            logger.info(f"📋 Returning cached recommendations for product {product_id}")
            return jsonify(cached_result)

        logger.info(f"🎯 Generating {recommendation_type} recommendations for product {product_id}")

        recommendations = recommendation_engine.get_recommendations(
            product_id=product_id,
            customer_segment=customer_segment,
            recommendation_type=recommendation_type,
            customer_history=data.get("customer_history", []),
        )

        # Cache the result
        cache_manager.set(cache_key, recommendations, ttl=1800)  # 30 minutes

        logger.info(f"✅ Generated {len(recommendations)} recommendations")
        return jsonify(recommendations)

    except Exception as e:
        logger.error(f"❌ Recommendation generation failed: {e!s}")
        return jsonify({"error": "Recommendation generation failed", "message": str(e)}), 500


@app.route("/api/v1/update_customer_segment", methods=["POST"])
@verify_api_key
@validate_request
def update_customer_segment():
    """
    Update customer segment based on behavior analysis

    Expected payload:
    {
        "customer_id": int,
        "behavior_data": {
            "viewed_products": list,
            "time_on_page": int,
            "interactions": str,
            "price_range_interest": str
        },
        "current_segment": str
    }
    """
    try:
        data = request.get_json()
        customer_id = data.get("customer_id")
        behavior_data = data.get("behavior_data", {})
        current_segment = data.get("current_segment", "new_visitor")

        logger.info(f"👤 Updating customer segment for customer {customer_id}")

        new_segment = customer_segmentation.update_segment(
            customer_id=customer_id, behavior_data=behavior_data, current_segment=current_segment
        )

        result = {
            "segment": new_segment,
            "confidence": customer_segmentation.get_segment_confidence(new_segment),
            "characteristics": customer_segmentation.get_segment_characteristics(new_segment),
        }

        logger.info(f"✅ Customer {customer_id} updated to segment: {new_segment}")
        return jsonify(result)

    except Exception as e:
        logger.error(f"❌ Customer segmentation failed: {e!s}")
        return jsonify({"error": "Customer segmentation failed", "message": str(e)}), 500


@app.route("/api/v1/get_dynamic_pricing", methods=["POST"])
@verify_api_key
@validate_request
def get_dynamic_pricing():
    """
    Get dynamic pricing recommendations

    Expected payload:
    {
        "product_id": int,
        "customer_segment": str,
        "inventory_level": dict,
        "demand_metrics": dict
    }
    """
    try:
        data = request.get_json()
        product_id = data.get("product_id")
        customer_segment = data.get("customer_segment", "general")

        cache_key = f"dynamic_pricing_{product_id}_{customer_segment}"
        cached_result = cache_manager.get(cache_key)
        if cached_result:
            logger.info(f"📋 Returning cached pricing for product {product_id}")
            return jsonify(cached_result)

        logger.info(f"💰 Calculating dynamic pricing for product {product_id}")

        pricing_data = dynamic_pricing.calculate_pricing(
            product_id=product_id,
            customer_segment=customer_segment,
            inventory_level=data.get("inventory_level", {}),
            demand_metrics=data.get("demand_metrics", {}),
        )

        # Cache the result for shorter time due to dynamic nature
        cache_manager.set(cache_key, pricing_data, ttl=300)  # 5 minutes

        logger.info(f"✅ Dynamic pricing calculated for product {product_id}")
        return jsonify(pricing_data)

    except Exception as e:
        logger.error(f"❌ Dynamic pricing calculation failed: {e!s}")
        return jsonify({"error": "Dynamic pricing calculation failed", "message": str(e)}), 500


@app.route("/api/v1/optimize_media", methods=["POST"])
@verify_api_key
@validate_request
def optimize_media():
    """
    Optimize product media for different resolutions and formats

    Expected payload:
    {
        "image_url": str,
        "target_resolutions": list,
        "optimization_level": str
    }
    """
    try:
        data = request.get_json()
        image_url = data.get("image_url")
        target_resolutions = data.get("target_resolutions", ["300x300", "600x600", "1200x1200"])
        optimization_level = data.get("optimization_level", "high")

        logger.info(f"🖼️ Optimizing media: {image_url}")

        optimized_media = media_optimizer.optimize_image(
            image_url=image_url, target_resolutions=target_resolutions, optimization_level=optimization_level
        )

        logger.info("✅ Media optimization completed")
        return jsonify(optimized_media)

    except Exception as e:
        logger.error(f"❌ Media optimization failed: {e!s}")
        return jsonify({"error": "Media optimization failed", "message": str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found", "message": "The requested API endpoint does not exist"}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error!s}")
    return jsonify({"error": "Internal server error", "message": "An unexpected error occurred"}), 500


if __name__ == "__main__":
    # Development server
    app.run(host="0.0.0.0", port=8080, debug=False)
else:
    # Production server (gunicorn)
    logger.info("🚀 Luxury AI Services API started in production mode")
    logger.info("📊 Available endpoints:")
    logger.info("   POST /api/v1/analyze_product - Product AI analysis")
    logger.info("   POST /api/v1/get_recommendations - AI recommendations")
    logger.info("   POST /api/v1/update_customer_segment - Customer segmentation")
    logger.info("   POST /api/v1/get_dynamic_pricing - Dynamic pricing")
    logger.info("   POST /api/v1/optimize_media - Media optimization")
    logger.info("   GET /health - Health check")
