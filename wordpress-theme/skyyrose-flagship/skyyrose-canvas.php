<?php
/**
 * Template Name: SkyyRose Canvas
 *
 * Full-width canvas template for the "Shop All" collections page.
 * Uses the theme header/footer and enqueues collections-shop CSS/JS.
 *
 * @package SkyyRose_Flagship
 * @since   3.2.2
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

get_header();
?>

<main id="primary" class="site-main collections-shop-page" role="main" tabindex="-1">

	<!-- Film Grain Overlay -->
	<div class="shop-grain" aria-hidden="true"></div>

	<!-- Hero -->
	<section class="shop-hero">
		<div class="shop-hero-label" aria-hidden="true"><?php echo esc_html__( 'The Skyy Rose Collection', 'skyyrose-flagship' ); ?></div>
		<h1><?php echo esc_html__( 'SHOP ALL', 'skyyrose-flagship' ); ?></h1>
		<p class="shop-hero-sub"><?php echo esc_html__( 'Three distinct worlds. One unified vision. Every piece crafted in Oakland for those who refuse to be ordinary.', 'skyyrose-flagship' ); ?></p>
		<div class="shop-count"><span id="productCount">18</span> <?php echo esc_html__( 'pieces across 3 collections', 'skyyrose-flagship' ); ?></div>
	</section>

	<!-- Collection Filter Tabs -->
	<div class="shop-tabs" role="tablist" aria-label="<?php esc_attr_e( 'Filter by collection', 'skyyrose-flagship' ); ?>">
		<button type="button" class="shop-tab active" data-collection="all" role="tab" aria-selected="true"><?php echo esc_html__( 'All Collections', 'skyyrose-flagship' ); ?></button>
		<button type="button" class="shop-tab" data-collection="black-rose" role="tab" aria-selected="false"><?php echo esc_html__( 'Black Rose', 'skyyrose-flagship' ); ?></button>
		<button type="button" class="shop-tab" data-collection="love-hurts" role="tab" aria-selected="false"><?php echo esc_html__( 'Love Hurts', 'skyyrose-flagship' ); ?></button>
		<button type="button" class="shop-tab" data-collection="signature" role="tab" aria-selected="false"><?php echo esc_html__( 'Signature', 'skyyrose-flagship' ); ?></button>
	</div>

	<?php
	/*--------------------------------------------------------------
	 * Product Data
	 *
	 * Each collection has its own banner + grid section.
	 * Products are defined inline for maximum template control.
	 *--------------------------------------------------------------*/

	$collections = array(
		array(
			'slug'        => 'black-rose',
			'number'      => '01',
			'name'        => 'BLACK ROSE',
			'desc'        => 'Limited drops. Unlimited vision. Armor forged in Oakland\'s fire.',
			'experience'  => home_url( '/experience-black-rose/' ),
			'bg'          => '',
			'products'    => array(
				array( 'name' => 'Eclipse Hoodie',   'price' => '$185', 'spec' => '500gsm',          'type' => 'hoodies',     'badge' => 'new' ),
				array( 'name' => 'Noir Bomber',      'price' => '$295', 'spec' => 'Rose gold hardware','type' => 'outerwear',  'badge' => 'ltd' ),
				array( 'name' => 'Thorn Tee',        'price' => '$95',  'spec' => '280gsm',          'type' => 'tees',        'badge' => 'new' ),
				array( 'name' => 'Midnight Joggers',  'price' => '$145', 'spec' => '400gsm',          'type' => 'bottoms',     'badge' => 'ltd' ),
				array( 'name' => 'Shadow Crewneck',   'price' => '$155', 'spec' => '400gsm',          'type' => 'hoodies',     'badge' => '' ),
				array( 'name' => 'Obsidian Cap',      'price' => '$65',  'spec' => 'Structured fit',  'type' => 'accessories', 'badge' => '' ),
			),
		),
		array(
			'slug'        => 'love-hurts',
			'number'      => '02',
			'name'        => 'LOVE HURTS',
			'desc'        => 'Named after family. Raw emotion transformed into armor.',
			'experience'  => home_url( '/experience-love-hurts/' ),
			'bg'          => 'background:linear-gradient(135deg,#140808,#0a0505)',
			'products'    => array(
				array( 'name' => 'Blood Hoodie',     'price' => '$185', 'spec' => '500gsm',      'type' => 'hoodies',     'badge' => 'new' ),
				array( 'name' => 'Crimson Tee',      'price' => '$95',  'spec' => '280gsm',      'type' => 'tees',        'badge' => '' ),
				array( 'name' => 'Thorns Jacket',    'price' => '$265', 'spec' => 'Embroidered', 'type' => 'outerwear',   'badge' => 'ltd' ),
				array( 'name' => 'Heart Crewneck',   'price' => '$155', 'spec' => '400gsm',      'type' => 'hoodies',     'badge' => '' ),
				array( 'name' => 'Passion Joggers',  'price' => '$145', 'spec' => '400gsm',      'type' => 'bottoms',     'badge' => '' ),
				array( 'name' => 'Bleed Cap',        'price' => '$65',  'spec' => 'Structured fit','type' => 'accessories','badge' => '' ),
			),
		),
		array(
			'slug'        => 'signature',
			'number'      => '03',
			'name'        => 'SIGNATURE',
			'desc'        => 'Foundation wardrobe. Everyday luxury. Start here.',
			'experience'  => home_url( '/experience-signature/' ),
			'bg'          => 'background:linear-gradient(135deg,#0a0908,#080705)',
			'products'    => array(
				array( 'name' => 'Cloud Tee',       'price' => '$75',  'spec' => '250gsm',        'type' => 'tees',        'badge' => 'core' ),
				array( 'name' => 'Gold Hoodie',     'price' => '$165', 'spec' => '450gsm',        'type' => 'hoodies',     'badge' => 'new' ),
				array( 'name' => 'Cream Crewneck',  'price' => '$135', 'spec' => '400gsm',        'type' => 'hoodies',     'badge' => '' ),
				array( 'name' => 'Ash Joggers',     'price' => '$125', 'spec' => '350gsm',        'type' => 'bottoms',     'badge' => 'core' ),
				array( 'name' => 'Sand Shorts',     'price' => '$85',  'spec' => '280gsm',        'type' => 'bottoms',     'badge' => '' ),
				array( 'name' => 'Classic Cap',     'price' => '$55',  'spec' => 'Rose gold clasp','type' => 'accessories','badge' => '' ),
			),
		),
	);

	foreach ( $collections as $collection ) :
		$col_slug = esc_attr( $collection['slug'] );
	?>

	<!-- <?php echo esc_html( strtoupper( $collection['name'] ) ); ?> SECTION -->
	<div class="shop-banner" data-section="<?php echo $col_slug; ?>" id="<?php echo esc_attr( str_replace( '-', '', $collection['slug'] ) ); ?>">
		<div class="shop-banner-label"><?php echo esc_html( sprintf( __( 'Collection %s', 'skyyrose-flagship' ), $collection['number'] ) ); ?></div>
		<h2><?php echo esc_html( $collection['name'] ); ?></h2>
		<p class="shop-banner-desc"><?php echo esc_html( $collection['desc'] ); ?></p>
		<a href="<?php echo esc_url( $collection['experience'] ); ?>" class="shop-banner-link"><?php echo esc_html__( 'Enter 3D Experience', 'skyyrose-flagship' ); ?> &rarr;</a>
	</div>

	<div class="shop-grid-wrap">
		<div class="shop-grid" role="list" aria-label="<?php echo esc_attr( $collection['name'] . ' products' ); ?>">

			<?php foreach ( $collection['products'] as $product ) : ?>
			<div class="shop-product" data-collection="<?php echo $col_slug; ?>" data-type="<?php echo esc_attr( $product['type'] ); ?>" role="listitem">
				<div class="shop-product-img"<?php echo ! empty( $collection['bg'] ) ? ' style="' . esc_attr( $collection['bg'] ) . '"' : ''; ?>>
					<?php if ( ! empty( $product['badge'] ) ) : ?>
						<div class="badge badge-<?php echo esc_attr( $product['badge'] ); ?>">
							<?php
							$badge_labels = array( 'new' => 'New', 'ltd' => 'Limited', 'core' => 'Core' );
							echo esc_html( $badge_labels[ $product['badge'] ] ?? '' );
							?>
						</div>
					<?php endif; ?>
				</div>
				<div class="shop-product-body">
					<div class="shop-product-col"><?php echo esc_html( $collection['name'] ); ?></div>
					<div class="shop-product-name"><?php echo esc_html( $product['name'] ); ?></div>
					<div class="shop-product-meta">
						<span class="shop-product-price"><?php echo esc_html( $product['price'] ); ?></span>
						<span class="shop-product-spec"><?php echo esc_html( $product['spec'] ); ?></span>
					</div>
					<div class="shop-product-actions">
						<button class="shop-action-btn" type="button"><?php echo esc_html__( 'Quick View', 'skyyrose-flagship' ); ?></button>
						<button class="shop-action-btn shop-action-primary" type="button"><?php echo esc_html__( 'Pre-Order', 'skyyrose-flagship' ); ?></button>
					</div>
				</div>
			</div>
			<?php endforeach; ?>

		</div>
	</div>

	<?php endforeach; ?>

	<!-- CTA -->
	<section class="shop-cta">
		<div class="shop-cta-label"><?php echo esc_html__( 'Reserve Yours', 'skyyrose-flagship' ); ?></div>
		<h2><?php echo esc_html__( 'PRE-ORDER NOW', 'skyyrose-flagship' ); ?></h2>
		<p class="shop-cta-desc"><?php echo esc_html__( 'Limited quantities. Each piece individually numbered. Secure yours before the drop.', 'skyyrose-flagship' ); ?></p>
		<a href="<?php echo esc_url( home_url( '/pre-order/' ) ); ?>" class="shop-cta-btn"><?php echo esc_html__( 'Pre-Order', 'skyyrose-flagship' ); ?> &rarr;</a>
	</section>

</main><!-- #primary -->

<?php
get_footer();
