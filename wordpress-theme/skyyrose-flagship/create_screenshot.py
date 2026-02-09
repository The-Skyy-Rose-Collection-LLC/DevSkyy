#!/usr/bin/env python3
"""Generate screenshot.png for SkyyRose Flagship Theme"""

from PIL import Image, ImageDraw, ImageFont
import sys

# Create 1200x900 image with gradient
width, height = 1200, 900
image = Image.new('RGB', (width, height))
draw = ImageDraw.Draw(image)

# Create gradient background (dark purple to black)
for y in range(height):
    # Interpolate between two colors
    r = int(10 + (42 - 10) * (y / height))
    g = int(10 + (26 - 10) * (y / height))
    b = int(10 + (42 - 10) * (y / height))
    draw.rectangle([0, y, width, y + 1], fill=(r, g, b))

# Try to load system fonts, fall back to default
try:
    title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 100)
    subtitle_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
    body_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
    small_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
except:
    # Fall back to default font
    title_font = subtitle_font = body_font = small_font = ImageFont.load_default()

# Draw text layers
# Title
title = "SkyyRose"
bbox = draw.textbbox((0, 0), title, font=title_font)
title_width = bbox[2] - bbox[0]
draw.text(((width - title_width) // 2, 200), title, fill=(255, 255, 255), font=title_font)

# Subtitle
subtitle = "FLAGSHIP THEME"
bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
subtitle_width = bbox[2] - bbox[0]
draw.text(((width - subtitle_width) // 2, 320), subtitle, fill=(220, 220, 220), font=subtitle_font)

# Features line 1
features1 = "Premium WordPress • 3D Immersive Experiences"
bbox = draw.textbbox((0, 0), features1, font=body_font)
f1_width = bbox[2] - bbox[0]
draw.text(((width - f1_width) // 2, 420), features1, fill=(180, 180, 180), font=body_font)

# Features line 2
features2 = "WooCommerce Integration • WCAG 2.1 AA Accessible"
bbox = draw.textbbox((0, 0), features2, font=body_font)
f2_width = bbox[2] - bbox[0]
draw.text(((width - f2_width) // 2, 460), features2, fill=(180, 180, 180), font=body_font)

# Version
version = "Version 1.0.0"
bbox = draw.textbbox((0, 0), version, font=small_font)
v_width = bbox[2] - bbox[0]
draw.text(((width - v_width) // 2, 800), version, fill=(120, 120, 120), font=small_font)

# Save as PNG
image.save('screenshot.png', 'PNG', optimize=True, quality=90)
print("✓ Created screenshot.png (1200×900)")
print(f"  File size: {image.size}")
