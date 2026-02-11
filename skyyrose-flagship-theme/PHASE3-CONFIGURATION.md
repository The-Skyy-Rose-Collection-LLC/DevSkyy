# Ralph Loop Deployment - Phase 3: Configuration Guide

## 3.1 WordPress Theme Settings

**Navigate to**: Appearance → Customize

### Site Identity
- **Site Title**: SkyyRose Flagship
- **Tagline**: Luxury Fashion in Immersive 3D
- **Site Icon**: Upload `assets/images/skyyrose-icon.png`
- **Logo**: Upload `assets/images/skyyrose-logo.png`

### Colors (Brand Colors)
- **Primary**: #B76E79 (Rose Gold)
- **Secondary**: #D4AF37 (Gold)
- **Accent**: #C0C0C0 (Metallic Silver)
- **Text**: #1A1A1A (Near Black)
- **Background**: #FFFFFF (White)

### Typography
- **Heading Font**: Playfair Display (Google Fonts)
- **Body Font**: Montserrat (Google Fonts)
- **Font Sizes**:
  - H1: 48px
  - H2: 36px
  - H3: 28px
  - Body: 16px

### Menus
**Primary Navigation** (Header):
- Home → /
- Collections → /collections/
- About → /about/
- Contact → /contact/

**Footer Navigation**:
- Privacy Policy → /privacy-policy/
- Terms of Service → /terms/
- Shipping & Returns → /shipping-returns/

## 3.2 WooCommerce Configuration

**Navigate to**: WooCommerce → Settings

### General Settings
- **Store Address**: (Your business address)
- **Currency**: USD ($)
- **Selling Location**: All countries
- **Shipping Location**: All countries

### Product Categories (Create These)
1. **Signature Collection** (slug: `signature-collection`)
2. **Love Hurts** (slug: `love-hurts`)
3. **Black Rose** (slug: `black-rose`)
4. **Preorder** (slug: `preorder`)

### Products → Attributes (For 3D Hotspots)
**Create Custom Attribute**: "3D Position"
- **Name**: 3D Position
- **Slug**: 3d-position
- **Type**: Text
- **Format**: "X,Y,Z" (e.g., "0,1.5,0")

## 3.3 Create 3D Collection Pages

**Navigate to**: Pages → Add New

### Page 1: Signature Collection 3D
- **Title**: Signature Collection 3D
- **Slug**: signature-collection-3d
- **Template**: Signature Collection 3D (Converted from HTML)
- **Content**: (Leave blank - template handles everything)
- **Publish**: Yes

### Page 2: Love Hurts 3D
- **Title**: Love Hurts Collection 3D
- **Slug**: love-hurts-3d
- **Template**: Love Hurts 3D (Converted from HTML)
- **Content**: (Leave blank)
- **Publish**: Yes

### Page 3: Black Rose 3D
- **Title**: Black Rose Collection 3D
- **Slug**: black-rose-3d
- **Template**: Black Rose 3D (Converted from HTML)
- **Content**: (Leave blank)
- **Publish**: Yes

### Page 4: Preorder Gateway
- **Title**: Preorder Gateway
- **Slug**: preorder-gateway
- **Template**: Preorder Gateway 3D (Converted from HTML)
- **Content**: (Leave blank)
- **Publish**: Yes

## 3.4 Configure Homepage

**Navigate to**: Settings → Reading

### Homepage Settings
- **Your homepage displays**: A static page
- **Homepage**: Select "Home" or create new page with:
  - **Template**: Homepage Custom Template
  - **Content**: (Template handles hero, featured collections, CTAs)

### Posts Page
- **Posts page**: Select "Blog" or create new

## 3.5 Navigation Menu Setup

**Navigate to**: Appearance → Menus

### Create "Primary" Menu
1. Add pages:
   - Home
   - Collections (custom link to /collections/)
   - About
   - Contact
2. **Menu Location**: Primary Navigation
3. **Save Menu**

### Create "Collections" Submenu (Under "Collections")
1. Signature Collection 3D → /signature-collection-3d/
2. Love Hurts 3D → /love-hurts-3d/
3. Black Rose 3D → /black-rose-3d/
4. Preorder Gateway → /preorder-gateway/

## 3.6 Validation Checklist

After completing configuration:

- [ ] Site identity configured (logo, icon, colors)
- [ ] Typography settings applied
- [ ] Primary menu created and assigned
- [ ] WooCommerce settings saved
- [ ] 4 product categories created
- [ ] 3D Position attribute created
- [ ] All 4 3D collection pages published
- [ ] Homepage set to static page
- [ ] Navigation menu displays correctly

## Next Steps

Once Phase 3 complete, proceed to:
- **Phase 4**: 3D Asset Verification (test Three.js, WebGL, hotspots)
- **Phase 5**: Brand Styling Verification (CSS, colors, fonts)
- **Phase 6**: WooCommerce Integration (create test products)

## Troubleshooting

**If menus don't appear**:
- Go to Appearance → Menus
- Verify "Primary Navigation" is checked under "Display Location"

**If 3D pages show blank**:
- Check template assignment (Page Attributes → Template)
- Verify JavaScript files loaded (DevTools → Network tab)

**If colors don't apply**:
- Clear WordPress cache
- Clear browser cache (Ctrl+Shift+R)

