<?php
/**
 * Front Page: Instagram Feed
 *
 * 6-square grid with hover overlay showing likes/comments.
 *
 * @package SkyyRose_Flagship
 * @since   3.2.0
 */

// Prevent direct access.
if ( ! defined( 'ABSPATH' ) ) {
	exit;
}

$insta_img_dir = get_theme_file_uri( 'assets/images/instagram' );
$insta_img_path = get_theme_file_path( 'assets/images/instagram' );

$insta_posts = array(
	array(
		'alt'      => __( 'Black Rose collection photoshoot', 'skyyrose-flagship' ),
		'likes'    => '2.4K',
		'comments' => '186',
		'image'    => 'insta-1-black-rose-shoot.jpg',
		'gradient' => 'linear-gradient(135deg, #1a0000, #3d0000)',
	),
	array(
		'alt'      => __( 'Love Hurts varsity jacket detail', 'skyyrose-flagship' ),
		'likes'    => '1.8K',
		'comments' => '142',
		'image'    => 'insta-2-love-hurts-detail.jpg',
		'gradient' => 'linear-gradient(135deg, #2d1a1d, #4a2a30)',
	),
	array(
		'alt'      => __( 'Oakland skyline with SkyyRose gear', 'skyyrose-flagship' ),
		'likes'    => '3.1K',
		'comments' => '234',
		'image'    => 'insta-3-oakland-skyline.jpg',
		'gradient' => 'linear-gradient(135deg, #0a0a14, #1a1a2e)',
	),
	array(
		'alt'      => __( 'Signature collection behind the scenes', 'skyyrose-flagship' ),
		'likes'    => '2.7K',
		'comments' => '198',
		'image'    => 'insta-4-signature-bts.jpg',
		'gradient' => 'linear-gradient(135deg, #1a1810, #2d2820)',
	),
	array(
		'alt'      => __( 'Customer wearing BLACK Rose Hoodie', 'skyyrose-flagship' ),
		'likes'    => '4.2K',
		'comments' => '312',
		'image'    => 'insta-5-customer-lifestyle.jpg',
		'gradient' => 'linear-gradient(135deg, #1a0808, #2a0a0a)',
	),
	array(
		'alt'      => __( 'SkyyRose pop-up event in Oakland', 'skyyrose-flagship' ),
		'likes'    => '5.1K',
		'comments' => '428',
		'image'    => 'insta-6-popup-event.jpg',
		'gradient' => 'linear-gradient(135deg, #140a10, #2a1420)',
	),
);
?>

<section class="instagram-feed" aria-labelledby="instagram-heading">
	<div class="instagram-feed__header section-header">
		<span class="section-header__label">
			<?php esc_html_e( 'Follow the Movement', 'skyyrose-flagship' ); ?>
		</span>
		<h2 class="section-header__title" id="instagram-heading">
			<?php esc_html_e( '@skyyrose', 'skyyrose-flagship' ); ?>
		</h2>
		<p class="section-header__subtitle">
			<?php esc_html_e( 'Join 25K+ followers for behind-the-scenes content, new drops, and community highlights.', 'skyyrose-flagship' ); ?>
		</p>
	</div>

	<div class="instagram-feed__grid">
		<?php foreach ( $insta_posts as $post ) : ?>
			<a
				href="<?php echo esc_url( 'https://www.instagram.com/skyyrose/' ); ?>"
				class="instagram-feed__item js-scroll-reveal"
				target="_blank"
				rel="noopener noreferrer"
				aria-label="<?php echo esc_attr( sprintf( __( 'View %s on Instagram', 'skyyrose-flagship' ), $post['alt'] ) ); ?>"
			>
				<div class="instagram-feed__image" style="background: <?php echo esc_attr( $post['gradient'] ); ?>;" aria-hidden="true">
					<?php
					$insta_file = ! empty( $post['image'] ) ? $insta_img_path . '/' . $post['image'] : '';
					if ( $insta_file && file_exists( $insta_file ) ) :
					?>
						<img
							src="<?php echo esc_url( $insta_img_dir . '/' . $post['image'] ); ?>"
							alt="<?php echo esc_attr( $post['alt'] ); ?>"
							loading="lazy"
							width="400"
							height="400"
							class="instagram-feed__photo"
						>
					<?php else : ?>
						<svg class="instagram-feed__placeholder-icon" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1" opacity="0.2" aria-hidden="true" focusable="false">
							<rect x="2" y="2" width="20" height="20" rx="5" ry="5"/>
							<path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"/>
							<line x1="17.5" y1="6.5" x2="17.51" y2="6.5"/>
						</svg>
					<?php endif; ?>
				</div>
				<div class="instagram-feed__overlay" aria-hidden="true">
					<span class="instagram-feed__stat">
						<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false">
							<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
						</svg>
						<?php echo esc_html( $post['likes'] ); ?>
					</span>
					<span class="instagram-feed__stat">
						<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false">
							<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
						</svg>
						<?php echo esc_html( $post['comments'] ); ?>
					</span>
				</div>
			</a>
		<?php endforeach; ?>
	</div>

	<div class="instagram-feed__cta">
		<a href="<?php echo esc_url( 'https://www.instagram.com/skyyrose/' ); ?>" class="btn btn--outline" target="_blank" rel="noopener noreferrer">
			<?php esc_html_e( 'Follow @skyyrose', 'skyyrose-flagship' ); ?>
		</a>
	</div>
</section>
