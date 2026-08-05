<?php
/**
 * Virtual Collections index route.
 *
 * @package SkyyRoseFlagship2
 */

defined( 'ABSPATH' ) || exit;

get_header();
?>
<main id="primary" class="sr2-page sr2-page--collections">
	<?php get_template_part( 'template-parts/collections-index' ); ?>
</main>
<?php
get_footer();
