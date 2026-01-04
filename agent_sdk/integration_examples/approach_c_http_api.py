"""
Approach C: HTTP API Call to Internal Service

PROS:
✅ Language agnostic - service can be in any language
✅ Service isolation - failures don't affect agent
✅ Independent scaling - scale services independently
✅ Versioning - API versions allow gradual migration
✅ Load balancing - distribute across multiple instances
✅ Caching - HTTP caching (ETags, Cache-Control)
✅ Monitoring - standard HTTP metrics (status codes, latency)
✅ Security - authentication, rate limiting, CORS

CONS:
❌ Network latency - HTTP overhead (typically 10-50ms)
❌ Complexity - need to run separate service
❌ Serialization - JSON encode/decode overhead
❌ Error handling - network failures, timeouts
❌ Testing - need to mock HTTP calls
❌ Discovery - need service registry in production

BEST FOR:
- Microservices architecture
- Polyglot systems (Python agent → Node.js service)
- Third-party integrations
- Cross-team boundaries
- When services need independent deployment
- Public API exposure

ARCHITECTURE:
┌─────────┐      ┌──────────┐      ┌────────────┐
│ Agent   │─HTTP─>│ FastAPI  │─────>│ Tripo3D    │
│ SDK     │<─────│ Service  │<─────│ Agent      │
└─────────┘      └──────────┘      └────────────┘
                       │
                 ┌─────┴─────┐
                 │   Cache   │
                 │  (Redis)  │
                 └───────────┘
"""

import asyncio
from typing import Any

import httpx
from claude_agent_sdk import tool

# Configuration
API_BASE_URL = "http://localhost:8001/api/v1"  # Internal service
API_TIMEOUT = 60.0  # seconds
API_MAX_RETRIES = 3


class DevSkyyAPIClient:
    """
    HTTP client for DevSkyy internal services.

    Handles:
    - Connection pooling
    - Retry logic
    - Error handling
    - Authentication
    - Rate limiting
    """

    def __init__(
        self,
        base_url: str = API_BASE_URL,
        timeout: float = API_TIMEOUT,
        api_key: str | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.api_key = api_key

        # Create persistent HTTP client with connection pooling
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        )

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    def _get_headers(self) -> dict[str, str]:
        """Get headers for API requests."""
        headers = {"Content-Type": "application/json", "User-Agent": "DevSkyy-Agent-SDK/1.0"}

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        return headers

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        retry_count: int = 0,
    ) -> dict[str, Any]:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint (e.g., "/3d/generate")
            data: JSON body for POST/PUT
            params: Query parameters
            retry_count: Current retry attempt

        Returns:
            Response data as dict

        Raises:
            httpx.HTTPError: On HTTP errors
            ValueError: On invalid response
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = await self.client.request(
                method=method, url=url, json=data, params=params, headers=self._get_headers()
            )

            # Raise for 4xx/5xx status codes
            response.raise_for_status()

            # Parse JSON response
            return response.json()

        except httpx.HTTPStatusError as e:
            # Handle specific HTTP errors
            if e.response.status_code == 429:  # Too Many Requests
                if retry_count < API_MAX_RETRIES:
                    # Exponential backoff
                    wait_time = 2**retry_count
                    await asyncio.sleep(wait_time)
                    return await self._request(method, endpoint, data, params, retry_count + 1)
                else:
                    raise ValueError("Rate limit exceeded, max retries reached")

            elif e.response.status_code >= 500:  # Server error
                if retry_count < API_MAX_RETRIES:
                    await asyncio.sleep(1)
                    return await self._request(method, endpoint, data, params, retry_count + 1)
                else:
                    raise ValueError(f"Server error: {e.response.text}")

            else:
                # Client error (400-499) - don't retry
                try:
                    error_data = e.response.json()
                    error_message = error_data.get("detail", e.response.text)
                except Exception:
                    error_message = e.response.text

                raise ValueError(f"API error: {error_message}")

        except httpx.TimeoutException:
            if retry_count < API_MAX_RETRIES:
                await asyncio.sleep(1)
                return await self._request(method, endpoint, data, params, retry_count + 1)
            else:
                raise ValueError("Request timeout, max retries reached")

        except httpx.NetworkError:
            raise ValueError(f"Network error: Unable to connect to {url}")

    # Convenience methods for different HTTP verbs
    async def get(self, endpoint: str, params: dict | None = None):
        """GET request."""
        return await self._request("GET", endpoint, params=params)

    async def post(self, endpoint: str, data: dict[str, Any]):
        """POST request."""
        return await self._request("POST", endpoint, data=data)

    async def put(self, endpoint: str, data: dict[str, Any]):
        """PUT request."""
        return await self._request("PUT", endpoint, data=data)

    async def delete(self, endpoint: str):
        """DELETE request."""
        return await self._request("DELETE", endpoint)


# Global API client (reuses connection pool)
api_client = DevSkyyAPIClient()


@tool(
    "generate_3d_model",
    "Generate a 3D model from text description or image using Tripo3D",
    {
        "prompt": str,
        "image_url": str,
        "style": str,
    },
)
async def generate_3d_model(args: dict[str, Any]) -> dict[str, Any]:
    """
    HTTP API integration for 3D generation.

    Flow:
    1. Send POST request to internal API
    2. API service calls Tripo3D
    3. Return formatted response

    API Endpoint: POST /api/v1/3d/generate
    """
    try:
        prompt = args.get("prompt", "")
        image_url = args.get("image_url")
        style = args.get("style", "realistic")

        # Call internal API service
        response = await api_client.post(
            "/3d/generate", data={"prompt": prompt, "image_url": image_url, "style": style}
        )

        # Extract data from API response
        model_url = response.get("model_url")
        task_id = response.get("task_id")
        status = response.get("status")
        metadata = response.get("metadata", {})

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"""3D Model Generated Successfully!

Model URL: {model_url}
Task ID: {task_id}
Status: {status}
Polycount: {metadata.get('polycount', 'N/A')}
Texture Resolution: {metadata.get('texture_resolution', 'N/A')}

The model is ready for download or integration.""",
                }
            ]
        }

    except ValueError as e:
        # API-specific errors
        return {"content": [{"type": "text", "text": f"API Error: {str(e)}"}], "is_error": True}

    except Exception as e:
        # Unexpected errors
        return {
            "content": [{"type": "text", "text": f"Error generating 3D model: {str(e)}"}],
            "is_error": True,
        }


@tool(
    "manage_product",
    "Create, update, or retrieve WooCommerce products",
    {
        "action": str,
        "product_data": dict,
        "product_id": int,
    },
)
async def manage_product(args: dict[str, Any]) -> dict[str, Any]:
    """
    HTTP API integration for product management.

    API Endpoints:
    - POST   /api/v1/products        (create)
    - GET    /api/v1/products        (list)
    - GET    /api/v1/products/{id}   (get)
    - PUT    /api/v1/products/{id}   (update)
    - DELETE /api/v1/products/{id}   (delete)
    """
    try:
        action = args.get("action", "list")
        product_data = args.get("product_data", {})
        product_id = args.get("product_id")

        if action == "create":
            response = await api_client.post("/products", data=product_data)

            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"""Product Created Successfully!

ID: {response.get('id')}
Name: {response.get('name')}
Price: ${response.get('price')}
SKU: {response.get('sku')}
URL: {response.get('permalink')}""",
                    }
                ]
            }

        elif action == "get":
            if not product_id:
                raise ValueError("product_id required for get action")

            response = await api_client.get(f"/products/{product_id}")

            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"""Product Details:

Name: {response.get('name')}
Price: ${response.get('price')}
Stock: {response.get('stock_quantity')}
Status: {response.get('status')}
Categories: {', '.join(response.get('categories', []))}""",
                    }
                ]
            }

        elif action == "list":
            # Use product_data as query filters
            response = await api_client.get("/products", params=product_data)

            products = response.get("products", [])
            total = response.get("total", 0)

            product_list = "\n".join(
                [
                    f"- {p.get('name')} (${p.get('price')}) - ID: {p.get('id')}"
                    for p in products[:10]
                ]
            )

            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"""Found {total} products:

{product_list}

{'...' if total > 10 else ''}""",
                    }
                ]
            }

        elif action == "update":
            if not product_id:
                raise ValueError("product_id required for update action")

            response = await api_client.put(f"/products/{product_id}", data=product_data)

            return {
                "content": [{"type": "text", "text": f"Product {product_id} updated successfully!"}]
            }

        else:
            raise ValueError(f"Unknown action: {action}")

    except ValueError as e:
        return {"content": [{"type": "text", "text": f"Error: {str(e)}"}], "is_error": True}


@tool(
    "analyze_data",
    "Analyze business data and generate insights",
    {
        "data_source": str,
        "time_range": str,
        "metrics": list,
    },
)
async def analyze_data(args: dict[str, Any]) -> dict[str, Any]:
    """
    HTTP API integration for analytics.

    API Endpoint: POST /api/v1/analytics/analyze
    """
    try:
        data_source = args.get("data_source", "sales")
        time_range = args.get("time_range", "last_7_days")
        metrics = args.get("metrics", [])

        # Call analytics API
        response = await api_client.post(
            "/analytics/analyze",
            data={"source": data_source, "time_range": time_range, "metrics": metrics},
        )

        # Format the response
        summary = response.get("summary", "")
        key_metrics = response.get("metrics", {})
        insights = response.get("insights", [])

        metrics_text = "\n".join([f"- {k}: {v}" for k, v in key_metrics.items()])

        insights_text = "\n".join([f"• {insight}" for insight in insights])

        return {
            "content": [
                {
                    "type": "text",
                    "text": f"""Data Analysis Complete

📊 Summary:
{summary}

📈 Key Metrics:
{metrics_text}

💡 Insights:
{insights_text}""",
                }
            ]
        }

    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error analyzing data: {str(e)}"}],
            "is_error": True,
        }


# ============================================================================
# Internal FastAPI Service (runs separately)
# ============================================================================

"""
Example FastAPI service that the agent calls.

File: services/devskyy_api/main.py

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agents.tripo_agent import Tripo3DAgent
from agents.commerce_agent import CommerceAgent

app = FastAPI(title="DevSkyy Internal API")

class Generate3DRequest(BaseModel):
    prompt: str
    image_url: Optional[str] = None
    style: str = "realistic"

@app.post("/api/v1/3d/generate")
async def generate_3d(request: Generate3DRequest):
    try:
        agent = Tripo3DAgent()

        if request.image_url:
            result = await agent.generate_from_image(
                image_url=request.image_url,
                prompt=request.prompt,
                style=request.style
            )
        else:
            result = await agent.generate_from_text(
                prompt=request.prompt,
                style=request.style
            )

        return {
            "model_url": result["model_url"],
            "task_id": result["task_id"],
            "status": "completed",
            "metadata": result.get("metadata", {})
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/products")
async def list_products(category: Optional[str] = None, limit: int = 10):
    agent = CommerceAgent()
    products = await agent.list_products({"category": category, "limit": limit})
    return products

# ... more endpoints
```

Run with: uvicorn services.devskyy_api.main:app --port 8001
"""


# Example usage
if __name__ == "__main__":
    print("✅ Approach C: HTTP API - Example complete")
    print("\nTo test:")
    print("  1. Start internal API service:")
    print("     uvicorn services.devskyy_api.main:app --port 8001")
    print("\n  2. Test with curl:")
    print("     curl -X POST http://localhost:8001/api/v1/3d/generate \\")
    print("       -H 'Content-Type: application/json' \\")
    print('       -d \'{"prompt": "engagement ring", "style": "realistic"}\'')
    print("\n  3. Use in Agent SDK:")
    print("     python approach_c_http_api.py")
    print("\nBenefits:")
    print("  - Service can be in any language (Node.js, Go, etc.)")
    print("  - Independent scaling and deployment")
    print("  - Standard HTTP monitoring and caching")
    print("  - Easy to add authentication and rate limiting")
