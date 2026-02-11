# Phase 3: WordPress Configuration - Complete Checklist

## Quick Start (15 minutes total)

### STEP 1: WooCommerce Product Categories (2 min)

**Path**: https://wordpress.com → Products → Categories

**Action**: Click "Add New Category" 4 times with these values:

| Category Name | Slug | Description (Optional) |
|---------------|------|------------------------|
| Signature Collection | `signature-collection` | Foundation luxury pieces in rose gold and gold |
| Love Hurts | `love-hurts` | Beauty & the Beast inspired romantic collection |
| Black Rose | `black-rose` | Gothic garden collection in metallic silver |
| Preorder | `preorder` | Exclusive early access to upcoming releases |

**Validation**: Navigate to Products → Categories and verify all 4 appear in the list.

---

### STEP 2: Create 3D Collection Pages (5 min)

**Path**: https://wordpress.com → Pages → Add New

**Create 4 pages** (one at a time):

#### Page 1: Signature Collection 3D
```
Title: Signature Collection 3D
Slug: signature-collection-3d (auto-generated)
Template: Signature Collection 3D (Converted from HTML)
    ↳ Look for this in Page Attributes → Template dropdown
Content: (Leave blank - template handles everything)
Status: Publish (click blue button)
```

#### Page 2: Love Hurts Collection 3D
```
Title: Love Hurts Collection 3D
Slug: love-hurts-3d
Template: Love Hurts 3D (Converted from HTML)
Content: (Leave blank)
Status: Publish
```

#### Page 3: Black Rose Collection 3D
```
Title: Black Rose Collection 3D
Slug: black-rose-3d
Template: Black Rose 3D (Converted from HTML)
Content: (Leave blank)
Status: Publish
```

#### Page 4: Preorder Gateway
```
Title: Preorder Gateway
Slug: preorder-gateway
Template: Preorder Gateway 3D (Converted from HTML)
Content: (Leave blank)
Status: Publish
```

**Validation**: Navigate to Pages → All Pages and verify all 4 pages show "Published" status.

---

### STEP 3: Configure Homepage (2 min)

**Path**: https://wordpress.com → Settings → Reading

**Settings to change**:
```
☐ Your homepage displays
   ● A static page (select this radio button)
   
☐ Homepage dropdown
   → Select: "Home" (if exists)
   → OR create new page with Template: "Homepage Custom Template"
   
☐ Posts page (optional)
   → Select: "Blog" or leave as "— Select —"
```

**Click**: "Save Changes" button at bottom

**Validation**: Visit https://skyyrose.co and verify homepage loads (not blog posts).

---

### STEP 4: Create Primary Navigation Menu (5 min)

**Path**: https://wordpress.com → Appearance → Menus

**Step 4.1: Create Menu**
```
Menu Name: Primary
Click: "Create Menu"
```

**Step 4.2: Add Menu Items**

Left column shows available items. Add these in order:

1. **Home**
   - Find in "Pages" section
   - Click: [+ Add to Menu]

2. **Collections** (Custom Link)
   - Click: "Custom Links" tab
   - URL: `/collections/`
   - Link Text: `Collections`
   - Click: [Add to Menu]

3. **About**
   - Find in "Pages" section
   - Click: [+ Add to Menu]

4. **Contact**
   - Find in "Pages" section
   - Click: [+ Add to Menu]

**Step 4.3: Add Sub-Menu Items** (drag under Collections)

Add these 4 pages as children of "Collections":
- Signature Collection 3D → `/signature-collection-3d/`
- Love Hurts Collection 3D → `/love-hurts-3d/`
- Black Rose Collection 3D → `/black-rose-3d/`
- Preorder Gateway → `/preorder-gateway/`

**To create sub-menu**: Drag item slightly to the right under "Collections"

**Step 4.4: Assign Menu Location**
```
☑ Primary Navigation (check this box)
```

**Click**: "Save Menu" button

**Validation**: Visit https://skyyrose.co and verify navigation menu appears in header with Collections dropdown.

---

### STEP 5: Theme Customizer (Optional, 3 min)

**Path**: https://wordpress.com → Appearance → Customize

**Site Identity**:
```
Site Title: SkyyRose Flagship
Tagline: Luxury Fashion in Immersive 3D
Site Icon: Upload → /assets/images/skyyrose-icon.png
Logo: Upload → /assets/images/skyyrose-logo.png
```

**Colors** (if available in customizer):
```
Primary Color: #B76E79 (Rose Gold)
Secondary Color: #D4AF37 (Gold)
Accent Color: #C0C0C0 (Metallic Silver)
```

**Typography** (if available):
```
Heading Font: Playfair Display
Body Font: Montserrat
```

**Click**: "Publish" button at top

**Note**: WordPress.com Business plan may have limited customizer options. Colors and typography are already defined in theme CSS, so this step is optional.

---

## Final Validation Checklist

After completing all steps:

- [ ] Navigate to: https://skyyrose.co
- [ ] Verify homepage loads (not blog)
- [ ] Verify navigation menu in header shows: Home | Collections | About | Contact
- [ ] Click "Collections" dropdown → verify 4 3D pages listed
- [ ] Click "Signature Collection 3D" → page should load (may show loader if 3D not set up yet)
- [ ] Repeat for other 3 collection pages
- [ ] Navigate to: Products → Categories → verify 4 categories exist

---

## Troubleshooting

### Issue: Templates not showing in dropdown
**Cause**: Theme not activated properly
**Fix**: Go to Appearance → Themes → verify "SkyyRose Flagship" is active

### Issue: Menu doesn't appear on site
**Cause**: Menu not assigned to location
**Fix**: Appearance → Menus → check "Primary Navigation" box → Save Menu

### Issue: 3D pages show blank
**Cause**: Template selected but JavaScript not loading
**Fix**: This is expected until Phase 4 (3D Asset Verification) - just verify template is assigned

### Issue: "Collections" custom link shows 404
**Cause**: No page exists at /collections/
**Fix**: This is normal - the link is for future WooCommerce shop page. Ignore for now.

---

## Time Estimate

| Step | Time |
|------|------|
| WooCommerce Categories | 2 min |
| Create 4 Pages | 5 min |
| Configure Homepage | 2 min |
| Create Navigation Menu | 5 min |
| Theme Customizer (Optional) | 3 min |
| **Total** | **15-20 min** |

---

## What's Next?

Once Phase 3 complete, proceed to:

- **Phase 4**: 3D Asset Verification (verify Three.js loads, scenes render)
- **Phase 5**: Brand Styling Verification (CSS, colors, fonts)
- **Phase 6**: WooCommerce Integration (create test products)
- **Phase 7**: Performance Testing (Lighthouse re-audit)

---

## Support Commands

Clear WordPress cache after configuration:
```
WordPress.com → Hosting Configuration → Performance → Clear Cache
```

Test 3D page directly:
```
https://skyyrose.co/signature-collection-3d/
```

Check if pages published:
```
WordPress.com → Pages → All Pages
```

---

**Status**: Ready to execute  
**Estimated Time**: 15-20 minutes  
**Prerequisites**: SkyyRose Flagship theme activated, WooCommerce plugin installed
