#!/usr/bin/env node
/**
 * Minify every assets/js/*.js (and assets/js/experiences/*.js) source to
 * its .min.js sibling using terser.
 *
 * Hand-checked-in mins have drifted from sources, causing stale code to ship
 * to production (Phase 2 launch sprint, bug B2). This script makes regen
 * mechanical and idempotent.
 *
 * Excluded: anything already ending in .min.js, anything under vendor/
 * (already shipped minified by upstream), and directories not explicitly
 * listed below. experiences/*.js files are global-script-style Three.js
 * orchestration (no ESM imports) and minify cleanly with the default config.
 */

const fs = require('fs');
const path = require('path');
const { minify } = require('terser');

const SRC_DIR = path.resolve(__dirname, '..', 'assets', 'js');
// Each entry: directory absolute path, relative label for log output.
const SCAN_DIRS = [
	{ dir: SRC_DIR, label: '' },
	{ dir: path.join(SRC_DIR, 'experiences'), label: 'experiences/' },
];

async function main() {
	const sources = [];
	for ( const { dir, label } of SCAN_DIRS ) {
		if ( ! fs.existsSync( dir ) ) { continue; }
		const entries = fs.readdirSync( dir );
		for ( const f of entries ) {
			if ( ! f.endsWith( '.js' ) ) { continue; }
			if ( f.endsWith( '.min.js' ) ) { continue; }
			sources.push({ src: path.join( dir, f ), label });
		}
	}

	let built = 0;
	let failed = 0;
	for (const { src, label } of sources) {
		const base = path.basename(src, '.js');
		const dest = path.join( path.dirname( src ), `${base}.min.js` );
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
			console.log(`  ✓ ${label}${base}.js → ${label}${base}.min.js  (${code.length} → ${result.code.length} bytes)`);
		} catch (err) {
			failed += 1;
			console.error(`  ✗ ${label}${base}.js — ${err.message}`);
		}
	}
	console.log(`\nDone: ${built} built, ${failed} failed.`);
	process.exit(failed === 0 ? 0 : 1);
}

main().catch((err) => {
	console.error(err);
	process.exit(1);
});
