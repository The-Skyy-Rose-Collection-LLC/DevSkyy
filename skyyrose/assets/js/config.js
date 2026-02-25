// SkyyRose Experience - Configuration
// Owner-confirmed prices as of 2026-02-24
// DRAFT = no price yet (save as draft in WooCommerce, not published)
// TBD = price to be determined (save as draft)

const CONFIG = {
  // Scene images — 2 scenes per collection (6 total)
  images: {
    'black-rose-moonlit-courtyard': {
      png: '../assets/scenes/black-rose/black-rose-moonlit-courtyard.png',
      jpeg: '../assets/scenes/black-rose/black-rose-moonlit-courtyard.png',
      mobile: {
        png: '../assets/scenes/black-rose/black-rose-moonlit-courtyard.png',
        jpeg: '../assets/scenes/black-rose/black-rose-moonlit-courtyard.png'
      }
    },
    'black-rose-iron-gazebo-garden': {
      png: '../assets/scenes/black-rose/black-rose-iron-gazebo-garden.png',
      jpeg: '../assets/scenes/black-rose/black-rose-iron-gazebo-garden.png',
      mobile: {
        png: '../assets/scenes/black-rose/black-rose-iron-gazebo-garden.png',
        jpeg: '../assets/scenes/black-rose/black-rose-iron-gazebo-garden.png'
      }
    },
    'love-hurts-cathedral-rose-chamber': {
      png: '../assets/scenes/love-hurts/love-hurts-cathedral-rose-chamber.png',
      jpeg: '../assets/scenes/love-hurts/love-hurts-cathedral-rose-chamber.png',
      mobile: {
        png: '../assets/scenes/love-hurts/love-hurts-cathedral-rose-chamber.png',
        jpeg: '../assets/scenes/love-hurts/love-hurts-cathedral-rose-chamber.png'
      }
    },
    'love-hurts-gothic-ballroom': {
      png: '../assets/scenes/love-hurts/love-hurts-gothic-ballroom.png',
      jpeg: '../assets/scenes/love-hurts/love-hurts-gothic-ballroom.png',
      mobile: {
        png: '../assets/scenes/love-hurts/love-hurts-gothic-ballroom.png',
        jpeg: '../assets/scenes/love-hurts/love-hurts-gothic-ballroom.png'
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

  // Background images (extra scenes not used as immersive rooms)
  backgrounds: {
    'black-rose': [
      '../assets/scenes/black-rose/black-rose-marble-rotunda.png',
      '../assets/scenes/black-rose/black-rose-white-rose-grotto.png'
    ],
    'love-hurts': [
      '../assets/scenes/love-hurts/love-hurts-crimson-throne-room.png',
      '../assets/scenes/love-hurts/love-hurts-enchanted-rose-shrine.png',
      '../assets/scenes/love-hurts/love-hurts-giant-rose-staircase.png',
      '../assets/scenes/love-hurts/love-hurts-reflective-ballroom.png'
    ]
  },

  // Room definitions — 2 rooms per collection (6 total)
  rooms: [
    // ===================== BLACK ROSE — Room 1: Moonlit Courtyard =====================
    {
      id: 'black-rose-moonlit-courtyard',
      collection: 'BLACK ROSE',
      name: 'Moonlit Courtyard',
      accent: '#B76E79',
      description: 'Moonlit garden courtyard with marble statues, black rose topiaries, and ornate fountains',
      hotspots: [
        {
          x: 15, y: 42,
          product: {
            id: 'br-006',
            collection: 'BLACK ROSE',
            name: 'BLACK Rose Sherpa Jacket',
            tagline: 'Unveil your dark allure',
            description: 'Unveil your dark allure. The BLACK Rose Sherpa Jacket combines lustrous black satin with plush Sherpa lining, crowned by an exquisite embroidered rose.',
            price: '$95',
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
          x: 38, y: 50,
          product: {
            id: 'br-005',
            collection: 'BLACK ROSE',
            name: 'BLACK Rose Hoodie — Signature Edition',
            tagline: 'Embrace twilight with signature embroidery',
            description: 'Embrace twilight with the BLACK Rose Hoodie — Signature Edition. Exquisite rose embroidery on deep charcoal creates a gothic romance masterpiece.',
            price: '$65',
            spec: 'Premium Cotton Fleece • Sleeve Rose Cascade • Hood Floral Print',
            badge: 'PRE-ORDER',
            image: 'assets/images/products/br-005/br-005-model.jpg',
            url: '/?product_id=br-005',
            variants: {
              sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'],
              colors: [{ name: 'Charcoal', hex: '#333333' }]
            }
          }
        },
        {
          x: 62, y: 55,
          product: {
            id: 'br-002',
            collection: 'BLACK ROSE',
            name: 'BLACK Rose Joggers',
            tagline: 'Twilight comfort meets gothic romance',
            description: "SkyyRose's BLACK Rose Joggers: Twilight comfort meets gothic romance. Embroidered black roses bloom on soft fabric. Pre-order now.",
            price: '$50',
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
          x: 82, y: 48,
          product: {
            id: 'br-007',
            collection: 'BLACK ROSE',
            name: 'BLACK Rose × Love Hurts Basketball Shorts',
            tagline: 'Where twilight meets the streets',
            description: 'SkyyRose BLACK Rose: Where twilight meets the streets. Embroidered roses bloom on black mesh, a gothic love letter to Oakland\'s soul.',
            price: '$65',
            spec: 'Premium Mesh • Embroidered Rose & Clouds • Oakland Bold Print',
            badge: 'PRE-ORDER',
            image: 'assets/images/products/br-007/br-007-model.jpg',
            url: '/?product_id=br-007',
            variants: {
              sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'],
              colors: [{ name: 'Black/White', hex: '#000000' }]
            }
          }
        }
      ]
    },
    // ===================== BLACK ROSE — Room 2: Iron Gazebo Garden =====================
    {
      id: 'black-rose-iron-gazebo-garden',
      collection: 'BLACK ROSE',
      name: 'Iron Gazebo Garden',
      accent: '#B76E79',
      description: 'Aerial view of ornate iron gazebo surrounded by rose hedge maze and cobblestone paths under moonlight',
      hotspots: [
        {
          x: 30, y: 40,
          product: {
            id: 'br-004',
            collection: 'BLACK ROSE',
            name: 'BLACK Rose Hoodie',
            tagline: 'Embroidered gothic luxury',
            description: "SkyyRose's BLACK Rose Hoodie: gothic luxury in twilight shadows. Intricate embroidery captures the bloom of darkness, a defiant statement for the modern romantic.",
            price: '$40',
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
          x: 55, y: 35,
          product: {
            id: 'br-001',
            collection: 'BLACK ROSE',
            name: 'BLACK Rose Crewneck',
            tagline: 'Gothic elegance meets street style',
            description: 'SkyyRose BLACK Rose Crewneck: gothic luxury blooms in twilight. Embroidered with defiant elegance, a dark romance woven in every thread.',
            price: null,
            priceLabel: 'DRAFT',
            spec: 'Premium Cotton • Relaxed Oversized Fit • Machine Wash Cold',
            badge: 'COMING SOON',
            image: 'assets/images/products/br-001/br-001-model.jpg',
            url: '/?product_id=br-001',
            variants: {
              sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'],
              colors: [{ name: 'Black', hex: '#000000' }]
            }
          }
        },
        {
          x: 72, y: 50,
          product: {
            id: 'br-008',
            collection: 'BLACK ROSE',
            name: "Women's BLACK Rose Hooded Dress",
            tagline: 'Gothic mystery in every silhouette',
            description: "Unleash your inner darkness with the Women's BLACK Rose Hooded Dress. Intricate black rose embroidery and a silhouette of gothic mystery.",
            price: null,
            priceLabel: 'TBD',
            spec: 'Premium Fabric • Attached Hood • Embroidered Rose',
            badge: 'COMING SOON',
            image: 'assets/images/products/br-008/br-008-model.jpg',
            url: '/?product_id=br-008',
            variants: {
              sizes: ['XS', 'S', 'M', 'L', 'XL', '2XL'],
              colors: [{ name: 'Black', hex: '#000000' }]
            }
          }
        },
        {
          x: 48, y: 60,
          product: {
            id: 'br-003',
            collection: 'BLACK ROSE',
            name: 'BLACK is Beautiful Jersey',
            tagline: 'Dare to bloom in defiant elegance',
            description: "Dare to bloom in the SkyyRose 'BLACK IS BEAUTIFUL' Jersey — where gothic luxury meets a powerful message, stitched in streetwise elegance.",
            price: null,
            priceLabel: 'DRAFT',
            spec: 'Premium Mesh • Button-Down Jersey • Sizes S–3XL',
            badge: 'COMING SOON',
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
        }
      ]
    },
    // ===================== LOVE HURTS — Room 1: Cathedral Rose Chamber =====================
    {
      id: 'love-hurts-cathedral-rose-chamber',
      collection: 'LOVE HURTS',
      name: 'Cathedral Rose Chamber',
      accent: '#8B0000',
      description: 'Gothic cathedral with enchanted rose under glass dome, stained glass windows, and crimson petals',
      hotspots: [
        {
          x: 35, y: 42,
          product: {
            id: 'lh-004',
            collection: 'LOVE HURTS',
            name: 'Love Hurts Varsity Jacket',
            tagline: 'Battle armor for the heartbroken',
            description: 'Oakland grit meets broken hearts in the Love Hurts Varsity Jacket. Black satin, fire-red script, secret rose garden. Pre-order your battle armor.',
            price: null,
            priceLabel: 'DRAFT',
            spec: 'Black Satin Shell • Rose-Lined Hood • Bold Script',
            badge: 'COMING SOON',
            image: 'assets/images/products/lh-004/lh-004-model.jpg',
            url: '/?product_id=lh-004',
            variants: {
              sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'],
              colors: [{ name: 'Black/Red', hex: '#1A1A1A' }]
            }
          }
        },
        {
          x: 68, y: 38,
          product: {
            id: 'lh-001',
            collection: 'LOVE HURTS',
            name: 'The Fannie',
            tagline: 'Oakland grit, luxury soul',
            description: "From the SkyyRose 'LOVE HURTS' collection, The Fannie is a luxury fanny pack embodying Oakland grit, passion, and the defiant bloom of a street rose.",
            price: '$70',
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
          x: 52, y: 60,
          product: {
            id: 'lh-003',
            collection: 'LOVE HURTS',
            name: 'Love Hurts Basketball Shorts',
            tagline: 'Feel the fire. Own the streets.',
            description: 'SkyyRose Love Hurts: Where street passion meets luxury. Rock these mesh basketball shorts with a defiant rose design, born from Oakland grit.',
            price: '$55',
            spec: 'Breathable Mesh • Elastic Waistband • Rose Design',
            badge: 'AVAILABLE',
            image: 'assets/images/products/lh-003/lh-003-model.jpg',
            url: '/?product_id=lh-003',
            variants: {
              sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'],
              colors: [{ name: 'Black/White', hex: '#1A1A1A' }]
            }
          }
        }
      ]
    },
    // ===================== LOVE HURTS — Room 2: Gothic Ballroom =====================
    {
      id: 'love-hurts-gothic-ballroom',
      collection: 'LOVE HURTS',
      name: 'Gothic Ballroom',
      accent: '#8B0000',
      description: 'Gothic chamber with rose under glass dome, purple draped fabrics, pink petals, and candlelit atmosphere',
      hotspots: [
        {
          x: 40, y: 45,
          product: {
            id: 'lh-002',
            collection: 'LOVE HURTS',
            name: 'Love Hurts Joggers (BLACK)',
            tagline: 'Oakland grit meets luxury',
            description: 'SkyyRose Love Hurts Joggers: Where Oakland grit meets luxury. Feel the fire with the embroidered rose, a symbol of passion forged in the streets.',
            price: '$67',
            spec: 'Premium Fabric • Tapered Fit • Zippered Ankles',
            badge: 'AVAILABLE',
            image: 'assets/images/products/lh-002/lh-002-model.jpg',
            url: '/?product_id=lh-002',
            variants: {
              sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'],
              colors: [{ name: 'Black', hex: '#000000' }]
            }
          }
        },
        {
          x: 65, y: 48,
          product: {
            id: 'lh-002b',
            collection: 'LOVE HURTS',
            name: 'Love Hurts Joggers (WHITE)',
            tagline: 'Oakland grit in a fresh colorway',
            description: 'SkyyRose Love Hurts Joggers in White: The same Oakland fire, reborn in fresh white. Embroidered rose, zippered ankles, premium construction.',
            price: '$67',
            spec: 'Premium Fabric • Tapered Fit • Zippered Ankles',
            badge: 'AVAILABLE',
            image: 'assets/images/products/lh-002b/lh-002b-model.jpg',
            url: '/?product_id=lh-002b',
            variants: {
              sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'],
              colors: [{ name: 'White', hex: '#F5F5F5' }]
            }
          }
        }
      ]
    },
    // ===================== SIGNATURE — Room 1: Waterfront Runway =====================
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
            id: 'sg-009',
            collection: 'SIGNATURE',
            name: 'The Sherpa Jacket',
            tagline: 'Signature warmth, rose-embroidered',
            description: 'Command attention in the SkyyRose Signature Sherpa Jacket, an opulent statement of West Coast luxury, defined by our signature rose embroidery.',
            price: '$80',
            spec: 'Premium Black Exterior • Sherpa Interior • Rose Embroidery',
            badge: 'PRE-ORDER',
            image: 'assets/images/products/sg-009/sg-009-model.jpg',
            url: '/?product_id=sg-009',
            variants: { sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'], colors: [{ name: 'Black', hex: '#1A1A1A' }] }
          }
        },
        {
          x: 32, y: 50,
          product: {
            id: 'sg-007',
            collection: 'SIGNATURE',
            name: 'The Signature Beanie',
            tagline: 'Signature warmth, rose-embroidered',
            description: 'Elevate your everyday with the SkyyRose Signature Beanie: a luxurious knit, bespoke comfort, and a bold statement of West Coast prestige.',
            price: '$25',
            spec: 'Fine Knit Yarn • Embroidered Rose • One Size',
            badge: 'AVAILABLE',
            image: 'assets/images/products/sg-007/sg-007-model.jpg',
            url: '/?product_id=sg-007',
            variants: { sizes: ['One Size'], colors: [{ name: 'Red', hex: '#C0392B' }, { name: 'Purple', hex: '#7D3C98' }, { name: 'Black', hex: '#1A1A1A' }] }
          }
        },
        {
          x: 42, y: 35,
          product: {
            id: 'sg-002-tee',
            collection: 'SIGNATURE',
            name: 'Stay Golden Set — Tee',
            tagline: 'Golden hour, every hour',
            description: 'Stay Golden Tee — elevated everyday style with the golden SkyyRose touch. Premium cotton, timeless design.',
            price: '$40',
            spec: 'Premium Cotton • Gold Print • Relaxed Fit',
            badge: 'PRE-ORDER',
            image: 'assets/images/products/sg-002/sg-002-tee-model.jpg',
            url: '/?product_id=sg-002-tee',
            variants: { sizes: ['XS', 'S', 'M', 'L', 'XL', '2XL'], colors: [{ name: 'White/Gold', hex: '#F5F5F5' }] }
          }
        },
        {
          x: 50, y: 38,
          product: {
            id: 'sg-002-shorts',
            collection: 'SIGNATURE',
            name: 'Stay Golden Set — Shorts',
            tagline: 'Golden hour comfort',
            description: 'Stay Golden Shorts — matching comfort in luxuriously textured mesh, vibrant abstract cityscape and Bay Area landmarks.',
            price: '$50',
            spec: 'Premium Mesh • Elastic Waistband • Bay Cityscape Print',
            badge: 'PRE-ORDER',
            image: 'assets/images/products/sg-002/sg-002-shorts-model.jpg',
            url: '/?product_id=sg-002-shorts',
            variants: { sizes: ['S', 'M', 'L', 'XL', '2XL'], colors: [{ name: 'White/Gold', hex: '#F5F5F5' }] }
          }
        },
        {
          x: 62, y: 36,
          product: {
            id: 'sg-006',
            collection: 'SIGNATURE',
            name: 'Mint & Lavender Hoodie',
            tagline: 'Refreshing mint, lavender artistry',
            description: 'Experience elevated comfort with the Mint & Lavender Hoodie from the SkyyRose SIGNATURE Collection, where a refreshing mint base meets opulent lavender artistry.',
            price: '$45',
            spec: 'Premium Soft-Touch Fabric • Kangaroo Pocket • Lavender Floral Graphic',
            badge: 'PRE-ORDER',
            image: 'assets/images/products/sg-006/sg-006-model.jpg',
            url: '/?product_id=sg-006',
            variants: { sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'], colors: [{ name: 'Mint', hex: '#98D8C8' }] }
          }
        },
        {
          x: 78, y: 55,
          product: {
            id: 'sg-001-tee',
            collection: 'SIGNATURE',
            name: 'The Bay Set — Tee',
            tagline: 'West Coast prestige, elevated',
            description: 'The Bay Set Tee: embody West Coast luxury. Iconic blue rose and Bay Area skyline on crisp white premium cotton.',
            price: '$40',
            spec: 'Premium Cotton • Blue Rose & Bay Skyline Print • Relaxed Fit',
            badge: 'PRE-ORDER',
            image: 'assets/images/products/sg-001/sg-001-tee-model.jpg',
            url: '/?product_id=sg-001-tee',
            variants: { sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'], colors: [{ name: 'White/Blue', hex: '#F5F5F5' }] }
          }
        },
        {
          x: 85, y: 60,
          product: {
            id: 'sg-001-shorts',
            collection: 'SIGNATURE',
            name: 'The Bay Set — Shorts',
            tagline: 'Bay Bridge artistry on premium mesh',
            description: 'The Bay Set Shorts: breathtaking Bay skyline panorama on premium mesh with signature blue rose. West Coast prestige, elevated.',
            price: '$50',
            spec: 'Premium Mesh • Bay Bridge Panorama • Drawstring Waist',
            badge: 'PRE-ORDER',
            image: 'assets/images/products/sg-001/sg-001-shorts-model.jpg',
            url: '/?product_id=sg-001-shorts',
            variants: { sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'], colors: [{ name: 'White/Blue', hex: '#F5F5F5' }] }
          }
        }
      ]
    },
    // ===================== SIGNATURE — Room 2: Golden Gate Showroom =====================
    {
      id: 'signature-showroom',
      collection: 'SIGNATURE',
      name: 'Golden Gate Showroom',
      accent: '#D4AF37',
      description: 'Golden Gate sunset showroom — panoramic windows, marble interior',
      hotspots: [
        {
          x: 18, y: 38,
          product: {
            id: 'sg-003',
            collection: 'SIGNATURE',
            name: 'The Signature Tee (Orchid)',
            tagline: 'Elevated everyday luxury',
            description: 'The Signature Tee in Orchid: embody elevated style with this premium staple, showcasing SkyyRose\'s commitment to couture-level everyday luxury.',
            price: '$15',
            spec: 'Premium Cotton • Gold SkyyRose Label • Classic Fit',
            badge: 'AVAILABLE',
            image: 'assets/images/products/sg-003/sg-003-model.jpg',
            url: '/?product_id=sg-003',
            variants: { sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'], colors: [{ name: 'Orchid', hex: '#9B59B6' }] }
          }
        },
        {
          x: 35, y: 45,
          product: {
            id: 'sg-005',
            collection: 'SIGNATURE',
            name: 'Stay Golden Tee',
            tagline: 'Golden hour, every hour',
            description: 'Signature Collection: The Stay Golden Tee embodies West Coast ambition, featuring an opulent rose design symbolizing resilience and the pursuit of excellence.',
            price: '$40',
            spec: 'Premium Cotton • Rose Design • Relaxed Fit',
            badge: 'AVAILABLE',
            image: 'assets/images/products/sg-005/sg-005-model.jpg',
            url: '/?product_id=sg-005',
            variants: { sizes: ['XS', 'S', 'M', 'L', 'XL', '2XL'], colors: [{ name: 'White/Gold', hex: '#F5F5F5' }] }
          }
        },
        {
          x: 50, y: 52,
          product: {
            id: 'sg-010',
            collection: 'SIGNATURE',
            name: 'The Bridge Series Shorts',
            tagline: 'Bay Area pride, premium mesh',
            description: 'Capture the essence of West Coast prestige with The Bridge Series Shorts, embodying Bay Area\'s iconic spirit in premium streetwear.',
            price: '$25',
            spec: 'Premium Mesh • Drawstring Waist • Bay Bridge / Golden Gate Colorways',
            badge: 'PRE-ORDER',
            image: 'assets/images/products/sg-010/sg-010-model.jpg',
            url: '/?product_id=sg-010',
            variants: { sizes: ['S', 'M', 'L', 'XL', '2XL'], colors: [{ name: 'Bay Bridge', hex: '#3498DB' }, { name: 'Golden Gate', hex: '#C0392B' }] }
          }
        },
        {
          x: 68, y: 42,
          product: {
            id: 'sg-011',
            collection: 'SIGNATURE',
            name: 'Original Label Tee (White)',
            tagline: 'The original SkyyRose label',
            description: 'Original Label Tee in White — the foundational piece featuring the original SkyyRose label design.',
            price: null,
            priceLabel: 'DRAFT',
            spec: 'Premium Cotton • Original Label Print • Classic Fit',
            badge: 'COMING SOON',
            image: 'assets/images/products/sg-011/sg-011-model.jpg',
            url: '/?product_id=sg-011',
            variants: { sizes: ['XS', 'S', 'M', 'L', 'XL', '2XL'], colors: [{ name: 'White', hex: '#F5F5F5' }] }
          }
        },
        {
          x: 82, y: 48,
          product: {
            id: 'sg-012',
            collection: 'SIGNATURE',
            name: 'Original Label Tee (Orchid)',
            tagline: 'The original label in orchid',
            description: 'Original Label Tee in Orchid — the same foundational design in a striking orchid colorway.',
            price: null,
            priceLabel: 'DRAFT',
            spec: 'Premium Cotton • Original Label Print • Classic Fit',
            badge: 'COMING SOON',
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
