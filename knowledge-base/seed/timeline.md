# SkyyRose Timeline — Brand Canon

> Canonical timeline for `template-about.php` Chapter III — The Journey (Phase 2 Commit 4, Selling Edition).
> Built from press-corroborated dates + Corey-provided drop years (2026-05-13).
> **Replaces** the fabricated 2019-2025 timeline in the deleted 686-line `template-about.php` (commit `3860e38cb`).

## Confirmed milestones

| Year | Event | Source |
|------|-------|--------|
| 2020 | The Skyy Rose Collection founded by Corey Foster — single-father origin | SF Post / Best of Best (Corey: "4 years ago" from 2024) |
| 2021 | Three flagship adult collections drop: **Black Rose**, **Love Hurts**, **Signature** | Corey 2026-05-13 |
| 2023 | **Maxim** features SkyyRose in "14 Game-Changing Entrepreneurs To Watch In 2023" (Feb 15) | Maxim article |
| 2024 | **San Francisco Post** profile — "From Oakland's Streets to Fashion Heights" (Aug 23) | SF Post article |
| 2024 | **Best of Best Review** awards SkyyRose **Best Bay Area Clothing Line 2024** (Aug 20) | Best of Best article |
| 2024 | **CEO Weekly** profile — "The Unyielding Journey of a Single Father and Entrepreneur" (Oct 22) | CEO Weekly article |
| 2024 | Featured on **The Blox** TV show | CEO Weekly article |
| 2026 | **Kids Capsule** collection launches | Corey 2026-05-13 |

## Timeline copy seeds (for `template-about.php` `$timeline_milestones` array)

Voice register: Corey's bio (`project_founder_voice.md` — declarative fragments, doubled truths, refusal aesthetic, no apology, no urgency theatre).

### 2020 — The Beginning

> Single father in Deep East Oakland. Searching for something his daughter could wear. Nothing fit the eye. He made it himself. The brand carries her name.

### 2021 — Three Chapters Drop

> Black Rose. Love Hurts. Signature. Three collections, one bloodline. Not a launch — a declaration.

### 2023 — National Recognition

> Maxim names Corey Foster one of 14 game-changing entrepreneurs to watch. The work travels past the city limits.

### 2024 — The Year of Receipts

> San Francisco Post profile. Best Bay Area Clothing Line Award. CEO Weekly cover story. The Blox interview. Independent press confirms what Oakland already knew.

### 2026 — The Kids Capsule

> The fourth chapter. Same craftsmanship, smaller silhouettes. Passing the torch on the same terms that built the brand.

## PHP shape (consumed by `template-about.php`)

```php
$timeline_milestones = array(
    array(
        'year'        => '2020',
        'title'       => 'The Beginning',
        'description' => 'Single father in Deep East Oakland. Searching for something his daughter could wear. Nothing fit the eye. He made it himself. The brand carries her name.',
    ),
    array(
        'year'        => '2021',
        'title'       => 'Three Chapters Drop',
        'description' => 'Black Rose. Love Hurts. Signature. Three collections, one bloodline. Not a launch — a declaration.',
    ),
    array(
        'year'        => '2023',
        'title'       => 'National Recognition',
        'description' => 'Maxim names Corey Foster one of 14 game-changing entrepreneurs to watch. The work travels past the city limits.',
    ),
    array(
        'year'        => '2024',
        'title'       => 'The Year of Receipts',
        'description' => 'San Francisco Post profile. Best Bay Area Clothing Line Award. CEO Weekly cover story. The Blox interview. Independent press confirms what Oakland already knew.',
    ),
    array(
        'year'        => '2026',
        'title'       => 'The Kids Capsule',
        'description' => 'The fourth chapter. Same craftsmanship, smaller silhouettes. Passing the torch on the same terms that built the brand.',
    ),
);
```

## Open questions (sharpening)

- Drop **months** for 2021 (sharpens timeline if known: Q1/Q2/Q3/Q4 per collection)
- 2022 milestone? (gap year between drop year and Maxim feature) — production scaling, family event, retail moment?
- 2025 milestone? (gap between award year and Kids Capsule) — site rebuild work? infrastructure? imagery pipeline development?

If both gap years stay empty, the timeline reads naturally — gaps are honest. No scaffold/TODO needed.
