/**
 * WordPress Management Page
 * =========================
 * Centralized interface for managing WordPress content, WooCommerce products,
 * and syncing between DevSkyy and WordPress.
 */

'use client';

import { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui';
import {
  Globe,
  FileText,
  ShoppingCart,
  Image as ImageIcon,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Clock,
  ExternalLink,
  Upload,
  Download
} from 'lucide-react';

// WordPress status interface
interface WordPressStatus {
  connected: boolean;
  site_url: string;
  last_sync: string;
  pages_count: number;
  products_count: number;
  media_count: number;
}

// WordPress page interface
interface WordPressPage {
  id: number;
  title: string;
  slug: string;
  status: string;
  link: string;
  modified: string;
}

// WooCommerce product interface
interface WooCommerceProduct {
  id: number;
  name: string;
  slug: string;
  price: string;
  status: string;
  stock_status: string;
  link: string;
}

export default function WordPressPage() {
  const [activeTab, setActiveTab] = useState<'overview' | 'pages' | 'products' | 'media' | 'sync'>('overview');
  const [status, setStatus] = useState<WordPressStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [pages, setPages] = useState<WordPressPage[]>([]);
  const [products, setProducts] = useState<WooCommerceProduct[]>([]);

  // Fetch WordPress status
  useEffect(() => {
    fetchStatus();
  }, []);

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/wordpress/status`);
      if (response.ok) {
        const data = await response.json();
        setStatus(data);
      }
    } catch (error) {
      console.error('Failed to fetch WordPress status:', error);
    } finally {
      setLoading(false);
    }
  };

  // Fetch pages
  const fetchPages = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/wordpress/pages`);
      if (response.ok) {
        const data = await response.json();
        setPages(data);
      }
    } catch (error) {
      console.error('Failed to fetch pages:', error);
    }
  };

  // Fetch products
  const fetchProducts = async () => {
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/wordpress/products`);
      if (response.ok) {
        const data = await response.json();
        setProducts(data);
      }
    } catch (error) {
      console.error('Failed to fetch products:', error);
    }
  };

  // Trigger sync
  const handleSync = async () => {
    setSyncing(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/wordpress/sync`, {
        method: 'POST',
      });
      if (response.ok) {
        await fetchStatus();
        if (activeTab === 'pages') await fetchPages();
        if (activeTab === 'products') await fetchProducts();
      }
    } catch (error) {
      console.error('Sync failed:', error);
    } finally {
      setSyncing(false);
    }
  };

  // Load data when tab changes
  useEffect(() => {
    if (activeTab === 'pages' && pages.length === 0) {
      fetchPages();
    }
    if (activeTab === 'products' && products.length === 0) {
      fetchProducts();
    }
  }, [activeTab]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Globe className="h-8 w-8" />
            WordPress Management
          </h1>
          <p className="text-gray-500 mt-1">
            Manage WordPress content, WooCommerce products, and sync status
          </p>
        </div>

        <button
          onClick={handleSync}
          disabled={syncing || loading}
          className="flex items-center gap-2 px-4 py-2 bg-brand-primary text-white rounded-lg hover:bg-brand-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <RefreshCw className={`h-4 w-4 ${syncing ? 'animate-spin' : ''}`} />
          {syncing ? 'Syncing...' : 'Sync Now'}
        </button>
      </div>

      {/* Status Banner */}
      {status && (
        <Card className={`border-2 ${status.connected ? 'border-green-500 bg-green-50 dark:bg-green-900/10' : 'border-red-500 bg-red-50 dark:bg-red-900/10'}`}>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {status.connected ? (
                  <CheckCircle2 className="h-6 w-6 text-green-600" />
                ) : (
                  <XCircle className="h-6 w-6 text-red-600" />
                )}
                <div>
                  <p className="font-semibold">
                    {status.connected ? 'Connected to WordPress' : 'WordPress Connection Failed'}
                  </p>
                  <p className="text-sm text-gray-600">
                    {status.site_url}
                  </p>
                </div>
              </div>
              <a
                href={status.site_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-brand-primary hover:underline"
              >
                Visit Site <ExternalLink className="h-4 w-4" />
              </a>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <div className="flex gap-2 border-b border-gray-200 dark:border-gray-700">
        {[
          { id: 'overview', label: 'Overview', icon: Globe },
          { id: 'pages', label: 'Pages', icon: FileText },
          { id: 'products', label: 'Products', icon: ShoppingCart },
          { id: 'media', label: 'Media', icon: ImageIcon },
          { id: 'sync', label: 'Sync', icon: RefreshCw },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-colors ${
              activeTab === tab.id
                ? 'border-brand-primary text-brand-primary'
                : 'border-transparent text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100'
            }`}
          >
            <tab.icon className="h-4 w-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="mt-6">
        {activeTab === 'overview' && (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {/* Stats Cards */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <FileText className="h-8 w-8 text-blue-500" />
                  <span className="text-3xl font-bold">{status?.pages_count || 0}</span>
                </div>
                <CardTitle className="text-lg">WordPress Pages</CardTitle>
                <CardDescription>Total published pages</CardDescription>
              </CardHeader>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <ShoppingCart className="h-8 w-8 text-green-500" />
                  <span className="text-3xl font-bold">{status?.products_count || 0}</span>
                </div>
                <CardTitle className="text-lg">WooCommerce Products</CardTitle>
                <CardDescription>Total products in store</CardDescription>
              </CardHeader>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <ImageIcon className="h-8 w-8 text-purple-500" />
                  <span className="text-3xl font-bold">{status?.media_count || 0}</span>
                </div>
                <CardTitle className="text-lg">Media Items</CardTitle>
                <CardDescription>Images and attachments</CardDescription>
              </CardHeader>
            </Card>

            {/* Last Sync */}
            <Card className="md:col-span-2 lg:col-span-3">
              <CardHeader>
                <div className="flex items-center gap-3">
                  <Clock className="h-6 w-6 text-gray-500" />
                  <div>
                    <CardTitle>Last Sync</CardTitle>
                    <CardDescription>
                      {status?.last_sync
                        ? new Date(status.last_sync).toLocaleString()
                        : 'Never synced'}
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
            </Card>

            {/* Quick Actions */}
            <Card className="md:col-span-2 lg:col-span-3">
              <CardHeader>
                <CardTitle>Quick Actions</CardTitle>
                <CardDescription>Common WordPress management tasks</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
                  <button className="flex items-center gap-2 p-3 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800">
                    <Upload className="h-4 w-4" />
                    Push to WordPress
                  </button>
                  <button className="flex items-center gap-2 p-3 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800">
                    <Download className="h-4 w-4" />
                    Pull from WordPress
                  </button>
                  <button className="flex items-center gap-2 p-3 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800">
                    <FileText className="h-4 w-4" />
                    Create Page
                  </button>
                  <button className="flex items-center gap-2 p-3 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800">
                    <ShoppingCart className="h-4 w-4" />
                    Sync Products
                  </button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {activeTab === 'pages' && (
          <Card>
            <CardHeader>
              <CardTitle>WordPress Pages</CardTitle>
              <CardDescription>Manage your WordPress pages</CardDescription>
            </CardHeader>
            <CardContent>
              {pages.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <FileText className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No pages found. Sync with WordPress to load pages.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {pages.map((page) => (
                    <div
                      key={page.id}
                      className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800"
                    >
                      <div>
                        <h3 className="font-semibold">{page.title}</h3>
                        <p className="text-sm text-gray-500">/{page.slug}</p>
                        <p className="text-xs text-gray-400 mt-1">
                          Modified: {new Date(page.modified).toLocaleDateString()}
                        </p>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className={`px-2 py-1 text-xs rounded ${
                          page.status === 'publish'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {page.status}
                        </span>
                        <a
                          href={page.link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-brand-primary hover:underline"
                        >
                          <ExternalLink className="h-4 w-4" />
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {activeTab === 'products' && (
          <Card>
            <CardHeader>
              <CardTitle>WooCommerce Products</CardTitle>
              <CardDescription>Manage your WooCommerce store products</CardDescription>
            </CardHeader>
            <CardContent>
              {products.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <ShoppingCart className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p>No products found. Sync with WooCommerce to load products.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {products.map((product) => (
                    <div
                      key={product.id}
                      className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800"
                    >
                      <div>
                        <h3 className="font-semibold">{product.name}</h3>
                        <p className="text-sm text-gray-500">/{product.slug}</p>
                        <p className="text-lg font-bold text-brand-primary mt-1">
                          ${product.price}
                        </p>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className={`px-2 py-1 text-xs rounded ${
                          product.stock_status === 'instock'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {product.stock_status}
                        </span>
                        <span className={`px-2 py-1 text-xs rounded ${
                          product.status === 'publish'
                            ? 'bg-green-100 text-green-800'
                            : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {product.status}
                        </span>
                        <a
                          href={product.link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-brand-primary hover:underline"
                        >
                          <ExternalLink className="h-4 w-4" />
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {activeTab === 'media' && (
          <Card>
            <CardHeader>
              <CardTitle>Media Library</CardTitle>
              <CardDescription>Manage WordPress media files</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12 text-gray-500">
                <ImageIcon className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>Media management coming soon</p>
              </div>
            </CardContent>
          </Card>
        )}

        {activeTab === 'sync' && (
          <Card>
            <CardHeader>
              <CardTitle>Sync Configuration</CardTitle>
              <CardDescription>Configure WordPress sync settings</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="p-4 border rounded-lg">
                  <h3 className="font-semibold mb-2">Automatic Sync</h3>
                  <p className="text-sm text-gray-600 mb-3">
                    Automatically sync content between DevSkyy and WordPress
                  </p>
                  <label className="flex items-center gap-2">
                    <input type="checkbox" className="rounded" />
                    <span>Enable automatic sync</span>
                  </label>
                </div>

                <div className="p-4 border rounded-lg">
                  <h3 className="font-semibold mb-2">Sync Interval</h3>
                  <p className="text-sm text-gray-600 mb-3">
                    How often to check for changes
                  </p>
                  <select className="w-full p-2 border rounded">
                    <option>Every 5 minutes</option>
                    <option>Every 15 minutes</option>
                    <option>Every 30 minutes</option>
                    <option>Every hour</option>
                  </select>
                </div>

                <div className="p-4 border rounded-lg">
                  <h3 className="font-semibold mb-2">Sync Direction</h3>
                  <p className="text-sm text-gray-600 mb-3">
                    Choose which direction to sync content
                  </p>
                  <div className="space-y-2">
                    <label className="flex items-center gap-2">
                      <input type="radio" name="direction" value="both" defaultChecked />
                      <span>Bidirectional (DevSkyy ↔ WordPress)</span>
                    </label>
                    <label className="flex items-center gap-2">
                      <input type="radio" name="direction" value="to-wp" />
                      <span>DevSkyy → WordPress only</span>
                    </label>
                    <label className="flex items-center gap-2">
                      <input type="radio" name="direction" value="from-wp" />
                      <span>WordPress → DevSkyy only</span>
                    </label>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
