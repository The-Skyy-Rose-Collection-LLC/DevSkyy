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
            name: 'Black Rose Tee',
            tagline: 'Gothic elegance meets street style',
            description: 'Premium cotton tee featuring our signature black rose graphic. Oversized fit with dropped shoulders for effortless luxury.',
            price: '$85',
            spec: '100% Premium Cotton • Oversized Fit • Machine Wash Cold',
            badge: 'BESTSELLER',
            image: 'assets/images/products/black-rose-tee.jpg',
            url: '/?product_id=br-001',
            variants: {
              sizes: ['XS', 'S', 'M', 'L', 'XL'],
              colors: [
                { name: 'Black', hex: '#000000' },
                { name: 'Charcoal', hex: '#1C1C1C' }
              ]
            }
          }
        },
        {
          x: 60,
          y: 35,
          product: {
            id: 'br-002',
            collection: 'BLACK ROSE',
            name: 'Rose Garden Dress',
            tagline: 'Where darkness blooms',
            description: 'Flowing midi dress with hand-embroidered rose details. Luxurious silk blend drapes beautifully for an ethereal silhouette.',
            price: '$245',
            spec: 'Silk Blend • Hand-Embroidered • Dry Clean Only',
            badge: 'NEW',
            image: 'assets/images/products/rose-garden-dress.jpg',
            url: '/?product_id=br-002',
            variants: {
              sizes: ['XS', 'S', 'M', 'L'],
              colors: [
                { name: 'Black', hex: '#000000' }
              ]
            }
          }
        },
        {
          x: 75,
          y: 55,
          product: {
            id: 'br-003',
            collection: 'BLACK ROSE',
            name: 'Thorn Leather Jacket',
            tagline: 'Edge meets elegance',
            description: 'Premium leather jacket with rose-thorn hardware details. Classic moto style reimagined with luxury craftsmanship.',
            price: '$595',
            spec: 'Italian Leather • Rose Gold Hardware • Professional Clean',
            badge: 'LIMITED',
            image: 'assets/images/products/thorn-jacket.jpg',
            url: '/?product_id=br-003',
            variants: {
              sizes: ['XS', 'S', 'M', 'L'],
              colors: [
                { name: 'Black', hex: '#000000' }
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
            name: 'Midnight Bloom Pants',
            tagline: 'Comfort in darkness',
            description: 'High-waisted wide-leg pants with subtle rose embroidery. Beige drawstring adds casual luxury to this statement piece.',
            price: '$165',
            spec: 'Cotton Blend • Embroidered Details • Machine Wash',
            badge: null,
            image: 'assets/images/products/midnight-pants.jpg',
            url: '/?product_id=br-004',
            variants: {
              sizes: ['XS', 'S', 'M', 'L', 'XL'],
              colors: [
                { name: 'Black', hex: '#000000' },
                { name: 'Charcoal', hex: '#1C1C1C' }
              ]
            }
          }
        },
        {
          x: 55,
          y: 75,
          product: {
            id: 'br-005',
            collection: 'BLACK ROSE',
            name: 'Gothic Rose Boots',
            tagline: 'Walk in beauty',
            description: 'Platform boots with rose-embossed leather and sterling silver buckles. Handcrafted Italian leather for lasting luxury.',
            price: '$425',
            spec: 'Italian Leather • Sterling Hardware • Handcrafted',
            badge: 'BESTSELLER',
            image: 'assets/images/products/gothic-boots.jpg',
            url: '/?product_id=br-005',
            variants: {
              sizes: ['6', '7', '8', '9', '10'],
              colors: [
                { name: 'Black', hex: '#000000' }
              ]
            }
          }
        },
        {
          x: 85,
          y: 45,
          product: {
            id: 'br-006',
            collection: 'BLACK ROSE',
            name: 'Rose Petal Scarf',
            tagline: 'Delicate darkness',
            description: 'Silk chiffon scarf with hand-painted rose petals. Oversized design offers endless styling possibilities.',
            price: '$135',
            spec: 'Silk Chiffon • Hand-Painted • Dry Clean',
            badge: null,
            image: 'assets/images/products/rose-scarf.jpg',
            url: '/?product_id=br-006',
            variants: {
              sizes: ['One Size'],
              colors: [
                { name: 'Black Rose', hex: '#1C1C1C' },
                { name: 'Midnight Rose', hex: '#0A0A0A' }
              ]
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
            name: 'Blood Rose Corset',
            tagline: 'Passion redefined',
            description: 'Structured corset with blood-red rose appliqués and sterling boning. Victorian romance meets modern edge.',
            price: '$325',
            spec: 'Silk Satin • Sterling Boning • Professional Clean',
            badge: 'NEW',
            image: 'assets/images/products/blood-corset.jpg',
            url: '/?product_id=lh-001',
            variants: {
              sizes: ['XS', 'S', 'M', 'L'],
              colors: [
                { name: 'Blood Red', hex: '#8B0000' },
                { name: 'Black', hex: '#000000' }
              ]
            }
          }
        },
        {
          x: 65,
          y: 40,
          product: {
            id: 'lh-002',
            collection: 'LOVE HURTS',
            name: 'Heartbreak Leather Pants',
            tagline: 'Danger in every step',
            description: 'High-waisted leather pants with heart-shaped hardware. Premium lambskin for second-skin fit and luxury feel.',
            price: '$475',
            spec: 'Lambskin Leather • Custom Hardware • Professional Clean',
            badge: 'BESTSELLER',
            image: 'assets/images/products/heartbreak-pants.jpg',
            url: '/?product_id=lh-002',
            variants: {
              sizes: ['XS', 'S', 'M', 'L'],
              colors: [
                { name: 'Black', hex: '#000000' }
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
            name: 'Thorn Crown Headpiece',
            tagline: 'Crowned in thorns',
            description: 'Statement headpiece featuring rose-gold thorns and blood-red crystals. Adjustable fit for any head size.',
            price: '$285',
            spec: 'Rose Gold • Swarovski Crystals • Handcrafted',
            badge: 'LIMITED',
            image: 'assets/images/products/thorn-crown.jpg',
            url: '/?product_id=lh-003',
            variants: {
              sizes: ['One Size'],
              colors: [
                { name: 'Rose Gold', hex: '#D4AF37' }
              ]
            }
          }
        },
        {
          x: 75,
          y: 50,
          product: {
            id: 'lh-004',
            collection: 'LOVE HURTS',
            name: 'Bleeding Heart Ring',
            tagline: 'Love eternal',
            description: 'Sterling silver ring with blood-red garnet heart. Each piece hand-engraved with rose thorns.',
            price: '$195',
            spec: 'Sterling Silver • Garnet Stone • Hand-Engraved',
            badge: null,
            image: 'assets/images/products/bleeding-ring.jpg',
            url: '/?product_id=lh-004',
            variants: {
              sizes: ['5', '6', '7', '8', '9'],
              colors: [
                { name: 'Silver', hex: '#C0C0C0' }
              ]
            }
          }
        },
        {
          x: 40,
          y: 70,
          product: {
            id: 'lh-005',
            collection: 'LOVE HURTS',
            name: 'Passion Killer Heels',
            tagline: 'Walk with confidence',
            description: 'Sky-high stilettos with blood-red patent leather and thorn-shaped heels. Italian craftsmanship at its finest.',
            price: '$525',
            spec: 'Patent Leather • Italian Made • Thorn Heel Design',
            badge: 'BESTSELLER',
            image: 'assets/images/products/passion-heels.jpg',
            url: '/?product_id=lh-005',
            variants: {
              sizes: ['6', '7', '8', '9', '10'],
              colors: [
                { name: 'Blood Red', hex: '#8B0000' },
                { name: 'Black', hex: '#000000' }
              ]
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
            name: 'Golden Hour Gown',
            tagline: 'Radiate luxury',
            description: 'Floor-length gown in champagne silk with hand-beaded gold details. Red carpet ready with timeless elegance.',
            price: '$1,295',
            spec: 'Silk Charmeuse • Hand-Beaded • Couture Finish',
            badge: 'LIMITED',
            image: 'assets/images/products/golden-gown.jpg',
            url: '/?product_id=sg-001',
            variants: {
              sizes: ['XS', 'S', 'M', 'L'],
              colors: [
                { name: 'Champagne Gold', hex: '#D4AF37' }
              ]
            }
          }
        },
        {
          x: 60,
          y: 35,
          product: {
            id: 'sg-002',
            collection: 'SIGNATURE',
            name: 'Executive Power Blazer',
            tagline: 'Command attention',
            description: 'Tailored blazer in Italian wool with gold hardware. Sharp silhouette for the modern executive.',
            price: '$645',
            spec: 'Italian Wool • Custom Tailored • Gold Hardware',
            badge: 'BESTSELLER',
            image: 'assets/images/products/power-blazer.jpg',
            url: '/?product_id=sg-002',
            variants: {
              sizes: ['XS', 'S', 'M', 'L', 'XL'],
              colors: [
                { name: 'Black', hex: '#000000' },
                { name: 'Charcoal', hex: '#1C1C1C' }
              ]
            }
          }
        },
        {
          x: 75,
          y: 55,
          product: {
            id: 'sg-003',
            collection: 'SIGNATURE',
            name: 'Dynasty Handbag',
            tagline: 'Carry your legacy',
            description: 'Structured leather handbag with 24k gold-plated hardware. Handcrafted in Florence with timeless design.',
            price: '$1,450',
            spec: 'Italian Leather • 24k Gold Hardware • Florence Made',
            badge: 'NEW',
            image: 'assets/images/products/dynasty-bag.jpg',
            url: '/?product_id=sg-003',
            variants: {
              sizes: ['One Size'],
              colors: [
                { name: 'Black', hex: '#000000' },
                { name: 'Cognac', hex: '#8B4513' }
              ]
            }
          }
        },
        {
          x: 45,
          y: 65,
          product: {
            id: 'sg-004',
            collection: 'SIGNATURE',
            name: 'Prestige Watch',
            tagline: 'Time is luxury',
            description: 'Swiss automatic watch with mother-of-pearl face and rose gold case. Limited edition of 100 pieces.',
            price: '$3,995',
            spec: 'Swiss Movement • Rose Gold • Limited Edition',
            badge: 'LIMITED',
            image: 'assets/images/products/prestige-watch.jpg',
            url: '/?product_id=sg-004',
            variants: {
              sizes: ['One Size'],
              colors: [
                { name: 'Rose Gold', hex: '#D4AF37' }
              ]
            }
          }
        },
        {
          x: 85,
          y: 45,
          product: {
            id: 'sg-005',
            collection: 'SIGNATURE',
            name: 'Empress Sunglasses',
            tagline: 'Shield your gaze',
            description: 'Oversized cat-eye sunglasses with 24k gold-plated frames. Italian craftsmanship with UV400 protection.',
            price: '$425',
            spec: '24k Gold Frames • UV400 Protection • Italian Made',
            badge: 'BESTSELLER',
            image: 'assets/images/products/empress-sunglasses.jpg',
            url: '/?product_id=sg-005',
            variants: {
              sizes: ['One Size'],
              colors: [
                { name: 'Gold', hex: '#D4AF37' },
                { name: 'Black Gold', hex: '#1C1C1C' }
              ]
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
