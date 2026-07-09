---
name: recipe-card
description: "Creates professional recipe cards with ingredient lists, step-by-step instructions, and scaling calculations. Use when documenting recipes for customers, content, or operations."
allowed-tools: Read Write Glob
metadata:
  author: matthewhitcham
  version: "1.0"
---

# Recipe Card

## When to Use This Skill

Use this skill when you need to:
- Create professional recipe cards for customers, blog content, or social media
- Document restaurant recipes with precise measurements and scaling
- Build recipe cards for cookbooks, e-books, or digital products
- Standardize kitchen recipes for consistency across staff

**DO NOT** use this skill for menu descriptions, nutritional analysis, or meal planning. This is for individual recipe card creation.

---

## Core Principle

A RECIPE CARD MUST BE FOLLOWABLE BY SOMEONE WHO HAS NEVER MADE THE DISH — EVERY MEASUREMENT IS EXACT, EVERY STEP IS ACTIONABLE, AND NOTHING IS ASSUMED.

---

## Phase 1: Brief

### Required Inputs

| Input | What to Ask | Default |
|-------|------------|---------|
| **Recipe name** | "What is the dish called?" | No default — must be provided |
| **Serving size** | "How many servings does this recipe make?" | 4 servings |
| **Skill level** | "Is this for beginners, intermediate, or advanced home cooks?" | Intermediate |
| **Audience** | "Who is this recipe for? Blog readers, restaurant staff, cookbook?" | Home cooks / blog readers |
| **Dietary notes** | "Any dietary labels? Vegetarian, vegan, gluten-free?" | Note if applicable |
| **Scaling needs** | "Should the recipe include scaling for different serving sizes?" | Yes — 2x and 0.5x |

**GATE: Confirm the brief before writing the recipe.**

---

## Phase 2: Structure

### Recipe Card Format

```
## [Recipe Name]

**Yield:** [X] servings
**Prep time:** [X] minutes
**Cook time:** [X] minutes
**Total time:** [X] minutes
**Difficulty:** Easy / Intermediate / Advanced
**Dietary:** [V] [VG] [GF] [DF] (if applicable)

### Description
[2-3 sentences describing the dish, its origin, or why it is special]

### Ingredients
[Organized list with exact measurements]

### Instructions
[Numbered step-by-step]

### Notes
[Tips, substitutions, and storage instructions]

### Scaling
[Adjusted measurements for 2x and 0.5x]
```

**GATE: Confirm the format before writing.**

---

## Phase 3: Write

### Ingredient List Rules

- **List in order of use** — ingredients appear in the order they are used in the instructions
- **Exact measurements** — "1 tablespoon olive oil" not "olive oil" or "some oil"
- **Specify preparation** — "1 onion, diced" not just "1 onion"
- **Group by section** — if the recipe has distinct parts (marinade, sauce, assembly), group ingredients under subheadings
- **Include sizes** — "1 large egg" not "1 egg"; "3 cloves garlic, minced" not "garlic"

### Ingredient Format

```
### Ingredients

**For the marinade:**
- 2 tablespoons soy sauce
- 1 tablespoon sesame oil
- 3 cloves garlic, minced
- 1-inch piece fresh ginger, grated

**For the stir-fry:**
- 1 pound boneless chicken thighs, cut into 1-inch pieces
- 2 tablespoons vegetable oil
- 1 red bell pepper, sliced
- 1 cup broccoli florets
- 2 green onions, sliced (for garnish)
```

### Instruction Writing Rules

- **One action per step** — "Dice the onion. Heat olive oil in a large skillet over medium-high heat." is two steps, not one.
- **Include sensory cues** — "Cook until golden brown, about 3-4 minutes" not just "cook for 4 minutes"
- **Specify heat levels** — "medium-high heat" not "hot"
- **Specify equipment** — "large skillet," "medium saucepan," "sheet pan"
- **Include timing AND visual cues** — time alone is unreliable. "Saute until translucent, about 3 minutes."
- **Number every step**

### Instruction Example

```
### Instructions

1. **Marinate the chicken.** In a medium bowl, combine soy sauce, sesame oil, garlic, and ginger. Add chicken pieces and toss to coat. Refrigerate for at least 15 minutes (up to 2 hours).

2. **Heat the pan.** Heat vegetable oil in a large skillet or wok over high heat until the oil shimmers.

3. **Sear the chicken.** Remove chicken from marinade (reserve marinade). Add chicken to the hot pan in a single layer. Cook without stirring for 2-3 minutes until golden brown on the bottom. Flip and cook 2 more minutes.

4. **Add vegetables.** Add bell pepper and broccoli. Stir-fry for 3-4 minutes until vegetables are crisp-tender and chicken is cooked through (internal temperature 165°F).

5. **Finish and serve.** Pour reserved marinade over the stir-fry. Cook 1 minute until sauce thickens slightly. Remove from heat. Garnish with sliced green onions. Serve immediately over steamed rice.
```

### Notes Section

Include:
- **Storage:** "Store in an airtight container in the refrigerator for up to 3 days. Reheat in a skillet over medium heat."
- **Substitutions:** "Substitute tofu for chicken for a vegetarian version. Use tamari instead of soy sauce for gluten-free."
- **Tips:** "Pat chicken dry before searing for the best browning. Do not overcrowd the pan."
- **Make ahead:** "Marinade can be prepared up to 24 hours in advance."

### Scaling Table

```
### Scaling Guide

| Ingredient | 0.5x (2 servings) | 1x (4 servings) | 2x (8 servings) |
|-----------|-------------------|------------------|------------------|
| Chicken thighs | 0.5 lb | 1 lb | 2 lb |
| Soy sauce | 1 tbsp | 2 tbsp | 4 tbsp (¼ cup) |
| Sesame oil | 1.5 tsp | 1 tbsp | 2 tbsp |
| Garlic | 2 cloves | 3 cloves | 6 cloves |
```

---

## Phase 4: Polish

### 1. Photography Notes

If the recipe will be published with a photo:
- Suggest plating style and garnish
- Recommend the best angle (overhead for flat dishes, 45° for tall dishes)
- Note any photo-worthy moments during cooking (steam, pour, garnish)

### 2. SEO Notes (for blog recipes)

- Use the recipe name in the H1 and first paragraph
- Write a 100-word intro before the recipe card (personal story or tips)
- Include structured data (Recipe schema) for search engines
- Target keywords: "[dish name] recipe," "easy [dish name]," "how to make [dish name]"

### 3. Quality Checklist

```
## Recipe Card Checklist

- [ ] Recipe name, yield, and timing are clearly stated
- [ ] Ingredients listed in order of use with exact measurements
- [ ] Preparation details included for each ingredient (diced, minced, etc.)
- [ ] Each instruction step has one action
- [ ] Sensory cues paired with timing (golden brown, 3-4 minutes)
- [ ] Heat levels and equipment specified
- [ ] Notes include storage, substitutions, and tips
- [ ] Scaling guide provided for at least 2 variations
- [ ] Dietary labels included if applicable
- [ ] Recipe tested and confirmed to produce the stated result
```

---

## Example

**Recipe card excerpt:**

```
## Honey Garlic Salmon

**Yield:** 4 servings | **Prep:** 10 min | **Cook:** 15 min | **Total:** 25 min
**Difficulty:** Easy | **Dietary:** GF, DF

### Description
Crispy-skinned salmon fillets glazed with a sticky honey garlic sauce. Ready in 25 minutes — perfect for a weeknight dinner that looks like you spent an hour.

### Ingredients
- 4 salmon fillets (6 oz each), skin-on, patted dry
- 1 tablespoon olive oil
- Salt and black pepper to taste
- 3 tablespoons honey
- 2 tablespoons soy sauce (use tamari for GF)
- 4 cloves garlic, minced
- 1 tablespoon fresh lemon juice
- 1 teaspoon sesame seeds (for garnish)
```

---

## Anti-Patterns

- **Assumed knowledge** — "Cook until done" assumes the reader knows what "done" looks like. Describe the visual, aural, and temperature cues.
- **Imprecise measurements** — "A handful of herbs" varies by hand size. Use tablespoons or cups.
- **Multiple actions per step** — "Dice the onion, mince the garlic, and heat the pan" is three steps crammed into one.
- **No timing or visual cues** — "Cook the sauce" for how long? Until it does what? Always include both.
- **Untested recipes** — publishing a recipe you have not made produces frustrated cooks and angry comments. Test every recipe.

---

## Recovery

- **Recipe is too long:** Split into sub-recipes (e.g., "Make the sauce" and "Cook the protein") or offer a quick version with fewer steps.
- **Reader reports different results:** Check altitude, equipment, and ingredient brand differences. Add troubleshooting notes.
- **Scaling produces odd measurements:** Round to the nearest practical measurement. "2.5 tablespoons" becomes "2 tablespoons plus 1.5 teaspoons."
- **Dietary substitutions are requested:** Add a substitutions section covering the top 3 dietary modifications (dairy-free, gluten-free, vegetarian).
