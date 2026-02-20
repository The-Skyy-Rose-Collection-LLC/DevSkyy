/**
 * WordPress Operations Manager
 * Complete WordPress REST API operations suite
 */

interface WooCommerceConfig {
  baseUrl: string
  consumerKey: string
  consumerSecret: string
}

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

interface WordPressPost {
  id?: number
  title: string | { raw: string; rendered?: string }
  content: string | { raw: string; rendered?: string }
  excerpt?: string | { raw: string; rendered?: string }
  status: 'draft' | 'publish' | 'pending' | 'private' | 'future'
  author?: number
  featured_media?: number
  comment_status?: 'open' | 'closed'
  ping_status?: 'open' | 'closed'
  format?: 'standard' | 'aside' | 'chat' | 'gallery' | 'link' | 'image' | 'quote' | 'status' | 'video' | 'audio'
  meta?: Record<string, any>
  categories?: number[]
  tags?: number[]
  sticky?: boolean
  date?: string
  date_gmt?: string
  slug?: string
  password?: string
}

interface WordPressPage {
  id?: number
  title: string | { raw: string; rendered?: string }
  content: string | { raw: string; rendered?: string }
  status: 'draft' | 'publish' | 'pending' | 'private'
  author?: number
  parent?: number
  menu_order?: number
  comment_status?: 'open' | 'closed'
  slug?: string
  template?: string
}

interface WordPressCategory {
  id?: number
  name: string
  slug?: string
  description?: string
  parent?: number
  meta?: Record<string, any>
}

interface WordPressTag {
  id?: number
  name: string
  slug?: string
  description?: string
  meta?: Record<string, any>
}

interface WordPressMedia {
  id?: number
  title: string
  alt_text?: string
  caption?: string
  description?: string
  post?: number
  author?: number
}

interface WordPressUser {
  id?: number
  username?: string
  name?: string
  first_name?: string
  last_name?: string
  email?: string
  url?: string
  description?: string
  roles?: string[]
  meta?: Record<string, any>
}

interface WordPressComment {
  id?: number
  post?: number
  parent?: number
  author?: number
  author_name?: string
  author_email?: string
  author_url?: string
  content: string | { raw: string; rendered?: string }
  status?: 'hold' | 'approve' | 'spam' | 'trash'
  meta?: Record<string, any>
}

interface WordPressSettings {
  title?: string
  description?: string
  url?: string
  email?: string
  timezone?: string
  date_format?: string
  time_format?: string
  start_of_week?: number
  language?: string
  use_smilies?: boolean
  default_category?: number
  default_post_format?: string
  posts_per_page?: number
  show_on_front?: 'posts' | 'page'
  page_on_front?: number
  page_for_posts?: number
}

// ============================================================================
// WORDPRESS OPERATIONS MANAGER
// ============================================================================

export class WordPressOperationsManager {
  private config: WooCommerceConfig
  private authHeader: string

  constructor(config: WooCommerceConfig) {
    this.config = config
    const credentials = btoa(`${config.consumerKey}:${config.consumerSecret}`)
    this.authHeader = `Basic ${credentials}`
  }

  // ==========================================================================
  // POSTS
  // ==========================================================================

  async createPost(post: WordPressPost): Promise<any> {
    return this.request('POST', '/wp/v2/posts', post)
  }

  async getPost(id: number): Promise<any> {
    return this.request('GET', `/wp/v2/posts/${id}`)
  }

  async updatePost(id: number, post: Partial<WordPressPost>): Promise<any> {
    return this.request('POST', `/wp/v2/posts/${id}`, post)
  }

  async deletePost(id: number, force = false): Promise<any> {
    return this.request('DELETE', `/wp/v2/posts/${id}?force=${force}`)
  }

  async listPosts(params?: {
    page?: number
    per_page?: number
    search?: string
    author?: number
    status?: string
    categories?: number[]
    tags?: number[]
    order?: 'asc' | 'desc'
    orderby?: string
  }): Promise<any[]> {
    const query = this.buildQuery(params)
    return this.request('GET', `/wp/v2/posts${query}`)
  }

  // ==========================================================================
  // PAGES
  // ==========================================================================

  async createPage(page: WordPressPage): Promise<any> {
    return this.request('POST', '/wp/v2/pages', page)
  }

  async getPage(id: number): Promise<any> {
    return this.request('GET', `/wp/v2/pages/${id}`)
  }

  async updatePage(id: number, page: Partial<WordPressPage>): Promise<any> {
    return this.request('POST', `/wp/v2/pages/${id}`, page)
  }

  async deletePage(id: number, force = false): Promise<any> {
    return this.request('DELETE', `/wp/v2/pages/${id}?force=${force}`)
  }

  async listPages(params?: {
    page?: number
    per_page?: number
    search?: string
    status?: string
    parent?: number
    order?: 'asc' | 'desc'
    orderby?: string
  }): Promise<any[]> {
    const query = this.buildQuery(params)
    return this.request('GET', `/wp/v2/pages${query}`)
  }

  // ==========================================================================
  // CATEGORIES
  // ==========================================================================

  async createCategory(category: WordPressCategory): Promise<any> {
    return this.request('POST', '/wp/v2/categories', category)
  }

  async getCategory(id: number): Promise<any> {
    return this.request('GET', `/wp/v2/categories/${id}`)
  }

  async updateCategory(id: number, category: Partial<WordPressCategory>): Promise<any> {
    return this.request('POST', `/wp/v2/categories/${id}`, category)
  }

  async deleteCategory(id: number, force = false): Promise<any> {
    return this.request('DELETE', `/wp/v2/categories/${id}?force=${force}`)
  }

  async listCategories(params?: {
    page?: number
    per_page?: number
    search?: string
    parent?: number
    hide_empty?: boolean
    order?: 'asc' | 'desc'
    orderby?: string
  }): Promise<any[]> {
    const query = this.buildQuery(params)
    return this.request('GET', `/wp/v2/categories${query}`)
  }

  // ==========================================================================
  // TAGS
  // ==========================================================================

  async createTag(tag: WordPressTag): Promise<any> {
    return this.request('POST', '/wp/v2/tags', tag)
  }

  async getTag(id: number): Promise<any> {
    return this.request('GET', `/wp/v2/tags/${id}`)
  }

  async updateTag(id: number, tag: Partial<WordPressTag>): Promise<any> {
    return this.request('POST', `/wp/v2/tags/${id}`, tag)
  }

  async deleteTag(id: number, force = false): Promise<any> {
    return this.request('DELETE', `/wp/v2/tags/${id}?force=${force}`)
  }

  async listTags(params?: {
    page?: number
    per_page?: number
    search?: string
    hide_empty?: boolean
    order?: 'asc' | 'desc'
    orderby?: string
  }): Promise<any[]> {
    const query = this.buildQuery(params)
    return this.request('GET', `/wp/v2/tags${query}`)
  }

  // ==========================================================================
  // MEDIA
  // ==========================================================================

  async uploadMedia(file: File, metadata?: Partial<WordPressMedia>): Promise<any> {
    const formData = new FormData()
    formData.append('file', file)

    if (metadata) {
      Object.entries(metadata).forEach(([key, value]) => {
        if (value !== undefined) {
          formData.append(key, String(value))
        }
      })
    }

    const endpoint = `${this.config.baseUrl}/index.php?rest_route=/wp/v2/media`
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        Authorization: this.authHeader,
      },
      body: formData,
    })

    if (!response.ok) {
      const error = await response.text()
      throw new Error(`Media upload failed: ${response.status} ${error}`)
    }

    return response.json()
  }

  async uploadMediaFromUrl(url: string, metadata?: Partial<WordPressMedia>): Promise<any> {
    // Download from URL
    const imageResponse = await fetch(url)
    const blob = await imageResponse.blob()
    const filename = url.split('/').pop() || 'image.jpg'
    const file = new File([blob], filename, { type: blob.type })

    return this.uploadMedia(file, metadata)
  }

  async getMedia(id: number): Promise<any> {
    return this.request('GET', `/wp/v2/media/${id}`)
  }

  async updateMedia(id: number, media: Partial<WordPressMedia>): Promise<any> {
    return this.request('POST', `/wp/v2/media/${id}`, media)
  }

  async deleteMedia(id: number, force = false): Promise<any> {
    return this.request('DELETE', `/wp/v2/media/${id}?force=${force}`)
  }

  async listMedia(params?: {
    page?: number
    per_page?: number
    search?: string
    author?: number
    media_type?: 'image' | 'video' | 'audio' | 'application'
    mime_type?: string
    order?: 'asc' | 'desc'
    orderby?: string
  }): Promise<any[]> {
    const query = this.buildQuery(params)
    return this.request('GET', `/wp/v2/media${query}`)
  }

  // ==========================================================================
  // USERS
  // ==========================================================================

  async createUser(user: WordPressUser & { username: string; email: string; password: string }): Promise<any> {
    return this.request('POST', '/wp/v2/users', user)
  }

  async getUser(id: number): Promise<any> {
    return this.request('GET', `/wp/v2/users/${id}`)
  }

  async updateUser(id: number, user: Partial<WordPressUser>): Promise<any> {
    return this.request('POST', `/wp/v2/users/${id}`, user)
  }

  async deleteUser(id: number, reassign?: number, force = false): Promise<any> {
    let query = `?force=${force}`
    if (reassign) query += `&reassign=${reassign}`
    return this.request('DELETE', `/wp/v2/users/${id}${query}`)
  }

  async listUsers(params?: {
    page?: number
    per_page?: number
    search?: string
    roles?: string[]
    order?: 'asc' | 'desc'
    orderby?: string
  }): Promise<any[]> {
    const query = this.buildQuery(params)
    return this.request('GET', `/wp/v2/users${query}`)
  }

  async getCurrentUser(): Promise<any> {
    return this.request('GET', '/wp/v2/users/me')
  }

  // ==========================================================================
  // COMMENTS
  // ==========================================================================

  async createComment(comment: WordPressComment): Promise<any> {
    return this.request('POST', '/wp/v2/comments', comment)
  }

  async getComment(id: number): Promise<any> {
    return this.request('GET', `/wp/v2/comments/${id}`)
  }

  async updateComment(id: number, comment: Partial<WordPressComment>): Promise<any> {
    return this.request('POST', `/wp/v2/comments/${id}`, comment)
  }

  async deleteComment(id: number, force = false): Promise<any> {
    return this.request('DELETE', `/wp/v2/comments/${id}?force=${force}`)
  }

  async listComments(params?: {
    page?: number
    per_page?: number
    search?: string
    post?: number
    parent?: number
    author?: number
    status?: string
    order?: 'asc' | 'desc'
    orderby?: string
  }): Promise<any[]> {
    const query = this.buildQuery(params)
    return this.request('GET', `/wp/v2/comments${query}`)
  }

  // ==========================================================================
  // TAXONOMIES
  // ==========================================================================

  async getTaxonomy(taxonomy: string): Promise<any> {
    return this.request('GET', `/wp/v2/taxonomies/${taxonomy}`)
  }

  async listTaxonomies(): Promise<any[]> {
    return this.request('GET', '/wp/v2/taxonomies')
  }

  async getTerms(taxonomy: string, params?: {
    page?: number
    per_page?: number
    search?: string
    parent?: number
    hide_empty?: boolean
    order?: 'asc' | 'desc'
    orderby?: string
  }): Promise<any[]> {
    const query = this.buildQuery(params)
    return this.request('GET', `/wp/v2/${taxonomy}${query}`)
  }

  async createTerm(taxonomy: string, term: { name: string; slug?: string; description?: string; parent?: number }): Promise<any> {
    return this.request('POST', `/wp/v2/${taxonomy}`, term)
  }

  // ==========================================================================
  // POST TYPES
  // ==========================================================================

  async getPostType(type: string): Promise<any> {
    return this.request('GET', `/wp/v2/types/${type}`)
  }

  async listPostTypes(): Promise<any[]> {
    return this.request('GET', '/wp/v2/types')
  }

  // ==========================================================================
  // SETTINGS
  // ==========================================================================

  async getSettings(): Promise<WordPressSettings> {
    return this.request('GET', '/wp/v2/settings')
  }

  async updateSettings(settings: Partial<WordPressSettings>): Promise<WordPressSettings> {
    return this.request('POST', '/wp/v2/settings', settings)
  }

  // ==========================================================================
  // SITE HEALTH
  // ==========================================================================

  async getSiteHealth(): Promise<any> {
    try {
      // WordPress 5.6+ site health endpoint
      return await this.request('GET', '/wp-site-health/v1/tests/background-updates')
    } catch (error) {
      // Fallback: Check basic connectivity
      const posts = await this.listPosts({ per_page: 1 })
      return {
        status: 'healthy',
        message: 'WordPress REST API is accessible',
        posts_count: posts.length
      }
    }
  }

  // ==========================================================================
  // THEMES
  // ==========================================================================

  async listThemes(): Promise<any[]> {
    return this.request('GET', '/wp/v2/themes')
  }

  async getActiveTheme(): Promise<any> {
    const themes = await this.listThemes()
    return themes.find(theme => theme.status === 'active')
  }

  // ==========================================================================
  // PLUGINS
  // ==========================================================================

  async listPlugins(): Promise<any[]> {
    return this.request('GET', '/wp/v2/plugins')
  }

  async getPlugin(plugin: string): Promise<any> {
    return this.request('GET', `/wp/v2/plugins/${plugin}`)
  }

  async updatePlugin(plugin: string, data: { status?: 'active' | 'inactive' }): Promise<any> {
    return this.request('POST', `/wp/v2/plugins/${plugin}`, data)
  }

  // ==========================================================================
  // SEARCH
  // ==========================================================================

  async search(query: string, params?: {
    type?: 'post' | 'page' | 'attachment' | 'term'
    subtype?: string
    page?: number
    per_page?: number
  }): Promise<any[]> {
    const queryParams = this.buildQuery({ ...params, search: query })
    return this.request('GET', `/wp/v2/search${queryParams}`)
  }

  // ==========================================================================
  // BLOCKS (Gutenberg)
  // ==========================================================================

  async listBlockTypes(): Promise<any[]> {
    return this.request('GET', '/wp/v2/block-types')
  }

  async getBlockType(name: string): Promise<any> {
    return this.request('GET', `/wp/v2/block-types/${name}`)
  }

  async listReusableBlocks(): Promise<any[]> {
    return this.request('GET', '/wp/v2/blocks')
  }

  async createReusableBlock(block: { title: string; content: string }): Promise<any> {
    return this.request('POST', '/wp/v2/blocks', block)
  }

  // ==========================================================================
  // UTILITIES
  // ==========================================================================

  private async request(method: string, endpoint: string, body?: any): Promise<any> {
    const url = `${this.config.baseUrl}/index.php?rest_route=${endpoint}`

    const options: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
        Authorization: this.authHeader,
      },
    }

    if (body && (method === 'POST' || method === 'PUT' || method === 'PATCH')) {
      options.body = JSON.stringify(body)
    }

    const response = await fetch(url, options)

    if (!response.ok) {
      const error = await response.text()
      throw new Error(`WordPress API error: ${response.status} ${error}`)
    }

    return response.json()
  }

  private buildQuery(params?: Record<string, any>): string {
    if (!params || Object.keys(params).length === 0) return ''

    const queryParams = new URLSearchParams()

    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        if (Array.isArray(value)) {
          queryParams.append(key, value.join(','))
        } else {
          queryParams.append(key, String(value))
        }
      }
    })

    return `?${queryParams.toString()}`
  }

  /**
   * Test connection to WordPress
   */
  async testConnection(): Promise<{ success: boolean; error?: string; info?: any }> {
    try {
      const settings = await this.getSettings()
      return {
        success: true,
        info: {
          title: settings.title,
          url: settings.url,
          description: settings.description
        }
      }
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      }
    }
  }
}

/**
 * Get WordPress operations manager instance
 */
export function getWordPressOperationsManager(): WordPressOperationsManager | null {
  const baseUrl = process.env.NEXT_PUBLIC_WORDPRESS_URL
  const consumerKey = process.env.NEXT_PUBLIC_WP_CONSUMER_KEY
  const consumerSecret = process.env.NEXT_PUBLIC_WP_CONSUMER_SECRET

  if (!baseUrl || !consumerKey || !consumerSecret) {
    console.warn('WordPress credentials not configured')
    return null
  }

  return new WordPressOperationsManager({
    baseUrl,
    consumerKey,
    consumerSecret
  })
}
