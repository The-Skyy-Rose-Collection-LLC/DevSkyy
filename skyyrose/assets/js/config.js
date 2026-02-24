// SkyyRose Experience - Configuration
// This will be replaced with WordPress REST API calls in Phase 3

const CONFIG = {
  // Scene images
  images: {
    'black-rose': {
      webp: 'assets/images/scenes/black-rose-garden-desktop.webp',
      jpeg: 'assets/images/scenes/black-rose-garden-desktop.jpg',
      mobile: {
        webp: 'assets/images/scenes/black-rose-garden-mobile.webp',
        jpeg: 'assets/images/scenes/black-rose-garden-mobile.jpg'
      }
    },
    'love-hurts': {
      webp: 'assets/images/scenes/love-hurts-ballroom-desktop.webp',
      jpeg: 'assets/images/scenes/love-hurts-ballroom-desktop.jpg',
      mobile: {
        webp: 'assets/images/scenes/love-hurts-ballroom-mobile.webp',
        jpeg: 'assets/images/scenes/love-hurts-ballroom-mobile.jpg'
      }
    },
    'signature-waterfront': {
      png: '../assets/scenes/signature/signature-waterfront-runway.png',
      jpeg: '../assets/scenes/signature/signature-waterfront-runway.png',
      mobile: {
        png: '../assets/scenes/signature/signature-waterfront-runway.png',
        jpeg: '../assets/scenes/signature/signature-waterfront-runway.png'
      }
    },
    'signature-showroom': {
      png: '../assets/scenes/signature/signature-golden-gate-showroom.png',
      jpeg: '../assets/scenes/signature/signature-golden-gate-showroom.png',
      mobile: {
        png: '../assets/scenes/signature/signature-golden-gate-showroom.png',
        jpeg: '../assets/scenes/signature/signature-golden-gate-showroom.png'
      }
    }
  },

  // Room definitions
  rooms: [
    {
      id: 'black-rose',
      collection: 'BLACK ROSE',
      name: 'The Garden',
      accent: '#B76E79',
      description: 'Gothic romance meets dark florals',
      hotspots: [
        {
          x: 25,
          y: 40,
          product: {
            id: 'br-001',
            collection: 'BLACK ROSE',
            name: 'BLACK Rose Crewneck',
            tagline: 'Gothic elegance meets street style',
            description: 'SkyyRose BLACK Rose Crewneck: gothic luxury blooms in twilight. Embroidered with defiant elegance, a dark romance woven in every thread.',
            price: '$125',
            spec: 'Premium Cotton • Relaxed Oversized Fit • Machine Wash Cold',
            badge: 'PRE-ORDER',
            image: 'assets/images/products/br-001/br-001-model.jpg',
            url: '/?product_id=br-001',
            variants: {
              sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'],
              colors: [{ name: 'Black', hex: '#000000' }]
            }
          }
        },
        {
          x: 60,
          y: 35,
          product: {
            id: 'br-002',
            collection: 'BLACK ROSE',
            name: 'BLACK Rose Joggers',
            tagline: 'Twilight comfort meets gothic romance',
            description: "SkyyRose's BLACK Rose Joggers: Twilight comfort meets gothic romance. Embroidered black roses bloom on soft fabric. Pre-order now.",
            price: '$95',
            spec: 'Premium Soft-Touch Fabric • Tapered Fit • Machine Wash',
            badge: 'PRE-ORDER',
            image: 'assets/images/products/br-002/br-002-model.jpg',
            url: '/?product_id=br-002',
            variants: {
              sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'],
              colors: [{ name: 'Black', hex: '#000000' }]
            }
          }
        },
        {
          x: 75,
          y: 55,
          product: {
            id: 'br-003',
            collection: 'BLACK ROSE',
            name: 'BLACK is Beautiful Jersey',
            tagline: 'Dare to bloom in defiant elegance',
            description: "Dare to bloom in the SkyyRose 'BLACK IS BEAUTIFUL' Jersey — where gothic luxury meets a powerful message, stitched in streetwise elegance.",
            price: '$110',
            spec: 'Premium Mesh • Button-Down Jersey • Sizes S–3XL',
            badge: 'PRE-ORDER',
            image: 'assets/images/products/br-003/br-003-model.jpg',
            url: '/?product_id=br-003',
            variants: {
              sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'],
              colors: [
                { name: 'Last Oakland', hex: '#1B4D1B' },
                { name: 'Giants', hex: '#27251F' }
              ]
            }
          }
        },
        {
          x: 40,
          y: 65,
          product: {
            id: 'br-004',
            collection: 'BLACK ROSE',
            name: 'BLACK Rose Hoodie',
            tagline: 'Embroidered gothic luxury',
            description: "SkyyRose's BLACK Rose Hoodie: gothic luxury in twilight shadows. Intricate embroidery captures the bloom of darkness, a defiant statement for the modern romantic.",
            price: '$145',
            spec: 'Premium Cotton Fleece • Kangaroo Pocket • Drawstring Hood',
            badge: 'PRE-ORDER',
            image: 'assets/images/products/br-004/br-004-model.jpg',
            url: '/?product_id=br-004',
            variants: {
              sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'],
              colors: [{ name: 'Black', hex: '#000000' }]
            }
          }
        },
        {
          x: 55,
          y: 75,
          product: {
            id: 'br-006',
            collection: 'BLACK ROSE',
            name: 'BLACK Rose Sherpa Jacket',
            tagline: 'Unveil your dark allure',
            description: 'Unveil your dark allure. The BLACK Rose Sherpa Jacket combines lustrous black satin with plush Sherpa lining, crowned by an exquisite embroidered rose.',
            price: '$295',
            spec: 'Satin Shell • Sherpa Lining • Embroidered Rose',
            badge: 'PRE-ORDER',
            image: 'assets/images/products/br-006/br-006-model.jpg',
            url: '/?product_id=br-006',
            variants: {
              sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'],
              colors: [{ name: 'Black', hex: '#000000' }]
            }
          }
        },
        {
          x: 85,
          y: 45,
          product: {
            id: 'br-008',
            collection: 'BLACK ROSE',
            name: "Women's BLACK Rose Hooded Dress",
            tagline: 'Gothic mystery in every silhouette',
            description: "Unleash your inner darkness with the Women's BLACK Rose Hooded Dress. Intricate black rose embroidery and a silhouette of gothic mystery.",
            price: '$175',
            spec: 'Premium Fabric • Attached Hood • Embroidered Rose',
            badge: 'PRE-ORDER',
            image: 'assets/images/products/br-008/br-008-model.jpg',
            url: '/?product_id=br-008',
            variants: {
              sizes: ['XS', 'S', 'M', 'L', 'XL', '2XL'],
              colors: [{ name: 'Black', hex: '#000000' }]
            }
          }
        }
      ]
    },
    {
      id: 'love-hurts',
      collection: 'LOVE HURTS',
      name: 'The Ballroom',
      accent: '#8B0000',
      description: 'Dramatic passion meets edgy sophistication',
      hotspots: [
        {
          x: 30,
          y: 45,
          product: {
            id: 'lh-001',
            collection: 'LOVE HURTS',
            name: 'The Fannie',
            tagline: 'Oakland grit, luxury soul',
            description: "From the SkyyRose 'LOVE HURTS' collection, The Fannie is a luxury fanny pack embodying Oakland grit, passion, and the defiant bloom of a street rose.",
            price: '$65',
            spec: 'Premium Fabric • Adjustable Strap • Rose Embroidery',
            badge: 'PRE-ORDER',
            image: 'assets/images/products/lh-001/lh-001-model.jpg',
            url: '/?product_id=lh-001',
            variants: {
              sizes: ['One Size'],
              colors: [{ name: 'Black', hex: '#000000' }]
            }
          }
        },
        {
          x: 65,
          y: 40,
          product: {
            id: 'lh-002',
            collection: 'LOVE HURTS',
            name: 'Love Hurts Joggers',
            tagline: 'Oakland grit meets luxury',
            description: 'SkyyRose Love Hurts Joggers: Where Oakland grit meets luxury. Feel the fire with the embroidered rose, a symbol of passion forged in the streets.',
            price: '$95',
            spec: 'Premium Fabric • Tapered Fit • Zippered Ankles',
            badge: 'AVAILABLE',
            image: 'assets/images/products/lh-002/lh-002-model.jpg',
            url: '/?product_id=lh-002',
            variants: {
              sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'],
              colors: [
                { name: 'Black', hex: '#000000' },
                { name: 'White', hex: '#F5F5F5' }
              ]
            }
          }
        },
        {
          x: 50,
          y: 60,
          product: {
            id: 'lh-003',
            collection: 'LOVE HURTS',
            name: 'Love Hurts Basketball Shorts',
            tagline: 'Feel the fire. Own the streets.',
            description: 'SkyyRose Love Hurts: Where street passion meets luxury. Rock these mesh basketball shorts with a defiant rose design, born from Oakland grit.',
            price: '$75',
            spec: 'Breathable Mesh • Elastic Waistband • Rose Design',
            badge: 'AVAILABLE',
            image: 'assets/images/products/lh-003/lh-003-model.jpg',
            url: '/?product_id=lh-003',
            variants: {
              sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'],
              colors: [{ name: 'Black/White', hex: '#1A1A1A' }]
            }
          }
        },
        {
          x: 75,
          y: 50,
          product: {
            id: 'lh-004',
            collection: 'LOVE HURTS',
            name: 'Love Hurts Varsity Jacket',
            tagline: 'Battle armor for the heartbroken',
            description: 'Oakland grit meets broken hearts in the Love Hurts Varsity Jacket. Black satin, fire-red script, secret rose garden. Pre-order your battle armor.',
            price: '$265',
            spec: 'Black Satin Shell • Rose-Lined Hood • Bold Script',
            badge: 'PRE-ORDER',
            image: 'assets/images/products/lh-001/lh-001-model.jpg',
            url: '/?product_id=lh-004',
            variants: {
              sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'],
              colors: [{ name: 'Black/Red', hex: '#1A1A1A' }]
            }
          }
        }
      ]
    },
    {
      id: 'signature-waterfront',
      collection: 'SIGNATURE',
      name: 'Waterfront Runway',
      accent: '#D4AF37',
      description: 'Bay Bridge waterfront — black marble platform, gold-lit display frames',
      hotspots: [
        {
          x: 15, y: 42,
          product: {
            id: 'sg-009', collection: 'SIGNATURE',
            name: 'Red Rose Beanie',
            tagline: 'Signature warmth, rose-embroidered',
            description: 'The Signature Collection Red Rose Beanie — fine knit, embroidered rose emblem, West Coast prestige.',
            price: '$45',
            spec: 'Fine Knit Yarn • Embroidered Rose • One Size',
            badge: 'PRE-ORDER',
            image: 'assets/images/products/sg-009/sg-009-model.jpg',
            url: '/?product_id=sg-009',
            variants: { sizes: ['One Size'], colors: [{ name: 'Red', hex: '#C0392B' }] }
          }
        },
        {
          x: 20, y: 48,
          product: {
            id: 'sg-010', collection: 'SIGNATURE',
            name: 'Lavender Rose Beanie',
            tagline: 'Soft lavender, bold statement',
            description: 'The Signature Collection Lavender Rose Beanie — luxurious knit with embroidered rose in soft lavender.',
            price: '$45',
            spec: 'Fine Knit Yarn • Embroidered Rose • One Size',
            badge: 'PRE-ORDER',
            image: 'assets/images/products/sg-010/sg-010-model.jpg',
            url: '/?product_id=sg-010',
            variants: { sizes: ['One Size'], colors: [{ name: 'Lavender', hex: '#7D3C98' }] }
          }
        },
        {
          x: 28, y: 55,
          product: {
            id: 'sg-006', collection: 'SIGNATURE',
            name: 'Cotton Candy Tee',
            tagline: 'Sweet tones, premium fabric',
            description: 'The Signature Collection Cotton Candy Tee — pastel luxury in premium cotton with the SR monogram.',
            price: '$65',
            spec: 'Premium Cotton • SR Monogram • Relaxed Fit',
            badge: 'PRE-ORDER',
            image: 'assets/images/products/sg-006/sg-006-model.jpg',
            url: '/?product_id=sg-006',
            variants: { sizes: ['XS', 'S', 'M', 'L', 'XL', '2XL'], colors: [{ name: 'Cotton Candy', hex: '#F8B4D9' }] }
          }
        },
        {
          x: 32, y: 62,
          product: {
            id: 'sg-007', collection: 'SIGNATURE',
            name: 'Cotton Candy Shorts',
            tagline: 'Matching comfort, pastel luxury',
            description: 'The Signature Collection Cotton Candy Shorts — pair with the Cotton Candy Tee for a complete pastel set.',
            price: '$55',
            spec: 'Premium Fabric • Elastic Waistband • Matching Set Available',
            badge: 'PRE-ORDER',
            image: 'assets/images/products/sg-007/sg-007-model.jpg',
            url: '/?product_id=sg-007',
            variants: { sizes: ['S', 'M', 'L', 'XL', '2XL'], colors: [{ name: 'Cotton Candy', hex: '#F8B4D9' }] }
          }
        },
        {
          x: 42, y: 35,
          product: {
            id: 'sg-002', collection: 'SIGNATURE',
            name: 'Stay Golden Tee',
            tagline: 'Golden hour, every hour',
            description: 'Stay Golden Tee — elevated everyday style with the golden SkyyRose touch. Premium cotton, timeless design.',
            price: '$65',
            spec: 'Premium Cotton • Gold Print • Relaxed Fit',
            badge: 'PRE-ORDER',
            image: 'assets/images/products/sg-002/sg-002-model.jpg',
            url: '/?product_id=sg-002',
            variants: { sizes: ['XS', 'S', 'M', 'L', 'XL', '2XL'], colors: [{ name: 'White/Gold', hex: '#F5F5F5' }] }
          }
        },
        {
          x: 50, y: 38,
          product: {
            id: 'sg-004', collection: 'SIGNATURE',
            name: 'Signature Hoodie',
            tagline: 'The definitive SkyyRose statement',
            description: 'The Signature Hoodie — premium cotton fleece with embroidered SkyyRose crest. The centerpiece of the collection.',
            price: '$145',
            spec: 'Premium Cotton Fleece • Kangaroo Pocket • Embroidered Crest',
            badge: 'PRE-ORDER',
            image: 'assets/images/products/sg-004/sg-004-model.jpg',
            url: '/?product_id=sg-004',
            variants: { sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'], colors: [{ name: 'Black', hex: '#1A1A1A' }] }
          }
        },
        {
          x: 62, y: 36,
          product: {
            id: 'sg-008', collection: 'SIGNATURE',
            name: 'Crop Hoodie',
            tagline: 'Cropped luxury, full statement',
            description: 'The Signature Crop Hoodie — the same premium cotton fleece in a cropped silhouette for bold Bay Area style.',
            price: '$125',
            spec: 'Premium Cotton Fleece • Cropped Cut • Drawstring Hood',
            badge: 'PRE-ORDER',
            image: 'assets/images/products/sg-008/sg-008-model.jpg',
            url: '/?product_id=sg-008',
            variants: { sizes: ['XS', 'S', 'M', 'L', 'XL'], colors: [{ name: 'Black', hex: '#1A1A1A' }] }
          }
        },
        {
          x: 70, y: 55,
          product: {
            id: 'sg-005', collection: 'SIGNATURE',
            name: 'Signature Shorts',
            tagline: 'Effortless West Coast style',
            description: 'The Signature Shorts — lightweight premium fabric with the SR monogram. Pairs with any Signature tee.',
            price: '$55',
            spec: 'Premium Fabric • Elastic Waistband • SR Monogram',
            badge: 'PRE-ORDER',
            image: 'assets/images/products/sg-005/sg-005-model.jpg',
            url: '/?product_id=sg-005',
            variants: { sizes: ['S', 'M', 'L', 'XL', '2XL'], colors: [{ name: 'Black', hex: '#1A1A1A' }] }
          }
        },
        {
          x: 75, y: 60,
          product: {
            id: 'sg-001', collection: 'SIGNATURE',
            name: 'The Bay Set',
            tagline: 'West Coast prestige, elevated',
            description: 'The Bay Set: embody West Coast luxury with this SIGNATURE collection ensemble. Iconic blue rose and Bay Area skyline.',
            price: '$225',
            spec: 'Premium Fabric • Tee + Shorts Set • Bay Bridge Design',
            badge: 'PRE-ORDER',
            image: 'assets/images/products/sg-001/sg-001-model.jpg',
            url: '/?product_id=sg-001',
            variants: { sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'], colors: [{ name: 'White/Blue', hex: '#F5F5F5' }] }
          }
        },
        {
          x: 38, y: 72,
          product: {
            id: 'sg-011', collection: 'SIGNATURE',
            name: 'Original Label Tee (White)',
            tagline: 'The original SkyyRose label',
            description: 'Original Label Tee in White — the foundational piece featuring the original SkyyRose label design.',
            price: '$55',
            spec: 'Premium Cotton • Original Label Print • Classic Fit',
            badge: 'AVAILABLE',
            image: 'assets/images/products/sg-011/sg-011-model.jpg',
            url: '/?product_id=sg-011',
            variants: { sizes: ['XS', 'S', 'M', 'L', 'XL', '2XL'], colors: [{ name: 'White', hex: '#F5F5F5' }] }
          }
        },
        {
          x: 58, y: 72,
          product: {
            id: 'sg-012', collection: 'SIGNATURE',
            name: 'Original Label Tee (Orchid)',
            tagline: 'The original label in orchid',
            description: 'Original Label Tee in Orchid — the same foundational design in a striking orchid colorway.',
            price: '$55',
            spec: 'Premium Cotton • Original Label Print • Classic Fit',
            badge: 'AVAILABLE',
            image: 'assets/images/products/sg-012/sg-012-model.jpg',
            url: '/?product_id=sg-012',
            variants: { sizes: ['XS', 'S', 'M', 'L', 'XL', '2XL'], colors: [{ name: 'Orchid', hex: '#9B59B6' }] }
          }
        }
      ]
    },
    {
      id: 'signature-showroom',
      collection: 'SIGNATURE',
      name: 'Golden Gate Showroom',
      accent: '#D4AF37',
      description: 'Golden Gate sunset showroom — panoramic windows, marble interior',
      hotspots: [
        {
          x: 15, y: 35,
          product: {
            id: 'sg-004', collection: 'SIGNATURE',
            name: 'Signature Hoodie',
            tagline: 'The definitive SkyyRose statement',
            description: 'The Signature Hoodie — premium cotton fleece with embroidered SkyyRose crest.',
            price: '$145',
            spec: 'Premium Cotton Fleece • Kangaroo Pocket • Embroidered Crest',
            badge: 'PRE-ORDER',
            image: 'assets/images/products/sg-004/sg-004-model.jpg',
            url: '/?product_id=sg-004',
            variants: { sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'], colors: [{ name: 'Black', hex: '#1A1A1A' }] }
          }
        },
        {
          x: 22, y: 40,
          product: {
            id: 'sg-003', collection: 'SIGNATURE',
            name: 'Pink Smoke Crewneck',
            tagline: 'Soft smoke, bold luxury',
            description: 'The Pink Smoke Crewneck — where subtle pink meets premium construction. A Signature Collection essential.',
            price: '$95',
            spec: 'Premium Cotton • Crew Neck • Relaxed Oversized Fit',
            badge: 'PRE-ORDER',
            image: 'assets/images/products/sg-003/sg-003-model.jpg',
            url: '/?product_id=sg-003',
            variants: { sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'], colors: [{ name: 'Pink Smoke', hex: '#E8B4B8' }] }
          }
        },
        {
          x: 50, y: 52,
          product: {
            id: 'sg-001', collection: 'SIGNATURE',
            name: 'The Bay Set',
            tagline: 'West Coast prestige, elevated',
            description: 'The Bay Set: embody West Coast luxury with this SIGNATURE collection ensemble. Center stage, featured.',
            price: '$225',
            spec: 'Premium Fabric • Tee + Shorts Set • Bay Bridge Design',
            badge: 'PRE-ORDER',
            image: 'assets/images/products/sg-001/sg-001-model.jpg',
            url: '/?product_id=sg-001',
            variants: { sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'], colors: [{ name: 'White/Blue', hex: '#F5F5F5' }] }
          }
        },
        {
          x: 32, y: 48,
          product: {
            id: 'sg-009', collection: 'SIGNATURE',
            name: 'Red Rose Beanie',
            tagline: 'Signature warmth, rose-embroidered',
            description: 'The Signature Collection Red Rose Beanie on the left marble pedestal.',
            price: '$45',
            spec: 'Fine Knit Yarn • Embroidered Rose • One Size',
            badge: 'PRE-ORDER',
            image: 'assets/images/products/sg-009/sg-009-model.jpg',
            url: '/?product_id=sg-009',
            variants: { sizes: ['One Size'], colors: [{ name: 'Red', hex: '#C0392B' }] }
          }
        },
        {
          x: 68, y: 48,
          product: {
            id: 'sg-010', collection: 'SIGNATURE',
            name: 'Lavender Rose Beanie',
            tagline: 'Soft lavender, bold statement',
            description: 'The Signature Collection Lavender Rose Beanie on the right marble pedestal.',
            price: '$45',
            spec: 'Fine Knit Yarn • Embroidered Rose • One Size',
            badge: 'PRE-ORDER',
            image: 'assets/images/products/sg-010/sg-010-model.jpg',
            url: '/?product_id=sg-010',
            variants: { sizes: ['One Size'], colors: [{ name: 'Lavender', hex: '#7D3C98' }] }
          }
        },
        {
          x: 78, y: 35,
          product: {
            id: 'sg-008', collection: 'SIGNATURE',
            name: 'Crop Hoodie',
            tagline: 'Cropped luxury, full statement',
            description: 'The Signature Crop Hoodie hanging on the right wall clothing rack.',
            price: '$125',
            spec: 'Premium Cotton Fleece • Cropped Cut • Drawstring Hood',
            badge: 'PRE-ORDER',
            image: 'assets/images/products/sg-008/sg-008-model.jpg',
            url: '/?product_id=sg-008',
            variants: { sizes: ['XS', 'S', 'M', 'L', 'XL'], colors: [{ name: 'Black', hex: '#1A1A1A' }] }
          }
        },
        {
          x: 85, y: 40,
          product: {
            id: 'sg-002', collection: 'SIGNATURE',
            name: 'Stay Golden Tee',
            tagline: 'Golden hour, every hour',
            description: 'Stay Golden Tee hanging on the right wall clothing rack in the showroom.',
            price: '$65',
            spec: 'Premium Cotton • Gold Print • Relaxed Fit',
            badge: 'PRE-ORDER',
            image: 'assets/images/products/sg-002/sg-002-model.jpg',
            url: '/?product_id=sg-002',
            variants: { sizes: ['XS', 'S', 'M', 'L', 'XL', '2XL'], colors: [{ name: 'White/Gold', hex: '#F5F5F5' }] }
          }
        },
        {
          x: 18, y: 58,
          product: {
            id: 'sg-005', collection: 'SIGNATURE',
            name: 'Signature Shorts',
            tagline: 'Effortless West Coast style',
            description: 'The Signature Shorts folded on the left wall shelf.',
            price: '$55',
            spec: 'Premium Fabric • Elastic Waistband • SR Monogram',
            badge: 'PRE-ORDER',
            image: 'assets/images/products/sg-005/sg-005-model.jpg',
            url: '/?product_id=sg-005',
            variants: { sizes: ['S', 'M', 'L', 'XL', '2XL'], colors: [{ name: 'Black', hex: '#1A1A1A' }] }
          }
        },
        {
          x: 25, y: 62,
          product: {
            id: 'sg-006', collection: 'SIGNATURE',
            name: 'Cotton Candy Tee',
            tagline: 'Sweet tones, premium fabric',
            description: 'Cotton Candy Tee folded on the left wall shelf in the showroom.',
            price: '$65',
            spec: 'Premium Cotton • SR Monogram • Relaxed Fit',
            badge: 'PRE-ORDER',
            image: 'assets/images/products/sg-006/sg-006-model.jpg',
            url: '/?product_id=sg-006',
            variants: { sizes: ['XS', 'S', 'M', 'L', 'XL', '2XL'], colors: [{ name: 'Cotton Candy', hex: '#F8B4D9' }] }
          }
        },
        {
          x: 75, y: 58,
          product: {
            id: 'sg-007', collection: 'SIGNATURE',
            name: 'Cotton Candy Shorts',
            tagline: 'Matching comfort, pastel luxury',
            description: 'Cotton Candy Shorts on the right wall display in the showroom.',
            price: '$55',
            spec: 'Premium Fabric • Elastic Waistband • Matching Set',
            badge: 'PRE-ORDER',
            image: 'assets/images/products/sg-007/sg-007-model.jpg',
            url: '/?product_id=sg-007',
            variants: { sizes: ['S', 'M', 'L', 'XL', '2XL'], colors: [{ name: 'Cotton Candy', hex: '#F8B4D9' }] }
          }
        },
        {
          x: 82, y: 58,
          product: {
            id: 'sg-011', collection: 'SIGNATURE',
            name: 'Original Label Tee (White)',
            tagline: 'The original SkyyRose label',
            description: 'Original Label Tee in White on the right wall display.',
            price: '$55',
            spec: 'Premium Cotton • Original Label Print • Classic Fit',
            badge: 'AVAILABLE',
            image: 'assets/images/products/sg-011/sg-011-model.jpg',
            url: '/?product_id=sg-011',
            variants: { sizes: ['XS', 'S', 'M', 'L', 'XL', '2XL'], colors: [{ name: 'White', hex: '#F5F5F5' }] }
          }
        },
        {
          x: 88, y: 62,
          product: {
            id: 'sg-012', collection: 'SIGNATURE',
            name: 'Original Label Tee (Orchid)',
            tagline: 'The original label in orchid',
            description: 'Original Label Tee in Orchid on the right wall display.',
            price: '$55',
            spec: 'Premium Cotton • Original Label Print • Classic Fit',
            badge: 'AVAILABLE',
            image: 'assets/images/products/sg-012/sg-012-model.jpg',
            url: '/?product_id=sg-012',
            variants: { sizes: ['XS', 'S', 'M', 'L', 'XL', '2XL'], colors: [{ name: 'Orchid', hex: '#9B59B6' }] }
          }
        }
      ]
    }
  ]
};

// Export for use in app.js
if (typeof module !== 'undefined' && module.exports) {
  module.exports = CONFIG;
}
