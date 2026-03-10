# Requirements: SkyyRose WordPress Quality & Accessibility

**Defined:** 2026-03-10
**Core Value:** skyyrose.co works flawlessly on every device, passes WCAG AA accessibility, and shows the right products in the right collections.

## v1.1 Requirements

Requirements for WordPress quality and accessibility release. Each maps to roadmap phases.

### Accessibility

- [ ] **A11Y-01**: All buttons have explicit `type="button"` attribute
- [ ] **A11Y-02**: No duplicate element IDs in rendered HTML (stylesheet handles, nonce fields)
- [ ] **A11Y-03**: Empty headings have content or `aria-hidden="true"`
- [ ] **A11Y-04**: Empty links have descriptive `aria-label` attributes
- [ ] **A11Y-05**: Focusable elements with `aria-hidden="true"` have `tabindex="-1"`
- [ ] **A11Y-06**: All form inputs (radio, text) have associated labels or `aria-label`
- [ ] **A11Y-07**: Skip navigation link is wired and functional
- [ ] **A11Y-08**: Stylesheet and script handles are unique (no `skyyrose-accessibility` collision)
- [ ] **A11Y-09**: Below-fold images have `loading="lazy"`, hero images have `loading="eager"`

### Color Contrast

- [ ] **CNTR-01**: All text meets WCAG AA contrast ratio (4.5:1 normal text, 3:1 large text)
- [ ] **CNTR-02**: Narrative subtext opacity increased to meet 4.5:1 against background
- [ ] **CNTR-03**: Interactive-cards small text (10-12px) meets minimum contrast
- [ ] **CNTR-04**: Love Hurts $0 pricing replaced with "Pre-Order" display

### Responsive & Typography

- [ ] **RESP-01**: Font sizes scale appropriately across mobile/tablet/desktop breakpoints
- [ ] **RESP-02**: No horizontal overflow or layout breaking on mobile devices (320px+)
- [ ] **RESP-03**: Touch targets meet minimum 44x44px on mobile
- [ ] **RESP-04**: Typography hierarchy is consistent across all page templates

### Luxury Cursor

- [ ] **CURS-01**: Cursor renders above modals/popups (z-index management)
- [ ] **CURS-02**: Cursor pauses or adapts when modal/popup is open
- [ ] **CURS-03**: Cursor JS does not load on pages where it's CSS-hidden (immersive)

### Collection & Product Data

- [ ] **DATA-01**: Black Rose collection shows correct hero banner image
- [x] **DATA-02**: Pre-order products are not displayed in live collection catalog pages
- [x] **DATA-03**: Product-to-collection assignments match authoritative product list

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Accessibility Advanced

- **A11Y-ADV-01**: WCAG AAA compliance (enhanced contrast 7:1)
- **A11Y-ADV-02**: Automated accessibility testing in CI pipeline
- **A11Y-ADV-03**: Screen reader testing with real AT tools (NVDA, VoiceOver)

## Out of Scope

| Feature | Reason |
|---------|--------|
| WCAG AAA compliance | Targeting AA level -- AAA deferred to v2 |
| New feature development | This milestone is polish and fixes only |
| Automated a11y CI testing | Would require pa11y/axe integration -- defer to v2 |
| Redesign of any page templates | Fixing existing layouts, not creating new ones |
| Mobile app | Web-first, mobile later |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| A11Y-01 | Phase 10 | Pending |
| A11Y-02 | Phase 10 | Pending |
| A11Y-03 | Phase 10 | Pending |
| A11Y-04 | Phase 10 | Pending |
| A11Y-05 | Phase 10 | Pending |
| A11Y-06 | Phase 10 | Pending |
| A11Y-07 | Phase 10 | Pending |
| A11Y-08 | Phase 10 | Pending |
| A11Y-09 | Phase 10 | Pending |
| CNTR-01 | Phase 11 | Pending |
| CNTR-02 | Phase 11 | Pending |
| CNTR-03 | Phase 11 | Pending |
| CNTR-04 | Phase 11 | Pending |
| RESP-01 | Phase 12 | Pending |
| RESP-02 | Phase 12 | Pending |
| RESP-03 | Phase 12 | Pending |
| RESP-04 | Phase 12 | Pending |
| CURS-01 | Phase 13 | Pending |
| CURS-02 | Phase 13 | Pending |
| CURS-03 | Phase 13 | Pending |
| DATA-01 | Phase 9 | Pending |
| DATA-02 | Phase 9 | Complete |
| DATA-03 | Phase 9 | Complete |

**Coverage:**
- v1.1 requirements: 18 total
- Mapped to phases: 18
- Unmapped: 0

---
*Requirements defined: 2026-03-10*
*Last updated: 2026-03-10 after roadmap creation*
