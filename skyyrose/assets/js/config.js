// SkyyRose Experience - Configuration
// This will be replaced with WordPress REST API calls in Phase 3

const CONFIG = {
  // Scene images (placeholder paths - will be optimized in build step)
  images: {
    'black-rose': {
      webp: 'assets/images/scenes/black-rose.webp',
      jpeg: 'assets/images/scenes/black-rose.jpg',
      mobile: {
        webp: 'assets/images/scenes/black-rose-mobile.webp',
        jpeg: 'assets/images/scenes/black-rose-mobile.jpg'
      }
    },
    'love-hurts': {
      webp: 'assets/images/scenes/love-hurts.webp',
      jpeg: 'assets/images/scenes/love-hurts.jpg',
      mobile: {
        webp: 'assets/images/scenes/love-hurts-mobile.webp',
        jpeg: 'assets/images/scenes/love-hurts-mobile.jpg'
      }
    },
    'signature': {
      webp: 'assets/images/scenes/signature.webp',
      jpeg: 'assets/images/scenes/signature.jpg',
      mobile: {
        webp: 'assets/images/scenes/signature-mobile.webp',
        jpeg: 'assets/images/scenes/signature-mobile.jpg'
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
      id: 'signature',
      collection: 'SIGNATURE',
      name: 'The Runway',
      accent: '#D4AF37',
      description: 'High fashion meets editorial excellence',
      hotspots: [
        {
          x: 35,
          y: 40,
          product: {
            id: 'sg-001',
            collection: 'SIGNATURE',
            name: 'The Bay Set',
            tagline: 'West Coast prestige, elevated',
            description: 'The Bay Set: embody West Coast luxury with this SIGNATURE collection ensemble. Featuring the iconic blue rose and a vibrant Bay Area skyline.',
            price: '$225',
            spec: 'Premium Fabric • Tee + Shorts Set • Bay Bridge Design',
            badge: 'PRE-ORDER',
            image: 'assets/images/products/sg-001/sg-001-model.jpg',
            url: '/?product_id=sg-001',
            variants: {
              sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'],
              colors: [{ name: 'White/Blue', hex: '#F5F5F5' }]
            }
          }
        },
        {
          x: 60,
          y: 35,
          product: {
            id: 'sg-006',
            collection: 'SIGNATURE',
            name: 'Mint & Lavender Hoodie',
            tagline: 'Bay Area luxury, effortless comfort',
            description: 'Experience elevated comfort with the Mint & Lavender Hoodie — where a refreshing mint base meets opulent lavender artistry.',
            price: '$145',
            spec: 'Premium Soft-Touch • Kangaroo Pocket • Ribbed Cuffs',
            badge: 'AVAILABLE',
            image: 'assets/images/products/sg-006/sg-006-model.jpg',
            url: '/?product_id=sg-006',
            variants: {
              sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'],
              colors: [{ name: 'Mint/Lavender', hex: '#B8E0D2' }]
            }
          }
        },
        {
          x: 75,
          y: 55,
          product: {
            id: 'sg-003',
            collection: 'SIGNATURE',
            name: 'The Signature Tee — Orchid',
            tagline: 'Elevated everyday luxury',
            description: 'The Signature Tee in Orchid: embody elevated style with this premium staple, showcasing SkyyRose\'s commitment to couture-level everyday luxury.',
            price: '$65',
            spec: 'Premium Cotton • SR Monogram Label • Orchid Colorway',
            badge: 'AVAILABLE',
            image: 'assets/images/products/sg-003/sg-003-model.jpg',
            url: '/?product_id=sg-003',
            variants: {
              sizes: ['XS', 'S', 'M', 'L', 'XL', '2XL'],
              colors: [{ name: 'Orchid', hex: '#9B59B6' }]
            }
          }
        },
        {
          x: 45,
          y: 65,
          product: {
            id: 'sg-007',
            collection: 'SIGNATURE',
            name: 'The Signature Beanie',
            tagline: 'Elevated style, West Coast prestige',
            description: 'Elevate your everyday with the SkyyRose Signature Beanie: a luxurious knit, bespoke comfort, and a bold statement of West Coast prestige.',
            price: '$45',
            spec: 'Fine Knit Yarn • Embroidered Rose Emblem • Available in 3 Colors',
            badge: 'AVAILABLE',
            image: 'assets/images/products/sg-007/sg-007-model.jpg',
            url: '/?product_id=sg-007',
            variants: {
              sizes: ['One Size'],
              colors: [
                { name: 'Red',    hex: '#C0392B' },
                { name: 'Purple', hex: '#7D3C98' },
                { name: 'Black',  hex: '#1A1A1A' }
              ]
            }
          }
        },
        {
          x: 85,
          y: 45,
          product: {
            id: 'sg-009',
            collection: 'SIGNATURE',
            name: 'The Sherpa Jacket',
            tagline: 'Command attention, wear your legacy',
            description: 'Command attention in the SkyyRose Signature Sherpa Jacket — opulent West Coast outerwear featuring signature rose embroidery. Pre-order your legacy.',
            price: '$295',
            spec: 'Premium Shell • Sherpa Interior • Signature Rose Embroidery',
            badge: 'PRE-ORDER',
            image: 'assets/images/products/sg-009/sg-009-model.jpg',
            url: '/?product_id=sg-009',
            variants: {
              sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'],
              colors: [{ name: 'Black', hex: '#000000' }]
            }
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
