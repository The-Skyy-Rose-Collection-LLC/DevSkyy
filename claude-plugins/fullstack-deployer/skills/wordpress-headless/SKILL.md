# WordPress Headless CMS

This skill provides comprehensive knowledge for WordPress as a headless CMS backend. It activates when users mention "wordpress api", "wp rest api", "headless wordpress", "wordpress backend", "ACF", "custom post types", "wordpress graphql", or encounter WordPress API-related errors.

---

## WordPress REST API Basics

### Base Endpoints
```
GET  /wp-json/wp/v2/posts          # List posts
GET  /wp-json/wp/v2/posts/{id}     # Single post
GET  /wp-json/wp/v2/pages          # List pages
GET  /wp-json/wp/v2/media          # List media
GET  /wp-json/wp/v2/categories     # List categories
GET  /wp-json/wp/v2/tags           # List tags
GET  /wp-json/wp/v2/users          # List users
```

### Query Parameters
```
?per_page=10              # Items per page (max 100)
?page=2                   # Page number
?search=keyword           # Search posts
?categories=1,2           # Filter by category IDs
?tags=5,6                 # Filter by tag IDs
?orderby=date             # Order by field
?order=desc               # Order direction
?_embed                   # Include embedded data (featured image, author)
?status=publish           # Post status
?slug=my-post             # Get by slug
```

## Fetching Data in Next.js

### Basic Fetch
```typescript
// lib/wordpress.ts
const WP_API_URL = process.env.WORDPRESS_API_URL

export async function getPosts(params?: {
  perPage?: number
  page?: number
  categories?: number[]
}) {
  const searchParams = new URLSearchParams()
  if (params?.perPage) searchParams.set('per_page', String(params.perPage))
  if (params?.page) searchParams.set('page', String(params.page))
  if (params?.categories) searchParams.set('categories', params.categories.join(','))
  searchParams.set('_embed', 'true')

  const response = await fetch(
    `${WP_API_URL}/wp-json/wp/v2/posts?${searchParams}`,
    { next: { revalidate: 60 } }
  )

  if (!response.ok) {
    throw new Error(`WordPress API error: ${response.status}`)
  }

  return response.json()
}

export async function getPost(slug: string) {
  const response = await fetch(
    `${WP_API_URL}/wp-json/wp/v2/posts?slug=${slug}&_embed=true`,
    { next: { revalidate: 60 } }
  )

  const posts = await response.json()
  return posts[0] || null
}
```

### Type Definitions
```typescript
// types/wordpress.ts
export interface WPPost {
  id: number
  slug: string
  title: { rendered: string }
  content: { rendered: string }
  excerpt: { rendered: string }
  date: string
  modified: string
  featured_media: number
  categories: number[]
  tags: number[]
  _embedded?: {
    'wp:featuredmedia'?: Array<{
      source_url: string
      alt_text: string
    }>
    author?: Array<{
      name: string
      avatar_urls: Record<string, string>
    }>
  }
}

export interface WPPage {
  id: number
  slug: string
  title: { rendered: string }
  content: { rendered: string }
  parent: number
  menu_order: number
}
```

## Advanced Custom Fields (ACF)

### Enable ACF in REST API
```php
// functions.php or plugin
function expose_acf_to_rest_api() {
  add_filter('acf/rest_api/field_settings/show_in_rest', '__return_true');
}
add_action('acf/init', 'expose_acf_to_rest_api');
```

### ACF to REST API Plugin Setup
```php
// Alternative: Use ACF to REST API plugin
// Adds 'acf' field to REST responses automatically
```

### Fetching ACF Data
```typescript
export async function getPostWithACF(slug: string) {
  const response = await fetch(
    `${WP_API_URL}/wp-json/wp/v2/posts?slug=${slug}&_embed=true`
  )
  const posts = await response.json()
  const post = posts[0]

  // ACF fields available at post.acf
  return {
    ...post,
    customFields: post.acf || {}
  }
}
```

## Custom Post Types

### Register CPT with REST Support
```php
// functions.php
function register_product_post_type() {
  register_post_type('product', [
    'labels' => [
      'name' => 'Products',
      'singular_name' => 'Product',
    ],
    'public' => true,
    'show_in_rest' => true, // Enable REST API
    'rest_base' => 'products', // Custom endpoint
    'supports' => ['title', 'editor', 'thumbnail', 'custom-fields'],
  ]);
}
add_action('init', 'register_product_post_type');
```

### Fetch Custom Post Type
```typescript
export async function getProducts() {
  const response = await fetch(
    `${WP_API_URL}/wp-json/wp/v2/products?_embed=true`
  )
  return response.json()
}
```

## Authentication for Protected Routes

### Application Passwords (WordPress 5.6+)
```typescript
const credentials = Buffer.from(
  `${process.env.WP_USERNAME}:${process.env.WP_APP_PASSWORD}`
).toString('base64')

export async function createPost(data: any) {
  const response = await fetch(`${WP_API_URL}/wp-json/wp/v2/posts`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Basic ${credentials}`
    },
    body: JSON.stringify(data)
  })
  return response.json()
}
```

### JWT Authentication
```typescript
// First, get token
const tokenResponse = await fetch(`${WP_API_URL}/wp-json/jwt-auth/v1/token`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username, password })
})
const { token } = await tokenResponse.json()

// Use token in requests
const response = await fetch(`${WP_API_URL}/wp-json/wp/v2/posts`, {
  headers: { 'Authorization': `Bearer ${token}` }
})
```

## WordPress GraphQL (WPGraphQL Plugin)

### Query Example
```graphql
query GetPosts {
  posts(first: 10) {
    nodes {
      id
      slug
      title
      excerpt
      featuredImage {
        node {
          sourceUrl
          altText
        }
      }
    }
  }
}
```

### Next.js Integration
```typescript
export async function getPostsGraphQL() {
  const response = await fetch(`${WP_API_URL}/graphql`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query: `
        query GetPosts {
          posts(first: 10) {
            nodes {
              slug
              title
              excerpt
            }
          }
        }
      `
    }),
    next: { revalidate: 60 }
  })

  const { data } = await response.json()
  return data.posts.nodes
}
```

## Common Errors and Solutions

### "rest_no_route"
- Endpoint doesn't exist or permalink structure issue
- Enable permalinks: Settings > Permalinks > Post name
- Flush permalinks: Settings > Permalinks > Save Changes

### CORS Errors
```php
// functions.php - Add CORS headers
function add_cors_headers() {
  header("Access-Control-Allow-Origin: " . $_SERVER['HTTP_ORIGIN']);
  header("Access-Control-Allow-Methods: GET, POST, OPTIONS");
  header("Access-Control-Allow-Headers: Authorization, Content-Type");
}
add_action('rest_api_init', 'add_cors_headers');
```

### "rest_forbidden"
- Authentication required for this endpoint
- Check user capabilities/permissions
- Verify Application Password or JWT token

### Empty "_embedded" Data
- Featured image not set on post
- Author doesn't have avatar
- Check that _embed parameter is included

## Environment Variables
```bash
WORDPRESS_API_URL=https://your-wordpress-site.com
WP_USERNAME=api_user
WP_APP_PASSWORD=xxxx xxxx xxxx xxxx xxxx xxxx
```

## Autonomous Recovery Steps

When encountering WordPress API errors:

1. **Check API URL** - Verify WordPress is accessible at the configured URL
2. **Test endpoint directly** - `curl https://site.com/wp-json/wp/v2/posts`
3. **Use Context7** to fetch WordPress REST API documentation
4. **Check permalinks** - Must be set to something other than "Plain"
5. **Verify authentication** if accessing protected endpoints
6. **Check CORS** if frontend on different domain
7. **Review WordPress error logs** at `wp-content/debug.log`
