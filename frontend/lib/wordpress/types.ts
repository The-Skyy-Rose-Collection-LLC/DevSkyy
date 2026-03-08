/**
 * WordPress REST API Response Types
 *
 * These represent what the WP REST API returns (not input shapes).
 * Used for type-safe rendering in the admin dashboard.
 */

export interface WPRenderedField {
  raw?: string
  rendered: string
}

export interface WPPostResponse {
  id: number
  title: WPRenderedField
  content: WPRenderedField
  excerpt?: WPRenderedField
  status: 'draft' | 'publish' | 'pending' | 'private' | 'future'
  date: string
  date_gmt?: string
  slug: string
  link?: string
  author?: number
  featured_media?: number
  categories?: number[]
  tags?: number[]
}

export interface WPPageResponse {
  id: number
  title: WPRenderedField
  content: WPRenderedField
  status: 'draft' | 'publish' | 'pending' | 'private'
  date?: string
  slug: string
  link?: string
  template?: string
  parent?: number
  menu_order?: number
}

export interface WPCategoryResponse {
  id: number
  name: string
  slug: string
  description?: string
  count: number
  parent?: number
}

export interface WPTagResponse {
  id: number
  name: string
  slug: string
  description?: string
  count: number
}

export interface WPMediaResponse {
  id: number
  title: WPRenderedField
  alt_text?: string
  caption?: WPRenderedField
  source_url?: string
  media_type?: 'image' | 'video' | 'audio' | 'application'
  mime_type?: string
}

export interface WPUserResponse {
  id: number
  name: string
  slug: string
  roles?: string[]
  avatar_urls?: Record<string, string>
  url?: string
  description?: string
}

export interface WPMenuResponse {
  id: number
  name: string
  slug?: string
  count: number
  locations?: string[]
}

export interface WPConnectionStatus {
  success: boolean
  error?: string
  info?: {
    title?: string
    url?: string
    description?: string
  }
}
