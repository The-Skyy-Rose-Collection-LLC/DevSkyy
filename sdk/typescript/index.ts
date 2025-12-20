/**
 * DevSkyy Enterprise Platform - TypeScript SDK
 * ============================================
 *
 * Official TypeScript/JavaScript SDK for interacting with DevSkyy Enterprise Platform.
 *
 * Features:
 * - Request signing for high-security endpoints
 * - Type-safe API client
 * - Automatic retry logic
 * - Rate limit handling
 * - Comprehensive error handling
 *
 * @packageDocumentation
 */

export { RequestSigner, type SignatureHeaders, type SignRequestOptions, type SignatureDetails } from './RequestSigner';

/**
 * SDK version
 */
export const SDK_VERSION = '1.0.0';

/**
 * User agent string for API requests
 */
export const USER_AGENT = `DevSkyy-TypeScript-SDK/${SDK_VERSION}`;
