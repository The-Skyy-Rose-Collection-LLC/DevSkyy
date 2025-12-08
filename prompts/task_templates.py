"""
Task Template Factory
Dynamic task injection templates for DevSkyy agents

These templates are injected at runtime to task agents with specific work.
They combine with the base system prompt to create complete prompts.

Categories:
- E-commerce Operations
- Content Generation
- Analytics & Reporting
- Security Operations
- Infrastructure Tasks
- AI/ML Operations
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class TaskCategory(Enum):
    """Task categories for template selection"""
    
    ECOMMERCE = "ecommerce"
    CONTENT = "content"
    ANALYTICS = "analytics"
    SECURITY = "security"
    INFRASTRUCTURE = "infrastructure"
    AI_ML = "ai_ml"
    CUSTOM = "custom"


class TaskPriority(Enum):
    """Task priority levels"""
    
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class TaskContext:
    """Context for task execution"""
    
    task_id: str
    category: TaskCategory
    priority: TaskPriority
    requester: str
    created_at: datetime = field(default_factory=datetime.now)
    deadline: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "task_id": self.task_id,
            "category": self.category.value,
            "priority": self.priority.value,
            "requester": self.requester,
            "created_at": self.created_at.isoformat(),
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "dependencies": self.dependencies,
            "metadata": self.metadata,
        }


class TaskTemplateFactory:
    """
    Factory for generating task injection templates.
    
    These templates are combined with agent system prompts at runtime
    to create complete, task-specific prompts.
    
    Usage:
        factory = TaskTemplateFactory()
        
        # Generate a product description task
        template = factory.create_ecommerce_task(
            task_type="product_description",
            product_data={
                "name": "Luxury Silk Dress",
                "category": "Women's Fashion",
                "price": 599.99
            },
            requirements=["SEO optimized", "3 emotional triggers", "150-200 words"]
        )
        
        # Inject into agent
        full_prompt = agent_system_prompt + template
    """
    
    def __init__(self):
        self.version = "1.0.0"
        logger.info("📋 TaskTemplateFactory initialized")
    
    # =========================================================================
    # E-COMMERCE TASK TEMPLATES
    # =========================================================================
    
    def create_ecommerce_task(
        self,
        task_type: str,
        context: Optional[TaskContext] = None,
        **kwargs
    ) -> str:
        """
        Create an e-commerce task template.
        
        Task types:
        - product_description
        - pricing_optimization
        - inventory_forecast
        - order_processing
        - customer_segmentation
        """
        templates = {
            "product_description": self._product_description_template,
            "pricing_optimization": self._pricing_optimization_template,
            "inventory_forecast": self._inventory_forecast_template,
            "order_processing": self._order_processing_template,
            "customer_segmentation": self._customer_segmentation_template,
        }
        
        template_func = templates.get(task_type)
        if not template_func:
            raise ValueError(f"Unknown e-commerce task type: {task_type}")
        
        return template_func(context=context, **kwargs)
    
    def _product_description_template(
        self,
        context: Optional[TaskContext] = None,
        product_data: Optional[Dict[str, Any]] = None,
        requirements: Optional[List[str]] = None,
        brand_voice: str = "luxury",
        word_count: int = 150,
        **kwargs
    ) -> str:
        """Generate product description task template"""
        
        product_json = json.dumps(product_data or {}, indent=2)
        reqs = requirements or ["SEO optimized", "Emotionally engaging", "Feature highlights"]
        
        return f"""
---

# TASK: PRODUCT DESCRIPTION GENERATION

## Task Context
{json.dumps(context.to_dict(), indent=2) if context else "No context provided"}

## Product Data
```json
{product_json}
```

## Requirements
{chr(10).join(f'- {req}' for req in reqs)}

## Brand Voice: {brand_voice.upper()}
{self._get_brand_voice_guide(brand_voice)}

## Word Count Target: {word_count} words (±10%)

## Output Format
```json
{{
    "title": "SEO-optimized product title",
    "short_description": "50-word teaser",
    "long_description": "Full description with paragraphs",
    "bullet_points": ["Feature 1", "Feature 2", "Feature 3"],
    "seo": {{
        "meta_title": "Title for search engines",
        "meta_description": "150-char meta description",
        "keywords": ["keyword1", "keyword2"]
    }}
}}
```

## Quality Checklist
□ Includes emotional triggers
□ Highlights key benefits (not just features)
□ Uses sensory language
□ Includes call-to-action
□ SEO keywords naturally integrated
□ No placeholder text

BEGIN GENERATION
"""
    
    def _pricing_optimization_template(
        self,
        context: Optional[TaskContext] = None,
        product_data: Optional[Dict[str, Any]] = None,
        competitor_prices: Optional[List[float]] = None,
        demand_data: Optional[Dict[str, Any]] = None,
        strategy: str = "value_based",
        **kwargs
    ) -> str:
        """Generate pricing optimization task template"""
        
        return f"""
---

# TASK: PRICING OPTIMIZATION

## Task Context
{json.dumps(context.to_dict(), indent=2) if context else "No context provided"}

## Product Data
```json
{json.dumps(product_data or {}, indent=2)}
```

## Competitor Prices
{competitor_prices or "Not provided - use market research"}

## Demand Data
```json
{json.dumps(demand_data or {}, indent=2)}
```

## Pricing Strategy: {strategy.upper()}
- value_based: Price based on perceived value
- competitive: Match or beat competitors
- penetration: Lower price for market entry
- premium: Higher price for luxury positioning
- dynamic: Real-time demand-based pricing

## Analysis Required

### 1. Market Position Analysis
<market_analysis>
- Current price positioning
- Competitor landscape
- Price elasticity estimate
</market_analysis>

### 2. Recommended Price Points
<pricing_recommendations>
- Minimum viable price: $X (covers costs + margin)
- Optimal price: $Y (maximizes revenue)
- Premium price: $Z (luxury positioning)
</pricing_recommendations>

### 3. Price Testing Strategy
<ab_test_plan>
- Control: Current price
- Variant A: [Price]
- Variant B: [Price]
- Test duration: [Days]
- Success metric: [Revenue/Conversion/Profit]
</ab_test_plan>

## Output Format
```json
{{
    "recommended_price": 0.00,
    "confidence": 0.0,
    "price_range": {{"min": 0.00, "max": 0.00}},
    "reasoning": "Explanation of recommendation",
    "ab_test": {{
        "variants": [],
        "duration_days": 14,
        "success_metric": "revenue"
    }}
}}
```

BEGIN ANALYSIS
"""
    
    def _inventory_forecast_template(
        self,
        context: Optional[TaskContext] = None,
        historical_data: Optional[Dict[str, Any]] = None,
        forecast_horizon_days: int = 30,
        confidence_level: float = 0.95,
        **kwargs
    ) -> str:
        """Generate inventory forecast task template"""
        
        return f"""
---

# TASK: INVENTORY DEMAND FORECASTING

## Task Context
{json.dumps(context.to_dict(), indent=2) if context else "No context provided"}

## Historical Data
```json
{json.dumps(historical_data or {}, indent=2)}
```

## Forecast Parameters
- Horizon: {forecast_horizon_days} days
- Confidence Level: {confidence_level * 100}%
- Method: ML ensemble (ARIMA + Prophet + XGBoost)

## Analysis Required

### 1. Data Quality Assessment
<data_quality>
- Missing values: [Count]
- Outliers detected: [Count]
- Seasonality: [Detected/Not detected]
- Trend: [Increasing/Decreasing/Stable]
</data_quality>

### 2. Forecast Output
<forecast>
- Day 1: [Units] (CI: [Low]-[High])
- Day 7: [Units] (CI: [Low]-[High])
- Day 14: [Units] (CI: [Low]-[High])
- Day 30: [Units] (CI: [Low]-[High])
</forecast>

### 3. Reorder Recommendations
<reorder>
- Current stock: [Units]
- Days until stockout: [Days]
- Recommended reorder point: [Units]
- Recommended order quantity: [Units]
- Safety stock: [Units]
</reorder>

## Output Format
```json
{{
    "forecast": [
        {{"day": 1, "predicted": 0, "lower_bound": 0, "upper_bound": 0}},
        ...
    ],
    "summary": {{
        "total_predicted_demand": 0,
        "peak_day": 1,
        "trend": "increasing"
    }},
    "reorder": {{
        "reorder_point": 0,
        "order_quantity": 0,
        "safety_stock": 0,
        "days_to_stockout": 0
    }},
    "model_metrics": {{
        "mape": 0.0,
        "rmse": 0.0,
        "confidence": 0.95
    }}
}}
```

BEGIN FORECASTING
"""
    
    def _order_processing_template(
        self,
        context: Optional[TaskContext] = None,
        order_data: Optional[Dict[str, Any]] = None,
        processing_type: str = "standard",
        **kwargs
    ) -> str:
        """Generate order processing task template"""
        
        return f"""
---

# TASK: ORDER PROCESSING

## Task Context
{json.dumps(context.to_dict(), indent=2) if context else "No context provided"}

## Order Data
```json
{json.dumps(order_data or {}, indent=2)}
```

## Processing Type: {processing_type.upper()}
- standard: Normal fulfillment flow
- express: Expedited processing
- priority: VIP customer handling
- bulk: Batch processing

## Processing Steps

### 1. Validation
<validation>
□ Order ID valid
□ Customer exists
□ Products available
□ Payment verified
□ Shipping address valid
</validation>

### 2. Inventory Allocation
<inventory>
□ Stock reserved
□ Warehouse assigned
□ Pick list generated
</inventory>

### 3. Fulfillment
<fulfillment>
□ Items picked
□ Quality check passed
□ Packed
□ Shipping label generated
</fulfillment>

### 4. Notification
<notification>
□ Order confirmation sent
□ Shipping notification sent
□ Tracking number provided
</notification>

## Output Format
```json
{{
    "order_id": "string",
    "status": "processed",
    "steps_completed": ["validation", "inventory", "fulfillment", "notification"],
    "tracking_number": "string",
    "estimated_delivery": "ISO date",
    "warehouse": "string",
    "notes": []
}}
```

BEGIN PROCESSING
"""
    
    def _customer_segmentation_template(
        self,
        context: Optional[TaskContext] = None,
        customer_data: Optional[Dict[str, Any]] = None,
        segmentation_type: str = "rfm",
        **kwargs
    ) -> str:
        """Generate customer segmentation task template"""
        
        return f"""
---

# TASK: CUSTOMER SEGMENTATION

## Task Context
{json.dumps(context.to_dict(), indent=2) if context else "No context provided"}

## Customer Data
```json
{json.dumps(customer_data or {}, indent=2)}
```

## Segmentation Method: {segmentation_type.upper()}
- rfm: Recency, Frequency, Monetary
- behavioral: Purchase patterns
- demographic: Age, location, etc.
- predictive: ML-based clustering

## Analysis Required

### 1. Customer Profile
<profile>
- Customer ID: [ID]
- Total purchases: [Count]
- Total revenue: $[Amount]
- Average order value: $[Amount]
- Days since last purchase: [Days]
- Purchase frequency: [Purchases/Month]
</profile>

### 2. Segment Assignment
<segmentation>
- Primary segment: [Segment Name]
- RFM Score: [Score]
- Lifetime value tier: [Tier]
- Churn risk: [Low/Medium/High]
</segmentation>

### 3. Recommendations
<recommendations>
- Engagement strategy: [Strategy]
- Recommended offers: [Offers]
- Communication channel: [Channel]
- Next best action: [Action]
</recommendations>

## Output Format
```json
{{
    "customer_id": "string",
    "segment": {{
        "name": "string",
        "rfm_score": "string",
        "tier": "string"
    }},
    "metrics": {{
        "total_purchases": 0,
        "total_revenue": 0.0,
        "avg_order_value": 0.0,
        "purchase_frequency": 0.0,
        "days_since_purchase": 0
    }},
    "predictions": {{
        "churn_risk": 0.0,
        "lifetime_value": 0.0,
        "next_purchase_probability": 0.0
    }},
    "recommendations": {{
        "strategy": "string",
        "offers": [],
        "channel": "string",
        "next_action": "string"
    }}
}}
```

BEGIN SEGMENTATION
"""
    
    # =========================================================================
    # CONTENT GENERATION TEMPLATES
    # =========================================================================
    
    def create_content_task(
        self,
        task_type: str,
        context: Optional[TaskContext] = None,
        **kwargs
    ) -> str:
        """
        Create a content generation task template.
        
        Task types:
        - blog_post
        - social_media
        - email_campaign
        - seo_content
        - wordpress_theme
        """
        templates = {
            "blog_post": self._blog_post_template,
            "social_media": self._social_media_template,
            "email_campaign": self._email_campaign_template,
            "wordpress_theme": self._wordpress_theme_template,
        }
        
        template_func = templates.get(task_type)
        if not template_func:
            raise ValueError(f"Unknown content task type: {task_type}")
        
        return template_func(context=context, **kwargs)
    
    def _blog_post_template(
        self,
        context: Optional[TaskContext] = None,
        topic: str = "",
        target_keywords: Optional[List[str]] = None,
        word_count: int = 1500,
        tone: str = "professional",
        **kwargs
    ) -> str:
        """Generate blog post creation template"""
        
        keywords = target_keywords or []
        
        return f"""
---

# TASK: BLOG POST CREATION

## Topic
{topic}

## SEO Keywords
Primary: {keywords[0] if keywords else "Not specified"}
Secondary: {', '.join(keywords[1:]) if len(keywords) > 1 else "Not specified"}

## Requirements
- Word count: {word_count} words
- Tone: {tone}
- Include: Header image suggestion, meta description, internal links
- Format: Markdown

## Structure
```markdown
# [Title - Include Primary Keyword]

![Header Image Description]

**Meta Description:** [150 chars max]

## Introduction (100-150 words)
[Hook + Problem statement + Preview]

## Section 1: [Subtopic]
[300-400 words]

## Section 2: [Subtopic]
[300-400 words]

## Section 3: [Subtopic]
[300-400 words]

## Conclusion
[Summary + CTA]

---
**Related Posts:** [Internal links]
**Tags:** [Relevant tags]
```

## Output Format
Return complete markdown blog post following the structure above.

BEGIN WRITING
"""
    
    def _social_media_template(
        self,
        context: Optional[TaskContext] = None,
        platform: str = "instagram",
        content_type: str = "product_launch",
        product_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """Generate social media content template"""
        
        platform_specs = {
            "instagram": {"caption_max": 2200, "hashtags_max": 30, "optimal_hashtags": 11},
            "twitter": {"caption_max": 280, "hashtags_max": 2, "optimal_hashtags": 2},
            "facebook": {"caption_max": 63206, "hashtags_max": 5, "optimal_hashtags": 2},
            "linkedin": {"caption_max": 3000, "hashtags_max": 5, "optimal_hashtags": 3},
        }
        
        specs = platform_specs.get(platform, platform_specs["instagram"])
        
        return f"""
---

# TASK: SOCIAL MEDIA CONTENT

## Platform: {platform.upper()}
- Max caption: {specs['caption_max']} chars
- Optimal hashtags: {specs['optimal_hashtags']}

## Content Type: {content_type}

## Product/Topic
```json
{json.dumps(product_data or {}, indent=2)}
```

## Output Format
```json
{{
    "caption": "Engaging caption text",
    "hashtags": ["hashtag1", "hashtag2"],
    "cta": "Call to action",
    "best_posting_time": "HH:MM timezone",
    "image_suggestions": ["Description of suggested images"],
    "carousel_slides": ["Slide 1 content", "Slide 2 content"]
}}
```

## Guidelines
- Start with hook in first line
- Use line breaks for readability
- Include emoji strategically
- End with clear CTA
- Hashtags relevant and varied

BEGIN CONTENT CREATION
"""
    
    def _email_campaign_template(
        self,
        context: Optional[TaskContext] = None,
        campaign_type: str = "promotional",
        audience_segment: str = "all",
        product_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """Generate email campaign template"""
        
        return f"""
---

# TASK: EMAIL CAMPAIGN CREATION

## Campaign Type: {campaign_type}
## Audience: {audience_segment}

## Product/Offer
```json
{json.dumps(product_data or {}, indent=2)}
```

## Email Structure
```html
Subject: [A/B Test: Version A | Version B]
Preview Text: [40-90 chars]

<email>
  <header>
    [Logo + Navigation]
  </header>
  
  <hero>
    [Headline + Hero Image]
    [Subheadline]
    [Primary CTA Button]
  </hero>
  
  <body>
    [Key Benefits - 3 points]
    [Social Proof]
    [Secondary CTA]
  </body>
  
  <footer>
    [Unsubscribe + Legal]
  </footer>
</email>
```

## Output Format
```json
{{
    "subject_lines": {{
        "version_a": "Subject A",
        "version_b": "Subject B"
    }},
    "preview_text": "Preview text",
    "html_content": "<full email HTML>",
    "plain_text": "Plain text version",
    "cta_text": "Button text",
    "cta_url": "URL placeholder",
    "send_time_recommendation": "Day and time"
}}
```

BEGIN EMAIL CREATION
"""
    
    def _wordpress_theme_template(
        self,
        context: Optional[TaskContext] = None,
        brand_name: str = "",
        style: str = "luxury",
        pages: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """Generate WordPress theme creation template"""
        
        default_pages = ["home", "shop", "product", "about", "contact", "blog"]
        pages_list = pages or default_pages
        
        return f"""
---

# TASK: WORDPRESS THEME GENERATION

## Brand: {brand_name}
## Style: {style.upper()}
## Pages: {', '.join(pages_list)}

## Theme Structure
```
theme-{brand_name.lower().replace(' ', '-')}/
├── style.css
├── functions.php
├── header.php
├── footer.php
├── index.php
├── single.php
├── page.php
├── archive.php
├── woocommerce/
│   ├── single-product.php
│   └── archive-product.php
├── assets/
│   ├── css/
│   ├── js/
│   └── images/
└── template-parts/
    ├── hero.php
    ├── product-card.php
    └── newsletter.php
```

## Style Guidelines ({style})
{self._get_style_guide(style)}

## Output Format
Provide complete theme files with:
- Full PHP template code
- CSS styling
- JavaScript functionality
- WooCommerce integration
- Responsive design
- Accessibility compliance

BEGIN THEME GENERATION
"""
    
    # =========================================================================
    # UTILITY METHODS
    # =========================================================================
    
    def _get_brand_voice_guide(self, brand_voice: str) -> str:
        """Get brand voice writing guidelines"""
        guides = {
            "luxury": """
- Use refined, sophisticated language
- Emphasize exclusivity and craftsmanship
- Appeal to aspirational emotions
- Avoid discounts/sales language
- Words: exquisite, timeless, artisan, heritage""",
            "casual": """
- Use friendly, conversational tone
- Be relatable and approachable
- Include humor where appropriate
- Use contractions freely
- Words: awesome, love, perfect, amazing""",
            "professional": """
- Use clear, precise language
- Focus on features and specifications
- Maintain authoritative tone
- Avoid superlatives without evidence
- Words: reliable, efficient, proven, trusted""",
            "streetwear": """
- Use trendy, urban language
- Reference culture and community
- Be bold and confident
- Use slang appropriately
- Words: fire, drop, exclusive, limited""",
        }
        return guides.get(brand_voice, guides["professional"])
    
    def _get_style_guide(self, style: str) -> str:
        """Get visual style guidelines"""
        guides = {
            "luxury": """
- Colors: Black, gold, cream, deep jewel tones
- Typography: Serif headers, clean sans-serif body
- Spacing: Generous whitespace
- Images: High-quality, editorial style
- Animations: Subtle, elegant transitions""",
            "minimalist": """
- Colors: Monochromatic, black/white/gray
- Typography: Clean sans-serif throughout
- Spacing: Maximum whitespace
- Images: Simple, product-focused
- Animations: None or very subtle""",
            "streetwear": """
- Colors: Bold, high contrast
- Typography: Bold sans-serif, possibly graffiti accents
- Spacing: Tight, energetic
- Images: Urban, lifestyle focused
- Animations: Dynamic, attention-grabbing""",
            "sustainable": """
- Colors: Earth tones, greens, natural palette
- Typography: Organic, rounded fonts
- Spacing: Open, breathing room
- Images: Natural, authentic
- Animations: Smooth, nature-inspired""",
        }
        return guides.get(style, guides["luxury"])
    
    # =========================================================================
    # GENERIC TASK TEMPLATE
    # =========================================================================
    
    def create_custom_task(
        self,
        task_description: str,
        context: Optional[TaskContext] = None,
        inputs: Optional[Dict[str, Any]] = None,
        expected_output: Optional[str] = None,
        constraints: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """
        Create a custom task template for any task type.
        
        Args:
            task_description: What the task should accomplish
            context: Task context with metadata
            inputs: Input data for the task
            expected_output: Description of expected output format
            constraints: List of constraints/requirements
        """
        
        return f"""
---

# TASK: CUSTOM OPERATION

## Task Description
{task_description}

## Task Context
{json.dumps(context.to_dict(), indent=2) if context else "No context provided"}

## Inputs
```json
{json.dumps(inputs or {}, indent=2)}
```

## Constraints
{chr(10).join(f'- {c}' for c in (constraints or [])) or "No specific constraints"}

## Expected Output
{expected_output or "Return structured JSON with results"}

## Execution Protocol
1. Analyze the task requirements
2. Validate all inputs
3. Execute the task logic
4. Validate outputs against constraints
5. Return structured response

BEGIN EXECUTION
"""


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


def create_task_factory() -> TaskTemplateFactory:
    """Factory function to create TaskTemplateFactory"""
    return TaskTemplateFactory()


def create_task_context(
    task_id: str,
    category: str,
    priority: str = "medium",
    requester: str = "system",
    **metadata
) -> TaskContext:
    """
    Convenience function to create TaskContext.
    
    Example:
        context = create_task_context(
            task_id="task_123",
            category="ecommerce",
            priority="high",
            requester="user_456"
        )
    """
    return TaskContext(
        task_id=task_id,
        category=TaskCategory[category.upper()],
        priority=TaskPriority[priority.upper()],
        requester=requester,
        metadata=metadata,
    )


# Export
__all__ = [
    "TaskTemplateFactory",
    "TaskContext",
    "TaskCategory",
    "TaskPriority",
    "create_task_factory",
    "create_task_context",
]
