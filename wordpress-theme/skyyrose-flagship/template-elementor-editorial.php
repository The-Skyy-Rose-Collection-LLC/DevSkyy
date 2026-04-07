<?php
/**
 * Template Name: Elementor Editorial
 * Template Post Type: page
 *
 * Blank canvas editorial template for Elementor page builder.
 * Loads the landing-pages.css brand palette so Elementor content
 * inherits SkyyRose design tokens and collection-aware CSS custom properties.
 *
 * The collection palette is controlled via a page meta field
 * 'skyyrose_collection' (black-rose | love-hurts | signature).
 * Elementor takes full control of the content area.
 *
 * @package SkyyRose_Flagship
 * @since   6.5.0
 */

defined( 'ABSPATH' ) || exit;

// Determine collection palette from page meta (default: signature).
$skyyrose_ee_collection = get_post_meta( get_the_ID(), 'skyyrose_collection', true );
if ( ! in_array( $skyyrose_ee_collection, array( 'black-rose', 'love-hurts', 'signature' ), true ) ) {
	$skyyrose_ee_collection = 'signature';
}

get_header();
?>

<div class="lp" data-collection="<?php echo esc_attr( $skyyrose_ee_collection ); ?>">

	<?php
	while ( have_posts() ) :
		the_post();
		the_content();
	endwhile;
	?>

</div><!-- /.lp -->

<?php get_footer(); ?>
