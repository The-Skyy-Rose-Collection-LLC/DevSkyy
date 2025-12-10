"""
Elementor Template Generator
============================

Generate Elementor Pro JSON templates for SkyyRose brand.

Templates:
- Homepage with hero, collections, testimonials
- Collection landing pages (BLACK ROSE, LOVE HURTS, SIGNATURE)
- Product page components
- About page
- Blog/Journal page

References:
- Elementor JSON Structure: https://developers.elementor.com/
- SkyyRose Brand: Oakland luxury streetwear, "Where Love Meets Luxury"
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


# =============================================================================
# Enums
# =============================================================================

class TemplateType(str, Enum):
    """Elementor template types"""
    PAGE = "page"
    SECTION = "section"
    HEADER = "header"
    FOOTER = "footer"
    SINGLE = "single"
    ARCHIVE = "archive"
    POPUP = "popup"
    LOOP_ITEM = "loop-item"


class WidgetType(str, Enum):
    """Common Elementor widget types"""
    HEADING = "heading"
    TEXT_EDITOR = "text-editor"
    IMAGE = "image"
    VIDEO = "video"
    BUTTON = "button"
    ICON = "icon"
    DIVIDER = "divider"
    SPACER = "spacer"
    IMAGE_BOX = "image-box"
    ICON_BOX = "icon-box"
    GALLERY = "gallery"
    CAROUSEL = "media-carousel"
    TESTIMONIAL = "testimonial"
    TABS = "tabs"
    ACCORDION = "accordion"
    FORM = "form"
    POSTS = "posts"
    PRODUCTS = "woocommerce-products"
    PRODUCT_IMAGES = "wc-product-images"
    ADD_TO_CART = "wc-add-to-cart"
    MENU = "nav-menu"
    SOCIAL = "social-icons"
    COUNTDOWN = "countdown"
    PROGRESS = "progress"
    ANIMATED_HEADLINE = "animated-headline"
    CALL_TO_ACTION = "call-to-action"
    FLIP_BOX = "flip-box"


# =============================================================================
# SkyyRose Brand Constants
# =============================================================================

SKYYROSE_BRAND = {
    "name": "SkyyRose",
    "tagline": "Where Love Meets Luxury",
    "location": "Oakland, California",
    "colors": {
        "primary": "#D4AF37",      # Rose Gold
        "secondary": "#0D0D0D",    # Obsidian Black
        "accent": "#8B7355",       # Warm Bronze
        "light": "#F5F5F0",        # Ivory
        "text": "#1A1A1A",
        "text_light": "#666666",
    },
    "fonts": {
        "heading": "Playfair Display",
        "body": "Montserrat",
    },
    "collections": {
        "BLACK_ROSE": {
            "name": "Black Rose",
            "tagline": "Limited Edition Dark Elegance",
            "description": "Numbered limited editions crafted for those who appreciate exclusivity and refined darkness.",
            "color": "#1A1A1A",
        },
        "LOVE_HURTS": {
            "name": "Love Hurts",
            "tagline": "Emotional Expression Pieces",
            "description": "Honoring the founder's family name, each piece tells a story of love, loss, and resilience.",
            "color": "#8B0000",
        },
        "SIGNATURE": {
            "name": "Signature",
            "tagline": "Foundation Wardrobe Essentials",
            "description": "Timeless pieces that form the foundation of elevated everyday style.",
            "color": "#D4AF37",
        },
    },
}


# =============================================================================
# Element Builders
# =============================================================================

@dataclass
class ElementorElement:
    """Base Elementor element"""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:7])
    elType: str = "widget"
    widgetType: str = ""
    settings: Dict[str, Any] = field(default_factory=dict)
    elements: List["ElementorElement"] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        result = {
            "id": self.id,
            "elType": self.elType,
            "settings": self.settings,
            "elements": [e.to_dict() for e in self.elements],
        }
        if self.widgetType:
            result["widgetType"] = self.widgetType
        return result


@dataclass
class ElementorWidget(ElementorElement):
    """Elementor widget"""
    elType: str = "widget"
    
    @classmethod
    def heading(
        cls,
        title: str,
        tag: str = "h2",
        align: str = "center",
        color: str = None,
        size: str = None,
    ) -> "ElementorWidget":
        """Create heading widget"""
        settings = {
            "title": title,
            "header_size": tag,
            "align": align,
            "typography_typography": "custom",
            "typography_font_family": SKYYROSE_BRAND["fonts"]["heading"],
        }
        if color:
            settings["title_color"] = color
        if size:
            settings["typography_font_size"] = {"unit": "px", "size": int(size)}
        
        return cls(widgetType="heading", settings=settings)
    
    @classmethod
    def text(
        cls,
        content: str,
        align: str = "center",
        color: str = None,
    ) -> "ElementorWidget":
        """Create text editor widget"""
        settings = {
            "editor": content,
            "align": align,
            "typography_typography": "custom",
            "typography_font_family": SKYYROSE_BRAND["fonts"]["body"],
        }
        if color:
            settings["text_color"] = color
        
        return cls(widgetType="text-editor", settings=settings)
    
    @classmethod
    def button(
        cls,
        text: str,
        link: str = "#",
        style: str = "default",
        size: str = "md",
        align: str = "center",
        bg_color: str = None,
        text_color: str = None,
    ) -> "ElementorWidget":
        """Create button widget"""
        settings = {
            "text": text,
            "link": {"url": link, "is_external": False, "nofollow": False},
            "button_type": style,
            "size": size,
            "align": align,
        }
        if bg_color:
            settings["background_color"] = bg_color
        if text_color:
            settings["button_text_color"] = text_color
        
        return cls(widgetType="button", settings=settings)
    
    @classmethod
    def image(
        cls,
        url: str,
        alt: str = "",
        size: str = "full",
        align: str = "center",
        link: str = None,
    ) -> "ElementorWidget":
        """Create image widget"""
        settings = {
            "image": {"url": url, "alt": alt},
            "image_size": size,
            "align": align,
        }
        if link:
            settings["link"] = {"url": link}
        
        return cls(widgetType="image", settings=settings)
    
    @classmethod
    def spacer(cls, height: int = 50) -> "ElementorWidget":
        """Create spacer widget"""
        return cls(
            widgetType="spacer",
            settings={"space": {"unit": "px", "size": height}}
        )
    
    @classmethod
    def divider(cls, style: str = "solid", color: str = None) -> "ElementorWidget":
        """Create divider widget"""
        settings = {"style": style}
        if color:
            settings["color"] = color
        return cls(widgetType="divider", settings=settings)
    
    @classmethod
    def products(
        cls,
        columns: int = 4,
        rows: int = 2,
        category: List[int] = None,
        orderby: str = "date",
    ) -> "ElementorWidget":
        """Create WooCommerce products widget"""
        settings = {
            "columns": columns,
            "rows": rows,
            "orderby": orderby,
            "paginate": "yes",
        }
        if category:
            settings["query_include"] = "terms"
            settings["query_include_term_ids"] = category
        
        return cls(widgetType="woocommerce-products", settings=settings)
    
    @classmethod
    def icon_box(
        cls,
        title: str,
        description: str,
        icon: str = "fas fa-star",
        position: str = "top",
    ) -> "ElementorWidget":
        """Create icon box widget"""
        return cls(
            widgetType="icon-box",
            settings={
                "title_text": title,
                "description_text": description,
                "selected_icon": {"value": icon, "library": "fa-solid"},
                "position": position,
            }
        )
    
    @classmethod
    def testimonial(
        cls,
        content: str,
        name: str,
        title: str = "",
        image_url: str = None,
    ) -> "ElementorWidget":
        """Create testimonial widget"""
        settings = {
            "testimonial_content": content,
            "testimonial_name": name,
            "testimonial_job": title,
        }
        if image_url:
            settings["testimonial_image"] = {"url": image_url}
        
        return cls(widgetType="testimonial", settings=settings)
    
    @classmethod
    def social_icons(
        cls,
        icons: List[Dict[str, str]] = None,
    ) -> "ElementorWidget":
        """Create social icons widget"""
        default_icons = [
            {"social_icon": {"value": "fab fa-instagram"}, "link": {"url": "https://instagram.com/skyyrose"}},
            {"social_icon": {"value": "fab fa-tiktok"}, "link": {"url": "https://tiktok.com/@skyyrose"}},
            {"social_icon": {"value": "fab fa-twitter"}, "link": {"url": "https://twitter.com/skyyrose"}},
        ]
        
        return cls(
            widgetType="social-icons",
            settings={"social_icon_list": icons or default_icons}
        )


@dataclass
class ElementorColumn(ElementorElement):
    """Elementor column"""
    elType: str = "column"
    _column_size: int = 100
    
    def to_dict(self) -> dict:
        result = super().to_dict()
        result["settings"]["_column_size"] = self._column_size
        return result


@dataclass 
class ElementorSection(ElementorElement):
    """Elementor section"""
    elType: str = "section"
    
    @classmethod
    def create(
        cls,
        widgets: List[ElementorWidget],
        columns: int = 1,
        layout: str = "boxed",
        bg_color: str = None,
        bg_image: str = None,
        padding: Dict[str, int] = None,
        min_height: int = None,
        content_position: str = "middle",
    ) -> "ElementorSection":
        """Create section with widgets distributed across columns"""
        settings = {
            "layout": layout,
            "content_position": content_position,
        }
        
        if bg_color:
            settings["background_background"] = "classic"
            settings["background_color"] = bg_color
        
        if bg_image:
            settings["background_background"] = "classic"
            settings["background_image"] = {"url": bg_image}
            settings["background_position"] = "center center"
            settings["background_size"] = "cover"
        
        if padding:
            settings["padding"] = {
                "unit": "px",
                "top": padding.get("top", 50),
                "bottom": padding.get("bottom", 50),
                "left": padding.get("left", 0),
                "right": padding.get("right", 0),
            }
        
        if min_height:
            settings["min_height"] = {"unit": "vh", "size": min_height}
        
        # Create columns
        column_size = 100 // columns
        column_elements = []
        
        for i in range(columns):
            col = ElementorColumn(_column_size=column_size)
            # Distribute widgets to columns
            widgets_for_col = widgets[i::columns] if widgets else []
            col.elements = widgets_for_col
            column_elements.append(col)
        
        section = cls(settings=settings)
        section.elements = column_elements
        return section


# =============================================================================
# Template Generator
# =============================================================================

class ElementorTemplateGenerator:
    """
    Generate Elementor Pro templates for SkyyRose
    
    Usage:
        generator = ElementorTemplateGenerator()
        
        # Generate homepage
        homepage = generator.homepage()
        
        # Generate collection page
        black_rose = generator.collection_page("BLACK_ROSE")
        
        # Export to JSON
        json_data = generator.export(homepage)
    """
    
    def __init__(self, brand: dict = None):
        self.brand = brand or SKYYROSE_BRAND
    
    def _create_template(
        self,
        title: str,
        template_type: TemplateType,
        elements: List[ElementorSection],
    ) -> dict:
        """Create template structure"""
        return {
            "title": title,
            "type": template_type.value,
            "version": "0.4",
            "metadata": {
                "title": title,
                "type": template_type.value,
                "created_at": datetime.utcnow().isoformat(),
                "generator": "DevSkyy ElementorTemplateGenerator",
                "brand": "SkyyRose",
            },
            "content": [section.to_dict() for section in elements],
        }
    
    # -------------------------------------------------------------------------
    # Homepage
    # -------------------------------------------------------------------------
    
    def homepage(self) -> dict:
        """Generate SkyyRose homepage template"""
        sections = []
        
        # Hero Section
        hero = ElementorSection.create(
            widgets=[
                ElementorWidget.heading(
                    "SkyyRose",
                    tag="h1",
                    color=self.brand["colors"]["primary"],
                    size="72",
                ),
                ElementorWidget.text(
                    f"<p style='font-size: 24px;'>{self.brand['tagline']}</p>",
                    color=self.brand["colors"]["light"],
                ),
                ElementorWidget.text(
                    f"<p>Oakland, California</p>",
                    color=self.brand["colors"]["text_light"],
                ),
                ElementorWidget.spacer(30),
                ElementorWidget.button(
                    "Shop Collections",
                    link="/collections",
                    size="lg",
                    bg_color=self.brand["colors"]["primary"],
                    text_color=self.brand["colors"]["secondary"],
                ),
            ],
            bg_color=self.brand["colors"]["secondary"],
            min_height=100,
            padding={"top": 150, "bottom": 150},
        )
        sections.append(hero)
        
        # Collections Grid
        collections_intro = ElementorSection.create(
            widgets=[
                ElementorWidget.heading("Our Collections", tag="h2"),
                ElementorWidget.text("<p>Three distinct expressions of luxury streetwear</p>"),
                ElementorWidget.spacer(30),
            ],
            padding={"top": 80, "bottom": 20},
        )
        sections.append(collections_intro)
        
        # Collection Cards
        collection_widgets = []
        for key, collection in self.brand["collections"].items():
            collection_widgets.extend([
                ElementorWidget.heading(collection["name"], tag="h3", size="28"),
                ElementorWidget.text(f"<p>{collection['tagline']}</p>"),
                ElementorWidget.button(
                    "Explore",
                    link=f"/collections/{collection['name'].lower().replace(' ', '-')}",
                    size="sm",
                ),
            ])
        
        collections_section = ElementorSection.create(
            widgets=collection_widgets,
            columns=3,
            padding={"top": 20, "bottom": 80},
        )
        sections.append(collections_section)
        
        # Featured Products
        featured = ElementorSection.create(
            widgets=[
                ElementorWidget.heading("Featured Pieces", tag="h2"),
                ElementorWidget.spacer(20),
                ElementorWidget.products(columns=4, rows=1, orderby="popularity"),
            ],
            bg_color=self.brand["colors"]["light"],
            padding={"top": 80, "bottom": 80},
        )
        sections.append(featured)
        
        # Brand Story
        story = ElementorSection.create(
            widgets=[
                ElementorWidget.heading("The Story", tag="h2"),
                ElementorWidget.text(
                    "<p>Born in Oakland, SkyyRose emerges from a vision of luxury "
                    "that speaks to the soul. Every piece is crafted with intention, "
                    "designed for those who understand that true style transcends trends.</p>"
                    "<p>Where Love Meets Luxury isn't just a tagline—it's our promise.</p>"
                ),
                ElementorWidget.button("About Us", link="/about", size="md"),
            ],
            padding={"top": 100, "bottom": 100},
        )
        sections.append(story)
        
        # Values
        values = ElementorSection.create(
            widgets=[
                ElementorWidget.icon_box(
                    "Craftsmanship",
                    "Every stitch tells a story of dedication",
                    "fas fa-gem",
                ),
                ElementorWidget.icon_box(
                    "Exclusivity",
                    "Limited editions for the discerning few",
                    "fas fa-crown",
                ),
                ElementorWidget.icon_box(
                    "Oakland Roots",
                    "Bay Area heritage in every design",
                    "fas fa-city",
                ),
            ],
            columns=3,
            bg_color=self.brand["colors"]["secondary"],
            padding={"top": 60, "bottom": 60},
        )
        sections.append(values)
        
        # Newsletter
        newsletter = ElementorSection.create(
            widgets=[
                ElementorWidget.heading("Join the Rose Garden", tag="h3"),
                ElementorWidget.text("<p>Be the first to know about new drops and exclusive offers</p>"),
                ElementorWidget.spacer(20),
            ],
            bg_color=self.brand["colors"]["light"],
            padding={"top": 60, "bottom": 60},
        )
        sections.append(newsletter)
        
        return self._create_template(
            title="SkyyRose Homepage",
            template_type=TemplateType.PAGE,
            elements=sections,
        )
    
    # -------------------------------------------------------------------------
    # Collection Pages
    # -------------------------------------------------------------------------
    
    def collection_page(self, collection_key: str) -> dict:
        """Generate collection landing page"""
        collection = self.brand["collections"].get(collection_key.upper())
        
        if not collection:
            raise ValueError(f"Unknown collection: {collection_key}")
        
        sections = []
        
        # Hero
        hero = ElementorSection.create(
            widgets=[
                ElementorWidget.heading(
                    collection["name"],
                    tag="h1",
                    color=self.brand["colors"]["primary"],
                    size="64",
                ),
                ElementorWidget.text(
                    f"<p style='font-size: 20px;'>{collection['tagline']}</p>",
                    color=self.brand["colors"]["light"],
                ),
                ElementorWidget.divider(color=self.brand["colors"]["primary"]),
                ElementorWidget.text(
                    f"<p>{collection['description']}</p>",
                    color=self.brand["colors"]["text_light"],
                ),
            ],
            bg_color=collection["color"],
            min_height=60,
            padding={"top": 120, "bottom": 120},
        )
        sections.append(hero)
        
        # Products
        products = ElementorSection.create(
            widgets=[
                ElementorWidget.heading("The Collection", tag="h2"),
                ElementorWidget.spacer(30),
                ElementorWidget.products(columns=3, rows=4),
            ],
            padding={"top": 60, "bottom": 80},
        )
        sections.append(products)
        
        # Story
        story = ElementorSection.create(
            widgets=[
                ElementorWidget.heading("The Vision", tag="h3"),
                ElementorWidget.text(
                    f"<p>{collection['description']}</p>"
                    "<p>Each piece in this collection represents our commitment "
                    "to excellence and our Oakland heritage.</p>"
                ),
            ],
            bg_color=self.brand["colors"]["light"],
            padding={"top": 80, "bottom": 80},
        )
        sections.append(story)
        
        # CTA
        cta = ElementorSection.create(
            widgets=[
                ElementorWidget.heading("Explore More", tag="h3"),
                ElementorWidget.button(
                    "View All Collections",
                    link="/collections",
                    bg_color=self.brand["colors"]["primary"],
                ),
            ],
            bg_color=self.brand["colors"]["secondary"],
            padding={"top": 60, "bottom": 60},
        )
        sections.append(cta)
        
        return self._create_template(
            title=f"SkyyRose - {collection['name']} Collection",
            template_type=TemplateType.PAGE,
            elements=sections,
        )
    
    def black_rose_page(self) -> dict:
        """Generate BLACK ROSE collection page"""
        return self.collection_page("BLACK_ROSE")
    
    def love_hurts_page(self) -> dict:
        """Generate LOVE HURTS collection page"""
        return self.collection_page("LOVE_HURTS")
    
    def signature_page(self) -> dict:
        """Generate SIGNATURE collection page"""
        return self.collection_page("SIGNATURE")
    
    # -------------------------------------------------------------------------
    # About Page
    # -------------------------------------------------------------------------
    
    def about_page(self) -> dict:
        """Generate About page template"""
        sections = []
        
        # Hero
        hero = ElementorSection.create(
            widgets=[
                ElementorWidget.heading(
                    "About SkyyRose",
                    tag="h1",
                    size="56",
                ),
                ElementorWidget.text(
                    "<p>The story behind the brand</p>",
                ),
            ],
            bg_color=self.brand["colors"]["secondary"],
            padding={"top": 100, "bottom": 100},
        )
        sections.append(hero)
        
        # Story
        story = ElementorSection.create(
            widgets=[
                ElementorWidget.heading("Our Story", tag="h2"),
                ElementorWidget.text(
                    "<p>SkyyRose was born from a vision of creating luxury streetwear "
                    "that speaks to the soul. Founded in Oakland, California, our brand "
                    "represents the intersection of street culture and high fashion.</p>"
                    "<p>The name 'SkyyRose' embodies our philosophy: reaching for the sky "
                    "while staying grounded in beauty and elegance. Each piece we create "
                    "is a testament to our commitment to quality, exclusivity, and authentic expression.</p>"
                ),
            ],
            padding={"top": 80, "bottom": 40},
        )
        sections.append(story)
        
        # Values
        values = ElementorSection.create(
            widgets=[
                ElementorWidget.heading("Our Values", tag="h2"),
                ElementorWidget.icon_box(
                    "Quality First",
                    "Premium materials and expert craftsmanship in every piece",
                    "fas fa-star",
                ),
                ElementorWidget.icon_box(
                    "Limited Production",
                    "Small batches ensure exclusivity and attention to detail",
                    "fas fa-gem",
                ),
                ElementorWidget.icon_box(
                    "Oakland Pride",
                    "Rooted in the Bay Area, inspired by its culture and energy",
                    "fas fa-heart",
                ),
            ],
            columns=3,
            bg_color=self.brand["colors"]["light"],
            padding={"top": 60, "bottom": 60},
        )
        sections.append(values)
        
        # Mission
        mission = ElementorSection.create(
            widgets=[
                ElementorWidget.heading("Our Mission", tag="h2"),
                ElementorWidget.text(
                    "<p style='font-size: 24px; font-style: italic;'>"
                    "\"Where Love Meets Luxury\"</p>"
                    "<p>We create clothing that makes you feel powerful, beautiful, "
                    "and authentically yourself. Every design tells a story, every "
                    "piece is meant to be treasured.</p>"
                ),
                ElementorWidget.button("Shop Now", link="/shop", size="lg"),
            ],
            padding={"top": 80, "bottom": 100},
        )
        sections.append(mission)
        
        return self._create_template(
            title="About SkyyRose",
            template_type=TemplateType.PAGE,
            elements=sections,
        )
    
    # -------------------------------------------------------------------------
    # Blog Page
    # -------------------------------------------------------------------------
    
    def blog_page(self) -> dict:
        """Generate Blog/Journal page template"""
        sections = []
        
        # Hero
        hero = ElementorSection.create(
            widgets=[
                ElementorWidget.heading(
                    "The Journal",
                    tag="h1",
                    size="56",
                ),
                ElementorWidget.text(
                    "<p>Stories, style guides, and behind-the-scenes</p>",
                ),
            ],
            bg_color=self.brand["colors"]["secondary"],
            padding={"top": 80, "bottom": 80},
        )
        sections.append(hero)
        
        # Posts grid
        # Note: This would use Elementor's posts widget in practice
        posts = ElementorSection.create(
            widgets=[
                ElementorWidget.heading("Latest Posts", tag="h2"),
                ElementorWidget.spacer(30),
            ],
            padding={"top": 60, "bottom": 80},
        )
        sections.append(posts)
        
        # Newsletter
        newsletter = ElementorSection.create(
            widgets=[
                ElementorWidget.heading("Stay Connected", tag="h3"),
                ElementorWidget.text("<p>Subscribe for style updates and exclusive content</p>"),
            ],
            bg_color=self.brand["colors"]["light"],
            padding={"top": 60, "bottom": 60},
        )
        sections.append(newsletter)
        
        return self._create_template(
            title="SkyyRose Journal",
            template_type=TemplateType.PAGE,
            elements=sections,
        )
    
    # -------------------------------------------------------------------------
    # Header & Footer
    # -------------------------------------------------------------------------
    
    def header(self) -> dict:
        """Generate header template"""
        sections = []
        
        header = ElementorSection.create(
            widgets=[
                ElementorWidget.heading(
                    "SkyyRose",
                    tag="h1",
                    size="28",
                    color=self.brand["colors"]["primary"],
                ),
            ],
            bg_color=self.brand["colors"]["secondary"],
            padding={"top": 15, "bottom": 15},
        )
        sections.append(header)
        
        return self._create_template(
            title="SkyyRose Header",
            template_type=TemplateType.HEADER,
            elements=sections,
        )
    
    def footer(self) -> dict:
        """Generate footer template"""
        sections = []
        
        footer = ElementorSection.create(
            widgets=[
                ElementorWidget.heading(
                    "SkyyRose",
                    tag="h4",
                    color=self.brand["colors"]["primary"],
                ),
                ElementorWidget.text(
                    f"<p>{self.brand['tagline']}</p>"
                    f"<p>{self.brand['location']}</p>",
                    color=self.brand["colors"]["text_light"],
                ),
                ElementorWidget.social_icons(),
                ElementorWidget.text(
                    f"<p>© {datetime.now().year} SkyyRose. All rights reserved.</p>",
                    color=self.brand["colors"]["text_light"],
                ),
            ],
            bg_color=self.brand["colors"]["secondary"],
            padding={"top": 60, "bottom": 40},
        )
        sections.append(footer)
        
        return self._create_template(
            title="SkyyRose Footer",
            template_type=TemplateType.FOOTER,
            elements=sections,
        )
    
    # -------------------------------------------------------------------------
    # Export
    # -------------------------------------------------------------------------
    
    def export(self, template: dict, pretty: bool = True) -> str:
        """Export template to JSON string"""
        if pretty:
            return json.dumps(template, indent=2)
        return json.dumps(template)
    
    def export_all(self) -> Dict[str, dict]:
        """Generate all templates"""
        return {
            "homepage": self.homepage(),
            "black_rose": self.black_rose_page(),
            "love_hurts": self.love_hurts_page(),
            "signature": self.signature_page(),
            "about": self.about_page(),
            "blog": self.blog_page(),
            "header": self.header(),
            "footer": self.footer(),
        }
    
    def save_all(self, output_dir: str = "./templates/elementor"):
        """Save all templates to files"""
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        templates = self.export_all()
        
        for name, template in templates.items():
            filepath = os.path.join(output_dir, f"{name}.json")
            with open(filepath, "w") as f:
                f.write(self.export(template))
            logger.info(f"Saved template: {filepath}")
        
        return list(templates.keys())
