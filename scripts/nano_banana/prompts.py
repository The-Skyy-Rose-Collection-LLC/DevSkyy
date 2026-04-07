"""Prompt templates and logo treatment metadata.

All prompts take product dict so the model knows EXACTLY what garment
it's rendering, which collection it belongs to, and what branding to expect.

Brand DNA: SkyyRose is Oakland luxury streetwear. Dark, cinematic, raw.
Not generic e-commerce — every render should feel editorial.
"""

from __future__ import annotations

# -- Anti-hallucination constraints (appended to every prompt) ----------------

ANTI_HALLUCINATION = (
    "\n\nSTRICT RULES — NON-NEGOTIABLE:\n"
    "- Render ONLY the side specified (front or back). Never show both sides.\n"
    "- Do NOT add text, logos, patches, or branding absent from the reference.\n"
    "- Do NOT invent pockets, panels, zippers, or details not in the reference.\n"
    "- Do NOT change the garment type, silhouette, or cut.\n"
    "- Do NOT add sponsor logos, team names, league marks, or athlete names.\n"
    "- Do NOT alter colors — match hex values from the reference exactly.\n"
    "- If a detail is unclear in the reference, leave it out — never guess.\n"
    "- This is a luxury fashion brand. Accuracy is the only standard."
)

ENHANCED_SUFFIX = (
    " CRITICAL: The item MUST be pixel-accurate to the reference. "
    "Do not change any colors, patterns, logos, or design elements. "
    "This is a luxury fashion brand — accuracy is everything." + ANTI_HALLUCINATION
)

# -- Collection lighting profiles --------------------------------------------
# Each collection has a distinct visual identity that shows even in flat shots.

COLLECTION_LIGHTING = {
    "black-rose": {
        "bg": "Deep matte black (#0A0A0A) backdrop with subtle charcoal gradient",
        "light": "Cool silver key light from upper-left, black fill, thin silver rim light creating metallic edge highlights",
        "mood": "Dark, authoritative, monochrome luxury — the garment commands the frame",
        "shadow": "Deep pooling shadow beneath, barely visible floor plane",
    },
    "love-hurts": {
        "bg": "Rich black (#0A0A0A) backdrop with barely perceptible crimson warmth in the shadows",
        "light": "Warm dramatic key light upper-left with subtle crimson gel, dark fill, strong rim light for edge separation",
        "mood": "Emotionally charged, intimate, the fabric tells a story",
        "shadow": "Soft directional shadow, warm-toned edges",
    },
    "signature": {
        "bg": "Warm charcoal (#1A1A1A) fading to deep black, hint of golden hour warmth",
        "light": "Golden-warm key light upper-left, soft neutral fill, warm rim light creating a premium glow",
        "mood": "Refined, approachable luxury — the everyday elevated",
        "shadow": "Clean soft shadow, subtle warm floor reflection",
    },
    "kids-capsule": {
        "bg": "Clean dark gray (#1C1C1C) with subtle warmth",
        "light": "Bright but not flat — angled key light, soft fill, playful rim highlights",
        "mood": "Premium and confident — scaled down, never dumbed down",
        "shadow": "Crisp shadow, energetic composition",
    },
}


# -- View prompts -------------------------------------------------------------

def front_prompt(product: dict) -> str:
    """Build a front-view product shot prompt with collection-specific styling."""
    name = product["name"]
    collection = product["collection"]
    sku = product.get("sku", "")
    lighting = COLLECTION_LIGHTING.get(collection, COLLECTION_LIGHTING["black-rose"])
    treatment = LOGO_TREATMENTS.get(sku, "")

    branding_note = ""
    if treatment:
        branding_note = (
            f"\n\nBRANDING DETAIL: The real product has: {treatment}. "
            "Reproduce this branding EXACTLY as described — correct position, correct material finish, correct colors."
        )

    return (
        f"Generate a photorealistic luxury e-commerce product render of this {name} — FRONT VIEW ONLY.\n"
        f"The provided image is the source tech flat. Study every stitch, color, and logo placement.\n\n"
        f"VIEW: Show ONLY the front panel. Do NOT render the back.\n\n"
        f"PRESENTATION:\n"
        f"- No model, no person, no mannequin. Garment floating on an invisible form with natural 3D shape and drape.\n"
        f"- {lighting['bg']}.\n"
        f"- {lighting['light']}.\n"
        f"- {lighting['mood']}.\n"
        f"- {lighting['shadow']}.\n"
        f"- Fabric texture must be photorealistic — visible weave, thread weight, material sheen.\n\n"
        f"FIDELITY: Match the reference EXACTLY — same colors, text, numbers, "
        f"logo placement, panels, stripes. Change NOTHING.{branding_note}" + ANTI_HALLUCINATION
    )


def back_prompt(product: dict) -> str:
    """Build a back-view product shot prompt with collection-specific styling."""
    name = product["name"]
    collection = product["collection"]
    sku = product.get("sku", "")
    lighting = COLLECTION_LIGHTING.get(collection, COLLECTION_LIGHTING["black-rose"])
    treatment = LOGO_TREATMENTS.get(sku, "")

    branding_note = ""
    if treatment and "back" in treatment.lower():
        back_detail = treatment.split("back:")[-1].strip() if "back:" in treatment.lower() else treatment
        branding_note = (
            f"\n\nBACK BRANDING: {back_detail}. "
            "Reproduce the back branding EXACTLY."
        )

    return (
        f"Generate a photorealistic luxury e-commerce product render of this {name} — BACK VIEW ONLY.\n"
        f"The provided image is the back-panel tech flat. Reproduce every detail exactly.\n\n"
        f"VIEW: Show ONLY the back panel. Garment facing away from camera.\n\n"
        f"PRESENTATION:\n"
        f"- No model, no person, no mannequin. Garment floating on invisible form, back-facing, full 3D drape.\n"
        f"- {lighting['bg']}.\n"
        f"- {lighting['light']}.\n"
        f"- Fabric texture must be photorealistic.\n\n"
        f"FIDELITY: Match the back reference exactly.{branding_note}" + ANTI_HALLUCINATION
    )


def accessory_prompt(product: dict) -> str:
    """Build a prompt for accessories (beanies, fanny packs, etc.)."""
    name = product["name"]
    collection = product["collection"]
    sku = product.get("sku", "")
    lighting = COLLECTION_LIGHTING.get(collection, COLLECTION_LIGHTING["signature"])
    treatment = LOGO_TREATMENTS.get(sku, "")

    branding_note = ""
    if treatment:
        branding_note = f"\n\nBRANDING: {treatment}. Reproduce exactly."

    return (
        f"Generate a photorealistic luxury product render of this {name} — HERO ANGLE.\n"
        f"The provided image is the source reference. Reproduce every detail exactly.\n\n"
        f"PRESENTATION:\n"
        f"- No model. Product only, slightly angled for dimension.\n"
        f"- {lighting['bg']}.\n"
        f"- {lighting['light']}.\n"
        f"- Tight framing — the accessory fills the frame.\n\n"
        f"FIDELITY: Match the reference exactly.{branding_note}" + ANTI_HALLUCINATION
    )


# -- Branding (lifestyle) prompts per collection ------------------------------
# These are editorial shots — models wearing the product in a brand-aligned environment.
# The key is OAKLAND AUTHENTICITY, not generic fashion photography.

BRANDING_TEMPLATES = {
    "black-rose": (
        "The reference image shows a {name}. Generate a fashion editorial photo:\n\n"
        "MODEL: Confident, diverse model wearing this EXACT {name}. The garment must be "
        "100%% identical to the reference — every logo, color, panel, stitch.\n\n"
        "SETTING: Oakland industrial — concrete walls, steel beams, raw textures. "
        "Night. The only light is silver-toned spotlights carving the model from darkness. "
        "This is where luxury grows from concrete.\n\n"
        "LIGHTING: Dramatic chiaroscuro. Hard silver key light, deep black shadows. "
        "No color — only silver (#C0C0C0) tones. The darkness is the point.\n\n"
        "MOOD: Quiet authority. This person doesn't announce themselves — they command "
        "presence the way Oakland taught them. Unshakable.\n\n"
        "COMPOSITION: 3/4 body shot, cinematic aspect ratio. "
        "Slight dutch angle. Film grain. The garment is the hero.{treatment_note}"
    ),
    "love-hurts": (
        "The reference image shows a {name}. Generate a fashion editorial photo:\n\n"
        "MODEL: Confident, diverse model wearing this EXACT {name}. The garment must be "
        "100%% identical to the reference.\n\n"
        "SETTING: Raw emotional space — cracked concrete, weathered brick, "
        "a single red neon glow in the background. Oakland at 2 AM. "
        "This collection is named after the founder's family name — it's personal.\n\n"
        "LIGHTING: Warm dramatic — deep crimson (#DC143C) accent light from one side, "
        "hard shadows on the other. The light catches the branding. Vulnerable but strong.\n\n"
        "MOOD: Pain transformed into beauty. Vulnerability as strength. "
        "The model wears their scars like armor.\n\n"
        "COMPOSITION: 3/4 body, cinematic. Close enough to see the fabric. "
        "The emotion is in the details.{treatment_note}"
    ),
    "signature": (
        "The reference image shows a {name}. Generate a fashion editorial photo:\n\n"
        "MODEL: Confident, diverse model wearing this EXACT {name}. The garment must be "
        "100%% identical to the reference.\n\n"
        "SETTING: Oakland golden hour — Bay Bridge or city skyline in soft focus background. "
        "Warm pavement, late afternoon sun. This is where it all started — a father "
        "with a daughter's name and a refusal to quit.\n\n"
        "LIGHTING: Golden hour warmth — rich amber key light, soft gold (#D4AF37) tones. "
        "Natural, elevated, the everyday made extraordinary.\n\n"
        "MOOD: Understated confidence. Not shouting — just built different. "
        "The foundation wardrobe for someone who already knows who they are.\n\n"
        "COMPOSITION: 3/4 body, warm cinematic. Bay Area light. "
        "The gold in the fabric catches the sun.{treatment_note}"
    ),
    "kids-capsule": (
        "The reference image shows a {name}. Generate a fashion editorial photo:\n\n"
        "MODEL: CHILD model (age 8-12) wearing this EXACT {name}. 100%% identical "
        "to reference. This child carries themselves with confidence.\n\n"
        "SETTING: Clean Oakland street — mural wall or playground with premium feel. "
        "No pastels, no cartoons. Real streetwear scaled down, not dumbed down.\n\n"
        "LIGHTING: Bright but cinematic — the child stands in a pool of warm light. "
        "Premium energy, playful confidence.\n\n"
        "MOOD: Legacy. This brand is named after the founder's daughter, Skyy Rose. "
        "Kids Capsule is the promise made real.\n\n"
        "COMPOSITION: 3/4 body, eye-level with the child. Respectful, powerful.{treatment_note}"
    ),
}

ACCESSORY_BRANDING_TEMPLATES = {
    "love-hurts": (
        "The reference image shows a {name}. Display this EXACT {name} in a "
        "moody Oakland editorial — cracked concrete surface, single crimson accent light, "
        "deep shadows. Raw emotion. 100%% identical to reference. "
        "Cinematic product photography. The accessory tells the story.{treatment_note}"
    ),
    "signature": (
        "The reference image shows a {name}. Display this EXACT {name} in a "
        "golden hour Oakland editorial — warm pavement, Bay Area light, subtle gold tones. "
        "100%% identical to reference. Premium product photography. "
        "Everyday luxury.{treatment_note}"
    ),
}


# -- Composite prompts --------------------------------------------------------

def composite_prompt(name: str, sku: str, view: str = "front") -> str:
    """Build a prompt for compositing real branding onto an AI lifestyle shot."""
    treatment = LOGO_TREATMENTS.get(sku, "")
    treatment_note = f" The real product's logo/branding is {treatment}." if treatment else ""
    return (
        f"I am providing TWO images. "
        f"IMAGE 1 (the AI render): A professional fashion photo of a model wearing a {name}. "
        f"Keep this composition, pose, lighting, and background. "
        f"IMAGE 2 (the REAL product): The actual {name} showing the TRUE logo.{treatment_note} "
        f"YOUR TASK: Generate a new image keeping the EXACT same model, pose, and background "
        f"from Image 1 — but correct the garment's logo/branding to match Image 2 exactly. "
        f"Study the logo closely: light interaction, shadows, raised/flat, glossy/matte finish. "
        f"Reproduce these visual properties exactly. Only the garment branding changes."
    )


# -- FLUX prompts (text-to-image, no reference) -------------------------------

def flux_prompt(name: str, view: str, source_desc: str = "") -> str:
    """Build a FLUX prompt for converting tech flats to photorealistic shots."""
    view_label = {
        "front": "FRONT VIEW", "back": "BACK VIEW", "branding": "cinematic editorial shot",
    }.get(view, "FRONT VIEW")

    base = f"Professional luxury product photography of a {name} on invisible ghost mannequin, {view_label}. "
    if source_desc:
        base += f"{source_desc} "

    if "branding" in view:
        base += (
            "Oakland industrial setting — concrete walls, dramatic silver spotlights, "
            "deep black shadows. Gothic luxury. Cinematic composition, slight floor reflection. "
        )
    else:
        base += (
            "Deep matte black (#0A0A0A) studio background. "
            "Silver key light upper-left, dark fill, thin rim light for metallic edge highlights. "
            "Luxury fashion photography — the garment commands the frame. "
        )

    base += "Photorealistic fabric texture with natural 3D shape and drape. All text and logos perfectly legible."
    return base


# -- Prompt router ------------------------------------------------------------

def get_prompt(product: dict, view: str) -> str:
    """Select the right prompt for a product + view combination."""
    name = product["name"]
    collection = product["collection"]
    sku = product.get("sku", "")
    is_accessory = product.get("is_accessory", False)

    if view == "branding":
        treatment = LOGO_TREATMENTS.get(sku, "")
        treatment_note = f"\n\nBRANDING TO PRESERVE: {treatment}" if treatment else ""

        if is_accessory:
            tpl = ACCESSORY_BRANDING_TEMPLATES.get(
                collection,
                BRANDING_TEMPLATES.get(collection, BRANDING_TEMPLATES["black-rose"]),
            )
            return tpl.format(name=name, treatment_note=treatment_note) + ANTI_HALLUCINATION
        tpl = BRANDING_TEMPLATES.get(collection, BRANDING_TEMPLATES["black-rose"])
        return tpl.format(name=name, treatment_note=treatment_note) + ANTI_HALLUCINATION

    if is_accessory:
        return accessory_prompt(product)
    if view == "front":
        return front_prompt(product)
    return back_prompt(product)


# -- Logo treatment metadata --------------------------------------------------
# Describes the REAL material treatment for each product's branding.
# Used by front/back prompts AND composite step.

LOGO_TREATMENTS = {
    # -- Black Rose Collection --
    "br-001": "front chest center (~10 in): ROSE-ONLY logo — 3D dimensional rose, layered spiral petals, curved stem with two broad leaves, brushed rose-gold metallic; embossed into fabric",
    "br-002": "left thigh: ROSE-ONLY logo as silicone patch — glossy smooth finish, die-cut edges, rose-gold metallic",
    "br-003": "front: 'BLACK IS BEAUTIFUL' bold block text in white/gold; back: large ROSE-ONLY embroidered logo",
    "br-003-oakland": "front: 'BLACK IS BEAUTIFUL' — letter A in 'BLACK' is black, rest gold; back: ROSE-ONLY embroidered",
    "br-003-giants": "front: 'BLACK IS BEAUTIFUL' in orange/black Giants colorway; back: ROSE-ONLY embroidered",
    "br-003-white": "front: 'BLACK IS BEAUTIFUL' in black on white; back: ROSE-ONLY embroidered",
    "br-004": "front chest center: ROSE-ONLY embroidered in rose-gold thread, raised texture",
    "br-005": "right chest: small ROSE-ONLY silicone cutout patch (~3 in); LEFT SIDE of hoodie body (not sleeve): large ROSE-ONLY embroidered (~8 in); hood lining: all-over sublimated rose pattern",
    "br-006": "left chest: ROSE-ONLY embroidered (~5 in); back: large ROSE-ONLY embroidered (~12 in), rose-gold thread",
    "br-007": "front waistband: tackle-twill 'OAKLAND'; throughout: sublimated ROSE-ONLY repeating",
    "br-008": "football jersey #80 — front digit '8' has rose-gold rose fill, '0' plain white; back reversed",
    "br-009": "football jersey #32 — front digit '3' has rose-gold rose fill, '2' plain white; back reversed",
    "br-010": "front chest: 'THE BAY' bold gold text; below: circular ROSE-ONLY in rose-gold; lower half: grey/silver gradient",
    "br-011": "hooded hockey jersey teal — front: large circular rose crest; back: 'BLACK IS BEAUTIFUL' cyan text + rose-filled #0",
    "br-012": "button-front baseball jersey, dark green (#1A3C2A) with gold (#D4AF37) piping and trim; front: 'BLACK IS BEAUTIFUL' arched text in gold with 'A' in black; small SkyyRose woven label at lower hem; back: large ROSE-ONLY embroidered in grey/silver with gold clouds at base, SR monogram at upper back in gold",
    # -- Love Hurts Collection --
    "lh-002": "left thigh: LOVE HURTS HEART GRAPHIC — cracked red heart in thorny branches, three roses, blood-splash drips",
    "lh-003": "throughout: sublimated LOVE HURTS HEART GRAPHIC; left panel: large LOVE HURTS WORDMARK",
    "lh-004": "front chest: LOVE HURTS WORDMARK red graffiti; inside hood: sublimated heart graphic; back: large heart graphic",
    "lh-006": "front face: LOVE HURTS HEART GRAPHIC — cracked heart, thorny branches, three roses, blood-splash",
    # -- Signature Collection --
    "sg-001": "entire shorts: sublimated Bay Bridge panorama; hem: ROSE-ONLY embroidered in blue thread",
    "sg-002": "front chest: ROSE-ONLY embroidered (~6 in) gold thread; within petals: Golden Gate Bridge imagery",
    "sg-003": "entire shorts: sublimated Golden Gate Bridge panorama; hem: ROSE-ONLY in purple thread",
    "sg-004": "front chest: SR MONOGRAM + ROSE embroidered rose-gold (~5 in); back neck: SR MONOGRAM gold",
    "sg-005": "white crewneck tee; front chest center (~9 in): stylized rose with Bay Bridge imagery visible inside petals, blue/teal coloring, blue clouds at base; back collar: SR monogram in black",
    "sg-006": "front chest: ROSE-ONLY in lavender thread (~6 in) on mint/lavender colorblock",
    "sg-007": "brim: ROSE-ONLY silicone patch (~2 in); three colorways: rose-gold, grey-black, purple",
    "sg-009": "black nylon shell zip-front jacket with white sherpa lining visible when opened; left chest (~3 in): small ROSE-ONLY embroidered in red/green (red petals, green leaves, grey clouds at base); SkyyRose woven label inside collar; NOT a hooded jacket — collar only",
    "sg-011": "front chest: THE SKYROSE COLLECTION SCRIPT gold foil — 'THE' serifed caps, 'Skyy Rose' cursive, 'Collection' spaced caps",
    "sg-012": "front chest: THE SKYROSE COLLECTION SCRIPT gold foil on orchid fabric",
    "sg-013": "front chest: ROSE-ONLY embroidered lavender (~6 in); back neck: SR MONOGRAM gold",
    "sg-014": "left thigh: ROSE-ONLY embroidered lavender (~4 in) on mint/lavender colorblock",
    # -- Kids Capsule --
    "kids-001": "left chest + left thigh: ROSE-ONLY embroidered black on red; right sleeve: circular woven patch",
    "kids-002": "left chest + left thigh: ROSE-ONLY embroidered black on purple; right sleeve: circular woven patch",
}
