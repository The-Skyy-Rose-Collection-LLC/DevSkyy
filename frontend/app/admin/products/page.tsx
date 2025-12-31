/**
 * Admin Products Page
 * ====================
 * Product management with 3D model and sync status.
 */

'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import {
  Package,
  Box,
  RefreshCw,
  Plus,
  Eye,
  Search,
  Filter,
  ChevronLeft,
} from 'lucide-react';
import Link from 'next/link';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui';

// Types
interface Product {
  sku: string;
  name: string;
  status: string;
  has_3d_model: boolean;
  synced: boolean;
  stock: number;
  price: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

export default function ProductsPage() {
  const router = useRouter();
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState({
    status: '',
    has3d: '',
  });

  const loadProducts = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filter.status) params.append('status', filter.status);
      if (filter.has3d) params.append('has_3d', filter.has3d);

      const res = await fetch(`${API_BASE}/api/v1/admin/products?${params}`);
      if (res.ok) {
        const data = await res.json();
        setProducts(data);
      }
    } catch (error) {
      console.error('Failed to load products:', error);
    }
    setLoading(false);
  }, [filter]);

  useEffect(() => {
    loadProducts();
  }, [loadProducts]);

  const syncProduct = useCallback(async (sku: string) => {
    try {
      await fetch(`${API_BASE}/api/v1/sync/product`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sku,
          name: sku,
          price: 0,
          image_paths: [],
        }),
      });
      await loadProducts();
    } catch (error) {
      console.error('Sync failed:', error);
    }
  }, [loadProducts]);

  const generate3DModel = useCallback(async (sku: string) => {
    try {
      // This would trigger 3D generation
      alert(`3D model generation triggered for ${sku}. Check 3D Pipeline for progress.`);
    } catch (error) {
      console.error('3D generation failed:', error);
    }
  }, []);

  const filteredProducts = products.filter(
    (p) =>
      p.sku.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="container mx-auto py-8 px-4">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div className="flex items-center gap-4">
          <Link
            href="/admin"
            className="p-2 hover:bg-muted rounded-md transition-colors"
          >
            <ChevronLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-3xl font-bold">Products</h1>
            <p className="text-muted-foreground mt-1">
              {products.length} products in catalog
            </p>
          </div>
        </div>
        <button
          onClick={() => router.push('/admin/products/new')}
          className="inline-flex items-center px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
        >
          <Plus className="w-4 h-4 mr-2" />
          Add Product
        </button>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardContent className="pt-6">
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <input
                  type="text"
                  placeholder="Search products..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
                />
              </div>
            </div>

            <select
              value={filter.status}
              onChange={(e) => setFilter({ ...filter, status: e.target.value })}
              className="px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">All Status</option>
              <option value="draft">Draft</option>
              <option value="publish">Published</option>
            </select>

            <select
              value={filter.has3d}
              onChange={(e) => setFilter({ ...filter, has3d: e.target.value })}
              className="px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">All 3D Status</option>
              <option value="true">Has 3D Model</option>
              <option value="false">No 3D Model</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Products Table */}
      <Card>
        <CardContent className="pt-6">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <RefreshCw className="w-6 h-6 animate-spin text-muted-foreground" />
            </div>
          ) : filteredProducts.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              No products found. Add your first product to get started.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4 font-medium">SKU</th>
                    <th className="text-left py-3 px-4 font-medium">Name</th>
                    <th className="text-left py-3 px-4 font-medium">Status</th>
                    <th className="text-left py-3 px-4 font-medium">3D Model</th>
                    <th className="text-left py-3 px-4 font-medium">Synced</th>
                    <th className="text-left py-3 px-4 font-medium">Stock</th>
                    <th className="text-left py-3 px-4 font-medium">Price</th>
                    <th className="text-left py-3 px-4 font-medium">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredProducts.map((product) => (
                    <tr key={product.sku} className="border-b hover:bg-muted/50">
                      <td className="py-3 px-4 font-mono text-sm">{product.sku}</td>
                      <td className="py-3 px-4">{product.name}</td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-1 text-xs rounded-full ${
                            product.status === 'publish'
                              ? 'bg-green-100 text-green-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {product.status}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        {product.has_3d_model ? (
                          <span className="inline-flex items-center gap-1 px-2 py-1 text-xs rounded-full bg-green-100 text-green-800">
                            <Box className="w-3 h-3" />
                            Yes
                          </span>
                        ) : (
                          <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-800">
                            No
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        {product.synced ? (
                          <span className="px-2 py-1 text-xs rounded-full bg-blue-100 text-blue-800">
                            Synced
                          </span>
                        ) : (
                          <span className="px-2 py-1 text-xs rounded-full bg-yellow-100 text-yellow-800">
                            Pending
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4">{product.stock}</td>
                      <td className="py-3 px-4">${product.price.toFixed(2)}</td>
                      <td className="py-3 px-4">
                        <div className="flex gap-2">
                          <button
                            onClick={() => router.push(`/admin/products/${product.sku}`)}
                            className="p-2 hover:bg-muted rounded-md transition-colors"
                            title="View Details"
                          >
                            <Eye className="w-4 h-4" />
                          </button>
                          {!product.has_3d_model && (
                            <button
                              onClick={() => generate3DModel(product.sku)}
                              className="p-2 hover:bg-muted rounded-md transition-colors"
                              title="Generate 3D Model"
                            >
                              <Box className="w-4 h-4" />
                            </button>
                          )}
                          <button
                            onClick={() => syncProduct(product.sku)}
                            className="p-2 hover:bg-muted rounded-md transition-colors"
                            title="Sync to WordPress"
                          >
                            <RefreshCw className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
