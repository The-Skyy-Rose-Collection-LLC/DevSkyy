# Verification Rules and Examples

Every role verifies its work before handoff. If the required proof cannot be
produced, report `BLOCKED` or `FAIL`; never broaden a claim.

## Trusted sources

Use repository-approved canon and source-of-truth files for brand/catalog facts.
For platform claims use current primary sources: official WordPress,
WooCommerce, PHP, browser, WCAG/WAI, marketplace, dependency documentation, or
the authoritative upstream source code. Record URL or source path, publisher,
retrieval date, relevant version, and the specific requirement used. Community
posts may aid discovery but cannot authenticate a release claim.

## Evidence records

Each record contains gate ID, phase/attempt, source/built/package candidate ID,
claim, proof class, route/component, viewport/state, command or journey, result,
tool and platform versions, authoritative source, timestamp, artifact path and
SHA-256, owner, independent reviewer, and disposition.

## Examples

### Visual design

Claim: collection page preserves garment prominence on mobile.

Proof: approved creative-contract section, approved SKU/image provenance,
deterministic 390px browser screenshot, comparison screenshot, screenshot hash,
eyes-on reviewer, and `PASS`/finding. CSS inspection alone fails this gate.

### WooCommerce compatibility

Claim: template overrides support the targeted WooCommerce version.

Proof: official upstream template/source at that version, override inventory,
automated outdated-template result, and browser journeys for relevant product
states. Documentation alone does not prove the candidate.

### Accessibility

Claim: cart drawer is keyboard accessible.

Proof: current WCAG/WAI requirement, keyboard journey trace, focus screenshots,
automated scan output, and independent manual disposition. An automated scan
alone is insufficient.

### Build and package

Claim: the archive is installable and contains current generated assets.

Proof: clean-environment build command, source/generated parity check, archive
digest, package inventory, install/activation smoke result, and candidate
provenance chain.

### Product imagery

Claim: the PDP displays the correct garment.

Proof: catalog SKU, approved image-registry record, rights status, pixel-level
eyes-on comparison, route screenshot, and reviewer disposition. Filename and alt
text agreement alone are insufficient.
