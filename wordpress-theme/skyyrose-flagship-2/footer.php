<?php
defined( 'ABSPATH' ) || exit;

get_template_part( 'template-parts/skyy-mascot' );
if ( ! skyyrose2_render_builder_location( 'footer' ) ) {
	skyyrose2_footer();
}
wp_footer();
?>
</body>
</html>
