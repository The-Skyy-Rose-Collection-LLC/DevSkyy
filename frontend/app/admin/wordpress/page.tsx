'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { getWordPressOperationsManager } from '@/lib/wordpress/operations-manager'
import { getWordPressMenuManager } from '@/lib/wordpress/menu-manager'
import { useWordPressAgent } from '@/lib/wordpress/agent-client'
import type {
  WPPostResponse,
  WPPageResponse,
  WPCategoryResponse,
  WPTagResponse,
  WPMediaResponse,
  WPUserResponse,
  WPMenuResponse,
  WPConnectionStatus,
} from '@/lib/wordpress/types'
import { WPErrorBoundary } from '@/components/admin/wp-error-boundary'
import {
  PostsSkeleton,
  PagesSkeleton,
  MediaSkeleton,
  CategoriesSkeleton,
  TagsSkeleton,
  UsersSkeleton,
} from '@/components/admin/wp-skeleton'
import {
  Globe,
  FileText,
  Image,
  Tag,
  Folder,
  User,
  Settings,
  Activity,
  Plus,
  RefreshCw,
  Trash2,
  Edit,
  CheckCircle2,
  XCircle,
  Bot,
  Square,
  ExternalLink,
  X
} from 'lucide-react'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type WPManager = ReturnType<typeof getWordPressOperationsManager>
type MenuManager = ReturnType<typeof getWordPressMenuManager>

interface CreateFormState {
  type: 'post' | 'page' | 'category' | 'tag' | null
  title: string
  content: string
  slug: string
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function WordPressAdminPage() {
  const [wpManager, setWpManager] = useState<WPManager | null>(null)
  const [menuManager, setMenuManager] = useState<MenuManager | null>(null)
  const [connectionStatus, setConnectionStatus] = useState<WPConnectionStatus | null>(null)
  const [loading, setLoading] = useState(false)
  const [opLoading, setOpLoading] = useState<string | null>(null)
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null)

  // Data state
  const [posts, setPosts] = useState<WPPostResponse[]>([])
  const [pages, setPages] = useState<WPPageResponse[]>([])
  const [categories, setCategories] = useState<WPCategoryResponse[]>([])
  const [tags, setTags] = useState<WPTagResponse[]>([])
  const [media, setMedia] = useState<WPMediaResponse[]>([])
  const [users, setUsers] = useState<WPUserResponse[]>([])
  const [menus, setMenus] = useState<WPMenuResponse[]>([])
  const [selectedCollection, setSelectedCollection] = useState('black-rose')

  // Create form
  const [createForm, setCreateForm] = useState<CreateFormState>({ type: null, title: '', content: '', slug: '' })

  // Media upload ref
  const fileInputRef = useRef<HTMLInputElement>(null)

  const { status: agentStatus, messages: agentMessages, execute: agentExecute, abort: agentAbort, reset: agentReset } = useWordPressAgent()

  // -------------------------------------------------------------------------
  // Toast helper
  // -------------------------------------------------------------------------

  const showToast = useCallback((message: string, type: 'success' | 'error' = 'success') => {
    setToast({ message, type })
    setTimeout(() => setToast(null), 4000)
  }, [])

  // -------------------------------------------------------------------------
  // Init
  // -------------------------------------------------------------------------

  useEffect(() => {
    const manager = getWordPressOperationsManager()
    const mManager = getWordPressMenuManager()
    setWpManager(manager)
    setMenuManager(mManager)
    if (manager) testConnection(manager)
  }, [])

  const testConnection = async (manager: WPManager) => {
    setLoading(true)
    try {
      const result = await manager.testConnection()
      setConnectionStatus(result)
      if (result.success) loadData(manager)
    } catch {
      setConnectionStatus({ success: false, error: 'Connection test failed' })
    }
    setLoading(false)
  }

  const loadData = async (manager: WPManager) => {
    try {
      const [postsData, pagesData, categoriesData, tagsData, mediaData] = await Promise.all([
        manager.listPosts({ per_page: 20 }),
        manager.listPages({ per_page: 20 }),
        manager.listCategories({ per_page: 50 }),
        manager.listTags({ per_page: 50 }),
        manager.listMedia({ per_page: 20 })
      ])
      setPosts(postsData)
      setPages(pagesData)
      setCategories(categoriesData)
      setTags(tagsData)
      setMedia(mediaData)
    } catch {
      showToast('Failed to load WordPress data', 'error')
    }
  }

  const loadMenus = async () => {
    if (!menuManager) return
    try {
      const menusData = await menuManager.getMenus()
      setMenus(menusData)
    } catch {
      showToast('Failed to load menus', 'error')
    }
  }

  // -------------------------------------------------------------------------
  // CRUD Handlers
  // -------------------------------------------------------------------------

  const handleCreate = async () => {
    if (!wpManager || !createForm.type || !createForm.title.trim()) return
    setOpLoading('create')
    try {
      const base = {
        title: createForm.title,
        content: createForm.content || '',
        status: 'draft' as const,
        ...(createForm.slug ? { slug: createForm.slug } : {}),
      }

      switch (createForm.type) {
        case 'post':
          await wpManager.createPost(base)
          setPosts(await wpManager.listPosts({ per_page: 20 }))
          break
        case 'page':
          await wpManager.createPage(base)
          setPages(await wpManager.listPages({ per_page: 20 }))
          break
        case 'category':
          await wpManager.createCategory({ name: createForm.title, slug: createForm.slug || undefined, description: createForm.content || undefined })
          setCategories(await wpManager.listCategories({ per_page: 50 }))
          break
        case 'tag':
          await wpManager.createTag({ name: createForm.title, slug: createForm.slug || undefined, description: createForm.content || undefined })
          setTags(await wpManager.listTags({ per_page: 50 }))
          break
      }
      setCreateForm({ type: null, title: '', content: '', slug: '' })
      showToast(`${createForm.type} created as draft`)
    } catch (e) {
      showToast(`Failed to create ${createForm.type}: ${e instanceof Error ? e.message : 'Unknown error'}`, 'error')
    }
    setOpLoading(null)
  }

  const handleDelete = async (type: 'post' | 'page' | 'category' | 'tag' | 'media', id: number, title: string) => {
    if (!wpManager) return
    if (!window.confirm(`Delete "${title}"? This cannot be undone.`)) return

    setOpLoading(`delete-${type}-${id}`)
    try {
      switch (type) {
        case 'post':
          await wpManager.deletePost(id, true)
          setPosts((prev) => prev.filter((p) => p.id !== id))
          break
        case 'page':
          await wpManager.deletePage(id, true)
          setPages((prev) => prev.filter((p) => p.id !== id))
          break
        case 'category':
          await wpManager.deleteCategory(id, true)
          setCategories((prev) => prev.filter((c) => c.id !== id))
          break
        case 'tag':
          await wpManager.deleteTag(id, true)
          setTags((prev) => prev.filter((t) => t.id !== id))
          break
        case 'media':
          await wpManager.deleteMedia(id, true)
          setMedia((prev) => prev.filter((m) => m.id !== id))
          break
      }
      showToast(`Deleted ${type}: ${title}`)
    } catch (e) {
      showToast(`Failed to delete: ${e instanceof Error ? e.message : 'Unknown error'}`, 'error')
    }
    setOpLoading(null)
  }

  const handleToggleStatus = async (type: 'post' | 'page', id: number, currentStatus: string) => {
    if (!wpManager) return
    const newStatus = currentStatus === 'publish' ? 'draft' : 'publish'
    setOpLoading(`status-${type}-${id}`)
    try {
      if (type === 'post') {
        await wpManager.updatePost(id, { status: newStatus as 'draft' | 'publish' })
        setPosts(await wpManager.listPosts({ per_page: 20 }))
      } else {
        await wpManager.updatePage(id, { status: newStatus as 'draft' | 'publish' })
        setPages(await wpManager.listPages({ per_page: 20 }))
      }
      showToast(`Status changed to ${newStatus}`)
    } catch (e) {
      showToast(`Failed to update status: ${e instanceof Error ? e.message : 'Unknown error'}`, 'error')
    }
    setOpLoading(null)
  }

  const handleMediaUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!wpManager || !e.target.files?.length) return
    const file = e.target.files[0]
    setOpLoading('upload')
    try {
      await wpManager.uploadMedia(file, { title: file.name })
      setMedia(await wpManager.listMedia({ per_page: 20 }))
      showToast(`Uploaded: ${file.name}`)
    } catch (err) {
      showToast(`Upload failed: ${err instanceof Error ? err.message : 'Unknown error'}`, 'error')
    }
    setOpLoading(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  // -------------------------------------------------------------------------
  // Create Form Inline
  // -------------------------------------------------------------------------

  const renderCreateForm = () => {
    if (!createForm.type) return null
    const isContent = createForm.type === 'post' || createForm.type === 'page'
    return (
      <Card className="border-rose-500/30 mb-4">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm capitalize">New {createForm.type}</CardTitle>
            <Button size="sm" variant="ghost" onClick={() => setCreateForm({ type: null, title: '', content: '', slug: '' })}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          <Input
            placeholder={isContent ? 'Title' : 'Name'}
            value={createForm.title}
            onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })}
            autoFocus
          />
          <Input
            placeholder="Slug (optional)"
            value={createForm.slug}
            onChange={(e) => setCreateForm({ ...createForm, slug: e.target.value })}
          />
          {isContent && (
            <Textarea
              placeholder="Content (HTML supported)"
              rows={4}
              value={createForm.content}
              onChange={(e) => setCreateForm({ ...createForm, content: e.target.value })}
            />
          )}
          {!isContent && (
            <Input
              placeholder="Description (optional)"
              value={createForm.content}
              onChange={(e) => setCreateForm({ ...createForm, content: e.target.value })}
            />
          )}
          <div className="flex justify-end gap-2">
            <Button size="sm" variant="outline" onClick={() => setCreateForm({ type: null, title: '', content: '', slug: '' })}>
              Cancel
            </Button>
            <Button size="sm" onClick={handleCreate} disabled={!createForm.title.trim() || opLoading === 'create'}>
              {opLoading === 'create' ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : <Plus className="mr-2 h-4 w-4" />}
              Create as Draft
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  // -------------------------------------------------------------------------
  // Render
  // -------------------------------------------------------------------------

  return (
    <WPErrorBoundary fallbackTitle="WordPress panel error">
    <div className="container mx-auto py-8 space-y-8">
      {/* Toast */}
      {toast && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg text-sm font-medium ${
          toast.type === 'success' ? 'bg-green-900/90 text-green-200 border border-green-700' : 'bg-red-900/90 text-red-200 border border-red-700'
        }`}>
          {toast.message}
        </div>
      )}

      {/* Hidden file input for media upload */}
      <input ref={fileInputRef} type="file" className="hidden" accept="image/*,video/*,audio/*,.pdf,.doc,.docx" onChange={handleMediaUpload} />

      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-4xl luxury-text-gradient">WordPress Operations</h1>
          <p className="text-gray-400 mt-2">Complete WordPress management via REST API</p>
        </div>
        <Button onClick={() => wpManager && testConnection(wpManager)} disabled={loading}>
          {loading ? (
            <><RefreshCw className="mr-2 h-4 w-4 animate-spin" />Testing...</>
          ) : (
            <><Activity className="mr-2 h-4 w-4" />Test Connection</>
          )}
        </Button>
      </div>

      {/* Connection Status */}
      {connectionStatus && (
        <Card className={connectionStatus.success ? 'border-green-500/30' : 'border-red-500/30'}>
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              {connectionStatus.success ? (
                <CheckCircle2 className="h-5 w-5 text-green-400" />
              ) : (
                <XCircle className="h-5 w-5 text-red-400" />
              )}
              <div className="flex-1">
                <p className="font-semibold">
                  {connectionStatus.success ? 'Connected to WordPress' : 'Connection Failed'}
                </p>
                {connectionStatus.success && connectionStatus.info && (
                  <p className="text-sm text-gray-400">
                    {connectionStatus.info.title} - {connectionStatus.info.url}
                  </p>
                )}
                {connectionStatus.error && (
                  <p className="text-sm text-red-400">{connectionStatus.error}</p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Operations Tabs */}
      <Tabs defaultValue="posts" className="space-y-6">
        <TabsList className="grid grid-cols-8 w-full">
          <TabsTrigger value="posts"><FileText className="mr-2 h-4 w-4" />Posts</TabsTrigger>
          <TabsTrigger value="pages"><FileText className="mr-2 h-4 w-4" />Pages</TabsTrigger>
          <TabsTrigger value="media"><Image className="mr-2 h-4 w-4" />Media</TabsTrigger>
          <TabsTrigger value="categories"><Folder className="mr-2 h-4 w-4" />Categories</TabsTrigger>
          <TabsTrigger value="tags"><Tag className="mr-2 h-4 w-4" />Tags</TabsTrigger>
          <TabsTrigger value="users"><User className="mr-2 h-4 w-4" />Users</TabsTrigger>
          <TabsTrigger value="menus" onClick={loadMenus}><Globe className="mr-2 h-4 w-4" />Menus</TabsTrigger>
          <TabsTrigger value="agent"><Bot className="mr-2 h-4 w-4" />Agent</TabsTrigger>
        </TabsList>

        {/* ================================================================ */}
        {/* Posts */}
        {/* ================================================================ */}
        <TabsContent value="posts">
          {createForm.type === 'post' && renderCreateForm()}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Posts</CardTitle>
                  <CardDescription>Manage WordPress posts ({posts.length} loaded)</CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" onClick={() => wpManager && loadData(wpManager)}>
                    <RefreshCw className="mr-2 h-4 w-4" />Refresh
                  </Button>
                  <Button size="sm" onClick={() => setCreateForm({ type: 'post', title: '', content: '', slug: '' })}>
                    <Plus className="mr-2 h-4 w-4" />Create Post
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {loading && posts.length === 0 ? (
                <PostsSkeleton />
              ) : posts.length === 0 ? (
                <p className="text-gray-500">No posts found</p>
              ) : (
                <div className="space-y-3">
                  {posts.map((post) => (
                    <div key={post.id} className="flex items-center justify-between p-3 rounded-lg bg-gray-900/50 border border-gray-800">
                      <div className="min-w-0 flex-1">
                        <p className="font-semibold truncate">{post.title?.rendered || 'Untitled'}</p>
                        <div className="flex gap-2 mt-1">
                          <Badge variant="outline" className={`text-xs ${post.status === 'publish' ? 'border-green-600 text-green-400' : ''}`}>
                            {post.status}
                          </Badge>
                          <span className="text-xs text-gray-400">{new Date(post.date).toLocaleDateString()}</span>
                        </div>
                      </div>
                      <div className="flex gap-2 ml-3">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleToggleStatus('post', post.id, post.status)}
                          disabled={opLoading === `status-post-${post.id}`}
                          title={post.status === 'publish' ? 'Unpublish' : 'Publish'}
                        >
                          {post.status === 'publish' ? <XCircle className="h-4 w-4" /> : <CheckCircle2 className="h-4 w-4" />}
                        </Button>
                        {post.link && (
                          <Button size="sm" variant="outline" asChild title="View on site">
                            <a href={post.link} target="_blank" rel="noopener noreferrer"><ExternalLink className="h-4 w-4" /></a>
                          </Button>
                        )}
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleDelete('post', post.id, post.title?.rendered || 'Untitled')}
                          disabled={opLoading === `delete-post-${post.id}`}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ================================================================ */}
        {/* Pages */}
        {/* ================================================================ */}
        <TabsContent value="pages">
          {createForm.type === 'page' && renderCreateForm()}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Pages</CardTitle>
                  <CardDescription>Manage WordPress pages ({pages.length} loaded)</CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" onClick={() => wpManager && loadData(wpManager)}>
                    <RefreshCw className="mr-2 h-4 w-4" />Refresh
                  </Button>
                  <Button size="sm" onClick={() => setCreateForm({ type: 'page', title: '', content: '', slug: '' })}>
                    <Plus className="mr-2 h-4 w-4" />Create Page
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {loading && pages.length === 0 ? (
                <PagesSkeleton />
              ) : pages.length === 0 ? (
                <p className="text-gray-500">No pages found</p>
              ) : (
                <div className="space-y-3">
                  {pages.map((page) => (
                    <div key={page.id} className="flex items-center justify-between p-3 rounded-lg bg-gray-900/50 border border-gray-800">
                      <div className="min-w-0 flex-1">
                        <p className="font-semibold truncate">{page.title?.rendered || 'Untitled'}</p>
                        <div className="flex gap-2 mt-1">
                          <Badge variant="outline" className={`text-xs ${page.status === 'publish' ? 'border-green-600 text-green-400' : ''}`}>
                            {page.status}
                          </Badge>
                          {page.template && <Badge variant="outline" className="text-xs">{page.template}</Badge>}
                        </div>
                      </div>
                      <div className="flex gap-2 ml-3">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleToggleStatus('page', page.id, page.status)}
                          disabled={opLoading === `status-page-${page.id}`}
                          title={page.status === 'publish' ? 'Unpublish' : 'Publish'}
                        >
                          {page.status === 'publish' ? <XCircle className="h-4 w-4" /> : <CheckCircle2 className="h-4 w-4" />}
                        </Button>
                        {page.link && (
                          <Button size="sm" variant="outline" asChild title="View on site">
                            <a href={page.link} target="_blank" rel="noopener noreferrer"><ExternalLink className="h-4 w-4" /></a>
                          </Button>
                        )}
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleDelete('page', page.id, page.title?.rendered || 'Untitled')}
                          disabled={opLoading === `delete-page-${page.id}`}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ================================================================ */}
        {/* Media */}
        {/* ================================================================ */}
        <TabsContent value="media">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Media Library</CardTitle>
                  <CardDescription>Upload and manage media files ({media.length} loaded)</CardDescription>
                </div>
                <div className="flex gap-2">
                  <Button size="sm" variant="outline" onClick={() => wpManager && loadData(wpManager)}>
                    <RefreshCw className="mr-2 h-4 w-4" />Refresh
                  </Button>
                  <Button
                    size="sm"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={opLoading === 'upload'}
                  >
                    {opLoading === 'upload' ? (
                      <><RefreshCw className="mr-2 h-4 w-4 animate-spin" />Uploading...</>
                    ) : (
                      <><Plus className="mr-2 h-4 w-4" />Upload Media</>
                    )}
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {loading && media.length === 0 ? (
                <MediaSkeleton />
              ) : media.length === 0 ? (
                <p className="text-gray-500">No media files found</p>
              ) : (
                <div className="grid grid-cols-4 gap-4">
                  {media.map((item) => (
                    <div key={item.id} className="relative group rounded-lg overflow-hidden border border-gray-800 hover:border-rose-500/30">
                      {item.source_url ? (
                        <img src={item.source_url} alt={item.alt_text || 'Media'} className="w-full h-32 object-cover" />
                      ) : (
                        <div className="w-full h-32 bg-gray-800 flex items-center justify-center text-gray-500">
                          <FileText className="h-8 w-8" />
                        </div>
                      )}
                      <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                        {item.source_url && (
                          <Button size="sm" variant="outline" asChild>
                            <a href={item.source_url} target="_blank" rel="noopener noreferrer"><ExternalLink className="h-4 w-4" /></a>
                          </Button>
                        )}
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleDelete('media', item.id, item.title?.rendered || 'Media')}
                          disabled={opLoading === `delete-media-${item.id}`}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                      <p className="text-xs text-gray-400 p-1 truncate">{item.title?.rendered || 'Untitled'}</p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ================================================================ */}
        {/* Categories */}
        {/* ================================================================ */}
        <TabsContent value="categories">
          {createForm.type === 'category' && renderCreateForm()}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Categories</CardTitle>
                  <CardDescription>Manage post categories ({categories.length} loaded)</CardDescription>
                </div>
                <Button size="sm" onClick={() => setCreateForm({ type: 'category', title: '', content: '', slug: '' })}>
                  <Plus className="mr-2 h-4 w-4" />Create Category
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {loading && categories.length === 0 ? (
                <CategoriesSkeleton />
              ) : categories.length === 0 ? (
                <p className="text-gray-500">No categories found</p>
              ) : (
                <div className="space-y-2">
                  {categories.map((category) => (
                    <div key={category.id} className="flex items-center justify-between p-2 rounded bg-gray-900/50">
                      <div>
                        <span className="font-medium">{category.name}</span>
                        <span className="text-sm text-gray-400 ml-2">({category.count} posts)</span>
                        {category.slug && <span className="text-xs text-gray-500 ml-2">/{category.slug}</span>}
                      </div>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleDelete('category', category.id, category.name)}
                        disabled={opLoading === `delete-category-${category.id}` || category.id === 1}
                        title={category.id === 1 ? 'Cannot delete default category' : 'Delete'}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ================================================================ */}
        {/* Tags */}
        {/* ================================================================ */}
        <TabsContent value="tags">
          {createForm.type === 'tag' && renderCreateForm()}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Tags</CardTitle>
                  <CardDescription>Manage post tags ({tags.length} loaded)</CardDescription>
                </div>
                <Button size="sm" onClick={() => setCreateForm({ type: 'tag', title: '', content: '', slug: '' })}>
                  <Plus className="mr-2 h-4 w-4" />Create Tag
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {loading && tags.length === 0 ? (
                <TagsSkeleton />
              ) : tags.length === 0 ? (
                <p className="text-gray-500">No tags found</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {tags.map((tag) => (
                    <Badge
                      key={tag.id}
                      variant="outline"
                      className="px-3 py-1 group cursor-default"
                    >
                      {tag.name} ({tag.count})
                      <button
                        className="ml-2 opacity-0 group-hover:opacity-100 transition-opacity"
                        onClick={() => handleDelete('tag', tag.id, tag.name)}
                        disabled={opLoading === `delete-tag-${tag.id}`}
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ================================================================ */}
        {/* Users */}
        {/* ================================================================ */}
        <TabsContent value="users">
          <Card>
            <CardHeader>
              <CardTitle>Users</CardTitle>
              <CardDescription>WordPress user list (read-only)</CardDescription>
            </CardHeader>
            <CardContent>
              {users.length === 0 ? (
                <div className="space-y-3">
                  <p className="text-gray-500">Click Refresh to load users</p>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={async () => {
                      if (!wpManager) return
                      try {
                        setUsers(await wpManager.listUsers({ per_page: 20 }))
                      } catch {
                        showToast('Failed to load users', 'error')
                      }
                    }}
                  >
                    <RefreshCw className="mr-2 h-4 w-4" />Load Users
                  </Button>
                </div>
              ) : (
                <div className="space-y-2">
                  {users.map((user) => (
                    <div key={user.id} className="flex items-center justify-between p-2 rounded bg-gray-900/50">
                      <div className="flex items-center gap-3">
                        {user.avatar_urls?.['48'] && (
                          <img src={user.avatar_urls['48']} alt="" className="w-8 h-8 rounded-full" />
                        )}
                        <div>
                          <span className="font-medium">{user.name}</span>
                          {(user.roles?.length ?? 0) > 0 && (
                            <Badge variant="outline" className="ml-2 text-xs">{user.roles![0]}</Badge>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ================================================================ */}
        {/* Menus */}
        {/* ================================================================ */}
        <TabsContent value="menus">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Navigation Menus</CardTitle>
                  <CardDescription>Manage WordPress navigation menus</CardDescription>
                </div>
                <Button size="sm" onClick={loadMenus}>
                  <RefreshCw className="mr-2 h-4 w-4" />Refresh
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {menus.length === 0 ? (
                <p className="text-gray-500">No menus found (click Refresh)</p>
              ) : (
                <div className="space-y-3">
                  {menus.map((menu) => (
                    <div key={menu.id} className="p-3 rounded-lg bg-gray-900/50 border border-gray-800">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-semibold">{menu.name}</p>
                          <p className="text-sm text-gray-400">
                            {menu.count} items{' '}
                            {(menu.locations?.length ?? 0) > 0 && <>· Locations: {menu.locations!.join(', ')}</>}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* ================================================================ */}
        {/* Agent */}
        {/* ================================================================ */}
        <TabsContent value="agent">
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Agent Actions</CardTitle>
                <CardDescription>AI-powered WordPress operations via Claude Agent SDK</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-3 gap-3">
                  <Button
                    onClick={() => agentExecute("health_check", "Check WordPress and WooCommerce connectivity. Report site status, API version, and any issues.")}
                    disabled={agentStatus === "running"}
                    variant="outline"
                  >
                    <Activity className="mr-2 h-4 w-4" />Health Check
                  </Button>
                  <Button
                    onClick={() => agentExecute("sync_collection", `Sync all ${selectedCollection} products to WooCommerce. First check connectivity with wp_health_check, then use wp_sync_collection.`, { collection: selectedCollection })}
                    disabled={agentStatus === "running"}
                    variant="outline"
                  >
                    <RefreshCw className="mr-2 h-4 w-4" />Sync Collection
                  </Button>
                  <Button
                    onClick={() => agentExecute("get_pipeline_status", "Get the current status of all 9 dashboard pipelines.")}
                    disabled={agentStatus === "running"}
                    variant="outline"
                  >
                    <Settings className="mr-2 h-4 w-4" />Pipeline Status
                  </Button>
                </div>

                <div className="flex items-center gap-3">
                  <span className="text-sm text-gray-400">Collection:</span>
                  {["black-rose", "love-hurts", "signature"].map((col) => (
                    <Button
                      key={col}
                      size="sm"
                      variant={selectedCollection === col ? "default" : "outline"}
                      onClick={() => setSelectedCollection(col)}
                      className="capitalize"
                    >
                      {col.replace("-", " ")}
                    </Button>
                  ))}
                </div>

                <div className="flex gap-2">
                  <Input
                    placeholder="Ask the agent anything about WordPress..."
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && e.currentTarget.value.trim()) {
                        agentExecute("custom", e.currentTarget.value.trim())
                        e.currentTarget.value = ""
                      }
                    }}
                    disabled={agentStatus === "running"}
                    className="flex-1"
                  />
                  {agentStatus === "running" && (
                    <Button variant="destructive" onClick={agentAbort}>
                      <Square className="mr-2 h-4 w-4" />Stop
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>

            {agentMessages.length > 0 && (
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-sm">Agent Output</CardTitle>
                    <div className="flex items-center gap-2">
                      {agentStatus === "running" && (
                        <Badge className="bg-blue-500/20 text-blue-400 animate-pulse">Running...</Badge>
                      )}
                      {agentStatus === "done" && (
                        <Badge className="bg-green-500/20 text-green-400">Complete</Badge>
                      )}
                      {agentStatus === "error" && (
                        <Badge className="bg-red-500/20 text-red-400">Error</Badge>
                      )}
                      <Button size="sm" variant="ghost" onClick={agentReset}>Clear</Button>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2 max-h-96 overflow-y-auto font-mono text-sm">
                    {agentMessages.map((msg, i) => (
                      <div
                        key={i}
                        className={`p-2 rounded ${
                          msg.type === "thinking"
                            ? "bg-gray-800/50 text-gray-400 italic"
                            : msg.type === "tool_use"
                              ? "bg-blue-900/20 text-blue-300"
                              : msg.type === "error"
                                ? "bg-red-900/20 text-red-300"
                                : msg.type === "result"
                                  ? "bg-green-900/20 text-green-300"
                                  : "bg-gray-900/50 text-gray-200"
                        }`}
                      >
                        <span className="text-xs uppercase text-gray-500 mr-2">[{msg.type}]</span>
                        {msg.tool && <Badge variant="outline" className="mr-2 text-xs">{msg.tool}</Badge>}
                        {msg.content}
                        {msg.cost_usd !== undefined && msg.cost_usd !== null && (
                          <span className="text-xs text-gray-500 ml-2">(${msg.cost_usd.toFixed(3)})</span>
                        )}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>
      </Tabs>
    </div>
    </WPErrorBoundary>
  )
}
