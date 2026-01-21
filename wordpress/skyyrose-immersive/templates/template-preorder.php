<?php
/**
 * Template Name: Pre-Order Experience (Immersive)
 * Template Post Type: page
 *
 * Full scroll pre-order experience through all SkyyRose collections.
 * Features 3D morphing hero, collection sections, and integrated cart.
 *
 * @package SkyyRose_Immersive
 */

defined('ABSPATH') || exit;

// Get WooCommerce products for each collection
function skyyrose_get_collection_products($category_slugs, $limit = 4) {
    if (!function_exists('wc_get_products')) {
        return array();
    }
    return wc_get_products(array(
        'limit' => $limit,
        'status' => 'publish',
        'category' => $category_slugs,
        'orderby' => 'menu_order',
        'order' => 'ASC',
    ));
}

$blackrose_products = skyyrose_get_collection_products(array('black-rose', 'black-rose-collection'), 4);
$lovehurts_products = skyyrose_get_collection_products(array('love-hurts', 'love-hurts-collection'), 4);
$signature_products = skyyrose_get_collection_products(array('signature', 'signature-collection'), 5);

// Demo products for each collection if empty
$demo_blackrose = array(
    array('name' => 'Thorn Hoodie', 'price' => '185', 'desc' => 'Heavyweight French terry with embroidered thorns cascading down the sleeves.', 'emoji' => '&#127801;', 'badge' => 'Limited'),
    array('name' => 'Midnight Jacket', 'price' => '295', 'desc' => 'Matte leather jacket with crimson satin lining and silver rose hardware.', 'emoji' => '&#128420;', 'badge' => 'Exclusive'),
    array('name' => 'Gothic Rose Tee', 'price' => '75', 'desc' => 'Oversized vintage wash tee with hand-drawn rose graphic.', 'emoji' => '&#127801;', 'badge' => 'New'),
    array('name' => 'Chain Cargo Pants', 'price' => '165', 'desc' => 'Heavy canvas cargo with detachable silver chain details.', 'emoji' => '&#9939;', 'badge' => 'Limited'),
);

$demo_lovehurts = array(
    array('name' => 'Heartbreak Hoodie', 'price' => '195', 'desc' => 'Premium heavyweight hoodie with embroidered broken heart motif.', 'emoji' => '&#128148;', 'badge' => 'Signature'),
    array('name' => 'Tears of Gold Jacket', 'price' => '325', 'desc' => 'Satin bomber with gold tear embroidery and love letter lining.', 'emoji' => '&#128167;', 'badge' => 'Limited'),
    array('name' => 'Wounded Heart Tee', 'price' => '85', 'desc' => 'Oversized tee with anatomical heart graphic and rose thorns.', 'emoji' => '&#129657;', 'badge' => 'Best Seller'),
    array('name' => 'Scar Cargo Pants', 'price' => '165', 'desc' => 'Heavy canvas cargo with embroidered scar details.', 'emoji' => '&#128420;', 'badge' => 'New'),
);

$demo_signature = array(
    array('name' => 'Foundation Blazer', 'price' => '395', 'desc' => 'Premium Italian wool blend blazer with gold-tone hardware.', 'emoji' => '&#129509;', 'badge' => 'Investment'),
    array('name' => 'Essential Trouser', 'price' => '245', 'desc' => 'Tailored wool trousers with perfect drape and hidden stretch.', 'emoji' => '&#128086;', 'badge' => 'Essential'),
    array('name' => 'Luxury Cotton Tee', 'price' => '125', 'desc' => 'Pima cotton tee with gold thread detail at hem.', 'emoji' => '&#128085;', 'badge' => 'Foundation'),
    array('name' => 'Heritage Overcoat', 'price' => '595', 'desc' => 'Double-faced cashmere blend coat with timeless silhouette.', 'emoji' => '&#129509;', 'badge' => 'Investment'),
    array('name' => 'Classic Oxford Shirt', 'price' => '175', 'desc' => 'Egyptian cotton oxford with mother-of-pearl buttons.', 'emoji' => '&#128084;', 'badge' => 'Staple'),
);

// Build JSON data for WooCommerce products
function skyyrose_build_products_json($wc_products, $demo_products, $collection) {
    $products = array();

    if (!empty($wc_products)) {
        foreach ($wc_products as $product) {
            $image_id = $product->get_image_id();
            $products[] = array(
                'id' => $product->get_id(),
                'name' => $product->get_name(),
                'price' => $product->get_price(),
                'description' => $product->get_short_description() ?: 'A stunning piece from the ' . $collection . ' collection.',
                'link' => $product->get_permalink(),
                'image' => $image_id ? wp_get_attachment_image_url($image_id, 'medium') : '',
                'emoji' => '',
                'badge' => 'Pre-Order',
                'collection' => $collection,
                'isDemo' => false,
            );
        }
    } else {
        foreach ($demo_products as $i => $demo) {
            $products[] = array(
                'id' => 'demo-' . strtolower(str_replace(' ', '-', $collection)) . '-' . $i,
                'name' => $demo['name'],
                'price' => $demo['price'],
                'description' => $demo['desc'],
                'link' => '#',
                'image' => '',
                'emoji' => $demo['emoji'],
                'badge' => $demo['badge'],
                'collection' => $collection,
                'isDemo' => true,
            );
        }
    }

    return $products;
}

$blackrose_json = skyyrose_build_products_json($blackrose_products, $demo_blackrose, 'BLACK ROSE');
$lovehurts_json = skyyrose_build_products_json($lovehurts_products, $demo_lovehurts, 'LOVE HURTS');
$signature_json = skyyrose_build_products_json($signature_products, $demo_signature, 'SIGNATURE');

$all_products = array(
    'blackRose' => $blackrose_json,
    'loveHurts' => $lovehurts_json,
    'signature' => $signature_json,
);

$cart_url = function_exists('wc_get_cart_url') ? wc_get_cart_url() : home_url('/cart');
$checkout_url = function_exists('wc_get_checkout_url') ? wc_get_checkout_url() : home_url('/checkout');
$cart_count = (WC()->cart) ? WC()->cart->get_cart_contents_count() : 0;
?>
<!DOCTYPE html>
<html <?php language_attributes(); ?>>
<head>
    <meta charset="<?php bloginfo('charset'); ?>">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pre-Order Experience | <?php bloginfo('name'); ?> | Where Love Meets Luxury</title>
    <meta name="description" content="Exclusive pre-order access to all SkyyRose collections - BLACK ROSE, LOVE HURTS, and SIGNATURE. Immersive 3D shopping experience.">
    <?php wp_head(); ?>

    <script type="importmap">
    {
        "imports": {
            "three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js",
            "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"
        }
    }
    </script>

    <style>
        :root {
            --br-crimson: #DC143C;
            --br-dark: #0A0505;
            --br-silver: #C0C0C0;
            --lh-rose: #E91E63;
            --lh-burgundy: #880E4F;
            --lh-blush: #F8BBD9;
            --sg-gold: #D4AF37;
            --sg-rose-gold: #B76E79;
            --sg-black: #0A0A0A;
            --font-display: 'Playfair Display', Georgia, serif;
            --font-body: 'Inter', -apple-system, sans-serif;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap');

        html, body {
            font-family: var(--font-body);
            background: #000;
            color: #fff;
            overflow-x: hidden;
            scroll-behavior: smooth;
        }

        #loading-screen {
            position: fixed;
            inset: 0;
            background: #000;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            z-index: 10000;
            transition: opacity 1s ease, visibility 1s ease;
        }

        #loading-screen.hidden {
            opacity: 0;
            visibility: hidden;
        }

        .loader-logo {
            font-family: var(--font-display);
            font-size: 4rem;
            font-weight: 600;
            letter-spacing: 0.5em;
            margin-bottom: 1rem;
            background: linear-gradient(90deg, var(--br-crimson), var(--lh-rose), var(--sg-gold), var(--br-crimson));
            background-size: 300% 100%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: gradient-shift 3s ease infinite;
        }

        @keyframes gradient-shift {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }

        .loader-tagline {
            font-size: 0.9rem;
            letter-spacing: 0.5em;
            text-transform: uppercase;
            color: rgba(255,255,255,0.6);
            margin-bottom: 3rem;
        }

        .loader-ring {
            width: 80px;
            height: 80px;
            border: 2px solid rgba(255,255,255,0.1);
            border-top-color: var(--sg-gold);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin { to { transform: rotate(360deg); } }

        .loader-progress {
            margin-top: 2rem;
            font-size: 0.8rem;
            letter-spacing: 0.3em;
            color: var(--sg-gold);
        }

        #hero-canvas {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100vh;
            z-index: 1;
        }

        .scroll-content {
            position: relative;
            z-index: 10;
        }

        .hero-section {
            height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            position: relative;
        }

        .hero-badge {
            padding: 0.5rem 1.5rem;
            border: 1px solid var(--sg-gold);
            font-size: 0.7rem;
            letter-spacing: 0.4em;
            text-transform: uppercase;
            color: var(--sg-gold);
            margin-bottom: 2rem;
            animation: pulse-border 2s ease-in-out infinite;
        }

        @keyframes pulse-border {
            0%, 100% { box-shadow: 0 0 0 0 rgba(212, 175, 55, 0.4); }
            50% { box-shadow: 0 0 20px 5px rgba(212, 175, 55, 0.2); }
        }

        .hero-title {
            font-family: var(--font-display);
            font-size: 6rem;
            font-weight: 600;
            letter-spacing: 0.3em;
            margin-bottom: 1rem;
            background: linear-gradient(180deg, #fff 0%, rgba(255,255,255,0.7) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .hero-subtitle {
            font-size: 1.2rem;
            letter-spacing: 0.5em;
            text-transform: uppercase;
            color: rgba(255,255,255,0.6);
            margin-bottom: 3rem;
        }

        .hero-cta { display: flex; gap: 1.5rem; }

        .cta-btn {
            padding: 1rem 2.5rem;
            font-family: var(--font-body);
            font-size: 0.8rem;
            letter-spacing: 0.2em;
            text-transform: uppercase;
            text-decoration: none;
            cursor: pointer;
            transition: all 0.4s ease;
        }

        .cta-primary {
            background: linear-gradient(135deg, var(--sg-gold), var(--sg-rose-gold));
            border: none;
            color: #000;
        }

        .cta-primary:hover {
            transform: translateY(-3px);
            box-shadow: 0 15px 40px rgba(212, 175, 55, 0.4);
        }

        .cta-secondary {
            background: transparent;
            border: 1px solid rgba(255,255,255,0.3);
            color: #fff;
        }

        .cta-secondary:hover {
            border-color: #fff;
            background: rgba(255,255,255,0.1);
        }

        .scroll-indicator {
            position: absolute;
            bottom: 3rem;
            left: 50%;
            transform: translateX(-50%);
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 0.5rem;
            color: rgba(255,255,255,0.4);
            font-size: 0.7rem;
            letter-spacing: 0.3em;
            animation: bounce 2s ease-in-out infinite;
        }

        @keyframes bounce {
            0%, 100% { transform: translateX(-50%) translateY(0); }
            50% { transform: translateX(-50%) translateY(10px); }
        }

        .collection-section {
            min-height: 100vh;
            padding: 8rem 5%;
            position: relative;
            overflow: hidden;
        }

        .collection-bg {
            position: absolute;
            inset: 0;
            opacity: 0.15;
            pointer-events: none;
        }

        .black-rose-section { background: linear-gradient(180deg, #000 0%, var(--br-dark) 50%, #000 100%); }
        .black-rose-section .collection-bg { background: radial-gradient(ellipse at 30% 50%, var(--br-crimson) 0%, transparent 50%); }

        .love-hurts-section { background: linear-gradient(180deg, #000 0%, #0d0408 50%, #000 100%); }
        .love-hurts-section .collection-bg { background: radial-gradient(ellipse at 70% 50%, var(--lh-rose) 0%, transparent 50%); }

        .signature-section { background: linear-gradient(180deg, #000 0%, var(--sg-black) 50%, #000 100%); }
        .signature-section .collection-bg { background: radial-gradient(ellipse at 50% 50%, var(--sg-gold) 0%, transparent 40%); }

        .collection-header { text-align: center; margin-bottom: 4rem; }

        .collection-number {
            font-size: 0.8rem;
            letter-spacing: 0.5em;
            color: rgba(255,255,255,0.3);
            margin-bottom: 1rem;
        }

        .collection-title {
            font-family: var(--font-display);
            font-size: 4rem;
            font-weight: 600;
            letter-spacing: 0.2em;
            margin-bottom: 1rem;
        }

        .black-rose-section .collection-title { background: linear-gradient(135deg, var(--br-crimson), var(--br-silver)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
        .love-hurts-section .collection-title { background: linear-gradient(135deg, var(--lh-rose), var(--lh-blush)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
        .signature-section .collection-title { background: linear-gradient(135deg, var(--sg-gold), var(--sg-rose-gold)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }

        .collection-tagline {
            font-size: 1rem;
            letter-spacing: 0.4em;
            text-transform: uppercase;
            color: rgba(255,255,255,0.5);
        }

        .collection-link {
            display: inline-block;
            margin-top: 1rem;
            padding: 0.5rem 1rem;
            font-size: 0.75rem;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            text-decoration: none;
            border: 1px solid rgba(255,255,255,0.3);
            color: rgba(255,255,255,0.6);
            transition: all 0.3s ease;
        }

        .collection-link:hover { border-color: var(--sg-gold); color: var(--sg-gold); }

        .products-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 2rem;
            max-width: 1400px;
            margin: 0 auto;
        }

        .product-card {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.08);
            padding: 1.5rem;
            transition: all 0.4s ease;
            position: relative;
            overflow: hidden;
        }

        .product-card::before {
            content: '';
            position: absolute;
            inset: 0;
            background: linear-gradient(135deg, transparent 0%, rgba(255,255,255,0.05) 100%);
            opacity: 0;
            transition: opacity 0.4s ease;
        }

        .product-card:hover { transform: translateY(-10px); border-color: rgba(255,255,255,0.2); }
        .product-card:hover::before { opacity: 1; }

        .product-image {
            height: 200px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 1.5rem;
            position: relative;
            background: rgba(0,0,0,0.3);
            overflow: hidden;
        }

        .product-image img { width: 100%; height: 100%; object-fit: cover; }
        .product-image .emoji-placeholder { font-size: 5rem; }

        .product-badge {
            position: absolute;
            top: 0;
            right: 0;
            padding: 0.3rem 0.6rem;
            font-size: 0.65rem;
            letter-spacing: 0.1em;
            text-transform: uppercase;
        }

        .black-rose-section .product-badge { background: var(--br-crimson); }
        .love-hurts-section .product-badge { background: var(--lh-burgundy); }
        .signature-section .product-badge { background: transparent; border: 1px solid var(--sg-gold); color: var(--sg-gold); }

        .product-name { font-family: var(--font-display); font-size: 1.3rem; margin-bottom: 0.5rem; }
        .product-price { font-size: 1.1rem; margin-bottom: 1rem; }

        .black-rose-section .product-price { color: var(--br-crimson); }
        .love-hurts-section .product-price { color: var(--lh-rose); }
        .signature-section .product-price { color: var(--sg-gold); }

        .product-description { font-size: 0.85rem; color: rgba(255,255,255,0.6); line-height: 1.6; margin-bottom: 1.5rem; }
        .product-actions { display: flex; flex-direction: column; gap: 0.5rem; }

        .preorder-btn {
            width: 100%;
            padding: 0.8rem;
            font-family: var(--font-body);
            font-size: 0.75rem;
            letter-spacing: 0.15em;
            text-transform: uppercase;
            cursor: pointer;
            transition: all 0.3s ease;
        }

        .preorder-btn:disabled { opacity: 0.6; cursor: not-allowed; }

        .black-rose-section .preorder-btn { background: transparent; border: 1px solid var(--br-crimson); color: var(--br-crimson); }
        .black-rose-section .preorder-btn:hover:not(:disabled) { background: var(--br-crimson); color: #fff; }

        .love-hurts-section .preorder-btn { background: transparent; border: 1px solid var(--lh-rose); color: var(--lh-rose); }
        .love-hurts-section .preorder-btn:hover:not(:disabled) { background: var(--lh-rose); color: #fff; }

        .signature-section .preorder-btn { background: transparent; border: 1px solid var(--sg-gold); color: var(--sg-gold); }
        .signature-section .preorder-btn:hover:not(:disabled) { background: var(--sg-gold); color: #000; }

        .view-details-link {
            display: block;
            text-align: center;
            padding: 0.5rem;
            font-size: 0.7rem;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            text-decoration: none;
            color: rgba(255,255,255,0.5);
            transition: color 0.3s ease;
        }

        .view-details-link:hover { color: #fff; }

        .cart-btn {
            position: fixed;
            top: 2rem;
            right: 2rem;
            width: 50px;
            height: 50px;
            background: rgba(0,0,0,0.8);
            border: 1px solid var(--sg-gold);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            z-index: 1000;
            transition: all 0.3s ease;
            text-decoration: none;
            color: var(--sg-gold);
            font-size: 1.2rem;
        }

        .cart-btn:hover { background: var(--sg-gold); color: #000; }

        .cart-count {
            position: absolute;
            top: -5px;
            right: -5px;
            width: 20px;
            height: 20px;
            background: var(--lh-rose);
            border-radius: 50%;
            font-size: 0.7rem;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
        }

        .back-btn {
            position: fixed;
            top: 2rem;
            left: 2rem;
            padding: 0.8rem 1.2rem;
            background: rgba(0,0,0,0.8);
            border: 1px solid rgba(255,255,255,0.3);
            color: rgba(255,255,255,0.7);
            font-family: var(--font-body);
            font-size: 0.75rem;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            text-decoration: none;
            cursor: pointer;
            z-index: 1000;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        .back-btn:hover { border-color: var(--sg-gold); color: var(--sg-gold); }

        .toast {
            position: fixed;
            bottom: 2rem;
            left: 50%;
            transform: translateX(-50%) translateY(100px);
            background: linear-gradient(135deg, var(--sg-gold), var(--sg-rose-gold));
            color: #000;
            padding: 1rem 2rem;
            border-radius: 4px;
            font-size: 0.9rem;
            letter-spacing: 0.1em;
            z-index: 10000;
            opacity: 0;
            transition: all 0.4s ease;
            box-shadow: 0 10px 40px rgba(212, 175, 55, 0.5);
        }

        .toast.visible { transform: translateX(-50%) translateY(0); opacity: 1; }

        .footer {
            padding: 4rem 5%;
            background: #000;
            border-top: 1px solid rgba(255,255,255,0.1);
            text-align: center;
        }

        .footer-logo {
            font-family: var(--font-display);
            font-size: 2rem;
            letter-spacing: 0.4em;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, var(--sg-gold), var(--sg-rose-gold));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }

        .footer-tagline { font-size: 0.85rem; letter-spacing: 0.3em; color: rgba(255,255,255,0.4); margin-bottom: 2rem; }

        .footer-links { display: flex; justify-content: center; gap: 2rem; margin-bottom: 2rem; flex-wrap: wrap; }
        .footer-links a { color: rgba(255,255,255,0.6); text-decoration: none; font-size: 0.8rem; letter-spacing: 0.1em; transition: color 0.3s ease; }
        .footer-links a:hover { color: var(--sg-gold); }

        .footer-copyright { font-size: 0.75rem; color: rgba(255,255,255,0.3); }

        @media (max-width: 768px) {
            .hero-title { font-size: 3rem; letter-spacing: 0.2em; }
            .collection-title { font-size: 2.5rem; }
            .hero-cta { flex-direction: column; }
            .back-btn { top: auto; bottom: 2rem; left: 1rem; }
            .cart-btn { top: 1rem; right: 1rem; }
            .loader-logo { font-size: 2.5rem; }
        }
    </style>
</head>
<body <?php body_class('skyyrose-preorder-experience'); ?>>
    <div id="loading-screen">
        <div class="loader-logo">SKYYROSE</div>
        <div class="loader-tagline">Where Love Meets Luxury</div>
        <div class="loader-ring"></div>
        <div class="loader-progress" id="loader-progress">Loading Experience...</div>
    </div>

    <canvas id="hero-canvas"></canvas>

    <a href="<?php echo esc_url(home_url()); ?>" class="back-btn"><span>&larr;</span> Home</a>

    <a href="<?php echo esc_url($cart_url); ?>" class="cart-btn">&#128722;<span class="cart-count" id="cart-count"><?php echo esc_html($cart_count); ?></span></a>

    <div class="toast" id="toast">Added to cart!</div>

    <div class="scroll-content">
        <section class="hero-section">
            <span class="hero-badge">Exclusive Pre-Order Access</span>
            <h1 class="hero-title">SKYYROSE</h1>
            <p class="hero-subtitle">Where Love Meets Luxury</p>
            <div class="hero-cta">
                <a href="#black-rose" class="cta-btn cta-primary">Explore Collections</a>
                <a href="#signature" class="cta-btn cta-secondary">View Signature</a>
            </div>
            <div class="scroll-indicator"><span>Scroll to Explore</span><span>&darr;</span></div>
        </section>

        <section class="collection-section black-rose-section" id="black-rose">
            <div class="collection-bg"></div>
            <div class="collection-header">
                <p class="collection-number">COLLECTION 01</p>
                <h2 class="collection-title">BLACK ROSE</h2>
                <p class="collection-tagline">Dark Elegance &bull; Limited Edition</p>
                <a href="<?php echo esc_url(home_url('/collections/black-rose')); ?>" class="collection-link">View Full Collection &rarr;</a>
            </div>
            <div class="products-grid" id="blackrose-products"></div>
        </section>

        <section class="collection-section love-hurts-section" id="love-hurts">
            <div class="collection-bg"></div>
            <div class="collection-header">
                <p class="collection-number">COLLECTION 02</p>
                <h2 class="collection-title">LOVE HURTS</h2>
                <p class="collection-tagline">Honoring the Hurt Family Legacy</p>
                <a href="<?php echo esc_url(home_url('/collections/love-hurts')); ?>" class="collection-link">View Full Collection &rarr;</a>
            </div>
            <div class="products-grid" id="lovehurts-products"></div>
        </section>

        <section class="collection-section signature-section" id="signature">
            <div class="collection-bg"></div>
            <div class="collection-header">
                <p class="collection-number">COLLECTION 03</p>
                <h2 class="collection-title">SIGNATURE</h2>
                <p class="collection-tagline">Premium Foundation Essentials</p>
                <a href="<?php echo esc_url(home_url('/collections/signature')); ?>" class="collection-link">View Full Collection &rarr;</a>
            </div>
            <div class="products-grid" id="signature-products"></div>
        </section>

        <footer class="footer">
            <div class="footer-logo">SKYYROSE</div>
            <p class="footer-tagline">Where Love Meets Luxury &bull; Oakland, California</p>
            <div class="footer-links">
                <a href="<?php echo esc_url(home_url('/about')); ?>">About</a>
                <a href="<?php echo esc_url(home_url('/shipping')); ?>">Shipping</a>
                <a href="<?php echo esc_url(home_url('/returns')); ?>">Returns</a>
                <a href="<?php echo esc_url(home_url('/contact')); ?>">Contact</a>
            </div>
            <p class="footer-copyright">&copy; <?php echo date('Y'); ?> <?php bloginfo('name'); ?>. All rights reserved.</p>
        </footer>
    </div>

    <script type="module">
        import * as THREE from 'three';
        import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
        import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
        import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
        import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';

        let scene, camera, renderer, composer;
        let morphingGeometry, particles, rings = [];
        let clock = new THREE.Clock();
        let scrollY = 0, targetScrollY = 0;

        const themes = {
            hero: { primary: new THREE.Color(0xD4AF37), secondary: new THREE.Color(0xE91E63), tertiary: new THREE.Color(0xDC143C) },
            blackRose: { primary: new THREE.Color(0xDC143C), secondary: new THREE.Color(0xC0C0C0), tertiary: new THREE.Color(0x8B0000) },
            loveHurts: { primary: new THREE.Color(0xE91E63), secondary: new THREE.Color(0xF8BBD9), tertiary: new THREE.Color(0x880E4F) },
            signature: { primary: new THREE.Color(0xD4AF37), secondary: new THREE.Color(0xB76E79), tertiary: new THREE.Color(0xE5E4E2) }
        };

        init();
        animate();

        function init() {
            scene = new THREE.Scene();
            scene.background = new THREE.Color(0x000000);

            camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.1, 1000);
            camera.position.z = 30;

            const canvas = document.getElementById('hero-canvas');
            renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
            renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
            renderer.setSize(window.innerWidth, window.innerHeight);
            renderer.toneMapping = THREE.ACESFilmicToneMapping;
            renderer.toneMappingExposure = 1.2;

            createMorphingCore();
            createParticleField();
            createOrbitingRings();
            setupPostProcessing();

            window.addEventListener('resize', onWindowResize);
            window.addEventListener('scroll', () => { targetScrollY = window.scrollY; });

            simulateLoading();
        }

        function createMorphingCore() {
            const geometry = new THREE.IcosahedronGeometry(5, 4);
            const material = new THREE.ShaderMaterial({
                uniforms: {
                    uTime: { value: 0 },
                    uColor1: { value: themes.hero.primary },
                    uColor2: { value: themes.hero.secondary },
                    uColor3: { value: themes.hero.tertiary }
                },
                vertexShader: `
                    uniform float uTime;
                    varying vec3 vNormal, vPosition;
                    varying float vDisplacement;
                    vec3 mod289(vec3 x){return x-floor(x*(1./289.))*289.;}
                    vec4 mod289(vec4 x){return x-floor(x*(1./289.))*289.;}
                    vec4 permute(vec4 x){return mod289(((x*34.)+1.)*x);}
                    vec4 taylorInvSqrt(vec4 r){return 1.79284291400159-.85373472095314*r;}
                    float snoise(vec3 v){
                        const vec2 C=vec2(1./6.,1./3.);
                        const vec4 D=vec4(0.,.5,1.,2.);
                        vec3 i=floor(v+dot(v,C.yyy));
                        vec3 x0=v-i+dot(i,C.xxx);
                        vec3 g=step(x0.yzx,x0.xyz);
                        vec3 l=1.-g;
                        vec3 i1=min(g.xyz,l.zxy);
                        vec3 i2=max(g.xyz,l.zxy);
                        vec3 x1=x0-i1+C.xxx;
                        vec3 x2=x0-i2+C.yyy;
                        vec3 x3=x0-D.yyy;
                        i=mod289(i);
                        vec4 p=permute(permute(permute(i.z+vec4(0.,i1.z,i2.z,1.))+i.y+vec4(0.,i1.y,i2.y,1.))+i.x+vec4(0.,i1.x,i2.x,1.));
                        float n_=.142857142857;
                        vec3 ns=n_*D.wyz-D.xzx;
                        vec4 j=p-49.*floor(p*ns.z*ns.z);
                        vec4 x_=floor(j*ns.z);
                        vec4 y_=floor(j-7.*x_);
                        vec4 x=x_*ns.x+ns.yyyy;
                        vec4 y=y_*ns.x+ns.yyyy;
                        vec4 h=1.-abs(x)-abs(y);
                        vec4 b0=vec4(x.xy,y.xy);
                        vec4 b1=vec4(x.zw,y.zw);
                        vec4 s0=floor(b0)*2.+1.;
                        vec4 s1=floor(b1)*2.+1.;
                        vec4 sh=-step(h,vec4(0.));
                        vec4 a0=b0.xzyw+s0.xzyw*sh.xxyy;
                        vec4 a1=b1.xzyw+s1.xzyw*sh.zzww;
                        vec3 p0=vec3(a0.xy,h.x);
                        vec3 p1=vec3(a0.zw,h.y);
                        vec3 p2=vec3(a1.xy,h.z);
                        vec3 p3=vec3(a1.zw,h.w);
                        vec4 norm=taylorInvSqrt(vec4(dot(p0,p0),dot(p1,p1),dot(p2,p2),dot(p3,p3)));
                        p0*=norm.x;p1*=norm.y;p2*=norm.z;p3*=norm.w;
                        vec4 m=max(.6-vec4(dot(x0,x0),dot(x1,x1),dot(x2,x2),dot(x3,x3)),0.);
                        m=m*m;
                        return 42.*dot(m*m,vec4(dot(p0,x0),dot(p1,x1),dot(p2,x2),dot(p3,x3)));
                    }
                    void main(){
                        vNormal=normalize(normalMatrix*normal);
                        float n1=snoise(position*.3+uTime*.2);
                        float n2=snoise(position*.6+uTime*.3)*.5;
                        float n3=snoise(position*1.2+uTime*.1)*.25;
                        float d=(n1+n2+n3);
                        vDisplacement=d;
                        vec3 np=position+normal*d*.8;
                        vPosition=np;
                        gl_Position=projectionMatrix*modelViewMatrix*vec4(np,1.);
                    }
                `,
                fragmentShader: `
                    uniform float uTime;
                    uniform vec3 uColor1,uColor2,uColor3;
                    varying vec3 vNormal,vPosition;
                    varying float vDisplacement;
                    void main(){
                        vec3 vd=normalize(cameraPosition-vPosition);
                        float f=pow(1.-dot(vd,vNormal),3.);
                        float cm1=sin(vDisplacement*3.+uTime)*.5+.5;
                        float cm2=cos(vPosition.y*.5+uTime*.5)*.5+.5;
                        vec3 c=mix(uColor1,uColor2,cm1);
                        c=mix(c,uColor3,cm2*.5);
                        c+=f*uColor1*.5;
                        gl_FragColor=vec4(c,.9);
                    }
                `,
                transparent: true,
                side: THREE.DoubleSide
            });
            morphingGeometry = new THREE.Mesh(geometry, material);
            scene.add(morphingGeometry);
        }

        function createParticleField() {
            const pc = 3000;
            const pos = new Float32Array(pc * 3);
            const col = new Float32Array(pc * 3);
            const vel = new Float32Array(pc * 3);
            const cols = [new THREE.Color(0xD4AF37), new THREE.Color(0xE91E63), new THREE.Color(0xDC143C), new THREE.Color(0xC0C0C0), new THREE.Color(0xF8BBD9)];

            for (let i = 0; i < pc; i++) {
                const r = 15 + Math.random() * 35;
                const t = Math.random() * Math.PI * 2;
                const p = Math.acos(2 * Math.random() - 1);
                pos[i * 3] = r * Math.sin(p) * Math.cos(t);
                pos[i * 3 + 1] = r * Math.sin(p) * Math.sin(t);
                pos[i * 3 + 2] = r * Math.cos(p);
                vel[i * 3] = (Math.random() - .5) * .02;
                vel[i * 3 + 1] = (Math.random() - .5) * .02;
                vel[i * 3 + 2] = (Math.random() - .5) * .02;
                const c = cols[Math.floor(Math.random() * cols.length)];
                col[i * 3] = c.r; col[i * 3 + 1] = c.g; col[i * 3 + 2] = c.b;
            }

            const geo = new THREE.BufferGeometry();
            geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
            geo.setAttribute('color', new THREE.BufferAttribute(col, 3));
            geo.userData.velocities = vel;

            const mat = new THREE.PointsMaterial({ size: .1, vertexColors: true, transparent: true, opacity: .8, blending: THREE.AdditiveBlending, sizeAttenuation: true });
            particles = new THREE.Points(geo, mat);
            scene.add(particles);
        }

        function createOrbitingRings() {
            const rc = [0xD4AF37, 0xE91E63, 0xDC143C, 0xB76E79, 0xC0C0C0];
            for (let i = 0; i < 5; i++) {
                const geo = new THREE.TorusGeometry(8 + i * 3, .02 + i * .01, 16, 100);
                const mat = new THREE.MeshBasicMaterial({ color: rc[i], transparent: true, opacity: .4 - i * .05 });
                const ring = new THREE.Mesh(geo, mat);
                ring.rotation.x = Math.random() * Math.PI;
                ring.rotation.y = Math.random() * Math.PI;
                ring.userData.rs = { x: (Math.random() - .5) * .01, y: (Math.random() - .5) * .01, z: (Math.random() - .5) * .005 };
                rings.push(ring);
                scene.add(ring);
            }
        }

        function setupPostProcessing() {
            composer = new EffectComposer(renderer);
            composer.addPass(new RenderPass(scene, camera));
            composer.addPass(new UnrealBloomPass(new THREE.Vector2(window.innerWidth, window.innerHeight), 1.5, .4, .85));
            composer.addPass(new OutputPass());
        }

        function animate() {
            requestAnimationFrame(animate);
            const t = clock.getElapsedTime();
            scrollY += (targetScrollY - scrollY) * .1;

            if (morphingGeometry) {
                morphingGeometry.material.uniforms.uTime.value = t;
                morphingGeometry.rotation.y = t * .1;
                morphingGeometry.rotation.x = Math.sin(t * .2) * .2;
                const sp = scrollY / (document.body.scrollHeight - window.innerHeight);
                updateThemeColors(sp);
            }

            if (particles) {
                particles.rotation.y += .0005;
                particles.rotation.x += .0002;
                const pos = particles.geometry.attributes.position.array;
                const vel = particles.geometry.userData.velocities;
                for (let i = 0; i < pos.length; i += 3) {
                    pos[i] += vel[i]; pos[i + 1] += vel[i + 1]; pos[i + 2] += vel[i + 2];
                    const d = Math.sqrt(pos[i] ** 2 + pos[i + 1] ** 2 + pos[i + 2] ** 2);
                    if (d > 50) { const s = 15 / d; pos[i] *= s; pos[i + 1] *= s; pos[i + 2] *= s; }
                }
                particles.geometry.attributes.position.needsUpdate = true;
            }

            rings.forEach(r => { r.rotation.x += r.userData.rs.x; r.rotation.y += r.userData.rs.y; r.rotation.z += r.userData.rs.z; });

            camera.position.z = 30 - scrollY * .01;
            camera.position.y = scrollY * .005;

            composer.render();
        }

        function updateThemeColors(p) {
            let th;
            if (p < .25) th = lerpTheme(themes.hero, themes.blackRose, p * 4);
            else if (p < .5) th = lerpTheme(themes.blackRose, themes.loveHurts, (p - .25) * 4);
            else if (p < .75) th = lerpTheme(themes.loveHurts, themes.signature, (p - .5) * 4);
            else th = themes.signature;

            if (morphingGeometry) {
                morphingGeometry.material.uniforms.uColor1.value.copy(th.primary);
                morphingGeometry.material.uniforms.uColor2.value.copy(th.secondary);
                morphingGeometry.material.uniforms.uColor3.value.copy(th.tertiary);
            }
        }

        function lerpTheme(t1, t2, t) {
            return {
                primary: t1.primary.clone().lerp(t2.primary, t),
                secondary: t1.secondary.clone().lerp(t2.secondary, t),
                tertiary: t1.tertiary.clone().lerp(t2.tertiary, t)
            };
        }

        function onWindowResize() {
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
            composer.setSize(window.innerWidth, window.innerHeight);
        }

        function simulateLoading() {
            const el = document.getElementById('loader-progress');
            let p = 0;
            const i = setInterval(() => {
                p += Math.random() * 8;
                if (p >= 100) {
                    p = 100; clearInterval(i);
                    el.textContent = 'Welcome to SkyyRose';
                    setTimeout(() => document.getElementById('loading-screen').classList.add('hidden'), 800);
                } else el.textContent = `Loading ${Math.floor(p)}%`;
            }, 100);
        }
    </script>

    <script>
        const allProducts = <?php echo json_encode($all_products); ?>;

        function renderProducts() {
            renderCollectionProducts('blackrose-products', allProducts.blackRose);
            renderCollectionProducts('lovehurts-products', allProducts.loveHurts);
            renderCollectionProducts('signature-products', allProducts.signature);
        }

        function renderCollectionProducts(containerId, products) {
            const c = document.getElementById(containerId);
            if (!c) return;
            c.innerHTML = products.map(p => `
                <div class="product-card">
                    <div class="product-image">
                        ${p.image ? `<img src="${p.image}" alt="${p.name}">` : `<span class="emoji-placeholder">${p.emoji}</span>`}
                        <span class="product-badge">${p.badge}</span>
                    </div>
                    <h3 class="product-name">${p.name}</h3>
                    <p class="product-price">$${parseFloat(p.price).toFixed(0)}</p>
                    <p class="product-description">${p.description}</p>
                    <div class="product-actions">
                        <button class="preorder-btn" onclick="addToCart('${p.id}', '${p.name}', ${p.price}, '${p.collection}', ${p.isDemo})">Pre-Order Now</button>
                        ${!p.isDemo && p.link !== '#' ? `<a href="${p.link}" class="view-details-link">View Full Details &rarr;</a>` : ''}
                    </div>
                </div>
            `).join('');
        }

        function addToCart(productId, productName, price, collection, isDemo) {
            if (isDemo || String(productId).startsWith('demo')) {
                showToast(`Demo: ${productName} would be added to cart`);
                return;
            }

            const btn = event.target;
            const originalText = btn.textContent;
            btn.disabled = true;
            btn.textContent = 'Adding...';

            const formData = new FormData();
            formData.append('action', 'woocommerce_add_to_cart');
            formData.append('product_id', productId);
            formData.append('quantity', 1);

            fetch('<?php echo admin_url('admin-ajax.php'); ?>', {
                method: 'POST',
                body: formData,
                credentials: 'same-origin'
            })
            .then(r => r.json())
            .then(d => {
                btn.disabled = false;
                if (d.error) {
                    btn.textContent = originalText;
                    showToast('Error: ' + (d.error || 'Could not add to cart'));
                } else {
                    btn.textContent = '\u2713 Added!';
                    showToast(`${productName} added to cart!`);
                    const ce = document.getElementById('cart-count');
                    if (ce) ce.textContent = parseInt(ce.textContent) + 1;
                    setTimeout(() => { btn.textContent = originalText; }, 2000);
                }
            })
            .catch(e => {
                btn.disabled = false;
                btn.textContent = originalText;
                showToast('Error adding to cart');
                console.error(e);
            });
        }

        function showToast(msg) {
            const t = document.getElementById('toast');
            t.textContent = msg;
            t.classList.add('visible');
            setTimeout(() => t.classList.remove('visible'), 3000);
        }

        document.addEventListener('DOMContentLoaded', renderProducts);
    </script>

    <?php wp_footer(); ?>
</body>
</html>
