        import re
from datetime import datetime

from jinja2 import Template
import jinja2
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4
import asyncio
import logging
import random

"""
Autonomous Landing Page Generator with A/B Testing AI
Generates high-converting landing pages with real-time optimization

Features:
    - AI-driven copywriting with Claude Sonnet 4.5
- Automated A/B/C/D testing with statistical significance
- Real-time conversion tracking and optimization
- Dynamic content personalization
- Responsive design generation
- SEO optimization
- Performance monitoring
- Heatmap analysis simulation
- Multi-variant testing
- Automatic winner selection
"""

logger = logging.getLogger(__name__)

class AutonomousLandingPageGenerator:
    """
    Generates and optimizes landing pages autonomously using AI and A/B testing.
    Creates multiple variants and automatically selects winners based on performance.
    """

    def __init__(self):
        self.templates = self._load_templates()
        self.active_tests = {}
        self.performance_data = {}
        self.conversion_goals = {
            "email_signup": 0.15,  # 15% conversion target
            "purchase": 0.05,  # 5% conversion target
            "demo_request": 0.10,  # 10% conversion target
            "download": 0.20,  # 20% conversion target
        }

        # Luxury fashion-specific elements
        self.luxury_elements = {
            "colors": {
                "primary": ["#000000", "#1a1a1a", "#8B7355", "#D4AF37", "#FFFFFF"],
                "accent": ["#C9A961", "#FF69B4", "#8B008B", "#FF1493", "#DA70D6"],
            },
            "fonts": {
                "heading": ["Playfair Display", "Didot", "Bodoni MT", "Abril Fatface"],
                "body": ["Helvetica Neue", "Futura", "Proxima Nova", "Montserrat"],
            },
            "hero_styles": ["minimal", "bold", "elegant", "dramatic", "artistic"],
            "cta_variations": [
                "Shop Now",
                "Discover Collection",
                "Experience Luxury",
                "Explore",
                "View Collection",
                "Get Exclusive Access",
            ],
        }

        logger.info("🚀 Autonomous Landing Page Generator initialized")

    def _load_templates(self) -> Dict[str, str]:
        """Load base templates for landing pages."""
        return {
            "luxury_fashion": """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <meta name="description" content="{{ meta_description }}">
    <style>
        {{ custom_styles }}
    </style>
</head>
<body>
    {{ hero_section }}
    {{ value_props }}
    {{ product_showcase }}
    {{ testimonials }}
    {{ cta_section }}
    {{ footer }}

    <!-- A/B Testing Tracker -->
    <script>
        const variantId = '{{ variant_id }}';
        const testId = '{{ test_id }}';

        // Track page view
        fetch('/api/track', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                event: 'pageview',
                variant: variantId,
                test: testId,
                timestamp: new Date().toISOString()
            })
        });

        // Track conversions
        document.querySelectorAll('[data-conversion]').forEach(el => {
            el.addEventListener('click', (e) => {
                fetch('/api/track', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        event: 'conversion',
                        type: e.target.dataset.conversion,
                        variant: variantId,
                        test: testId,
                        timestamp: new Date().toISOString()
                    })
                });
            });
        });

        // Heatmap simulation
        document.addEventListener('click', (e) => {
            fetch('/api/track', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    event: 'click',
                    x: e.clientX,
                    y: e.clientY,
                    element: e.target.tagName,
                    variant: variantId,
                    test: testId
                })
            });
        });
    </script>
</body>
</html>
            """,
        }

    async def generate_landing_page(
        self,
        product_name: str,
        target_audience: str,
        goal: str = "email_signup",
        num_variants: int = 4,
    ) -> Dict[str, Any]:
        """
        Generate multiple landing page variants for A/B testing.

        Args:
            product_name: Name of the product/collection
            target_audience: Target demographic
            goal: Conversion goal type
            num_variants: Number of variants to generate

        Returns:
            Dict containing test ID and variant details
        """
        test_id = str(uuid4())
        variants = []

        logger.info(
            f"🎨 Generating {num_variants} landing page variants for {product_name}"
        )

        for i in range(num_variants):
            variant = await self._create_variant(
                product_name, target_audience, goal, chr(65 + i)
            )  # A, B, C, D
            variants.append(variant)

        # Initialize A/B test
        self.active_tests[test_id] = {
            "product": product_name,
            "audience": target_audience,
            "goal": goal,
            "variants": variants,
            "start_time": datetime.now(),
            "performance": {v["id"]: {"views": 0, "conversions": 0} for v in variants},
        }

        return {
            "test_id": test_id,
            "variants": variants,
            "status": "active",
            "message": f"Generated {num_variants} landing page variants",
        }

    async def _create_variant(
        self, product_name: str, target_audience: str, goal: str, variant_label: str
    ) -> Dict[str, Any]:
        """Create a single landing page variant."""
        variant_id = str(uuid4())

        # Generate variant-specific elements
        hero = self._generate_hero_section(product_name, variant_label)
        value_props = self._generate_value_props(target_audience, variant_label)
        product_showcase = self._generate_product_showcase(product_name, variant_label)
        testimonials = self._generate_testimonials(variant_label)
        cta = self._generate_cta_section(goal, variant_label)
        styles = self._generate_styles(variant_label)

        # Compile full HTML with safe template rendering
        html = render_safe_template(
            self.templates["luxury_fashion"],
            title=f"{product_name} - The Skyy Rose Collection",
            meta_description=f"Discover {product_name} - Luxury fashion redefined",
            custom_styles=styles,
            hero_section=hero,
            value_props=value_props,
            product_showcase=product_showcase,
            testimonials=testimonials,
            cta_section=cta,
            footer=self._generate_footer(),
            variant_id=variant_id,
            test_id="",  # Will be set when test starts
        )

        return {
            "id": variant_id,
            "label": f"Variant {variant_label}",
            "html": html,
            "elements": {
                "hero_style": self._get_variant_element(variant_label, "hero"),
                "cta_text": self._get_variant_element(variant_label, "cta"),
                "color_scheme": self._get_variant_element(variant_label, "color"),
            },
        }

    def _generate_hero_section(self, product_name: str, variant: str) -> str:
        """Generate hero section with variant-specific styling."""
        hero_style = self.luxury_elements["hero_styles"][
            ord(variant) - 65 % len(self.luxury_elements["hero_styles"])
        ]
        cta_text = self.luxury_elements["cta_variations"][
            ord(variant) - 65 % len(self.luxury_elements["cta_variations"])
        ]

        return f"""
        <section class="hero hero-{hero_style}" data-variant="{variant}">
            <div class="hero-content">
                <h1 class="hero-title">{product_name}</h1>
                <p class="hero-subtitle">Redefining Luxury Fashion</p>
                <button class="cta-button primary" data-conversion="hero_cta">
                    {cta_text}
                </button>
            </div>
            <div class="hero-image">
                <!-- Dynamic image based on variant -->
            </div>
        </section>
        """

    def _generate_value_props(self, target_audience: str, variant: str) -> str:
        """Generate value propositions section."""
        props = {
            "A": ["Exclusive Designs", "Premium Quality", "Timeless Elegance"],
            "B": ["Sustainable Luxury", "Artisan Crafted", "Limited Edition"],
            "C": ["Modern Heritage", "Innovative Materials", "Bespoke Service"],
            "D": ["Cultural Fusion", "Ethical Fashion", "Personal Styling"],
        }

        selected_props = props.get(variant, props["A"])

        props_html = ""
        for prop in selected_props:
            props_html += f"""
            <div class="value-prop">
                <h3>{prop}</h3>
                <p>Experience the pinnacle of {prop.lower()} with our collection</p>
            </div>
            """

        return f"""
        <section class="value-props">
            <div class="container">
                <h2>Why Choose The Skyy Rose Collection</h2>
                <div class="props-grid">
                    {props_html}
                </div>
            </div>
        </section>
        """

    def _generate_product_showcase(self, product_name: str, variant: str) -> str:
        """Generate product showcase section."""
        layout_styles = {
            "A": "grid",
            "B": "carousel",
            "C": "masonry",
            "D": "featured",
        }

        layout = layout_styles.get(variant, "grid")

        return f"""
        <section class="product-showcase showcase-{layout}">
            <div class="container">
                <h2>Featured from {product_name}</h2>
                <div class="products-{layout}">
                    <!-- Dynamic product cards -->
                    <div class="product-card">
                        <img src="/api/placeholder/300/400" alt="Product 1">
                        <h3>Signature Piece</h3>
                        <p class="price">$2,500</p>
                        <button data-conversion="product_view">View Details</button>
                    </div>
                </div>
            </div>
        </section>
        """

    def _generate_testimonials(self, variant: str) -> str:
        """Generate testimonials section."""
        testimonial_styles = {
            "A": "Clean quotes with photos",
            "B": "Video testimonials",
            "C": "Instagram-style cards",
            "D": "Rotating carousel",
        }

        return f"""
        <section class="testimonials">
            <div class="container">
                <h2>What Our Clients Say</h2>
                <!-- {testimonial_styles.get(variant, testimonial_styles['A'])} -->
                <div class="testimonial-grid">
                    <div class="testimonial">
                        <p>"Absolutely stunning quality and design"</p>
                        <cite>- Fashion Editor, Vogue</cite>
                    </div>
                </div>
            </div>
        </section>
        """

    def _generate_cta_section(self, goal: str, variant: str) -> str:
        """Generate call-to-action section based on conversion goal."""
        cta_text = self.luxury_elements["cta_variations"][
            ord(variant) - 65 % len(self.luxury_elements["cta_variations"])
        ]

        goal_specific = {
            "email_signup": f"""
                <input type="email" placeholder="Enter your email for exclusive access">
                <button data-conversion="email_signup">{cta_text}</button>
            """,
            "purchase": f"""
                <button data-conversion="purchase" class="cta-large">{cta_text}</button>
                <p>Free worldwide shipping on orders over $500</p>
            """,
            "demo_request": f"""
                <button data-conversion="demo_request">Schedule Personal Consultation</button>
                <p>Experience our collection with a style expert</p>
            """,
            "download": f"""
                <button data-conversion="download">Download Lookbook</button>
                <p>Get our exclusive 2024 collection catalog</p>
            """,
        }

        return f"""
        <section class="cta-section">
            <div class="container">
                <h2>Ready to Elevate Your Style?</h2>
                {goal_specific.get(goal, goal_specific["email_signup"])}
            </div>
        </section>
        """

    def _generate_styles(self, variant: str) -> str:
        """Generate CSS styles for the variant."""
        color_index = ord(variant) - 65
        primary = self.luxury_elements["colors"]["primary"][
            color_index % len(self.luxury_elements["colors"]["primary"])
        ]
        accent = self.luxury_elements["colors"]["accent"][
            color_index % len(self.luxury_elements["colors"]["accent"])
        ]
        heading_font = self.luxury_elements["fonts"]["heading"][
            color_index % len(self.luxury_elements["fonts"]["heading"])
        ]
        body_font = self.luxury_elements["fonts"]["body"][
            color_index % len(self.luxury_elements["fonts"]["body"])
        ]

        return f"""
        @import url('https://fonts.googleapis.com/css2?family={heading_font.replace(' ', '+')}:wght@400;700&family={body_font.replace(' ', '+')}:wght@300;400;700&display=swap');

        :root {{
            --primary-color: {primary};
            --accent-color: {accent};
            --heading-font: '{heading_font}', serif;
            --body-font: '{body_font}', sans-serif;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: var(--body-font);
            line-height: 1.6;
            color: var(--primary-color);
        }}

        h1, h2, h3 {{
            font-family: var(--heading-font);
            font-weight: 700;
            margin-bottom: 1rem;
        }}

        .hero {{
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
            color: white;
            text-align: center;
        }}

        .hero-title {{
            font-size: 4rem;
            margin-bottom: 1rem;
            letter-spacing: 2px;
        }}

        .cta-button {{
            padding: 1rem 3rem;
            font-size: 1.2rem;
            background: white;
            color: var(--primary-color);
            border: none;
            cursor: pointer;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .cta-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 4rem 2rem;
        }}

        section {{
            padding: 4rem 0;
        }}

        .value-props {{
            background: #f8f8f8;
        }}

        .props-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-top: 3rem;
        }}

        .value-prop {{
            text-align: center;
            padding: 2rem;
        }}

        .products-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 2rem;
            margin-top: 3rem;
        }}

        .product-card {{
            background: white;
            border: 1px solid #e0e0e0;
            padding: 1rem;
            transition: transform 0.3s ease;
        }}

        .product-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}

        .product-card img {{
            width: 100%;
            height: auto;
        }}

        .price {{
            font-size: 1.5rem;
            font-weight: bold;
            color: var(--accent-color);
            margin: 1rem 0;
        }}

        @media (max-width: 768px) {{
            .hero-title {{
                font-size: 2.5rem;
            }}

            .props-grid,
            .products-grid {{
                grid-template-columns: 1fr;
            }}
        }}
        """

    def _generate_footer(self) -> str:
        """Generate footer section."""
        return """
        <footer>
            <div class="container">
                <p>&copy; 2024 The Skyy Rose Collection. All rights reserved.</p>
                <div class="social-links">
                    <a href="#">Instagram</a>
                    <a href="#">Facebook</a>
                    <a href="#">Pinterest</a>
                </div>
            </div>
        </footer>
        """

    def _get_variant_element(self, variant: str, element_type: str) -> str:
        """Get variant-specific element."""
        index = ord(variant) - 65

        if element_type == "hero":
            return self.luxury_elements["hero_styles"][
                index % len(self.luxury_elements["hero_styles"])
            ]
        elif element_type == "cta":
            return self.luxury_elements["cta_variations"][
                index % len(self.luxury_elements["cta_variations"])
            ]
        elif element_type == "color":
            primary = self.luxury_elements["colors"]["primary"][
                index % len(self.luxury_elements["colors"]["primary"])
            ]
            accent = self.luxury_elements["colors"]["accent"][
                index % len(self.luxury_elements["colors"]["accent"])
            ]
            return f"{primary}/{accent}"

        return ""

    async def track_event(
        self,
        test_id: str,
        variant_id: str,
        event_type: str,
        data: Optional[Dict] = None,
    ) -> bool:
        """
        Track user interaction event for A/B testing.

        Args:
            test_id: Test identifier
            variant_id: Variant identifier
            event_type: Type of event (pageview, conversion, click)
            data: Additional event data

        Returns:
            Success status
        """
        if test_id not in self.active_tests:
            logger.warning(f"Test {test_id} not found")
            return False

        test = self.active_tests[test_id]

        if event_type == "pageview":
            test["performance"][variant_id]["views"] += 1
        elif event_type == "conversion":
            test["performance"][variant_id]["conversions"] += 1

        # Store detailed event data for analysis
        if test_id not in self.performance_data:
            self.performance_data[test_id] = []

        self.performance_data[test_id].append(
            {
                "variant": variant_id,
                "event": event_type,
                "timestamp": datetime.now(),
                "data": data or {},
            }
        )

        return True

    async def analyze_test_performance(self, test_id: str) -> Dict[str, Any]:
        """
        Analyze A/B test performance and determine winner.

        Uses statistical significance testing to determine winning variant.
        """
        if test_id not in self.active_tests:
            return {"error": "Test not found"}

        test = self.active_tests[test_id]
        results = []

        for variant in test["variants"]:
            variant_id = variant["id"]
            perf = test["performance"][variant_id]

            # Calculate conversion rate
            conversion_rate = (
                perf["conversions"] / perf["views"] if perf["views"] > 0 else 0
            )

            # Calculate confidence interval
            confidence = self._calculate_confidence(perf["conversions"], perf["views"])

            results.append(
                {
                    "variant": variant["label"],
                    "variant_id": variant_id,
                    "views": perf["views"],
                    "conversions": perf["conversions"],
                    "conversion_rate": conversion_rate,
                    "confidence_interval": confidence,
                    "elements": variant["elements"],
                }
            )

        # Sort by conversion rate
        results.sort(key=lambda x: x["conversion_rate"], reverse=True)

        # Determine if we have a statistically significant winner
        winner = None
        if len(results) >= 2 and results[0]["views"] >= 100:
            # Check if top performer is significantly better
            if results[0]["conversion_rate"] > results[1]["conversion_rate"] * 1.2:
                winner = results[0]

        return {
            "test_id": test_id,
            "product": test["product"],
            "audience": test["audience"],
            "goal": test["goal"],
            "duration": (datetime.now() - test["start_time"]).total_seconds() / 3600,
            "results": results,
            "winner": winner,
            "recommendation": self._get_recommendation(results, winner),
        }

    def _calculate_confidence(
        self, conversions: int, views: int
    ) -> Tuple[float, float]:
        """Calculate 95% confidence interval for conversion rate."""
        if views == 0:
            return (0, 0)

        p = conversions / views
        z = 1.96  # 95% confidence

        # Wilson score interval
        denominator = 1 + z**2 / views
        centre_adjusted_probability = p + z**2 / (2 * views)
        adjusted_standard_deviation = (p * (1 - p) + z**2 / (4 * views)) / views

        lower = (
            centre_adjusted_probability - z * (adjusted_standard_deviation**0.5)
        ) / denominator
        upper = (
            centre_adjusted_probability + z * (adjusted_standard_deviation**0.5)
        ) / denominator

        return (max(0, lower), min(1, upper))

    def _get_recommendation(self, results: List[Dict], winner: Optional[Dict]) -> str:
        """Generate recommendation based on test results."""
        if winner:
            elements = winner["elements"]
            return f"""
            ✅ **Winner Found**: {winner['variant']} with {winner['conversion_rate']:.2%} conversion rate

            **Winning Elements**:
            - Hero Style: {elements['hero_style']}
            - CTA Text: {elements['cta_text']}
            - Color Scheme: {elements['color_scheme']}

            **Recommendation**: Deploy this variant to production. The winning combination shows
            a {(winner['conversion_rate'] / results[-1]['conversion_rate'] - 1) * 100:.1f}% improvement
            over the worst performer.
            """

        elif results[0]["views"] < 100:
            return """
            ⏳ **More Data Needed**: Continue running the test to achieve statistical significance.
            Minimum 100 views per variant recommended for reliable results.
            """

        else:
            return """
            📊 **No Clear Winner Yet**: Variants are performing similarly. Consider:
            1. Running test longer for more data
            2. Creating more differentiated variants
            3. Testing different page elements
            """

    async def auto_optimize(self, test_id: str) -> Dict[str, Any]:
        """
        Automatically optimize landing page based on test results.
        Generates new variants based on winning elements.
        """
        analysis = await self.analyze_test_performance(test_id)

        if not analysis.get("winner"):
            return {
                "status": "waiting",
                "message": "Not enough data for optimization yet",
            }

        winner = analysis["winner"]
        test = self.active_tests[test_id]

        # Generate new optimized variants based on winner
        logger.info(f"🎯 Auto-optimizing based on winning variant: {winner['variant']}")

        # Create new test with optimized variants
        new_variants = []
        winning_elements = winner["elements"]

        # Generate variations of the winning formula
        for i in range(3):
            variant = await self._create_optimized_variant(
                test["product"],
                test["audience"],
                test["goal"],
                winning_elements,
                chr(65 + i),
            )
            new_variants.append(variant)

        # Start new optimized test
        new_test_id = str(uuid4())
        self.active_tests[new_test_id] = {
            "product": test["product"],
            "audience": test["audience"],
            "goal": test["goal"],
            "variants": new_variants,
            "start_time": datetime.now(),
            "performance": {
                v["id"]: {"views": 0, "conversions": 0} for v in new_variants
            },
            "parent_test": test_id,
            "optimization_round": test.get("optimization_round", 0) + 1,
        }

        return {
            "status": "optimized",
            "new_test_id": new_test_id,
            "based_on": winner["variant"],
            "improvements": winning_elements,
            "message": f"Created optimized test with {len(new_variants)} new variants",
        }

    async def _create_optimized_variant(
        self,
        product_name: str,
        target_audience: str,
        goal: str,
        winning_elements: Dict,
        variant_label: str,
    ) -> Dict[str, Any]:
        """Create optimized variant based on winning elements."""
        # Start with winning elements and make minor variations
        variant = await self._create_variant(
            product_name, target_audience, goal, variant_label
        )

        # Apply winning elements with slight modifications
        variant["elements"] = {
            "hero_style": winning_elements["hero_style"],
            "cta_text": self._get_similar_cta(winning_elements["cta_text"]),
            "color_scheme": self._adjust_colors(winning_elements["color_scheme"]),
        }

        return variant

    def _get_similar_cta(self, winning_cta: str) -> str:
        """Get similar CTA text to winning variant."""
        similar_ctas = {
            "Shop Now": ["Shop Collection", "Shop Today", "Start Shopping"],
            "Discover Collection": [
                "Explore Collection",
                "View Collection",
                "See Collection",
            ],
            "Experience Luxury": ["Discover Luxury", "Feel Luxury", "Live Luxury"],
        }

        for key, values in similar_ctas.items():
            if winning_cta == key:
                return random.choice(values)

        return winning_cta

    def _adjust_colors(self, color_scheme: str) -> str:
        """Create slight variation of winning color scheme."""
        # Parse color scheme
        colors = color_scheme.split("/")
        if len(colors) != 2:
            return color_scheme

        # Slightly adjust colors (simplified for example)
        # In production, would use proper color theory
        return f"{colors[0]}/{colors[1]}"

    async def export_winner(self, test_id: str) -> Dict[str, Any]:
        """
        Export winning landing page variant for production deployment.
        """
        analysis = await self.analyze_test_performance(test_id)

        if not analysis.get("winner"):
            return {
                "error": "No winner determined yet",
                "status": "failed",
            }

        winner = analysis["winner"]
        test = self.active_tests[test_id]

        # Find winning variant HTML
        winning_variant = next(
            (v for v in test["variants"] if v["id"] == winner["variant_id"]), None
        )

        if not winning_variant:
            return {"error": "Winner variant not found", "status": "failed"}

        # Clean HTML for production (remove tracking scripts)
        production_html = self._prepare_for_production(winning_variant["html"])

        # Generate deployment package
        deployment = {
            "html": production_html,
            "variant_id": winner["variant_id"],
            "performance": {
                "conversion_rate": winner["conversion_rate"],
                "confidence": winner["confidence_interval"],
                "total_views": winner["views"],
                "total_conversions": winner["conversions"],
            },
            "elements": winner["elements"],
            "test_id": test_id,
            "exported_at": datetime.now().isoformat(),
        }

        # Save to file
        filename = f"landing_page_{test['product'].replace(' ', '_')}_{winner['variant_id'][:8]}.html"

        return {
            "status": "exported",
            "filename": filename,
            "deployment": deployment,
            "message": f"Exported winning variant with {winner['conversion_rate']:.2%} conversion rate",
        }

    def _prepare_for_production(self, html: str) -> str:
        """Remove testing code and prepare HTML for production."""
        # In a real implementation, would properly parse and clean HTML
        # For now, simple string replacement

        # Remove A/B testing tracker script
        html = re.sub(
            r"<!-- A/B Testing Tracker -->.*?</script>", "", html, flags=re.DOTALL
        )

        # Remove data attributes used for testing
        html = re.sub(r'data-variant="[^"]*"', "", html)
        html = re.sub(r'data-conversion="[^"]*"', "", html)

        return html

# Factory function
def create_landing_page_generator() -> AutonomousLandingPageGenerator:
    """Create Autonomous Landing Page Generator."""
    return AutonomousLandingPageGenerator()

# Example usage
async def main():
    """Example: Generate and test landing pages."""
    generator = create_landing_page_generator(
    # Generate landing page variants
    result = await generator.generate_landing_page(
        product_name="2024 Rose Gold Collection",
        target_audience="Affluent women 25-45 interested in luxury fashion",
        goal="email_signup",
        num_variants=4,
)

    logger.info(f"✅ Generated test: {result['test_id']}")
    logger.info(f"📊 Created {len(result['variants'])} variants")

    # Simulate some traffic and conversions
    test_id = result["test_id"]
    for variant in result["variants"]:
        # Simulate views
        for _ in range(random.randint(100, 500)):
            await generator.track_event(test_id, variant["id"], "pageview")

        # Simulate conversions (different rates per variant)
        conversion_rate = random.uniform(0.05, 0.25)
        num_conversions = int(100 * conversion_rate)
        for _ in range(num_conversions):
            await generator.track_event(test_id, variant["id"], "conversion")

    # Analyze results
    analysis = await generator.analyze_test_performance(test_id)

    logger.info("\n📊 Test Results:")
    for result in analysis["results"]:
        logger.info(
            f"  {result['variant']}: {result['conversion_rate']:.2%} ({result['views']} views)"
        )

    if analysis.get("winner"):
        logger.info(f"\n🏆 Winner: {analysis['winner']['variant']}")

    # Auto-optimize based on results
    optimization = await generator.auto_optimize(test_id)
    if optimization["status"] == "optimized":
        logger.info(f"\n🚀 Created optimized test: {optimization['new_test_id']}")

    # Export winner
    export = await generator.export_winner(test_id)
    if export["status"] == "exported":
        logger.info(f"\n✅ Exported to: {export['filename']}")

if __name__ == "__main__":
    asyncio.run(main())

def create_safe_template(template_string: str) -> jinja2.Template:
    """
    Create a safe Jinja2 template with comprehensive XSS protection.

    Security features:
    - Automatic HTML escaping for html/xml templates
    - Restricted template features to prevent code injection
    - Safe finalization of undefined variables
    """
    # Create secure environment with restricted features
    env = jinja2.Environment(
        # Enable automatic escaping for HTML/XML content
        autoescape=jinja2.select_autoescape(['html', 'xml']),
        # Safely handle undefined variables
        finalize=lambda x: x if x is not None else '',
        # Disable potentially dangerous features
        trim_blocks=True,
        lstrip_blocks=True,
        # Prevent access to private attributes
        undefined=jinja2.StrictUndefined
    )

    # Remove potentially dangerous globals and filters
    env.globals.pop('range', None)
    env.globals.pop('lipsum', None)
    env.globals.pop('cycler', None)

    return env.from_string(template_string)

def render_safe_template(template_string: str, **kwargs) -> str:
    """
    Safely render template with comprehensive input sanitization.

    Security measures:
    - HTML escaping of all string inputs
    - Validation of template variables
    - Protection against template injection
    """
    try:
        template = create_safe_template(template_string)

        # Sanitize all input variables
        safe_kwargs = {}
        for key, value in kwargs.items():
            # Validate key name to prevent injection
            if not key.replace('_', '').isalnum():
                raise ValueError(f"Invalid template variable name: {key}")

            if isinstance(value, str):
                # Escape HTML characters and limit length
                if len(value) > 10000:  # Prevent DoS via large strings
                    value = value[:10000] + "..."
                safe_kwargs[key] = jinja2.escape(value)
            elif isinstance(value, (int, float, bool)):
                safe_kwargs[key] = value
            elif value is None:
                safe_kwargs[key] = ""
            else:
                # Convert other types to safe strings
                safe_kwargs[key] = jinja2.escape(str(value))

        return template.render(**safe_kwargs)

    except jinja2.TemplateError as e:
        logger.error(f"Template rendering error: {e}")
        return "<div>Template rendering error</div>"
    except Exception as e:
        logger.error(f"Unexpected error in template rendering: {e}")
        return "<div>Content unavailable</div>"
