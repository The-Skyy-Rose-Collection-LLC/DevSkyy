from unittest.mock import MagicMock, patch

from skyyrose.elite_studio.agents.prompt_enrichment_agent import PromptEnrichmentAgent


def _mock_catalog(sku: str, name: str, branding: str, collection: str = "black-rose"):
    product = MagicMock()
    product.name = name
    product.branding_summary = branding
    product.collection = collection
    catalog = MagicMock()
    catalog.require.return_value = product
    return catalog


def test_prompt_contains_spec_primacy():
    """Enriched prompt must include the spec-wins-over-reference instruction."""
    agent = PromptEnrichmentAgent()
    with patch("skyyrose.elite_studio.agents.prompt_enrichment_agent.Catalog") as MockCat:
        MockCat.load.return_value = _mock_catalog(
            "br-004", "BLACK Rose Hoodie", "SR monogram right chest"
        )
        result = agent.enrich(
            sku="br-004", vision_spec="black hoodie with rose motif", style="ghost_mannequin"
        )
    assert result.success
    assert (
        "spec is authoritative" in result.enriched_spec.lower()
        or "branding block" in result.enriched_spec.lower()
    )


def test_prompt_contains_ghost_mannequin_instructions():
    """Ghost-mannequin style must produce invisible-mannequin photography instructions."""
    agent = PromptEnrichmentAgent()
    with patch("skyyrose.elite_studio.agents.prompt_enrichment_agent.Catalog") as MockCat:
        MockCat.load.return_value = _mock_catalog(
            "br-004", "BLACK Rose Hoodie", "SR monogram right chest"
        )
        result = agent.enrich(sku="br-004", vision_spec="black hoodie", style="ghost_mannequin")
    prompt = result.enriched_spec.lower()
    assert "ghost mannequin" in prompt or "invisible mannequin" in prompt or "hollow man" in prompt


def test_prompt_reads_branding_from_csv():
    """branding_spec from CSV must appear verbatim in the enriched prompt."""
    agent = PromptEnrichmentAgent()
    with patch("skyyrose.elite_studio.agents.prompt_enrichment_agent.Catalog") as MockCat:
        MockCat.load.return_value = _mock_catalog(
            "sg-013",
            "Mint & Lavender Crewneck",
            "black-roses-cloud-cluster embroidered front center lavender + back of neck 1.5in lavender",
        )
        result = agent.enrich(sku="sg-013", vision_spec="mint crewneck", style="ghost_mannequin")
    assert "black-roses-cloud-cluster" in result.enriched_spec


def test_flat_lay_style_no_ghost_mannequin_instructions():
    """flat_lay style must NOT include ghost-mannequin instructions."""
    agent = PromptEnrichmentAgent()
    with patch("skyyrose.elite_studio.agents.prompt_enrichment_agent.Catalog") as MockCat:
        MockCat.load.return_value = _mock_catalog("br-004", "BLACK Rose Hoodie", "SR monogram")
        result = agent.enrich(sku="br-004", vision_spec="black hoodie", style="flat_lay")
    prompt = result.enriched_spec.lower()
    assert "ghost mannequin" not in prompt and "invisible mannequin" not in prompt
