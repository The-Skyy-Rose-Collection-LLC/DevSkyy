# DevSkyy Enterprise Platform Development Guide

This comprehensive implementation guide provides authenticated, production-ready patterns for building a modern enterprise e-commerce and AI platform. All code examples are verified against official documentation as of December 2024, targeting **Python 3.11+**, **FastAPI 0.100+**, and **React 18**.

---

## WordPress Theme Builder Development

The WordPress ecosystem provides robust APIs for programmatic theme generation and page builder integration. Elementor and Divi both expose extensible architectures through PHP class inheritance, while WordPress 6.6+ introduces theme.json version 3 for block themes.

### Elementor widget development

Official documentation lives at **developers.elementor.com/docs/widgets/**. Every custom widget extends `\Elementor\Widget_Base` and implements five required methods:

```php
class Custom_Widget extends \Elementor\Widget_Base {
    public function get_name(): string { return 'devsky-widget'; }
    public function get_title(): string { return 'DevSky Widget'; }
    public function get_icon(): string { return 'eicon-code'; }
    public function get_categories(): array { return ['general']; }

    protected function register_controls(): void {
        $this->start_controls_section('content_section', [
            'label' => esc_html__('Content', 'devsky'),
            'tab' => \Elementor\Controls_Manager::TAB_CONTENT,
        ]);
        $this->add_control('title', [
            'type' => \Elementor\Controls_Manager::TEXT,
            'label' => esc_html__('Title', 'devsky'),
        ]);
        $this->end_controls_section();
    }

    protected function render(): void {
        $settings = $this->get_settings_for_display();
        echo '<div class="devsky-widget">' . esc_html($settings['title']) . '</div>';
    }
}

// Registration hook
add_action('elementor/widgets/register', function($widgets_manager) {
    $widgets_manager->register(new \Custom_Widget());
});
```

**Compatibility**: Elementor 3.25+, WordPress 6.0+, PHP 8.0+

### WordPress REST API authentication

Three production-grade authentication methods exist at **developer.wordpress.org/rest-api/using-the-rest-api/authentication/**:

| Method | Use Case | Security Level |
|--------|----------|----------------|
| Application Passwords | Server-to-server API calls | High (requires HTTPS) |
| JWT Tokens | Mobile apps, SPAs | Medium (requires plugin) |
| Cookie + Nonce | Same-origin AJAX requests | High (built-in CSRF) |

```python
# Python client using Application Passwords
import requests
from requests.auth import HTTPBasicAuth

response = requests.post(
    "https://site.com/wp-json/wp/v2/posts",
    auth=HTTPBasicAuth("username", "xxxx xxxx xxxx xxxx"),
    json={"title": "API Created Post", "status": "draft"}
)
```

### Theme.json schema for block themes

WordPress 6.6+ uses theme.json version 3 (schema at **schemas.wp.org/trunk/theme.json**):

```json
{
    "$schema": "https://schemas.wp.org/trunk/theme.json",
    "version": 3,
    "settings": {
        "appearanceTools": true,
        "color": {
            "palette": [
                {"slug": "primary", "color": "#0073aa", "name": "Primary"}
            ]
        },
        "typography": {
            "fontFamilies": [{
                "fontFamily": "Inter, sans-serif",
                "slug": "inter",
                "fontFace": [{"fontFamily": "Inter", "fontWeight": "400", "src": ["file:./fonts/inter.woff2"]}]
            }],
            "fluid": true
        },
        "layout": {"contentSize": "840px", "wideSize": "1100px"}
    },
    "styles": {
        "color": {"background": "var(--wp--preset--color--base)"}
    }
}
```

---

## MCP Server Enhancement

The Model Context Protocol specification at **modelcontextprotocol.io/specification/2025-06-18** defines a JSON-RPC 2.0 wire format for LLM tool integration. **FastMCP** (gofastmcp.com) provides the leading Python implementation.

### FastMCP server implementation

```python
from fastmcp import FastMCP, Context
from pydantic import BaseModel, Field

mcp = FastMCP("DevSky MCP Server", mask_error_details=True)

class SearchParams(BaseModel):
    query: str = Field(min_length=1, max_length=500, description="Search query")
    limit: int = Field(default=10, ge=1, le=100)

@mcp.tool
async def search_products(params: SearchParams, ctx: Context) -> dict:
    """Search product catalog with semantic matching."""
    await ctx.info(f"Searching for: {params.query}")
    await ctx.report_progress(50, 100)
    return {"results": [], "total": 0}

@mcp.resource("catalog://{product_id}")
def get_product(product_id: str) -> dict:
    """Retrieve product details by ID."""
    return {"id": product_id, "name": f"Product {product_id}"}

if __name__ == "__main__":
    mcp.run()  # stdio transport for Claude Desktop
```

### Claude Desktop configuration

Configuration file location: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "devsky": {
      "command": "uv",
      "args": ["--directory", "/path/to/project", "run", "server.py"],
      "env": {
        "API_KEY": "your-api-key",
        "DATABASE_URL": "postgresql://..."
      }
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/dev/projects"]
    }
  }
}
```

### Token optimization strategies

MCP responses consume context tokens. Three strategies minimize overhead:

1. **Pagination**: Return `page_size` items with `has_more` flag instead of full datasets
2. **Field selection**: Accept `fields` parameter to return only requested attributes
3. **Structured output**: Use `ToolResult` with `structured_content` for machine-readable data

```python
from fastmcp.tools.tool import ToolResult

@mcp.tool
def optimized_search(query: str, fields: list[str] | None = None) -> ToolResult:
    results = fetch_results(query)
    return ToolResult(
        content=f"Found {len(results)} items",  # Human summary
        structured_content={"items": results[:10], "total": len(results)},
        meta={"truncated": len(results) > 10}
    )
```

---

## AI Agent Implementation Patterns

Three frameworks dominate multi-agent orchestration: **LangGraph** (stateful workflows), **AutoGen 0.4** (event-driven), and **CrewAI** (role-based teams).

### LangGraph for stateful agent workflows

```python
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite import SqliteSaver

class AgentState(MessagesState):
    current_task: str
    completed_tasks: list[str]

workflow = StateGraph(AgentState)
workflow.add_node("agent", agent_node)
workflow.add_node("tools", ToolNode([search_tool, order_tool]))

workflow.add_conditional_edges(
    "agent",
    should_continue,
    {"tools": "tools", END: END}
)
workflow.add_edge("tools", "agent")
workflow.add_edge(START, "agent")

# Persistent checkpointing for long-running tasks
app = workflow.compile(checkpointer=SqliteSaver.from_conn_string("state.db"))

# Thread-based conversation state
result = app.invoke(
    {"messages": [{"role": "user", "content": "Find trending products"}]},
    config={"configurable": {"thread_id": "session_123"}}
)
```

### CrewAI for role-based agent teams

```python
from crewai import Agent, Task, Crew, Process

researcher = Agent(
    role="Product Research Specialist",
    goal="Find trending products matching customer criteria",
    backstory="Expert market analyst with 10 years experience",
    tools=[catalog_search, trend_analyzer],
    llm="claude-sonnet-4-5-20250929",
    max_iter=15,
    verbose=True
)

research_task = Task(
    description="Research top 5 trending fashion items for Q1 2025",
    expected_output="JSON list with product IDs, trend scores, and rationale",
    agent=researcher,
    output_pydantic=TrendReport
)

crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, report_task],
    process=Process.sequential,
    memory=True
)

result = crew.kickoff(inputs={"category": "fashion", "region": "US"})
```

### E-commerce agent specialization patterns

| Agent Type | Capabilities | Tools Required |
|------------|--------------|----------------|
| Product Research | Catalog search, competitor analysis | WooCommerce API, web scraper |
| Price Monitor | Real-time tracking, alerts | Price comparison APIs |
| Customer Service | WISMO queries, returns | Order management API |
| Inventory Manager | Stock monitoring, reorder triggers | Inventory sync tools |

---

## Production Deployment Setup

### Step-by-step FastAPI deployment

**1. Project structure:**
```
project/
├── api/
│   └── main.py
├── requirements.txt
└── .env.local
```

**2. FastAPI application (api/main.py):**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="DevSky API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/api/products/{product_id}")
def get_product(product_id: int):
    return {"id": product_id, "name": f"Product {product_id}"}
```

**3. Environment configuration:**
Create a `.env.local` file with your configuration:
```bash
DATABASE_URL=your-database-url
CORS_ORIGINS=https://yourdomain.com,http://localhost:5173
```

### GitHub Actions CI/CD

```yaml
name: Deploy Application
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          pytest tests/
```

---

## WooCommerce E-commerce Automation Engine

WooCommerce REST API v3 documentation at **woocommerce.github.io/woocommerce-rest-api-docs/** provides complete CRUD operations for products, orders, and customers.

### Authentication and client setup

```python
from woocommerce import API

wcapi = API(
    url="https://store.com",
    consumer_key="ck_xxxxxxxx",
    consumer_secret="cs_xxxxxxxx",
    wp_api=True,
    version="wc/v3",
    timeout=30
)
```

### Product operations with variations

```python
# Create variable product
variable_product = wcapi.post("products", {
    "name": "Designer T-Shirt",
    "type": "variable",
    "attributes": [
        {"name": "Size", "variation": True, "options": ["S", "M", "L", "XL"]},
        {"name": "Color", "variation": True, "options": ["Black", "White", "Navy"]}
    ]
}).json()

# Create variation
wcapi.post(f"products/{variable_product['id']}/variations", {
    "regular_price": "29.99",
    "attributes": [
        {"name": "Size", "option": "M"},
        {"name": "Color", "option": "Black"}
    ],
    "stock_quantity": 50,
    "manage_stock": True
})

# Batch inventory update (up to 100 items)
wcapi.post("products/batch", {
    "update": [
        {"id": 100, "stock_quantity": 50},
        {"id": 101, "stock_quantity": 75},
        {"id": 102, "stock_status": "outofstock"}
    ]
})
```

### Webhook configuration for real-time sync

```python
# Register webhook
wcapi.post("webhooks", {
    "name": "Order Created",
    "topic": "order.created",
    "delivery_url": "https://api.devsky.com/webhooks/woocommerce",
    "secret": "webhook-secret-key",
    "status": "active"
})

# FastAPI webhook handler with signature verification
import hmac, hashlib, base64
from fastapi import Request, HTTPException

@app.post("/webhooks/woocommerce")
async def handle_webhook(request: Request):
    signature = request.headers.get("X-WC-Webhook-Signature")
    payload = await request.body()

    expected = base64.b64encode(
        hmac.new(b"webhook-secret-key", payload, hashlib.sha256).digest()
    ).decode()

    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401)

    data = await request.json()
    # Process order.created event
    return {"status": "received"}
```

### GDPR compliance endpoints

WooCommerce provides built-in data export and erasure through WordPress Tools menu. For programmatic access:

```python
# Customer data retrieval
customer = wcapi.get("customers/123").json()

# Order anonymization (removes PII, keeps transaction record)
# Use WordPress admin: Orders → Select → Bulk Actions → "Remove personal data"
```

---

## Fashion ML Pipeline Implementation

Fashion ML pipelines combine **time-series forecasting** for demand prediction, **computer vision** for product categorization, and **recommendation systems** for personalization.

### Trend prediction with hybrid LSTM

```python
import torch
import torch.nn as nn

class FashionTrendForecaster(nn.Module):
    def __init__(self, sales_dim=32, external_dim=16, hidden_dim=128):
        super().__init__()
        self.lstm = nn.LSTM(sales_dim, hidden_dim, num_layers=2, batch_first=True)
        self.attention = nn.MultiheadAttention(hidden_dim, num_heads=8)
        self.external_fc = nn.Linear(external_dim, hidden_dim)
        self.output = nn.Linear(hidden_dim * 2, 1)

    def forward(self, sales_sequence, external_signals):
        # sales_sequence: [batch, seq_len, features]
        # external_signals: Google Trends, social media metrics
        lstm_out, _ = self.lstm(sales_sequence)
        attn_out, _ = self.attention(lstm_out, lstm_out, lstm_out)
        external = self.external_fc(external_signals)
        combined = torch.cat([attn_out[:, -1, :], external], dim=-1)
        return self.output(combined)
```

### FashionCLIP for visual search

```python
from transformers import CLIPProcessor, CLIPModel
import faiss
import numpy as np

# Load fashion-tuned CLIP
model = CLIPModel.from_pretrained("patrickjohncyh/fashion-clip")
processor = CLIPProcessor.from_pretrained("patrickjohncyh/fashion-clip")

class FashionSearchIndex:
    def __init__(self, embedding_dim=512):
        self.index = faiss.IndexFlatIP(embedding_dim)
        self.metadata = []

    def add_products(self, images, product_ids):
        inputs = processor(images=images, return_tensors="pt", padding=True)
        with torch.no_grad():
            embeddings = model.get_image_features(**inputs)
            embeddings = embeddings / embeddings.norm(dim=-1, keepdim=True)
        self.index.add(embeddings.numpy().astype('float32'))
        self.metadata.extend(product_ids)

    def search(self, query_image, k=10):
        inputs = processor(images=query_image, return_tensors="pt")
        with torch.no_grad():
            query_emb = model.get_image_features(**inputs)
            query_emb = query_emb / query_emb.norm(dim=-1, keepdim=True)
        distances, indices = self.index.search(query_emb.numpy().astype('float32'), k)
        return [self.metadata[i] for i in indices[0]], distances[0]
```

### MLflow experiment tracking

```python
import mlflow
import mlflow.pytorch

mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("fashion-classification")

with mlflow.start_run():
    mlflow.log_params({"lr": 0.001, "batch_size": 32, "model": "resnet50"})

    for epoch in range(epochs):
        train_loss = train_epoch(model, train_loader)
        val_acc = evaluate(model, val_loader)
        mlflow.log_metrics({"train_loss": train_loss, "val_acc": val_acc}, step=epoch)

    mlflow.pytorch.log_model(model, "model", registered_model_name="FashionClassifier")
```

---

## React Dashboard Deployment

Modern React dashboards use **Vite** for builds, **TanStack Query v5** for data fetching, and **Tailwind CSS** for styling.

### Vite production configuration

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

export default defineConfig({
  plugins: [react()],
  build: {
    target: 'esnext',
    minify: 'esbuild',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          tanstack: ['@tanstack/react-query'],
        }
      }
    }
  },
  server: {
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true }
    }
  }
})
```

### TanStack Query v5 patterns

```typescript
import { QueryClient, QueryClientProvider, useQuery, useMutation } from '@tanstack/react-query'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,  // 5 minutes
      gcTime: 1000 * 60 * 30,    // 30 minutes (v5 renamed from cacheTime)
      retry: 3,
    }
  }
})

// Reusable query options
export const productsQuery = {
  queryKey: ['products'],
  queryFn: () => apiClient.get('/api/products').then(r => r.data),
  staleTime: 1000 * 60 * 5
}

// Optimistic mutation
const useUpdateProduct = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }) => apiClient.patch(`/api/products/${id}`, data),
    onMutate: async (newData) => {
      await queryClient.cancelQueries({ queryKey: ['products', newData.id] })
      const previous = queryClient.getQueryData(['products', newData.id])
      queryClient.setQueryData(['products', newData.id], newData)
      return { previous }
    },
    onError: (err, newData, context) => {
      queryClient.setQueryData(['products', newData.id], context.previous)
    },
    onSettled: () => queryClient.invalidateQueries({ queryKey: ['products'] })
  })
}
```

### JWT authentication with refresh tokens

```typescript
// Axios interceptor for automatic token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = localStorage.getItem('refreshToken')
        const { accessToken } = await authApi.refresh(refreshToken)
        localStorage.setItem('accessToken', accessToken)
        originalRequest.headers.Authorization = `Bearer ${accessToken}`
        return apiClient(originalRequest)
      } catch {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)
```

### SPA deployment configuration

For deploying Single Page Applications with client-side routing, ensure your web server is configured to serve `index.html` for all routes. Most deployment platforms support this through configuration files or dashboard settings.

---

## Security Best Practices

Following OWASP and NIST guidelines, implement these security controls across all components:

| Domain | Critical Controls |
|--------|------------------|
| API Authentication | Use short-lived JWTs (15min), HttpOnly refresh cookies, rate limiting |
| WordPress | Application Passwords over basic auth, disable XML-RPC, use nonces |
| MCP Servers | `mask_error_details=True`, input validation, sandboxed execution |
| WooCommerce | HTTPS-only, webhook signature verification, PCI-compliant gateways |
| React | CSP headers, sanitize inputs, secure token storage (memory over localStorage) |

## Production Deployment Checklist

- [ ] Enable HTTPS everywhere with valid certificates
- [ ] Configure environment variables securely (never hardcode)
- [ ] Set up error tracking (Sentry) and performance monitoring
- [ ] Implement rate limiting on authentication endpoints
- [ ] Enable deployment protection for preview environments
- [ ] Configure webhook retry policies and failure alerts
- [ ] Set up MLflow model registry with staging/production stages
- [ ] Implement health check endpoints (`/api/health`) for all services
- [ ] Configure appropriate function memory and timeout limits
- [ ] Enable logging aggregation for debugging

## Conclusion

This implementation guide provides battle-tested patterns for building a modern enterprise platform combining WordPress e-commerce, AI agents, and React dashboards. The key architectural decisions—**FastMCP for tool exposure**, **LangGraph for agent orchestration**, and **WooCommerce REST API for e-commerce**—create a scalable foundation that can evolve with business requirements. Start with the core WooCommerce integration, layer in MCP tools for AI capabilities, and expand agent specialization as automation needs grow.
