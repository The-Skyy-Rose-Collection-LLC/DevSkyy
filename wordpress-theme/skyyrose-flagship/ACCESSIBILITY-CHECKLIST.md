# Accessibility Testing Checklist

Quick reference checklist for WCAG 2.1 AA compliance testing.

## Perceivable

### Text Alternatives (1.1)
- [ ] All images have appropriate alt text
- [ ] Decorative images use empty alt=""
- [ ] Complex images have detailed descriptions
- [ ] Form buttons have descriptive values
- [ ] Icons have text alternatives or aria-labels

### Time-based Media (1.2)
- [ ] Videos have captions
- [ ] Audio content has transcripts
- [ ] Pre-recorded audio/video has audio descriptions

### Adaptable (1.3)
- [ ] Content structure is marked with proper HTML
- [ ] Heading hierarchy is logical (H1 → H2 → H3)
- [ ] Lists use proper list markup
- [ ] Tables use proper table markup
- [ ] Form labels are associated with inputs
- [ ] Instructions don't rely on sensory characteristics alone

### Distinguishable (1.4)
- [ ] Color is not used as the only visual means of conveying information
- [ ] Text has minimum 4.5:1 contrast ratio
- [ ] Large text has minimum 3:1 contrast ratio
- [ ] UI components have minimum 3:1 contrast ratio
- [ ] Text can be resized to 200% without loss of content
- [ ] No images of text (use real text)
- [ ] Audio doesn't autoplay or has controls
- [ ] Focus indicators are visible

## Operable

### Keyboard Accessible (2.1)
- [ ] All functionality available via keyboard
- [ ] No keyboard traps
- [ ] Keyboard shortcuts don't conflict
- [ ] Tab order is logical
- [ ] Skip links are provided

### Enough Time (2.2)
- [ ] Time limits can be turned off, adjusted, or extended
- [ ] Moving content can be paused, stopped, or hidden
- [ ] No blinking content
- [ ] Interruptions can be postponed or suppressed

### Seizures and Physical Reactions (2.3)
- [ ] Nothing flashes more than 3 times per second
- [ ] Motion animation can be disabled

### Navigable (2.4)
- [ ] Blocks of content can be bypassed (skip links)
- [ ] Pages have descriptive titles
- [ ] Focus order is meaningful
- [ ] Link purpose is clear from link text
- [ ] Multiple ways to find pages (menu, search, sitemap)
- [ ] Headings and labels are descriptive
- [ ] Focus indicator is visible

### Input Modalities (2.5)
- [ ] All pointer gestures have keyboard alternatives
- [ ] Touch targets are at least 44x44 CSS pixels
- [ ] Labels match visible text
- [ ] Motion actuation can be disabled

## Understandable

### Readable (3.1)
- [ ] Page language is identified
- [ ] Language changes are marked
- [ ] Unusual words are defined
- [ ] Abbreviations are explained

### Predictable (3.2)
- [ ] Focus doesn't cause unexpected context changes
- [ ] Input doesn't cause unexpected context changes
- [ ] Navigation is consistent across pages
- [ ] Components are identified consistently
- [ ] Changes are initiated only on request

### Input Assistance (3.3)
- [ ] Errors are identified and described
- [ ] Labels and instructions are provided
- [ ] Error suggestions are offered
- [ ] Errors are prevented for legal/financial data
- [ ] Help is available for form completion

## Robust

### Compatible (4.1)
- [ ] HTML is valid
- [ ] Name, role, value are programmatically determined
- [ ] Status messages can be programmatically determined
- [ ] ARIA is used correctly
- [ ] No duplicate IDs

---

## Quick Keyboard Tests

### Navigation
```
Tab                  → Move forward through interactive elements
Shift + Tab          → Move backward through interactive elements
Enter                → Activate links and buttons
Space                → Activate buttons, check/uncheck checkboxes
Escape               → Close modals, cancel actions
Arrow Keys           → Navigate within menus, select options
Home/End             → Jump to first/last item
```

### Expected Behavior
- [ ] Tab moves focus visibly
- [ ] All interactive elements can receive focus
- [ ] Focus order follows visual order
- [ ] Skip link appears and works
- [ ] Menu opens/closes with keyboard
- [ ] Modal traps focus (Tab cycles within)
- [ ] Escape closes modal
- [ ] Form can be completed without mouse

---

## Quick Screen Reader Tests

### VoiceOver (Mac)
```
Command + F5         → Enable VoiceOver
Control              → Pause/resume speech
Control + Option + → → Navigate forward
Control + Option + ← → Navigate backward
Control + Option + U → Open rotor (headings, links, etc.)
```

### NVDA (Windows)
```
Control + Alt + N    → Start NVDA
Insert + Down Arrow  → Read from current position
Insert + Space       → Browse/focus mode toggle
Insert + F7          → Elements list
H                    → Next heading
```

### What to Listen For
- [ ] Meaningful page title announced
- [ ] Heading hierarchy makes sense
- [ ] All images have descriptions
- [ ] Form labels are read
- [ ] Button purposes are clear
- [ ] Link text is descriptive
- [ ] Dynamic updates are announced
- [ ] Landmark regions are identified

---

## Automated Testing Tools

### Browser DevTools
- [ ] Run Lighthouse accessibility audit
- [ ] Check color contrast in DevTools
- [ ] Inspect ARIA attributes
- [ ] Validate HTML

### Extensions
- [ ] WAVE - Visual accessibility check
- [ ] Axe DevTools - Automated testing
- [ ] Color Contrast Analyzer - Contrast verification
- [ ] HeadingsMap - Heading structure visualization

---

## Manual Checks

### Visual Review
- [ ] Focus indicators are visible
- [ ] Text is readable at 200% zoom
- [ ] Content reflows at mobile sizes
- [ ] No horizontal scrolling at 320px width
- [ ] Touch targets are large enough
- [ ] Spacing is adequate
- [ ] Error messages are clear and visible

### Functionality Review
- [ ] Forms validate and provide helpful errors
- [ ] Search works and is accessible
- [ ] Cart updates are announced
- [ ] Modals are accessible
- [ ] Dropdowns work with keyboard
- [ ] Media controls are accessible
- [ ] Custom widgets are accessible

---

## Common Issues to Check

### Forms
- [ ] Every input has a label
- [ ] Required fields are marked
- [ ] Error messages are specific
- [ ] Success messages are clear
- [ ] Field validation is helpful
- [ ] Submit buttons are descriptive

### Images
- [ ] Product images have meaningful alt text
- [ ] Logos have alt text
- [ ] Icon-only buttons have aria-labels
- [ ] Complex images have long descriptions

### Navigation
- [ ] Main menu is keyboard accessible
- [ ] Submenu navigation works with keyboard
- [ ] Mobile menu is accessible
- [ ] Breadcrumbs are marked up correctly
- [ ] Search is accessible

### WooCommerce Specific
- [ ] Product quantity inputs are labeled
- [ ] Add to cart buttons are descriptive
- [ ] Cart updates are announced
- [ ] Checkout forms are accessible
- [ ] Product filters are keyboard accessible
- [ ] Product images have alt text
- [ ] Reviews are accessible

---

## Priority Levels

### Critical (Fix Immediately)
- Missing alt text on important images
- Keyboard traps
- Color contrast failures on text
- Forms without labels
- Missing page titles

### High Priority
- Poor focus indicators
- Incomplete ARIA implementation
- Heading hierarchy issues
- Skip link missing or broken

### Medium Priority
- Non-descriptive link text
- Missing landmark roles
- Inconsistent navigation
- Missing status messages

### Low Priority
- Minor HTML validation errors
- Redundant ARIA
- Could be more descriptive
- Nice-to-have improvements

---

## Testing Schedule

### Before Launch
- [ ] Complete full accessibility audit
- [ ] Test with screen reader
- [ ] Complete keyboard testing
- [ ] Run automated tests
- [ ] Fix all critical issues
- [ ] Fix all high priority issues

### Monthly
- [ ] Run automated tests
- [ ] Spot check new content
- [ ] Review analytics for accessibility issues

### Quarterly
- [ ] Full keyboard test
- [ ] Screen reader test
- [ ] User testing with disabled users
- [ ] Review and update documentation

---

## Resources

- [WCAG 2.1 Quick Reference](https://www.w3.org/WAI/WCAG21/quickref/)
- [WebAIM Checklist](https://webaim.org/standards/wcag/checklist)
- [A11y Project Checklist](https://www.a11yproject.com/checklist/)

---

**Remember:** Automated tools catch only 30-40% of accessibility issues. Manual testing is essential!
