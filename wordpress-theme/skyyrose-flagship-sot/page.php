<?php
/**
 * Marketplace pages.
 *
 * @package SkyyRoseFlagshipSOT
 */

defined( 'ABSPATH' ) || exit;

get_header();
while ( have_posts() ) :
	the_post();
	$slug = get_post_field( 'post_name', get_the_ID() );
	?>
	<main id="primary" class="srs-page">
		<?php if ( 'collections' === $slug ) : ?>
			<header><p><?php esc_html_e( 'Collections', 'skyyrose-flagship-sot' ); ?></p><h1><?php esc_html_e( 'Choose your world.', 'skyyrose-flagship-sot' ); ?></h1></header>
			<div class="srs-rail" tabindex="0" aria-label="<?php esc_attr_e( 'Collection worlds. Scroll horizontally.', 'skyyrose-flagship-sot' ); ?>">
			<?php
			foreach ( skyyrosesot_collections() as $collection_slug => $collection ) :
				$image  = skyyrosesot_first_image( $collection );
				$lockup = skyyrosesot_lockup( $collection );
				?>
				<?php
				if ( $image ) :
					?>
				<a class="srs-world" href="<?php echo esc_url( home_url( '/collections/' . $collection_slug . '/' ) ); ?>" style="<?php echo esc_attr( skyyrosesot_collection_style( $collection ) ); ?>"><img src="<?php echo esc_url( skyyrosesot_asset_uri( $image ) ); ?>" alt="" loading="lazy" width="1920" height="1080"><span><small><?php echo esc_html( $collection['name'] ); ?></small>
					<?php
					if ( $lockup ) :
						?>
	<img class="srs-world__lockup" src="<?php echo esc_url( skyyrosesot_asset_uri( $lockup ) ); ?>" alt="<?php echo esc_attr( $collection['name'] ); ?>"><?php endif; ?><em><?php echo esc_html( $collection['story']['seed'] ); ?></em><b><?php esc_html_e( 'Enter world →', 'skyyrose-flagship-sot' ); ?></b></span></a><?php endif; ?><?php endforeach; ?></div>
		<?php elseif ( 'pre-order' === $slug || 'preorder' === $slug ) : ?>
			<header><p><?php esc_html_e( 'Pre-order', 'skyyrose-flagship-sot' ); ?></p><h1><?php esc_html_e( 'Reserve next chapter.', 'skyyrose-flagship-sot' ); ?></h1><div class="srs-page__copy"><?php the_content(); ?></div></header><?php skyyrosesot_render_products( '', 18 ); ?>
		<?php elseif ( 'contact' === $slug ) : ?>
			<header><p><?php esc_html_e( 'Contact', 'skyyrose-flagship-sot' ); ?></p><h1><?php esc_html_e( 'Talk to SkyyRose.', 'skyyrose-flagship-sot' ); ?></h1></header><div class="srs-page__copy"><p><a href="mailto:hello@skyyrose.co">hello@skyyrose.co</a></p><?php the_content(); ?></div>
		<?php else : ?>
			<header><p><?php echo esc_html( get_the_title() ); ?></p><h1><?php the_title(); ?></h1></header><div class="srs-page__copy"><?php the_content(); ?></div>
		<?php endif; ?>
	</main>
	<?php
endwhile;
get_footer();
