#!/usr/bin/env node
/**
 * rename-assets.js — Rename source product photos to descriptive names
 *
 * Maps all files referenced in products-catalog.html to human-readable names
 * like br-001-crewneck-front.png instead of PhotoRoom_011_20230616_170635.png.
 *
 * Usage:
 *   node build/rename-assets.js           # dry run (preview only)
 *   node build/rename-assets.js --apply   # actually rename files
 */

const fs   = require('fs');
const path = require('path');

const BASE   = path.join(__dirname, '../assets/images/source-products');
const DRY    = !process.argv.includes('--apply');

if (DRY) {
  console.log('\n[rename-assets] DRY RUN — pass --apply to execute renames\n');
}

// ──────────────────────────────────────────────────────────────────────────────
// RENAME MAP
// Format: { dir: 'collection-dir', from: 'old-filename', to: 'new-filename' }
// Special action 'move': relocate file from one dir to another
// ──────────────────────────────────────────────────────────────────────────────

const RENAMES = [
  // ── BLACK ROSE ─────────────────────────────────────────────────────────────
  // BR-001 — BLACK Rose Crewneck
  { dir: 'black-rose', from: 'PhotoRoom_011_20230616_170635.png',   to: 'br-001-crewneck-front.png' },
  { dir: 'black-rose', from: 'PhotoRoom_001_20230616_170635.PNG',   to: 'br-001-crewneck-back.png'  },

  // BR-002 — BLACK Rose Joggers
  { dir: 'black-rose', from: 'PhotoRoom_010_20231221_160237.jpeg',  to: 'br-002-joggers.jpeg' },

  // BR-003 — BLACK is Beautiful Jersey (2 colorways)
  { dir: 'black-rose', from: '266AD7B0-88A6-4489-AA58-AB72A575BD33 3.JPG', to: 'br-003-jersey-last-oakland-back.jpg'  },
  { dir: 'black-rose', from: '5A8946B1-B51F-4144-BCBB-F028462077A0.jpg',   to: 'br-003-jersey-last-oakland-front.jpg' },
  { dir: 'black-rose', from: 'PhotoRoom_003_20230616_170635 (1).png',       to: 'br-003-jersey-giants-back.png'       },
  { dir: 'black-rose', from: 'BLACK is Beautiful Giants Front.jpg',          to: 'br-003-jersey-giants-front.jpg'      },
  { dir: 'black-rose', from: 'PhotoRoom_000_20230616_170635.png',            to: 'br-003-jersey-alt.png'               },
  { dir: 'black-rose', from: 'The BLACK Jersey (BLACK Rose Collection).jpg', to: 'br-003-jersey-black-front.jpg'       },

  // BR-004 — BLACK Rose Hoodie
  { dir: 'black-rose', from: 'PhotoRoom_001_20230523_204834.PNG',   to: 'br-004-hoodie-front.png' },

  // BR-005 — BLACK Rose Hoodie Signature Edition
  { dir: 'black-rose', from: 'PhotoRoom_008_20221210_093149.PNG',   to: 'br-005-hoodie-signature-front.png' },

  // BR-006 — BLACK Rose Sherpa Jacket
  { dir: 'black-rose', from: 'The BLACK Rose Sherpa Front.jpg',     to: 'br-006-sherpa-front.jpg' },
  { dir: 'black-rose', from: 'The BLACK Rose Sherpa Back.jpg',      to: 'br-006-sherpa-back.jpg'  },

  // BR-007 — BLACK Rose × Love Hurts Basketball Shorts (collab)
  { dir: 'black-rose', from: 'PhotoRoom_20221110_201933.PNG',       to: 'br-007-shorts-front.png' },
  { dir: 'black-rose', from: 'PhotoRoom_20221110_202133.PNG',       to: 'br-007-shorts-side.png'  },
  // IMG_1733.jpeg lives in love-hurts dir — move it to black-rose
  { dir: 'love-hurts', from: 'IMG_1733.jpeg', moveTo: 'black-rose', to: 'br-007-shorts-alt.jpeg' },

  // BR-008 — Women's BLACK Rose Hooded Dress
  { dir: 'black-rose', from: 'Womens Black Rose Hooded Dress.jpeg', to: 'br-008-hooded-dress-front.jpeg' },

  // ── LOVE HURTS ─────────────────────────────────────────────────────────────
  // LH-001 — The Fannie (fanny pack / waist bag)
  { dir: 'love-hurts', from: 'IMG_0117.jpeg',                                    to: 'lh-001-fannie-front-1.jpeg' },
  { dir: 'love-hurts', from: '4074E988-4DAF-4221-8446-4B93422AF437.jpg',         to: 'lh-001-fannie-front-2.jpg'  },

  // LH-002 — Love Hurts Joggers (Black / White colorways)
  { dir: 'love-hurts', from: 'IMG_2102.png',                                     to: 'lh-002-joggers-black.png'   },
  { dir: 'love-hurts', from: 'IMG_2103.png',                                     to: 'lh-002-joggers-white-1.png' },
  { dir: 'love-hurts', from: 'IMG_2105.png',                                     to: 'lh-002-joggers-white-2.png' },

  // LH-003 — Love Hurts Basketball Shorts
  { dir: 'love-hurts', from: 'PhotoRoom_004_20221110_200039.png',                to: 'lh-003-shorts-side.png'    },
  { dir: 'love-hurts', from: 'PhotoRoom_003_20221110_200039.png',                to: 'lh-003-shorts-side-2.png'  },
  { dir: 'love-hurts', from: 'PhotoRoom_018_20231221_160237.jpeg',               to: 'lh-003-shorts-front.jpeg'  },

  // ── SIGNATURE ──────────────────────────────────────────────────────────────
  // SG-001 — The Bay Set
  { dir: 'signature', from: '0F85F48C-364B-43CB-8297-E90BB7B8BB51 2.jpg',       to: 'sg-001-bay-set-1.jpg' },
  { dir: 'signature', from: '24661692-0F81-43F4-AA69-7E026552914A.jpg',         to: 'sg-001-bay-set-2.jpg' },

  // SG-002 — Stay Golden Set
  { dir: 'signature', from: '562143CF-4A77-42B8-A58C-C77ED21E9B5E.jpg',         to: 'sg-002-stay-golden-set.jpg' },

  // SG-003 — Signature Tee Orchid
  { dir: 'signature', from: 'IMG_0553.JPG',                                      to: 'sg-003-tee-orchid-front.jpg' },
  { dir: 'signature', from: 'Signature T \u201cOrchard\u201d.jpeg',              to: 'sg-003-tee-orchid.jpeg'      },

  // SG-004 — Signature Tee White
  { dir: 'signature', from: 'IMG_0554.JPG',                                      to: 'sg-004-tee-white-front.jpg' },
  { dir: 'signature', from: 'Signature T \u201cWhite\u201d.jpeg',                to: 'sg-004-tee-white.jpeg'      },

  // SG-005 — Stay Golden Tee
  { dir: 'signature', from: 'Photo Dec 18 2023, 6 09 21 PM.jpg',                to: 'sg-005-stay-golden-tee.jpg' },

  // SG-006 — Mint & Lavender Hoodie
  { dir: 'signature', from: 'PhotoRoom_004_20231221_160237.jpeg',               to: 'sg-006-mint-lavender-hoodie-front.jpeg' },
  { dir: 'signature', from: 'Mint & Lavender Set (Sold Separately) .jpeg',      to: 'sg-006-mint-lavender-set-1.jpeg'        },
  { dir: 'signature', from: 'MINT & Lavender Set 2 .jpeg',                      to: 'sg-006-mint-lavender-set-2.jpeg'        },

  // SG-007 — Signature Beanie Red
  { dir: 'signature', from: 'Photoroom_010_20240926_104051.jpg',                to: 'sg-007-beanie-red.jpg' },

  // SG-008 — Signature Beanie (original)
  { dir: 'signature', from: 'PhotoRoom_000_20221210_093149.png',                to: 'sg-008-beanie.png' },

  // SG-009 — The Sherpa Jacket (moved from Love Hurts)
  { dir: 'signature', from: 'PhotoRoom_002_20231221_072338.jpg',                to: 'sg-009-sherpa-front.jpg' },
  { dir: 'signature', from: 'PhotoRoom_003_20231221_072338.jpg',                to: 'sg-009-sherpa-back.jpg'  },
];

// ──────────────────────────────────────────────────────────────────────────────
// Execute renames
// ──────────────────────────────────────────────────────────────────────────────

let renamed = 0;
let skipped = 0;
let missing = 0;

// Build map of new names we're creating (to detect catalog update needed)
const newFilenames = {}; // { 'black-rose/br-001-crewneck-front.png': 'black-rose/PhotoRoom_011...' }

for (const r of RENAMES) {
  const srcDir  = path.join(BASE, r.dir);
  const srcFile = path.join(srcDir, r.from);
  const destDir = r.moveTo ? path.join(BASE, r.moveTo) : srcDir;
  const destFile = path.join(destDir, r.to);

  const finalDir = r.moveTo || r.dir;
  newFilenames[`${finalDir}/${r.to}`] = `${r.dir}/${r.from}`;

  if (!fs.existsSync(srcFile)) {
    console.log(`  MISSING  ${r.dir}/${r.from}`);
    missing++;
    continue;
  }

  if (fs.existsSync(destFile) && srcFile !== destFile) {
    console.log(`  EXISTS   ${finalDir}/${r.to} (skipping)`);
    skipped++;
    continue;
  }

  const action = r.moveTo ? `MOVE  ${r.dir} → ${r.moveTo}` : 'RENAME';
  console.log(`  ${action}  ${r.from}`);
  console.log(`         → ${r.to}`);

  if (!DRY) {
    if (!fs.existsSync(destDir)) fs.mkdirSync(destDir, { recursive: true });
    fs.renameSync(srcFile, destFile);
  }
  renamed++;
}

console.log(`\n  ${DRY ? '[DRY RUN] Would rename' : 'Renamed'}: ${renamed} | Skipped: ${skipped} | Missing: ${missing}`);

// ──────────────────────────────────────────────────────────────────────────────
// Report unmapped files (not in RENAMES list)
// ──────────────────────────────────────────────────────────────────────────────

console.log('\n──────────────────────────────────────────────────────');
console.log('UNMAPPED FILES (not in catalog):');
console.log('──────────────────────────────────────────────────────');

const CATALOG_DIRS = ['black-rose', 'love-hurts', 'signature', 'mis'];
const mappedSrc = new Set(RENAMES.map(r => `${r.dir}/${r.from}`));

for (const dir of CATALOG_DIRS) {
  const dirPath = path.join(BASE, dir);
  if (!fs.existsSync(dirPath)) continue;
  const files = fs.readdirSync(dirPath).filter(f => !f.startsWith('.') && !f.startsWith('_'));
  const unmapped = files.filter(f => !mappedSrc.has(`${dir}/${f}`));
  if (unmapped.length > 0) {
    console.log(`\n  ${dir}/`);
    for (const f of unmapped) {
      const tag = f.startsWith('skyyrosedad_') ? '[AI concept]' : '            ';
      console.log(`    ${tag}  ${f}`);
    }
  }
}

if (!DRY) {
  console.log('\n──────────────────────────────────────────────────────');
  console.log('NOTE: Update products-catalog.html with new filenames.');
  console.log('Run: node build/update-catalog-filenames.js');
}
