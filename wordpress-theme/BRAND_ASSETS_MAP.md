# SkyyRose Brand Assets - Complete Mapping

## Collection Logos (Use These)
Located: `/wp-content/themes/skyyrose-immersive/assets/images/logos/`

## Product Photography (Use These)
Located: `/wp-content/uploads/2025/12/`

### Black Rose Products:
- black-rose_Womens-Black-Rose-Hooded-Dress.png
- black-rose_The-BLACK-Rose-Sherpa-Back.png

### Love Hurts Products:
- love-hurts__Love-Hurts-Collection_-The-Fannie-2.png
- love-hurts__Love-Hurts-Collection_-Sincerely-Hearted-Joggers-Black.png
- love-hurts__Love-Hurts-Collection_-_Fannie_-Pack.png

### Signature Products:
- signature__Signature-Collection_-Cotton-Candy-Shorts.png
- signature__Signature-Collection_-Crop-Hoodie-back.png
- signature__Signature-Collection_-Crop-Hoodie-front.png
- signature__Signature-Collection_-Original-Label-Tee-Orchid.png
- signature__Signature-Collection_-Lavender-Rose-Beanie.png
- signature_The-Pink-Smoke-Crewneck.png
- signature__The-Signature-Collection_-The-Sherpa-2.png

### Hero Images:
Located: `/wp-content/uploads/2022/08/`
- hero_girl_optimized_0321.jpg (main hero)
- girl-optimized02.png
- home_feature_5a.jpg
- home_feature_7a.jpg
- home_feature_8.jpg

## Collection Hero Images:
Located: `/wp-content/themes/skyyrose-theme/assets/images/`
- collection-black-rose.png
- collection-love-hurts.png

## URL Pattern for WordPress:
```php
<?php echo esc_url(wp_get_upload_dir()['baseurl'] . '/2025/12/product-name.png'); ?>
// OR
<?php echo esc_url(get_template_directory_uri() . '/assets/images/logos/logo-name.PNG'); ?>
```

## Template Usage:

### Home Page:
- Hero: hero_girl_optimized_0321.jpg
- Black Rose card: collection-black-rose.png
- Love Hurts card: collection-love-hurts.png
- Signature card: Use signature sherpa or hoodie

### Collection Pages:
- Black Rose: collection-black-rose.png as hero
- Love Hurts: collection-love-hurts.png as hero
- Signature: signature hoodie as hero

### Product Grid:
- Use actual product PNGs from /2025/12/
- Query WooCommerce for real products with featured images

### Vault Page:
- Rotate collection logos from logos/ directory
- Display actual pre-order products with their images
