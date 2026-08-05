<?php defined( 'ABSPATH' ) || exit; ?><!doctype html>
<html <?php language_attributes(); ?>>
<head>
	<meta charset="<?php bloginfo( 'charset' ); ?>">
	<meta name="viewport" content="width=device-width,initial-scale=1">
	<?php wp_head(); ?>
</head>
<body <?php body_class(); ?>>
	<?php wp_body_open(); ?>
	<a class="sr2-skip" href="#sr2-content"><?php esc_html_e( 'Skip to content', 'skyyrose-flagship-2' ); ?></a>
	<?php if ( ! skyyrose2_render_builder_location( 'header' ) ) : ?>
		<?php skyyrose2_header(); ?>
	<?php endif; ?>
	<span id="sr2-content" tabindex="-1"></span>
