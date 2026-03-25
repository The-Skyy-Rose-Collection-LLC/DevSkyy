# WordPress Agent Integration Setup

## skyyrose.co Configuration Guide

### Step 1: Domain Mapping (WordPress.com)

1. Go to **WordPress.com Dashboard** → **skyyrose.wordpress.com**
2. Navigate to **Settings → Domains**
3. Click **Add a Domain**
4. Enter: `skyyrose.co`
5. Choose **Connect existing domain**

**DNS Records to Add at Your Domain Registrar:**

```
Type: CNAME
Name: skyyrose.co (or @)
Value: skyyrose.wordpress.com
TTL: 3600
```

OR if your registrar requires A records:

```
Type: A
Name: @
Value: 192.0.78.24

Type: A
Name: www
Value: 192.0.78.24
```

**Verify & Activate:**

- Wait 24-48 hours for DNS propagation
- WordPress.com will auto-generate SSL certificate
- Site will be accessible at <https://skyyrose.co>

---

### Step 2: Install Agent Integration Plugin

Create plugin file on WordPress.com via SFTP:

**File: `wp-content/plugins/devskyy-agents/devskyy-agents.php`**

```php
<?php
/**
 * Plugin Name: DevSkyy Agents
 * Description: Integrates DevSkyy AI Agents with WordPress
 * Version: 1.0.0
 * Author: DevSkyy Team
 */

// Register shortcode: [devskyy_agents]
add_shortcode('devskyy_agents', 'devskyy_agents_shortcode');

function devskyy_agents_shortcode($atts) {
    ob_start();
    ?>
    <div id="devskyy-agents-container" style="margin: 2rem 0;">
        <h2>AI Agents Dashboard</h2>
        <p>Powered by DevSkyy Platform</p>

        <div class="agents-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; margin-top: 2rem;">

            <!-- Commerce Agent -->
            <div class="agent-card" style="border: 1px solid #ddd; padding: 1.5rem; border-radius: 8px;">
                <h3>🛒 Commerce Agent</h3>
                <p>Manage products, inventory, and pricing optimization</p>
                <button onclick="executeAgent('commerce')" class="button button-primary">
                    Launch Agent
                </button>
            </div>

            <!-- Creative Agent -->
            <div class="agent-card" style="border: 1px solid #ddd; padding: 1.5rem; border-radius: 8px;">
                <h3>🎨 Creative Agent</h3>
                <p>Generate images, 3D models, and creative content</p>
                <button onclick="executeAgent('creative')" class="button button-primary">
                    Launch Agent
                </button>
            </div>

            <!-- Marketing Agent -->
            <div class="agent-card" style="border: 1px solid #ddd; padding: 1.5rem; border-radius: 8px;">
                <h3>📱 Marketing Agent</h3>
                <p>Create content, campaigns, and SEO optimization</p>
                <button onclick="executeAgent('marketing')" class="button button-primary">
                    Launch Agent
                </button>
            </div>

            <!-- Support Agent -->
            <div class="agent-card" style="border: 1px solid #ddd; padding: 1.5rem; border-radius: 8px;">
                <h3>👥 Support Agent</h3>
                <p>Handle tickets, FAQs, and customer support</p>
                <button onclick="executeAgent('support')" class="button button-primary">
                    Launch Agent
                </button>
            </div>

            <!-- Operations Agent -->
            <div class="agent-card" style="border: 1px solid #ddd; padding: 1.5rem; border-radius: 8px;">
                <h3>⚙️ Operations Agent</h3>
                <p>Manage deployment, monitoring, and DevOps</p>
                <button onclick="executeAgent('operations')" class="button button-primary">
                    Launch Agent
                </button>
            </div>

            <!-- Analytics Agent -->
            <div class="agent-card" style="border: 1px solid #ddd; padding: 1.5rem; border-radius: 8px;">
                <h3>📊 Analytics Agent</h3>
                <p>Generate reports, forecasts, and ML insights</p>
                <button onclick="executeAgent('analytics')" class="button button-primary">
                    Launch Agent
                </button>
            </div>

        </div>

        <div id="agent-response" style="margin-top: 2rem; padding: 1rem; background: #f5f5f5; border-radius: 8px; display: none;">
            <h3>Agent Response:</h3>
            <pre id="response-content"></pre>
        </div>
    </div>

    <script>
    async function executeAgent(agentId) {
        try {
            const response = await fetch('https://frontend-skkyroseco.vercel.app/api/v1/agents/execute', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    agent_id: agentId,
                    task: `Execute ${agentId} agent task`,
                    model: 'gpt-4'
                })
            });

            const data = await response.json();

            document.getElementById('agent-response').style.display = 'block';
            document.getElementById('response-content').textContent = JSON.stringify(data, null, 2);

        } catch (error) {
            alert('Error executing agent: ' + error.message);
        }
    }
    </script>

    <?php
    return ob_get_clean();
}

// Enqueue styles
add_action('wp_enqueue_scripts', 'devskyy_agents_enqueue_styles');

function devskyy_agents_enqueue_styles() {
    wp_enqueue_style('dashicons');
}
?>
```

---

### Step 3: Environment Configuration

Update WordPress environment variables in Vercel:

```bash
WORDPRESS_URL=https://skyyrose.co
WORDPRESS_USERNAME=your_wordpress_username
WORDPRESS_APP_PASSWORD=your_app_password
WORDPRESS_CLIENT_ID=123138
WORDPRESS_CLIENT_SECRET=<from .env.secrets>
```

---

### Step 4: Create Agent Pages on WordPress

Create these pages on WordPress.com:

1. **Homepage** - `/`
   - Add shortcode: `[devskyy_agents]`
   - Hero section showcasing the 6 agents

2. **Agents** - `/agents/`
   - List all available agents
   - Include `[devskyy_agents]` shortcode
   - Add descriptions and capabilities

3. **Dashboard** - `/dashboard/`
   - Link to: `https://frontend-skkyroseco.vercel.app`
   - Or embed iframe with agent control panel

4. **API Docs** - `/api/`
   - OpenAPI documentation
   - Link to: `https://frontend-skkyroseco.vercel.app/docs`

---

### Step 5: Configure WooCommerce Integration

If selling products on skyyrose.co:

1. Enable WooCommerce on WordPress.com
2. Add products with 3D models:

   ```php
   // Use WordPress3DMediaSync to attach 3D models
   $sync->sync_3d_model(
       product_id: $product_id,
       glb_url: 'https://cdn.skyyrose.com/models/product.glb',
       usdz_url: 'https://cdn.skyyrose.com/models/product.usdz'
   )
   ```

3. Customers can view 3D models in product pages
4. AR viewer available on mobile (USDZ format)

---

### Step 6: SSL & Security

✅ WordPress.com provides:

- Free SSL certificate (automatic)
- HTTPS redirect
- Jetpack security

✅ API Security:

- JWT authentication enabled
- CORS configured for skyyrose.co
- Rate limiting active

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│              skyyrose.co (WordPress.com)             │
├──────────────────────────────────────────────────────┤
│                                                      │
│  Homepage                                            │
│  ├── Agent Dashboard [devskyy_agents]                │
│  ├── Commerce Agent (Product Management)             │
│  ├── Creative Agent (Image/3D Generation)            │
│  ├── Marketing Agent (Content Creation)              │
│  ├── Support Agent (Customer Service)                │
│  ├── Operations Agent (DevOps)                       │
│  └── Analytics Agent (Reporting)                     │
│                                                      │
│  WooCommerce (Optional)                              │
│  ├── Products with 3D Models                         │
│  ├── AR Viewer (Mobile)                              │
│  └── Inventory Sync                                  │
│                                                      │
└──────────────────────────────────────────────────────┘
                          ↓ API Calls
┌──────────────────────────────────────────────────────┐
│       DevSkyy Backend (Vercel Serverless)            │
├──────────────────────────────────────────────────────┤
│  FastAPI + 6 SuperAgents                             │
│  - Commerce Agent                                    │
│  - Creative Agent                                    │
│  - Marketing Agent                                   │
│  - Support Agent                                     │
│  - Operations Agent                                  │
│  - Analytics Agent                                   │
│                                                      │
│  LLM Round Table (Multi-Provider Competition)        │
│  - OpenAI GPT-4                                      │
│  - Anthropic Claude                                  │
│  - Google Gemini                                     │
│  - Mistral                                           │
│  - Cohere                                            │
│  - Groq                                              │
│                                                      │
│  Database: Neon PostgreSQL                           │
└──────────────────────────────────────────────────────┘
```

---

## Quick Start Commands

```bash
# 1. Verify WordPress connection
python3 -c "from wordpress.client import WordPressClient; wp = WordPressClient.from_env(); print(wp.site_info())"

# 2. Sync 3D models (if using WooCommerce)
python3 examples/wordpress_3d_sync_demo.py

# 3. Test agent from WordPress
curl -X POST https://frontend-skkyroseco.vercel.app/api/v1/agents/execute \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "commerce", "task": "List products"}'
```

---

## Troubleshooting

**DNS not resolving?**

- Wait 24-48 hours for propagation
- Check DNS records at: <https://mxtoolbox.com/>

**Plugin not loading?**

- Verify SFTP upload to: `wp-content/plugins/devskyy-agents/`
- Activate plugin in WordPress.com admin

**API calls blocked?**

- Check CORS configuration in Vercel
- Verify JWT token in request headers
- Check rate limiting (25/sec per IP)

**3D models not displaying?**

- Verify GLB/USDZ URLs are accessible
- Check WooCommerce settings for custom meta fields

---

## Support

- **DevSkyy Docs**: `/Users/coreyfoster/DevSkyy/docs/`
- **WordPress Integration**: `/Users/coreyfoster/DevSkyy/wordpress/`
- **API Reference**: `https://frontend-skkyroseco.vercel.app/docs`
