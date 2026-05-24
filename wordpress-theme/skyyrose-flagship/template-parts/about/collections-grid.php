<?php
/**
 * About Chapter II — The Collections.
 *
 * Editorial index-style row list: each collection renders as a bordered
 * row with index number, name, tagline, short description, and an arrow CTA.
 * Hero image floats at the right of each row (4:5 portrait crop).
 *
 * @package SkyyRose
 * @since   1.3.0
 */

defined( 'ABSPATH' ) || exit;

$catalog = function_exists( 'skyyrose_get_product_catalog' ) ? skyyrose_get_product_catalog() : array();

$collection_data = array(
	'signature'    => array(
		'title' => 'Signature',
		'tag'   => 'The Origin',
		'desc'  => 'The first rose, the first script. Where SkyyRose began — gold-accented luxury streetwear, gender-neutral by default.',
		'link'  => '/collection-signature/',
		'img'   => '',
	),
	'black-rose'   => array(
		'title' => 'Black Rose',
		'tag'   => 'The Refusal',
		'desc'  => 'Dark, powerful, unapologetic. Silver-on-black, gothic restraint. Streetwear armor for everyone who refused to apologize first.',
		'link'  => '/collection-black-rose/',
		'img'   => '',
	),
	'love-hurts'   => array(
		'title' => 'Love Hurts',
		'tag'   => 'The Grief',
		'desc'  => 'A collection named after grief, made to be worn anyway. Crimson and deep red, Beauty &amp; the Beast cadence — luxury or witchcraft, take your pick.',
		'link'  => '/collection-love-hurts/',
		'img'   => '',
	),
	'kids-capsule' => array(
		'title' => 'Kids Capsule',
		'tag'   => 'The Heir',
		'desc'  => 'Rose gold and soft pink. The fourth chapter, smaller silhouettes, same craftsmanship. Passing the torch on the same terms that built the brand.',
		'link'  => '/collection-kids-capsule/',
		'img'   => '',
	),
);

// Map first catalog product per collection for the portal hero image.
foreach ( $catalog as $product ) {
	$col = $product['collection'] ?? '';
	if ( isset( $collection_data[ $col ] ) && empty( $collection_data[ $col ]['img'] ) ) {
		$collection_data[ $col ]['img'] = $product['image_url'] ?? '';
	}
}
?>

<section class="abt-collections" id="collections">
	<div class="abt-chapter__container">
		<div class="abt-chapter__head rv rv-clip-up">
			<span class="abt-chapter__num" aria-hidden="true"><?php esc_html_e( 'CH. 02', 'skyyrose' ); ?></span>
			<span class="abt-chapter__rule" aria-hidden="true"></span>
			<span class="abt-chapter__label"><?php esc_html_e( 'The Collections', 'skyyrose' ); ?></span>
		</div>
		<h2 class="abt-chapter__title rv rv-clip-up rv-d1">
			<?php
			echo wp_kses(
				__( 'Four Worlds.<br>One Bloodline.', 'skyyrose' ),
				array(
					'br'     => array(),
					'em'     => array(),
					'strong' => array(),
				)
			);
			?>
		</h2>
	</div>

	<ol class="abt-coll-list stagger-grid" role="list">
		<?php
		$i = 0;
		foreach ( $collection_data as $slug => $data ) :
			++$i;
			$index   = str_pad( (string) $i, 2, '0', STR_PAD_LEFT );
			$img_url = ! empty( $data['img'] ) ? $data['img'] : get_theme_file_uri( 'assets/images/placeholder-product.jpg' );
			?>
			<li class="abt-coll-row" data-collection="<?php echo esc_attr( $slug ); ?>" role="listitem">
				<a href="<?php echo esc_url( home_url( $data['link'] ) ); ?>" class="abt-coll-row__link">
					<span class="abt-coll-row__index" aria-hidden="true"><?php echo esc_html( $index ); ?></span>
					<figure class="abt-coll-row__media">
						<img src="<?php echo esc_url( $img_url ); ?>"
							alt="<?php echo esc_attr( $data['title'] ); ?>"
							loading="lazy"
							width="800" height="1000">
					</figure>
					<div class="abt-coll-row__body">
						<span class="abt-coll-row__tag"><?php echo esc_html( $data['tag'] ); ?></span>
						<h3 class="abt-coll-row__title"><?php echo esc_html( $data['title'] ); ?></h3>
						<p class="abt-coll-row__desc">
							<?php
							echo wp_kses(
								$data['desc'],
								array(
									'em'     => array(),
									'strong' => array(),
								)
							);
							?>
						</p>
					</div>
					<span class="abt-coll-row__cta" aria-hidden="true">
						<?php esc_html_e( 'Enter', 'skyyrose' ); ?>
						<svg width="14" height="10" viewBox="0 0 14 10" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M9 1L13 5L9 9M13 5H1" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>
					</span>
				</a>
			</li>
		<?php endforeach; ?>
	</ol>
</section>
