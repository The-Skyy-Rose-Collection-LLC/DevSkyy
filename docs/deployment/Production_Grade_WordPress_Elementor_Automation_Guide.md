# Production-Grade WordPress/Elementor Automation Reference

Automating WordPress with Elementor Pro requires mastering three interrelated systems: the Elementor JSON schema for template data, WordPress REST API mechanics for deployment, and the MCP protocol for AI-agent tooling. This guide provides verified technical specifications for building production automation that programmatically creates, deploys, and manages WooCommerce theme builder templates.

## Elementor template data lives in post meta, not REST endpoints

Elementor stores all template content in the `_elementor_data` post meta field as a JSON-encoded string. Templates use the `elementor_library` custom post type, and the current schema version is **0.4**. The root structure contains four required fields:

```json
{
  "title": "Template Name",
  "type": "product",
  "version": "0.4",
  "page_settings": {},
  "content": []
}
```

The `type` field determines the template category: `header`, `footer`, `single`, `archive`, `product` (WooCommerce single), or `product-archive`. Each element in the `content` array follows a recursive structure with **five required properties**:

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique 8-character hex identifier |
| `elType` | string | `container`, `section`, `column`, or `widget` |
| `isInner` | boolean | Whether element is nested |
| `settings` | object | Widget-specific configuration |
| `elements` | array | Child elements (empty for widgets) |

Widgets add a sixth field, `widgetType`, which identifies the widget (e.g., `woocommerce-product-add-to-cart`). Settings values use consistent patterns: strings for simple values, objects with `unit` and `size` for dimensions, and objects with `top`, `right`, `bottom`, `left`, `isLinked` for spacing. Responsive variants append `_tablet` or `_mobile` suffixes.

## WooCommerce widgets require specific settings schemas

The three core WooCommerce widgets each have distinct configuration structures. The **Add To Cart widget is mandatory** for single product templates—Elementor's editor will fail to load without it.

**woocommerce-product-images** controls gallery display:
```json
{
  "widgetType": "woocommerce-product-images",
  "settings": {
    "sale_flash": "yes",
    "image_border_border": "none",
    "spacing": {"unit": "px", "size": 10},
    "lightbox": "yes",
    "zoom": "yes"
  }
}
```

**woocommerce-product-add-to-cart** handles purchase functionality:
```json
{
  "widgetType": "woocommerce-product-add-to-cart",
  "settings": {
    "show_quantity": "yes",
    "layout": "stacked",
    "button_size": "md",
    "button_text_color": "#ffffff",
    "button_background_color": "#2ecc71"
  }
}
```

**woocommerce-archive-products** displays product grids:
```json
{
  "widgetType": "woocommerce-archive-products",
  "settings": {
    "columns": 4,
    "rows": 4,
    "paginate": "yes",
    "allow_order": "yes",
    "show_result_count": "yes",
    "query_post_type": "current_query"
  }
}
```

## Display conditions use a hierarchical string format

The `_elementor_conditions` meta field stores a PHP serialized array of condition strings following the pattern `{action}/{type}/{sub_type}/{sub_id}`. Actions are `include` or `exclude`.

| Condition String | Applies To |
|------------------|------------|
| `include/product` | All single products |
| `include/product/123` | Specific product ID 123 |
| `include/product_cat/45` | Products in category ID 45 |
| `include/product_archive` | All product archives |
| `include/shop_page` | Main shop page only |
| `exclude/product/789` | Exclude specific product |

Setting conditions programmatically requires updating the meta and clearing the cache:

```php
update_post_meta($template_id, '_elementor_conditions', ['include/product']);
delete_option('elementor_pro_theme_builder_conditions');
```

## Template deployment uses WordPress REST API with custom meta

Elementor does **not expose dedicated REST endpoints** for template CRUD operations. Instead, deploy templates through WordPress's native post API combined with Elementor-specific meta fields. The only Elementor REST endpoint (`/wp-json/elementor/v1/cache`) handles CSS cache clearing.

Creating a template via REST API requires a two-step process:

**Step 1: Create the elementor_library post**
```bash
curl -X POST "https://site.com/wp-json/wp/v2/posts" \
  -H "Authorization: Basic base64(username:app_password)" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Product Template",
    "status": "publish",
    "type": "elementor_library"
  }'
```

**Step 2: Set required meta fields via custom endpoint or direct access**

Seven meta fields are essential for functional templates:

| Meta Key | Purpose | Example Value |
|----------|---------|---------------|
| `_elementor_edit_mode` | Enables Elementor | `"builder"` |
| `_elementor_template_type` | Template category | `"product"` |
| `_elementor_data` | JSON content | `wp_slash(json_encode($data))` |
| `_elementor_conditions` | Display rules | `['include/product']` |
| `_elementor_version` | Elementor version | `ELEMENTOR_VERSION` |
| `_elementor_pro_version` | Pro version | `ELEMENTOR_PRO_VERSION` |
| `_wp_page_template` | WordPress template | `"elementor_canvas"` |

After updating `_elementor_data`, regenerate CSS by calling `\Elementor\Plugin::$instance->files_manager->clear_cache()` or the REST endpoint `DELETE /wp-json/elementor/v1/cache`.

## Authentication differs between WordPress core and WooCommerce APIs

WordPress **Application Passwords** (introduced in 5.6) provide the recommended authentication for REST API automation. Format credentials as Basic Auth with base64 encoding:

```
Authorization: Basic base64(username:application_password)
```

Application Passwords display as `xxxx xxxx xxxx xxxx xxxx xxxx` (24 characters with spaces) and **require HTTPS** in production. For local development without SSL, add `define('WP_ENVIRONMENT_TYPE', 'local');` to wp-config.php.

WooCommerce uses a separate credential system with **Consumer Key/Secret pairs** generated at WooCommerce → Settings → Advanced → REST API. These use identical Basic Auth format but with different credentials:

```
Authorization: Basic base64(ck_XXXX:cs_XXXX)
```

For automation systems, store credentials in environment variables and use dedicated API user accounts with minimal capabilities:

```php
define('WC_CONSUMER_KEY', getenv('WC_CONSUMER_KEY'));
define('WC_CONSUMER_SECRET', getenv('WC_CONSUMER_SECRET'));
```

## FastMCP patterns optimize AI agent tool consumption

FastMCP 2.0 provides the highest-productivity pattern for MCP server development with decorator-based tool definitions:

```python
from fastmcp import FastMCP, Context, ToolError
from pydantic import BaseModel, Field

mcp = FastMCP("WordPress Automation")

class TemplateParams(BaseModel):
    name: str = Field(description="Template display name")
    type: str = Field(description="Template type: product, product-archive, header, footer")
    conditions: list[str] = Field(description="Display conditions array")

@mcp.tool()
async def create_elementor_template(params: TemplateParams, ctx: Context) -> dict:
    """Create an Elementor theme builder template.

    Returns template ID and deployment status.
    """
    try:
        await ctx.info(f"Creating {params.type} template: {params.name}")
        result = await deploy_template(params)
        return {"template_id": result.id, "status": "deployed"}
    except APIError as e:
        await ctx.error(f"Deployment failed: {e}")
        raise ToolError(f"Template creation failed: {e.message}")
```

**Tool design best practices for AI consumption:**
- Start descriptions with action verbs (Create, Get, Update, Delete)
- Use Pydantic models with Field descriptions for complex inputs
- Return structured data that helps agents decide next steps
- Raise `ToolError` for recoverable errors with actionable messages
- Use `ctx.report_progress()` for long-running operations

Error handling should distinguish client-visible errors from internal failures:

```python
from mcp.types import CallToolResult, TextContent

@mcp.tool()
async def risky_operation(data: dict) -> CallToolResult:
    try:
        result = await process(data)
        return CallToolResult(
            content=[TextContent(type="text", text=str(result))]
        )
    except ValidationError as e:
        return CallToolResult(
            isError=True,
            content=[TextContent(type="text", text=f"Invalid input: {e}")]
        )
```

## Resource and prompt definitions complete MCP servers

Resources expose read-only data through URI templates:

```python
@mcp.resource("wordpress://templates/{template_id}")
async def get_template(template_id: str) -> dict:
    """Retrieve Elementor template by ID."""
    return await fetch_template_data(template_id)
```

Prompts generate structured messages for AI workflows:

```python
@mcp.prompt()
def template_review(template_json: str) -> str:
    """Generate a template review request."""
    return f"Review this Elementor template JSON for production readiness:\n\n{template_json}"
```

The lifespan pattern manages shared resources like HTTP clients and database connections:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def app_lifespan(server: FastMCP):
    client = httpx.AsyncClient(timeout=30.0)
    try:
        yield {"http_client": client}
    finally:
        await client.aclose()

mcp = FastMCP("Server", lifespan=app_lifespan)
```

## Complete deployment workflow for WooCommerce templates

A production-ready template deployment function combines all these elements:

```php
function deploy_woocommerce_template($config) {
    // Create post
    $template_id = wp_insert_post([
        'post_type' => 'elementor_library',
        'post_title' => $config['name'],
        'post_status' => 'publish'
    ]);

    // Set taxonomy term
    wp_set_object_terms($template_id, $config['type'], 'elementor_library_type');

    // Core meta
    update_post_meta($template_id, '_elementor_edit_mode', 'builder');
    update_post_meta($template_id, '_elementor_template_type', $config['type']);
    update_post_meta($template_id, '_elementor_version', ELEMENTOR_VERSION);
    update_post_meta($template_id, '_elementor_pro_version', ELEMENTOR_PRO_VERSION);

    // Content and conditions
    update_post_meta($template_id, '_elementor_data', wp_slash(json_encode($config['content'])));
    update_post_meta($template_id, '_elementor_conditions', $config['conditions']);

    // Clear caches
    delete_option('elementor_pro_theme_builder_conditions');
    \Elementor\Plugin::$instance->files_manager->clear_cache();

    return $template_id;
}
```

## Conclusion

Production WordPress/Elementor automation centers on understanding three systems: the `_elementor_data` JSON schema for content structure, WordPress post meta for template deployment, and proper authentication flows for API access. The Add To Cart widget requirement for product templates and the conditions cache clearing step are common failure points. For MCP server integration, FastMCP's decorator pattern with Pydantic validation provides the cleanest interface for AI agent consumption, while proper error handling with `isError` flags enables agents to recover gracefully from failures.
