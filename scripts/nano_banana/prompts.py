"""Prompt templates and logo treatment metadata.

All prompts are functions that take the product name so the model
knows EXACTLY what garment it's rendering.
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


# -- View prompts -------------------------------------------------------------


def front_prompt(name: str) -> str:
    return (
        f"Generate a photorealistic e-commerce product render of this {name} — FRONT VIEW ONLY.\n"
        "The provided image is the source tech flat. Reproduce every detail exactly.\n\n"
        "VIEW: Show ONLY the front panel. Do NOT render the back.\n\n"
        "PRESENTATION: No model, no person, no mannequin. "
        "Garment floating naturally on an invisible form, full 3D shape and drape. "
        "Clean white/light gray studio background, subtle floor shadow. "
        "Professional e-commerce lighting — soft key light upper-left, fill right, rim light.\n\n"
        "FIDELITY: Match the reference exactly — same colors, text, numbers, "
        "logo placement, panels, stripes. Change NOTHING." + ANTI_HALLUCINATION
    )


def back_prompt(name: str) -> str:
    return (
        f"Generate a photorealistic e-commerce product render of this {name} — BACK VIEW ONLY.\n"
        "The provided image is the back-panel tech flat. Reproduce every detail exactly.\n\n"
        "VIEW: Show ONLY the back panel. Garment facing away from camera.\n\n"
        "PRESENTATION: No model, no person, no mannequin. "
        "Garment floating on an invisible form, back-facing, full 3D drape. "
        "Clean white/light gray studio background. Professional lighting.\n\n"
        "FIDELITY: Match the back reference exactly." + ANTI_HALLUCINATION
    )


def accessory_prompt(name: str) -> str:
    return (
        f"Generate a photorealistic e-commerce product render of this {name} — FRONT VIEW.\n"
        "The provided image is the source reference. Reproduce every detail exactly.\n\n"
        "PRESENTATION: No model, no person. Clean white/light gray studio background. "
        "Professional product photography lighting.\n\n"
        "FIDELITY: Match the reference exactly." + ANTI_HALLUCINATION
    )


# -- Branding (lifestyle) prompts per collection ------------------------------

BRANDING_TEMPLATES = {
    "black-rose": (
        "The reference image shows a {name}. Generate a fashion model wearing "
        "this EXACT {name} in a dark, moody editorial setting — black marble, "
        "dramatic shadows, rose gold accent lighting. Gothic luxury. "
        "The {name} must be 100% identical to the reference. "
        "Deep blacks, dramatic contrast. Rose gold (#B76E79) tones. "
        "Cinematic composition, 3/4 body shot."
    ),
    "love-hurts": (
        "The reference image shows a {name}. Generate a fashion model wearing "
        "this EXACT {name} in a passionate, romantic editorial setting — red "
        "roses, velvet textures, warm dramatic lighting. 100% identical to reference. "
        "Rich reds, deep burgundy. Luxury castle backdrop. "
        "Cinematic composition, 3/4 body shot."
    ),
    "signature": (
        "The reference image shows a {name}. Generate a fashion model wearing "
        "this EXACT {name} in a Bay Area urban editorial — golden hour light, "
        "city skyline or Golden Gate Bridge silhouette. 100% identical to reference. "
        "Warm golden tones, California luxury. Gold (#D4AF37) accent lighting. "
        "Cinematic composition, 3/4 body shot."
    ),
    "kids-capsule": (
        "The reference image shows a {name}. Generate a CHILD model (age 8-12) "
        "wearing this EXACT {name}, front-facing, playful yet premium editorial. "
        "Bright studio lighting, clean background. 100% identical to reference. "
        "Vibrant, youthful energy with luxury quality. 3/4 body shot."
    ),
}

ACCESSORY_BRANDING_TEMPLATES = {
    "love-hurts": (
        "The reference image shows a {name}. Display this EXACT {name} in a "
        "passionate, romantic editorial — red roses, velvet, warm lighting. "
        "100% identical to reference. Cinematic product photography."
    ),
    "signature": (
        "The reference image shows a {name}. Display this EXACT {name} in a "
        "Bay Area urban editorial — golden hour, warm golden tones. "
        "100% identical to reference. Premium product photography."
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
        "front": "FRONT VIEW",
        "back": "BACK VIEW",
        "branding": "cinematic editorial shot",
    }.get(view, "FRONT VIEW")

    base = f"Professional e-commerce product photography of a {name} on an invisible ghost mannequin, {view_label}. "
    if source_desc:
        base += f"{source_desc} "

    if "branding" in view:
        base += (
            "Dark moody studio — black marble, dramatic shadows, rose gold (#B76E79) "
            "accent lighting. Gothic luxury. Cinematic composition, slight floor reflection. "
        )
    else:
        base += (
            "Light gray (#E8E8E8) studio background with subtle floor reflection. "
            "Professional product photography lighting — soft key upper-left, fill right, rim light. "
        )

    base += "Photorealistic fabric texture with natural 3D shape and drape. All text and logos perfectly legible."
    return base


# -- Prompt router ------------------------------------------------------------


def get_prompt(product: dict, view: str) -> str:
    """Select the right prompt for a product + view combination."""
    name = product["name"]
    collection = product["collection"]
    is_accessory = product["is_accessory"]

    if view == "branding":
        if is_accessory:
            tpl = ACCESSORY_BRANDING_TEMPLATES.get(
                collection, BRANDING_TEMPLATES.get(collection, BRANDING_TEMPLATES["black-rose"])
            )
            return tpl.format(name=name)
        return BRANDING_TEMPLATES.get(collection, BRANDING_TEMPLATES["black-rose"]).format(
            name=name
        )

    if is_accessory:
        return accessory_prompt(name)
    if view == "front":
        return front_prompt(name)
    return back_prompt(name)


# -- Logo treatment metadata --------------------------------------------------
# Describes the REAL material treatment for each product's branding.
# Used by composite step to tell the model what the logo actually looks like.

LOGO_TREATMENTS = {
    # -- Black Rose Collection --
    "br-001": "front chest center (~10 in): ROSE-ONLY logo — 3D dimensional rose, layered spiral petals, curved stem with two broad leaves, brushed rose-gold metallic; embossed into fabric",
    "br-002": "left thigh: ROSE-ONLY logo as silicone patch — glossy smooth finish, die-cut edges, rose-gold metallic",
    "br-003": "front: 'BLACK IS BEAUTIFUL' bold block text in white/gold; back: large ROSE-ONLY embroidered logo",
    "br-003-oakland": "front: 'BLACK IS BEAUTIFUL' — letter A in 'BLACK' is black, rest gold; back: ROSE-ONLY embroidered",
    "br-003-giants": "front: 'BLACK IS BEAUTIFUL' in orange/black Giants colorway; back: ROSE-ONLY embroidered",
    "br-003-white": "front: 'BLACK IS BEAUTIFUL' in black on white; back: ROSE-ONLY embroidered",
    "br-004": "front chest center: ROSE-ONLY embroidered in rose-gold thread, raised texture",
    "br-005": "right chest: ROSE-ONLY silicone patch; left body panel: ROSE-ONLY embroidered",
    "br-006": "left chest: ROSE-ONLY embroidered (~5 in); back: large ROSE-ONLY embroidered (~12 in), rose-gold thread",
    "br-007": "front waistband: tackle-twill 'OAKLAND'; throughout: sublimated ROSE-ONLY repeating",
    "br-008": "football jersey #80 — front digit '8' has rose-gold rose fill, '0' plain white; back reversed",
    "br-009": "football jersey #32 — front digit '3' has rose-gold rose fill, '2' plain white; back reversed",
    "br-010": "front chest: 'THE BAY' bold gold text; below: circular ROSE-ONLY in rose-gold; lower half: grey/silver gradient",
    "br-011": "hooded hockey jersey teal — front: large circular rose crest; back: 'BLACK IS BEAUTIFUL' cyan text + rose-filled #0",
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
    "sg-005": "front chest: ROSE-ONLY embroidered navy/gold; within petals: Bay Bridge imagery",
    "sg-006": "front chest: ROSE-ONLY in lavender thread (~6 in) on mint/lavender colorblock",
    "sg-007": "brim: ROSE-ONLY silicone patch (~2 in); three colorways: rose-gold, grey-black, purple",
    "sg-009": "front chest: ROSE-ONLY embroidered (~5 in) red thread on cream sherpa",
    "sg-011": "front chest: THE SKYROSE COLLECTION SCRIPT gold foil — 'THE' serifed caps, 'Skyy Rose' cursive, 'Collection' spaced caps",
    "sg-012": "front chest: THE SKYROSE COLLECTION SCRIPT gold foil on orchid fabric",
    "sg-013": "front chest: ROSE-ONLY embroidered lavender (~6 in); back neck: SR MONOGRAM gold",
    "sg-014": "left thigh: ROSE-ONLY embroidered lavender (~4 in) on mint/lavender colorblock",
    # -- Kids Capsule --
    "kids-001": "left chest + left thigh: ROSE-ONLY embroidered black on red; right sleeve: circular woven patch",
    "kids-002": "left chest + left thigh: ROSE-ONLY embroidered black on purple; right sleeve: circular woven patch",
}
