# SkyyRose Collection Pages - Deployment Guide

**Stage 4.12: WordPress Collection Page Integration with Agent Templates**

---

## 🚀 Quick Start - Go Live in 5 Steps

### Step 1: Verify WordPress Configuration
```bash
# Test WordPress connection
python3 -c "
from wordpress.collection_page_manager import WordPressConfig
config = WordPressConfig(
    wp_url='https://skyyrose.com',  # Your WordPress URL
    username='admin',
    app_password='xxxx xxxx xxxx xxxx'
)
print(f'✅ WordPress API Ready: {config.base_url}')
"
```

### Step 2: Upload 3D Experiences
```python
import asyncio
from wordpress.collection_page_manager import (
    WordPressCollectionPageManager,
    WordPressConfig,
    CollectionType
)

async def deploy():
    config = WordPressConfig(
        wp_url='https://skyyrose.com',
        username='admin',
        app_password='xxxx xxxx xxxx xxxx'
    )

    async with WordPressCollectionPageManager(config) as manager:
        # Upload BLACK ROSE experience
        media = await manager.upload_3d_experience(
            file_path='wordpress/collection_templates/skyyrose-black-rose-garden-production.html',
            collection_type=CollectionType.BLACK_ROSE
        )
        print(f"✅ Uploaded: {media['source_url']}")

asyncio.run(deploy())
```

### Step 3: Create Collection Pages
```python
async def create_pages():
    config = WordPressConfig(
        wp_url='https://skyyrose.com',
        username='admin',
        app_password='xxxx xxxx xxxx xxxx'
    )

    async with WordPressCollectionPageManager(config) as manager:
        # Create BLACK ROSE collection page
        page = await manager.create_collection_page(
            collection_type=CollectionType.BLACK_ROSE,
            media_url='https://skyyrose.com/wp-content/uploads/2024/12/black-rose.html',
            products=[
                {
                    'name': 'Black Rose Pendant',
                    'price': '$185',
                    'description': 'Exquisite dark elegance'
                }
            ]
        )
        print(f"✅ Created page: {page['link']}")

asyncio.run(create_pages())
```

### Step 4: Enable Agent Template Reference
```python
from agents.collection_content_agent import create_collection_content_agent

# Create agent with built-in design templates
agent = create_collection_content_agent()

# Agent can now reference templates for consistency
templates = agent.get_all_templates()
print(f"✅ Agent has {len(templates)} design templates loaded")

# Agent can recover if design breaks
recovery = agent.recover_collection_design(
    collection_type='black_rose',
    issue_description='Color scheme incorrect'
)
```

### Step 5: Publish Pages
```python
async def publish():
    config = WordPressConfig(
        wp_url='https://skyyrose.com',
        username='admin',
        app_password='xxxx xxxx xxxx xxxx'
    )

    async with WordPressCollectionPageManager(config) as manager:
        # Get draft pages and publish
        pages = await manager.list_collection_pages()

        for page in pages:
            if page['status'] == 'draft':
                await manager.publish_page(page['id'])
                print(f"✅ Published: {page['title']}")

asyncio.run(publish())
```

---

## 📋 Collection Pages Reference

### BLACK ROSE Garden
- **URL**: `/collections/black-rose-garden`
- **File**: `skyyrose-black-rose-garden-production.html` (30 KB)
- **Colors**: Black (#000000), Silver (#C0C0C0), White (#FFFFFF)
- **Theme**: Dark elegance, gothic luxury
- **Experience**: Virtual dark garden with spotlight effects

**Agent Template Available**: `CollectionContentAgent.get_design_template('black_rose')`

### LOVE HURTS Castle
- **URL**: `/collections/love-hurts-castle`
- **File**: `skyyrose-love-hurts-castle-production.html` (31 KB)
- **Colors**: Burgundy (#8B4049), Rose (#C9356C), Pink (#FF6B9D)
- **Theme**: Emotional expression, vulnerability
- **Experience**: Castle interior with dramatic lighting

**Agent Template Available**: `CollectionContentAgent.get_design_template('love_hurts')`

### SIGNATURE Runway
- **URL**: `/collections/signature-runway`
- **File**: `skyyrose-signature-runway-production.html` (19 KB)
- **Colors**: Gold (#C9A962), Bright Gold (#FFD700), Black (#000000)
- **Theme**: Premium essentials, Oakland heritage
- **Experience**: Fashion runway with gold accents

**Agent Template Available**: `CollectionContentAgent.get_design_template('signature')`

---

## 🔐 Authentication & Configuration

### WordPress REST API Requirements
```bash
# Enable REST API in WordPress
1. Settings → Permalinks → Save Changes (refreshes REST)
2. Settings → Users → Create App Password for admin
3. Copy: "xxxx xxxx xxxx xxxx" format
```

### Environment Variables
```bash
# .env file
WORDPRESS_URL=https://skyyrose.com
WORDPRESS_USERNAME=admin
WORDPRESS_APP_PASSWORD=xxxx xxxx xxxx xxxx
REDIS_URL=redis://localhost  # Optional caching

# Agent configuration
export ANTHROPIC_API_KEY=sk-...
export OPENAI_API_KEY=sk-...
```

### Verify Connection
```python
from wordpress.collection_page_manager import WordPressConfig, WordPressCollectionPageManager
import asyncio

async def test_connection():
    config = WordPressConfig(
        wp_url='https://skyyrose.com',
        username='admin',
        app_password='xxxx xxxx xxxx xxxx'
    )

    try:
        async with WordPressCollectionPageManager(config) as manager:
            pages = await manager.list_collection_pages()
            print(f"✅ Connected! Found {len(pages)} pages")
    except Exception as e:
        print(f"❌ Connection failed: {e}")

asyncio.run(test_connection())
```

---

## 🎨 Design Consistency Check

### Automated Validation
```python
from agents.collection_content_agent import create_collection_content_agent

agent = create_collection_content_agent()

# Validate a collection's design
validation = await agent.validate_collection_design(
    collection_type='black_rose',
    design_data={
        'colors': {
            'primary': '#000000',
            'secondary': '#C0C0C0'
        },
        'theme': 'Dark Elegance, Mystery, Exclusivity'
    }
)

if validation['status'] == 'success':
    print("✅ Design is consistent with template")
else:
    print(f"⚠️ Issues found: {validation['result']}")
```

### Manual Template Reference
```python
from wordpress.collection_page_manager import CollectionDesignTemplates, CollectionType

# Get exact template specifications
template = CollectionDesignTemplates.get_template(CollectionType.BLACK_ROSE)

print(f"Name: {template.name}")
print(f"Colors: {template.colors}")
print(f"Theme: {template.theme}")
print(f"Description: {template.description}")
```

---

## 🚨 Recovery Protocol

### If Design Breaks
```python
from agents.collection_content_agent import create_collection_content_agent

agent = create_collection_content_agent()

# Get recovery instructions
recovery = await agent.recover_collection_design(
    collection_type='black_rose',
    issue_description='Colors changed to incorrect values'
)

print(f"Recovery Status: {recovery['status']}")
print(f"Instructions:\n{recovery['result']}")
```

### Restore from HTML Template
```bash
# All original HTML files are stored in:
ls -la wordpress/collection_templates/

# Copy back to WordPress media if needed
# Files are also available as templates in agent system
```

### Manual Restoration
1. **Get Template**: `CollectionDesignTemplates.get_template(CollectionType.BLACK_ROSE)`
2. **Restore Colors**: Use exact HEX values from template
3. **Verify Theme**: Check alignment with theme statement
4. **Redeploy**: Re-upload HTML experience to WordPress

---

## 📊 Status Dashboard

### Check Page Status
```python
async def check_status():
    config = WordPressConfig(...)

    async with WordPressCollectionPageManager(config) as manager:
        pages = await manager.list_collection_pages()

        for page in pages:
            status = page.get('status', 'unknown')
            url = page.get('link', 'N/A')
            print(f"{page['title']}: {status} ({url})")

asyncio.run(check_status())
```

### Monitor 3D Experience Performance
- Browser console for WebGL errors
- Performance tab for load times
- Network tab for asset delivery
- Mobile test for responsive behavior

---

## 🔗 API Endpoints

### List Pages
```
GET /wp-json/wp/v2/pages?per_page=100
```

### Create Page
```
POST /wp-json/wp/v2/pages
Body: {
  "title": "BLACK ROSE Garden",
  "slug": "black-rose-garden",
  "content": "...",
  "status": "draft"
}
```

### Upload Media
```
POST /wp-json/wp/v2/media
Body: multipart/form-data with file
```

### Update Page
```
POST /wp-json/wp/v2/pages/{id}
Body: {
  "status": "publish",
  "content": "..."
}
```

---

## ✅ Pre-Launch Checklist

- [ ] WordPress REST API enabled
- [ ] App password created and verified
- [ ] Redis configured (optional but recommended)
- [ ] 3D HTML files uploaded to `wordpress/collection_templates/`
- [ ] Agent templates loaded: `CollectionContentAgent.get_all_templates()`
- [ ] Connection test passes: `WordPressCollectionPageManager` connects
- [ ] Pages created in draft status
- [ ] Design validation passes
- [ ] 3D experiences load correctly in browser
- [ ] Mobile responsive verified
- [ ] SEO metadata added
- [ ] Performance benchmarks met (< 3s load time)
- [ ] Analytics tracking configured
- [ ] Backup of templates created
- [ ] Pages published and live

---

## 📦 File Structure

```
wordpress/
├── collection_page_manager.py      # Core page manager
├── collection_deployment_guide.md  # This file
├── collection_templates/
│   ├── skyyrose-black-rose-garden-production.html
│   ├── skyyrose-love-hurts-castle-production.html
│   └── skyyrose-signature-runway-production.html
└── README_3D_SYNC.md

agents/
├── collection_content_agent.py     # Agent with templates
└── ...

docs/
├── COLLECTION_DEPLOYMENT.md
└── guides/
    └── WORDPRESS_INTEGRATION.md
```

---

## 🎯 Next Steps

1. **Configure credentials** in `.env`
2. **Test connection** with verification script
3. **Upload designs** using `upload_3d_experience()`
4. **Create pages** with `create_collection_page()`
5. **Validate design** consistency
6. **Publish** pages
7. **Monitor** performance
8. **Use agent templates** for future updates

---

## 📞 Support & Recovery

### Get Agent Template Reference
```python
agent = create_collection_content_agent()
template = agent.get_design_template('black_rose')
# Returns full template with colors, theme, instructions
```

### Trigger Design Recovery
```python
recovery = await agent.recover_collection_design(
    collection_type='black_rose',
    issue_description='Describe the issue here'
)
# Returns recovery steps and template references
```

### Access Original Files
```bash
# All 3D experiences permanently stored in:
wordpress/collection_templates/
# Serve directly or re-upload to WordPress
```

---

**Ready to Deploy! 🚀**

All collections have design templates stored in the agent system.
If anything breaks, agents can reference templates to recover.

Last Updated: 2024-12-19
Status: Production Ready
