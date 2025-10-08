/**
 * Global Type Definitions for DevSkyy Platform
 * Enterprise-grade TypeScript type system
 */

// ============================================
// Core Types
// ============================================

export interface ApiResponse<T = any> {
  success: boolean
  data?: T
  error?: ApiError
  message?: string
}

export interface ApiError {
  type: string
  message: string
  details?: Record<string, any>
  status_code: number
  path?: string
}

// ============================================
// Agent Types
// ============================================

export interface Agent {
  id: string
  name: string
  type: AgentType
  status: AgentStatus
  capabilities: string[]
  metrics: AgentMetrics
  lastActive: Date
  avatar?: string
}

export enum AgentType {
  BRAND_INTELLIGENCE = 'brand_intelligence',
  FASHION_VISION = 'fashion_vision',
  SOCIAL_MEDIA = 'social_media',
  SEO_MARKETING = 'seo_marketing',
  CUSTOMER_SERVICE = 'customer_service',
  SECURITY = 'security',
  PERFORMANCE = 'performance',
  ECOMMERCE = 'ecommerce',
  WORDPRESS = 'wordpress',
  WEB_DEVELOPMENT = 'web_development',
}

export enum AgentStatus {
  ACTIVE = 'active',
  IDLE = 'idle',
  BUSY = 'busy',
  ERROR = 'error',
  OFFLINE = 'offline',
}

export interface AgentMetrics {
  tasksCompleted: number
  successRate: number
  averageResponseTime: number
  uptime: number
}

// ============================================
// Task Types
// ============================================

export interface Task {
  id: string
  title: string
  description: string
  type: TaskType
  status: TaskStatus
  priority: TaskPriority
  assignedAgent?: string
  createdAt: Date
  updatedAt: Date
  completedAt?: Date
  metadata?: Record<string, any>
}

export enum TaskType {
  CONTENT_GENERATION = 'content_generation',
  IMAGE_ANALYSIS = 'image_analysis',
  CODE_FIX = 'code_fix',
  SEO_OPTIMIZATION = 'seo_optimization',
  SOCIAL_POST = 'social_post',
  CUSTOMER_SUPPORT = 'customer_support',
  SECURITY_SCAN = 'security_scan',
  PERFORMANCE_TEST = 'performance_test',
}

export enum TaskStatus {
  PENDING = 'pending',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

export enum TaskPriority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  URGENT = 'urgent',
}

// ============================================
// Product Types
// ============================================

export interface Product {
  id: string
  name: string
  description: string
  category: ProductCategory
  price: number
  cost: number
  sku: string
  stockQuantity: number
  sizes: string[]
  colors: string[]
  images: string[]
  tags: string[]
  createdAt: Date
  updatedAt: Date
}

export enum ProductCategory {
  JEWELRY = 'jewelry',
  ACCESSORIES = 'accessories',
  CLOTHING = 'clothing',
  BEAUTY = 'beauty',
  HOME = 'home',
}

// ============================================
// Customer Types
// ============================================

export interface Customer {
  id: string
  email: string
  firstName: string
  lastName: string
  phone?: string
  preferences?: Record<string, any>
  lifetimeValue: number
  orderCount: number
  createdAt: Date
}

// ============================================
// Order Types
// ============================================

export interface Order {
  id: string
  customerId: string
  items: OrderItem[]
  status: OrderStatus
  totalAmount: number
  shippingAddress: Address
  billingAddress?: Address
  createdAt: Date
  updatedAt: Date
}

export interface OrderItem {
  productId: string
  quantity: number
  size?: string
  color?: string
  price: number
}

export enum OrderStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  SHIPPED = 'shipped',
  DELIVERED = 'delivered',
  CANCELLED = 'cancelled',
}

export interface Address {
  street: string
  city: string
  state: string
  postalCode: string
  country: string
}

// ============================================
// Analytics Types
// ============================================

export interface AnalyticsData {
  period: string
  metrics: Metrics
  trends: Trend[]
  insights: Insight[]
}

export interface Metrics {
  revenue: number
  orders: number
  customers: number
  conversionRate: number
  averageOrderValue: number
  customerLifetimeValue: number
}

export interface Trend {
  metric: string
  direction: 'up' | 'down' | 'stable'
  change: number
  period: string
}

export interface Insight {
  id: string
  type: InsightType
  title: string
  description: string
  severity: 'info' | 'warning' | 'critical'
  actionable: boolean
  recommendedAction?: string
}

export enum InsightType {
  SALES = 'sales',
  INVENTORY = 'inventory',
  CUSTOMER = 'customer',
  PERFORMANCE = 'performance',
  SECURITY = 'security',
}

// ============================================
// WordPress Types
// ============================================

export interface WordPressConnection {
  url: string
  username: string
  connected: boolean
  lastSync?: Date
  status: ConnectionStatus
}

export enum ConnectionStatus {
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  ERROR = 'error',
  SYNCING = 'syncing',
}

// ============================================
// Social Media Types
// ============================================

export interface SocialMediaPost {
  id: string
  platform: SocialPlatform
  content: string
  media?: string[]
  scheduledAt?: Date
  publishedAt?: Date
  status: PostStatus
  engagement?: Engagement
}

export enum SocialPlatform {
  FACEBOOK = 'facebook',
  INSTAGRAM = 'instagram',
  TWITTER = 'twitter',
  LINKEDIN = 'linkedin',
  TIKTOK = 'tiktok',
}

export enum PostStatus {
  DRAFT = 'draft',
  SCHEDULED = 'scheduled',
  PUBLISHED = 'published',
  FAILED = 'failed',
}

export interface Engagement {
  likes: number
  comments: number
  shares: number
  reach: number
  impressions: number
}

// ============================================
// User Types
// ============================================

export interface User {
  id: string
  email: string
  username: string
  role: UserRole
  permissions: Permission[]
  profile?: UserProfile
  createdAt: Date
}

export enum UserRole {
  ADMIN = 'admin',
  MANAGER = 'manager',
  AGENT = 'agent',
  USER = 'user',
}

export enum Permission {
  MANAGE_AGENTS = 'manage_agents',
  MANAGE_PRODUCTS = 'manage_products',
  MANAGE_ORDERS = 'manage_orders',
  MANAGE_CUSTOMERS = 'manage_customers',
  VIEW_ANALYTICS = 'view_analytics',
  MANAGE_USERS = 'manage_users',
  MANAGE_SETTINGS = 'manage_settings',
}

export interface UserProfile {
  firstName: string
  lastName: string
  avatar?: string
  phone?: string
  timezone?: string
}

// ============================================
// UI Component Types
// ============================================

export interface NavItem {
  id: string
  label: string
  icon: string
  path?: string
  gradient?: string
  description?: string
  onClick?: () => void
}

export interface DashboardCard {
  id: string
  title: string
  value: string | number
  change?: number
  trend?: 'up' | 'down' | 'stable'
  icon?: string
  color?: string
}

export interface NotificationItem {
  id: string
  type: NotificationType
  title: string
  message: string
  timestamp: Date
  read: boolean
  actionUrl?: string
}

export enum NotificationType {
  INFO = 'info',
  SUCCESS = 'success',
  WARNING = 'warning',
  ERROR = 'error',
}

// ============================================
// Form Types
// ============================================

export interface FormField<T = any> {
  name: string
  label: string
  type: FieldType
  value: T
  placeholder?: string
  required?: boolean
  validation?: ValidationRule[]
  error?: string
}

export enum FieldType {
  TEXT = 'text',
  EMAIL = 'email',
  PASSWORD = 'password',
  NUMBER = 'number',
  TEXTAREA = 'textarea',
  SELECT = 'select',
  CHECKBOX = 'checkbox',
  RADIO = 'radio',
  DATE = 'date',
  FILE = 'file',
}

export interface ValidationRule {
  type: ValidationType
  value?: any
  message: string
}

export enum ValidationType {
  REQUIRED = 'required',
  MIN_LENGTH = 'min_length',
  MAX_LENGTH = 'max_length',
  MIN_VALUE = 'min_value',
  MAX_VALUE = 'max_value',
  PATTERN = 'pattern',
  EMAIL = 'email',
  URL = 'url',
}

// ============================================
// Utility Types
// ============================================

export type Nullable<T> = T | null
export type Optional<T> = T | undefined
export type ID = string | number
export type Timestamp = Date | string

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  hasMore: boolean
}

export interface FilterOptions {
  search?: string
  filters?: Record<string, any>
  sort?: SortOptions
  pagination?: PaginationOptions
}

export interface SortOptions {
  field: string
  direction: 'asc' | 'desc'
}

export interface PaginationOptions {
  page: number
  pageSize: number
}