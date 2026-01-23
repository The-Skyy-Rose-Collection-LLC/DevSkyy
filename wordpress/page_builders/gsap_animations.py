"""
GSAP Animation Module for SkyyRose WordPress Theme.

Provides 2025 interactive vibes with:
- GSAP ScrollTrigger animations
- View Transitions API integration
- Magnetic hover effects on CTAs
- Custom cursor with product preview
- Parallax scrolling (using 2.5D assets)
- Glassmorphism cards with backdrop-blur
- Micro-interactions on all interactive elements

Author: DevSkyy Platform Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class AnimationType(str, Enum):
    """GSAP animation types."""

    FADE_IN_UP = "fadeInUp"
    FADE_IN_DOWN = "fadeInDown"
    FADE_IN_LEFT = "fadeInLeft"
    FADE_IN_RIGHT = "fadeInRight"
    SCALE_IN = "scaleIn"
    ROTATE_IN = "rotateIn"
    BLUR_IN = "blurIn"
    STAGGER_FADE = "staggerFade"
    PARALLAX = "parallax"
    MAGNETIC = "magnetic"
    SPLIT_TEXT = "splitText"
    REVEAL = "reveal"
    MORPH = "morph"


class EasingType(str, Enum):
    """GSAP easing functions."""

    POWER1_OUT = "power1.out"
    POWER2_OUT = "power2.out"
    POWER3_OUT = "power3.out"
    POWER4_OUT = "power4.out"
    EXPO_OUT = "expo.out"
    CIRC_OUT = "circ.out"
    ELASTIC_OUT = "elastic.out(1, 0.5)"
    BACK_OUT = "back.out(1.7)"
    BOUNCE_OUT = "bounce.out"
    CUSTOM_LUXURY = "power2.inOut"


@dataclass
class GSAPConfig:
    """GSAP animation configuration."""

    # ScrollTrigger settings
    scroll_trigger_start: str = "top 80%"
    scroll_trigger_end: str = "bottom 20%"
    scrub: bool | float = False
    pin: bool = False
    markers: bool = False  # Debug only

    # Animation settings
    duration: float = 0.8
    stagger: float = 0.1
    delay: float = 0
    easing: EasingType = EasingType.POWER3_OUT

    # Parallax settings
    parallax_speed: float = 0.5
    parallax_direction: str = "y"

    # View Transitions
    view_transition_name: str | None = None
    view_transition_duration: float = 0.4


class GSAPAnimationBuilder:
    """
    Builds GSAP animation configurations for Elementor widgets.

    Generates JavaScript code and CSS classes for 2025 interactive effects.
    """

    def __init__(self, config: GSAPConfig | None = None) -> None:
        """Initialize animation builder."""
        self.config = config or GSAPConfig()

    def build_scroll_animation(
        self,
        animation_type: AnimationType,
        selector: str,
        *,
        custom_from: dict[str, Any] | None = None,
        custom_to: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Build ScrollTrigger animation configuration.

        Args:
            animation_type: Type of animation
            selector: CSS selector for target elements
            custom_from: Override from state
            custom_to: Override to state

        Returns:
            Animation configuration dict
        """
        # Default animation states
        animations = {
            AnimationType.FADE_IN_UP: {
                "from": {"opacity": 0, "y": 60},
                "to": {"opacity": 1, "y": 0},
            },
            AnimationType.FADE_IN_DOWN: {
                "from": {"opacity": 0, "y": -60},
                "to": {"opacity": 1, "y": 0},
            },
            AnimationType.FADE_IN_LEFT: {
                "from": {"opacity": 0, "x": -60},
                "to": {"opacity": 1, "x": 0},
            },
            AnimationType.FADE_IN_RIGHT: {
                "from": {"opacity": 0, "x": 60},
                "to": {"opacity": 1, "x": 0},
            },
            AnimationType.SCALE_IN: {
                "from": {"opacity": 0, "scale": 0.8},
                "to": {"opacity": 1, "scale": 1},
            },
            AnimationType.ROTATE_IN: {
                "from": {"opacity": 0, "rotation": -15, "scale": 0.9},
                "to": {"opacity": 1, "rotation": 0, "scale": 1},
            },
            AnimationType.BLUR_IN: {
                "from": {"opacity": 0, "filter": "blur(20px)"},
                "to": {"opacity": 1, "filter": "blur(0px)"},
            },
            AnimationType.REVEAL: {
                "from": {"clipPath": "inset(0 100% 0 0)"},
                "to": {"clipPath": "inset(0 0% 0 0)"},
            },
        }

        base_anim = animations.get(
            animation_type,
            {"from": {"opacity": 0}, "to": {"opacity": 1}},
        )

        return {
            "selector": selector,
            "type": animation_type.value,
            "from": custom_from or base_anim["from"],
            "to": custom_to or base_anim["to"],
            "scrollTrigger": {
                "trigger": selector,
                "start": self.config.scroll_trigger_start,
                "end": self.config.scroll_trigger_end,
                "scrub": self.config.scrub,
                "pin": self.config.pin,
                "markers": self.config.markers,
            },
            "duration": self.config.duration,
            "ease": self.config.easing.value,
            "delay": self.config.delay,
            "stagger": self.config.stagger if animation_type == AnimationType.STAGGER_FADE else 0,
        }

    def build_magnetic_button(self, selector: str) -> dict[str, Any]:
        """
        Build magnetic hover effect for CTA buttons.

        Args:
            selector: CSS selector for buttons

        Returns:
            Magnetic effect configuration
        """
        return {
            "selector": selector,
            "type": "magnetic",
            "strength": 0.3,
            "ease": "power2.out",
            "duration": 0.4,
            "lerp": 0.1,
            "onEnter": {"scale": 1.05},
            "onLeave": {"scale": 1},
        }

    def build_parallax(
        self,
        selector: str,
        speed: float | None = None,
        direction: str | None = None,
    ) -> dict[str, Any]:
        """
        Build parallax scrolling effect.

        Args:
            selector: CSS selector for parallax elements
            speed: Parallax speed multiplier
            direction: 'x' or 'y' direction

        Returns:
            Parallax configuration
        """
        return {
            "selector": selector,
            "type": "parallax",
            "speed": speed or self.config.parallax_speed,
            "direction": direction or self.config.parallax_direction,
            "scrub": True,
        }

    def build_split_text_animation(
        self,
        selector: str,
        split_type: str = "chars,words",
    ) -> dict[str, Any]:
        """
        Build split text reveal animation.

        Args:
            selector: CSS selector for text elements
            split_type: How to split text (chars, words, lines)

        Returns:
            Split text animation configuration
        """
        return {
            "selector": selector,
            "type": "splitText",
            "splitType": split_type,
            "from": {"opacity": 0, "y": 20, "rotateX": -90},
            "to": {"opacity": 1, "y": 0, "rotateX": 0},
            "stagger": 0.02,
            "duration": 0.8,
            "ease": "back.out(1.7)",
        }

    def build_custom_cursor(self) -> dict[str, Any]:
        """
        Build custom cursor with product preview.

        Returns:
            Custom cursor configuration
        """
        return {
            "enabled": True,
            "size": 24,
            "expandedSize": 80,
            "color": "rgba(183, 110, 121, 0.3)",
            "borderColor": "#B76E79",
            "borderWidth": 1,
            "blendMode": "difference",
            "lerp": 0.15,
            "hoverTargets": "[data-cursor-hover]",
            "productPreview": {
                "enabled": True,
                "size": 200,
                "offset": {"x": 20, "y": 20},
            },
        }

    def generate_gsap_script(
        self,
        animations: list[dict[str, Any]],
    ) -> str:
        """
        Generate GSAP initialization script.

        Args:
            animations: List of animation configurations

        Returns:
            JavaScript code string
        """
        import json

        return f"""
<script>
// SkyyRose GSAP Animations - 2025 Interactive Vibes
(function() {{
  'use strict';

  // Wait for GSAP and ScrollTrigger
  if (typeof gsap === 'undefined') {{
    console.warn('GSAP not loaded');
    return;
  }}

  gsap.registerPlugin(ScrollTrigger);

  const animations = {json.dumps(animations, indent=2)};

  // Initialize scroll animations
  animations.forEach(anim => {{
    if (anim.type === 'parallax') {{
      gsap.to(anim.selector, {{
        y: () => anim.speed * 100 + '%',
        ease: 'none',
        scrollTrigger: {{
          trigger: anim.selector,
          start: 'top bottom',
          end: 'bottom top',
          scrub: anim.scrub
        }}
      }});
    }} else if (anim.type === 'magnetic') {{
      initMagneticButtons(anim);
    }} else if (anim.type === 'splitText') {{
      initSplitTextAnimation(anim);
    }} else {{
      gsap.from(anim.selector, {{
        ...anim.from,
        duration: anim.duration,
        ease: anim.ease,
        delay: anim.delay,
        stagger: anim.stagger,
        scrollTrigger: anim.scrollTrigger
      }});
    }}
  }});

  // Magnetic button effect
  function initMagneticButtons(config) {{
    const buttons = document.querySelectorAll(config.selector);

    buttons.forEach(button => {{
      button.addEventListener('mousemove', (e) => {{
        const rect = button.getBoundingClientRect();
        const x = e.clientX - rect.left - rect.width / 2;
        const y = e.clientY - rect.top - rect.height / 2;

        gsap.to(button, {{
          x: x * config.strength,
          y: y * config.strength,
          duration: config.duration,
          ease: config.ease
        }});
      }});

      button.addEventListener('mouseleave', () => {{
        gsap.to(button, {{
          x: 0,
          y: 0,
          duration: config.duration,
          ease: config.ease
        }});
      }});
    }});
  }}

  // Split text animation (requires SplitType or similar)
  function initSplitTextAnimation(config) {{
    if (typeof SplitType === 'undefined') {{
      // Fallback to regular animation
      gsap.from(config.selector, {{
        opacity: 0,
        y: 30,
        duration: config.duration,
        ease: config.ease,
        scrollTrigger: {{
          trigger: config.selector,
          start: 'top 80%'
        }}
      }});
      return;
    }}

    const elements = document.querySelectorAll(config.selector);
    elements.forEach(el => {{
      const split = new SplitType(el, {{ types: config.splitType }});
      const chars = split.chars || split.words || split.lines;

      gsap.from(chars, {{
        ...config.from,
        duration: config.duration,
        ease: config.ease,
        stagger: config.stagger,
        scrollTrigger: {{
          trigger: el,
          start: 'top 80%'
        }}
      }});
    }});
  }}

  console.log('SkyyRose GSAP initialized with', animations.length, 'animations');
}})();
</script>
"""

    def generate_view_transitions_css(self) -> str:
        """
        Generate View Transitions API CSS.

        Returns:
            CSS code string for view transitions
        """
        return """
<style>
/* View Transitions API - 2025 Navigation */
@view-transition {
  navigation: auto;
}

::view-transition-old(root),
::view-transition-new(root) {
  animation-duration: 0.4s;
  animation-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
}

::view-transition-old(root) {
  animation-name: fade-out;
}

::view-transition-new(root) {
  animation-name: fade-in;
}

@keyframes fade-out {
  from { opacity: 1; transform: translateY(0); }
  to { opacity: 0; transform: translateY(-20px); }
}

@keyframes fade-in {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Named view transitions for elements */
[data-view-transition="hero"] {
  view-transition-name: hero;
}

[data-view-transition="product"] {
  view-transition-name: product;
}

[data-view-transition="card"] {
  view-transition-name: card;
}

/* Hero transition */
::view-transition-old(hero),
::view-transition-new(hero) {
  animation-duration: 0.6s;
}

::view-transition-old(hero) {
  animation-name: hero-exit;
}

::view-transition-new(hero) {
  animation-name: hero-enter;
}

@keyframes hero-exit {
  from { opacity: 1; transform: scale(1); }
  to { opacity: 0; transform: scale(1.1); }
}

@keyframes hero-enter {
  from { opacity: 0; transform: scale(0.9); }
  to { opacity: 1; transform: scale(1); }
}
</style>
"""

    def generate_glassmorphism_css(self) -> str:
        """
        Generate glassmorphism card styles.

        Returns:
            CSS code string for glassmorphism effects
        """
        return """
<style>
/* Glassmorphism Cards - 2025 */
.glass-card {
  background: rgba(26, 26, 26, 0.7);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.3),
    inset 0 0 0 1px rgba(255, 255, 255, 0.05);
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.glass-card:hover {
  background: rgba(26, 26, 26, 0.8);
  border-color: rgba(183, 110, 121, 0.3);
  box-shadow:
    0 12px 48px rgba(0, 0, 0, 0.4),
    0 0 0 1px rgba(183, 110, 121, 0.2),
    inset 0 0 0 1px rgba(255, 255, 255, 0.1);
  transform: translateY(-4px);
}

/* Glassmorphism Hero Overlay */
.glass-hero {
  background: linear-gradient(
    135deg,
    rgba(26, 26, 26, 0.8) 0%,
    rgba(26, 26, 26, 0.4) 100%
  );
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

/* Glassmorphism Button */
.glass-button {
  background: rgba(183, 110, 121, 0.2);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(183, 110, 121, 0.4);
  color: #fff;
  padding: 16px 32px;
  border-radius: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  transition: all 0.3s ease;
  cursor: pointer;
}

.glass-button:hover {
  background: rgba(183, 110, 121, 0.4);
  border-color: rgba(183, 110, 121, 0.8);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(183, 110, 121, 0.3);
}
</style>
"""

    def generate_custom_cursor_script(self) -> str:
        """
        Generate custom cursor JavaScript.

        Returns:
            JavaScript code for custom cursor
        """
        config = self.build_custom_cursor()
        import json

        return f"""
<script>
// SkyyRose Custom Cursor - 2025
(function() {{
  'use strict';

  const config = {json.dumps(config, indent=2)};
  if (!config.enabled) return;

  // Create cursor elements
  const cursor = document.createElement('div');
  cursor.className = 'skyyrose-cursor';
  document.body.appendChild(cursor);

  const cursorFollower = document.createElement('div');
  cursorFollower.className = 'skyyrose-cursor-follower';
  document.body.appendChild(cursorFollower);

  let mouseX = 0, mouseY = 0;
  let cursorX = 0, cursorY = 0;
  let followerX = 0, followerY = 0;

  document.addEventListener('mousemove', (e) => {{
    mouseX = e.clientX;
    mouseY = e.clientY;
  }});

  // Lerp animation
  function animate() {{
    cursorX += (mouseX - cursorX) * 0.5;
    cursorY += (mouseY - cursorY) * 0.5;
    followerX += (mouseX - followerX) * config.lerp;
    followerY += (mouseY - followerY) * config.lerp;

    cursor.style.transform = `translate(${{cursorX - config.size/2}}px, ${{cursorY - config.size/2}}px)`;
    cursorFollower.style.transform = `translate(${{followerX - config.expandedSize/2}}px, ${{followerY - config.expandedSize/2}}px)`;

    requestAnimationFrame(animate);
  }}
  animate();

  // Hover interactions
  const hoverTargets = document.querySelectorAll(config.hoverTargets);
  hoverTargets.forEach(target => {{
    target.addEventListener('mouseenter', () => {{
      cursor.classList.add('cursor-hover');
      cursorFollower.classList.add('cursor-hover');

      // Product preview
      if (config.productPreview.enabled && target.dataset.productImage) {{
        showProductPreview(target.dataset.productImage);
      }}
    }});

    target.addEventListener('mouseleave', () => {{
      cursor.classList.remove('cursor-hover');
      cursorFollower.classList.remove('cursor-hover');
      hideProductPreview();
    }});
  }});

  // Product preview (floating image)
  let previewEl = null;

  function showProductPreview(imageUrl) {{
    if (!previewEl) {{
      previewEl = document.createElement('div');
      previewEl.className = 'skyyrose-product-preview';
      document.body.appendChild(previewEl);
    }}

    previewEl.style.backgroundImage = `url(${{imageUrl}})`;
    previewEl.classList.add('visible');
  }}

  function hideProductPreview() {{
    if (previewEl) {{
      previewEl.classList.remove('visible');
    }}
  }}
}})();
</script>

<style>
/* Custom Cursor Styles */
.skyyrose-cursor {{
  position: fixed;
  width: 24px;
  height: 24px;
  background: rgba(183, 110, 121, 0.3);
  border: 1px solid #B76E79;
  border-radius: 50%;
  pointer-events: none;
  z-index: 9999;
  mix-blend-mode: difference;
  transition: width 0.3s, height 0.3s, background 0.3s;
}}

.skyyrose-cursor-follower {{
  position: fixed;
  width: 80px;
  height: 80px;
  border: 1px solid rgba(183, 110, 121, 0.3);
  border-radius: 50%;
  pointer-events: none;
  z-index: 9998;
  transition: width 0.3s, height 0.3s, border-color 0.3s;
}}

.skyyrose-cursor.cursor-hover {{
  width: 40px;
  height: 40px;
  background: rgba(183, 110, 121, 0.6);
}}

.skyyrose-cursor-follower.cursor-hover {{
  width: 120px;
  height: 120px;
  border-color: rgba(183, 110, 121, 0.6);
}}

.skyyrose-product-preview {{
  position: fixed;
  width: 200px;
  height: 200px;
  background-size: cover;
  background-position: center;
  border-radius: 12px;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.5);
  pointer-events: none;
  z-index: 9997;
  opacity: 0;
  transform: scale(0.8);
  transition: opacity 0.3s, transform 0.3s;
}}

.skyyrose-product-preview.visible {{
  opacity: 1;
  transform: scale(1);
}}

/* Hide default cursor on desktop */
@media (hover: hover) and (pointer: fine) {{
  body {{
    cursor: none;
  }}

  a, button, [data-cursor-hover] {{
    cursor: none;
  }}
}}

/* Disable custom cursor on touch devices */
@media (hover: none) {{
  .skyyrose-cursor,
  .skyyrose-cursor-follower,
  .skyyrose-product-preview {{
    display: none;
  }}
}}
</style>
"""


def generate_gsap_enqueue_script() -> str:
    """
    Generate WordPress script to enqueue GSAP libraries.

    Returns:
        PHP code for functions.php
    """
    return """
<?php
/**
 * Enqueue GSAP libraries for SkyyRose 2025 Interactive Vibes
 */
function skyyrose_enqueue_gsap() {
    // GSAP Core
    wp_enqueue_script(
        'gsap-core',
        'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js',
        array(),
        '3.12.5',
        true
    );

    // ScrollTrigger Plugin
    wp_enqueue_script(
        'gsap-scrolltrigger',
        'https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js',
        array('gsap-core'),
        '3.12.5',
        true
    );

    // SplitType for text animations (optional)
    wp_enqueue_script(
        'splittype',
        'https://unpkg.com/split-type@0.3.4/umd/index.min.js',
        array(),
        '0.3.4',
        true
    );

    // SkyyRose animations
    wp_enqueue_script(
        'skyyrose-animations',
        get_stylesheet_directory_uri() . '/assets/js/skyyrose-animations.js',
        array('gsap-core', 'gsap-scrolltrigger'),
        '1.0.0',
        true
    );
}
add_action('wp_enqueue_scripts', 'skyyrose_enqueue_gsap');
?>
"""


__all__ = [
    "AnimationType",
    "EasingType",
    "GSAPConfig",
    "GSAPAnimationBuilder",
    "generate_gsap_enqueue_script",
]
