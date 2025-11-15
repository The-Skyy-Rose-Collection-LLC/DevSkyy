"""
Enhanced WordPress Theme Templates
Additional luxury templates for theme builder
"""

THEME_TEMPLATES = {
    "luxury_minimalist": {
        "name": "Luxury Minimalist",
        "colors": {"primary": "#000000", "secondary": "#FFFFFF", "accent": "#C9A962"},
        "fonts": {"heading": "Cormorant Garamond", "body": "Montserrat"},
        "style": "clean modern with gold accents",
    },
    "vintage_elegance": {
        "name": "Vintage Elegance",
        "colors": {"primary": "#8B4513", "secondary": "#F5E6D3", "accent": "#D4AF37"},
        "fonts": {"heading": "Playfair Display", "body": "Crimson Text"},
        "style": "classic vintage with serif typography",
    },
    "modern_bold": {
        "name": "Modern Bold",
        "colors": {"primary": "#FF6B6B", "secondary": "#4ECDC4", "accent": "#FFE66D"},
        "fonts": {"heading": "Poppins", "body": "Inter"},
        "style": "vibrant modern with bold colors",
    },
    "sustainable_earth": {
        "name": "Sustainable Earth",
        "colors": {"primary": "#2D5016", "secondary": "#F4F1DE", "accent": "#E07A5F"},
        "fonts": {"heading": "Raleway", "body": "Lato"},
        "style": "eco-friendly earth tones",
    },
}


def get_template(template_name: str) -> dict:
    """Get theme template by name"""
    return THEME_TEMPLATES.get(template_name, THEME_TEMPLATES["luxury_minimalist"])


def list_templates() -> list:
    """List all available templates"""
    return list(THEME_TEMPLATES.keys())
