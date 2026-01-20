/**
 * Zod Validation Schemas
 * ======================
 * Centralized validation schemas for forms across the application.
 * These schemas provide runtime validation and TypeScript type inference.
 */

import { z } from 'zod';

// ============================================================================
// Chat & Message Schemas
// ============================================================================

export const chatInputSchema = z.object({
  message: z
    .string()
    .min(1, 'Message is required')
    .max(10000, 'Message is too long (max 10,000 characters)'),
  agentId: z.string().optional(),
});

export type ChatInputData = z.infer<typeof chatInputSchema>;

// ============================================================================
// Task Schemas
// ============================================================================

export const taskExecuteSchema = z.object({
  prompt: z
    .string()
    .min(1, 'Task prompt is required')
    .max(5000, 'Prompt is too long'),
  agentType: z.enum([
    'commerce',
    'creative',
    'marketing',
    'support',
    'operations',
    'analytics',
  ]),
  priority: z.enum(['low', 'medium', 'high']).default('medium'),
  timeout: z.number().min(1000).max(300000).optional(),
});

export type TaskExecuteData = z.infer<typeof taskExecuteSchema>;

// ============================================================================
// Settings Schemas
// ============================================================================

export const settingsSchema = z.object({
  apiEndpoint: z.string().url('Must be a valid URL').optional(),
  theme: z.enum(['light', 'dark', 'system']).default('system'),
  notifications: z.boolean().default(true),
  autoRefresh: z.boolean().default(true),
  refreshInterval: z.number().min(5).max(300).default(30),
});

export type SettingsData = z.infer<typeof settingsSchema>;

// ============================================================================
// Brand Settings Schemas
// ============================================================================

export const brandSettingsSchema = z.object({
  brandName: z.string().min(1, 'Brand name is required').max(100),
  tagline: z.string().max(200).optional(),
  primaryColor: z.string().regex(/^#[0-9A-Fa-f]{6}$/, 'Must be a valid hex color'),
  secondaryColor: z.string().regex(/^#[0-9A-Fa-f]{6}$/, 'Must be a valid hex color'),
  accentColor: z.string().regex(/^#[0-9A-Fa-f]{6}$/, 'Must be a valid hex color').optional(),
  logoUrl: z.string().url().optional(),
});

export type BrandSettingsData = z.infer<typeof brandSettingsSchema>;

// ============================================================================
// Authentication Schemas
// ============================================================================

export const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  rememberMe: z.boolean().default(false),
});

export type LoginData = z.infer<typeof loginSchema>;

export const registerSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email('Invalid email address'),
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
    .regex(/[0-9]/, 'Password must contain at least one number'),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: 'Passwords do not match',
  path: ['confirmPassword'],
});

export type RegisterData = z.infer<typeof registerSchema>;

// ============================================================================
// Contact / Feedback Schemas
// ============================================================================

export const feedbackSchema = z.object({
  type: z.enum(['bug', 'feature', 'feedback', 'other']),
  subject: z.string().min(5, 'Subject must be at least 5 characters').max(200),
  message: z.string().min(20, 'Message must be at least 20 characters').max(5000),
  email: z.string().email().optional(),
  attachScreenshot: z.boolean().default(false),
});

export type FeedbackData = z.infer<typeof feedbackSchema>;

// ============================================================================
// Product / 3D Pipeline Schemas
// ============================================================================

export const product3DGenerationSchema = z.object({
  productName: z.string().min(1, 'Product name is required').max(200),
  productType: z.enum(['clothing', 'accessory', 'footwear', 'jewelry', 'other']),
  imageUrl: z.string().url('Must be a valid image URL').optional(),
  description: z.string().max(1000).optional(),
  generateVariants: z.boolean().default(false),
  quality: z.enum(['draft', 'standard', 'high']).default('standard'),
});

export type Product3DGenerationData = z.infer<typeof product3DGenerationSchema>;

// ============================================================================
// Search Schemas
// ============================================================================

export const searchSchema = z.object({
  query: z.string().min(1, 'Search query is required').max(500),
  filters: z.object({
    type: z.array(z.string()).optional(),
    dateRange: z.object({
      start: z.date().optional(),
      end: z.date().optional(),
    }).optional(),
  }).optional(),
  limit: z.number().min(1).max(100).default(20),
  offset: z.number().min(0).default(0),
});

export type SearchData = z.infer<typeof searchSchema>;
