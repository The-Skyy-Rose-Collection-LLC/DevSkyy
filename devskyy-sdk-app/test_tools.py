"""Offline checks for the catalog tools and agent wiring.

These run WITHOUT contacting the Claude API — they call the tool handlers directly and
construct the agent options, which is enough to catch import errors, schema typos, and
broken handler logic for free. Run with:  python test_tools.py
(or `pytest test_tools.py` if you add pytest.)

We do NOT call query() here: that spawns the agent and makes a billed API call.
"""

from __future__ import annotations

import asyncio

from catalog import find_products, products_in_collection

from tools import catalog_server, collection_canon, list_collection, lookup_product

# `@tool` returns an SdkMcpTool dataclass, not the raw function. The async handler is `.handler`;
# that's what the SDK invokes by tool name. We call it directly here to test the logic offline.
lookup_handler = lookup_product.handler
list_handler = list_collection.handler
canon_handler = collection_canon.handler


def _text(result: dict) -> str:
    """Pull the concatenated text out of a tool result's content blocks."""
    return "\n".join(b["text"] for b in result["content"] if b["type"] == "text")


async def _checks() -> None:
    # --- catalog layer -------------------------------------------------------
    assert find_products("br-001"), "exact SKU lookup should find a product"
    assert find_products("rose"), "keyword 'rose' should match at least one product"
    assert find_products("nope-404") == [], "unknown query returns empty list"
    assert products_in_collection("Love Hurts"), "Love Hurts should have products"
    assert products_in_collection("Nonexistent") == [], "bad collection returns empty list"

    # --- lookup_product tool -------------------------------------------------
    hit = await lookup_handler({"query": "br-001"})
    assert "br-001" in _text(hit) and not hit.get("is_error"), hit
    assert "$320.00" in _text(hit), "price must be quoted exactly"

    miss = await lookup_handler({"query": "zzz"})
    assert "No products matched" in _text(miss), miss
    assert not miss.get("is_error"), "a clean no-match is data, not an error"

    empty = await lookup_handler({"query": "   "})
    assert empty.get("is_error") is True, "empty query is a usage error"

    # --- list_collection tool ------------------------------------------------
    coll = await list_handler({"collection": "love hurts"})  # case-insensitive
    coll_text = _text(coll)
    assert "Love Hurts" in coll_text and not coll.get("is_error"), coll
    assert "#DC143C" in coll_text, "list output should surface the collection accent"
    assert "bloodline that raised me" in coll_text, "list output should carry the collection ethos"

    bad = await list_handler({"collection": "Sweaters"})
    assert bad.get("is_error") is True, "invalid collection is an error"
    assert "Valid:" in _text(bad), "should list valid collections"

    # --- collection_canon tool -----------------------------------------------
    canon = await canon_handler({"collection": "Black Rose"})
    canon_text = _text(canon)
    assert not canon.get("is_error"), canon
    assert "Armor" in canon_text, "Black Rose canon is 'armor'"
    assert "#C0C0C0" in canon_text, "canon should include the accent token"
    # Canon must NOT cross-wire: Love Hurts' line must never appear under Black Rose.
    assert "bloodline that raised me" not in canon_text, "collection canon must not cross-wire"

    canon_bad = await canon_handler({"collection": ""})
    assert canon_bad.get("is_error") is True, "empty collection is a usage error"

    # --- server build --------------------------------------------------------
    assert catalog_server is not None, "create_sdk_mcp_server must return a server object"

    print("All offline tool checks passed.")


if __name__ == "__main__":
    asyncio.run(_checks())
