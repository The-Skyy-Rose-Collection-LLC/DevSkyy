# SkyyRose Flagship SOT

Fresh marketplace staging theme. Uses no copied product or scene imagery.

## Asset authority

- Collection identity, lockups, scenes, products, and collection fonts resolve from `skyyrose-flagship/data/collections/<slug>/sot.json`.
- Product images use `front_model_image`, then SOT `image`. No Woo thumbnail fallback.
- Scroll World uses same current camera-flight engine, but each scene is built from SOT collection imagery at runtime.
- Existing source theme remains SOT asset host during staging. Before replacement, move SOT assets and JSON to a shared persistent host, then supply `skyyrosesot_source_directory` and `skyyrosesot_asset_base_uri` filters. Do not duplicate asset tree.

## Page map

- Homepage, collection index, four collection pages, world page, shop, single product, cart, pre-order, about, contact.
- Assign `Collections World SOT` to `/collections-world/`.
- Assign `SkyyRose SOT Collection` to collection child pages under `/collections/`.
