#!/usr/bin/env node
/**
 * Minify every assets/js/*.js and assets/js/system/*.js source to
 * its .min.js sibling using terser.
 *
 * Hand-checked-in mins have drifted from sources, causing stale code to ship
 * to production (Phase 2 launch sprint, bug B2). This script makes regen
 * mechanical and idempotent.
 *
 * Excluded: anything already ending in .min.js, anything under vendor/
 * (already shipped minified by upstream), and directories not explicitly
 * listed below.
 */

const fs = require('fs');
const path = require('path');
const { minify } = require('terser');

// --check verifies every .min.js matches its source without writing anything.
// Kept in this file so the check reuses the exact terser options below; a copy
// of that config in the verify harness would drift and false-report staleness.
const CHECK_ONLY = process.argv.includes('--check');

const SRC_DIR = path.resolve(__dirname, '..', 'assets', 'js');
// Each entry: directory absolute path, relative label for log output.
const SCAN_DIRS = [
	{ dir: SRC_DIR, label: '' },
	{ dir: path.join(SRC_DIR, 'system'), label: 'system/' },
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
	const stale = [];
	// theme-root-relative source path -> minified code, for the bundle phase.
	const minByRel = {};
	for (const { src, label } of sources) {
		const base = path.basename(src, '.js');
		const dest = path.join( path.dirname( src ), `${base}.min.js` );
		const code = fs.readFileSync(src, 'utf8');
		try {
			// No sourceMap — source maps would expose full unminified JS source on
			// production via the sourceMappingURL comment. Defenders should not have
			// to think about whether maps shipped or not; the safe default is off.
			const result = await minify(code, {
				// drop_console removes console.* calls from production output.
				// Source files keep debug logs for development; mins ship silent.
				compress: { passes: 2, drop_console: true },
				mangle: true,
				format: { comments: false },
			});
			minByRel[`assets/js/${label}${base}.js`] = result.code;
			if ( CHECK_ONLY ) {
				// Content comparison, not mtime — a git checkout or `touch`
				// reorders mtimes without changing bytes. terser is
				// deterministic for a given source + options, so a byte
				// mismatch means the .min really is out of date.
				if ( ! fs.existsSync( dest ) ) {
					stale.push(`${label}${base}.min.js — missing`);
				} else if ( fs.readFileSync( dest, 'utf8' ) !== result.code ) {
					stale.push(`${label}${base}.min.js — differs from source`);
				}
				built += 1;
				continue;
			}
			fs.writeFileSync(dest, result.code, 'utf8');
			built += 1;
			console.log(`  ✓ ${label}${base}.js → ${label}${base}.min.js  (${code.length} → ${result.code.length} bytes)`);
		} catch (err) {
			failed += 1;
			console.error(`  ✗ ${label}${base}.js — ${err.message}`);
		}
	}
	// Bundle phase: concatenate minified outputs per bundles.config.js, in
	// order, joined with '\n;' (the leading empty statement makes each part
	// concat-safe regardless of how the previous one ends). Fails closed on
	// any missing part.
	const bundles = require('./bundles.config.js').js;
	for ( const [ bundleRel, parts ] of Object.entries( bundles ) ) {
		const missing = parts.filter( ( p ) => ! ( p in minByRel ) );
		if ( missing.length > 0 ) {
			failed += 1;
			console.error(`  ✗ ${bundleRel} — missing part(s): ${missing.join(', ')}`);
			continue;
		}
		const content = parts.map( ( p ) => minByRel[ p ] ).join( '\n;' );
		const bundlePath = path.resolve( SRC_DIR, '..', '..', bundleRel );
		if ( CHECK_ONLY ) {
			if ( ! fs.existsSync( bundlePath ) ) {
				stale.push(`${bundleRel} — bundle missing`);
			} else if ( fs.readFileSync( bundlePath, 'utf8' ) !== content ) {
				stale.push(`${bundleRel} — bundle differs from fresh concat`);
			}
			continue;
		}
		fs.mkdirSync( path.dirname( bundlePath ), { recursive: true } );
		fs.writeFileSync( bundlePath, content, 'utf8' );
		console.log(`  ✓ bundle ${bundleRel}  (${parts.length} parts, ${content.length} bytes)`);
	}

	if ( CHECK_ONLY ) {
		if ( failed > 0 ) {
			console.error(`[build:js --check] ${failed} file(s) failed to minify`);
			process.exit(1);
		}
		if ( stale.length > 0 ) {
			console.error(`[build:js --check] ${stale.length} stale .min.js file(s):`);
			stale.forEach(s => console.error(`  ${s}`));
			console.error('[build:js --check] Run: npm run build:js');
			process.exit(1);
		}
		console.log(`[build:js --check] ${built} file(s) in sync with source.`);
		process.exit(0);
	}
	console.log(`\nDone: ${built} built, ${failed} failed.`);
	process.exit(failed === 0 ? 0 : 1);
}

main().catch((err) => {
	console.error(err);
	process.exit(1);
});
