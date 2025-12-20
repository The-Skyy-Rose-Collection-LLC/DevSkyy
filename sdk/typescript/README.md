# DevSkyy TypeScript SDK

Official TypeScript SDK for the DevSkyy Enterprise Platform. This SDK provides secure request signing for high-risk API operations.

## Installation

```bash
npm install @devskyy/sdk
```

## Features

- ✅ **HMAC-SHA256 Request Signing** - Secure request authentication
- ✅ **Replay Attack Prevention** - Nonce + timestamp validation
- ✅ **TypeScript Support** - Full type definitions
- ✅ **Zero Dependencies** - Uses Node.js crypto module
- ✅ **Cross-Platform** - Works in Node.js and modern browsers (with crypto polyfill)

## Quick Start

```typescript
import { RequestSigner } from '@devskyy/sdk';

// Initialize with your signing secret
const signer = new RequestSigner('your-secret-key');

// Sign a GET request
const headers = signer.signRequest({
  method: 'GET',
  path: '/api/v1/admin/stats'
});

// Make the request
const response = await fetch('https://api.devskyy.com/api/v1/admin/stats', {
  method: 'GET',
  headers: {
    'Authorization': 'Bearer your-jwt-token',
    ...headers
  }
});
```

## API Reference

### `RequestSigner`

Main class for signing API requests.

#### Constructor

```typescript
new RequestSigner(signingSecret: string | Buffer)
```

**Parameters:**

- `signingSecret` - Your HMAC signing secret (string or Buffer)

#### Methods

##### `signRequest(options: SignRequestOptions): SignatureHeaders`

Signs a request and returns headers to include.

**Parameters:**

```typescript
interface SignRequestOptions {
  method: string;           // HTTP method (GET, POST, etc.)
  path: string;             // Request path
  body?: string | object | Buffer;  // Request body (optional)
  timestamp?: number;       // Unix timestamp (default: now)
  keyId?: string;          // Key identifier (default: "client")
}
```

**Returns:**

```typescript
interface SignatureHeaders {
  'X-Timestamp': string;
  'X-Nonce': string;
  'X-Signature': string;
  'X-Key-ID': string;
}
```

**Example:**

```typescript
const headers = signer.signRequest({
  method: 'POST',
  path: '/api/v1/admin/users/123/delete',
  body: { reason: 'compliance' }
});
```

##### `signRequestDetails(options: SignRequestOptions): SignatureDetails`

Returns detailed signature information for debugging.

**Returns:**

```typescript
interface SignatureDetails {
  timestamp: number;
  nonce: string;
  signature: string;
  keyId: string;
  payload: string;
}
```

##### `verifySignature(...): boolean`

Verifies a request signature (for testing).

**Parameters:**

- `method: string`
- `path: string`
- `body: string | object | Buffer | null`
- `timestamp: number`
- `nonce: string`
- `signature: string`

**Returns:** `true` if signature is valid, `false` otherwise

## Usage Examples

### POST Request with JSON Body

```typescript
const signer = new RequestSigner('my-secret-key');

const requestBody = {
  user_id: '123',
  reason: 'compliance'
};

const headers = signer.signRequest({
  method: 'POST',
  path: '/api/v1/users/123/delete',
  body: requestBody
});

const response = await fetch('https://api.devskyy.com/api/v1/users/123/delete', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer your-jwt-token',
    'Content-Type': 'application/json',
    ...headers
  },
  body: JSON.stringify(requestBody)
});
```

### GET Request

```typescript
const signer = new RequestSigner('my-secret-key');

const headers = signer.signRequest({
  method: 'GET',
  path: '/api/v1/admin/stats'
});

const response = await fetch('https://api.devskyy.com/api/v1/admin/stats', {
  headers: {
    'Authorization': 'Bearer your-jwt-token',
    ...headers
  }
});
```

### PUT Request with String Body

```typescript
const signer = new RequestSigner('my-secret-key');

const csvData = 'id,name,email\n1,John,john@example.com';

const headers = signer.signRequest({
  method: 'PUT',
  path: '/api/v1/admin/users/import',
  body: csvData
});

const response = await fetch('https://api.devskyy.com/api/v1/admin/users/import', {
  method: 'PUT',
  headers: {
    'Authorization': 'Bearer your-jwt-token',
    'Content-Type': 'text/csv',
    ...headers
  },
  body: csvData
});
```

### Debugging Signatures

```typescript
const signer = new RequestSigner('my-secret-key');

const details = signer.signRequestDetails({
  method: 'POST',
  path: '/api/v1/admin/stats',
  body: { action: 'generate_report' }
});

console.log('Signature Details:', details);
// Output:
// {
//   timestamp: 1703001234,
//   nonce: 'a1b2c3d4e5f6...',
//   signature: '9f8e7d6c5b4a...',
//   keyId: 'client',
//   payload: 'POST:/api/v1/admin/stats:1703001234:a1b2c3d4e5f6...:body_hash'
// }
```

## Protected Endpoints

The following endpoints require request signing:

- `/api/v1/admin/*` - All administrative operations
- `/api/v1/agents/*/execute` - Agent execution endpoints
- `/api/v1/users/*/delete` - User deletion endpoints
- `/api/v1/payments/*` - Payment processing endpoints
- `/api/v1/keys/rotate` - API key rotation

## Security

### HMAC-SHA256

This SDK uses HMAC-SHA256 for request signing, providing:

- **Authentication**: Verify request authenticity
- **Integrity**: Detect request tampering
- **Non-repudiation**: Cryptographic proof of request origin

### Replay Attack Prevention

Each signed request includes:

- **Timestamp**: 5-minute validity window
- **Nonce**: Cryptographically random 32-character hex string
- **One-time use**: Nonces are tracked server-side and rejected if reused

### Constant-Time Comparison

Signature verification uses constant-time string comparison to prevent timing attacks.

## Error Handling

```typescript
try {
  const response = await fetch('https://api.devskyy.com/api/v1/admin/stats', {
    headers: {
      'Authorization': 'Bearer your-jwt-token',
      ...headers
    }
  });

  if (response.status === 401) {
    console.error('Invalid signature or expired token');
  } else if (response.status === 403) {
    console.error('IP blacklisted or insufficient permissions');
  } else if (response.status === 429) {
    const retryAfter = response.headers.get('Retry-After');
    console.error(`Rate limit exceeded. Retry after ${retryAfter} seconds`);
  }
} catch (error) {
  console.error('Request failed:', error);
}
```

## Development

```bash
# Install dependencies
npm install

# Build TypeScript
npm run build

# Run linting
npm run lint

# Format code
npm run format
```

## TypeScript Configuration

This SDK requires TypeScript 5.0+ and Node.js 18.0+.

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "strict": true,
    "esModuleInterop": true
  }
}
```

## License

MIT License - See LICENSE file for details

## Support

- **Documentation**: <https://docs.devskyy.com>
- **Issues**: <https://github.com/devskyy/devskyy/issues>
- **Email**: <support@devskyy.com>

## Related

- [Python SDK](../request_signer.py) - Python request signing implementation
- [API Documentation](../../docs/API.md) - Full API reference
- [Security Guide](../../SECURITY_IMPLEMENTATION_REPORT.md) - Security implementation details
