from skyyrose.core.dossier_loader import parse_dossier_markdown

_DOSSIER = """---
sku: br-006
name: Black Rose Bomber Sherpa
collection: black-rose
reference_image: product-references/br-006-real-front.jpg
extra_references:
  - product-references/br-006-real-back.jpg
---
**Garment type lock:** bomber jacket
## Branding
- region: chest
## Negative
- no extra logos
"""


def test_dossier_carries_reference_image_and_extras():
    d = parse_dossier_markdown(_DOSSIER)
    assert d.reference_image == "product-references/br-006-real-front.jpg"
    assert d.extra_references == ["product-references/br-006-real-back.jpg"]
