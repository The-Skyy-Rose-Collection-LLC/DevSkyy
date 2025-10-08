/**
 * API Client Type Definitions
 */

import { ApiResponse } from './index'

export interface ApiClientConfig {
  baseUrl: string
  timeout?: number
  headers?: Record<string, string>
  retries?: number
}

export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  headers?: Record<string, string>
  params?: Record<string, any>
  body?: any
  timeout?: number
}

export interface ApiEndpoints {
  agents: {
    list: string
    get: (id: string) => string
    create: string
    update: (id: string) => string
    delete: (id: string) => string
    execute: (id: string) => string
  }
  tasks: {
    list: string
    get: (id: string) => string
    create: string
    update: (id: string) => string
    delete: (id: string) => string
  }
  products: {
    list: string
    get: (id: string) => string
    create: string
    update: (id: string) => string
    delete: (id: string) => string
  }
  orders: {
    list: string
    get: (id: string) => string
    create: string
    update: (id: string) => string
  }
  analytics: {
    dashboard: string
    report: (type: string) => string
  }
}

export class ApiClient {
  private config: ApiClientConfig

  constructor(config: ApiClientConfig) {
    this.config = config
  }

  async request<T>(endpoint: string, options?: RequestOptions): Promise<ApiResponse<T>> {
    // Implementation would go here
    throw new Error('Not implemented')
  }

  async get<T>(endpoint: string, params?: Record<string, any>): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'GET', params })
  }

  async post<T>(endpoint: string, body: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'POST', body })
  }

  async put<T>(endpoint: string, body: any): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'PUT', body })
  }

  async delete<T>(endpoint: string): Promise<ApiResponse<T>> {
    return this.request<T>(endpoint, { method: 'DELETE' })
  }
}