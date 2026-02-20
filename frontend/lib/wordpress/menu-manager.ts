/**
 * WordPress Menu Manager
 * Autonomous agent control of WordPress menus and navigation
 */

interface WooCommerceConfig {
  baseUrl: string
  consumerKey: string
  consumerSecret: string
}

interface MenuItem {
  id?: number
  title: string
  url: string
  menu_order: number
  parent?: number
  classes?: string[]
  target?: '_blank' | '_self'
  attr_title?: string
  description?: string
  object?: string // post, page, custom, category, etc.
  object_id?: number
  type?: 'post_type' | 'taxonomy' | 'custom'
  type_label?: string
}

interface Menu {
  id: number
  name: string
  slug: string
  description: string
  count: number
  locations: string[]
}

export class WordPressMenuManager {
  private config: WooCommerceConfig
  private authHeader: string

  constructor(config: WooCommerceConfig) {
    this.config = config
    const credentials = btoa(`${config.consumerKey}:${config.consumerSecret}`)
    this.authHeader = `Basic ${credentials}`
  }

  /**
   * Get all menus
   */
  async getMenus(): Promise<Menu[]> {
    const endpoint = `${this.config.baseUrl}/index.php?rest_route=/wp/v2/menus`
    const response = await fetch(endpoint, {
      headers: { Authorization: this.authHeader }
    })

    if (!response.ok) {
      throw new Error(`Failed to fetch menus: ${response.status}`)
    }

    return response.json()
  }

  /**
   * Get menu by location (primary, footer, etc.)
   */
  async getMenuByLocation(location: string): Promise<Menu | null> {
    const menus = await this.getMenus()
    return menus.find(menu => menu.locations.includes(location)) || null
  }

  /**
   * Get menu items for a specific menu
   */
  async getMenuItems(menuId: number): Promise<MenuItem[]> {
    const endpoint = `${this.config.baseUrl}/index.php?rest_route=/wp/v2/menu-items&menus=${menuId}`
    const response = await fetch(endpoint, {
      headers: { Authorization: this.authHeader }
    })

    if (!response.ok) {
      throw new Error(`Failed to fetch menu items: ${response.status}`)
    }

    return response.json()
  }

  /**
   * Create a new menu item
   */
  async createMenuItem(menuId: number, item: MenuItem): Promise<MenuItem> {
    const endpoint = `${this.config.baseUrl}/index.php?rest_route=/wp/v2/menu-items`

    const payload = {
      title: item.title,
      url: item.url,
      menus: menuId,
      menu_order: item.menu_order,
      parent: item.parent || 0,
      classes: item.classes || [],
      target: item.target || '_self',
      attr_title: item.attr_title || '',
      description: item.description || '',
      object: item.object || 'custom',
      object_id: item.object_id || 0,
      type: item.type || 'custom',
      type_label: item.type_label || 'Custom Link'
    }

    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: this.authHeader
      },
      body: JSON.stringify(payload)
    })

    if (!response.ok) {
      const error = await response.text()
      throw new Error(`Failed to create menu item: ${response.status} ${error}`)
    }

    return response.json()
  }

  /**
   * Update an existing menu item
   */
  async updateMenuItem(itemId: number, updates: Partial<MenuItem>): Promise<MenuItem> {
    const endpoint = `${this.config.baseUrl}/index.php?rest_route=/wp/v2/menu-items/${itemId}`

    const response = await fetch(endpoint, {
      method: 'POST', // WordPress uses POST for updates
      headers: {
        'Content-Type': 'application/json',
        Authorization: this.authHeader
      },
      body: JSON.stringify(updates)
    })

    if (!response.ok) {
      const error = await response.text()
      throw new Error(`Failed to update menu item: ${response.status} ${error}`)
    }

    return response.json()
  }

  /**
   * Delete a menu item
   */
  async deleteMenuItem(itemId: number): Promise<boolean> {
    const endpoint = `${this.config.baseUrl}/index.php?rest_route=/wp/v2/menu-items/${itemId}`

    const response = await fetch(endpoint, {
      method: 'DELETE',
      headers: {
        Authorization: this.authHeader,
        'X-WP-Force': 'true' // Force delete, skip trash
      }
    })

    if (!response.ok) {
      throw new Error(`Failed to delete menu item: ${response.status}`)
    }

    return true
  }

  /**
   * Reorder menu items
   */
  async reorderMenuItems(menuId: number, itemIds: number[]): Promise<boolean> {
    try {
      // Update menu_order for each item
      for (let i = 0; i < itemIds.length; i++) {
        await this.updateMenuItem(itemIds[i], { menu_order: i + 1 })
      }
      return true
    } catch (error) {
      console.error('Failed to reorder menu items:', error)
      return false
    }
  }

  /**
   * Add collection pages to menu (autonomous operation)
   */
  async addCollectionToMenu(
    menuId: number,
    collection: {
      name: string
      slug: string
      postId?: number
    }
  ): Promise<MenuItem> {
    const menuItems = await this.getMenuItems(menuId)
    const maxOrder = Math.max(...menuItems.map(item => item.menu_order), 0)

    return this.createMenuItem(menuId, {
      title: collection.name,
      url: `${this.config.baseUrl}/collection/${collection.slug}`,
      menu_order: maxOrder + 1,
      object: collection.postId ? 'page' : 'custom',
      object_id: collection.postId || 0,
      type: collection.postId ? 'post_type' : 'custom',
      classes: ['menu-collection', `collection-${collection.slug}`]
    })
  }

  /**
   * Autonomous menu sync - ensure all collections are in menu
   */
  async syncCollectionsToMenu(
    menuLocation: string,
    collections: Array<{ name: string; slug: string; postId?: number }>
  ): Promise<{
    success: boolean
    added: string[]
    errors: string[]
  }> {
    const result = {
      success: true,
      added: [] as string[],
      errors: [] as string[]
    }

    try {
      // Get menu by location
      const menu = await this.getMenuByLocation(menuLocation)
      if (!menu) {
        throw new Error(`Menu not found for location: ${menuLocation}`)
      }

      // Get existing items
      const existingItems = await this.getMenuItems(menu.id)
      const existingSlugs = new Set(
        existingItems
          .filter(item => item.classes?.some(c => c.startsWith('collection-')))
          .map(item => {
            const match = item.classes?.find(c => c.startsWith('collection-'))
            return match?.replace('collection-', '')
          })
          .filter(Boolean)
      )

      // Add missing collections
      for (const collection of collections) {
        if (!existingSlugs.has(collection.slug)) {
          try {
            await this.addCollectionToMenu(menu.id, collection)
            result.added.push(collection.slug)
          } catch (error) {
            result.errors.push(`Failed to add ${collection.slug}: ${error}`)
            result.success = false
          }
        }
      }

      return result
    } catch (error) {
      result.success = false
      result.errors.push(error instanceof Error ? error.message : 'Unknown error')
      return result
    }
  }
}

/**
 * Get WordPress menu manager instance
 */
export function getWordPressMenuManager(): WordPressMenuManager | null {
  const baseUrl = process.env.NEXT_PUBLIC_WORDPRESS_URL
  const consumerKey = process.env.NEXT_PUBLIC_WP_CONSUMER_KEY
  const consumerSecret = process.env.NEXT_PUBLIC_WP_CONSUMER_SECRET

  if (!baseUrl || !consumerKey || !consumerSecret) {
    console.warn('WordPress credentials not configured')
    return null
  }

  return new WordPressMenuManager({
    baseUrl,
    consumerKey,
    consumerSecret
  })
}
