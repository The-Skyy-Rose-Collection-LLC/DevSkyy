---
name: Luxury Fashion E-Commerce
description: Expert knowledge in luxury fashion e-commerce, high-end jewelry presentation, SkyyRose brand DNA, luxury customer experience, and premium product storytelling. Triggers on keywords like "luxury", "fashion", "jewelry", "high-end", "premium", "skyyrose", "collection", "product presentation", "luxury customer experience".
version: 1.0.0
---

# Luxury Fashion E-Commerce

Master the art of presenting luxury fashion and jewelry online with premium user experiences, brand storytelling, and high-end e-commerce patterns specific to SkyyRose.

## When to Use This Skill

Activate when working on:
- Product presentation and photography
- Collection storytelling and narrative
- Luxury customer journey design
- High-end checkout experiences
- VIP customer features
- Brand voice and copywriting
- Jewelry-specific features (sizing, materials, care)
- Premium packaging and unboxing
- Concierge services integration

## SkyyRose Brand DNA

### Core Values

```yaml
Brand: SkyyRose
Tagline: "Where Love Meets Luxury"
Founded: Oakland, CA
Aesthetic: Gothic Romance meets Modern Luxury

Core Values:
  - Authenticity: Handcrafted with genuine emotion
  - Luxury: Premium materials, impeccable craftsmanship
  - Storytelling: Every piece tells a love story
  - Empowerment: Jewelry as self-expression
  - Sustainability: Ethically sourced materials

Color Palette:
  Primary: "#B76E79"  # Rose Gold
  Secondary: "#2C2C2C"  # Deep Black
  Accent: "#E8C5A5"  # Champagne Gold
  Supporting:
    - "#1A1A1A"  # Midnight
    - "#F5F5F5"  # Soft White
    - "#8B4C54"  # Dark Rose

Typography:
  Headings: "Playfair Display" (Elegant Serif)
  Body: "Inter" (Clean Sans-Serif)
  Accents: "Cormorant" (Refined Serif)

Voice:
  Tone: Sophisticated yet warm, poetic yet clear
  Style: Conversational luxury (never pretentious)
  Emotion: Romantic, empowering, authentic
```

### Collections

**1. Signature Collection**
```yaml
Theme: "Oakland Love Story"
Aesthetic: Urban romance, Bay Area inspired
Key Elements:
  - Golden Gate Bridge motifs
  - Oakland skyline accents
  - Urban elegance
  - Everyday luxury

Price Range: $150 - $800
Target: Everyday luxury, accessible premium
Story: "Love letters to Oakland - where our story began"

Product Types:
  - Necklaces (layering pieces)
  - Earrings (statement and subtle)
  - Rings (stackable and solitaire)
  - Bracelets (delicate chains)
```

**2. Black Rose Collection**
```yaml
Theme: "Gothic Romance"
Aesthetic: Dark elegance, mysterious beauty
Key Elements:
  - Black diamonds
  - Oxidized metals
  - Rose motifs
  - Gothic architecture inspiration

Price Range: $300 - $2,000
Target: Bold statement pieces, alternative luxury
Story: "Beauty in darkness - love's complex nature"

Product Types:
  - Statement necklaces
  - Dramatic earrings
  - Cocktail rings
  - Cuffs and bangles

Immersive Experience:
  3D Environment: Gothic cathedral with stained glass
  Lighting: Moody, dramatic shadows
  Sound: Ambient gothic atmosphere
```

**3. Love Hurts Collection**
```yaml
Theme: "Passionate Rebellion"
Aesthetic: Edgy romance, vulnerable strength
Key Elements:
  - Heart + thorn motifs
  - Mixed metals
  - Asymmetrical designs
  - Raw crystal accents

Price Range: $200 - $1,500
Target: Emotionally expressive, storytelling pieces
Story: "Love's beautiful pain - wearing your heart"

Product Types:
  - Layered necklaces
  - Mismatched earrings
  - Statement rings
  - Chain details

Immersive Experience:
  3D Environment: Romantic castle ruins
  Lighting: Sunset rose gold glow
  Sound: Heartbeat rhythm
```

## Luxury Product Presentation

### High-End Product Photography

```html
<!-- Product Gallery (Luxury Standard) -->
<div class="luxury-product-gallery">
  <!-- Hero Image: Large, high-res -->
  <picture>
    <source srcset="product-hero-4k.avif" type="image/avif">
    <source srcset="product-hero-4k.webp" type="image/webp">
    <img
      src="product-hero-4k.jpg"
      alt="SkyyRose Signature Necklace in Rose Gold"
      width="2000"
      height="2000"
      loading="eager"
      fetchpriority="high"
    >
  </picture>

  <!-- Lifestyle Images -->
  <div class="lifestyle-gallery">
    <img src="lifestyle-1.jpg" alt="Model wearing necklace with evening dress">
    <img src="lifestyle-2.jpg" alt="Close-up showing craftsmanship detail">
    <img src="detail-1.jpg" alt="Clasp mechanism detail">
    <img src="packaging-1.jpg" alt="Luxury packaging and presentation">
  </div>

  <!-- 360° Viewer -->
  <div class="product-360">
    <canvas id="product-360-viewer"></canvas>
    <p class="instruction">Drag to rotate</p>
  </div>

  <!-- 3D Interactive Viewer -->
  <div class="product-3d-viewer">
    <!-- Three.js / Babylon.js integration -->
  </div>
</div>
```

### Product Description Copywriting

```markdown
## Good: Luxury Fashion Copy

### SkyyRose Midnight Rose Necklace

**Where Gothic Elegance Meets Modern Romance**

Hand-forged in oxidized sterling silver with conflict-free black diamonds,
each Midnight Rose tells a story of love's mysterious beauty. Our Oakland
artisans spend 40+ hours crafting every piece, ensuring the rose petals
catch light like secrets whispered in the dark.

**Materials:**
- Oxidized .925 Sterling Silver
- 0.5ct Conflict-Free Black Diamonds
- Hand-Applied Patina Finish

**Craftsmanship:**
- 40+ hours of artisan work
- Hand-forged rose petals
- Custom oxidation process
- Lifetime craftsmanship guarantee

**Sizing:**
- 16" chain (petite)
- 18" chain (standard) ← Most Popular
- 20" chain (statement)
- Custom lengths available

**Care:**
- Polish gently with included cloth
- Avoid harsh chemicals
- Store in provided velvet pouch
- Complimentary lifetime cleaning

**The Story:**
Inspired by Oakland's hidden rooftop gardens where roses grow between
urban steel, this piece embodies the beauty found in unexpected places.
Wear it as a reminder that love flourishes everywhere.

---

## Bad: Generic E-Commerce Copy

### Necklace

Nice silver necklace with black stones. Good quality. Available in
different sizes. Order now!
```

## Luxury Customer Journey

### Pre-Purchase Experience

```typescript
// Personalized Shopping Experience
interface LuxuryCustomerJourney {
  discovery: {
    // Immersive 3D collection tours
    immersiveCollectionTour: boolean;

    // Style quiz for recommendations
    personalStyleQuiz: {
      aesthetic: 'Classic' | 'Edgy' | 'Romantic' | 'Minimalist';
      occasion: 'Everyday' | 'Special' | 'Bridal' | 'Gift';
      priceRange: [number, number];
    };

    // AR try-on (future)
    augmentedRealityTryOn: boolean;
  };

  consideration: {
    // High-res zoom
    productZoom: '4K';

    // 360° viewer
    interactive360: true;

    // 3D model
    threeDimensionalView: true;

    // Size guide with hand model
    interactiveSizeGuide: true;

    // Video showing piece in motion
    lifestyleVideo: string[];

    // Customer testimonials
    curatedReviews: Review[];
  };

  purchase: {
    // White-glove checkout
    luxuryCheckout: true;

    // Gift options
    premiumGiftWrapping: boolean;
    personalizedMessage: string;

    // VIP options
    conciergeService: boolean;
    appointmentShopping: boolean;
  };

  postPurchase: {
    // Premium packaging
    luxuryUnboxing: true;

    // Lifetime services
    lifetimeCleaning: true;
    lifetimeResizing: true;

    // Care instructions
    personalizedCareGuide: PDF;

    // VIP access
    exclusivePreviewAccess: boolean;
    birthdayDiscount: number;
  };
}
```

### Luxury Checkout Flow

```html
<!-- White-Glove Checkout Experience -->
<div class="luxury-checkout">
  <!-- Progress Indicator (Elegant) -->
  <nav class="checkout-progress" aria-label="Checkout steps">
    <ol>
      <li class="completed">Cart</li>
      <li class="current">Shipping</li>
      <li>Payment</li>
      <li>Confirmation</li>
    </ol>
  </nav>

  <!-- Shipping with White-Glove Options -->
  <section class="checkout-section">
    <h2>Shipping & Delivery</h2>

    <div class="shipping-options">
      <!-- Standard Luxury -->
      <label class="shipping-option">
        <input type="radio" name="shipping" value="standard">
        <div class="option-details">
          <strong>Signature Delivery</strong>
          <p>5-7 business days • Insured • Signature required</p>
          <span class="price">Complimentary</span>
        </div>
      </label>

      <!-- Expedited -->
      <label class="shipping-option">
        <input type="radio" name="shipping" value="express">
        <div class="option-details">
          <strong>Express Delivery</strong>
          <p>2-3 business days • Fully insured • White-glove service</p>
          <span class="price">$35</span>
        </div>
      </label>

      <!-- VIP -->
      <label class="shipping-option luxury">
        <input type="radio" name="shipping" value="concierge">
        <div class="option-details">
          <strong>Concierge Delivery</strong>
          <p>Next day • Personal delivery • Gift presentation</p>
          <span class="price">$150</span>
        </div>
      </label>
    </div>

    <!-- Gift Options -->
    <div class="gift-options">
      <label>
        <input type="checkbox" name="gift_wrap">
        Premium Gift Wrapping (+$25)
      </label>

      <label>
        <input type="checkbox" name="gift_message">
        Include Personal Message
      </label>

      <textarea
        name="message"
        placeholder="Your heartfelt message..."
        maxlength="250"
      ></textarea>
    </div>
  </section>

  <!-- Payment (Secure, Premium) -->
  <section class="checkout-section">
    <h2>Payment</h2>

    <!-- Trust Badges -->
    <div class="trust-badges">
      <img src="/badges/secure-checkout.svg" alt="256-bit SSL Encryption">
      <img src="/badges/pci-compliant.svg" alt="PCI DSS Compliant">
      <img src="/badges/money-back.svg" alt="30-Day Returns">
    </div>

    <!-- Payment Methods -->
    <div class="payment-methods">
      <!-- Credit Card (default) -->
      <!-- PayPal -->
      <!-- Apple Pay -->
      <!-- Affirm (financing) -->
      <!-- Cryptocurrency (optional luxury) -->
    </div>

    <!-- Financing for luxury items -->
    <div class="financing-option">
      <p>Pay in 4 interest-free payments of $187.50 with Affirm</p>
      <button type="button">Learn More</button>
    </div>
  </section>

  <!-- Order Summary (Luxury Styled) -->
  <aside class="order-summary">
    <h3>Your Order</h3>

    <div class="summary-item">
      <img src="product-thumb.jpg" alt="Midnight Rose Necklace">
      <div>
        <p class="product-name">Midnight Rose Necklace</p>
        <p class="product-variant">18" Sterling Silver</p>
      </div>
      <p class="price">$750.00</p>
    </div>

    <div class="summary-totals">
      <div class="subtotal">
        <span>Subtotal</span>
        <span>$750.00</span>
      </div>
      <div class="shipping">
        <span>Signature Delivery</span>
        <span>Complimentary</span>
      </div>
      <div class="tax">
        <span>Tax</span>
        <span>$61.88</span>
      </div>
      <div class="total">
        <span>Total</span>
        <span>$811.88</span>
      </div>
    </div>

    <button type="submit" class="luxury-cta">
      Complete Your Order
    </button>

    <p class="guarantee">
      🔒 Secure checkout • 30-day returns • Lifetime guarantee
    </p>
  </aside>
</div>
```

## Jewelry-Specific Features

### Ring Size Guide

```html
<div class="ring-size-guide">
  <h3>Find Your Perfect Fit</h3>

  <!-- Interactive Size Chart -->
  <div class="size-chart-interactive">
    <svg viewBox="0 0 400 100">
      <!-- Visual hand model with ring placement -->
    </svg>

    <div class="size-selector">
      <button>US 5</button>
      <button>US 6</button>
      <button>US 7</button>
      <button class="popular">US 7.5 (Most Popular)</button>
      <button>US 8</button>
      <!-- ... -->
    </div>
  </div>

  <!-- Measurement Guide -->
  <details>
    <summary>How to Measure at Home</summary>
    <ol>
      <li>Cut a thin strip of paper</li>
      <li>Wrap around finger where ring will sit</li>
      <li>Mark where paper overlaps</li>
      <li>Measure length in mm</li>
      <li>Match to our size chart</li>
    </ol>
    <a href="/size-guide.pdf" download>Download Printable Guide</a>
  </details>

  <!-- Free Resizing Offer -->
  <div class="resizing-guarantee">
    <p>✨ <strong>Perfect Fit Guarantee</strong></p>
    <p>Complimentary resizing within 30 days</p>
  </div>
</div>
```

### Materials & Care

```html
<section class="materials-care">
  <h3>Materials & Craftsmanship</h3>

  <dl class="material-specs">
    <dt>Primary Metal</dt>
    <dd>
      .925 Sterling Silver
      <span class="info-tooltip" aria-label="92.5% pure silver">ⓘ</span>
    </dd>

    <dt>Gemstones</dt>
    <dd>
      0.5ct Black Diamonds (Conflict-Free)
      <span class="certification">
        <a href="/certifications/12345.pdf">View Certificate</a>
      </span>
    </dd>

    <dt>Finish</dt>
    <dd>Hand-Applied Oxidized Patina</dd>

    <dt>Weight</dt>
    <dd>12.5 grams</dd>

    <dt>Origin</dt>
    <dd>Handcrafted in Oakland, CA</dd>
  </dl>

  <h4>Care Instructions</h4>
  <ul class="care-instructions">
    <li>Polish gently with included microfiber cloth</li>
    <li>Avoid contact with perfumes, lotions, chlorine</li>
    <li>Store in provided velvet pouch when not wearing</li>
    <li>Remove before showering or swimming</li>
    <li><strong>Complimentary lifetime professional cleaning</strong></li>
  </ul>

  <a href="/care-guide" class="cta-link">Full Care Guide →</a>
</section>
```

## Premium UX Patterns

### Luxury Loading States

```tsx
// Don't show generic spinners - use branded loading
function LuxuryLoadingState() {
  return (
    <div className="luxury-loading">
      {/* Animated SkyyRose logo */}
      <svg className="loading-logo" viewBox="0 0 100 100">
        {/* Rose motif animation */}
      </svg>
      <p className="loading-text">Curating your experience...</p>
    </div>
  );
}
```

### Empty States

```tsx
// Luxury-appropriate empty states
function EmptyCartState() {
  return (
    <div className="empty-state luxury">
      <img src="/illustrations/empty-cart-luxury.svg" alt="">
      <h2>Your Collection Awaits</h2>
      <p>
        Begin your journey through handcrafted luxury.
        Each piece tells a story of love and artistry.
      </p>
      <Link href="/collections" className="luxury-cta">
        Explore Collections
      </Link>
    </div>
  );
}
```

## See Also

- `skills/immersive-3d-web-development/` - 3D product viewers
- `skills/interactive-web-development/` - Animations and interactions
- `skills/web-performance/` - High-res image optimization
- `skills/woocommerce-integration/` - E-commerce functionality

## References

See `references/` for:
- `luxury-copywriting-guide.md` - Brand voice and product descriptions
- `jewelry-photography-standards.md` - Image quality requirements
- `customer-journey-mapping.md` - Luxury UX flows
- `premium-checkout-patterns.md` - High-end conversion optimization

## Examples

See `examples/` for:
- `product-page-luxury.html` - Complete luxury product page
- `collection-landing.html` - Collection storytelling page
- `luxury-checkout-flow.html` - Premium checkout experience
- `vip-features.tsx` - Concierge and VIP functionality
