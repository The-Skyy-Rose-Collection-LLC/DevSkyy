import { createHash, verify as verifySignature } from 'node:crypto';
import {
  closeSync,
  chmodSync,
  constants as fsConstants,
  existsSync,
  fstatSync,
  lstatSync,
  mkdtempSync,
  mkdirSync,
  openSync,
  readFileSync,
  realpathSync,
  statSync,
  symlinkSync,
  writeSync,
  writeFileSync,
  readSync,
  rmSync,
} from 'node:fs';
import { basename, dirname, isAbsolute, join, relative, resolve } from 'node:path';
import { spawnSync } from 'node:child_process';
import { tmpdir } from 'node:os';
import { fileURLToPath } from 'node:url';

const manifestPath = fileURLToPath(
  new URL('../docs/theme-machine/manifest.json', import.meta.url),
);
const expectedLaneIds = [
  '01-primary-builder',
  '02-platform-doctrine',
  '03-luxury-direction',
  '04-storefront-composition',
  '05-immersive-storytelling',
  '06-elementor-authoring',
  '07-commerce-checkout',
  '08-catalog-integrity',
  '09-accessibility',
  '10-e2e-visual-qa',
  '11-security-review',
  '12-review-and-simplify',
  '13-release-and-recovery',
];
const expectedGateIds = [
  'marketplace-policy',
  'licensing-attribution',
  'legal-ip-clearance',
  'collection-narrative-worlds',
  'privacy-data',
  'video-delivery-safety',
  'accessibility',
  'performance',
  'security',
  'updates-child-theme',
  'demo-import-onboarding',
  'sbom-dependencies',
  'reproducible-package',
  'compatibility',
  'handoff-support',
  'scroll-world-fallbacks',
  'commerce',
  'browser-e2e-quality',
];
const expectedProfileIds = [
  'internal-production',
  'wordpress-org',
  'themeforest',
];
const expectedApprovalDomains = [
  'creative',
  'brand',
  'commerce',
  'asset-licensing',
  'release',
  'material-product',
];
const sha256Pattern = /^[a-f0-9]{64}$/i;
const commitPattern = /^[a-f0-9]{40,64}$/i;
const maxReportBytes = 5 * 1024 * 1024;
const maxArtifactBytes = 2 * 1024 * 1024 * 1024;
const maxAggregateArtifactBytes = 3 * 1024 * 1024 * 1024;
const maxExtractedVideoBytes = 2 * 1024 * 1024 * 1024;

function fail(message) {
  throw new Error(`Theme machine validation failed: ${message}`);
}

function assert(condition, message) {
  if (!condition) fail(message);
}

function assertNonEmptyString(value, message) {
  assert(typeof value === 'string' && value.trim().length > 0, message);
}

function assertStringArray(value, message) {
  assert(
    Array.isArray(value) &&
      value.length > 0 &&
      value.every((item) => typeof item === 'string' && item.length > 0),
    message,
  );
}

function assertUniqueIds(records, label) {
  const ids = records.map((record) => record.id);
  assert(
    new Set(ids).size === ids.length,
    `${label} IDs must be unique (received ${ids.join(', ')})`,
  );
}

function assertSameMembers(actual, expected, message) {
  assert(
    actual.length === expected.length &&
      expected.every((item) => actual.includes(item)),
    message,
  );
}

function parseJson(path, label, maxBytes = maxReportBytes) {
  try {
    const size = statSync(path).size;
    assert(size <= maxBytes, `${label} exceeds ${maxBytes} bytes`);
    return JSON.parse(readFileSync(path, 'utf8'));
  } catch (error) {
    fail(`${label} is not readable JSON at ${path}: ${error.message}`);
  }
}

function sha256(value) {
  return createHash('sha256').update(value).digest('hex');
}

function canonicalize(value) {
  if (Array.isArray(value)) return `[${value.map(canonicalize).join(',')}]`;
  if (value && typeof value === 'object') {
    return `{${Object.keys(value)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${canonicalize(value[key])}`)
      .join(',')}}`;
  }
  return JSON.stringify(value);
}

function parseTimestamp(value, label) {
  assert(
    typeof value === 'string' &&
      /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$/.test(value),
    `${label} must be an ISO UTC timestamp`,
  );
  const timestamp = new Date(value).valueOf();
  assert(!Number.isNaN(timestamp), `${label} is invalid`);
  assert(timestamp <= Date.now() + 60_000, `${label} cannot be in the future`);
  return timestamp;
}

function assertFreshTimestamp(value, label, reportTimestamp, maxAgeDays) {
  const timestamp = parseTimestamp(value, label);
  assert(timestamp <= reportTimestamp, `${label} cannot postdate the report`);
  assert(
    reportTimestamp - timestamp <= maxAgeDays * 86_400_000,
    `${label} is stale`,
  );
  return timestamp;
}

function run(command, args, label, options = {}) {
  const result = spawnSync(command, args, {
    encoding: 'utf8',
    maxBuffer: 16 * 1024 * 1024,
    ...options,
  });
  assert(!result.error, `${label} could not run: ${result.error?.message}`);
  assert(
    result.status === 0,
    `${label} failed: ${(result.stderr || result.stdout || 'unknown error').trim()}`,
  );
  return result.stdout;
}

function ageInDays(dateString) {
  const reviewed = new Date(`${dateString}T00:00:00Z`);
  assert(!Number.isNaN(reviewed.valueOf()), `invalid review date ${dateString}`);
  return Math.floor((Date.now() - reviewed.valueOf()) / 86_400_000);
}

function validateDependencyGraph(lanes) {
  const laneIds = new Set(lanes.map((lane) => lane.id));
  const visiting = new Set();
  const visited = new Set();

  function visit(id) {
    if (visited.has(id)) return;
    assert(!visiting.has(id), `lane dependency cycle includes ${id}`);
    visiting.add(id);
    const lane = lanes.find((candidate) => candidate.id === id);
    for (const dependency of lane.depends_on) {
      assert(laneIds.has(dependency), `${id} depends on unknown lane ${dependency}`);
      visit(dependency);
    }
    visiting.delete(id);
    visited.add(id);
  }

  for (const lane of lanes) visit(lane.id);
}

function validateManifest(manifest) {
  assert(manifest.schema_version === 2, 'schema_version must be 2');
  assert(manifest.authority?.final_approver === 'user/founder', 'final approver must be user/founder');
  assertSameMembers(
    manifest.authority?.approval_domains ?? [],
    expectedApprovalDomains,
    'authority must reserve all canonical founder approval domains',
  );
  assert(
    manifest.authority?.approval_artifact === 'founder-approval-record',
    'authority must require the founder approval artifact',
  );
  assert(
    manifest.authority?.approval_verification?.method === 'ed25519' &&
      Array.isArray(manifest.authority.approval_verification.public_keys),
    'founder approvals must use configured Ed25519 verification',
  );
  assertNonEmptyString(
    manifest.authority.approval_verification.canonicalization,
    'founder approval verification needs canonicalization instructions',
  );
  for (const config of [
    manifest.authority.approval_verification,
    manifest.trust_roots?.build_attestation,
    manifest.trust_roots?.policy_attestation,
  ].filter(Boolean)) {
    const keyIds = config.public_keys.map((key) => key.id);
    assert(new Set(keyIds).size === keyIds.length, 'trusted public key IDs must be unique');
    for (const key of config.public_keys) {
      assertNonEmptyString(key.id, 'trusted public key needs id');
      assertNonEmptyString(key.public_key_pem, `${key.id} needs public_key_pem`);
    }
  }

  const requiredRequestFields = [
    'theme_path',
    'surface_or_outcome',
    'commerce_authority',
    'target_release_profiles',
    'distribution_model',
    'target_compatibility',
  ];
  assertSameMembers(
    manifest.request_contract?.required ?? [],
    requiredRequestFields,
    'request contract is incomplete',
  );
  assert(
    Array.isArray(manifest.brand_story_constraints),
    'brand_story_constraints must be an array',
  );
  assertUniqueIds(manifest.brand_story_constraints, 'brand story constraint');
  const storyConstraintById = new Map(
    manifest.brand_story_constraints.map((constraint) => [constraint.id, constraint]),
  );
  const blackRose = storyConstraintById.get('black-rose-beauty-and-depth');
  assert(blackRose, 'Black Rose beauty-and-depth constraint is required');
  assert(
    ['material', 'silhouette', 'reflection', 'contrast'].every((theme) =>
      blackRose.canonical_direction.toLowerCase().includes(theme)),
    'Black Rose dimensional-black direction is incomplete',
  );
  assertStringArray(blackRose.forbidden, 'Black Rose needs explicit anti-cliches');
  assert(
    ['goth', 'grief', 'black-as-absence'].every((term) =>
      blackRose.forbidden.some((item) => item.toLowerCase().includes(term)),
    ),
    'Black Rose must prohibit goth, grief, and black-as-absence cliches',
  );
  const loveHurts = storyConstraintById.get(
    'love-hurts-original-beast-perspective',
  );
  assert(loveHurts, 'Love Hurts original Beast-perspective constraint is required');
  assert(
    ['isolation', 'devotion', 'transformation', 'earned tenderness'].every(
      (theme) => loveHurts.canonical_direction.toLowerCase().includes(theme),
    ),
    'Love Hurts canonical themes are incomplete',
  );
  assertStringArray(loveHurts.forbidden, 'Love Hurts needs explicit IP prohibitions');
  assert(
    loveHurts.forbidden.length >= 8 &&
      loveHurts.forbidden.every((item) => item.toLowerCase().includes('disney')),
    'Love Hurts must explicitly prohibit every Disney-derived treatment',
  );
  assert(
    loveHurts.clearance_gate === 'legal-ip-clearance',
    'Love Hurts must require legal/IP clearance',
  );
  const kidsCapsule = storyConstraintById.get('kids-capsule-heir-to-throne');
  assert(kidsCapsule, 'Kids Capsule heir-to-throne constraint is required');
  assert(
    ['playful sovereignty', 'protection', 'possibility'].every((theme) =>
      kidsCapsule.canonical_direction.toLowerCase().includes(theme)),
    'Kids Capsule canonical themes are incomplete',
  );
  assertStringArray(kidsCapsule.forbidden, 'Kids Capsule needs explicit safeguards');
  assert(
    kidsCapsule.forbidden.some((item) => item.includes('adult')) &&
      kidsCapsule.forbidden.some((item) => item.includes('child profiling')) &&
      kidsCapsule.forbidden.some((item) => item.includes('another collection')),
    'Kids Capsule must prohibit adult reskins, child profiling, and collection leakage',
  );
  const signature = storyConstraintById.get(
    'signature-flagship-house-standard',
  );
  assert(signature, 'Signature Flagship house-standard constraint is required');
  assert(
    ['oakland confidence', 'craft', 'forward motion', 'city-tour', 'gold'].every(
      (theme) => signature.canonical_direction.toLowerCase().includes(theme),
    ),
    'Signature Flagship direction is incomplete',
  );
  assertStringArray(signature.forbidden, 'Signature needs explicit anti-drift rules');
  assert(
    signature.forbidden.some((item) => item.includes('neutral')) &&
      signature.forbidden.some((item) => item.includes('collage')) &&
      signature.forbidden.some((item) => item.includes('city-tour')) &&
      signature.forbidden.some((item) => item.includes('gold')),
    'Signature must reject neutral defaults and collection collage while preserving city-tour and gold',
  );
  assertSameMembers(
    manifest.evidence_policy?.gate_statuses ?? [],
    ['pass', 'fail', 'blocked', 'not_applicable'],
    'gate statuses must use the canonical evidence states',
  );
  assert(
    Number.isInteger(manifest.evidence_policy?.policy_refresh_days) &&
      manifest.evidence_policy.policy_refresh_days > 0,
    'policy_refresh_days must be a positive integer',
  );
  assert(
    Number.isInteger(manifest.evidence_policy?.evidence_refresh_days) &&
      manifest.evidence_policy.evidence_refresh_days > 0,
    'evidence_refresh_days must be a positive integer',
  );
  for (const trustRoot of ['build_attestation', 'policy_attestation']) {
    const config = manifest.trust_roots?.[trustRoot];
    assert(
      config?.method === 'ed25519' && Array.isArray(config.public_keys),
      `${trustRoot} must use configured Ed25519 trust roots`,
    );
    assertNonEmptyString(config.rule, `${trustRoot} needs a fail-closed rule`);
    assertNonEmptyString(
      config.canonicalization,
      `${trustRoot} needs canonicalization instructions`,
    );
  }

  assert(Array.isArray(manifest.lanes), 'lanes must be an array');
  assert(
    manifest.lanes.map((lane) => lane.id).join('|') ===
      expectedLaneIds.join('|'),
    'lane IDs must be the ordered canonical set',
  );
  assertUniqueIds(manifest.lanes, 'lane');
  for (const lane of manifest.lanes) {
    assertNonEmptyString(lane.primary, `${lane.id} needs a primary`);
    assertStringArray(lane.support, `${lane.id} needs paired support`);
    assertStringArray(lane.owns, `${lane.id} needs ownership`);
    assertStringArray(lane.hands_off, `${lane.id} needs a handoff`);
    assert(Array.isArray(lane.depends_on), `${lane.id} needs dependencies`);
  }
  validateDependencyGraph(manifest.lanes);
  const primaryBuilder = manifest.lanes[0];
  const platformDoctrine = manifest.lanes[1];
  assert(
    primaryBuilder.primary === 'fashion-theme-architect',
    'fashion-theme-architect must be primary builder',
  );
  assert(
    primaryBuilder.support.includes('skyyrose-wp-platform'),
    'primary builder must pair with skyyrose-wp-platform',
  );
  assert(
    platformDoctrine.primary === 'skyyrose-wp-platform',
    'skyyrose-wp-platform must be mandatory doctrine',
  );

  assert(Array.isArray(manifest.artifact_contract), 'artifact contract must be an array');
  assertUniqueIds(manifest.artifact_contract, 'artifact');
  const artifactIds = new Set(manifest.artifact_contract.map((artifact) => artifact.id));
  for (const artifact of manifest.artifact_contract) {
    assertNonEmptyString(artifact.format, `${artifact.id} needs a format`);
    assertNonEmptyString(artifact.description, `${artifact.id} needs a description`);
  }
  const semanticValidators = new Map(
    manifest.artifact_contract
      .filter((artifact) => artifact.semantic_validation)
      .map((artifact) => [artifact.id, artifact.semantic_validation]),
  );
  const requiredSemanticValidators = {
    'marketplace-policy-audit': 'marketplace-policy-v1',
    'video-delivery-audit': 'video-audit-v1',
    'scroll-fallback-report': 'scroll-fallback-v1',
    sbom: 'cyclonedx-v1',
    'build-provenance': 'reproducible-build-v1',
    'candidate-package': 'wordpress-theme-zip-v1',
    'package-checksums': 'sha256-list-v1',
    'compatibility-matrix': 'compatibility-matrix-v1',
    'founder-approval-record': 'founder-approval-v1',
  };
  for (const [artifactId, validatorId] of Object.entries(requiredSemanticValidators)) {
    assert(
      semanticValidators.get(artifactId) === validatorId,
      `${artifactId} must use ${validatorId} semantic validation`,
    );
  }
  assert(artifactIds.has('candidate-package'), 'artifact contract needs candidate-package');
  assert(artifactIds.has('founder-approval-record'), 'artifact contract needs founder-approval-record');
  assert(artifactIds.has('video-delivery-audit'), 'artifact contract needs video-delivery-audit');

  assert(Array.isArray(manifest.quality_gates), 'quality_gates must be an array');
  assertUniqueIds(manifest.quality_gates, 'quality gate');
  assert(
    manifest.quality_gates.map((gate) => gate.id).join('|') ===
      expectedGateIds.join('|'),
    'quality gates must be the ordered canonical set',
  );
  const laneIds = new Set(expectedLaneIds);
  for (const gate of manifest.quality_gates) {
    assert(laneIds.has(gate.owner_lane), `${gate.id} has unknown owner lane`);
    assertStringArray(gate.required_artifacts, `${gate.id} needs required artifacts`);
    assert(
      gate.required_artifacts.every((id) => artifactIds.has(id)),
      `${gate.id} references an unknown artifact`,
    );
    assert(
      Array.isArray(gate.criteria) &&
        gate.criteria.length >= 3 &&
        gate.criteria.every((criterion) =>
          typeof criterion === 'string' && criterion.trim().length > 0),
      `${gate.id} needs at least three evidence criteria`,
    );
  }

  assert(
    Array.isArray(manifest.authoritative_references),
    'authoritative_references must be an array',
  );
  assertUniqueIds(manifest.authoritative_references, 'reference');
  const referenceIds = new Set(
    manifest.authoritative_references.map((reference) => reference.id),
  );
  for (const reference of manifest.authoritative_references) {
    assert(
      ['wordpress-org', 'themeforest'].includes(reference.release_profile),
      `${reference.id} has unsupported release profile`,
    );
    assert(
      typeof reference.url === 'string' && reference.url.startsWith('https://'),
      `${reference.id} must use an HTTPS authoritative URL`,
    );
    assert(
      /^\d{4}-\d{2}-\d{2}$/.test(reference.reviewed_on),
      `${reference.id} needs an ISO reviewed_on date`,
    );
    assertNonEmptyString(reference.purpose, `${reference.id} needs a purpose`);
    assertStringArray(
      reference.required_sections,
      `${reference.id} needs canonical required_sections`,
    );
  }

  assert(Array.isArray(manifest.release_profiles), 'release_profiles must be an array');
  assertUniqueIds(manifest.release_profiles, 'release profile');
  assert(
    manifest.release_profiles.map((profile) => profile.id).join('|') ===
      expectedProfileIds.join('|'),
    'release profiles must be the ordered canonical set',
  );
  const gateIds = new Set(expectedGateIds);
  for (const profile of manifest.release_profiles) {
    const canonicalProfileGates = expectedGateIds.filter(
      (id) => id !== 'marketplace-policy' || profile.id !== 'internal-production',
    );
    assertSameMembers(
      profile.required_gates,
      canonicalProfileGates,
      `${profile.id} must require every applicable canonical gate`,
    );
    assert(
      profile.required_gates.every((id) => gateIds.has(id)),
      `${profile.id} references an unknown gate`,
    );
    assertSameMembers(
      profile.required_approvals,
      expectedApprovalDomains,
      `${profile.id} must reserve every founder approval domain`,
    );
    assert(Array.isArray(profile.policy_references), `${profile.id} needs policy references`);
    assert(
      profile.policy_references.every((id) => referenceIds.has(id)),
      `${profile.id} references unknown policy evidence`,
    );
    assert(
      profile.policy_references.every(
        (id) =>
          manifest.authoritative_references.find(
            (reference) => reference.id === id,
          ).release_profile === profile.id,
      ),
      `${profile.id} contains a policy reference owned by another profile`,
    );
    if (profile.id !== 'internal-production') {
      assert(
        profile.required_gates.includes('marketplace-policy'),
        `${profile.id} must require marketplace policy`,
      );
      assert(
        profile.policy_references.length > 0,
        `${profile.id} must cite current official policy`,
      );
    }
  }

  const reportContract = manifest.candidate_report_contract;
  for (const key of [
    'required',
    'candidate_required',
    'artifact_required',
    'gate_required',
    'criterion_required',
    'approval_required',
  ]) {
    assertStringArray(reportContract?.[key], `candidate report needs ${key}`);
  }

  return {
    artifactIds,
    gateById: new Map(manifest.quality_gates.map((gate) => [gate.id, gate])),
    profileById: new Map(
      manifest.release_profiles.map((profile) => [profile.id, profile]),
    ),
    referenceById: new Map(
      manifest.authoritative_references.map((reference) => [reference.id, reference]),
    ),
    semanticValidators,
  };
}

function assertRequiredFields(record, fields, label) {
  for (const field of fields) {
    assert(
      Object.hasOwn(record, field),
      `${label} is missing required field ${field}`,
    );
  }
}

function validateFreshReferences(manifest, model, profile) {
  for (const referenceId of profile.policy_references) {
    const reference = model.referenceById.get(referenceId);
    const age = ageInDays(reference.reviewed_on);
    assert(
      age >= 0,
      `${referenceId} reviewed_on cannot be in the future`,
    );
    assert(
      age <= manifest.evidence_policy.policy_refresh_days,
      `${referenceId} is stale at ${age} days; refresh official policy before release review`,
    );
  }
}

function validateSourceCandidate(candidate) {
  const themePath = realpathSync(resolve(candidate.theme_path));
  assert(statSync(themePath).isDirectory(), 'candidate theme_path must be a directory');
  const repositoryRoot = realpathSync(
    run('git', ['-C', themePath, 'rev-parse', '--show-toplevel'], 'resolve source repository').trim(),
  );
  const themeRelative = relative(repositoryRoot, themePath);
  assert(
    themeRelative !== '..' && !themeRelative.startsWith('../'),
    'candidate theme_path must be inside its source repository',
  );
  const resolvedCommit = run(
    'git',
    ['-C', repositoryRoot, 'rev-parse', '--verify', `${candidate.commit}^{commit}`],
    'resolve candidate commit',
  ).trim();
  assert(
    resolvedCommit.toLowerCase() === candidate.commit.toLowerCase(),
    'candidate commit must be the full resolved Git commit',
  );
  const headCommit = run(
    'git',
    ['-C', repositoryRoot, 'rev-parse', 'HEAD'],
    'resolve source HEAD',
  ).trim();
  assert(
    headCommit.toLowerCase() === candidate.commit.toLowerCase(),
    'source worktree HEAD must equal the candidate commit',
  );
  const status = run(
    'git',
    [
      '-C',
      repositoryRoot,
      'status',
      '--porcelain=v1',
      '--untracked-files=all',
    ],
    'check candidate source cleanliness',
  ).trim();
  assert(status.length === 0, 'candidate source repository must be clean at its commit');
  const sourceTree = run(
    'git',
    ['-C', repositoryRoot, 'rev-parse', `${candidate.commit}^{tree}`],
    'resolve candidate source tree',
  ).trim();
  return {
    repositoryRoot,
    sourceTree,
    themePath,
    themeRootName: basename(themePath),
  };
}

function artifactJson(artifact, label) {
  return parseJson(artifact.realPath, label, Math.min(maxArtifactBytes, 25 * 1024 * 1024));
}

function inspectZipMetadata(zipPath) {
  const script = [
    'import json, stat, sys, zipfile',
    'with zipfile.ZipFile(sys.argv[1]) as z:',
    ' print(json.dumps([{"name": i.filename, "size": i.file_size, "compressed": i.compress_size, "encrypted": bool(i.flag_bits & 1), "mode": (i.external_attr >> 16) & 0xffff, "symlink": stat.S_ISLNK((i.external_attr >> 16) & 0xffff), "special": bool(stat.S_IFMT((i.external_attr >> 16) & 0xffff) not in (0, stat.S_IFREG) and not i.is_dir()), "directory": i.is_dir()} for i in z.infolist()]))',
  ].join('\n');
  return JSON.parse(
    run('python3', ['-c', script, zipPath], 'inspect ZIP central directory'),
  );
}

function hashPathSync(path) {
  const fd = openSync(path, fsConstants.O_RDONLY | fsConstants.O_NOFOLLOW);
  const hash = createHash('sha256');
  const buffer = Buffer.allocUnsafe(1024 * 1024);
  try {
    let bytesRead;
    do {
      bytesRead = readSync(fd, buffer, 0, buffer.length, null);
      if (bytesRead > 0) hash.update(buffer.subarray(0, bytesRead));
    } while (bytesRead > 0);
  } finally {
    closeSync(fd);
  }
  return hash.digest('hex');
}

function extractZipEntry(zipPath, entry, outputPath) {
  const script = [
    'import shutil, sys, zipfile',
    'with zipfile.ZipFile(sys.argv[1]) as z:',
    ' with z.open(sys.argv[2]) as src, open(sys.argv[3], "xb") as dst:',
    '  shutil.copyfileobj(src, dst, length=1024 * 1024)',
  ].join('\n');
  run('python3', ['-c', script, zipPath, entry, outputPath], `extract ${entry}`);
  chmodSync(outputPath, 0o400);
}

function validateCandidateZip(artifact, candidate, source, selectedProfiles) {
  assert(artifact.path.toLowerCase().endsWith('.zip'), 'candidate-package must be a .zip');
  const metadata = inspectZipMetadata(artifact.realPath);
  const entries = metadata.map((entry) => entry.name);
  assert(entries.length > 0, 'candidate package is empty');
  assert(entries.length <= 10_000, 'candidate package exceeds 10,000 entries');
  assert(new Set(entries).size === entries.length, 'candidate package has duplicate entries');
  const normalizedNames = entries.map((entry) => entry.normalize('NFC').toLowerCase());
  assert(
    new Set(normalizedNames).size === normalizedNames.length,
    'candidate package has case-folding or Unicode-normalization collisions',
  );
  const rootPrefix = `${source.themeRootName}/`;
  let totalUncompressed = 0;
  for (const entryMetadata of metadata) {
    const entry = entryMetadata.name;
    const pathComponents = entry.split('/');
    const contentComponents = entryMetadata.directory
      ? pathComponents.slice(0, -1)
      : pathComponents;
    assert(
      !entry.includes('\\') &&
        !entry.includes('\0') &&
        !entry.startsWith('/') &&
        contentComponents.every(
          (component) =>
            component.length > 0 && component !== '.' && component !== '..',
        ) &&
        entry.startsWith(rootPrefix),
      `candidate package has unsafe or unexpected entry ${entry}`,
    );
    assert(!entryMetadata.encrypted, `candidate package contains encrypted entry ${entry}`);
    assert(!entryMetadata.symlink, `candidate package contains symlink entry ${entry}`);
    assert(!entryMetadata.special, `candidate package contains special-file entry ${entry}`);
    assert(
      entryMetadata.directory || entryMetadata.size <= 512 * 1024 * 1024,
      `candidate package entry exceeds 512 MiB: ${entry}`,
    );
    totalUncompressed += entryMetadata.size;
    assert(
      entryMetadata.size === 0 ||
        entryMetadata.compressed > 0 &&
          entryMetadata.size / entryMetadata.compressed <= 5_000,
      `candidate package has unsafe compression ratio: ${entry}`,
    );
    assert(
      !/(^|\/)(?:\.git|node_modules|tests?|__MACOSX|\.DS_Store|\.env(?:\..*)?)(?:\/|$)|\.map$/i.test(entry),
      `candidate package contains development-only entry ${entry}`,
    );
  }
  assert(
    totalUncompressed <= 2 * 1024 * 1024 * 1024,
    'candidate package expands beyond 2 GiB',
  );
  assert(entries.includes(`${rootPrefix}style.css`), 'candidate package needs style.css');
  assert(
    entries.includes(`${rootPrefix}index.php`) ||
      entries.includes(`${rootPrefix}templates/index.html`),
    'candidate package needs index.php or templates/index.html',
  );
  if (selectedProfiles.some((profile) => profile.id === 'wordpress-org')) {
    assert(entries.includes(`${rootPrefix}readme.txt`), 'WordPress.org package needs readme.txt');
  }
  const styleCss = run(
    'unzip',
    ['-p', artifact.realPath, `${rootPrefix}style.css`],
    'read packaged style.css',
    { maxBuffer: 2 * 1024 * 1024 },
  );
  const version = styleCss.match(/^\s*Version:\s*(.+?)\s*$/im)?.[1];
  assert(version === candidate.version, 'packaged style.css version does not match report');
  assert(/^\s*Theme Name:\s*\S.+$/im.test(styleCss), 'packaged style.css needs Theme Name');
  assert(/^\s*Text Domain:\s*\S.+$/im.test(styleCss), 'packaged style.css needs Text Domain');
  return {
    entries,
    metadata,
    videoEntries: metadata
      .filter(
        (entry) =>
          !entry.directory &&
          /\.(?:3gp|avi|flv|m4v|mkv|mov|mp4|mpeg|mpg|ogv|ogg|webm)$/i.test(
            entry.name,
          ),
      )
      .map((entry) => entry.name),
  };
}

function validateSbom(artifact, generatedAt, refreshDays) {
  const sbom = artifactJson(artifact, 'CycloneDX SBOM');
  assert(sbom.bomFormat === 'CycloneDX', 'SBOM bomFormat must be CycloneDX');
  assertNonEmptyString(sbom.specVersion, 'SBOM needs specVersion');
  assert(Number.isInteger(sbom.version) && sbom.version > 0, 'SBOM needs a positive version');
  assertNonEmptyString(sbom.metadata?.component?.name, 'SBOM needs metadata.component.name');
  assertFreshTimestamp(
    sbom.metadata?.timestamp,
    'SBOM metadata.timestamp',
    generatedAt,
    refreshDays,
  );
  assert(Array.isArray(sbom.components), 'SBOM components must be an array');
}

function validateVideoAudit(
  artifact,
  generatedAt,
  refreshDays,
  packageArtifact,
  packageMetadata,
  snapshotRoot,
  source,
) {
  const audit = artifactJson(artifact, 'video delivery audit');
  assert(audit.schema_version === 1, 'video audit schema_version must be 1');
  assert(audit.inventory_complete === true, 'video inventory must be explicitly complete');
  assertFreshTimestamp(audit.generated_at, 'video audit generated_at', generatedAt, refreshDays);
  assert(Array.isArray(audit.videos), 'video audit needs a videos array');
  assertSameMembers(
    audit.videos.map((video) => video.package_path),
    packageMetadata.videoEntries,
    'video audit must exactly match packaged delivery videos',
  );
  const extractedVideoBytes = packageMetadata.metadata
    .filter((entry) => packageMetadata.videoEntries.includes(entry.name))
    .reduce((total, entry) => total + entry.size, 0);
  assert(
    extractedVideoBytes <= maxExtractedVideoBytes,
    'packaged video extraction exceeds the 2 GiB staging limit',
  );
  const videoStage = join(snapshotRoot, 'videos');
  mkdirSync(videoStage, { mode: 0o700 });
  for (const [index, video] of audit.videos.entries()) {
    const label = `video audit item ${index + 1}`;
    assert(sha256Pattern.test(video.source_sha256), `${label} needs source_sha256`);
    assert(sha256Pattern.test(video.derivative_sha256), `${label} needs derivative_sha256`);
    assert(video.source_sha256 !== video.derivative_sha256, `${label} source and derivative must differ`);
    assert(video.source_master_outside_repository === true, `${label} master must be outside repository`);
    assertNonEmptyString(video.source_master_reference, `${label} needs source master reference`);
    assert(isAbsolute(video.source_master_reference), `${label} source master reference must be absolute`);
    const masterPath = resolve(video.source_master_reference);
    const masterRelative = relative(source.repositoryRoot, masterPath);
    assert(
      masterRelative === '..' || masterRelative.startsWith('../'),
      `${label} source master must resolve outside the repository`,
    );
    assert(existsSync(masterPath), `${label} source master does not exist`);
    assert(statSync(masterPath).isFile(), `${label} source master must be a file`);
    assert(
      statSync(masterPath).size <= maxArtifactBytes,
      `${label} source master exceeds the verification size limit`,
    );
    assert(
      hashPathSync(masterPath) === video.source_sha256.toLowerCase(),
      `${label} source hash does not match preserved master`,
    );
    assertNonEmptyString(video.transformation_command, `${label} needs transformation_command`);
    assertNonEmptyString(video.toolchain, `${label} needs toolchain`);
    assertNonEmptyString(video.license_provenance, `${label} needs license provenance`);
    assert(video.ffprobe?.audio_stream_count === 0, `${label} must prove zero audio streams`);
    assertNonEmptyString(video.ffprobe?.output, `${label} needs ffprobe output`);
    const extractedPath = join(videoStage, `${index}.video`);
    extractZipEntry(
      packageArtifact.realPath,
      video.package_path,
      extractedPath,
    );
    assert(
      hashPathSync(extractedPath) === video.derivative_sha256.toLowerCase(),
      `${label} derivative hash does not match packaged video`,
    );
    const probe = JSON.parse(
      run(
        'ffprobe',
        [
          '-v', 'error', '-select_streams', 'a', '-show_entries', 'stream=index',
          '-of', 'json', extractedPath,
        ],
        `${label} ffprobe`,
      ),
    );
    assert(
      Array.isArray(probe.streams) && probe.streams.length === 0,
      `${label} packaged derivative contains an audio stream`,
    );
    let submittedProbe;
    try {
      submittedProbe = JSON.parse(video.ffprobe.output);
    } catch {
      fail(`${label} stored ffprobe output must be JSON`);
    }
    assert(
      canonicalize(submittedProbe) === canonicalize(probe),
      `${label} stored ffprobe output does not match independent probe`,
    );
  }
}

function validateScrollFallbackAudit(
  artifact,
  artifactById,
  generatedAt,
  refreshDays,
) {
  const audit = artifactJson(artifact, 'scroll fallback audit');
  assert(audit.schema_version === 1, 'scroll fallback schema_version must be 1');
  assert(audit.inventory_complete === true, 'scroll-world inventory must be explicitly complete');
  assertFreshTimestamp(
    audit.generated_at,
    'scroll fallback generated_at',
    generatedAt,
    refreshDays,
  );
  assert(Array.isArray(audit.surfaces), 'scroll fallback audit needs a surfaces array');
  const requiredModes = [
    'no-javascript',
    'reduced-motion',
    'webgl-unavailable',
    'webgl-context-loss',
    'low-power',
    'asset-failure',
    'keyboard',
    'touch',
    'narrow-viewport',
  ];
  for (const [index, surface] of audit.surfaces.entries()) {
    const label = `scroll surface ${index + 1}`;
    assertNonEmptyString(surface.id, `${label} needs id`);
    assertSameMembers(surface.tested_modes ?? [], requiredModes, `${label} fallback modes are incomplete`);
    assert(surface.essential_story_preserved === true, `${label} must preserve essential story`);
    assert(surface.commerce_path_preserved === true, `${label} must preserve commerce path`);
    assert(surface.no_scroll_trap === true, `${label} must prove no scroll trap`);
    assertStringArray(surface.evidence_artifacts, `${label} needs evidence artifacts`);
    assert(
      surface.evidence_artifacts.every((id) => artifactById.has(id)),
      `${label} references an absent evidence artifact`,
    );
  }
}

function validateBuildProvenance(
  artifact,
  report,
  packageArtifact,
  generatedAt,
  refreshDays,
  source,
  trustConfig,
) {
  const envelope = artifactJson(artifact, 'build provenance');
  const provenance = validateTrustedEnvelope(
    envelope,
    trustConfig,
    'build attestation',
  );
  assert(provenance.schema_version === 1, 'build provenance payload schema_version must be 1');
  assert(provenance.repository_clean === true, 'build provenance must record a clean repository');
  assert(provenance.candidate_commit === report.candidate.commit, 'build provenance commit mismatch');
  assert(provenance.source_tree === source.sourceTree, 'build provenance source-tree mismatch');
  assert(provenance.theme_version === report.candidate.version, 'build provenance version mismatch');
  assert(provenance.manifest_sha256 === report.manifest_sha256, 'build provenance manifest mismatch');
  assert(provenance.package_sha256 === packageArtifact.digest, 'build provenance package mismatch');
  assertNonEmptyString(provenance.build_command, 'build provenance needs build_command');
  assert(
    provenance.toolchain &&
      typeof provenance.toolchain === 'object' &&
      Object.keys(provenance.toolchain).length > 0,
    'build provenance needs locked toolchain versions',
  );
  assert(Array.isArray(provenance.lockfiles), 'build provenance needs a lockfiles array');
  assert(
    Array.isArray(provenance.builds) && provenance.builds.length === 2,
    'build provenance needs exactly two clean builds',
  );
  assert(
    provenance.builds.every(
      (build) =>
        build.clean === true &&
        build.sha256 === packageArtifact.digest &&
        typeof build.completed_at === 'string',
    ),
    'both clean builds must match the candidate package digest',
  );
  for (const [index, build] of provenance.builds.entries()) {
    assertFreshTimestamp(
      build.completed_at,
      `build ${index + 1} completed_at`,
      generatedAt,
      refreshDays,
    );
  }
  assert(provenance.byte_identical === true, 'build provenance must confirm byte-identical archives');
  assert(provenance.zip_matches_source === true, 'trusted build must attest ZIP-to-source equality');
  assert(
    provenance.package_safety?.symlinks_rejected === true &&
      provenance.package_safety?.encryption_rejected === true &&
      provenance.package_safety?.expansion_limits_enforced === true,
    'trusted build must attest safe package inspection',
  );
}

function validateChecksums(artifact, packageArtifact) {
  assert(artifact.size <= 1024 * 1024, 'package checksum file exceeds 1 MiB');
  const lines = readFileSync(artifact.realPath, 'utf8').split(/\r?\n/).filter(Boolean);
  assert(lines.length > 0, 'package checksum file is empty');
  const parsed = lines.map((line) => line.match(/^([a-f0-9]{64})\s+\*?(.+)$/i));
  assert(parsed.every(Boolean), 'package checksum file has an invalid line');
  assert(
    parsed.some(
      (match) =>
        match[1].toLowerCase() === packageArtifact.digest.toLowerCase() &&
        basename(match[2]) === basename(packageArtifact.path),
    ),
    'package checksum file does not bind the candidate package',
  );
}

function validateFounderApproval(artifact, report, packageArtifact, manifest) {
  const record = artifactJson(artifact, 'founder approval record');
  assert(record.schema_version === 1, 'founder approval schema_version must be 1');
  assert(record.payload && typeof record.payload === 'object', 'founder approval needs payload');
  assertNonEmptyString(record.key_id, 'founder approval needs key_id');
  assertNonEmptyString(record.signature, 'founder approval needs signature');
  const keys = manifest.authority.approval_verification.public_keys;
  assert(
    keys.length > 0,
    'release authorization is blocked: no founder Ed25519 public key is configured',
  );
  const key = keys.find((candidate) => candidate.id === record.key_id);
  assert(key, `founder approval uses unknown key ${record.key_id}`);
  assertNonEmptyString(key.public_key_pem, `${record.key_id} needs public_key_pem`);
  const payload = record.payload;
  assert(payload.manifest_sha256 === report.manifest_sha256, 'approval manifest binding mismatch');
  assert(payload.candidate_commit === report.candidate.commit, 'approval commit binding mismatch');
  assert(payload.candidate_package_sha256 === packageArtifact.digest, 'approval package binding mismatch');
  assert(
    payload.evidence_root_sha256 === report.evidence_root_sha256,
    'approval evidence-root binding mismatch',
  );
  assertSameMembers(
    payload.target_release_profiles ?? [],
    report.target_release_profiles,
    'approval release profiles do not match report',
  );
  const issuedAt = parseTimestamp(payload.issued_at, 'approval issued_at');
  const expiresAt = new Date(payload.expires_at).valueOf();
  assert(!Number.isNaN(expiresAt), 'approval expires_at is invalid');
  assert(expiresAt > Date.now(), 'founder approval has expired');
  assert(expiresAt > issuedAt, 'founder approval expiry must follow issue time');
  assert(expiresAt - issuedAt <= 30 * 86_400_000, 'founder approval may be valid for at most 30 days');
  assert(
    canonicalize(payload.approvals) === canonicalize(report.approvals),
    'signed founder approvals do not match report approvals',
  );
  let signature;
  try {
    signature = Buffer.from(record.signature, 'base64');
  } catch {
    fail('founder approval signature must be base64');
  }
  assert(signature.length === 64, 'founder Ed25519 signature must be 64 bytes');
  assert(
    verifySignature(
      null,
      Buffer.from(canonicalize(payload)),
      key.public_key_pem,
      signature,
    ),
    'founder approval signature is invalid',
  );
}

function computeEvidenceRoot(report, artifactById) {
  const artifacts = report.artifacts
    .filter((artifact) => artifact.id !== 'founder-approval-record')
    .map((artifact) => {
      const verified = artifactById.get(artifact.id);
      return {
        id: artifact.id,
        path: artifact.path,
        sha256: verified.digest,
        size: verified.size,
      };
    });
  return sha256(
    canonicalize({
      manifest_schema_version: report.manifest_schema_version,
      manifest_sha256: report.manifest_sha256,
      phase: 'evidence-review',
      candidate: report.candidate,
      target_release_profiles: report.target_release_profiles,
      generated_at: report.generated_at,
      gates: report.gates,
      artifacts,
    }),
  );
}

function validateTrustedEnvelope(record, trustConfig, label) {
  assert(record.schema_version === 1, `${label} envelope schema_version must be 1`);
  assert(record.payload && typeof record.payload === 'object', `${label} needs payload`);
  assertNonEmptyString(record.key_id, `${label} needs key_id`);
  assertNonEmptyString(record.signature, `${label} needs signature`);
  assert(
    trustConfig.public_keys.length > 0,
    `${label} validation is blocked: no trusted Ed25519 public key is configured`,
  );
  const key = trustConfig.public_keys.find((candidate) => candidate.id === record.key_id);
  assert(key, `${label} uses unknown key ${record.key_id}`);
  assertNonEmptyString(key.public_key_pem, `${record.key_id} needs public_key_pem`);
  const signature = Buffer.from(record.signature, 'base64');
  assert(signature.length === 64, `${label} Ed25519 signature must be 64 bytes`);
  assert(
    verifySignature(
      null,
      Buffer.from(canonicalize(record.payload)),
      key.public_key_pem,
      signature,
    ),
    `${label} signature is invalid`,
  );
  return record.payload;
}

function validateCompatibilityMatrix(
  artifact,
  artifactById,
  generatedAt,
  refreshDays,
) {
  const matrix = artifactJson(artifact, 'compatibility matrix');
  assert(matrix.schema_version === 1, 'compatibility matrix schema_version must be 1');
  const requiredAxes = [
    'wordpress', 'php', 'woocommerce', 'browser', 'viewport', 'editor',
    'multisite', 'rtl', 'locale', 'plugins',
  ];
  assertSameMembers(matrix.axes ?? [], requiredAxes, 'compatibility matrix axes are incomplete');
  assert(Array.isArray(matrix.rows) && matrix.rows.length > 0, 'compatibility matrix needs rows');
  assertUniqueIds(matrix.rows, 'compatibility row');
  for (const [index, row] of matrix.rows.entries()) {
    assert(['pass', 'unsupported'].includes(row.status), `compatibility row ${index + 1} has invalid status`);
    assertNonEmptyString(row.environment, `compatibility row ${index + 1} needs environment`);
    assert(
      row.values &&
        typeof row.values === 'object' &&
        requiredAxes.every(
          (axis) =>
            typeof row.values[axis] === 'string' &&
            row.values[axis].trim().length > 0,
        ),
      `compatibility row ${index + 1} needs exact values for every axis`,
    );
    assert(
      ['minimum', 'latest-stable', 'maximum-advertised', 'additional'].includes(
        row.coverage,
      ),
      `compatibility row ${index + 1} has invalid coverage`,
    );
    assertStringArray(row.evidence_artifacts, `compatibility row ${index + 1} needs evidence`);
    assert(
      row.evidence_artifacts.every((id) => artifactById.has(id)),
      `compatibility row ${index + 1} references an absent artifact`,
    );
    assertFreshTimestamp(
      row.observed_at,
      `compatibility row ${index + 1} observed_at`,
      generatedAt,
      refreshDays,
    );
  }
  for (const coverage of ['minimum', 'latest-stable', 'maximum-advertised']) {
    assert(
      matrix.rows.some(
        (row) => row.coverage === coverage && row.status === 'pass',
      ),
      `compatibility matrix needs a passing ${coverage} row`,
    );
  }
  assertStringArray(
    matrix.advertised_row_ids,
    'compatibility matrix needs advertised_row_ids',
  );
  assert(
    matrix.advertised_row_ids.every((id) =>
      matrix.rows.some((row) => row.id === id && row.status === 'pass'),
    ),
    'every advertised compatibility row must pass',
  );
}

function validateMarketplacePolicy(
  artifact,
  selectedProfiles,
  manifest,
  model,
  generatedAt,
  trustConfig,
) {
  const envelope = artifactJson(artifact, 'marketplace policy audit');
  const audit = validateTrustedEnvelope(
    envelope,
    trustConfig,
    'policy attestation',
  );
  assert(audit.schema_version === 1, 'policy attestation payload schema_version must be 1');
  assert(Array.isArray(audit.profiles), 'marketplace policy audit needs profiles');
  for (const profile of selectedProfiles.filter((item) => item.policy_references.length > 0)) {
    const profileAudit = audit.profiles.find((item) => item.id === profile.id);
    assert(profileAudit, `marketplace policy audit is missing ${profile.id}`);
    assert(profileAudit.coverage_complete === true, `${profile.id} policy coverage must be complete`);
    assert(profileAudit.reviewer?.role === 'human', `${profile.id} policy audit needs a human reviewer`);
    assertNonEmptyString(profileAudit.reviewer?.name, `${profile.id} policy audit needs reviewer name`);
    const expectedRequirementIds = [
      ...new Set(
        profile.policy_references.flatMap(
          (referenceId) => model.referenceById.get(referenceId).required_sections,
        ),
      ),
    ];
    assertSameMembers(
      profileAudit.requirement_ids ?? [],
      expectedRequirementIds,
      `${profile.id} policy audit must cover canonical requirement IDs`,
    );
    assert(Array.isArray(profileAudit.sources), `${profile.id} policy audit needs sources`);
    assertSameMembers(
      profileAudit.sources.map((source) => source.reference_id),
      profile.policy_references,
      `${profile.id} policy snapshots must cover every canonical reference`,
    );
    for (const source of profileAudit.sources) {
      const reference = model.referenceById.get(source.reference_id);
      assert(source.url === reference.url, `${source.reference_id} URL does not match manifest`);
      assert(sha256Pattern.test(source.content_sha256), `${source.reference_id} needs content SHA-256`);
      assertNonEmptyString(source.content, `${source.reference_id} needs a captured policy snapshot`);
      assert(
        sha256(source.content) === source.content_sha256.toLowerCase(),
        `${source.reference_id} snapshot digest mismatch`,
      );
      assertNonEmptyString(
        source.revision_or_etag,
        `${source.reference_id} needs revision_or_etag`,
      );
      const retrievedAt = parseTimestamp(source.retrieved_at, `${source.reference_id} retrieved_at`);
      assert(
        retrievedAt <= generatedAt,
        `${source.reference_id} policy snapshot cannot postdate the report`,
      );
      assert(
        generatedAt - retrievedAt <= manifest.evidence_policy.policy_refresh_days * 86_400_000,
        `${source.reference_id} policy snapshot is stale`,
      );
    }
    assert(
      profileAudit.theme_check?.required_notices === 0,
      `${profile.id} must record zero required Theme Check notices`,
    );
  }
}

function snapshotAndHash(fd, snapshotPath) {
  const outputFd = openSync(
    snapshotPath,
    fsConstants.O_WRONLY | fsConstants.O_CREAT | fsConstants.O_EXCL,
    0o400,
  );
  const hash = createHash('sha256');
  const buffer = Buffer.allocUnsafe(1024 * 1024);
  try {
    let bytesRead;
    do {
      bytesRead = readSync(fd, buffer, 0, buffer.length, null);
      if (bytesRead > 0) {
        hash.update(buffer.subarray(0, bytesRead));
        let written = 0;
        while (written < bytesRead) {
          written += writeSync(
            outputFd,
            buffer,
            written,
            bytesRead - written,
          );
        }
      }
    } while (bytesRead > 0);
  } finally {
    closeSync(outputFd);
  }
  chmodSync(snapshotPath, 0o400);
  return hash.digest('hex');
}

function captureAncestorChain(rootPath, candidatePath) {
  const parentPath = dirname(candidatePath);
  const parentRelative = relative(rootPath, parentPath);
  const components = parentRelative === '' ? [] : parentRelative.split(/[\\/]/);
  const chain = [];
  let currentPath = rootPath;
  for (const component of ['', ...components]) {
    if (component) currentPath = join(currentPath, component);
    const stat = lstatSync(currentPath);
    assert(!stat.isSymbolicLink(), `artifact ancestor must not be a symlink: ${currentPath}`);
    assert(stat.isDirectory(), `artifact ancestor must be a directory: ${currentPath}`);
    chain.push({ path: currentPath, dev: stat.dev, ino: stat.ino });
  }
  return chain;
}

function assertAncestorChainUnchanged(chain) {
  for (const ancestor of chain) {
    const stat = lstatSync(ancestor.path);
    assert(
      !stat.isSymbolicLink() &&
        stat.isDirectory() &&
        stat.dev === ancestor.dev &&
        stat.ino === ancestor.ino,
      `artifact ancestor changed during verification: ${ancestor.path}`,
    );
  }
}

function validateArtifactFile(
  reportRoot,
  artifact,
  snapshotRoot,
  remainingAggregateBytes = maxAggregateArtifactBytes,
) {
  assertNonEmptyString(artifact.path, `${artifact.id} needs a relative path`);
  assert(!isAbsolute(artifact.path), `${artifact.id} path must be relative`);
  const candidatePath = resolve(reportRoot, artifact.path);
  const lexicalRelative = relative(reportRoot, candidatePath);
  assert(
    lexicalRelative !== '..' && !lexicalRelative.startsWith(`..${process.platform === 'win32' ? '\\' : '/'}`),
    `${artifact.id} path escapes the report bundle`,
  );
  const ancestorChain = captureAncestorChain(reportRoot, candidatePath);
  assert(existsSync(candidatePath), `${artifact.id} file does not exist at ${artifact.path}`);
  const realPath = realpathSync(candidatePath);
  const realRelative = relative(realpathSync(reportRoot), realPath);
  assert(
    realRelative !== '..' && !realRelative.startsWith(`..${process.platform === 'win32' ? '\\' : '/'}`),
    `${artifact.id} resolves outside the report bundle`,
  );
  const statBefore = statSync(realPath);
  assert(statBefore.isFile(), `${artifact.id} must resolve to a file`);
  assert(
    statBefore.size <= maxArtifactBytes,
    `${artifact.id} exceeds the ${maxArtifactBytes}-byte artifact limit`,
  );
  assert(
    statBefore.size <= remainingAggregateBytes,
    'candidate artifact bundle exceeds the 3 GiB aggregate staging limit',
  );
  const fd = openSync(realPath, fsConstants.O_RDONLY | fsConstants.O_NOFOLLOW);
  let digest;
  const snapshotPath = join(snapshotRoot, artifact.id);
  try {
    const opened = fstatSync(fd);
    assertAncestorChainUnchanged(ancestorChain);
    assert(
      statBefore.dev === opened.dev &&
        statBefore.ino === opened.ino &&
        statBefore.size === opened.size &&
        statBefore.mtimeMs === opened.mtimeMs,
      `${artifact.id} changed before it was opened`,
    );
    digest = snapshotAndHash(fd, snapshotPath);
    const statAfter = fstatSync(fd);
    assertAncestorChainUnchanged(ancestorChain);
    assert(
      opened.dev === statAfter.dev &&
        opened.ino === statAfter.ino &&
        opened.size === statAfter.size &&
        opened.mtimeMs === statAfter.mtimeMs,
      `${artifact.id} changed while it was being verified`,
    );
  } finally {
    closeSync(fd);
  }
  assert(
    digest.toLowerCase() === artifact.sha256.toLowerCase(),
    `${artifact.id} SHA-256 mismatch`,
  );
  return {
    realPath: snapshotPath,
    sourceRealPath: realPath,
    size: statBefore.size,
    digest,
  };
}

async function validateCandidateReport(
  report,
  reportPath,
  manifest,
  manifestDigest,
  model,
  snapshotRoot,
) {
  assertRequiredFields(
    report,
    manifest.candidate_report_contract.required,
    'candidate report',
  );
  assert(
    report.manifest_schema_version === manifest.schema_version,
    'candidate report manifest_schema_version does not match',
  );
  assert(
    report.manifest_sha256 === manifestDigest,
    'candidate report was produced against a different manifest revision',
  );
  assert(
    ['evidence-review', 'release-authorized'].includes(report.phase),
    'candidate report phase must be evidence-review or release-authorized',
  );
  const generatedAt = parseTimestamp(report.generated_at, 'candidate report generated_at');
  assert(
    Date.now() - generatedAt <=
      manifest.evidence_policy.evidence_refresh_days * 86_400_000,
    'candidate report evidence is stale',
  );
  assertRequiredFields(
    report.candidate,
    manifest.candidate_report_contract.candidate_required,
    'candidate',
  );
  assertNonEmptyString(report.candidate.theme_path, 'candidate needs theme_path');
  assertNonEmptyString(report.candidate.version, 'candidate needs version');
  assert(commitPattern.test(report.candidate.commit), 'candidate commit must be a Git object ID');
  assert(
    report.candidate.package_artifact_id === 'candidate-package',
    'candidate package_artifact_id must be candidate-package',
  );
  const source = validateSourceCandidate(report.candidate);

  assertStringArray(report.target_release_profiles, 'select at least one release profile');
  assert(
    new Set(report.target_release_profiles).size === report.target_release_profiles.length,
    'target release profiles must be unique',
  );
  const selectedProfiles = report.target_release_profiles.map((id) => {
    const profile = model.profileById.get(id);
    assert(profile, `unknown target release profile ${id}`);
    validateFreshReferences(manifest, model, profile);
    return profile;
  });

  assert(Array.isArray(report.artifacts), 'candidate report artifacts must be an array');
  assertUniqueIds(report.artifacts, 'candidate artifact');
  const reportRoot = dirname(resolve(reportPath));
  const artifactById = new Map();
  const realArtifactPaths = new Set();
  const artifactDigests = new Set();
  let aggregateArtifactBytes = 0;
  for (const artifact of report.artifacts) {
    assertRequiredFields(
      artifact,
      manifest.candidate_report_contract.artifact_required,
      `artifact ${artifact.id ?? '<unknown>'}`,
    );
    assert(model.artifactIds.has(artifact.id), `unknown artifact ${artifact.id}`);
    assert(sha256Pattern.test(artifact.sha256), `${artifact.id} needs a SHA-256 digest`);
    const verified = validateArtifactFile(
      reportRoot,
      artifact,
      snapshotRoot,
      maxAggregateArtifactBytes - aggregateArtifactBytes,
    );
    assert(!realArtifactPaths.has(verified.sourceRealPath), `${artifact.id} reuses another artifact path`);
    assert(!artifactDigests.has(verified.digest), `${artifact.id} duplicates another artifact's content`);
    realArtifactPaths.add(verified.sourceRealPath);
    artifactDigests.add(verified.digest);
    aggregateArtifactBytes += verified.size;
    artifactById.set(artifact.id, { ...artifact, ...verified });
  }
  assert(artifactById.has('candidate-package'), 'candidate-package artifact is missing');
  for (const artifactId of [
    'sbom',
    'video-delivery-audit',
    'build-provenance',
    'package-checksums',
    'compatibility-matrix',
    'scroll-fallback-report',
  ]) {
    assert(artifactById.has(artifactId), `${artifactId} artifact is missing`);
  }
  const packageArtifact = artifactById.get('candidate-package');

  const packageMetadata = validateCandidateZip(
    packageArtifact,
    report.candidate,
    source,
    selectedProfiles,
  );
  const evidenceRefreshDays = manifest.evidence_policy.evidence_refresh_days;
  validateSbom(artifactById.get('sbom'), generatedAt, evidenceRefreshDays);
  validateVideoAudit(
    artifactById.get('video-delivery-audit'),
    generatedAt,
    evidenceRefreshDays,
    packageArtifact,
    packageMetadata,
    snapshotRoot,
    source,
  );
  validateBuildProvenance(
    artifactById.get('build-provenance'),
    report,
    packageArtifact,
    generatedAt,
    evidenceRefreshDays,
    source,
    manifest.trust_roots.build_attestation,
  );
  validateChecksums(artifactById.get('package-checksums'), packageArtifact);
  validateCompatibilityMatrix(
    artifactById.get('compatibility-matrix'),
    artifactById,
    generatedAt,
    evidenceRefreshDays,
  );
  validateScrollFallbackAudit(
    artifactById.get('scroll-fallback-report'),
    artifactById,
    generatedAt,
    evidenceRefreshDays,
  );
  if (selectedProfiles.some((profile) => profile.policy_references.length > 0)) {
    assert(
      artifactById.has('marketplace-policy-audit'),
      'marketplace-policy-audit artifact is missing',
    );
    validateMarketplacePolicy(
      artifactById.get('marketplace-policy-audit'),
      selectedProfiles,
      manifest,
      model,
      generatedAt,
      manifest.trust_roots.policy_attestation,
    );
  }

  assert(Array.isArray(report.gates), 'candidate report gates must be an array');
  assertUniqueIds(report.gates, 'candidate gate');
  const reportGateById = new Map();
  for (const gate of report.gates) {
    assertRequiredFields(
      gate,
      manifest.candidate_report_contract.gate_required,
      `gate ${gate.id ?? '<unknown>'}`,
    );
    assert(model.gateById.has(gate.id), `unknown candidate gate ${gate.id}`);
    assert(
      manifest.evidence_policy.gate_statuses.includes(gate.status),
      `${gate.id} has invalid status ${gate.status}`,
    );
    assertStringArray(gate.evidence_artifacts, `${gate.id} needs evidence artifacts`);
    assertNonEmptyString(gate.notes, `${gate.id} needs evidence notes`);
    assert(
      gate.evidence_artifacts.every((id) => artifactById.has(id)),
      `${gate.id} references an absent artifact`,
    );
    const gateContract = model.gateById.get(gate.id);
    assert(
      Array.isArray(gate.criterion_results) &&
        gate.criterion_results.length === gateContract.criteria.length,
      `${gate.id} must report all ${gateContract.criteria.length} criteria`,
    );
    const criterionIndexes = gate.criterion_results.map(
      (criterion) => criterion.index,
    );
    assertSameMembers(
      criterionIndexes,
      gateContract.criteria.map((_, index) => index + 1),
      `${gate.id} criterion indexes must be the canonical 1-based set`,
    );
    for (const criterion of gate.criterion_results) {
      assertRequiredFields(
        criterion,
        manifest.candidate_report_contract.criterion_required,
        `${gate.id} criterion ${criterion.index ?? '<unknown>'}`,
      );
      assert(
        manifest.evidence_policy.gate_statuses.includes(criterion.status),
        `${gate.id} criterion ${criterion.index} has invalid status`,
      );
      assertStringArray(
        criterion.evidence_artifacts,
        `${gate.id} criterion ${criterion.index} needs evidence artifacts`,
      );
      assert(
        criterion.evidence_artifacts.every((id) => artifactById.has(id)),
        `${gate.id} criterion ${criterion.index} references an absent artifact`,
      );
      assert(
        criterion.evidence_artifacts.every((id) =>
          gate.evidence_artifacts.includes(id)),
        `${gate.id} criterion ${criterion.index} evidence is not declared by the gate`,
      );
      assertNonEmptyString(
        criterion.notes,
        `${gate.id} criterion ${criterion.index} needs evidence notes`,
      );
      const observedAt = parseTimestamp(
        criterion.observed_at,
        `${gate.id} criterion ${criterion.index} observed_at`,
      );
      assert(
        observedAt <= generatedAt,
        `${gate.id} criterion ${criterion.index} cannot postdate the report`,
      );
      assert(
        generatedAt - observedAt <=
          manifest.evidence_policy.evidence_refresh_days * 86_400_000,
        `${gate.id} criterion ${criterion.index} evidence is stale`,
      );
    }
    if (gate.status === 'pass') {
      assert(
        gate.criterion_results.every((criterion) => criterion.status === 'pass'),
        `${gate.id} cannot pass unless every criterion passes`,
      );
    }
    if (gate.status === 'not_applicable') {
      assert(
        gate.evidence_artifacts.includes(manifest.authority.approval_artifact),
        `${gate.id} not_applicable status needs founder approval evidence`,
      );
    }
    reportGateById.set(gate.id, gate);
  }

  const requiredGateIds = new Set(
    selectedProfiles.flatMap((profile) => profile.required_gates),
  );
  for (const gateId of requiredGateIds) {
    const gate = reportGateById.get(gateId);
    assert(gate, `required gate ${gateId} is missing`);
    assert(gate.status === 'pass', `required gate ${gateId} is ${gate.status}, not pass`);
    const requiredArtifacts = model.gateById.get(gateId).required_artifacts;
    assert(
      requiredArtifacts.every((id) => gate.evidence_artifacts.includes(id)),
      `${gateId} does not cite every required artifact`,
    );
  }

  const evidenceRoot = computeEvidenceRoot(report, artifactById);
  assert(
    report.evidence_root_sha256 === evidenceRoot,
    'candidate report evidence_root_sha256 does not bind the reviewed gates and artifacts',
  );

  assert(Array.isArray(report.approvals), 'candidate report approvals must be an array');
  if (report.phase === 'evidence-review') {
    assert(
      report.approvals.length === 0,
      'evidence-review reports must not imply founder authorization',
    );
    return {
      artifactCount: artifactById.size,
      gateCount: requiredGateIds.size,
      phase: report.phase,
      profiles: report.target_release_profiles,
    };
  }
  const approvalDomains = report.approvals.map((approval) => approval.domain);
  assert(
    new Set(approvalDomains).size === approvalDomains.length,
    'approval domains must be unique',
  );
  const approvalByDomain = new Map();
  for (const approval of report.approvals) {
    assertRequiredFields(
      approval,
      manifest.candidate_report_contract.approval_required,
      `approval ${approval.domain ?? '<unknown>'}`,
    );
    assert(
      expectedApprovalDomains.includes(approval.domain),
      `unknown approval domain ${approval.domain}`,
    );
    assert(approval.decision === 'approved', `${approval.domain} is not explicitly approved`);
    assertNonEmptyString(approval.approver, `${approval.domain} needs an approver`);
    assert(
      !/^(agent|machine|automation|automated)$/i.test(approval.approver.trim()),
      `${approval.domain} approval cannot come from an agent or machine`,
    );
    const recordedAt = parseTimestamp(
      approval.recorded_at,
      `${approval.domain} recorded_at`,
    );
    assert(recordedAt >= generatedAt, `${approval.domain} approval predates the evidence report`);
    assert(
      approval.evidence_artifact === manifest.authority.approval_artifact,
      `${approval.domain} must cite ${manifest.authority.approval_artifact}`,
    );
    assert(
      artifactById.has(approval.evidence_artifact),
      `${approval.domain} approval artifact is absent`,
    );
    approvalByDomain.set(approval.domain, approval);
  }

  const requiredApprovalDomains = new Set(
    selectedProfiles.flatMap((profile) => profile.required_approvals),
  );
  for (const domain of requiredApprovalDomains) {
    assert(approvalByDomain.has(domain), `founder approval is missing for ${domain}`);
  }

  assert(
    artifactById.has(manifest.authority.approval_artifact),
    `${manifest.authority.approval_artifact} artifact is missing`,
  );
  validateFounderApproval(
    artifactById.get(manifest.authority.approval_artifact),
    report,
    packageArtifact,
    manifest,
  );

  return {
    artifactCount: artifactById.size,
    gateCount: requiredGateIds.size,
    phase: report.phase,
    profiles: report.target_release_profiles,
  };
}

function parseArguments(argv) {
  if (argv.length === 0) return { reportPath: null, selfTest: false };
  if (argv.length === 1 && ['--help', '-h'].includes(argv[0])) {
    console.log('Usage: node scripts/validate-theme-machine.mjs [--report path/to/report.json | --self-test]');
    process.exit(0);
  }
  if (argv.length === 1 && argv[0] === '--self-test') {
    return { reportPath: null, selfTest: true };
  }
  assert(
    argv.length === 2 && argv[0] === '--report',
    'usage: validate-theme-machine.mjs [--report path/to/report.json | --self-test]',
  );
  return { reportPath: resolve(argv[1]), selfTest: false };
}

function runSelfTest() {
  const testRoot = mkdtempSync(join(tmpdir(), 'devskyy-theme-machine-test-'));
  const reportRoot = join(testRoot, 'bundle');
  const snapshotRoot = join(testRoot, 'snapshot');
  mkdirSync(reportRoot, { mode: 0o700 });
  mkdirSync(snapshotRoot, { mode: 0o700 });
  try {
    const original = Buffer.from('{"trusted":true}\n');
    const sourcePath = join(reportRoot, 'security.json');
    writeFileSync(sourcePath, original, { mode: 0o600 });
    const verified = validateArtifactFile(
      reportRoot,
      {
        id: 'security-report',
        path: 'security.json',
        sha256: sha256(original),
      },
      snapshotRoot,
    );
    writeFileSync(sourcePath, '{"trusted":false}\n');
    assert(
      readFileSync(verified.realPath).equals(original),
      'self-test: immutable snapshot changed with source',
    );

    const outsidePath = join(testRoot, 'outside.json');
    writeFileSync(outsidePath, '{}\n', { mode: 0o600 });
    symlinkSync(outsidePath, join(reportRoot, 'escape.json'));
    let escapeBlocked = false;
    try {
      validateArtifactFile(
        reportRoot,
        {
          id: 'privacy-data-map',
          path: 'escape.json',
          sha256: sha256('{}\n'),
        },
        snapshotRoot,
      );
    } catch {
      escapeBlocked = true;
    }
    assert(escapeBlocked, 'self-test: symlink escape was not blocked');

    let unsignedBlocked = false;
    try {
      validateTrustedEnvelope(
        { schema_version: 1, payload: {}, key_id: 'none', signature: 'AA==' },
        { public_keys: [] },
        'self-test attestation',
      );
    } catch {
      unsignedBlocked = true;
    }
    assert(unsignedBlocked, 'self-test: empty trust root did not fail closed');

    const baseReport = {
      manifest_schema_version: 2,
      manifest_sha256: 'a'.repeat(64),
      candidate: { commit: 'b'.repeat(40) },
      target_release_profiles: ['internal-production'],
      generated_at: '2026-08-04T00:00:00Z',
      gates: [{ id: 'security', status: 'pass' }],
      artifacts: [
        {
          id: 'security-report',
          path: 'security.json',
          sha256: verified.digest,
        },
      ],
    };
    const artifactMap = new Map([
      [
        'security-report',
        { digest: verified.digest, size: verified.size },
      ],
    ]);
    const firstRoot = computeEvidenceRoot(baseReport, artifactMap);
    const secondRoot = computeEvidenceRoot(
      { ...baseReport, gates: [{ id: 'security', status: 'blocked' }] },
      artifactMap,
    );
    assert(firstRoot !== secondRoot, 'self-test: evidence root did not bind gate status');
  } finally {
    rmSync(testRoot, { recursive: true, force: true });
  }
  console.log('Theme machine adversarial self-test passed: immutable snapshot, symlink containment, fail-closed trust root, and evidence-root binding.');
}

async function main() {
  const { reportPath, selfTest } = parseArguments(process.argv.slice(2));
  const manifestBytes = readFileSync(manifestPath);
  const manifest = JSON.parse(manifestBytes.toString('utf8'));
  const manifestDigest = sha256(manifestBytes);
  const model = validateManifest(manifest);

  if (selfTest) {
    runSelfTest();
    return;
  }

  if (!reportPath) {
    const unconfiguredTrustRoots = [
      manifest.trust_roots.build_attestation,
      manifest.trust_roots.policy_attestation,
      manifest.authority.approval_verification,
    ].filter((config) => config.public_keys.length === 0).length;
    console.log(
      `Theme machine contract valid: ${manifest.lanes.length} lanes, ${manifest.quality_gates.length} evidence gates, ${manifest.release_profiles.length} release profiles. ${unconfiguredTrustRoots} trust roots are intentionally unconfigured, so candidate report validation and authorization fail closed. No theme readiness was assessed.`,
    );
  } else {
    const report = parseJson(reportPath, 'candidate report');
    const snapshotRoot = mkdtempSync(
      join(tmpdir(), 'devskyy-theme-machine-'),
    );
    chmodSync(snapshotRoot, 0o700);
    let result;
    try {
      result = await validateCandidateReport(
        report,
        reportPath,
        manifest,
        manifestDigest,
        model,
        snapshotRoot,
      );
    } finally {
      rmSync(snapshotRoot, { recursive: true, force: true });
    }
    if (result.phase === 'evidence-review') {
      console.log(
        `Candidate report structurally and semantically validated for founder evidence review: ${result.profiles.join(', ')}; ${result.gateCount} required gates and ${result.artifactCount} bound artifacts. Human evidence quality, marketplace acceptance, and release approval remain unassessed.`,
      );
    } else {
      console.log(
        `Candidate report and founder signature validated for release handoff: ${result.profiles.join(', ')}. Marketplace acceptance and deployment remain separate external actions.`,
      );
    }
  }
}

main().catch((error) => {
  console.error(error.message);
  process.exitCode = 1;
});
