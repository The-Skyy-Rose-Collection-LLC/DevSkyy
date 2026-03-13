# WordPress Embed Snippets

Quick reference for embedding collection pages in WordPress.

---

## Full-Page Iframe Embeds

### SIGNATURE Collection

```html
<div class="collection-embed-container">
  <iframe
    src="https://app.devskyy.app/collections/signature"
    width="100%"
    height="100vh"
    frameborder="0"
    scrolling="auto"
    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
    allowfullscreen
    loading="lazy"
    title="SIGNATURE Collection - SkyyRose Luxury Fashion"
  ></iframe>
</div>

<style>
  .collection-embed-container {
    margin: -20px -20px 0 -20px;
    width: calc(100% + 40px);
    min-height: 100vh;
  }

  .collection-embed-container iframe {
    display: block;
    border: none;
  }
</style>
```

### LOVE HURTS Collection

```html
<div class="collection-embed-container">
  <iframe
    src="https://app.devskyy.app/collections/love-hurts"
    width="100%"
    height="100vh"
    frameborder="0"
    scrolling="auto"
    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
    allowfullscreen
    loading="lazy"
    title="LOVE HURTS Collection - SkyyRose Gothic Romance Fashion"
  ></iframe>
</div>

<style>
  .collection-embed-container {
    margin: -20px -20px 0 -20px;
    width: calc(100% + 40px);
    min-height: 100vh;
  }

  .collection-embed-container iframe {
    display: block;
    border: none;
  }
</style>
```

### BLACK ROSE Collection

```html
<div class="collection-embed-container">
  <iframe
    src="https://app.devskyy.app/collections/black-rose"
    width="100%"
    height="100vh"
    frameborder="0"
    scrolling="auto"
    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
    allowfullscreen
    loading="lazy"
    title="BLACK ROSE Collection - SkyyRose"
  ></iframe>
</div>

<style>
  .collection-embed-container {
    margin: -20px -20px 0 -20px;
    width: calc(100% + 40px);
    min-height: 100vh;
  }

  .collection-embed-container iframe {
    display: block;
    border: none;
  }
</style>
```

---

## Shortcode Implementation

Add to `functions.php`:

```php
/**
 * SkyyRose Collection Embed Shortcode
 *
 * Usage:
 * [skyyrose_collection collection="signature"]
 * [skyyrose_collection collection="love-hurts" height="100vh"]
 */
function skyyrose_collection_embed($atts) {
    $atts = shortcode_atts(array(
        'collection' => 'signature',
        'height' => '100vh',
    ), $atts);

    $collection = sanitize_text_field($atts['collection']);
    $height = sanitize_text_field($atts['height']);
    $url = "https://app.devskyy.app/collections/{$collection}";

    $collection_titles = array(
        'signature' => 'SIGNATURE Collection - SkyyRose Luxury Fashion',
        'love-hurts' => 'LOVE HURTS Collection - SkyyRose Gothic Romance',
        'black-rose' => 'BLACK ROSE Collection - SkyyRose',
    );

    $title = isset($collection_titles[$collection])
        ? $collection_titles[$collection]
        : ucwords(str_replace('-', ' ', $collection)) . ' Collection - SkyyRose';

    $output = sprintf(
        '<div class="collection-embed-container">
            <iframe
                src="%s"
                width="100%%"
                height="%s"
                frameborder="0"
                scrolling="auto"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                allowfullscreen
                loading="lazy"
                title="%s"
            ></iframe>
        </div>
        <style>
            .collection-embed-container {
                margin: -20px -20px 0 -20px;
                width: calc(100%% + 40px);
                min-height: %s;
            }
            .collection-embed-container iframe {
                display: block;
                border: none;
            }
        </style>',
        esc_url($url),
        esc_attr($height),
        esc_attr($title),
        esc_attr($height)
    );

    return $output;
}
add_shortcode('skyyrose_collection', 'skyyrose_collection_embed');
```

**Shortcode Usage in WordPress Editor**:

```
[skyyrose_collection collection="signature"]
[skyyrose_collection collection="love-hurts"]
[skyyrose_collection collection="black-rose"]
[skyyrose_collection collection="signature" height="80vh"]
```

---

## Elementor Widget

For Elementor users:

1. Add **HTML Widget**
2. Paste iframe code from above
3. Configure section:
   - Layout → Content Width: Full Width
   - Advanced → Margin: 0px all
   - Advanced → Padding: 0px all

---

## Navigation Menu Links

Add to WordPress menu:

- **SIGNATURE**: `https://skyyrose.com/collections/signature`
- **LOVE HURTS**: `https://skyyrose.com/collections/love-hurts`
- **BLACK ROSE**: `https://skyyrose.com/collections/black-rose`

Or link directly to app:

- **SIGNATURE**: `https://app.devskyy.app/collections/signature`
- **LOVE HURTS**: `https://app.devskyy.app/collections/love-hurts`
- **BLACK ROSE**: `https://app.devskyy.app/collections/black-rose`

---

## Mobile Optimization

The collection pages are fully responsive. No additional mobile-specific embeds needed.

**Test on**:
- iPhone SE (375px)
- iPhone 12 Pro (390px)
- iPad (768px)
- Desktop (1920px)

---

## SEO Considerations

When embedding via iframe:

- Page title: Set on WordPress page (e.g., "SIGNATURE Collection | SkyyRose")
- Meta description: Set on WordPress page
- Open Graph: Set on WordPress page (will override iframe metadata)
- Canonical URL: Point to WordPress page URL

For best SEO, consider creating WordPress pages with:
- Hero section with collection description
- Embedded iframe for interactive experience
- Product grid below (duplicated from app)
- Rich text content for search engines

---

## Performance Notes

- Iframe uses `loading="lazy"` for better performance
- Collection pages are optimized with:
  - Code splitting (Three.js lazy loaded)
  - WebP/AVIF images
  - Resource prefetching
  - Bundle optimization

**Expected Load Time**: 2-3 seconds on 4G

---

## Troubleshooting

**Issue**: Iframe shows "Refused to display in a frame"
- **Fix**: Verify `Content-Security-Policy` allows skyyrose.com

**Issue**: Iframe not loading
- **Fix**: Check browser console for errors
- **Fix**: Verify app.devskyy.app is accessible

**Issue**: Scrolling issues
- **Fix**: Adjust `scrolling="auto"` to `scrolling="yes"`
- **Fix**: Set explicit height (e.g., `height="2000px"`)

**Issue**: Three.js not rendering
- **Fix**: Wait for "Loading 3D Experience..." to complete
- **Fix**: Check if browser supports WebGL

---

## Support

For issues with WordPress embedding:
- Email: support@skyyrose.com
- Documentation: /docs/DEPLOYMENT.md
