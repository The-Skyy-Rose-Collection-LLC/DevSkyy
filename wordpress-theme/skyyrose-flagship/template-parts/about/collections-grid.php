<?php
/**
 * About Chapter II — The Collections (3D Portals)
 * Connects the catalog images to the editorial 3D portals.
 */
defined( 'ABSPATH' ) || exit;

// We fetch the collection data directly from the catalog to ensure the hero images are exact.
$catalog = function_exists('skyyrose_get_product_catalog') ? skyyrose_get_product_catalog() : array();
$collection_data = array(
    'black-rose' => array(
        'title' => 'Black Rose',
        'desc'  => 'Dark, powerful, unapologetic — Black Rose redefines what luxury streetwear looks like through a lens of strength and sophistication.',
        'link'  => '/collection-black-rose/',
        'img'   => ''
    ),
    'love-hurts' => array(
        'title' => 'Love Hurts',
        'desc'  => 'The Hurts bloodline. A grandmother’s legacy. Told from Beast’s perspective with the enchanted rose at its heart.',
        'link'  => '/collection-love-hurts/',
        'img'   => ''
    ),
    'signature' => array(
        'title' => 'Signature',
        'desc'  => 'The origin. The crown. The first rose and script logo that started it all. Signature is the foundation of SkyyRose.',
        'link'  => '/collection-signature/',
        'img'   => ''
    )
);

// Map the first product from each collection to use its front techflat/model as the portal image.
foreach ($catalog as $product) {
    if (isset($collection_data[$product['collection']]) && empty($collection_data[$product['collection']]['img'])) {
        $collection_data[$product['collection']]['img'] = $product['image_url'];
    }
}
?>
<section class="abt-collections" id="collections">
	<div class="abt-col-header rv-clip-up">
		<h2>The Collections</h2>
		<p>Three Worlds. One Vision.</p>
	</div>
	
	<div class="abt-portal-list">
		<?php foreach ($collection_data as $slug => $data) : ?>
			<a href="<?php echo esc_url( home_url( $data['link'] ) ); ?>" class="abt-portal-item rv-clip-up">
				<div class="abt-portal-media" data-portal="<?php echo esc_attr($slug); ?>">
					<img src="<?php echo esc_url($data['img'] ?: get_theme_file_uri('assets/images/placeholder-product.jpg')); ?>" alt="<?php echo esc_attr($data['title']); ?>" loading="lazy">
					<!-- WebGL canvas injected here by immersive-world.js -->
					<div class="abt-portal-canvas"></div>
				</div>
				<div class="abt-portal-content">
					<h3 class="abt-portal-title"><?php echo esc_html($data['title']); ?></h3>
					<p class="abt-portal-desc"><?php echo esc_html($data['desc']); ?></p>
					<span class="abt-portal-cta">Explore Portal</span>
				</div>
			</a>
		<?php endforeach; ?>
	</div>
</section>
