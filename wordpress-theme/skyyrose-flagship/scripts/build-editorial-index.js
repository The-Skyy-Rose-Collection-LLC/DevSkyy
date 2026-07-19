#!/usr/bin/env node
/**
 * Build data/editorial-index.json from data/dossiers/*.md.
 *
 * Dossiers are INTERNAL render-pipeline specs (garment locks, branding
 * placement, negative prompts, scene direction) and must never deploy or
 * render. The only thing the storefront needs from them is a boolean:
 * "does this product qualify for the editorial PDP layout?"
 *
 * This script applies the same eligibility predicate the retired runtime
 * parser used (inc/product-catalog.php pre-1.11.2): a dossier qualifies
 * when it has a non-empty "**Garment type lock:**" line OR a non-empty
 * "### Front" subsection under "## Branding". Output is a deterministic
 * slug->true map — no dossier text ever enters the artifact.
 *
 * Run from anywhere: node skyyrose-flagship/scripts/build-editorial-index.js
 * Wired into `npm run build` (wordpress-theme/package.json).
 */

'use strict';

const fs = require('fs');
const path = require('path');

const themeDir = path.resolve(__dirname, '..');
const dossierDir = path.join(themeDir, 'data', 'dossiers');
const outFile = path.join(themeDir, 'data', 'editorial-index.json');

function isEligible(raw) {
	// Strip YAML front-matter (between --- fences), as the PHP parser did.
	let body = raw;
	const fm = raw.match(/^---\s*\n[\s\S]*?\n---\s*\n/);
	if (fm) {
		body = raw.slice(fm[0].length);
	}

	const lock = body.match(/\*\*Garment type lock:\*\*\s*([\s\S]+?)(?:\n\n|\n##)/);
	if (lock && lock[1].trim() !== '') {
		return true;
	}

	const branding = body.match(/## Branding[^\n]*\n([\s\S]*?)(?=\n## [^#]|$)/);
	if (branding) {
		const front = branding[1].match(/### Front\s*\n([\s\S]*?)(?=\n### |\n## |$)/);
		if (front && front[1].trim() !== '') {
			return true;
		}
	}

	return false;
}

if (!fs.existsSync(dossierDir)) {
	console.error(`build-editorial-index: dossier dir missing: ${dossierDir}`);
	process.exit(1);
}

const eligible = {};
const files = fs.readdirSync(dossierDir).filter((f) => f.endsWith('.md')).sort();

for (const file of files) {
	const raw = fs.readFileSync(path.join(dossierDir, file), 'utf8');
	if (raw.trim() === '') {
		continue;
	}
	if (isEligible(raw)) {
		eligible[file.replace(/\.md$/, '')] = true;
	}
}

if (Object.keys(eligible).length === 0) {
	// A dossier corpus that compiles to zero eligible products means the
	// parse broke, not that every product lost its editorial layout.
	console.error('build-editorial-index: 0 eligible dossiers — refusing to write an empty index');
	process.exit(1);
}

const artifact = {
	generated_by: 'scripts/build-editorial-index.js',
	source: 'data/dossiers/*.md (not deployed)',
	count: Object.keys(eligible).length,
	eligible,
};

fs.writeFileSync(outFile, JSON.stringify(artifact, null, '\t') + '\n');
console.log(`build-editorial-index: ${artifact.count}/${files.length} dossiers eligible -> ${path.relative(process.cwd(), outFile)}`);
