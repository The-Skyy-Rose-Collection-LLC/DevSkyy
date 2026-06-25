---
name: accessibility
description: Design, implement, and audit inclusive digital products using WCAG 2.2 Level AA
  standards. Use this skill to generate semantic ARIA for Web and accessibility traits for Web and Native platforms (iOS/Android).
origin: ECC
---

# Accessibility (WCAG 2.2)

This skill ensures that digital interfaces are Perceivable, Operable, Understandable, and Robust (POUR) for all users, including those using screen readers, switch controls, or keyboard navigation. It focuses on the technical implementation of WCAG 2.2 success criteria.

## When to Use

- Defining UI component specifications for Web, iOS, or Android.
- Auditing existing code for accessibility barriers or compliance gaps.
- Implementing new WCAG 2.2 standards like Target Size (Minimum) and Focus Appearance.
- Mapping high-level design requirements to technical attributes (ARIA roles, traits, hints).

## Core Concepts

- **POUR Principles**: The foundation of WCAG (Perceivable, Operable, Understandable, Robust).
- **Semantic Mapping**: Using native elements over generic containers to provide built-in accessibility.
- **Accessibility Tree**: The representation of the UI that assistive technologies actually "read."
- **Focus Management**: Controlling the order and visibility of the keyboard/screen reader cursor.
- **Labeling & Hints**: Providing context through `aria-label`, `accessibilityLabel`, and `contentDescription`.

## How It Works

### Step 1: Identify the Component Role

Determine the functional purpose (e.g., Is this a button, a link, or a tab?). Use the most semantic native element available before resorting to custom roles.

### Step 2: Define Perceivable Attributes

- Ensure text contrast meets **4.5:1** (normal) or **3:1** (large/UI).
- Add text alternatives for non-text content (images, icons).
- Implement responsive reflow (up to 400% zoom without loss of function).

### Step 3: Implement Operable Controls

- Ensure a minimum **24x24 CSS pixel** target size (WCAG 2.2 SC 2.5.8).
- Verify all interactive elements are reachable via keyboard and have a visible focus indicator (SC 2.4.11).
- Provide single-pointer alternatives for dragging movements.

### Step 4: Ensure Understandable Logic

- Use consistent navigation patterns.
- Provide descriptive error messages and suggestions for correction (SC 3.3.3).
- Implement "Redundant Entry" (SC 3.3.7) to prevent asking for the same data twice.

### Step 5: Verify Robust Compatibility

- Use correct `Name, Role, Value` patterns.
- Implement `aria-live` or live regions for dynamic status updates.

## Accessibility Architecture Diagram

```mermaid
flowchart TD
  UI["UI Component"] --> Platform{Platform?}
  Platform -->|Web| ARIA["WAI-ARIA + HTML5"]
  Platform -->|iOS| SwiftUI["Accessibility Traits + Labels"]
  Platform -->|Android| Compose["Semantics + ContentDesc"]

  ARIA --> AT["Assistive Technology (Screen Readers, Switches)"]
  SwiftUI --> AT
  Compose --> AT
```

## Cross-Platform Mapping

| Feature            | Web (HTML/ARIA)          | iOS (SwiftUI)                        | Android (Compose)                                           |
| :----------------- | :----------------------- | :----------------------------------- | :---------------------------------------------------------- |
| **Primary Label**  | `aria-label` / `<label>` | `.accessibilityLabel()`              | `contentDescription`                                        |
| **Secondary Hint** | `aria-describedby`       | `.accessibilityHint()`               | `Modifier.semantics { stateDescription = ... }`             |
| **Action Role**    | `role="button"`          | `.accessibilityAddTraits(.isButton)` | `Modifier.semantics { role = Role.Button }`                 |
| **Live Updates**   | `aria-live="polite"`     | `.accessibilityLiveRegion(.polite)`  | `Modifier.semantics { liveRegion = LiveRegionMode.Polite }` |

## Examples

### Web: Accessible Search

```html
<form role="search">
  <label for="search-input" class="sr-only">Search products</label>
  <input type="search" id="search-input" placeholder="Search..." />
  <button type="submit" aria-label="Submit Search">
    <svg aria-hidden="true">...</svg>
  </button>
</form>
```

### iOS: Accessible Action Button

```swift
Button(action: deleteItem) {
    Image(systemName: "trash")
}
.accessibilityLabel("Delete item")
.accessibilityHint("Permanently removes this item from your list")
.accessibilityAddTraits(.isButton)
```

### Android: Accessible Toggle

```kotlin
Switch(
    checked = isEnabled,
    onCheckedChange = { onToggle() },
    modifier = Modifier.semantics {
        contentDescription = "Enable notifications"
    }
)
```

## Anti-Patterns to Avoid

- **Div-Buttons**: Using a `<div>` or `<span>` for a click event without adding a role and keyboard support.
- **Color-Only Meaning**: Indicating an error or status _only_ with a color change (e.g., turning a border red).
- **Uncontained Modal Focus**: Modals that don't trap focus, allowing keyboard users to navigate background content while the modal is open. Focus must be contained _and_ escapable via the `Escape` key or an explicit close button (WCAG SC 2.1.2).
- **Redundant Alt Text**: Using "Image of..." or "Picture of..." in alt text (screen readers already announce the role "Image").

## Best Practices Checklist

- [ ] Interactive elements meet the **24x24px** (Web) or **44x44pt** (Native) target size.
- [ ] Focus indicators are clearly visible and high-contrast.
- [ ] Modals **contain focus** while open, and release it cleanly on close (`Escape` key or close button).
- [ ] Dropdowns and menus restore focus to the trigger element on close.
- [ ] Forms provide text-based error suggestions.
- [ ] All icon-only buttons have a descriptive text label.
- [ ] Content reflows properly when text is scaled.

## References

- [WCAG 2.2 Guidelines](https://www.w3.org/TR/WCAG22/)
- [WAI-ARIA Authoring Practices](https://www.w3.org/TR/wai-aria-practices/)
- [iOS Accessibility Programming Guide](https://developer.apple.com/documentation/accessibility)
- [iOS Human Interface Guidelines - Accessibility](https://developer.apple.com/design/human-interface-guidelines/accessibility)
- [Android Accessibility Developer Guide](https://developer.android.com/guide/topics/ui/accessibility)

## Composite WAI-ARIA Widget Patterns

### Dialog with Focus Trap (`role="dialog"` + `aria-modal`)

A modal must trap keyboard focus inside while open and restore it to the trigger on close.

```html
<button id="open-dialog">Open Settings</button>

<div
  id="settings-dialog"
  role="dialog"
  aria-modal="true"
  aria-labelledby="dialog-title"
  aria-describedby="dialog-desc"
  hidden
>
  <h2 id="dialog-title">Settings</h2>
  <p id="dialog-desc">Adjust your account preferences below.</p>

  <label for="theme-select">Theme</label>
  <select id="theme-select">
    <option>Light</option>
    <option>Dark</option>
  </select>

  <button id="dialog-close">Close</button>
</div>
```

```js
// Minimal focus-trap implementation
const FOCUSABLE = 'a[href],button:not([disabled]),input,select,textarea,[tabindex]:not([tabindex="-1"])';

function openDialog(dialog, trigger) {
  dialog.hidden = false;
  const focusable = [...dialog.querySelectorAll(FOCUSABLE)];
  focusable[0]?.focus();

  dialog.addEventListener('keydown', function trap(e) {
    if (e.key === 'Escape') { closeDialog(dialog, trigger); dialog.removeEventListener('keydown', trap); return; }
    if (e.key !== 'Tab') return;
    const first = focusable[0], last = focusable[focusable.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  });
}

function closeDialog(dialog, trigger) {
  dialog.hidden = true;
  trigger.focus(); // restore focus to trigger
}
```

### Combobox (`role="combobox"` + `aria-expanded` / `aria-controls` / `aria-activedescendant`)

```html
<label for="country-input">Country</label>
<div class="combobox-wrapper">
  <input
    id="country-input"
    type="text"
    role="combobox"
    aria-expanded="false"
    aria-autocomplete="list"
    aria-controls="country-listbox"
    aria-activedescendant=""
    autocomplete="off"
  />
  <ul id="country-listbox" role="listbox" aria-label="Countries" hidden>
    <li id="opt-au" role="option" aria-selected="false">Australia</li>
    <li id="opt-ca" role="option" aria-selected="false">Canada</li>
    <li id="opt-us" role="option" aria-selected="false">United States</li>
  </ul>
</div>
```

Key attributes to keep in sync as the user navigates:
- `aria-expanded="true"` when the listbox is visible.
- `aria-activedescendant` set to the `id` of the currently highlighted option.
- `aria-selected="true"` on the confirmed selection; `"false"` on all others.

### Tabs (`role="tablist"` / `role="tab"` / `role="tabpanel"`)

```html
<div class="tabs">
  <ul role="tablist" aria-label="Order details">
    <li>
      <button
        id="tab-summary"
        role="tab"
        aria-selected="true"
        aria-controls="panel-summary"
        tabindex="0"
      >Summary</button>
    </li>
    <li>
      <button
        id="tab-items"
        role="tab"
        aria-selected="false"
        aria-controls="panel-items"
        tabindex="-1"
      >Items</button>
    </li>
  </ul>

  <div id="panel-summary" role="tabpanel" aria-labelledby="tab-summary" tabindex="0">
    <!-- summary content -->
  </div>
  <div id="panel-items" role="tabpanel" aria-labelledby="tab-items" tabindex="0" hidden>
    <!-- items content -->
  </div>
</div>
```

Keyboard contract: `ArrowLeft`/`ArrowRight` move focus between tabs; `Home`/`End` jump to first/last. Set `tabindex="0"` on the active tab, `tabindex="-1"` on all others. Activate on focus (recommended for desktop) or on `Enter`/`Space` (manual activation).

## Automated Accessibility Testing

### jest-axe (unit / component level)

```ts
// Button.test.tsx
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from 'jest-axe';
import { IconButton } from './IconButton';

expect.extend(toHaveNoViolations);

it('has no axe violations', async () => {
  const { container } = render(
    <IconButton icon="trash" label="Delete item" onClick={() => {}} />
  );
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

### @axe-core/playwright (integration / E2E level)

```ts
// dialog.spec.ts
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('settings dialog is accessible', async ({ page }) => {
  await page.goto('/settings');
  await page.getByRole('button', { name: 'Open Settings' }).click();
  await page.getByRole('dialog').waitFor();

  const results = await new AxeBuilder({ page })
    .include('[role="dialog"]')
    .analyze();

  expect(results.violations).toEqual([]);
});
```

Install: `npm install --save-dev jest-axe @axe-core/playwright`

## Related Skills

- `frontend-patterns`
- `design-system`
- `liquid-glass-design`
