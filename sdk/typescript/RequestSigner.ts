/**
 * Request Signer SDK - TypeScript Edition
 * ========================================
 *
 * Client helper for signing API requests to DevSkyy Enterprise Platform.
 *
 * This SDK provides utilities for signing high-risk operations that require
 * request signatures for enhanced security.
 *
 * @example
 * ```typescript
 * import { RequestSigner } from './RequestSigner';
 *
 * // Initialize with your signing secret
 * const signer = new RequestSigner('your-secret-key');
 *
 * // Sign a request
 * const headers = signer.signRequest({
 *   method: 'POST',
 *   path: '/api/v1/admin/users/123/delete',
 *   body: { reason: 'compliance' }
 * });
 *
 * // Make the request with signed headers
 * const response = await fetch('https://api.devskyy.com/api/v1/admin/users/123/delete', {
 *   method: 'POST',
 *   headers: {
 *     ...headers,
 *     'Content-Type': 'application/json'
 *   },
 *   body: JSON.stringify({ reason: 'compliance' })
 * });
 * ```
 *
 * Protected Endpoints (require request signing):
 * - /api/v1/admin/*              - All admin operations
 * - /api/v1/agents/*/execute     - Agent execution
 * - /api/v1/users/*/delete       - User deletion
 * - /api/v1/payments/*           - Payment operations
 * - /api/v1/keys/rotate          - Key rotation
 */

import { createHash, createHmac, randomBytes } from 'crypto';

/**
 * Request signature headers
 */
export interface SignatureHeaders {
  'X-Timestamp': string;
  'X-Nonce': string;
  'X-Signature': string;
  'X-Key-ID': string;
}

/**
 * Request signing options
 */
export interface SignRequestOptions {
  /** HTTP method (GET, POST, PUT, DELETE, etc.) */
  method: string;
  /** Request path (e.g., "/api/v1/admin/stats") */
  path: string;
  /** Request body (string, object, or Buffer) */
  body?: string | Record<string, any> | Buffer | null;
  /** Unix timestamp (default: current time) */
  timestamp?: number;
  /** Key identifier for the signature (default: "client") */
  keyId?: string;
}

/**
 * Signature details for debugging
 */
export interface SignatureDetails {
  timestamp: number;
  nonce: string;
  signature: string;
  keyId: string;
  payload: string;
}

/**
 * Client helper for signing API requests.
 *
 * Implements HMAC-SHA256 request signing with nonce and timestamp
 * for replay attack prevention.
 */
export class RequestSigner {
  private signingSecret: Buffer;

  /**
   * Initialize request signer.
   *
   * @param signingSecret - Secret key for HMAC signing (string or Buffer)
   */
  constructor(signingSecret: string | Buffer) {
    if (typeof signingSecret === 'string') {
      this.signingSecret = Buffer.from(signingSecret, 'utf-8');
    } else {
      this.signingSecret = signingSecret;
    }
  }

  /**
   * Sign a request and return headers to include.
   *
   * @param options - Request signing options
   * @returns Dictionary of headers to include in request
   *
   * @example
   * ```typescript
   * const signer = new RequestSigner('my-secret');
   * const headers = signer.signRequest({
   *   method: 'POST',
   *   path: '/api/v1/admin/stats'
   * });
   * // Add these headers to your HTTP request
   * ```
   */
  signRequest(options: SignRequestOptions): SignatureHeaders {
    const { method, path, body = null, keyId = 'client' } = options;

    // Generate timestamp and nonce
    const timestamp = options.timestamp || Math.floor(Date.now() / 1000);
    const nonce = randomBytes(16).toString('hex');

    // Convert body to Buffer
    let bodyBytes: Buffer;
    if (body === null || body === undefined) {
      bodyBytes = Buffer.alloc(0);
    } else if (typeof body === 'string') {
      bodyBytes = Buffer.from(body, 'utf-8');
    } else if (Buffer.isBuffer(body)) {
      bodyBytes = body;
    } else {
      // Assume it's an object/JSON
      bodyBytes = Buffer.from(JSON.stringify(body), 'utf-8');
    }

    // Create signature payload
    const bodyHash = createHash('sha256').update(bodyBytes).digest('hex');
    const payload = `${method}:${path}:${timestamp}:${nonce}:${bodyHash}`;

    // Generate HMAC signature
    const signature = createHmac('sha256', this.signingSecret)
      .update(payload)
      .digest('hex');

    // Return headers
    return {
      'X-Timestamp': timestamp.toString(),
      'X-Nonce': nonce,
      'X-Signature': signature,
      'X-Key-ID': keyId,
    };
  }

  /**
   * Sign a request and return signature details as an object.
   *
   * Useful for debugging or logging signature details.
   *
   * @param options - Request signing options
   * @returns Signature details object
   */
  signRequestDetails(options: SignRequestOptions): SignatureDetails {
    const { method, path, body = null, keyId = 'client' } = options;

    // Generate timestamp and nonce
    const timestamp = options.timestamp || Math.floor(Date.now() / 1000);
    const nonce = randomBytes(16).toString('hex');

    // Convert body to Buffer
    let bodyBytes: Buffer;
    if (body === null || body === undefined) {
      bodyBytes = Buffer.alloc(0);
    } else if (typeof body === 'string') {
      bodyBytes = Buffer.from(body, 'utf-8');
    } else if (Buffer.isBuffer(body)) {
      bodyBytes = body;
    } else {
      bodyBytes = Buffer.from(JSON.stringify(body), 'utf-8');
    }

    // Create signature payload
    const bodyHash = createHash('sha256').update(bodyBytes).digest('hex');
    const payload = `${method}:${path}:${timestamp}:${nonce}:${bodyHash}`;

    // Generate HMAC signature
    const signature = createHmac('sha256', this.signingSecret)
      .update(payload)
      .digest('hex');

    return {
      timestamp,
      nonce,
      signature,
      keyId,
      payload,
    };
  }

  /**
   * Verify a request signature (for testing).
   *
   * @param options - Verification options
   * @returns True if signature is valid, false otherwise
   */
  verifySignature(
    method: string,
    path: string,
    body: string | Record<string, any> | Buffer | null,
    timestamp: number,
    nonce: string,
    signature: string
  ): boolean {
    // Convert body to Buffer
    let bodyBytes: Buffer;
    if (body === null || body === undefined) {
      bodyBytes = Buffer.alloc(0);
    } else if (typeof body === 'string') {
      bodyBytes = Buffer.from(body, 'utf-8');
    } else if (Buffer.isBuffer(body)) {
      bodyBytes = body;
    } else {
      bodyBytes = Buffer.from(JSON.stringify(body), 'utf-8');
    }

    // Recreate signature
    const bodyHash = createHash('sha256').update(bodyBytes).digest('hex');
    const payload = `${method}:${path}:${timestamp}:${nonce}:${bodyHash}`;
    const expectedSignature = createHmac('sha256', this.signingSecret)
      .update(payload)
      .digest('hex');

    // Constant-time comparison
    return this.constantTimeCompare(signature, expectedSignature);
  }

  /**
   * Constant-time string comparison to prevent timing attacks.
   *
   * @param a - First string
   * @param b - Second string
   * @returns True if strings are equal
   */
  private constantTimeCompare(a: string, b: string): boolean {
    if (a.length !== b.length) {
      return false;
    }

    let result = 0;
    for (let i = 0; i < a.length; i++) {
      result |= a.charCodeAt(i) ^ b.charCodeAt(i);
    }

    return result === 0;
  }
}

/**
 * Example: Sign a GET request
 */
export function exampleSignGetRequest(): void {
  const signer = new RequestSigner('my-secret-key');

  // GET requests typically have no body
  const headers = signer.signRequest({
    method: 'GET',
    path: '/api/v1/admin/stats',
  });

  console.log('Signed GET request headers:');
  for (const [key, value] of Object.entries(headers)) {
    console.log(`  ${key}: ${value}`);
  }
}

/**
 * Example: Sign a POST request with JSON body
 */
export function exampleSignPostRequest(): void {
  const signer = new RequestSigner('my-secret-key');

  // POST request with JSON body
  const requestBody = { user_id: '123', reason: 'compliance' };

  const headers = signer.signRequest({
    method: 'POST',
    path: '/api/v1/users/123/delete',
    body: requestBody,
  });

  console.log('Signed POST request headers:');
  for (const [key, value] of Object.entries(headers)) {
    console.log(`  ${key}: ${value}`);
  }
}

/**
 * Example: Make a signed request with fetch
 */
export async function exampleFetchRequest(): Promise<void> {
  const signer = new RequestSigner('my-secret-key');

  // Prepare request
  const url = 'https://api.devskyy.com/api/v1/admin/stats';
  const method = 'GET';
  const path = '/api/v1/admin/stats';

  // Sign the request
  const signatureHeaders = signer.signRequest({ method, path });

  // Combine with auth headers
  const headers = {
    Authorization: 'Bearer your-jwt-token',
    ...signatureHeaders,
  };

  console.log(`Making signed ${method} request to ${url}`);
  console.log('Headers:', headers);

  // Uncomment to actually make the request:
  // const response = await fetch(url, { method, headers });
  // console.log(`Response: ${response.status}`);
}

// Run examples if executed directly
if (require.main === module) {
  console.log('Request Signer SDK Examples');
  console.log('='.repeat(50));
  console.log();

  console.log('Example 1: Sign GET request');
  console.log('-'.repeat(50));
  exampleSignGetRequest();
  console.log();

  console.log('Example 2: Sign POST request with JSON body');
  console.log('-'.repeat(50));
  exampleSignPostRequest();
  console.log();

  console.log('Example 3: Make signed request with fetch');
  console.log('-'.repeat(50));
  exampleFetchRequest();
}
