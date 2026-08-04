import { readFileSync } from 'node:fs';

const manifestPath = new URL('../docs/theme-machine/manifest.json', import.meta.url);
const manifest = JSON.parse(readFileSync(manifestPath, 'utf8'));
const expectedLaneIds = [
  '01-primary-builder', '02-platform-doctrine', '03-luxury-direction',
  '04-storefront-composition', '05-immersive-storytelling', '06-elementor-authoring',
  '07-commerce-checkout', '08-catalog-integrity', '09-accessibility',
  '10-e2e-visual-qa', '11-security-review', '12-review-and-simplify',
  '13-release-and-recovery',
];

function assert(condition, message) {
  if (!condition) throw new Error(`Theme machine manifest invalid: ${message}`);
}

assert(manifest.schema_version === 1, 'schema_version must be 1');
assert(Array.isArray(manifest.lanes), 'lanes must be an array');
assert(manifest.lanes.length === expectedLaneIds.length, 'there must be exactly 13 lanes');
assert(manifest.lanes.map((lane) => lane.id).join('|') === expectedLaneIds.join('|'), 'lane IDs must be the ordered canonical set');
for (const lane of manifest.lanes) {
  assert(typeof lane.primary === 'string' && lane.primary.length > 0, `${lane.id} needs a primary`);
  assert(Array.isArray(lane.support) && lane.support.length > 0, `${lane.id} needs paired support`);
  assert(Array.isArray(lane.owns) && lane.owns.length > 0, `${lane.id} needs ownership`);
  assert(Array.isArray(lane.hands_off) && lane.hands_off.length > 0, `${lane.id} needs a handoff`);
}
const primaryBuilder = manifest.lanes[0];
const platformDoctrine = manifest.lanes[1];
assert(primaryBuilder.primary === 'fashion-theme-architect', 'fashion-theme-architect must be primary builder');
assert(primaryBuilder.support.includes('skyyrose-wp-platform'), 'primary builder must pair with skyyrose-wp-platform');
assert(platformDoctrine.primary === 'skyyrose-wp-platform', 'skyyrose-wp-platform must be mandatory doctrine');
console.log(`Theme machine manifest valid: ${manifest.lanes.length} lanes, core pair intact.`);
