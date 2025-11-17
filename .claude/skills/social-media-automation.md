---
name: social-media-automation
description: Brand-aware social media automation for Instagram, Facebook, TikTok with AI content generation and scheduling
---

You are the Social Media Automation expert for DevSkyy. Create and schedule brand-aligned content across multiple platforms with AI-powered optimization.

## Core Social Media System

### 1. Brand-Aware Content Generator

```python
from typing import Dict, Any, List
import anthropic
import os

class SocialMediaContentGenerator:
    """Generate brand-aligned social media content"""

    def __init__(self, brand_manager):
        self.brand_manager = brand_manager
        self.brand_context = brand_manager.get_brand_context()
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    async def generate_post(
        self,
        platform: str,
        post_type: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate social media post with brand voice.

        Args:
            platform: Platform (instagram, facebook, tiktok, pinterest)
            post_type: Type (product_launch, lifestyle, behind_the_scenes, ugc)
            context: Context for post (product_info, event_info, etc.)

        Returns:
            Generated post with caption, hashtags, and media suggestions
        """
        brand = self.brand_context

        # Platform-specific constraints
        constraints = {
            "instagram": {
                "caption_max": 2200,
                "hashtags_max": 30,
                "tone": "visual_storytelling"
            },
            "facebook": {
                "caption_max": 63206,
                "hashtags_max": 10,
                "tone": "conversational"
            },
            "tiktok": {
                "caption_max": 150,
                "hashtags_max": 5,
                "tone": "trendy_authentic"
            }
        }

        platform_constraints = constraints.get(platform, constraints["instagram"])

        prompt = f"""Create a {platform} post for {brand['brand_name']}.

Brand Voice:
- Tone: {brand['voice']['tone']}
- Personality: {', '.join(brand['voice']['personality'])}
- Style: {brand['voice']['style']}

Post Type: {post_type}
Context: {context}

Platform Constraints:
- Max caption length: {platform_constraints['caption_max']} characters
- Max hashtags: {platform_constraints['hashtags_max']}
- Tone: {platform_constraints['tone']}

Generate:
1. Compelling caption that matches brand voice
2. Relevant hashtags (mix of popular and niche)
3. Call-to-action
4. Media suggestions (image/video description)

Format as JSON:
{{
    "caption": "...",
    "hashtags": ["#...", "#..."],
    "cta": "...",
    "media_suggestions": ["..."],
    "best_time_to_post": "..."
}}"""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            import json
            post_data = json.loads(message.content[0].text)

            return {
                "success": True,
                "platform": platform,
                "post_type": post_type,
                "post_data": post_data,
                "brand_aligned": True
            }

        except Exception as e:
            return {
                "error": f"Post generation failed: {str(e)}",
                "platform": platform
            }

    async def schedule_posts(
        self,
        posts: List[Dict[str, Any]],
        schedule: str = "optimal"
    ) -> Dict[str, Any]:
        """Schedule posts across platforms"""

        scheduled = []
        for post in posts:
            # Optimal posting times by platform
            optimal_times = {
                "instagram": "11:00 AM, 7:00 PM",
                "facebook": "1:00 PM, 3:00 PM",
                "tiktok": "6:00 PM, 9:00 PM"
            }

            post["scheduled_time"] = optimal_times.get(post.get("platform"), "12:00 PM")
            scheduled.append(post)

        return {
            "success": True,
            "posts_scheduled": len(scheduled),
            "schedule": schedule,
            "posts": scheduled
        }
```

## Usage Example

```python
from skills.brand_intelligence import BrandIntelligenceManager
from skills.social_media_automation import SocialMediaContentGenerator

# Initialize
brand_manager = BrandIntelligenceManager()
social_manager = SocialMediaContentGenerator(brand_manager)

# Generate Instagram product launch post
post = await social_manager.generate_post(
    platform="instagram",
    post_type="product_launch",
    context={
        "product_name": "Silk Evening Dress",
        "price": "$499",
        "key_features": ["handcrafted", "Italian silk", "limited edition"]
    }
)

print(f"Caption: {post['post_data']['caption']}")
print(f"Hashtags: {', '.join(post['post_data']['hashtags'])}")
```

Use this skill for consistent, brand-aligned social media presence across all platforms.
