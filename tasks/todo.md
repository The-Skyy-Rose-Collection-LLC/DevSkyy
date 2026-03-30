# Current Tasks

## SkyyRose Theme v6.2.0 — Remaining Work

### Hero Images Needed (1-shot fix batch)
- [ ] Black Rose logo — dark chrome on dark bg, needs lighter version or glow
- [ ] Pre-Order hero — needs tri-split scene images
- [ ] About hero — needs Skyy Rose photo from user
- [ ] Kids Capsule hero — needs scene image + logo wordmark
- [ ] Love Hurts hero — user wants Beast with back turned (image not in repo)

### File Splits (over 800-line limit)
- [ ] `about.css` (1,401 lines) → split into `about-layout.css` + `about-effects.css`
- [ ] `homepage-v2.css` (1,338 lines) → audit for dead rules, split if still over 800
- [ ] `preorder-gateway.js` (966 lines) → audit/split into logic + animations

### Immersive Pages (separate terminal)
- [ ] Being built in parallel — DO NOT TOUCH from this terminal

### Post-Launch
- [ ] Run build.sh to generate missing .min.css/.min.js for new files
- [ ] Lighthouse audit: target Performance >90, Accessibility >90
- [ ] Mobile viewport test (375px)
