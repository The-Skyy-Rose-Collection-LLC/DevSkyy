---
name: scroll-timeline-supports-pattern
tags: [css, animation-timeline, scroll-driven, browser-support, raf-fallback]
locked: 2026-05-25
verified_via: Context7/flackr/scroll-timeline
---

# animation-timeline: scroll() — @supports + rAF Fallback Pattern

## Syntax (verified)

```css
@supports (animation-timeline: scroll()) {
  @keyframes heroParallax {
    from { transform: scale(1.05) translateY(0%); }
    to   { transform: scale(1.05) translateY(-8%); }
  }
  .hero__bg {
    animation: heroParallax linear both;
    animation-timeline: scroll(block root);  /* root scroller, block axis */
    animation-range: 0vh 100vh;
  }
}
```

## Browser Support (as of 2026-05)

| Browser | Native | Version |
|---------|--------|---------|
| Chrome | YES | 115+ |
| Edge | YES | 115+ |
| Firefox | YES | 110+ |
| Safari | NO | not supported |

## JS Fallback Gate

```js
var supportsScrollTimeline = CSS.supports && CSS.supports('animation-timeline', 'scroll()');
if (!prefersReduced && !supportsScrollTimeline) {
  // rAF parallax path (Safari + older browsers)
}
```

## Key Rules

- `@supports (animation-timeline: scroll())` — correct guard syntax
- `scroll(block root)` — block axis on root scroller (best for vertical parallax)
- `scroll(y nearest)` — y axis on nearest scrollable ancestor
- Always include `animation-range` — without it, animation applies over full scroll height
- prefers-reduced-motion: add `animation: none !important` inside the @supports block too
- Compose with `scale()` in keyframes — NOT as a separate transform (they override each other)
- rAF path: use `translate3d(0, offset, 0) scale(1.05)` to compose both transforms

## Pitfall

If rAF sets `node.style.transform` while CSS scroll-driven animation also runs → both fight.
Fix: gate rAF on `supportsScrollTimeline` so only one path runs at a time.
