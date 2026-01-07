---
name: WordPress Elementor Integration
description: This skill should be used when the user asks to "create WordPress theme", "generate Elementor widgets", "deploy to WordPress", "integrate WooCommerce", "upload media to WordPress", or mentions Shoptimizer child theme, WordPress API, or site deployment.
version: 1.0.0
---

# WordPress Elementor Integration Skill

Use this skill when working with WordPress themes, Elementor page builder, and WooCommerce integration for SkyyRose.

## When to Use This Skill

Invoke this skill when the user:

- Wants to create or modify WordPress themes
- Needs to generate Elementor page layouts or widgets
- Asks about WooCommerce product integration
- Requests WordPress media uploads (images, 3D models)
- Mentions Shoptimizer child theme customization
- Needs WordPress REST API integration

## WordPress Architecture

### Current Setup

- **Live Site**: `https://skyyrose.com`
- **Parent Theme**: Shoptimizer (optimized for WooCommerce)
- **Child Theme**: `skyyrose-shoptimizer-child` (custom)
- **Page Builder**: Elementor Pro
- **E-commerce**: WooCommerce with custom integrations

### Key Components

1. **Operations Agent** (`agents/operations_agent.py`):
   - WordPress deployment and management
   - Theme generation and customization
   - Media uploads
   - Site health monitoring

2. **WordPress MCP Tool** (`devskyy_mcp.py:devskyy_generate_wordpress_theme`):
   - Automated theme scaffolding
   - Child theme generation
   - Custom post types
   - Theme customization

3. **WooCommerce MCP Server** (`mcp/woocommerce_mcp.py`):
   - Product CRUD operations
   - Order management
   - Inventory sync
   - Customer data

## WordPress REST API Integration

### Authentication

```python
import httpx

WORDPRESS_URL = "https://skyyrose.com"
WOO_KEY = "ck_..."  # pragma: allowlist secret
WOO_SECRET = "cs_..."  # pragma: allowlist secret

async def wordpress_request(endpoint: str, method: str = "GET", data: dict = None):
    """Make authenticated WordPress API request."""
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method,
            f"{WORDPRESS_URL}/wp-json{endpoint}",
            json=data,
            auth=(WOO_KEY, WOO_SECRET)
        )
        return response.json()
```

### Upload Media

```python
async def upload_media_to_wordpress(file_path: str, title: str, alt_text: str = None):
    """Upload file to WordPress media library."""
    with open(file_path, 'rb') as f:
        files = {'file': f}
        headers = {
            'Authorization': f'Bearer {WP_AUTH_TOKEN}'
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{WORDPRESS_URL}/wp-json/wp/v2/media",
                files=files,
                headers=headers,
                data={
                    'title': title,
                    'alt_text': alt_text or title
                }
            )

    return response.json()['id']
```

## Elementor Integration

### Generate Page Layout

Located in `agents/operations_agent.py`:

```python
async def generate_elementor_page(
    page_title: str,
    sections: list,
    collection: str = None
) -> dict:
    """Generate Elementor page JSON structure."""

    elementor_data = {
        "version": "3.0",
        "title": page_title,
        "elements": []
    }

    for section in sections:
        elementor_data["elements"].append({
            "id": str(uuid.uuid4()),
            "elType": "section",
            "settings": section.get("settings", {}),
            "elements": section.get("columns", [])
        })

    return elementor_data
```

### Custom Elementor Widgets

```python
# Register custom widget for 3D model viewer
elementor_widget = {
    "name": "skyyrose-3d-viewer",
    "title": "SkyyRose 3D Model",
    "icon": "eicon-3d-viewer",
    "categories": ["skyyrose"],
    "settings": {
        "model_url": {
            "type": "url",
            "label": "3D Model URL (.glb)"
        },
        "auto_rotate": {
            "type": "switcher",
            "label": "Auto Rotate",
            "default": "yes"
        }
    }
}
```

## WooCommerce Product Management

### Create Product

```python
async def create_woocommerce_product(product_data: dict) -> int:
    """Create WooCommerce product via REST API."""

    response = await wordpress_request(
        "/wc/v3/products",
        method="POST",
        data={
            "name": product_data["name"],
            "type": "simple",
            "regular_price": str(product_data["price"]),
            "description": product_data["description"],
            "short_description": product_data["short_desc"],
            "categories": [
                {"id": product_data["category_id"]}
            ],
            "images": [
                {"src": img_url} for img_url in product_data["images"]
            ],
            "meta_data": [
                {
                    "key": "_product_3d_model",
                    "value": product_data.get("model_3d_url")
                }
            ]
        }
    )

    return response["id"]
```

### Attach 3D Model to Product

```python
async def attach_3d_model(product_id: int, model_media_id: int):
    """Link 3D model media to WooCommerce product."""

    await wordpress_request(
        f"/wc/v3/products/{product_id}",
        method="PUT",
        data={
            "meta_data": [
                {
                    "key": "_product_3d_model",
                    "value": model_media_id
                }
            ]
        }
    )
```

## Shoptimizer Child Theme

### Theme Structure

```
skyyrose-shoptimizer-child/
├── style.css              # Theme metadata & custom styles
├── functions.php          # Theme functions & hooks
├── assets/
│   ├── logos/            # 5 rotating logo variants
│   └── css/              # Rotating logo animations
├── templates/            # Custom page templates
└── woocommerce/          # WooCommerce template overrides
```

### Rotating Logo Integration

Located in child theme `functions.php`:

```php
function skyyrose_rotating_logo() {
    $logos = [
        'black-rose' => get_stylesheet_directory_uri() . '/assets/logos/black-rose-trophy-cosmic.png',
        'love-hurts' => get_stylesheet_directory_uri() . '/assets/logos/love-hurts-trophy-red.png',
        'signature' => get_stylesheet_directory_uri() . '/assets/logos/signature-rose-rosegold.png',
        'sr-monogram' => get_stylesheet_directory_uri() . '/assets/logos/sr-monogram-rosegold.png'
    ];

    // Auto-detect collection from page context
    $collection = get_collection_from_context();
    $logo_url = $logos[$collection] ?? $logos['sr-monogram'];

    return sprintf(
        '<img src="%s" alt="SkyyRose Logo" class="rotating-logo animate-rotate3D"/>',
        esc_url($logo_url)
    );
}
```

## Deployment Workflow

### Step 1: Theme Packaging

```python
import zipfile

def package_child_theme(theme_dir: str, output_path: str):
    """Package child theme for WordPress upload."""
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(theme_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, theme_dir)
                zipf.write(file_path, arcname)
```

### Step 2: Upload via SFTP/FTP

```python
import paramiko

async def deploy_theme_sftp(zip_path: str, host: str, username: str, password: str):
    """Deploy theme via SFTP."""
    transport = paramiko.Transport((host, 22))
    transport.connect(username=username, password=password)

    sftp = paramiko.SFTPClient.from_transport(transport)
    remote_path = f"/wp-content/themes/{os.path.basename(zip_path)}"

    sftp.put(zip_path, remote_path)
    sftp.close()
    transport.close()
```

### Step 3: Activate Theme

```python
# Via WP-CLI (if available)
subprocess.run([
    "wp", "theme", "activate", "skyyrose-shoptimizer-child",
    "--path=/var/www/html"
])
```

## File Locations

- **Operations Agent**: `agents/operations_agent.py`
- **WordPress MCP Tool**: `devskyy_mcp.py` (line 189)
- **WooCommerce MCP**: `mcp/woocommerce_mcp.py`
- **Child Theme Package**: `skyyrose-shoptimizer-child.zip`
- **Deployment Memory**: `.serena/memories/skyyrose_wordpress_child_theme_deployment.md`

## Common Use Cases

### Use Case 1: Product Launch

```python
# 1. Generate 3D model
model = await tripo_agent.generate_from_text("new hoodie design")

# 2. Upload to WordPress
media_id = await upload_media_to_wordpress(model.glb_path, "Hoodie 3D Model")

# 3. Create WooCommerce product
product_id = await create_woocommerce_product({
    "name": "Signature Hoodie",
    "price": 89.99,
    "description": "...",
    "model_3d_url": media_id
})
```

### Use Case 2: Collection Page

```python
# Generate Elementor collection page
page_data = await generate_elementor_page(
    page_title="BLACK_ROSE Collection",
    sections=[
        {
            "type": "hero",
            "settings": {
                "background_image": hero_img_url,
                "heading": "BLACK_ROSE",
                "subheading": "Dark romantic aesthetic"
            }
        },
        {
            "type": "product_grid",
            "columns": [
                {"products": black_rose_product_ids}
            ]
        }
    ]
)
```

## References

See `references/` directory for:

- Complete WordPress REST API documentation
- Elementor widget development guide
- WooCommerce hooks and filters reference
- Shoptimizer child theme customization
- SFTP deployment automation
- Site optimization techniques
