<?php
defined( 'ABSPATH' ) || exit;


if ( ! skyyrose2_render_builder_location( 'footer' ) ) {
	get_template_part( 'template-parts/skyy-mascot' );
	skyyrose2_footer();
}
wp_footer();
?>
</body>
</html>
