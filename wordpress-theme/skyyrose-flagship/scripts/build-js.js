#!/usr/bin/env node
/**
 * Minify every assets/js/*.js source to assets/js/*.min.js using terser.
 *
 * Hand-checked-in mins have drifted from sources, causing stale code to ship
 * to production (Phase 2 launch sprint, bug B2). This script makes regen
 * mechanical and idempotent. Run via:  npx terser ... (driven by this file)
 *
 * Source files excluded: anything already ending in .min.js (we never
 * minify a minified file), and files inside experiences/ (Three.js worlds
 * shipped as ESM source, not minified).
 */

const fs = require('fs');
const path = require('path');
const { minify } = require('terser');

const SRC_DIR = path.resolve(__dirname, '..', 'assets', 'js');

async function main() {
	const entries = fs.readdirSync(SRC_DIR);
	const sources = entries
		.filter((f) => f.endsWith('.js') && !f.endsWith('.min.js'))
		.map((f) => path.join(SRC_DIR, f));

	let built = 0;
	let failed = 0;
	for (const src of sources) {
		const base = path.basename(src, '.js');
		const dest = path.join(SRC_DIR, `${base}.min.js`);
		const code = fs.readFileSync(src, 'utf8');
		try {
			// No sourceMap — source maps would expose full unminified JS source on
			// production via the sourceMappingURL comment. Defenders should not have
			// to think about whether maps shipped or not; the safe default is off.
			const result = await minify(code, {
				compress: { passes: 2 },
				mangle: true,
				format: { comments: false },
			});
			fs.writeFileSync(dest, result.code, 'utf8');
			built += 1;
			console.log(`  ✓ ${base}.js → ${base}.min.js  (${code.length} → ${result.code.length} bytes)`);
		} catch (err) {
			failed += 1;
			console.error(`  ✗ ${base}.js — ${err.message}`);
		}
	}
	console.log(`\nDone: ${built} built, ${failed} failed.`);
	process.exit(failed === 0 ? 0 : 1);
}

main().catch((err) => {
	console.error(err);
	process.exit(1);
});
