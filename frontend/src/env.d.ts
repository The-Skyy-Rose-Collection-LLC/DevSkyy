/// <reference types="vite/client" />

/**
 * Environment Variable Type Definitions
 * Provides TypeScript support for import.meta.env variables
 */

interface ImportMetaEnv {
  // API Configuration
  readonly VITE_API_URL: string

  // Application
  readonly VITE_APP_NAME: string
  readonly VITE_APP_VERSION: string
  readonly VITE_APP_ENV: 'development' | 'staging' | 'production'

  // Optional: Analytics
  readonly VITE_GOOGLE_ANALYTICS_ID?: string
  readonly VITE_SENTRY_DSN?: string

  // Optional: Feature Flags
  readonly VITE_ENABLE_VOICE?: string
  readonly VITE_ENABLE_3D?: string
  readonly VITE_ENABLE_SOCIAL_AUTH?: string

  // Mode (automatically provided by Vite)
  readonly MODE: string
  readonly DEV: boolean
  readonly PROD: boolean
  readonly SSR: boolean
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
