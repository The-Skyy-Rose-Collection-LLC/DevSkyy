<claude-mem-context>

</claude-mem-context>

# Email Flows Skill — Brand Canon Guardrails

## Hard Rules (Enforced in Every Email Output)

### Tagline
Verbatim, with period: **"Luxury Grows from Concrete."**
Never paraphrase. Never drop the period.

### Collection Voice Attribution — Never Mix

| Collection | Color | Hex | Voice register | Forbidden cross-use |
|---|---|---|---|---|
| Black Rose | Silver | `#C0C0C0` | armor, concrete, darkness as beauty, "you already stood up", "concrete answering back" | Do NOT use "bloodline" or crimson register here |
| Love Hurts | Crimson | `#DC143C` | raw emotion, family, bloodline. "Bloodline that raised me" = LOVE HURTS ONLY | Do NOT use this phrase for BR, SIG, or KC |
| Signature | Gold | `#D4AF37` | Bay Area golden hour, "stay golden", warmth, legacy | — |
| Kids Capsule | Rose Gold | `#B76E79` | little royalty, joy, inheritance, next generation | — |

### Products
- Always by NAME in customer-facing copy (resolve from `wordpress-theme/skyyrose-flagship/data/skyyrose-catalog.csv`)
- Never by SKU in customer-facing copy
- `purchased:{sku}` tags are internal identifiers — not customer-facing

### No Cross-Sell
Founder canon (standing, locked): no cross-sell, no "you might also like", no "complete the look", no related products.
Garment is the protagonist. Every email ends at the product, not beyond it.

### No Urgency Timers
No countdown widgets. Urgency lives in copy ("12 left", "closes tonight") — never in JavaScript timers or dynamic countdown embeds.

### No European Luxury House DNA
Visual and copy references = The Five only:
Kith · Oaklandish · Culture Kings · Fear of God · Palm Angels

Never reference: Bottega, Numéro, Hedi Slimane, Rick Owens, 032c, Acne Studios, Givenchy (Tisci era)

### No Hardcoded Discount Codes
`WELCOME10` → `{{ welcome_discount_code }}`
All discount codes generated via Klaviyo's dynamic coupon system. Never a string literal in template copy.

### Oakland Anchor
Brand geography = Oakland. "Bay Area golden hour" references in Signature copy are explicitly approved. Bay Bridge = Oakland (not San Francisco).

## STOP-AND-SHOW (Non-Negotiable)

Before activating any Klaviyo flow, campaign, or sequence that would send real emails:
1. Stop
2. Print: flow name, target segment, estimated recipient count, cost estimate if applicable
3. Wait for explicit `y` from user

Same gate applies to: WooCommerce writes, media uploads, paid API calls.
