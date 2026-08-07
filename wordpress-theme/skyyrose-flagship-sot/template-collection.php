<?php
/**
 * Template Name: SkyyRose SOT Collection
 *
 * @package SkyyRoseFlagshipSOT
 */

defined( 'ABSPATH' ) || exit;

$slug       = sanitize_title( get_post_field( 'post_name', get_the_ID() ) );
$collection = skyyrosesot_collection( $slug );
$hero       = skyyrosesot_first_image( $collection );
$lockup     = skyyrosesot_lockup( $collection );

get_header();
?>
<main id="primary" class="srs-page" style="<?php echo esc_attr( skyyrosesot_collection_style( $collection ) ); ?>">
	<section class="srs-page__hero">
	<?php
	if ( $hero ) :
		?>
		<img src="<?php echo esc_url( skyyrosesot_asset_uri( $hero ) ); ?>" alt="" fetchpriority="high" width="1920" height="1080"><?php endif; ?><div>
		<?php
		if ( $lockup ) :
			?>
		<img class="srs-lockup" src="<?php echo esc_url( skyyrosesot_asset_uri( $lockup ) ); ?>" alt="<?php echo esc_attr( $collection['name'] ); ?>"><?php endif; ?><p><?php echo esc_html( $collection['story']['seed'] ?? '' ); ?></p><a class="srs-button" href="#shop"><?php esc_html_e( 'Shop collection', 'skyyrose-flagship-sot' ); ?></a></div></section>
	<section id="shop" class="srs-section"><header><p><?php echo esc_html( $collection['name'] ?? '' ); ?></p><h2 style="font-family:var(--srs-script),cursive"><?php esc_html_e( 'Pieces from this world.', 'skyyrose-flagship-sot' ); ?></h2></header><?php skyyrosesot_render_products( $slug, 18 ); ?></section>
</main>
<?php get_footer(); ?>
