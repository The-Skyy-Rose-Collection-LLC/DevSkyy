# SkyyRose Elementor Page Customization Guide

**Complete step-by-step guide to customize your 6 pages using Elementor**

---

## 🎨 SkyyRose Brand Colors & Styling

Before you start, here are the brand colors to use consistently:

```
Primary Color:    #B76E79 (Dusty Rose/Mauve)
Secondary Color:  #1A1A1A (Black)
Accent Gold:      #D4AF37 (Gold)
Light Bg:         #F8F8F8 (Off-white)
Text Dark:        #2A2A2A (Dark Gray)
Text Light:       #FFFFFF (White)
```

**Typography**:

- Headings: Bold, serif fonts (Georgia, Playfair Display)
- Body: Clean sans-serif (Open Sans, Roboto)
- Logo: "SkyyRose - Where Love Meets Luxury"

---

## 📄 Page-by-Page Customization

### **Page 1: HOME PAGE**

**URL**: <https://skyyrose.co/home>
**Edit Link**: <https://wordpress.com/page/skyyrose.co/150>

#### Hero Section

1. Open page in Elementor
2. Add a Hero widget with:
   - **Headline**: "SkyyRose - Where Love Meets Luxury"
   - **Subheadline**: "Immersive 3D Collection Experiences"
   - **Background**: Dark image or gradient (#1A1A1A to #2A2A2A)
   - **Button**: "Explore Collections" → links to /collections page
   - **Text Color**: White
   - **Button Color**: #B76E79

#### Featured Collections Section

3. Add Image Box widget (3 columns) for each collection:

   **Column 1 - SIGNATURE**
   - Image: Use first signature model or collection photo
   - Title: "Signature Collection"
   - Description: "Luxury outdoor experiences"
   - Button: "View" → /signature
   - Badge: "27 Models"

   **Column 2 - LOVE HURTS**
   - Image: Love Hurts collection preview
   - Title: "Love Hurts Collection"
   - Description: "Castle ballroom moments"
   - Button: "View" → /love-hurts
   - Badge: "31 Models"

   **Column 3 - BLACK ROSE**
   - Image: Black Rose collection preview
   - Title: "Black Rose Collection"
   - Description: "Gothic rose garden"
   - Button: "View" → /black-rose
   - Badge: "Coming Soon"

#### About Mini Section

4. Add Text Block:
   - **Heading**: "About SkyyRose"
   - **Text**: 2-3 lines about brand
   - **Button**: "Read More" → /about

#### Press Mentions Section

5. Add Logo Grid or Text Grid:
   - Show 3-4 press logos or mentions
   - "Featured in: Vogue, Harper's Bazaar, Forbes"

#### CTA Section

6. Add Call-To-Action:
   - **Text**: "Pre-Order Your Favorites"
   - **Button**: "Browse Collections" → /collections
   - **Background**: #B76E79 (dusty rose)
   - **Text**: White

#### Footer

7. Add Footer widget with:
   - Copyright text
   - Social media links (Instagram, TikTok, etc.)
   - Contact info
   - Quick links

---

### **Page 2: COLLECTIONS**

**URL**: <https://skyyrose.co/collections>
**Edit Link**: <https://wordpress.com/page/skyyrose.co/151>

#### Title Section

1. Add Heading: "Our Collections"
2. Add Text: "Explore immersive 3D experiences across three unique collections"

#### Collections Grid (3 Cards)

3. Add 3 Image Cards in a grid:

   **Card 1 - Signature**
   - Image: Signature collection hero
   - Overlay Title: "Signature Collection"
   - Overlay Text: "57 3D Models"
   - Link: /signature
   - Hover Effect: Fade/Zoom

   **Card 2 - Love Hurts**
   - Image: Love Hurts collection hero
   - Overlay Title: "Love Hurts Collection"
   - Overlay Text: "31 3D Models"
   - Link: /love-hurts
   - Hover Effect: Fade/Zoom

   **Card 3 - Black Rose**
   - Image: Black Rose collection hero
   - Overlay Title: "Black Rose Collection"
   - Overlay Text: "Coming Soon"
   - Link: /black-rose
   - Hover Effect: Fade/Zoom (Slightly grayed out)

#### Features Section

4. Add 3-column Feature widget:
   - **Feature 1**:
     - Icon: 3D cube
     - Title: "Interactive 3D Models"
     - Text: "Rotate, zoom, and explore products in 3D"
   - **Feature 2**:
     - Icon: Mobile/AR
     - Title: "AR Quick Look"
     - Text: "View products in your space on iOS"
   - **Feature 3**:
     - Icon: Heart
     - Title: "Exclusive Experiences"
     - Text: "Immersive brand storytelling in 3D"

#### CTA

5. Add Banner:
   - "Ready to explore?"
   - Button: "Start Now" → /signature
   - Background: #1A1A1A, Text: White

---

### **Page 3: SIGNATURE COLLECTION**

**URL**: <https://skyyrose.co/signature>
**Edit Link**: <https://wordpress.com/page/skyyrose.co/152>

#### Hero

1. Add Hero Section:
   - **Title**: "Signature Collection"
   - **Subtitle**: "Luxury Outdoor Experiences"
   - **Background**: Luxury garden/outdoor image

#### Collection Description

2. Add Rich Text Block:

   ```
   The Signature Collection represents the pinnacle of luxury and
   sophistication. Each piece is crafted with precision and paired
   with stunning 3D visualizations of immersive outdoor experiences.

   57 Unique Products | Pre-Order Now | Free Shipping Over $150
   ```

#### 3D Model Viewer Section

3. Add Elementor "Image Gallery" widget:
   - **Title**: "Explore Our Models"
   - **Description**: "Click to view 3D models"
   - Add all 57 models from media library
   - Configure as Grid (4-5 columns)
   - Enable Lightbox
   - Filter/Search enabled

#### Featured Products (Top 5)

4. Add 5-Column Product Cards:
   - For each top product:
     - Product image thumbnail
     - Product name
     - 3D model thumbnail
     - "View Details" button
     - Price or "Pre-Order" button
   - Colors: #B76E79 buttons, dark text

#### Hotspot Interactive Map

5. Add Code/Embed widget:

   ```html
   <!-- Add Three.js viewer embed here -->
   <div id="three-viewer">
     <!-- 3D hotspot experience -->
   </div>
   ```

   (This will be added after 3D models are uploaded)

#### CTA Banner

6. Add Banner:
   - "Ready to pre-order?"
   - Button: "View All Items" → Product page
   - Button: "Learn More" → /about
   - Background: #B76E79, Text: White

#### Related Collections

7. Add Navigation:
   - Previous: ← Love Hurts
   - Next: Black Rose →

---

### **Page 4: LOVE HURTS COLLECTION**

**URL**: <https://skyyrose.co/love-hurts>
**Edit Link**: <https://wordpress.com/page/skyyrose.co/154>

#### Hero

1. Add Hero Section:
   - **Title**: "Love Hurts Collection"
   - **Subtitle**: "Castle Ballroom Moments"
   - **Background**: Elegant castle/ballroom image
   - **Text Color**: White
   - **Button**: "Explore Now"

#### Collection Story

2. Add Text with Image Block:
   - **Heading**: "A Collection Born From Romance"
   - **Text**: 2-3 paragraphs about the collection's inspiration
   - **Image**: Collection hero image on side
   - **Layout**: Text left, Image right

#### 3D Model Gallery

3. Add Elementor Gallery:
   - **Title**: "31 Exclusive Models"
   - Grid of 31 3D model thumbnails
   - Lightbox enabled
   - Filter by category (if organized)

#### Product Showcase

4. Add Carousel widget:
   - Display top 10 products in carousel
   - Each item: Image + Name + Price/PreOrder
   - Navigation arrows
   - Auto-play every 3 seconds

#### Immersive Experience Section

5. Add Banner with Video/3D Viewer:
   - **Title**: "Immerse Yourself"
   - **Description**: "Experience the castle ballroom in 3D"
   - Embed 3D viewer or video demo
   - "Start Experience" button

#### Pricing & Shipping

6. Add Info Boxes (3 columns):
   - **Box 1**:
     - Icon: Tag
     - Title: "Pre-Order Pricing"
     - Text: "Early access pricing available now"
   - **Box 2**:
     - Icon: Truck
     - Title: "Free Shipping"
     - Text: "On orders over $150"
   - **Box 3**:
     - Icon: Calendar
     - Title: "Delivery"
     - Text: "5-7 business days"

#### Navigation

7. Add Previous/Next:
   - ← Signature | Black Rose →

---

### **Page 5: BLACK ROSE COLLECTION**

**URL**: <https://skyyrose.co/black-rose>
**Edit Link**: <https://wordpress.com/page/skyyrose.co/153>

#### Hero

1. Add Hero Section:
   - **Title**: "Black Rose Collection"
   - **Subtitle**: "Gothic Rose Garden - Coming Soon"
   - **Background**: Dark, moody rose garden image
   - **Banner Badge**: "Coming Soon"
   - **Button**: "Notify Me" → Email capture form

#### Collection Preview

2. Add Rich Text:

   ```
   The Black Rose Collection showcases an exquisite exploration of
   gothic elegance and dark romance. This collection features 11
   stunning pieces set in a hauntingly beautiful rose garden.

   STATUS: Launching January 2026
   PRE-REGISTRATIONS: Open
   ```

#### Email Capture Form

3. Add Form:
   - Field 1: Email
   - Field 2: Interest (Checkbox)
   - Button: "Notify Me When Available"
   - Success Message: "Thanks! We'll notify you at launch"
   - Redirect to: Success page

#### Teaser Section

4. Add Image Gallery (3 images):
   - 3 sneak peek images
   - Text overlay: "Coming January 2026"
   - Slightly blurred/darkened

#### What to Expect

5. Add Feature Section (3 columns):
   - **Feature 1**: "11 Exclusive Designs"
   - **Feature 2**: "Gothic Inspiration"
   - **Feature 3**: "3D + AR Experience"

#### Navigation

6. Add Links:
   - ← Love Hurts | Home →

---

### **Page 6: ABOUT SKYYROSE**

**URL**: <https://skyyrose.co/about>
**Edit Link**: <https://wordpress.com/page/skyyrose.co/155>

#### Hero

1. Add Hero:
   - **Title**: "About SkyyRose"
   - **Subtitle**: "Where Love Meets Luxury"

#### Brand Story

2. Add Text + Image Block:
   - **Heading**: "Our Story"
   - **Story Text**: 3-4 paragraphs about brand origin
   - **Image**: Brand founder/team photo
   - **Layout**: Image left, text right

#### Mission & Values

3. Add 3-Column Feature:
   - **Column 1**:
     - Icon: Heart
     - Title: "Our Mission"
     - Text: "To create immersive experiences..."
   - **Column 2**:
     - Icon: Star
     - Title: "Quality First"
     - Text: "Every product is crafted with precision..."
   - **Column 3**:
     - Icon: Globe
     - Title: "Global Community"
     - Text: "Serving customers worldwide..."

#### Timeline

4. Add Timeline widget:
   - **2020**: "Founded SkyyRose"
   - **2021**: "Launched first collection"
   - **2022**: "Expanded to 3D experiences"
   - **2023**: "Featured in major publications"
   - **2024**: "Added AR Quick Look"
   - **2025**: "3-collection lineup complete"

#### Press & Recognition

5. Add Logo Grid:
   - **Title**: "Featured In"
   - Logos: Vogue, Harper's Bazaar, Forbes, etc.
   - Quotes from publications

#### Team

6. Add Team Grid (if available):
   - Team member photos
   - Names and roles
   - Social media links

#### CTA

7. Add Banner:
   - "Join Our Community"
   - Button: "Subscribe to Newsletter"
   - Secondary: "Follow Us" (social icons)
   - Background: #B76E79, Text: White

#### Contact

8. Add Contact Section:
   - Email
   - Phone
   - Social media links
   - Contact form

---

## 🎬 How to Edit Pages in Elementor

### Step 1: Access Elementor

1. Login to WordPress: <https://wordpress.com/dashboard/home/skyyrose.co>
2. Go to Pages
3. Find your page (e.g., "Home")
4. Click "Edit"
5. Choose "Edit with Elementor" button

### Step 2: Add Sections

In Elementor:

1. Click "+" icon to add new section
2. Choose layout (1 column, 2 columns, 3 columns, etc.)
3. Drag from left panel to section

### Step 3: Add Widgets

1. Click "+" in section
2. Search for widget type (Heading, Text, Image, Gallery, etc.)
3. Drag widget to section
4. Edit widget settings on right panel

### Step 4: Style Elements

For each widget:

1. Open widget settings (gear icon)
2. Content tab: Add text, images, links
3. Style tab: Colors, fonts, spacing
4. Advanced tab: Custom CSS, responsive settings

### Step 5: Preview & Publish

1. Click "Preview" to see live version
2. Click "Update" to save changes
3. Click "Publish" when ready to go live

---

## 🎨 Styling Tips

### Colors

- Use #B76E79 for CTA buttons and highlights
- Use #1A1A1A for dark sections and text
- Use #F8F8F8 for light backgrounds
- Ensure good contrast for readability

### Typography

- Heading: Large, bold, serif (40-60px)
- Subheading: Medium, serif (24-32px)
- Body: Regular weight, sans-serif (16-18px)
- Links: Underlined, #B76E79

### Layout

- Use whitespace generously
- Sections should have padding (40-60px)
- Images should be high-quality and optimized
- Mobile-first design (test on phone!)

### Performance

- Optimize images before uploading
- Use lazy loading for images
- Minimize animations (affects loading speed)
- Test Core Web Vitals after changes

---

## 📱 Mobile Optimization

After styling each page:

1. **Preview on Mobile**: Click responsive icon (bottom right of Elementor)
2. **Check Breakpoints**:
   - Desktop: 1920px+
   - Tablet: 768px-1024px
   - Mobile: 320px-767px
3. **Adjust for Mobile**:
   - Stack columns on mobile
   - Reduce image sizes
   - Increase button sizes
   - Adjust font sizes

---

## 🔗 Internal Links to Use

| Page | Link |
|------|------|
| Home | /home |
| Collections | /collections |
| Signature | /signature |
| Love Hurts | /love-hurts |
| Black Rose | /black-rose |
| About | /about |

---

## ✅ Customization Checklist

### Home Page

- [ ] Hero section with headline and CTA
- [ ] 3 collection cards with images
- [ ] About section
- [ ] Press mentions
- [ ] Footer with links

### Collections Page

- [ ] Title and description
- [ ] 3 collection grid cards
- [ ] Features section (3 columns)
- [ ] CTA banner

### Signature Collection

- [ ] Hero with title
- [ ] Description text
- [ ] 57-model gallery
- [ ] Top products showcase
- [ ] Related collections navigation

### Love Hurts Collection

- [ ] Hero section
- [ ] Collection story with image
- [ ] 31-model gallery
- [ ] Product carousel
- [ ] Pricing/shipping info
- [ ] Navigation

### Black Rose Collection

- [ ] Hero with "Coming Soon" badge
- [ ] Email capture form
- [ ] Teaser images
- [ ] What to expect section
- [ ] Navigation

### About Page

- [ ] Brand story with images
- [ ] Mission & values (3 columns)
- [ ] Timeline
- [ ] Press recognition
- [ ] Contact information
- [ ] Newsletter signup

---

## 🚀 Next Steps After Customization

1. **Upload 3D Models** (88 files)
   - Add to media library
   - Organize by collection

2. **Add 3D Viewers**
   - Insert model galleries on collection pages
   - Configure interactive hotspots

3. **Test Everything**
   - Desktop, tablet, mobile
   - All links working
   - Images loading properly
   - Forms submitting

4. **Verify Performance**
   - Core Web Vitals
   - Page load times
   - Mobile friendliness

5. **Submit to Search Engines**
   - Google Search Console
   - Bing Webmaster Tools
   - Verify sitemap

---

## 💡 Pro Tips

1. **Save Often**: Use keyboard shortcut (Cmd+S or Ctrl+S)
2. **Use Templates**: WordPress has pre-built templates - try them!
3. **Duplicate Sections**: If a section works well, duplicate it for other pages
4. **Test Forms**: Make sure email capture works before launch
5. **Image Optimization**: Use tools like Smush to compress images
6. **Caching**: Enable WordPress caching for better performance
7. **Mobile First**: Always design for mobile first, then scale up
8. **Accessibility**: Add alt text to all images for SEO

---

## 🎯 Success Criteria

Your pages are customized when:

- ✅ All text content added and edited
- ✅ All brand colors applied correctly
- ✅ Images optimized and uploaded
- ✅ Links tested and working
- ✅ Mobile design responsive
- ✅ Forms functional
- ✅ CTAs visible and clickable
- ✅ No broken images
- ✅ Page loads under 3 seconds
- ✅ Core Web Vitals passing

---

**Ready to customize? Start with the Home page, then move to Collections. Once pages are styled, upload your 3D models!** 🎨

Questions? Check Elementor's official documentation at elementor.com/help
