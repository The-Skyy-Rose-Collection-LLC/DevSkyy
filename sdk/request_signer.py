"""
Request Signer SDK
==================

Client helper for signing API requests to DevSkyy Enterprise Platform.

This SDK provides utilities for signing high-risk operations that require
request signatures for enhanced security.

Usage:
    from sdk.request_signer import RequestSigner

    # Initialize with your signing secret
    signer = RequestSigner(signing_secret="your-secret-key")

    # Sign a request
    headers = signer.sign_request(
        method="POST",
        path="/api/v1/admin/users/123/delete",
        body=b'{"reason": "compliance"}'
    )

    # Make the request with signed headers
    import httpx
    response = httpx.post(
        "https://api.devskyy.com/api/v1/admin/users/123/delete",
        headers=headers,
        json={"reason": "compliance"}
    )

Protected Endpoints (require request signing):
- /api/v1/admin/*              - All admin operations
- /api/v1/agents/*/execute     - Agent execution
- /api/v1/users/*/delete       - User deletion
- /api/v1/payments/*           - Payment operations
- /api/v1/keys/rotate          - Key rotation
"""

import hashlib
import hmac
import secrets
import time
from typing import Any


class RequestSigner:
    """
    Client helper for signing API requests.

    Implements HMAC-SHA256 request signing with nonce and timestamp
    for replay attack prevention.
    """

    def __init__(self, signing_secret: str | bytes):
        """
        Initialize request signer.

        Args:
            signing_secret: Secret key for HMAC signing (string or bytes)
        """
        if isinstance(signing_secret, str):
            self.signing_secret = signing_secret.encode()
        else:
            self.signing_secret = signing_secret

    def sign_request(
        self,
        method: str,
        path: str,
        body: bytes | str | dict | None = None,
        timestamp: int | None = None,
        key_id: str = "client",
    ) -> dict[str, str]:
        """
        Sign a request and return headers to include.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            path: Request path (e.g., "/api/v1/admin/stats")
            body: Request body (bytes, string, or dict for JSON)
            timestamp: Unix timestamp (default: current time)
            key_id: Key identifier for the signature

        Returns:
            Dictionary of headers to include in request:
            {
                "X-Timestamp": "1234567890",
                "X-Nonce": "random-nonce",
                "X-Signature": "hmac-sha256-signature",
                "X-Key-ID": "client"
            }

        Example:
            signer = RequestSigner("my-secret")
            headers = signer.sign_request("POST", "/api/v1/admin/stats")
            # Add these headers to your HTTP request
        """
        # Generate timestamp and nonce
        timestamp = timestamp or int(time.time())
        nonce = secrets.token_hex(16)

        # Convert body to bytes
        if body is None:
            body_bytes = b""
        elif isinstance(body, dict):
            import json

            body_bytes = json.dumps(body).encode()
        elif isinstance(body, str):
            body_bytes = body.encode()
        else:
            body_bytes = body

        # Create signature payload
        body_hash = hashlib.sha256(body_bytes).hexdigest()
        payload = f"{method}:{path}:{timestamp}:{nonce}:{body_hash}"

        # Generate HMAC signature
        signature = hmac.new(self.signing_secret, payload.encode(), hashlib.sha256).hexdigest()

        # Return headers
        return {
            "X-Timestamp": str(timestamp),
            "X-Nonce": nonce,
            "X-Signature": signature,
            "X-Key-ID": key_id,
        }

    def sign_request_dict(
        self,
        method: str,
        path: str,
        body: bytes | str | dict | None = None,
        timestamp: int | None = None,
        key_id: str = "client",
    ) -> dict[str, Any]:
        """
        Sign a request and return signature details as a dictionary.

        Useful for debugging or logging signature details.

        Args:
            method: HTTP method
            path: Request path
            body: Request body
            timestamp: Unix timestamp (default: current time)
            key_id: Key identifier

        Returns:
            Dictionary with signature details:
            {
                "timestamp": 1234567890,
                "nonce": "random-nonce",
                "signature": "hmac-sha256-signature",
                "key_id": "client",
                "payload": "method:path:timestamp:nonce:body_hash"
            }
        """
        # Generate timestamp and nonce
        timestamp = timestamp or int(time.time())
        nonce = secrets.token_hex(16)

        # Convert body to bytes
        if body is None:
            body_bytes = b""
        elif isinstance(body, dict):
            import json

            body_bytes = json.dumps(body).encode()
        elif isinstance(body, str):
            body_bytes = body.encode()
        else:
            body_bytes = body

        # Create signature payload
        body_hash = hashlib.sha256(body_bytes).hexdigest()
        payload = f"{method}:{path}:{timestamp}:{nonce}:{body_hash}"

        # Generate HMAC signature
        signature = hmac.new(self.signing_secret, payload.encode(), hashlib.sha256).hexdigest()

        return {
            "timestamp": timestamp,
            "nonce": nonce,
            "signature": signature,
            "key_id": key_id,
            "payload": payload,
        }

    def verify_signature(
        self,
        method: str,
        path: str,
        body: bytes | str | dict | None,
        timestamp: int,
        nonce: str,
        signature: str,
    ) -> bool:
        """
        Verify a request signature (for testing).

        Args:
            method: HTTP method
            path: Request path
            body: Request body
            timestamp: Request timestamp
            nonce: Request nonce
            signature: Signature to verify

        Returns:
            True if signature is valid, False otherwise
        """
        # Convert body to bytes
        if body is None:
            body_bytes = b""
        elif isinstance(body, dict):
            import json

            body_bytes = json.dumps(body).encode()
        elif isinstance(body, str):
            body_bytes = body.encode()
        else:
            body_bytes = body

        # Recreate signature
        body_hash = hashlib.sha256(body_bytes).hexdigest()
        payload = f"{method}:{path}:{timestamp}:{nonce}:{body_hash}"
        expected_signature = hmac.new(
            self.signing_secret, payload.encode(), hashlib.sha256
        ).hexdigest()

        # Constant-time comparison
        return hmac.compare_digest(signature, expected_signature)


# Example usage functions
def example_sign_get_request():
    """Example: Sign a GET request"""
    signer = RequestSigner("my-secret-key")

    # GET requests typically have no body
    headers = signer.sign_request(
        method="GET",
        path="/api/v1/admin/stats",
    )

    print("Signed GET request headers:")
    for key, value in headers.items():
        print(f"  {key}: {value}")

    return headers


def example_sign_post_request():
    """Example: Sign a POST request with JSON body"""
    signer = RequestSigner("my-secret-key")

    # POST request with JSON body
    request_body = {"user_id": "123", "reason": "compliance"}

    headers = signer.sign_request(
        method="POST",
        path="/api/v1/users/123/delete",
        body=request_body,
    )

    print("Signed POST request headers:")
    for key, value in headers.items():
        print(f"  {key}: {value}")

    return headers


def example_httpx_request():
    """Example: Make a signed request with httpx"""
    try:
        import httpx
    except ImportError:
        print("httpx not installed. Install with: pip install httpx")
        return

    signer = RequestSigner("my-secret-key")

    # Prepare request
    url = "https://api.devskyy.com/api/v1/admin/stats"
    method = "GET"
    path = "/api/v1/admin/stats"

    # Sign the request
    signature_headers = signer.sign_request(method=method, path=path)

    # Combine with auth headers
    headers = {
        "Authorization": "Bearer your-jwt-token",
        **signature_headers,
    }

    # Make request (example - will fail without valid server)
    print(f"Making signed {method} request to {url}")
    print("Headers:", headers)

    # Uncomment to actually make the request:
    # response = httpx.get(url, headers=headers)
    # print(f"Response: {response.status_code}")


if __name__ == "__main__":
    print("Request Signer SDK Examples")
    print("=" * 50)
    print()

    print("Example 1: Sign GET request")
    print("-" * 50)
    example_sign_get_request()
    print()

    print("Example 2: Sign POST request with JSON body")
    print("-" * 50)
    example_sign_post_request()
    print()

    print("Example 3: Make signed request with httpx")
    print("-" * 50)
    example_httpx_request()
