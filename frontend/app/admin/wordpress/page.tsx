'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { getWordPressOperationsManager } from '@/lib/wordpress/operations-manager'
import { getWordPressMenuManager } from '@/lib/wordpress/menu-manager'
import {
  Globe,
  FileText,
  Image,
  Tag,
  Folder,
  User,
  MessageSquare,
  Settings,
  Activity,
  Plus,
  RefreshCw,
  Trash2,
  Edit,
  CheckCircle2,
  XCircle
} from 'lucide-react'

export default function WordPressAdminPage() {
  const [wpManager, setWpManager] = useState<any>(null)
  const [menuManager, setMenuManager] = useState<any>(null)
  const [connectionStatus, setConnectionStatus] = useState<any>(null)
  const [loading, setLoading] = useState(false)

  // State for different operations
  const [posts, setPosts] = useState<any[]>([])
  const [pages, setPages] = useState<any[]>([])
  const [categories, setCategories] = useState<any[]>([])
  const [tags, setTags] = useState<any[]>([])
  const [media, setMedia] = useState<any[]>([])
  const [users, setUsers] = useState<any[]>([])
  const [menus, setMenus] = useState<any[]>([])

  useEffect(() => {
    const manager = getWordPressOperationsManager()
    const mManager = getWordPressMenuManager()

    setWpManager(manager)
    setMenuManager(mManager)

    if (manager) {
      testConnection(manager)
    }
  }, [])

  const testConnection = async (manager: any) => {
    setLoading(true)
    const result = await manager.testConnection()
    setConnectionStatus(result)
    setLoading(false)

    if (result.success) {
      // Load initial data
      loadData(manager)
    }
  }

  const loadData = async (manager: any) => {
    try {
      const [postsData, pagesData, categoriesData, tagsData, mediaData] = await Promise.all([
        manager.listPosts({ per_page: 10 }),
        manager.listPages({ per_page: 10 }),
        manager.listCategories({ per_page: 10 }),
        manager.listTags({ per_page: 10 }),
        manager.listMedia({ per_page: 10 })
      ])

      setPosts(postsData)
      setPages(pagesData)
      setCategories(categoriesData)
      setTags(tagsData)
      setMedia(mediaData)
    } catch (error) {
      console.error('Failed to load WordPress data:', error)
    }
  }

  const loadMenus = async () => {
    if (!menuManager) return
    try {
      const menusData = await menuManager.getMenus()
      setMenus(menusData)
    } catch (error) {
      console.error('Failed to load menus:', error)
    }
  }

  return (
    <div className="container mx-auto py-8 space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-4xl luxury-text-gradient">
            WordPress Operations
          </h1>
          <p className="text-gray-400 mt-2">
            Complete WordPress management via REST API
          </p>
        </div>
        <Button
          onClick={() => wpManager && testConnection(wpManager)}
          disabled={loading}
        >
          {loading ? (
            <>
              <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
              Testing...
            </>
          ) : (
            <>
              <Activity className="mr-2 h-4 w-4" />
              Test Connection
            </>
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
        <TabsList className="grid grid-cols-7 w-full">
          <TabsTrigger value="posts">
            <FileText className="mr-2 h-4 w-4" />
            Posts
          </TabsTrigger>
          <TabsTrigger value="pages">
            <FileText className="mr-2 h-4 w-4" />
            Pages
          </TabsTrigger>
          <TabsTrigger value="media">
            <Image className="mr-2 h-4 w-4" />
            Media
          </TabsTrigger>
          <TabsTrigger value="categories">
            <Folder className="mr-2 h-4 w-4" />
            Categories
          </TabsTrigger>
          <TabsTrigger value="tags">
            <Tag className="mr-2 h-4 w-4" />
            Tags
          </TabsTrigger>
          <TabsTrigger value="users">
            <User className="mr-2 h-4 w-4" />
            Users
          </TabsTrigger>
          <TabsTrigger value="menus" onClick={loadMenus}>
            <Globe className="mr-2 h-4 w-4" />
            Menus
          </TabsTrigger>
        </TabsList>

        {/* Posts */}
        <TabsContent value="posts">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Posts</CardTitle>
                  <CardDescription>Manage WordPress posts</CardDescription>
                </div>
                <Button size="sm">
                  <Plus className="mr-2 h-4 w-4" />
                  Create Post
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {posts.length === 0 ? (
                <p className="text-gray-500">No posts found</p>
              ) : (
                <div className="space-y-3">
                  {posts.map((post) => (
                    <div
                      key={post.id}
                      className="flex items-center justify-between p-3 rounded-lg bg-gray-900/50 border border-gray-800"
                    >
                      <div>
                        <p className="font-semibold">
                          {post.title?.rendered || 'Untitled'}
                        </p>
                        <div className="flex gap-2 mt-1">
                          <Badge variant="outline" className="text-xs">
                            {post.status}
                          </Badge>
                          <span className="text-xs text-gray-400">
                            {new Date(post.date).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button size="sm" variant="outline">
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button size="sm" variant="outline">
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

        {/* Pages */}
        <TabsContent value="pages">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Pages</CardTitle>
                  <CardDescription>Manage WordPress pages</CardDescription>
                </div>
                <Button size="sm">
                  <Plus className="mr-2 h-4 w-4" />
                  Create Page
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {pages.length === 0 ? (
                <p className="text-gray-500">No pages found</p>
              ) : (
                <div className="space-y-3">
                  {pages.map((page) => (
                    <div
                      key={page.id}
                      className="flex items-center justify-between p-3 rounded-lg bg-gray-900/50 border border-gray-800"
                    >
                      <div>
                        <p className="font-semibold">
                          {page.title?.rendered || 'Untitled'}
                        </p>
                        <div className="flex gap-2 mt-1">
                          <Badge variant="outline" className="text-xs">
                            {page.status}
                          </Badge>
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button size="sm" variant="outline">
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button size="sm" variant="outline">
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

        {/* Media */}
        <TabsContent value="media">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Media Library</CardTitle>
                  <CardDescription>Upload and manage media files</CardDescription>
                </div>
                <Button size="sm">
                  <Plus className="mr-2 h-4 w-4" />
                  Upload Media
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {media.length === 0 ? (
                <p className="text-gray-500">No media files found</p>
              ) : (
                <div className="grid grid-cols-4 gap-4">
                  {media.map((item) => (
                    <div
                      key={item.id}
                      className="relative group rounded-lg overflow-hidden border border-gray-800 hover:border-rose-500/30"
                    >
                      <img
                        src={item.source_url}
                        alt={item.alt_text || 'Media'}
                        className="w-full h-32 object-cover"
                      />
                      <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                        <Button size="sm" variant="outline">
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button size="sm" variant="outline">
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

        {/* Categories */}
        <TabsContent value="categories">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Categories</CardTitle>
                  <CardDescription>Manage post categories</CardDescription>
                </div>
                <Button size="sm">
                  <Plus className="mr-2 h-4 w-4" />
                  Create Category
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {categories.length === 0 ? (
                <p className="text-gray-500">No categories found</p>
              ) : (
                <div className="space-y-2">
                  {categories.map((category) => (
                    <div
                      key={category.id}
                      className="flex items-center justify-between p-2 rounded bg-gray-900/50"
                    >
                      <div>
                        <span className="font-medium">{category.name}</span>
                        <span className="text-sm text-gray-400 ml-2">
                          ({category.count} posts)
                        </span>
                      </div>
                      <div className="flex gap-2">
                        <Button size="sm" variant="ghost">
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button size="sm" variant="ghost">
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

        {/* Tags */}
        <TabsContent value="tags">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Tags</CardTitle>
                  <CardDescription>Manage post tags</CardDescription>
                </div>
                <Button size="sm">
                  <Plus className="mr-2 h-4 w-4" />
                  Create Tag
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {tags.map((tag) => (
                  <Badge key={tag.id} variant="outline" className="px-3 py-1">
                    {tag.name} ({tag.count})
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Users */}
        <TabsContent value="users">
          <Card>
            <CardHeader>
              <CardTitle>Users</CardTitle>
              <CardDescription>Manage WordPress users</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-gray-500">User management operations available via API</p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Menus */}
        <TabsContent value="menus">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Navigation Menus</CardTitle>
                  <CardDescription>Manage WordPress navigation menus</CardDescription>
                </div>
                <Button size="sm" onClick={loadMenus}>
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Refresh
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {menus.length === 0 ? (
                <p className="text-gray-500">No menus found</p>
              ) : (
                <div className="space-y-3">
                  {menus.map((menu) => (
                    <div
                      key={menu.id}
                      className="p-3 rounded-lg bg-gray-900/50 border border-gray-800"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-semibold">{menu.name}</p>
                          <p className="text-sm text-gray-400">
                            {menu.count} items • Locations: {menu.locations.join(', ') || 'None'}
                          </p>
                        </div>
                        <Button size="sm" variant="outline">
                          <Edit className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
