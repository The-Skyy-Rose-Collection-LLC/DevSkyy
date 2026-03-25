/**
 * SkyyRose — WooCommerce Product CSV Generator
 * =============================================
 * Generates a WooCommerce-ready product import CSV including:
 *   - Simple products
 *   - Variable products (parent + color variations)
 *   - Grouped products (sets sold separately)
 *
 * Usage:
 *   node build/generate-woocommerce-csv.js
 *
 * Output:
 *   assets/data/woocommerce-import.csv
 *
 * Before importing to WooCommerce:
 *   1. Upload all product images to WordPress Media Library
 *   2. Replace IMAGE_BASE_URL with your actual domain
 *   3. WooCommerce > Products > Import > select the CSV
 */

const path = require('path');
const fs   = require('fs');

const ROOT     = path.join(__dirname, '..');
const ECOM_DIR = path.join(ROOT, 'assets/images/products-ecom');
const DATA_DIR = path.join(ROOT, 'assets/data');
const OUT_CSV  = path.join(DATA_DIR, 'woocommerce-import.csv');

// Replace with your live domain before importing
const IMAGE_BASE_URL = 'https://skyyrose.com/wp-content/uploads/products';

const SIZES_APPAREL  = 'S|M|L|XL|2XL|3XL';
const SIZES_ONE_SIZE = 'One Size';
const TAX_STATUS     = 'taxable';

// ── Product Data ──────────────────────────────────────────────────────────────
// type: 'simple' | 'variable' | 'grouped'
// status: 'instock' | 'onbackorder'
// For variable: colorways array with { color, price, status }
// For grouped:  children array with simple product defs

const PRODUCTS = [

  // ── BLACK ROSE ─────────────────────────────────────────────────────────────
  {
    type: 'simple',
    id: 'br-001', sku: 'SR-BR-001',
    name: 'BLACK Rose Crewneck',
    price: 60, status: 'onbackorder',
    category: 'BLACK ROSE Collection',
    sizes: SIZES_APPAREL,
    images: ['br-001-product-web.jpg'],
    col: 'black-rose',
  },
  {
    type: 'simple',
    id: 'br-002', sku: 'SR-BR-002',
    name: 'BLACK Rose Joggers',
    price: 50, status: 'onbackorder',
    category: 'BLACK ROSE Collection',
    sizes: SIZES_APPAREL,
    images: ['br-002-product-web.jpg'],
    col: 'black-rose',
  },
  {
    type: 'variable',
    id: 'br-003', sku: 'SR-BR-003',
    name: 'BLACK is Beautiful Jersey',
    category: 'BLACK ROSE Collection',
    sizes: SIZES_APPAREL,
    col: 'black-rose',
    colorways: [
      { color: 'White',        price: 80,  status: 'instock',      images: ['br-003-product-6-web.jpg', 'br-003-product-7-web.jpg'] },
      { color: 'Black',        price: 80,  status: 'instock',      images: ['br-003-product-3-web.jpg'] },
      { color: 'Giants',       price: 95,  status: 'instock',      images: ['br-003-product-4-web.jpg', 'br-003-product-5-web.jpg'] },
      { color: 'Last Oakland', price: 110, status: 'onbackorder',  images: ['br-003-product-web.jpg', 'br-003-product-2-web.jpg'] },
    ],
  },
  {
    type: 'simple',
    id: 'br-004', sku: 'SR-BR-004',
    name: 'BLACK Rose Hoodie',
    price: 40, status: 'onbackorder',
    category: 'BLACK ROSE Collection',
    sizes: SIZES_APPAREL,
    images: ['br-004-product-web.jpg'],
    col: 'black-rose',
  },
  {
    type: 'simple',
    id: 'br-005', sku: 'SR-BR-005',
    name: 'BLACK Rose Hoodie — Signature Edition',
    price: 65, status: 'instock',
    category: 'BLACK ROSE Collection',
    sizes: SIZES_APPAREL,
    images: ['br-005-product-web.jpg'],
    col: 'black-rose',
  },
  {
    type: 'simple',
    id: 'br-006', sku: 'SR-BR-006',
    name: 'BLACK Rose Sherpa Jacket',
    price: 95, status: 'onbackorder',
    category: 'BLACK ROSE Collection',
    sizes: SIZES_APPAREL,
    images: ['br-006-product-web.jpg', 'br-006-product-2-web.jpg'],
    col: 'black-rose',
  },
  {
    type: 'simple',
    id: 'br-007', sku: 'SR-BR-007',
    name: 'BLACK Rose × Love Hurts Basketball Shorts',
    price: 65, status: 'instock',
    category: 'BLACK ROSE Collection',
    sizes: SIZES_APPAREL,
    images: ['br-007-product-web.jpg', 'br-007-product-2-web.jpg'],
    col: 'black-rose',
  },
  {
    type: 'simple',
    id: 'br-008', sku: 'SR-BR-008',
    name: "Women's BLACK Rose Hooded Dress",
    price: 0, status: 'onbackorder',
    category: 'BLACK ROSE Collection',
    sizes: SIZES_APPAREL,
    images: ['br-008-product-web.jpg'],
    col: 'black-rose',
    note: 'PRICE PLACEHOLDER — update before publishing',
  },

  // ── LOVE HURTS ─────────────────────────────────────────────────────────────
  {
    type: 'simple',
    id: 'lh-001', sku: 'SR-LH-001',
    name: 'The Fannie',
    price: 70, status: 'onbackorder',
    category: 'LOVE HURTS Collection',
    sizes: SIZES_ONE_SIZE,
    images: ['lh-001-product-web.jpg', 'lh-001-product-2-web.jpg'],
    col: 'love-hurts',
  },
  {
    type: 'variable',
    id: 'lh-002', sku: 'SR-LH-002',
    name: 'Love Hurts Joggers',
    category: 'LOVE HURTS Collection',
    sizes: SIZES_APPAREL,
    col: 'love-hurts',
    colorways: [
      { color: 'Black', price: 67, status: 'instock', images: ['lh-002-product-web.jpg'] },
      { color: 'White', price: 67, status: 'instock', images: ['lh-002b-product-web.jpg', 'lh-002b-product-2-web.jpg'] },
    ],
  },
  {
    type: 'simple',
    id: 'lh-003', sku: 'SR-LH-003',
    name: 'Love Hurts Basketball Shorts',
    price: 55, status: 'instock',
    category: 'LOVE HURTS Collection',
    sizes: SIZES_APPAREL,
    images: ['lh-003-product-web.jpg', 'lh-003-product-2-web.jpg', 'lh-003-product-3-web.jpg'],
    col: 'love-hurts',
  },
  {
    type: 'simple',
    id: 'lh-004', sku: 'SR-LH-004',
    name: 'Love Hurts Varsity Jacket',
    price: 85, status: 'onbackorder',
    category: 'LOVE HURTS Collection',
    sizes: SIZES_APPAREL,
    images: ['lh-004-product-web.jpg'],
    col: 'love-hurts',
  },

  // ── SIGNATURE ──────────────────────────────────────────────────────────────
  {
    type: 'grouped',
    id: 'sg-001', sku: 'SR-SG-001',
    name: 'The Bay Set',
    category: 'SIGNATURE Collection',
    images: ['sg-001-product-web.jpg', 'sg-001-product-2-web.jpg'],
    col: 'signature',
    children: [
      { sku: 'SR-SG-001-TEE',    name: 'The Bay Tee',    price: 40, sizes: SIZES_APPAREL, status: 'onbackorder' },
      { sku: 'SR-SG-001-SHORTS', name: 'The Bay Shorts', price: 50, sizes: SIZES_APPAREL, status: 'onbackorder' },
    ],
  },
  {
    type: 'grouped',
    id: 'sg-002', sku: 'SR-SG-002',
    name: 'Stay Golden Set',
    category: 'SIGNATURE Collection',
    images: ['sg-002-product-web.jpg'],
    col: 'signature',
    children: [
      { sku: 'SR-SG-005',        name: 'Stay Golden Tee',    price: 40, sizes: SIZES_APPAREL, status: 'instock' },
      { sku: 'SR-SG-002-SHORTS', name: 'Stay Golden Shorts', price: 50, sizes: SIZES_APPAREL, status: 'onbackorder' },
    ],
  },
  {
    type: 'variable',
    id: 'sg-003', sku: 'SR-SG-003',
    name: 'The Signature Tee',
    category: 'SIGNATURE Collection',
    sizes: SIZES_APPAREL,
    col: 'signature',
    colorways: [
      { color: 'Orchid', price: 15, status: 'instock', images: ['sg-003-product-web.jpg', 'sg-003-product-2-web.jpg'] },
      { color: 'White',  price: 15, status: 'instock', images: ['sg-004-product-web.jpg', 'sg-004-product-2-web.jpg'] },
    ],
  },
  {
    type: 'simple',
    id: 'sg-005', sku: 'SR-SG-005',
    name: 'Stay Golden Tee',
    price: 40, status: 'instock',
    category: 'SIGNATURE Collection',
    sizes: SIZES_APPAREL,
    images: ['sg-005-product-web.jpg'],
    col: 'signature',
  },
  {
    type: 'simple',
    id: 'sg-006', sku: 'SR-SG-006',
    name: 'Mint & Lavender Hoodie',
    price: 45, status: 'instock',
    category: 'SIGNATURE Collection',
    sizes: SIZES_APPAREL,
    images: ['sg-006-product-web.jpg', 'sg-006-product-2-web.jpg', 'sg-006-product-3-web.jpg'],
    col: 'signature',
  },
  {
    type: 'variable',
    id: 'sg-007', sku: 'SR-SG-007',
    name: 'The Signature Beanie',
    category: 'SIGNATURE Collection',
    sizes: SIZES_ONE_SIZE,
    col: 'signature',
    colorways: [
      { color: 'Red',    price: 25, status: 'instock', images: ['sg-007-product-web.jpg'] },
      { color: 'Purple', price: 25, status: 'instock', images: ['sg-007-product-2-web.jpg'] },
      { color: 'Black',  price: 25, status: 'instock', images: ['sg-007-product-3-web.jpg'] },
    ],
  },
  {
    type: 'simple',
    id: 'sg-009', sku: 'SR-SG-009',
    name: 'The Sherpa Jacket',
    price: 80, status: 'onbackorder',
    category: 'SIGNATURE Collection',
    sizes: SIZES_APPAREL,
    images: ['sg-009-product-web.jpg', 'sg-009-product-2-web.jpg'],
    col: 'signature',
  },
  {
    type: 'variable',
    id: 'sg-010', sku: 'SR-SG-010',
    name: 'The Bridge Series Shorts',
    category: 'SIGNATURE Collection',
    sizes: SIZES_APPAREL,
    col: 'signature',
    colorways: [
      { color: 'Bay Bridge',   price: 60, status: 'onbackorder', images: ['sg-010-product-web.jpg'] },
      { color: 'Golden Gate',  price: 60, status: 'onbackorder', images: ['sg-010-product-2-web.jpg'] },
    ],
  },
];

// ── CSV Helpers ───────────────────────────────────────────────────────────────
function imgUrl(productId, filename) {
  return `${IMAGE_BASE_URL}/${productId}/${filename}`;
}

function imgUrls(productId, files) {
  return files.map(f => imgUrl(productId, f)).join(', ');
}

function esc(val) {
  const s = String(val ?? '');
  if (s.includes(',') || s.includes('"') || s.includes('\n')) {
    return `"${s.replace(/"/g, '""')}"`;
  }
  return s;
}

function row(cols) {
  return cols.map(esc).join(',');
}

// ── CSV Column Headers ────────────────────────────────────────────────────────
const HEADERS = [
  'ID', 'Type', 'SKU', 'Name', 'Published',
  'Is featured?', 'Visibility in catalog',
  'Short description', 'Description',
  'Date sale price starts', 'Date sale price ends',
  'Tax status', 'Tax class',
  'In stock?', 'Stock', 'Low stock amount',
  'Backorders allowed?', 'Sold individually?',
  'Weight (kg)', 'Length (cm)', 'Width (cm)', 'Height (cm)',
  'Allow customer reviews?', 'Purchase note',
  'Sale price', 'Regular price',
  'Categories', 'Tags', 'Shipping class',
  'Images',
  'Download limit', 'Download expiry',
  'Parent', 'Grouped products',
  'Upsells', 'Cross-sells',
  'External URL', 'Button text', 'Position',
  'Attribute 1 name', 'Attribute 1 value(s)', 'Attribute 1 visible', 'Attribute 1 global',
  'Attribute 2 name', 'Attribute 2 value(s)', 'Attribute 2 visible', 'Attribute 2 global',
  'Meta: _note',
];

function baseRow(p, type, overrides = {}) {
  return {
    ID: '', Type: type, SKU: p.sku || '',
    Name: p.name, Published: 1,
    'Is featured?': 0, 'Visibility in catalog': 'visible',
    'Short description': '', Description: '',
    'Date sale price starts': '', 'Date sale price ends': '',
    'Tax status': TAX_STATUS, 'Tax class': '',
    'In stock?': p.status === 'instock' ? 1 : (p.status === 'onbackorder' ? 1 : 0),
    Stock: '', 'Low stock amount': '',
    'Backorders allowed?': p.status === 'onbackorder' ? 'notify' : 'no',
    'Sold individually?': 0,
    'Weight (kg)': '', 'Length (cm)': '', 'Width (cm)': '', 'Height (cm)': '',
    'Allow customer reviews?': 1, 'Purchase note': '',
    'Sale price': '', 'Regular price': p.price || '',
    Categories: p.category || '',
    Tags: '', 'Shipping class': '',
    Images: p.images ? imgUrls(p.id || overrides.id, p.images) : '',
    'Download limit': '', 'Download expiry': '',
    Parent: '', 'Grouped products': '',
    Upsells: '', 'Cross-sells': '',
    'External URL': '', 'Button text': '', Position: '',
    'Attribute 1 name': '', 'Attribute 1 value(s)': '', 'Attribute 1 visible': '', 'Attribute 1 global': '',
    'Attribute 2 name': '', 'Attribute 2 value(s)': '', 'Attribute 2 visible': '', 'Attribute 2 global': '',
    'Meta: _note': p.note || '',
    ...overrides,
  };
}

// ── Row Generators ────────────────────────────────────────────────────────────
function simpleRow(p) {
  return [baseRow(p, 'simple', {
    'Attribute 1 name': 'Size',
    'Attribute 1 value(s)': p.sizes || SIZES_APPAREL,
    'Attribute 1 visible': 1,
    'Attribute 1 global': 1,
  })];
}

function variableRows(p) {
  const allColors = p.colorways.map(c => c.color).join('|');
  const rows = [];

  // Parent row
  rows.push(baseRow(p, 'variable', {
    'Regular price': '',  // parent has no price
    'In stock?': 1,
    Images: imgUrls(p.id, p.colorways[0].images),  // use first colorway as hero
    'Attribute 1 name': 'Color',
    'Attribute 1 value(s)': allColors,
    'Attribute 1 visible': 1,
    'Attribute 1 global': 1,
    'Attribute 2 name': 'Size',
    'Attribute 2 value(s)': p.sizes || SIZES_APPAREL,
    'Attribute 2 visible': 1,
    'Attribute 2 global': 1,
  }));

  // Variation rows (one per colorway)
  p.colorways.forEach((cw, i) => {
    rows.push(baseRow(
      { ...p, price: cw.price, status: cw.status, images: cw.images, note: '' },
      'variation',
      {
        SKU: `${p.sku}-${cw.color.toUpperCase().replace(/\s+/g, '-')}`,
        Name: `${p.name} — ${cw.color}`,
        Parent: p.sku,
        Images: imgUrls(p.id, cw.images),
        'Regular price': cw.price,
        'Backorders allowed?': cw.status === 'onbackorder' ? 'notify' : 'no',
        'In stock?': 1,
        Position: i,
        'Attribute 1 name': 'Color',
        'Attribute 1 value(s)': cw.color,
        'Attribute 1 visible': 1,
        'Attribute 1 global': 1,
        'Attribute 2 name': 'Size',
        'Attribute 2 value(s)': p.sizes || SIZES_APPAREL,
        'Attribute 2 visible': 1,
        'Attribute 2 global': 1,
      }
    ));
  });

  return rows;
}

function groupedRows(p) {
  const rows = [];
  const childSkus = p.children.map(c => c.sku).join(', ');

  // Grouped parent
  rows.push(baseRow(p, 'grouped', {
    'Regular price': '',
    'In stock?': 1,
    'Backorders allowed?': 'no',
    'Grouped products': childSkus,
    'Attribute 1 name': '', 'Attribute 1 value(s)': '',
  }));

  // Individual children
  p.children.forEach(child => {
    rows.push(baseRow(
      { ...child, id: p.id, category: p.category, col: p.col, images: [] },
      'simple',
      {
        SKU: child.sku,
        Name: child.name,
        'Regular price': child.price,
        'Backorders allowed?': child.status === 'onbackorder' ? 'notify' : 'no',
        'In stock?': 1,
        Images: '',  // share grouped parent image
        'Attribute 1 name': 'Size',
        'Attribute 1 value(s)': child.sizes || SIZES_APPAREL,
        'Attribute 1 visible': 1,
        'Attribute 1 global': 1,
      }
    ));
  });

  return rows;
}

// ── Main ──────────────────────────────────────────────────────────────────────
function main() {
  if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });

  const allRows = [HEADERS.join(',')];
  let counts = { simple: 0, variable: 0, variation: 0, grouped: 0, child: 0 };

  for (const p of PRODUCTS) {
    let productRows = [];

    if (p.type === 'simple') {
      productRows = simpleRow(p);
      counts.simple++;
    } else if (p.type === 'variable') {
      productRows = variableRows(p);
      counts.variable++;
      counts.variation += p.colorways.length;
    } else if (p.type === 'grouped') {
      productRows = groupedRows(p);
      counts.grouped++;
      counts.child += p.children.length;
    }

    for (const r of productRows) {
      allRows.push(row(HEADERS.map(h => r[h] ?? '')));
    }
  }

  fs.writeFileSync(OUT_CSV, allRows.join('\n'), 'utf8');

  const totalProducts  = counts.simple + counts.variable + counts.grouped;
  const totalRows      = counts.simple + counts.variable + counts.variation + counts.grouped + counts.child;

  console.log('\n SkyyRose — WooCommerce CSV Generator');
  console.log('='.repeat(56));
  console.log(`  Products:   ${totalProducts} (${counts.simple} simple, ${counts.variable} variable, ${counts.grouped} grouped)`);
  console.log(`  Variations: ${counts.variation}`);
  console.log(`  Set items:  ${counts.child}`);
  console.log(`  Total rows: ${totalRows}`);
  console.log(`\n  Output: assets/data/woocommerce-import.csv`);
  console.log('\n  Before importing to WooCommerce:');
  console.log(`  1. Upload all product images to WordPress Media Library`);
  console.log(`  2. Replace IMAGE_BASE_URL in this script with your domain:`);
  console.log(`     Currently: ${IMAGE_BASE_URL}`);
  console.log(`  3. WooCommerce > Products > Import > select the CSV`);
  console.log(`\n  ⚠️  br-008 Women's Dress price is $0 — update before publishing\n`);
}

main();
