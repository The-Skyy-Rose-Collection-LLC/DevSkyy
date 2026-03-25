/**
 * WordPress Menu Manager
 * Autonomous agent control of WordPress menus and navigation
 */

import { wpProxyFetch } from './proxy-client'

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
  private siteUrl: string

  constructor(config: { baseUrl?: string } = {}) {
    this.siteUrl = config.baseUrl ?? ''
  }

  /**
   * Get all menus
   */
  async getMenus(): Promise<Menu[]> {
    return wpProxyFetch('GET', '/wp/v2/menus')
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
    return wpProxyFetch('GET', `/wp/v2/menu-items?menus=${menuId}`)
  }

  /**
   * Create a new menu item
   */
  async createMenuItem(menuId: number, item: MenuItem): Promise<MenuItem> {
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

    return wpProxyFetch('POST', '/wp/v2/menu-items', payload)
  }

  /**
   * Update an existing menu item
   */
  async updateMenuItem(itemId: number, updates: Partial<MenuItem>): Promise<MenuItem> {
    return wpProxyFetch('POST', `/wp/v2/menu-items/${itemId}`, updates)
  }

  /**
   * Delete a menu item
   */
  async deleteMenuItem(itemId: number): Promise<boolean> {
    await wpProxyFetch('DELETE', `/wp/v2/menu-items/${itemId}`)
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
      url: `${this.siteUrl}/collection/${collection.slug}`,
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
 * Get WordPress menu manager instance.
 * Credentials are handled server-side by /api/wordpress/proxy.
 */
export function getWordPressMenuManager(): WordPressMenuManager {
  return new WordPressMenuManager({
    baseUrl: process.env.NEXT_PUBLIC_WORDPRESS_URL,
  })
}
